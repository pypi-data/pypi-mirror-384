# Speclit: Natural Language Query Tool

**Status:** Implemented  
**Version:** 1.0  
**Last Updated:** October 15, 2025

## Overview

The `query_from_natural_language()` tool provides an intelligent, end-to-end solution for executing Kusto queries using natural language requests. It eliminates the need to manually write KQL by automatically discovering tables, sampling schemas, generating queries, and executing them—all in a single tool call.

## Problem Statement

Users often know what data they want but don't want to:
- Search for the right table
- Sample the schema to find column names
- Write the KQL syntax manually
- Handle query execution and result management

This creates friction in the data exploration workflow, especially for:
- Quick ad-hoc queries
- Users unfamiliar with KQL syntax
- Exploratory data analysis
- Rapid prototyping

## Solution

A single tool that accepts natural language requests and handles the entire query workflow:

1. **Table Discovery**: Automatically searches for relevant tables if not specified
2. **Schema Sampling**: Discovers actual column names and types
3. **Query Generation**: Translates natural language to KQL using intelligent heuristics
4. **Validation**: Ensures the query is safe and well-formed
5. **Execution**: Runs the query and caches results
6. **Suggestions**: Provides next steps based on results

## Tool Specification

### Tool Name
`query_from_natural_language`

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `request` | string | Yes | - | Natural language description of what to query |
| `cluster` | string | No | auto-detect | Kusto cluster name |
| `database` | string | No | auto-detect | Database name |
| `table` | string | No | auto-search | Table name |
| `limit` | integer | No | 100 | Maximum rows to return (max: 10000) |
| `time_range` | string | No | "24h" | Time filter (e.g., "1h", "7d", null to disable) |

### Return Value

JSON object containing:

```json
{
  "success": true,
  "table_info": {
    "cluster": "string",
    "database": "string", 
    "table": "string",
    "full_path": "cluster.database.table"
  },
  "natural_language_request": "original request",
  "generated_query": "KQL query that was generated",
  "results": [...],
  "row_count": 42,
  "columns": [...],
  "execution_time_ms": 123.45,
  "cache_key": "cache_key_for_results",
  "suggestions": [
    "Next steps and analysis suggestions"
  ]
}
```

## Usage Examples

### Example 1: Simple Filter Query
```python
query_from_natural_language(
    request="Show me the latest 50 events where severity is high"
)
```

**Generated KQL:**
```kql
EventTable
| where Timestamp > ago(24h)
| where Severity == 'high'
| order by Timestamp desc
| take 50
```

### Example 2: Aggregation Query
```python
query_from_natural_language(
    request="Count errors by error type in the last hour",
    time_range="1h"
)
```

**Generated KQL:**
```kql
ErrorTable
| where Timestamp > ago(1h)
| summarize Count = count() by ErrorType
| order by Count desc
```

### Example 3: Performance Query
```python
query_from_natural_language(
    request="Find all requests that took longer than 5 seconds",
    limit=200
)
```

**Generated KQL:**
```kql
RequestTable
| where Timestamp > ago(24h)
| where DurationMs > 5000
| take 200
```

### Example 4: Unique Values Query
```python
query_from_natural_language(
    request="Get unique users who logged in today"
)
```

**Generated KQL:**
```kql
LoginTable
| where Timestamp > ago(24h)
| distinct UserId
```

## Supported Natural Language Patterns

The tool recognizes common query patterns:

### Filtering Patterns
- "where X is Y" → `where X == 'Y'`
- "severity is high/critical/error" → `where Severity == 'high'`
- "error" → Finds error-related columns and filters

### Aggregation Patterns
- "count" or "number of" → `summarize Count = count()`
- "count by X" → `summarize Count = count() by X`
- "unique" or "distinct" → `distinct Column` or `dcount()`

### Ordering Patterns
- "latest" or "recent" or "last" → `order by Timestamp desc`
- "top" or "first" → `order by Column desc`

### Performance Patterns
- "took longer than X seconds" → `where Duration > X * 1000`
- "slower than X ms" → `where Duration > X`

## Implementation Details

### Query Generation Algorithm

The query generator uses a rule-based approach:

1. **Column Discovery**: Extracts available columns from schema sample
2. **Type Detection**: Identifies datetime columns for time filtering
3. **Pattern Matching**: Matches request against known patterns
4. **Filter Building**: Constructs WHERE clauses from patterns
5. **Aggregation Detection**: Determines if aggregation is needed
6. **Ordering Logic**: Adds appropriate ORDER BY clauses
7. **Limit Application**: Adds TAKE clause (unless aggregating)

### Schema Sampling

Before generating the query, the tool:
1. Executes `{table} | take 5` to get sample data
2. Extracts column names and types
3. Uses this information for accurate query generation
4. Prevents hallucination of non-existent columns

### Safety Features

- **Row Limits**: Enforces maximum of 10,000 rows
- **Timeout Protection**: Queries timeout after reasonable duration
- **Result Caching**: All results cached for 1 hour
- **Validation**: Generated queries are validated before execution

## Limitations

### Current Limitations

1. **Pattern-Based**: Uses heuristics, not AI/ML for query generation
2. **Simple Queries**: Best for straightforward queries, not complex joins
3. **English Only**: Natural language parsing is English-specific
4. **Column Name Matching**: Relies on column names appearing in request

### When to Use Other Tools

Use manual query building when you need:
- Complex joins across multiple tables
- Advanced KQL operators (mvexpand, materialize, etc.)
- Custom aggregations or calculations
- Precise control over query structure

## Integration with Other Tools

The tool integrates seamlessly with the existing workflow:

1. **Result Caching**: Returns `cache_key` for use with:
   - `get_cached_results()` - Paginate through results
   - `query_handle_analyze()` - Statistical analysis
   - `export_results()` - Export to CSV/JSON/Excel

2. **Table Discovery**: Uses existing `table_search` service
3. **Query Execution**: Uses existing `connection_manager`
4. **Performance Monitoring**: Uses existing metrics system

## Future Enhancements

Potential improvements:

1. **AI-Powered Generation**: Use LLM for more sophisticated query generation
2. **Learning System**: Learn from successful queries and user feedback
3. **Multi-Table Support**: Generate queries across multiple tables
4. **Query Templates**: Save commonly-used patterns as templates
5. **Language Support**: Support for other natural languages
6. **Semantic Understanding**: Better understanding of domain-specific terms

## Testing

### Unit Tests
Location: `tests/test_natural_language_query.py`

Test coverage includes:
- Pattern matching for different query types
- Filter generation from natural language
- Column name discovery
- Query validation
- Error handling

### Integration Tests
- End-to-end query execution
- Table discovery integration
- Schema sampling
- Result caching

## Performance Metrics

Typical performance:
- Table search: <100ms
- Schema sampling: 50-200ms  
- Query generation: <10ms
- Query execution: Varies by complexity
- Total latency: 200ms - 5s (depending on query)

## Examples in Practice

### Troubleshooting Scenario
```python
# Quick check for recent errors
query_from_natural_language(
    request="Show errors in the last hour"
)
```

### Monitoring Scenario  
```python
# Check for slow requests
query_from_natural_language(
    request="Find requests that took longer than 10 seconds today"
)
```

### Analysis Scenario
```python
# Understand error distribution
query_from_natural_language(
    request="Count errors by error code in the last 24 hours"
)
```

## Conclusion

The natural language query tool provides a convenient, fast way to execute common Kusto queries without writing KQL. It's perfect for quick data exploration and ad-hoc queries, while more complex use cases can still use the full suite of manual query building tools.

The tool demonstrates the power of combining multiple services (table search, schema sampling, query execution) into a single, user-friendly interface that handles the most common query patterns automatically.
