"""
MCP resources for Kusto server - static documentation and help content.

This module provides MCP resources for help documentation and guides.
"""

from ..core.logging_config import get_logger

logger = get_logger("mcp_tools.resources")


def register_resources(mcp):
    """Register MCP resources with the server."""

    @mcp.resource("kusto://help/overview")
    def help_overview() -> str:
        """Overview of the Kusto Table Search MCP Server"""
        return """
# Kusto Table Search MCP Server

A production-ready MCP server for discovering and querying Kusto tables with
anti-hallucination features and intelligent caching.

## Key Features

🔍 **Smart Table Search**: Search 9,799+ tables across multiple clusters
🛡️ **Anti-Hallucination**: Schema validation, sampling-based query building
🎯 **Query Handles**: Prevent context pollution with server-side result caching
💾 **Query Templates**: Save and reuse common query patterns
⚡ **Performance**: Lazy loading, intelligent caching, performance monitoring

## Getting Started

1. **Search for tables**: Use `search_kusto_tables` with natural language queries
2. **Sample schema**: Use `sample_table_for_query_building` to get real column names
3. **Build queries**: Use actual column names from schema (never guess!)
4. **Execute safely**: Use `execute_query_with_handle` for large results
5. **Analyze**: Use `query_handle_analyze` to explore results without context pollution

## Anti-Hallucination Best Practices

- ALWAYS sample tables before writing queries
- NEVER assume column names - get them from schema
- Use query handles for large result sets
- Validate queries against schema before execution

## Performance Tips

- Repeated table searches are cached (instant response)
- Schema is lazily loaded and cached (no expensive startup)
- Query handles expire after 1 hour
- Use cache_stats to monitor performance
"""

    @mcp.resource("kusto://help/anti-hallucination")
    def help_anti_hallucination() -> str:
        """Anti-hallucination features and best practices"""
        return """
# Anti-Hallucination Features

This server implements multiple strategies to prevent AI agents from hallucinating
table names, column names, or query results.

## Schema Validation

✅ All table schemas are fetched from actual Kusto clusters
✅ Column names and types are cached for fast access
✅ No invented or guessed schema information

## Sampling-Based Query Building

1. **Sample first**: Always use `sample_table_for_query_building`
2. **Get real names**: Extract actual column names from schema
3. **Build queries**: Use only the column names you discovered
4. **Validate**: Server validates queries against cached schema

## Query Handle System

- Results stored server-side (not in context)
- Analytics performed without loading data
- Guarantees results match actual query execution
- Prevents fabrication of query results

## Best Practices

```
# CORRECT WORKFLOW
1. search_kusto_tables("wireserver requests")
2. sample_table_for_query_building(cluster, db, table)
3. Build query using EXACT column names from step 2
4. execute_query_with_handle(query)
5. query_handle_analyze(handle, "count")

# NEVER DO THIS
❌ Assume column names without sampling
❌ Invent column names based on table name
❌ Use generic names like "Timestamp" without verification
```

## Validation Tools

- `sample_table_for_query_building`: Get real schema
- `get_table_details`: Get comprehensive table information
- `query_handle_validate`: Verify cached results exist
"""
