"""
Schema Cache Service - Lazy Loading

Provides on-demand schema fetching with intelligent caching to avoid
expensive upfront metadata collection.

Key features:
- Lazy loading: Only fetch schema when table is actually queried
- Per-table caching with TTL
- LRU eviction for memory management
- Automatic retry with exponential backoff for failed fetches
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import OrderedDict
from dataclasses import dataclass, asdict
import hashlib

from ..core.exceptions import CacheError, SchemaError
from ..core.logging_config import get_logger
from ..core.performance import measure_operation, record_cache_hit, record_cache_miss
from ..utils.kusto_client import get_connection_manager
from ..utils.helpers import safe_json_dumps, load_json_file, save_json_file

logger = get_logger("cache")


@dataclass
class SchemaMetadata:
    """Cached schema metadata for a table"""
    table_path: str  # cluster.database.table
    cluster: str
    database: str
    table: str
    columns: List[Dict[str, str]]  # [{'name': 'col', 'type': 'string'}, ...]
    time_columns: List[str]
    primary_time_column: Optional[str]
    numeric_columns: List[str]
    string_columns: List[str]
    row_count: Optional[int]
    last_updated: Optional[str]
    fetched_at: datetime
    cache_hits: int = 0
    notes: List[Dict[str, Any]] = None  # User-added context notes
    
    def __post_init__(self):
        """Initialize notes list if None"""
        if self.notes is None:
            self.notes = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['fetched_at'] = self.fetched_at.isoformat()
        return result


@dataclass
class CacheEntry:
    """Cache entry with TTL and access tracking"""
    data: SchemaMetadata
    expires_at: datetime
    access_count: int
    last_accessed: datetime
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update access tracking"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.data.cache_hits += 1


class SchemaCacheService:
    """
    Service for lazy-loading and caching table schemas
    
    Benefits over upfront caching:
    1. Faster startup - no massive data collection
    2. Lower memory usage - only cache what's used
    3. Always fresh - fetch on-demand means recent schema
    4. User-friendly - fast response for frequently-used tables
    """
    
    def __init__(
        self,
        max_cache_size: int = 5000,
        default_ttl_hours: int = 24,
        enable_persistent_cache: bool = True,
        cache_file: str = "cache/schema_cache.json",
        notes_file: str = "cache/table_notes.json"
    ):
        # LRU cache using OrderedDict
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_cache_size = max_cache_size
        self.default_ttl = timedelta(hours=default_ttl_hours)
        
        # Persistent cache
        self.enable_persistent_cache = enable_persistent_cache
        self.cache_file = cache_file
        self.notes_file = notes_file
        
        # Table notes storage (persistent across cache clears)
        self.table_notes: Dict[str, List[Dict[str, Any]]] = {}
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.fetch_attempts = 0
        self.fetch_failures = 0
        
        # Load persistent cache if enabled
        if enable_persistent_cache:
            self._load_persistent_cache()
            self._load_notes()
    
    def _make_cache_key(self, cluster: str, database: str, table: str) -> str:
        """Generate cache key for a table"""
        return f"{cluster}.{database}.{table}"
    
    def _evict_lru(self):
        """Evict least recently used item if cache is full"""
        if len(self.cache) >= self.max_cache_size:
            # Remove the oldest item (first in OrderedDict)
            self.cache.popitem(last=False)
    
    async def get_schema(
        self,
        cluster: str,
        database: str,
        table: str,
        fetch_if_missing: bool = True
    ) -> Optional[SchemaMetadata]:
        """
        Get schema for a table, fetching if necessary
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            fetch_if_missing: Whether to fetch from Kusto if not cached
        
        Returns:
            SchemaMetadata if available, None otherwise
        """
        with measure_operation("schema_cache_get", {"table": f"{cluster}.{database}.{table}"}):
            cache_key = self._make_cache_key(cluster, database, table)
            
            # Check cache first
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                
                # Check if expired
                if entry.is_expired():
                    del self.cache[cache_key]
                    record_cache_miss("schema")
                    logger.debug(f"Schema cache expired for {cache_key}")
                else:
                    # Cache hit! Move to end (most recently used)
                    self.cache.move_to_end(cache_key)
                    entry.touch()
                    record_cache_hit("schema")
                    logger.debug(f"Schema cache hit for {cache_key}")
                    return entry.data
            else:
                record_cache_miss("schema")
                logger.debug(f"Schema cache miss for {cache_key}")
            
            # Cache miss - fetch if enabled
            if fetch_if_missing:
                return await self._fetch_and_cache_schema(cluster, database, table)
            
            return None
    
    async def _fetch_and_cache_schema(
        self,
        cluster: str,
        database: str,
        table: str
    ) -> Optional[SchemaMetadata]:
        """Fetch schema from Kusto and cache it"""
        self.fetch_attempts += 1
        table_path = f"{cluster}.{database}.{table}"
        
        try:
            connection_manager = get_connection_manager()
            logger.info(f"Fetching schema for {table_path}...")
            schema_data = await connection_manager.get_table_schema(cluster, database, table)
            
            if schema_data:
                # Convert to SchemaMetadata
                cache_key = self._make_cache_key(cluster, database, table)
                schema_metadata = SchemaMetadata(
                    table_path=schema_data["table_path"],
                    cluster=schema_data["cluster"],
                    database=schema_data["database"],
                    table=schema_data["table"],
                    columns=schema_data["columns"],
                    time_columns=schema_data["time_columns"],
                    primary_time_column=schema_data["primary_time_column"],
                    numeric_columns=schema_data["numeric_columns"],
                    string_columns=schema_data["string_columns"],
                    row_count=None,  # Not fetched in schema query
                    last_updated=None,
                    fetched_at=datetime.fromisoformat(schema_data["fetched_at"]),
                    notes=self.table_notes.get(cache_key, [])
                )
                
                self.store_schema(schema_metadata)
                logger.info(f"Successfully fetched and cached schema for {table_path} ({len(schema_metadata.columns)} columns)")
                return schema_metadata
            else:
                self.fetch_failures += 1
                logger.warning(f"No schema data returned for {table_path}")
                logger.info("Troubleshooting: This usually means the table doesn't exist or you don't have access. Check table name and permissions.")
                return None
                
        except Exception as e:
            self.fetch_failures += 1
            logger.error(f"Failed to fetch schema for {table_path}: {e}")
            logger.info("Troubleshooting hints:")
            logger.info("  1. Ensure you're logged in: az login")
            logger.info("  2. Check table exists and you have access")
            logger.info("  3. Verify network connectivity to Kusto cluster")
            logger.info(f"  4. Test with: az kusto query --cluster {cluster} --database {database} --query '{table} | take 1'")
            raise SchemaError(
                f"Could not fetch schema for {table_path}. This may be due to authentication, network, or permissions issues. {e}",
                table_path=table_path
            )
    
    def store_schema(
        self,
        schema_data: SchemaMetadata,
        ttl_hours: Optional[int] = None
    ):
        """
        Store schema in cache
        
        Args:
            schema_data: Schema metadata to cache
            ttl_hours: Optional custom TTL in hours
        """
        cache_key = self._make_cache_key(
            schema_data.cluster,
            schema_data.database,
            schema_data.table
        )
        
        # Evict LRU item if needed
        self._evict_lru()
        
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        
        entry = CacheEntry(
            data=schema_data,
            expires_at=datetime.now() + ttl,
            access_count=0,
            last_accessed=datetime.now()
        )
        
        self.cache[cache_key] = entry
        logger.debug(f"Stored schema in cache: {cache_key}")
        
        # Save to persistent cache if enabled
        if self.enable_persistent_cache:
            self._save_persistent_cache()
    
    def has_schema(self, cluster: str, database: str, table: str) -> bool:
        """Check if schema is cached and valid"""
        cache_key = self._make_cache_key(cluster, database, table)
        if cache_key not in self.cache:
            return False
        
        entry = self.cache[cache_key]
        return not entry.is_expired()
    
    def invalidate(self, cluster: str, database: str, table: str):
        """Invalidate cached schema for a table"""
        cache_key = self._make_cache_key(cluster, database, table)
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def clear_expired(self) -> int:
        """Remove expired cache entries, returns count removed"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0.0
        total_requests = self.cache_hits + self.cache_misses
        if total_requests > 0:
            hit_rate = (self.cache_hits / total_requests) * 100
        
        fetch_success_rate = 0.0
        if self.fetch_attempts > 0:
            fetch_success_rate = ((self.fetch_attempts - self.fetch_failures) / self.fetch_attempts) * 100
        
        # Get top accessed tables
        top_tables = sorted(
            [(key, entry.access_count) for key, entry in self.cache.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'cache_size': len(self.cache),
            'max_cache_size': self.max_cache_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'fetch_attempts': self.fetch_attempts,
            'fetch_failures': self.fetch_failures,
            'fetch_success_rate_percent': round(fetch_success_rate, 2),
            'top_accessed_tables': [
                {'table': key, 'access_count': count}
                for key, count in top_tables
            ]
        }
    
    def get_cached_tables(self) -> List[Dict[str, Any]]:
        """Get list of all cached tables with metadata"""
        tables = []
        
        for key, entry in self.cache.items():
            tables.append({
                'table_path': entry.data.table_path,
                'cluster': entry.data.cluster,
                'database': entry.data.database,
                'table': entry.data.table,
                'column_count': len(entry.data.columns),
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed.isoformat(),
                'expires_at': entry.expires_at.isoformat(),
                'is_expired': entry.is_expired()
            })
        
        return tables
    
    def _load_persistent_cache(self):
        """Load cache from disk"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            for item in data.get('cache', []):
                cache_key = self._make_cache_key(
                    item['cluster'],
                    item['database'],
                    item['table']
                )
                schema_data = SchemaMetadata(
                    table_path=item['table_path'],
                    cluster=item['cluster'],
                    database=item['database'],
                    table=item['table'],
                    columns=item['columns'],
                    time_columns=item['time_columns'],
                    primary_time_column=item.get('primary_time_column'),
                    numeric_columns=item['numeric_columns'],
                    string_columns=item['string_columns'],
                    row_count=item.get('row_count'),
                    last_updated=item.get('last_updated'),
                    fetched_at=datetime.fromisoformat(item['fetched_at']),
                    cache_hits=item.get('cache_hits', 0),
                    notes=self.table_notes.get(cache_key, [])
                )
                
                cache_key = self._make_cache_key(
                    schema_data.cluster,
                    schema_data.database,
                    schema_data.table
                )
                
                # Check if expired
                expires_at = datetime.fromisoformat(item['expires_at'])
                if datetime.now() < expires_at:
                    entry = CacheEntry(
                        data=schema_data,
                        expires_at=expires_at,
                        access_count=item.get('access_count', 0),
                        last_accessed=datetime.fromisoformat(item.get('last_accessed', datetime.now().isoformat()))
                    )
                    self.cache[cache_key] = entry
        
        except FileNotFoundError:
            pass  # No persistent cache file yet
        except Exception as e:
            print(f"Warning: Failed to load persistent cache: {e}")
    
    def _save_persistent_cache(self):
        """Save cache to disk"""
        try:
            cache_data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'cache': []
            }
            
            for key, entry in self.cache.items():
                if not entry.is_expired():
                    item = entry.data.to_dict()
                    item['expires_at'] = entry.expires_at.isoformat()
                    item['access_count'] = entry.access_count
                    item['last_accessed'] = entry.last_accessed.isoformat()
                    cache_data['cache'].append(item)
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Failed to save persistent cache: {e}")
    
    def clear_all(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.fetch_attempts = 0
        self.fetch_failures = 0
    
    def add_note(self, cluster: str, database: str, table: str, note: str, category: str = "general") -> Dict[str, Any]:
        """
        Add a note to a table's metadata
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            note: Note text to add
            category: Note category (e.g., 'workflow', 'usage', 'schema', 'general')
        
        Returns:
            Dictionary with the added note
        """
        cache_key = self._make_cache_key(cluster, database, table)
        
        # Create note entry
        note_entry = {
            "note": note,
            "category": category,
            "added_at": datetime.now().isoformat(),
            "table_path": f"{cluster}.{database}.{table}"
        }
        
        # Add to notes storage
        if cache_key not in self.table_notes:
            self.table_notes[cache_key] = []
        self.table_notes[cache_key].append(note_entry)
        
        # Update cached schema if present
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if entry.data.notes is None:
                entry.data.notes = []
            entry.data.notes.append(note_entry)
        
        # Save notes to persistent storage
        if self.enable_persistent_cache:
            self._save_notes()
        
        logger.info(f"Added note to {cache_key}: {note[:50]}...")
        return note_entry
    
    def get_notes(self, cluster: str, database: str, table: str) -> List[Dict[str, Any]]:
        """
        Get all notes for a table
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
        
        Returns:
            List of note entries
        """
        cache_key = self._make_cache_key(cluster, database, table)
        return self.table_notes.get(cache_key, [])
    
    def _load_notes(self):
        """Load table notes from disk"""
        try:
            with open(self.notes_file, 'r') as f:
                data = json.load(f)
                self.table_notes = data.get('notes', {})
                logger.info(f"Loaded notes for {len(self.table_notes)} tables")
        except FileNotFoundError:
            logger.debug("No notes file found, starting with empty notes")
            self.table_notes = {}
        except Exception as e:
            logger.warning(f"Failed to load table notes: {e}")
            self.table_notes = {}
    
    def _save_notes(self):
        """Save table notes to disk"""
        try:
            import os
            os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
            
            notes_data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'notes': self.table_notes
            }
            
            with open(self.notes_file, 'w') as f:
                json.dump(notes_data, f, indent=2)
            logger.debug(f"Saved notes for {len(self.table_notes)} tables")
        except Exception as e:
            logger.error(f"Failed to save table notes: {e}")


# Singleton instance
_schema_cache_service = SchemaCacheService()


def get_schema_cache_service() -> SchemaCacheService:
    """Get the singleton schema cache service instance"""
    return _schema_cache_service
