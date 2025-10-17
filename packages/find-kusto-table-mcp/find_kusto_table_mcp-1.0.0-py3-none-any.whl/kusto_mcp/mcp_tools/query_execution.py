"""
Query execution tools for Kusto MCP server.

This module provides tools for executing KQL queries and managing query results:
- execute_query: Execute queries with direct results and automatic file export
"""

from typing import Optional, Any
from datetime import datetime
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.query_execution")


def register_query_execution_tools(mcp, services: dict):
    """Register query execution tools with the MCP server."""
    connection_manager = services['connection_manager']

    @mcp.tool()
    async def execute_query(
        cluster: str,
        database: str,
        table: str,
        query: str,
        limit: int = 100,
        ctx: Context = None
    ) -> str:
        """
        🚀 Execute a KQL query and get results directly.
        
        This is the PRIMARY query execution tool. Returns results inline (up to 100 rows for preview)
        and automatically exports full results to file if > 100 rows.
        
        Simple workflow:
        1. execute_query() → get results immediately
        2. If > 100 rows, full results exported to exports/ directory
        3. Use the export_path to access full results
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name (for tracking)
            query: KQL query to execute
            limit: Row limit (default: 100, max: 10000)
        
        Returns:
            JSON with:
            - success: Execution status
            - results: Query results (first 100 rows for preview)
            - row_count: Number of rows returned
            - columns: Column names and types
            - execution_time_ms: Query execution time
            - export_path: Path to full results file (if > 100 rows)
        """
        if ctx:
            await ctx.info(f"Executing query on {cluster}.{database}.{table}")
        
        with measure_operation("execute_query"):
            try:
                # Validate limit
                limit = min(limit, 10000)
                
                # Add LIMIT to query if not already present
                query_with_limit = query
                if limit and "take" not in query.lower() and "limit" not in query.lower():
                    query_with_limit = f"{query}\n| take {limit}"
                
                # Execute query on real Kusto cluster
                start_time = datetime.now()
                results, columns = await connection_manager.execute_query(
                    cluster=cluster,
                    database=database,
                    query=query_with_limit,
                    timeout_seconds=None
                )
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                row_count = len(results)
                
                if ctx:
                    await ctx.info(f"Query completed: {row_count} rows in {execution_time_ms:.0f}ms")
                
                # Build response
                result = {
                    "success": True,
                    "row_count": row_count,
                    "columns": [col["name"] for col in columns],
                    "column_types": {col["name"]: col["type"] for col in columns},
                    "execution_time_ms": execution_time_ms,
                    "query": query_with_limit
                }
                
                # Always show preview (first 100 rows)
                preview_size = min(100, row_count)
                result["results"] = results[:preview_size]
                result["preview_size"] = preview_size
                
                # If more than 100 rows, export to file
                if row_count > 100:
                    import sys
                    from pathlib import Path
                    export_dir = Path(sys.path[0]) / "exports"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{table}_{timestamp}.json"
                    filepath = export_dir / filename
                    
                    export_data = {
                        "cluster": cluster,
                        "database": database,
                        "table": table,
                        "executed_at": datetime.now().isoformat(),
                        "query": query_with_limit,
                        "row_count": row_count,
                        "columns": columns,
                        "results": results
                    }
                    
                    import json
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    result["export_path"] = str(filepath)
                    result["note"] = f"Showing first {preview_size} rows. Full results exported to {filepath}"
                    
                    if ctx:
                        await ctx.info(f"Full results exported to {filepath}")
                
                # Add verification metadata to help users verify results aren't hallucinated
                import hashlib
                result["verification"] = {
                    "query_hash": hashlib.md5(query_with_limit.encode()).hexdigest()[:12],
                    "executed_at": datetime.now().isoformat(),
                    "data_source": f"{cluster}.{database}.{table}",
                    "verify_instructions": "Use verify_query_result tool to re-run this query and verify results",
                    "verification_params": {
                        "cluster": cluster,
                        "database": database,
                        "query": query_with_limit,
                        "expected_row_count": row_count,
                        "expected_columns": [col["name"] for col in columns]
                    }
                }
                
                return safe_json_dumps(result, indent=2)
                
            except Exception as e:
                logger.error(f"Query execution failed: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Execution failed: {str(e)}")
                raise ToolError(f"Execution failed: {str(e)}")
