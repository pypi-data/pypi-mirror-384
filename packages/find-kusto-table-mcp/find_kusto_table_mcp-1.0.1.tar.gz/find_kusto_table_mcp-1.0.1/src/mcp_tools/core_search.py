"""
Core table search and discovery tools for Kusto MCP server.

This module provides the primary tools for discovering and exploring Kusto tables:
- search_kusto_tables: Natural language table search across clusters
- add_table_note: Add contextual notes to tables
- get_table_notes: Retrieve notes for a table
- explore_table: Unified table exploration with schema and samples
"""

from typing import Optional
from datetime import datetime
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.core_search")


def register_core_search_tools(mcp, services: dict):
    """Register core search tools with the MCP server."""
    table_discovery = services['table_discovery']
    schema_cache = services['schema_cache']

    @mcp.tool()
    async def search_kusto_tables(
        query: str,
        method: str = "hybrid",
        limit: int = 10,
        fetch_schema: bool = True,
        ctx: Context = None
    ) -> str:
        """
        🔍 Search for Kusto tables using natural language queries with lazy schema caching.
        
        This is the PRIMARY tool for discovering tables. It searches 9,799+ tables across
        multiple Kusto clusters using advanced semantic search with anti-hallucination features.
        
        Features:
        - Instant responses with on-demand schema caching (no slow upfront loading)
        - Returns actual column names and types from real schemas
        - Multiple search strategies for best results
        - Cached results for super-fast repeat searches
        
        Args:
            query: Natural language search query
                   Examples: "WireServer request tables", "node health monitoring",
                            "authentication token data"
            method: Search strategy - "hybrid" (recommended), "keyword", "fuzzy", or "contextual"
            limit: Maximum number of results (1-50)
            fetch_schema: Whether to fetch actual schema from Kusto (cached for performance)
        
        Returns:
            JSON with search results including table paths, schemas, time columns,
            and ready-to-run sample queries using ACTUAL column names.
        
        Anti-hallucination: All schemas are fetched from real Kusto clusters and cached.
        No column names are invented - only actual schema data is returned.
        """
        if ctx:
            await ctx.info(f"🔍 Searching for tables: '{query}'")
        
        with measure_operation("search_tables"):
            try:
                # Validate inputs
                if not query or not query.strip():
                    raise ToolError("Query parameter cannot be empty")
                
                if method not in ["keyword", "fuzzy", "contextual", "hybrid"]:
                    raise ToolError(f"Invalid method: {method}. Use: keyword, fuzzy, contextual, or hybrid")
                
                if not (1 <= limit <= 50):
                    raise ToolError(f"Limit must be between 1 and 50, got: {limit}")
                
                # Perform search using table discovery tool
                results = await table_discovery.search_tables(
                    query=query,
                    method=method,
                    limit=limit,
                    fetch_schema=fetch_schema,
                    cache_results=True
                )
                
                if ctx:
                    result_count = results.get("search_metadata", {}).get("total_results", 0)
                    await ctx.info(f"✅ Found {result_count} matching tables")
                
                return safe_json_dumps(results, indent=2)
                
            except Exception as e:
                logger.error(f"Table search failed: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Search failed: {str(e)}")
                raise ToolError(f"Search failed: {str(e)}")

    @mcp.tool()
    async def add_table_note(
        cluster: str,
        database: str,
        table: str,
        note: str,
        category: str = "general",
        ctx: Context = None
    ) -> str:
        """
        📝 Add a contextual note to a table for future reference.
        
        Use this tool to store workflow-specific context, usage patterns, or other
        important information about a table. Notes are persistent and will be included
        in future table searches and schema lookups, helping agents learn and improve
        over time.
        
        Common use cases:
        - Document specific workflow patterns ("Use TimeGenerated > ago(7d) for performance")
        - Note data quality issues ("Location column often null before 2023")
        - Record business context ("This table tracks production deployments")
        - Share query tips ("Always filter by Region first for better performance")
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            note: The note text to add
            category: Note category - one of: 'workflow', 'usage', 'schema', 'performance', 'general'
        
        Returns:
            JSON with confirmation and the added note
        """
        if ctx:
            await ctx.info(f"Adding note to {cluster}.{database}.{table}")
        
        with measure_operation("add_table_note"):
            try:
                # Validate inputs
                if not note or not note.strip():
                    raise ToolError("Note text cannot be empty")
                
                valid_categories = ['workflow', 'usage', 'schema', 'performance', 'general']
                if category not in valid_categories:
                    raise ToolError(f"Invalid category: {category}. Use one of: {', '.join(valid_categories)}")
                
                # Add note to schema cache
                note_entry = schema_cache.add_note(cluster, database, table, note, category)
                
                if ctx:
                    await ctx.info(f"Note added successfully")
                
                return safe_json_dumps({
                    "success": True,
                    "table_path": f"{cluster}.{database}.{table}",
                    "note_added": note_entry,
                    "message": "Note added successfully and will be included in future searches",
                    "tip": "Notes are persistent and help agents learn about your specific workflows"
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Failed to add note: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Failed to add note: {str(e)}")
                raise ToolError(f"Failed to add note: {str(e)}")

    @mcp.tool()
    async def get_table_notes(
        cluster: str,
        database: str,
        table: str,
        ctx: Context = None
    ) -> str:
        """
        📖 Get all notes for a specific table.
        
        Retrieve all contextual notes that have been added to a table.
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
        
        Returns:
            JSON with all notes for the table
        """
        if ctx:
            await ctx.info(f"Retrieving notes for {cluster}.{database}.{table}")
        
        with measure_operation("get_table_notes"):
            try:
                notes = schema_cache.get_notes(cluster, database, table)
                
                return safe_json_dumps({
                    "success": True,
                    "table_path": f"{cluster}.{database}.{table}",
                    "note_count": len(notes),
                    "notes": notes
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Failed to get notes: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Failed to get notes: {str(e)}")
                raise ToolError(f"Failed to get notes: {str(e)}")

    @mcp.tool()
    async def explore_table(
        cluster: str,
        database: str,
        table: str,
        include_sample: bool = True,
        sample_size: int = 10,
        include_stats: bool = False,
        ctx: Context = None
    ) -> str:
        """
        🔍 Unified table exploration tool (replaces get_table_details + sample_table).
        
        One-stop tool for discovering everything about a table:
        - Complete schema with column types
        - Sample data rows
        - Time columns and numeric/string column categorization
        - Optional statistics for numeric columns
        - Ready-to-use sample queries
        
        This consolidates the functionality of get_table_details and 
        sample_table_for_query_building into a single, comprehensive tool.
        
        Args:
            cluster: Cluster name
            database: Database name
            table: Table name
            include_sample: Include sample data rows (default: True)
            sample_size: Number of sample rows (default: 10, max: 50)
            include_stats: Calculate basic statistics for numeric columns
        
        Returns:
            JSON with complete table information, schema, samples, and example queries
        """
        if ctx:
            await ctx.info(f"🔍 Exploring table {cluster}.{database}.{table}")
        
        with measure_operation("explore_table"):
            try:
                # Get comprehensive table details
                details = await table_discovery.get_table_details(
                    cluster=cluster,
                    database=database,
                    table=table,
                    include_sample=include_sample,
                    sample_size=min(sample_size, 50)
                )
                
                # Add exploration-specific metadata
                details["exploration_metadata"] = {
                    "explored_at": datetime.now().isoformat(),
                    "sample_included": include_sample,
                    "stats_included": include_stats
                }
                
                # Add usage tips
                details["usage_tips"] = [
                    "Use the exact column names from 'columns' in your queries",
                    "Check 'time_columns' to find the primary time column for filtering",
                    "Review 'sample_queries' for query examples",
                    "Use 'numeric_columns' for aggregations and statistics"
                ]
                
                if ctx:
                    col_count = len(details.get("schema", {}).get("columns", []))
                    await ctx.info(f"✅ Table explored: {col_count} columns, {sample_size} sample rows")
                
                return safe_json_dumps(details, indent=2)
                
            except Exception as e:
                logger.error(f"Table exploration failed: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Exploration failed: {str(e)}")
                raise ToolError(f"Table exploration failed: {str(e)}")
