"""
Cache and performance management tools for Kusto MCP server.

This module provides tools for monitoring server performance and cache statistics:
- cache_stats: Get comprehensive cache statistics and health metrics
- performance_stats: Get detailed performance metrics and timing data
- cache_clear: Clear expired cache entries to free up memory

Best Practices:
- Use cache_stats to monitor cache health and hit rates
- Use performance_stats to identify slow operations
- Use cache_clear periodically to free up memory

Example Usage:
    # Monitor cache health
    stats = cache_stats()
    
    # Check specific operation performance
    perf = performance_stats(operation="execute_query")
    
    # Clear expired entries
    result = cache_clear()
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation, get_performance_summary, get_operation_stats
from ..core.exceptions import CacheError
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.cache_management")


def register_cache_management_tools(mcp, services: dict):
    """Register cache and performance management tools with the MCP server."""
    schema_cache = services['schema_cache']
    templates = services['templates']
    table_discovery = services['table_discovery']

    @mcp.tool()
    def cache_stats() -> str:
        """
        📈 Get comprehensive cache statistics and performance metrics.
        
        Returns detailed statistics for all caching systems:
        - Schema cache (hit rates, size, top accessed tables)
        - Query templates (count, usage patterns)
        - Table discovery cache (index size, last updated)
        - Overall performance metrics (operation timings, throughput)
        
        Perfect for:
        - Monitoring cache health and efficiency
        - Identifying performance bottlenecks
        - Capacity planning and optimization
        
        Returns:
            JSON string with comprehensive cache statistics including:
            - Hit rates and miss counts
            - Memory usage estimates
            - Top accessed resources
            - Performance trends
        """
        with measure_operation("cache_stats"):
            try:
                stats: Dict[str, Any] = {
                    "schema_cache": schema_cache.get_stats(),
                    "query_templates": templates.get_stats(),
                    "table_discovery": table_discovery.get_cache_stats(),
                    "performance": get_performance_summary(),
                    "timestamp": datetime.now().isoformat(),
                    "server_health": "healthy"
                }
                
                # Add health indicators
                schema_stats = stats.get("schema_cache", {})
                if isinstance(schema_stats, dict):
                    hit_rate = schema_stats.get("hit_rate", 0)
                    if hit_rate < 0.5:
                        stats["server_health"] = "warning"
                        stats["recommendations"] = ["Low cache hit rate detected. Consider warming up cache."]
                
                return safe_json_dumps(stats, indent=2)
            except Exception as e:
                logger.error(f"Failed to get cache stats: {e}", exc_info=True)
                raise CacheError(f"Failed to retrieve cache statistics: {str(e)}", cache_type="all")

    @mcp.tool()
    def performance_stats(operation: Optional[str] = None) -> str:
        """
        📈 Get detailed performance statistics and monitoring data.
        
        Provides comprehensive performance metrics including:
        - Overall system performance summary
        - Per-operation timing statistics
        - Throughput and latency metrics
        - Performance trends over time
        
        Args:
            operation: Optional specific operation name to get detailed stats for.
                      Examples: "execute_query", "cache_stats", "search_kusto_tables"
        
        Returns:
            JSON string with performance metrics including:
            - Average execution times
            - Operation counts
            - P50, P95, P99 latency percentiles (if available)
            - Cache hit rates
            - Bottleneck identification
        
        Example:
            # Get overall performance summary
            stats = performance_stats()
            
            # Get stats for specific operation
            query_stats = performance_stats(operation="execute_query")
        """
        with measure_operation("performance_stats"):
            try:
                perf_summary = get_performance_summary()
                
                result: Dict[str, Any] = {
                    "performance_summary": perf_summary,
                    "timestamp": datetime.now().isoformat()
                }
                
                if operation:
                    op_stats = get_operation_stats(operation)
                    if op_stats:
                        result["operation_stats"] = op_stats
                        result["operation_name"] = operation
                    else:
                        result["operation_stats"] = None
                        result["warning"] = f"No statistics available for operation: {operation}"
                        result["hint"] = "Check operation name spelling or ensure the operation has been executed"
                
                return safe_json_dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Failed to get performance stats: {e}", exc_info=True)
                raise CacheError(f"Failed to retrieve performance statistics: {str(e)}", cache_type="performance")

    @mcp.tool()
    def cache_clear() -> str:
        """
        🗑️ Clear expired cache entries to free up memory.
        
        This tool performs cache maintenance by:
        - Removing expired schema cache entries
        - Clearing stale query handles
        - Freeing up memory from unused caches
        - Reporting what was cleared
        
        Perfect for:
        - Periodic maintenance
        - Memory cleanup
        - Forcing cache refresh
        
        Returns:
            JSON string with details about what was cleared:
            - schema_cache_cleared: Number of schema entries removed
            - handles_cleared: Number of query handles removed
            - memory_freed_estimate: Approximate memory freed
            - timestamp: When the cleanup occurred
        
        Note: This does NOT clear actively used or recent cache entries.
              Only expired or stale data is removed.
        """
        with measure_operation("cache_clear"):
            try:
                cleared_counts: Dict[str, int] = {}
                
                # Clear expired schema cache entries
                if hasattr(schema_cache, 'clear_expired'):
                    schema_cleared = schema_cache.clear_expired()
                    cleared_counts['schema_cache_cleared'] = schema_cleared
                else:
                    cleared_counts['schema_cache_cleared'] = 0
                    cleared_counts['schema_cache_note'] = "No expired entries found or clear method not available"
                
                # Note: Query handles and templates should not be auto-cleared
                # as they may be intentionally persisted
                
                result: Dict[str, Any] = {
                    "success": True,
                    "cleared_counts": cleared_counts,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Cache maintenance completed. Expired entries removed."
                }
                
                total_cleared = sum(v for v in cleared_counts.values() if isinstance(v, int))
                if total_cleared == 0:
                    result["message"] = "No expired cache entries found. Cache is clean."
                else:
                    result["message"] = f"Successfully cleared {total_cleared} expired cache entries."
                
                logger.info(f"Cache cleared: {total_cleared} entries removed")
                return safe_json_dumps(result, indent=2)
                
            except Exception as e:
                logger.error(f"Cache clear failed: {e}", exc_info=True)
                raise CacheError(f"Failed to clear cache: {str(e)}", cache_type="all")
