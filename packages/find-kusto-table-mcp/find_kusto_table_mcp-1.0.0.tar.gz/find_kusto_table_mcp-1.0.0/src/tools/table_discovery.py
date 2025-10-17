"""
Smart table discovery and search tools with advanced caching.

Provides intelligent table search with lazy schema loading, result caching,
and integration with the schema cache service for optimal performance.
"""

import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from collections import OrderedDict

from ..core.exceptions import ValidationError, SearchError
from ..core.logging_config import get_logger
from ..core.performance import measure_operation, record_cache_hit, record_cache_miss
from ..services.schema_cache_service import get_schema_cache_service
from ..utils.kusto_client import get_connection_manager
from ..utils.helpers import calculate_similarity, truncate_string, safe_json_dumps

logger = get_logger("discovery")


class SmartTableDiscovery:
    """
    Smart table discovery with dynamic Kusto queries and caching
    
    Key features:
    - Dynamic table discovery from Kusto clusters
    - LRU cache for search results (fast repeated searches)
    - Lazy schema loading (only fetch when requested)
    - Integration with schema cache service
    - Fuzzy matching and keyword search
    """
    
    def __init__(self, search_cache_ttl_minutes: int = 30, max_cache_entries: int = 100):
        self.schema_cache = get_schema_cache_service()
        self.connection_manager = get_connection_manager()
        
        # LRU cache for search results
        self.cached_searches: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_cache_entries = max_cache_entries
        self.search_cache_ttl = timedelta(minutes=search_cache_ttl_minutes)
        
        # Available tables cache (cluster -> database -> [tables])
        self.available_tables: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self.tables_loaded = False
        
        # Statistics
        self.search_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info("Initialized SmartTableDiscovery with dynamic discovery")
    
    async def _load_tables_from_cluster(self, cluster: str) -> Dict[str, List[Dict[str, Any]]]:
        """Dynamically load tables from a Kusto cluster"""
        try:
            cluster_client = self.connection_manager.get_cluster_client(cluster)
        except Exception as e:
            logger.error(f"Failed to create cluster client for {cluster}: {e}")
            logger.info("Hint: Make sure you're logged in to Azure CLI with 'az login' or have proper authentication configured")
            return {}
        
        try:
            # Get list of databases
            logger.info(f"Fetching databases from cluster {cluster}...")
            databases = await cluster_client.list_databases()
            logger.info(f"Found {len(databases)} databases in {cluster}")
            
            tables_by_db = {}
            for database in databases:
                try:
                    # Get tables in this database
                    logger.debug(f"Fetching tables from {cluster}.{database}...")
                    tables = await cluster_client.list_tables(database)
                    tables_by_db[database] = tables
                    logger.info(f"Loaded {len(tables)} tables from {cluster}.{database}")
                except Exception as e:
                    logger.warning(f"Failed to load tables from {cluster}.{database}: {e}")
                    tables_by_db[database] = []
            
            total_tables = sum(len(tables) for tables in tables_by_db.values())
            logger.info(f"Successfully loaded {total_tables} tables from {cluster} across {len(tables_by_db)} databases")
            return tables_by_db
        except Exception as e:
            logger.error(f"Failed to load databases from {cluster}: {e}")
            logger.info("Hint: Check network connectivity and authentication. Try running 'az login' if using Azure CLI authentication.")
            return {}
    
    async def _ensure_tables_loaded(self, clusters: Optional[List[str]] = None):
        """Ensure tables are loaded from specified clusters"""
        if not clusters:
            # Load from configured clusters in connection_strings.json
            clusters = self._get_configured_clusters()
            if not clusters:
                logger.warning("No clusters configured, defaulting to mock cluster")
                clusters = ["mock-cluster"]
        
        for cluster in clusters:
            if cluster not in self.available_tables:
                logger.info(f"Loading tables from cluster: {cluster}")
                self.available_tables[cluster] = await self._load_tables_from_cluster(cluster)
        
        self.tables_loaded = True
    
    def _get_configured_clusters(self) -> List[str]:
        """Get list of configured clusters from connection strings"""
        try:
            import json
            import os
            
            # Navigate from src/tools/table_discovery.py to project root
            # __file__ is src/tools/table_discovery.py
            # dirname(__file__) is src/tools/
            # dirname(dirname(__file__)) is src/
            # dirname(dirname(dirname(__file__))) is project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            conn_file = os.path.join(project_root, 'cache', 'connection_strings.json')
            
            logger.debug(f"Looking for connection strings at: {conn_file}")
            
            if os.path.exists(conn_file):
                with open(conn_file, 'r') as f:
                    data = json.load(f)
                    # Extract cluster names from the config
                    clusters = []
                    for cluster_info in data.get('clusters', []):
                        cluster_name = cluster_info.get('name', '')
                        if cluster_name:
                            clusters.append(cluster_name)
                    
                    logger.info(f"Found {len(clusters)} configured clusters: {clusters}")
                    return clusters
            else:
                logger.warning(f"Connection strings file not found at: {conn_file}")
        except Exception as e:
            logger.error(f"Failed to load configured clusters: {e}")
        
        return []
    
    def _make_cache_key(self, query: str, method: str, limit: int, fetch_schema: bool) -> str:
        """Generate cache key for search results"""
        return f"{query.lower()}:{method}:{limit}:{fetch_schema}"
    
    def _evict_lru_cache(self):
        """Evict least recently used cache entry if needed"""
        if len(self.cached_searches) >= self.max_cache_entries:
            self.cached_searches.popitem(last=False)
    
    async def search_tables(
        self,
        query: str,
        method: str = "hybrid",
        limit: int = 10,
        fetch_schema: bool = True,
        cache_results: bool = True,
        clusters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for tables using natural language query with dynamic discovery
        
        Args:
            query: Natural language search query
            method: Search method (keyword, fuzzy, contextual, hybrid)
            limit: Maximum results to return
            fetch_schema: Whether to fetch schema for results (lazy)
            cache_results: Whether to cache results
            clusters: List of clusters to search (defaults to configured clusters)
            
        Returns:
            Dictionary with search results and metadata
        """
        with measure_operation("search_tables", {
            "query": query,
            "method": method,
            "limit": limit,
            "fetch_schema": fetch_schema
        }):
            self.search_count += 1
            
            # If no clusters specified, use configured clusters
            if not clusters:
                clusters = self._get_configured_clusters()
            
            # Ensure tables are loaded
            await self._ensure_tables_loaded(clusters)
            
            # Check cache first
            if cache_results:
                cache_key = self._make_cache_key(query, method, limit, fetch_schema)
                
                if cache_key in self.cached_searches:
                    cached_entry = self.cached_searches[cache_key]
                    cached_at = cached_entry.get("cached_at")
                    
                    # Check if cache is still valid
                    if cached_at:
                        age = datetime.now() - datetime.fromisoformat(cached_at)
                        if age < self.search_cache_ttl:
                            # Move to end (mark as recently used)
                            self.cached_searches.move_to_end(cache_key)
                            self.cache_hits += 1
                            record_cache_hit("table_search")
                            logger.debug(f"Cache hit for search: {query[:50]}")
                            return cached_entry["results"]
                
                self.cache_misses += 1
                record_cache_miss("table_search")
            
            # Perform dynamic search
            try:
                # Search across all loaded tables
                raw_results = self._search_loaded_tables(query, method, limit)
                
                # Enrich results with schema if requested
                enriched_results = []
                for result in raw_results:
                    enriched = result.copy()
                    
                    if fetch_schema:
                        cluster = result["cluster"]
                        database = result["database"]
                        table = result["table"]
                        
                        # Fetch schema lazily from cache
                        schema_info = await self.schema_cache.get_schema(
                            cluster, database, table
                        )
                        
                        if schema_info:
                            # schema_info is a SchemaMetadata object, not a dict
                            enriched["schema"] = schema_info.columns
                            enriched["primary_time_column"] = schema_info.primary_time_column
                            enriched["numeric_columns"] = schema_info.numeric_columns
                            enriched["string_columns"] = schema_info.string_columns
                            enriched["time_columns"] = schema_info.time_columns
                            enriched["notes"] = schema_info.notes if schema_info.notes else []
                            enriched["has_schema"] = True
                        else:
                            enriched["has_schema"] = False
                            enriched["notes"] = []
                    
                    enriched_results.append(enriched)
                
                search_results = {
                    "results": enriched_results,
                    "total_results": len(enriched_results),
                    "query": query,
                    "method": method,
                    "searched_at": datetime.now().isoformat(),
                    "from_cache": False
                }
                
                # Cache results
                if cache_results:
                    self._evict_lru_cache()
                    self.cached_searches[cache_key] = {
                        "results": search_results,
                        "cached_at": datetime.now().isoformat()
                    }
                
                logger.info(f"Search completed: '{query}' -> {len(enriched_results)} results")
                return search_results
                
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                raise SearchError(f"Table search failed: {str(e)}", query=query)
    
    def _search_loaded_tables(self, query: str, method: str, limit: int) -> List[Dict[str, Any]]:
        """
        Search loaded tables using specified method
        
        Args:
            query: Search query
            method: Search method (keyword, fuzzy, contextual, hybrid)
            limit: Maximum results
            
        Returns:
            List of matching tables with scores
        """
        query_lower = query.lower()
        query_words = query_lower.split()
        
        results = []
        
        # Search across all clusters and databases
        for cluster, databases in self.available_tables.items():
            for database, tables in databases.items():
                for table_info in tables:
                    table_name = table_info.get("TableName", "")
                    folder = table_info.get("Folder", "")
                    doc_string = table_info.get("DocString", "")
                    
                    score = 0.0
                    
                    # Score based on method
                    if method in ("keyword", "hybrid"):
                        score += self._keyword_score(
                            query_lower, query_words, 
                            table_name.lower(), folder.lower(), doc_string.lower()
                        )
                    
                    if method in ("fuzzy", "hybrid"):
                        score += self._fuzzy_score(query_lower, table_name.lower())
                    
                    if method == "contextual":
                        # Contextual search uses both keyword and fuzzy with different weights
                        score += self._keyword_score(
                            query_lower, query_words,
                            table_name.lower(), folder.lower(), doc_string.lower()
                        ) * 0.6
                        score += self._fuzzy_score(query_lower, table_name.lower()) * 0.4
                    
                    # Only include if score is above threshold
                    if score > 0:
                        results.append({
                            "cluster": cluster,
                            "database": database,
                            "table": table_name,
                            "folder": folder,
                            "description": doc_string,
                            "score": score,
                            "relevance": min(score / 10.0, 1.0)  # Normalize to 0-1
                        })
        
        # Sort by score descending and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _keyword_score(
        self, 
        query: str, 
        query_words: List[str],
        table_name: str,
        folder: str,
        doc_string: str
    ) -> float:
        """Calculate keyword-based score"""
        score = 0.0
        
        # Exact table name match (highest priority)
        if query == table_name:
            score += 10.0
        
        # Table name contains query
        elif query in table_name:
            score += 7.0
        
        # Table name starts with query
        elif table_name.startswith(query):
            score += 6.0
        
        # Individual word matches
        for word in query_words:
            if len(word) > 2:  # Skip very short words
                if word in table_name:
                    score += 2.0
                if word in folder:
                    score += 1.0
                if word in doc_string:
                    score += 0.5
        
        return score
    
    def _fuzzy_score(self, query: str, table_name: str) -> float:
        """
        Calculate fuzzy matching score using Levenshtein-like distance
        
        Returns score between 0 (no match) and 5 (close match)
        """
        if not query or not table_name:
            return 0.0
        
        # Simple character-based similarity
        query_set = set(query)
        table_set = set(table_name)
        
        if not query_set:
            return 0.0
        
        # Jaccard similarity of character sets
        intersection = len(query_set & table_set)
        union = len(query_set | table_set)
        char_similarity = intersection / union if union > 0 else 0
        
        # Subsequence matching (how many query chars appear in order)
        subseq_score = 0
        query_idx = 0
        for char in table_name:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        subseq_score = query_idx / len(query) if len(query) > 0 else 0
        
        # Length penalty (prefer similar length matches)
        len_diff = abs(len(query) - len(table_name))
        len_penalty = max(0, 1.0 - (len_diff / max(len(query), len(table_name))))
        
        # Combined fuzzy score
        fuzzy = (char_similarity * 0.4 + subseq_score * 0.4 + len_penalty * 0.2) * 5.0
        
        return fuzzy
    
    async def get_table_details(
        self,
        cluster: str,
        database: str,
        table: str,
        include_sample: bool = False,
        sample_size: int = 5
    ) -> Dict[str, Any]:
        """
        Get comprehensive details about a specific table
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            include_sample: Whether to include sample data
            sample_size: Number of sample rows to fetch
            
        Returns:
            Dictionary with table details, schema, and optional sample data
        """
        with measure_operation("get_table_details", {
            "table": f"{cluster}.{database}.{table}",
            "include_sample": include_sample
        }):
            table_path = f"{cluster}.{database}.{table}"
            
            # Get schema from cache
            schema = await self.schema_cache.get_schema(
                cluster, database, table, fetch_if_missing=True
            )
            
            if not schema:
                raise ValidationError(f"Unable to fetch schema for {table_path}")
            
            details = {
                'table_path': table_path,
                'cluster': cluster,
                'database': database,
                'table': table,
                'schema': {
                    'columns': schema.columns,
                    'time_columns': schema.time_columns,
                    'primary_time_column': schema.primary_time_column,
                    'numeric_columns': schema.numeric_columns,
                    'string_columns': schema.string_columns,
                    'column_count': len(schema.columns)
                },
                'notes': schema.notes if schema.notes else [],
                'metadata': {
                    'fetched_at': schema.fetched_at.isoformat(),
                    'cache_hits': schema.cache_hits
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Add example queries
            details['example_queries'] = self._generate_example_queries(
                table, schema
            )
            
            # Add sample data if requested
            if include_sample:
                try:
                    sample_data = await self.connection_manager.sample_table(
                        cluster, database, table, sample_size
                    )
                    details['sample_data'] = {
                        'rows': sample_data.get('sample_rows', []),
                        'sample_size': len(sample_data.get('sample_rows', [])),
                        'sampled_at': sample_data.get('sampled_at', datetime.now().isoformat())
                    }
                except Exception as e:
                    logger.warning(f"Failed to fetch sample data: {e}")
                    details['sample_data'] = {'error': str(e)}
            
            logger.info(f"Retrieved details for {table_path}")
            return details
    
    def _generate_example_queries(
        self,
        table: str,
        schema: Any
    ) -> List[Dict[str, str]]:
        """Generate example queries for a table"""
        examples = []
        
        # Basic query
        examples.append({
            'name': 'Basic query',
            'description': 'Get recent records',
            'query': f'{table}\\n| take 100'
        })
        
        # Time-based query if time column exists
        if schema.primary_time_column or schema.time_columns:
            time_col = schema.primary_time_column or schema.time_columns[0]
            examples.append({
                'name': 'Recent data (1 hour)',
                'description': 'Filter by time range',
                'query': f'{table}\\n| where {time_col} > ago(1h)\\n| take 100'
            })
        
        # Aggregation query if numeric columns exist
        if schema.numeric_columns and (schema.primary_time_column or schema.time_columns):
            time_col = schema.primary_time_column or schema.time_columns[0]
            numeric_col = schema.numeric_columns[0]
            examples.append({
                'name': 'Aggregation by time',
                'description': 'Aggregate numeric column over time',
                'query': f'{table}\\n| where {time_col} > ago(1h)\\n| summarize avg({numeric_col}) by bin({time_col}, 5m)'
            })
        
        # Grouping query if string columns exist
        if schema.string_columns and len(schema.string_columns) > 0:
            group_col = schema.string_columns[0]
            examples.append({
                'name': 'Count by category',
                'description': f'Group and count by {group_col}',
                'query': f'{table}\\n| summarize count() by {group_col}\\n| order by count_ desc\\n| take 10'
            })
        
        return examples
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0.0
        total_searches = self.cache_hits + self.cache_misses
        if total_searches > 0:
            hit_rate = (self.cache_hits / total_searches) * 100
        
        return {
            'search_count': self.search_count,
            'cached_searches': len(self.cached_searches),
            'max_cache_entries': self.max_cache_entries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'loaded_clusters': len(self.available_tables),
            'tables_loaded': self.tables_loaded
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics (alias for get_cache_stats)"""
        stats = self.get_cache_stats()
        stats['cache_hit_rate'] = stats['hit_rate_percent'] / 100.0
        return stats
    
    def clear_search_cache(self):
        """Clear the search results cache"""
        cleared_count = len(self.cached_searches)
        self.cached_searches.clear()
        logger.info(f"Cleared {cleared_count} cached search results")
        return cleared_count
    
    def get_tables_by_cluster(self, cluster: str) -> List[str]:
        """Get all tables for a specific cluster"""
        return self.tables_by_cluster.get(cluster, [])
    
    def get_all_clusters(self) -> List[str]:
        """Get list of all available clusters"""
        return list(self.tables_by_cluster.keys())
    
    def table_exists(self, cluster: str, database: str, table: str) -> bool:
        """Check if a table exists in the registry"""
        table_path = f"{cluster}.{database}.{table}"
        return table_path in self.available_tables


def create_smart_table_discovery() -> SmartTableDiscovery:
    """Create and configure smart table discovery instance"""
    return SmartTableDiscovery()

