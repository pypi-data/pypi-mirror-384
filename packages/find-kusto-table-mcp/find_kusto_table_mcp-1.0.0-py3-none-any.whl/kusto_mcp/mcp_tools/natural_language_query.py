"""
Natural language query tool for Kusto MCP server.

This module provides a tool for executing queries based on natural language requests:
- query_from_natural_language: Translate natural language to KQL and execute
"""

from typing import Optional
from datetime import datetime
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.natural_language_query")


def register_natural_language_query_tool(mcp, services: dict):
    """Register natural language query tool with the MCP server."""
    table_discovery = services['table_discovery']
    schema_cache = services['schema_cache']
    connection_manager = services['connection_manager']

    @mcp.tool()
    async def query_from_natural_language(
        request: str,
        cluster: Optional[str] = None,
        database: Optional[str] = None,
        table: Optional[str] = None,
        limit: int = 100,
        time_range_hours: int = 24,
        ingestion_delay_minutes: int = 5,
        ctx: Context = None
    ) -> str:
        """
        🧠 Execute a Kusto query based on natural language request.
        
        This is an intelligent end-to-end tool that:
        1. Searches for relevant tables (if not specified)
        2. Samples the table schema to discover actual columns
        3. Generates a KQL query from your natural language request
        4. Validates and executes the query
        5. Returns results with suggestions for further analysis
        
        Perfect for quick data exploration when you know what you want but
        don't want to write the KQL yourself.
        
        Examples:
        - "Show me the latest 50 events where severity is high"
        - "Count errors by error type in the last hour"
        - "Find all requests that took longer than 5 seconds"
        - "Get unique users who logged in today"
        
        Args:
            request: Natural language description of what you want to query
            cluster: (Optional) Cluster name - will auto-detect if not specified
            database: (Optional) Database name - will auto-detect if not specified
            table: (Optional) Table name - will search if not specified
            limit: Maximum rows to return (default: 100, max: 10000)
            time_range_hours: Hours of data to query (default: 24)
            ingestion_delay_minutes: Account for data ingestion delay (default: 5 minutes)
        
        Returns:
            JSON with:
            - success: Execution status
            - table_info: Details about the table used
            - generated_query: The KQL query that was generated with absolute timestamps
            - results: Query results (preview of first 100 rows)
            - row_count: Number of rows returned
            - columns: Column names and types
            - execution_time_ms: Query execution time
            - export_path: Path to full results file (if > 100 rows)
            - suggestions: Next steps and analysis suggestions
        """
        if ctx:
            await ctx.info(f"🧠 Processing natural language query: {request[:100]}...")
        
        with measure_operation("query_from_natural_language"):
            try:
                # Step 1: Find the table if not specified
                if not table or not cluster or not database:
                    if ctx:
                        await ctx.info("🔍 Searching for relevant tables...")
                    
                    search_response = await table_discovery.search_tables(
                        query=request,
                        limit=5,
                        fetch_schema=True
                    )
                    search_results = search_response.get("results", [])
                    
                    if not search_results:
                        raise ToolError("No relevant tables found for your request. Please specify cluster, database, and table.")
                    
                    # Use the best match
                    best_match = search_results[0]
                    cluster = cluster or best_match["cluster"]
                    database = database or best_match["database"]
                    table = table or best_match["table"]
                    
                    if ctx:
                        score = best_match.get("score", 0.0)
                        await ctx.info(f"✅ Found table: {cluster}.{database}.{table} (score: {score:.2f})")
                
                # Step 2: Sample the table schema
                if ctx:
                    await ctx.info(f"📋 Sampling schema for {table}...")
                
                sample_query = f"{table}\n| take 5"
                sample_results, sample_columns = await connection_manager.execute_query(
                    cluster=cluster,
                    database=database,
                    query=sample_query,
                    timeout_seconds=30
                )
                
                # Build column info for query generation
                column_info = []
                column_types = {}
                for col in sample_columns:
                    col_name = col['name']
                    col_type = col.get('type', 'unknown')
                    column_types[col_name] = col_type
                    column_info.append(f"- {col_name} ({col_type})")
                
                if ctx:
                    await ctx.info(f"✅ Found {len(column_info)} columns")
                
                # Step 3: Generate KQL query from natural language
                if ctx:
                    await ctx.info("🔨 Generating KQL query...")
                
                # Calculate absolute timestamps
                from datetime import timedelta
                end_time = datetime.utcnow() - timedelta(minutes=ingestion_delay_minutes)
                start_time = end_time - timedelta(hours=time_range_hours)
                
                query = await _generate_kql_from_natural_language(
                    request=request,
                    table_name=table,
                    columns=sample_columns,
                    sample_data=sample_results[:3] if sample_results else [],
                    start_time=start_time,
                    end_time=end_time,
                    limit=limit,
                    ctx=ctx
                )
                
                if ctx:
                    await ctx.info(f"✅ Generated query with absolute timestamps:\n{query}")
                
                # Step 4: Execute the query with retry logic
                if ctx:
                    await ctx.info("🚀 Testing and executing query...")
                
                max_attempts = 3
                attempt = 0
                last_error = None
                results = None
                columns = None
                execution_time_ms = 0
                
                while attempt < max_attempts:
                    attempt += 1
                    
                    try:
                        if ctx and attempt > 1:
                            await ctx.info(f"Attempt {attempt}/{max_attempts} - Refining query...")
                        
                        start_exec_time = datetime.now()
                        results, columns = await connection_manager.execute_query(
                            cluster=cluster,
                            database=database,
                            query=query,
                            timeout_seconds=60
                        )
                        execution_time_ms = (datetime.now() - start_exec_time).total_seconds() * 1000
                        
                        # Success! Break the retry loop
                        if ctx:
                            await ctx.info(f"Query executed successfully on attempt {attempt}")
                        break
                        
                    except Exception as e:
                        last_error = str(e)
                        error_lower = last_error.lower()
                        
                        if ctx:
                            await ctx.info(f"Attempt {attempt} failed: {last_error[:100]}")
                        
                        # If this is the last attempt, raise the error
                        if attempt >= max_attempts:
                            raise ToolError(f"Query failed after {max_attempts} attempts. Last error: {last_error}")
                        
                        # Try to fix common issues
                        if "column" in error_lower and "not found" in error_lower:
                            # Column name issue - resample schema and regenerate
                            if ctx:
                                await ctx.info("Column not found - resampling schema...")
                            
                            sample_query = f"{table}\n| take 5"
                            sample_results, sample_columns = await connection_manager.execute_query(
                                cluster=cluster,
                                database=database,
                                query=sample_query,
                                timeout_seconds=30
                            )
                            
                            # Regenerate query with updated schema
                            query = await _generate_kql_from_natural_language(
                                request=request,
                                table_name=table,
                                columns=sample_columns,
                                sample_data=sample_results[:3] if sample_results else [],
                                start_time=start_time,
                                end_time=end_time,
                                limit=limit,
                                ctx=ctx
                            )
                            
                            if ctx:
                                await ctx.info(f"Regenerated query: {query}")
                        
                        elif "syntax" in error_lower or "parse" in error_lower:
                            # Syntax error - simplify the query
                            if ctx:
                                await ctx.info("Syntax error - simplifying query...")
                            
                            # Fallback to a simpler query
                            datetime_col = next((col['name'] for col in sample_columns if 'datetime' in col.get('type', '').lower()), None)
                            if datetime_col:
                                start_str = start_time.strftime("datetime(%Y-%m-%d %H:%M:%S)")
                                end_str = end_time.strftime("datetime(%Y-%m-%d %H:%M:%S)")
                                query = f"{table}\n| where {datetime_col} between ({start_str} .. {end_str})\n| take {limit}"
                            else:
                                query = f"{table}\n| take {limit}"
                            
                            if ctx:
                                await ctx.info(f"Simplified query: {query}")
                        
                        else:
                            # Unknown error - just retry with same query
                            if ctx:
                                await ctx.info("Unknown error - retrying...")
                
                # If we still don't have results, something went wrong
                if results is None:
                    raise ToolError(f"Failed to execute query: {last_error}")
                
                row_count = len(results)
                
                # Build response
                response = {
                    "success": True,
                    "table_info": {
                        "cluster": cluster,
                        "database": database,
                        "table": table,
                        "full_path": f"{cluster}.{database}.{table}"
                    },
                    "natural_language_request": request,
                    "generated_query": query,
                    "results": results[:100],  # Always preview first 100
                    "preview_size": min(100, row_count),
                    "row_count": row_count,
                    "columns": columns,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "suggestions": _generate_suggestions(row_count, results, columns)
                }
                
                # Export full results if > 100 rows
                if row_count > 100:
                    import sys
                    from pathlib import Path
                    export_dir = Path(sys.path[0]) / "exports"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{table}_nl_query_{timestamp}.json"
                    filepath = export_dir / filename
                    
                    export_data = {
                        "cluster": cluster,
                        "database": database,
                        "table": table,
                        "natural_language_request": request,
                        "executed_at": datetime.now().isoformat(),
                        "query": query,
                        "row_count": row_count,
                        "columns": columns,
                        "results": results
                    }
                    
                    import json
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    response["export_path"] = str(filepath)
                    response["note"] = f"Showing first 100 rows. Full results exported to {filepath}"
                    
                    if ctx:
                        await ctx.info(f"Full results exported to {filepath}")
                
                if ctx:
                    await ctx.info(f"✅ Query executed successfully - {row_count} rows returned in {execution_time_ms:.0f}ms")
                
                return safe_json_dumps(response, indent=2)
                
            except Exception as e:
                logger.error(f"Natural language query failed: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Query failed: {str(e)}")
                raise ToolError(f"Natural language query failed: {str(e)}")


def _validate_generated_query(query: str) -> list:
    """
    Basic validation for generated queries to catch common issues.
    Returns list of warnings (empty if no issues).
    
    Checks for:
    - Missing time filters on time-series data
    - Missing result limits
    - Other performance considerations
    """
    warnings = []
    query_lower = query.lower()
    
    # Check for time filter if query uses time-series data
    if '| where' not in query_lower or ('datetime' not in query_lower and 'between' not in query_lower):
        if 'timestamp' in query_lower:
            warnings.append("Consider adding time filter for better performance")
    
    # Check for result limit
    if 'take' not in query_lower and 'limit' not in query_lower and 'summarize' not in query_lower:
        warnings.append("Query may return large result set - limit applied")
    
    return warnings


async def _generate_kql_from_natural_language(
    request: str,
    table_name: str,
    columns: list,
    sample_data: list,
    start_time: datetime,
    end_time: datetime,
    limit: int,
    ctx: Context = None
) -> str:
    """
    Generate KQL query from natural language using absolute timestamps.
    
    Uses AI-powered generation when ctx.sample is available (free models only).
    Falls back to rule-based heuristics for compatibility.
    
    ALWAYS uses absolute datetime literals, never relative timestamps like ago().
    """
    # Try AI-powered generation first
    if ctx and hasattr(ctx, 'sample'):
        try:
            from ..utils.sampling_client import SamplingClient
            
            sampling_client = SamplingClient(ctx)
            
            # Build schema dict from columns
            schema_dict = {col['name']: col.get('type', 'unknown') for col in columns}
            
            # Extract time columns
            time_columns = [
                col['name'] for col in columns 
                if 'datetime' in col.get('type', '').lower() or 'timestamp' in col['name'].lower()
            ]
            primary_time_column = time_columns[0] if time_columns else None
            
            # Generate query using AI
            logger.info("Attempting AI-powered query generation for natural language request")
            result = await sampling_client.generate_query_with_ai(
                user_request=request,
                cluster="unknown",  # Will be filled in by caller
                database="unknown",
                table=table_name,
                schema=schema_dict,
                columns=[col['name'] for col in columns],
                time_columns=time_columns,
                primary_time_column=primary_time_column
            )
            
            query = result['query']
            
            # Apply limit if specified and not already in query
            if limit and 'take' not in query.lower() and 'limit' not in query.lower():
                query += f"\n| take {limit}"
            
            logger.info(f"AI generated query with confidence: {result.get('confidence', 'unknown')}")
            return query
            
        except Exception as e:
            logger.warning(f"AI query generation failed, falling back to rule-based: {str(e)}")
            # Fall through to rule-based generation
    
    # FALLBACK: Rule-based query generation
    logger.info("Using rule-based query generation for natural language request")
    
    request_lower = request.lower()
    
    # Extract column names
    column_names = [col['name'] for col in columns]
    column_types = {col['name']: col.get('type', 'unknown') for col in columns}
    
    # Find datetime column for time filtering
    datetime_column = None
    for col_name, col_type in column_types.items():
        if 'datetime' in col_type.lower() or 'timestamp' in col_name.lower():
            datetime_column = col_name
            break
    
    # Start building query
    query_parts = [table_name]
    
    # Add time filter with absolute timestamps
    if datetime_column and start_time and end_time:
        start_str = start_time.strftime("datetime(%Y-%m-%d %H:%M:%S)")
        end_str = end_time.strftime("datetime(%Y-%m-%d %H:%M:%S)")
        query_parts.append(f"| where {datetime_column} between ({start_str} .. {end_str})")
    
    # Detect common patterns and add filters
    filters = []
    
    # Pattern: "where X is/equals Y"
    if "where" in request_lower or "=" in request or "is" in request_lower:
        # Try to extract column and value
        for col in column_names:
            col_lower = col.lower()
            if col_lower in request_lower:
                # Simple heuristic for equality
                if "is high" in request_lower or "= high" in request_lower or "equals high" in request_lower:
                    filters.append(f"{col} == 'high'")
                elif "is critical" in request_lower:
                    filters.append(f"{col} == 'critical'")
                elif "is error" in request_lower or "= error" in request_lower:
                    filters.append(f"{col} == 'error'")
    
    # Pattern: "severity is/equals X"
    if "severity" in request_lower:
        severity_col = next((c for c in column_names if "severity" in c.lower()), None)
        if severity_col:
            if "high" in request_lower:
                filters.append(f"{severity_col} == 'high'")
            elif "critical" in request_lower:
                filters.append(f"{severity_col} == 'critical'")
            elif "error" in request_lower:
                filters.append(f"{severity_col} == 'error'")
    
    # Pattern: "error" or "errors"
    if "error" in request_lower:
        error_cols = [c for c in column_names if "error" in c.lower() or "status" in c.lower()]
        if error_cols:
            filters.append(f"{error_cols[0]} == 'error'")
    
    # Pattern: "duration/time > X seconds/milliseconds"
    if any(word in request_lower for word in ["duration", "took", "longer", "slower"]):
        duration_col = next((c for c in column_names if "duration" in c.lower() or "time" in c.lower()), None)
        if duration_col:
            # Extract number
            import re
            numbers = re.findall(r'\d+', request)
            if numbers:
                threshold = int(numbers[0])
                if "millisecond" in request_lower or "ms" in request_lower:
                    filters.append(f"{duration_col} > {threshold}")
                elif "second" in request_lower:
                    filters.append(f"{duration_col} > {threshold * 1000}")
    
    # Add filters
    if filters:
        query_parts.append("| where " + " and ".join(filters))
    
    # Detect aggregation patterns
    if "count" in request_lower or "number of" in request_lower:
        if "by" in request_lower or "group" in request_lower:
            # Try to find group by column
            group_col = None
            for col in column_names:
                if col.lower() in request_lower and "type" in col.lower():
                    group_col = col
                    break
            
            if group_col:
                query_parts.append(f"| summarize Count = count() by {group_col}")
                query_parts.append("| order by Count desc")
            else:
                query_parts.append("| summarize Count = count()")
        else:
            query_parts.append("| summarize Count = count()")
    
    # Detect distinct/unique patterns
    elif "unique" in request_lower or "distinct" in request_lower:
        # Find the column to get unique values for
        unique_col = None
        for col in column_names:
            if col.lower() in request_lower:
                unique_col = col
                break
        
        if unique_col:
            query_parts.append(f"| summarize UniqueValues = dcount({unique_col})")
        else:
            query_parts.append(f"| distinct {column_names[0]}")
    
    # Detect top/latest patterns
    elif "latest" in request_lower or "recent" in request_lower or "last" in request_lower:
        if datetime_column:
            query_parts.append(f"| order by {datetime_column} desc")
    elif "top" in request_lower or "first" in request_lower:
        query_parts.append(f"| order by {column_names[0]} desc")
    
    # Add limit (unless we're aggregating)
    if not any("summarize" in part for part in query_parts):
        query_parts.append(f"| take {limit}")
    
    generated_query = "\n".join(query_parts)
    
    # Validate generated query and log any warnings
    warnings = _validate_generated_query(generated_query)
    if warnings and ctx:
        for warning in warnings:
            await ctx.info(f"⚠️ {warning}")
    
    return generated_query


def _generate_suggestions(row_count: int, results: list, columns: list) -> list:
    """Generate smart suggestions based on query results."""
    suggestions = []
    
    if row_count == 0:
        suggestions.append("No results found. Try broadening your search criteria or adjusting time range.")
        return suggestions
    
    if row_count > 100:
        suggestions.append(f"Large result set ({row_count} rows). Full results have been exported to file.")
    
    if row_count < 10:
        suggestions.append("Small result set. You might want to broaden your time range or adjust filters.")
    
    # Suggest further analysis
    suggestions.append("Refine your query or use different filters to explore the data further.")
    
    # Suggest correlation analysis
    if row_count >= 10:
        numeric_cols = [col['name'] for col in columns if 'int' in col.get('type', '').lower() or 'real' in col.get('type', '').lower() or 'double' in col.get('type', '').lower()]
        if len(numeric_cols) >= 2:
            suggestions.append(f"Use correlation analysis to find relationships between numeric columns: {', '.join(numeric_cols[:3])}")
    
    return suggestions
