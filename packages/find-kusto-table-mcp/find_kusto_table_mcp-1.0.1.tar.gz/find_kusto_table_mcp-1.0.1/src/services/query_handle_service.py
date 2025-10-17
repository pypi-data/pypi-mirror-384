"""
Query Handle Service for Kusto MCP

Manages query handles to enable safe query operations without risk of table/column
hallucination. Query handles store actual query results and metadata, which can
then be used for analytics and result manipulation.

Features:
- In-memory caching with configurable TTL
- Persistent disk storage (survives restarts)
- LRU eviction for memory management
- Integrity verification with hashing

Inspired by enhanced-ado-mcp's successful query handle pattern.
"""

import hashlib
import json
import time
import pickle
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, OrderedDict

from ..core.exceptions import HandleError, ValidationError
from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import generate_handle, safe_json_dumps

logger = get_logger("query_handle")


@dataclass
class ItemContext:
    """Context for a single result item - enables rich selection"""
    index: int  # Zero-based index in results
    row_data: Dict[str, Any]  # The actual row data
    tags: List[str] = None  # Optional tags for filtering
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class SelectionCriteria:
    """Criteria for selecting items from cached results"""
    column_filters: Optional[Dict[str, Any]] = None  # {'column_name': value}
    column_contains: Optional[Dict[str, str]] = None  # {'column_name': 'substring'}
    column_range: Optional[Dict[str, tuple]] = None  # {'column_name': (min, max)}
    tags: Optional[List[str]] = None  # Filter by tags
    limit: Optional[int] = None


@dataclass
class SelectionMetadata:
    """Metadata about cached results for selection"""
    total_items: int
    selectable_indices: List[int]  # All valid indices
    available_columns: List[str]  # Column names
    column_types: Dict[str, str]  # Column type information


@dataclass
class QueryResultMetadata:
    """Metadata about query execution"""
    query: str
    table_path: str
    cluster: str
    database: str
    table: str
    row_count: int
    columns: List[Dict[str, str]]  # [{'name': 'col1', 'type': 'string'}, ...]
    execution_time_ms: float
    timestamp: str


@dataclass
class QueryHandleData:
    """Data stored for a query handle"""
    handle: str
    metadata: QueryResultMetadata
    results: List[Dict[str, Any]]  # Actual query results
    created_at: datetime
    expires_at: datetime
    result_hash: str  # Hash of results for integrity verification
    item_context: Optional[List[ItemContext]] = None  # Rich context for each item
    selection_metadata: Optional[SelectionMetadata] = None  # Selection helpers
    
    def is_expired(self) -> bool:
        """Check if handle has expired"""
        return datetime.now() > self.expires_at
    
    def minutes_until_expiration(self) -> int:
        """Get minutes until expiration"""
        delta = self.expires_at - datetime.now()
        return max(0, int(delta.total_seconds() / 60))


class QueryHandleService:
    """
    Service for managing query handles
    
    Provides anti-hallucination guarantees by:
    1. Storing actual query results server-side
    2. Returning opaque handles instead of raw data
    3. Enabling analytics on cached results without context pollution
    4. Automatic expiration and cleanup
    5. Persistent disk storage (survives restarts)
    6. LRU eviction for memory management
    """
    
    def __init__(
        self, 
        default_ttl_hours: int = 1,
        persist_to_disk: bool = True,
        cache_dir: str = "cache/query_handles",
        max_memory_handles: int = 1000
    ):
        self.handles: OrderedDict[str, QueryHandleData] = OrderedDict()
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.server_start_time = datetime.now()
        self.persist_to_disk = persist_to_disk
        self.cache_dir = Path(cache_dir)
        self.max_memory_handles = max_memory_handles
        
        # Create cache directory
        if self.persist_to_disk:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Query handle persistence enabled: {self.cache_dir}")
        
        # Statistics
        self.total_handles_created = 0
        self.total_queries_executed = 0
        self.disk_writes = 0
        self.disk_reads = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Load persisted handles from disk
        if self.persist_to_disk:
            self._load_persisted_handles()
        

    
    def _hash_results(self, results: List[Dict[str, Any]]) -> str:
        """Generate hash of results for integrity verification"""
        result_str = json.dumps(results, sort_keys=True, default=str)
        return hashlib.sha256(result_str.encode()).hexdigest()[:16]
    
    def store_query_results(
        self,
        query: str,
        table_path: str,
        cluster: str,
        database: str,
        table: str,
        results: List[Dict[str, Any]],
        columns: List[Dict[str, str]],
        execution_time_ms: float,
        ttl_hours: Optional[int] = None
    ) -> str:
        """
        Store query results and return a handle
        
        Args:
            query: The KQL query that was executed
            table_path: Full table path (cluster.database.table)
            cluster: Cluster name
            database: Database name
            table: Table name
            results: Query results as list of dictionaries
            columns: Column metadata
            execution_time_ms: Query execution time
            ttl_hours: Optional custom TTL in hours
            
        Returns:
            Query handle string (e.g., "qh_a1b2c3d4...")
        """
        with measure_operation("store_query_results", {
            "table_path": table_path,
            "row_count": len(results),
            "query_length": len(query)
        }):
            handle = generate_handle("qh")
            ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
            
            metadata = QueryResultMetadata(
                query=query,
                table_path=table_path,
                cluster=cluster,
                database=database,
                table=table,
                row_count=len(results),
                columns=columns,
                execution_time_ms=execution_time_ms,
                timestamp=datetime.now().isoformat()
            )
            
            handle_data = QueryHandleData(
                handle=handle,
                metadata=metadata,
                results=results,
                created_at=datetime.now(),
                expires_at=datetime.now() + ttl,
                result_hash=self._hash_results(results)
            )
            
            # Create item context for rich selection
            handle_data.item_context = self._create_item_context(results)
            handle_data.selection_metadata = self._create_selection_metadata(results, columns)
            
            self.handles[handle] = handle_data
            self.total_handles_created += 1
            self.total_queries_executed += 1
            
            # Persist to disk
            self._persist_handle(handle, handle_data)
            
            # Enforce memory limits with LRU eviction
            self._ensure_memory_limit()
            
            logger.info(
                f"Stored query results in handle {handle}: {len(results)} rows, "
                f"expires in {ttl}, persisted={self.persist_to_disk}"
            )
            return handle
    
    def get_handle_data(self, handle: str) -> Optional[QueryHandleData]:
        """
        Get query handle data, returns None if expired or not found
        
        Checks memory cache first, then loads from disk if needed (lazy loading)
        """
        with measure_operation("get_handle_data", {"handle": handle}):
            if not handle or not handle.startswith("qh_"):
                logger.warning(f"Invalid handle format: {handle}")
                return None
            
            # Check memory cache first
            if handle in self.handles:
                self.cache_hits += 1
                data = self.handles[handle]
                
                # Check expiration
                if data.is_expired():
                    logger.debug(f"Handle {handle} expired")
                    del self.handles[handle]
                    self._delete_handle_from_disk(handle)
                    return None
                
                # Touch for LRU
                self._touch_handle(handle)
                return data
            
            # Not in memory, try loading from disk
            self.cache_misses += 1
            data = self._load_handle_from_disk(handle)
            
            if data:
                # Add to memory cache
                self.handles[handle] = data
                self._ensure_memory_limit()
                self._touch_handle(handle)
                logger.debug(f"Handle {handle} loaded from disk into memory")
                return data
            
            logger.debug(f"Handle {handle} not found in memory or disk")
            return None
    
    def get_results(self, handle: str, limit: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """Get query results by handle"""
        data = self.get_handle_data(handle)
        if not data:
            return None
        
        results = data.results
        if limit:
            results = results[:limit]
        
        return results
    
    def get_metadata(self, handle: str) -> Optional[QueryResultMetadata]:
        """Get query metadata by handle"""
        data = self.get_handle_data(handle)
        return data.metadata if data else None
    
    def analyze_results(
        self,
        handle: str,
        operation: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Perform analytics on cached results without loading into context
        
        Supported operations:
        - 'count': Count total rows
        - 'count_by': Count rows grouped by column
        - 'unique_values': Get unique values for a column
        - 'aggregate': Perform aggregation (sum, avg, min, max)
        - 'filter': Filter results by condition
        - 'top': Get top N results
        - 'sample': Get random sample
        """
        with measure_operation("analyze_results", {
            "handle": handle,
            "operation": operation
        }):
            data = self.get_handle_data(handle)
            if not data:
                logger.warning(f"Handle {handle} not found or expired for analysis")
                return None
            
            results = data.results
            logger.debug(f"Analyzing {len(results)} results with operation: {operation}")
        
        if operation == 'count':
            return {'count': len(results)}
        
        elif operation == 'count_by':
            column = kwargs.get('column')
            if not column:
                return {'error': 'column parameter required'}
            
            counts = defaultdict(int)
            for row in results:
                value = row.get(column, 'NULL')
                counts[str(value)] += 1
            
            return {
                'operation': 'count_by',
                'column': column,
                'groups': dict(counts),
                'total_groups': len(counts)
            }
        
        elif operation == 'unique_values':
            column = kwargs.get('column')
            limit = kwargs.get('limit', 100)
            if not column:
                return {'error': 'column parameter required'}
            
            unique_vals = set()
            for row in results:
                if column in row:
                    unique_vals.add(str(row[column]))
            
            unique_list = sorted(list(unique_vals))[:limit]
            
            return {
                'operation': 'unique_values',
                'column': column,
                'unique_count': len(unique_vals),
                'values': unique_list,
                'truncated': len(unique_vals) > limit
            }
        
        elif operation == 'aggregate':
            column = kwargs.get('column')
            agg_type = kwargs.get('type', 'sum')  # sum, avg, min, max, count
            
            if not column:
                return {'error': 'column parameter required'}
            
            values = []
            for row in results:
                if column in row:
                    try:
                        values.append(float(row[column]))
                    except (ValueError, TypeError):
                        pass
            
            if not values:
                return {'error': f'No numeric values found in column {column}'}
            
            result = {
                'operation': 'aggregate',
                'column': column,
                'type': agg_type,
                'value_count': len(values)
            }
            
            if agg_type == 'sum':
                result['value'] = sum(values)
            elif agg_type == 'avg':
                result['value'] = sum(values) / len(values)
            elif agg_type == 'min':
                result['value'] = min(values)
            elif agg_type == 'max':
                result['value'] = max(values)
            elif agg_type == 'count':
                result['value'] = len(values)
            
            return result
        
        elif operation == 'filter':
            column = kwargs.get('column')
            value = kwargs.get('value')
            operator = kwargs.get('operator', '==')
            
            if not column:
                return {'error': 'column parameter required'}
            
            filtered = []
            for row in results:
                if column not in row:
                    continue
                
                row_val = row[column]
                match = False
                
                if operator == '==':
                    match = row_val == value
                elif operator == '!=':
                    match = row_val != value
                elif operator == 'contains':
                    match = str(value).lower() in str(row_val).lower()
                elif operator == '>':
                    try:
                        match = float(row_val) > float(value)
                    except:
                        pass
                elif operator == '<':
                    try:
                        match = float(row_val) < float(value)
                    except:
                        pass
                
                if match:
                    filtered.append(row)
            
            return {
                'operation': 'filter',
                'column': column,
                'operator': operator,
                'value': value,
                'matched_count': len(filtered),
                'total_count': len(results),
                'results': filtered[:100]  # Limit to prevent context explosion
            }
        
        elif operation == 'top':
            column = kwargs.get('column')
            n = kwargs.get('n', 10)
            ascending = kwargs.get('ascending', False)
            
            if not column:
                return {'error': 'column parameter required'}
            
            # Sort by column
            sorted_results = sorted(
                [r for r in results if column in r],
                key=lambda x: x[column],
                reverse=not ascending
            )[:n]
            
            return {
                'operation': 'top',
                'column': column,
                'n': n,
                'ascending': ascending,
                'results': sorted_results
            }
        
        elif operation == 'sample':
            n = kwargs.get('n', 10)
            import random
            
            sample_size = min(n, len(results))
            sampled = random.sample(results, sample_size)
            
            return {
                'operation': 'sample',
                'sample_size': sample_size,
                'total_size': len(results),
                'results': sampled
            }
        
        else:
            return {'error': f'Unknown operation: {operation}'}
    
    def list_handles(self, include_expired: bool = False) -> List[Dict[str, Any]]:
        """List all query handles with metadata"""
        handles_list = []
        
        for handle, data in self.handles.items():
            if not include_expired and data.is_expired():
                continue
            
            handles_list.append({
                'handle': handle,
                'table_path': data.metadata.table_path,
                'row_count': data.metadata.row_count,
                'created_at': data.created_at.isoformat(),
                'expires_at': data.expires_at.isoformat(),
                'minutes_remaining': data.minutes_until_expiration(),
                'is_expired': data.is_expired(),
                'query_preview': data.metadata.query[:100] + '...' if len(data.metadata.query) > 100 else data.metadata.query
            })
        
        return handles_list
    
    def validate_handle(self, handle: str) -> Dict[str, Any]:
        """Validate a query handle and return detailed info"""
        data = self.get_handle_data(handle)
        
        if not data:
            return {
                'is_valid': False,
                'valid': False,
                'error': 'Handle not found or expired',
                'handle': handle
            }
        
        return {
            'is_valid': True,
            'valid': True,
            'handle': handle,
            'table_path': data.metadata.table_path,
            'row_count': data.metadata.row_count,
            'column_count': len(data.metadata.columns),
            'columns': data.metadata.columns,
            'created_at': data.created_at.isoformat(),
            'expires_at': data.expires_at.isoformat(),
            'minutes_remaining': data.minutes_until_expiration(),
            'query': data.metadata.query,
            'execution_time_ms': data.metadata.execution_time_ms,
            'result_hash': data.result_hash
        }
    
    def get_cached_results(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get cached results for a handle
        
        Returns:
            Dictionary with 'results' and 'columns' keys, or None if handle not found
        """
        try:
            data = self.get_handle_data(handle)
            
            if not data:
                return None
            
            # Safely access metadata attributes
            metadata = getattr(data, 'metadata', None)
            if not metadata:
                logger.error(f"Handle {handle} has no metadata")
                return None
            
            return {
                'results': getattr(data, 'results', []),
                'columns': getattr(metadata, 'columns', []),
                'row_count': getattr(metadata, 'row_count', 0),
                'table_path': getattr(metadata, 'table_path', 'unknown'),
                'metadata': {
                    'query': getattr(metadata, 'query', ''),
                    'cluster': getattr(metadata, 'cluster', ''),
                    'database': getattr(metadata, 'database', ''),
                    'table': getattr(metadata, 'table', ''),
                    'execution_time_ms': getattr(metadata, 'execution_time_ms', 0),
                    'timestamp': getattr(metadata, 'timestamp', '')
                }
            }
        except Exception as e:
            logger.error(f"Error getting cached results for handle {handle}: {e}", exc_info=True)
            return None
    
    # ============================================================================
    # PERSISTENCE METHODS
    # ============================================================================
    
    def _get_handle_path(self, handle: str) -> Path:
        """Get file path for a handle"""
        return self.cache_dir / f"{handle}.pkl"
    
    def _persist_handle(self, handle: str, data: QueryHandleData):
        """Persist handle to disk"""
        if not self.persist_to_disk:
            return
        
        try:
            path = self._get_handle_path(handle)
            with open(path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            self.disk_writes += 1
            logger.debug(f"Persisted handle {handle} to disk")
        except Exception as e:
            logger.error(f"Failed to persist handle {handle}: {e}")
    
    def _load_handle_from_disk(self, handle: str) -> Optional[QueryHandleData]:
        """Load handle from disk"""
        if not self.persist_to_disk:
            return None
        
        try:
            path = self._get_handle_path(handle)
            if not path.exists():
                return None
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            # Check if expired
            if data.is_expired():
                logger.debug(f"Loaded handle {handle} from disk but it's expired")
                path.unlink()  # Delete expired file
                return None
            
            self.disk_reads += 1
            logger.debug(f"Loaded handle {handle} from disk")
            return data
        except Exception as e:
            logger.error(f"Failed to load handle {handle} from disk: {e}")
            return None
    
    def _delete_handle_from_disk(self, handle: str):
        """Delete handle from disk"""
        if not self.persist_to_disk:
            return
        
        try:
            path = self._get_handle_path(handle)
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted handle {handle} from disk")
        except Exception as e:
            logger.error(f"Failed to delete handle {handle} from disk: {e}")
    
    def _load_persisted_handles(self):
        """Load all persisted handles from disk on startup"""
        if not self.persist_to_disk or not self.cache_dir.exists():
            return
        
        loaded_count = 0
        expired_count = 0
        
        logger.info(f"Loading persisted handles from {self.cache_dir}")
        
        for path in self.cache_dir.glob("qh_*.pkl"):
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                
                # Check expiration
                if data.is_expired():
                    expired_count += 1
                    path.unlink()  # Delete expired file
                    continue
                
                # Add to memory cache
                self.handles[data.handle] = data
                loaded_count += 1
                
                # Apply LRU limit
                if len(self.handles) >= self.max_memory_handles:
                    self._evict_lru()
                
            except Exception as e:
                logger.error(f"Failed to load handle from {path}: {e}")
        
        logger.info(
            f"Loaded {loaded_count} handles from disk, "
            f"deleted {expired_count} expired handles"
        )
    
    def _evict_lru(self):
        """Evict least recently used handle from memory (but keep on disk)"""
        if not self.handles:
            return
        
        # Get oldest handle (first in OrderedDict)
        oldest_handle = next(iter(self.handles))
        logger.debug(f"Evicting LRU handle from memory: {oldest_handle}")
        del self.handles[oldest_handle]
    
    def _ensure_memory_limit(self):
        """Ensure memory doesn't exceed max_memory_handles"""
        while len(self.handles) > self.max_memory_handles:
            self._evict_lru()
    
    def _touch_handle(self, handle: str):
        """Move handle to end of OrderedDict (mark as recently used)"""
        if handle in self.handles:
            self.handles.move_to_end(handle)
    
    # ============================================================================
    # HANDLE LIFECYCLE
    # ============================================================================
    
    def cleanup_expired(self) -> int:
        """Remove expired handles from memory and disk, returns count of removed handles"""
        expired = []
        
        # Clean memory
        for handle, data in list(self.handles.items()):
            if data.is_expired():
                expired.append(handle)
                del self.handles[handle]
                self._delete_handle_from_disk(handle)
        
        # Clean disk files not in memory
        if self.persist_to_disk and self.cache_dir.exists():
            for path in self.cache_dir.glob("qh_*.pkl"):
                handle = path.stem
                if handle not in self.handles:
                    try:
                        with open(path, 'rb') as f:
                            data = pickle.load(f)
                        if data.is_expired():
                            path.unlink()
                            expired.append(handle)
                    except Exception as e:
                        logger.error(f"Failed to check expiration for {path}: {e}")
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired handles")
        
        return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        active = sum(1 for d in self.handles.values() if not d.is_expired())
        expired = sum(1 for d in self.handles.values() if d.is_expired())
        
        total_rows = sum(d.metadata.row_count for d in self.handles.values())
        avg_rows = total_rows / len(self.handles) if self.handles else 0
        
        # Count disk files
        disk_handles = 0
        if self.persist_to_disk and self.cache_dir.exists():
            disk_handles = len(list(self.cache_dir.glob("qh_*.pkl")))
        
        return {
            'server_uptime_seconds': (datetime.now() - self.server_start_time).total_seconds(),
            'memory_handles': len(self.handles),
            'disk_handles': disk_handles,
            'max_memory_handles': self.max_memory_handles,
            'active_handles': active,
            'expired_handles': expired,
            'total_handles_created': self.total_handles_created,
            'total_queries_executed': self.total_queries_executed,
            'total_rows_cached': total_rows,
            'average_rows_per_handle': avg_rows,
            'persistence_enabled': self.persist_to_disk,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'disk_writes': self.disk_writes,
            'disk_reads': self.disk_reads,
            'cache_hit_rate': (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0
            )
        }
    
    def _create_item_context(self, results: List[Dict[str, Any]]) -> List[ItemContext]:
        """Create rich context for each result item"""
        return [
            ItemContext(index=i, row_data=row, tags=[])
            for i, row in enumerate(results)
        ]
    
    def _create_selection_metadata(
        self, 
        results: List[Dict[str, Any]], 
        columns: List[Dict[str, str]]
    ) -> SelectionMetadata:
        """Create metadata to help with selection operations"""
        if not results:
            return SelectionMetadata(
                total_items=0,
                selectable_indices=[],
                available_columns=[],
                column_types={}
            )
        
        return SelectionMetadata(
            total_items=len(results),
            selectable_indices=list(range(len(results))),
            available_columns=[col['name'] for col in columns],
            column_types={col['name']: col['type'] for col in columns}
        )
    
    def get_items_by_indices(
        self, 
        handle: str, 
        indices: List[int]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Select specific items by their indices
        
        Args:
            handle: Query handle
            indices: Zero-based indices to select
            
        Returns:
            Selected items or None if handle invalid
        """
        with measure_operation("get_items_by_indices", {
            "handle": handle,
            "index_count": len(indices)
        }):
            data = self.get_handle_data(handle)
            if not data:
                logger.warning(f"Handle {handle} not found or expired")
                return None
            
            # Validate indices
            valid_indices = [i for i in indices if 0 <= i < len(data.results)]
            if len(valid_indices) != len(indices):
                invalid = [i for i in indices if i < 0 or i >= len(data.results)]
                logger.warning(f"Invalid indices for handle {handle}: {invalid}")
            
            # Select items
            selected = [data.results[i] for i in valid_indices]
            logger.info(f"Selected {len(selected)} items by indices from handle {handle}")
            return selected
    
    def get_items_by_criteria(
        self, 
        handle: str, 
        criteria: SelectionCriteria
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Select items matching criteria
        
        Args:
            handle: Query handle
            criteria: Selection criteria
            
        Returns:
            Matching items or None if handle invalid
        """
        with measure_operation("get_items_by_criteria", {"handle": handle}):
            data = self.get_handle_data(handle)
            if not data:
                logger.warning(f"Handle {handle} not found or expired")
                return None
            
            selected = []
            
            for item_ctx in (data.item_context or []):
                row = item_ctx.row_data
                matches = True
                
                # Apply column filters
                if criteria.column_filters:
                    for col, value in criteria.column_filters.items():
                        if row.get(col) != value:
                            matches = False
                            break
                
                # Apply contains filters
                if matches and criteria.column_contains:
                    for col, substring in criteria.column_contains.items():
                        if substring.lower() not in str(row.get(col, '')).lower():
                            matches = False
                            break
                
                # Apply range filters
                if matches and criteria.column_range:
                    for col, (min_val, max_val) in criteria.column_range.items():
                        try:
                            val = float(row.get(col, 0))
                            if not (min_val <= val <= max_val):
                                matches = False
                                break
                        except (ValueError, TypeError):
                            matches = False
                            break
                
                # Apply tag filters
                if matches and criteria.tags:
                    if not any(tag in item_ctx.tags for tag in criteria.tags):
                        matches = False
                
                if matches:
                    selected.append(row)
                    
                    # Apply limit
                    if criteria.limit and len(selected) >= criteria.limit:
                        break
            
            logger.info(f"Selected {len(selected)} items by criteria from handle {handle}")
            return selected
    
    def tag_items(
        self, 
        handle: str, 
        indices: List[int], 
        tags: List[str]
    ) -> bool:
        """
        Add tags to specific items for later filtering
        
        Args:
            handle: Query handle
            indices: Items to tag
            tags: Tags to add
            
        Returns:
            Success status
        """
        data = self.get_handle_data(handle)
        if not data or not data.item_context:
            return False
        
        for idx in indices:
            if 0 <= idx < len(data.item_context):
                data.item_context[idx].tags.extend(tags)
        
        logger.info(f"Tagged {len(indices)} items in handle {handle} with tags: {tags}")
        return True
    
    def get_item_context(self, handle: str, index: int) -> Optional[ItemContext]:
        """Get rich context for a specific item"""
        data = self.get_handle_data(handle)
        if not data or not data.item_context:
            return None
        
        if 0 <= index < len(data.item_context):
            return data.item_context[index]
        
        return None
    
    def get_selection_preview(
        self, 
        handle: str, 
        criteria: Optional[SelectionCriteria] = None,
        max_preview: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get a preview of what would be selected without returning all data
        
        Args:
            handle: Query handle
            criteria: Optional selection criteria
            max_preview: Max items to include in preview
            
        Returns:
            Preview information
        """
        data = self.get_handle_data(handle)
        if not data:
            return None
        
        if criteria:
            selected = self.get_items_by_criteria(handle, criteria)
        else:
            selected = data.results
        
        if not selected:
            return {
                'handle': handle,
                'total_matching': 0,
                'preview_items': [],
                'available_columns': data.selection_metadata.available_columns if data.selection_metadata else []
            }
        
        return {
            'handle': handle,
            'total_matching': len(selected),
            'preview_items': selected[:max_preview],
            'truncated': len(selected) > max_preview,
            'available_columns': data.selection_metadata.available_columns if data.selection_metadata else []
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        active = sum(1 for d in self.handles.values() if not d.is_expired())
        expired = sum(1 for d in self.handles.values() if d.is_expired())
        
        total_rows = sum(d.metadata.row_count for d in self.handles.values())
        avg_rows = total_rows / len(self.handles) if self.handles else 0
        
        return {
            'server_uptime_seconds': (datetime.now() - self.server_start_time).total_seconds(),
            'total_handles': len(self.handles),
            'active_handles': active,
            'expired_handles': expired,
            'total_handles_created': self.total_handles_created,
            'total_queries_executed': self.total_queries_executed,
            'total_rows_cached': total_rows,
            'average_rows_per_handle': avg_rows
        }
    
    def clear_all(self):
        """Clear all handles (for testing)"""
        self.handles.clear()


# Singleton instance
_query_handle_service = QueryHandleService()


def get_query_handle_service() -> QueryHandleService:
    """Get the singleton query handle service instance"""
    return _query_handle_service
