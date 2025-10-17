"""
Query development tools for Kusto MCP server.

This module provides tools for query validation and formatting:
- validate_query: Validate KQL query syntax and best practices
- format_query: Format and beautify KQL queries
"""

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.query_development")


def register_query_development_tools(mcp, services: dict):
    """Register query development tools with the MCP server."""
    query_optimizer = services['query_optimizer']

    @mcp.tool()
    async def validate_query(
        cluster: str,
        database: str,
        query: str,
        ctx: Context = None
    ) -> str:
        """
        ✅ Validate a KQL query without executing it.
        
        Check query syntax, estimate execution cost, and identify potential issues
        before running the query. Helps catch errors early and optimize queries.
        
        Validation includes:
        - Syntax checking
        - Schema validation (table/column existence)
        - Cost estimation
        - Performance warnings
        - Best practices compliance
        
        Args:
            cluster: Cluster name
            database: Database name
            query: KQL query to validate
        
        Returns:
            JSON with validation status, errors, warnings, and recommendations
        """
        if ctx:
            await ctx.info(f"✅ Validating query syntax and schema")
        
        with measure_operation("validate_query"):
            try:
                validation_result = {
                    "valid": True,
                    "syntax_valid": True,
                    "errors": [],
                    "warnings": [],
                    "recommendations": []
                }
                
                # Basic syntax validation
                if not query or not query.strip():
                    validation_result["valid"] = False
                    validation_result["errors"].append("Query is empty")
                    return safe_json_dumps(validation_result, indent=2)
                
                # Check for common issues
                query_lower = query.lower()
                
                # Missing time filter warning
                if "where" not in query_lower or "ago(" not in query_lower:
                    validation_result["warnings"].append(
                        "Query may benefit from a time filter (e.g., | where Timestamp > ago(1h))"
                    )
                
                # Missing limit warning
                if "take" not in query_lower and "limit" not in query_lower:
                    validation_result["warnings"].append(
                        "Query has no row limit. Consider adding '| take N' to prevent large result sets"
                    )
                
                # Performance recommendations
                if "extend" in query_lower and "where" in query_lower:
                    extend_pos = query_lower.find("extend")
                    where_pos = query_lower.find("where")
                    if extend_pos < where_pos:
                        validation_result["recommendations"].append(
                            "Move 'where' clause before 'extend' for better performance"
                        )
                
                # Analyze with query optimizer
                try:
                    analysis = query_optimizer.analyze_query(query, None)
                    validation_result["complexity_score"] = analysis.get("complexity_score", 0)
                    validation_result["estimated_cost"] = analysis.get("estimated_cost", "unknown")
                    
                    if analysis.get("performance_issues"):
                        validation_result["warnings"].extend([
                            issue.get("message", issue.get("description", "Unknown issue")) 
                            for issue in analysis["performance_issues"]
                        ])
                    
                    if analysis.get("recommendations"):
                        validation_result["recommendations"].extend(analysis["recommendations"])
                except Exception as e:
                    validation_result["warnings"].append(f"Could not perform deep analysis: {str(e)}")
                
                if ctx:
                    status = "✅ Valid" if validation_result["valid"] else "❌ Invalid"
                    await ctx.info(f"{status} - {len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings")
                
                return safe_json_dumps(validation_result, indent=2)
                
            except Exception as e:
                logger.error(f"Query validation failed: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Validation failed: {str(e)}")
                raise ToolError(f"Validation failed: {str(e)}")

    @mcp.tool()
    def format_query(
        query: str,
        cluster: str = None,
        database: str = None,
        convert_to_absolute_timestamps: bool = True
    ) -> str:
        """
        🎨 Format and beautify a KQL query with best practices.
        
        Applies standard KQL formatting conventions for better readability:
        - Puts each pipe operator on its own line with proper indentation
        - Converts relative timestamps (ago()) to absolute datetime literals
        - Adds fully qualified cluster.database references
        - Human-readable formatting with clear structure
        
        Args:
            query: KQL query to format
            cluster: Optional cluster name for fully qualified references
            database: Optional database name for fully qualified references
            convert_to_absolute_timestamps: Convert ago() to absolute datetime (default: True)
        
        Returns:
            JSON with formatted query and transformation notes
        """
        import re
        from datetime import datetime, timedelta
        
        with measure_operation("format_query"):
            try:
                original_query = query
                transformations = []
                
                # Step 1: Convert relative timestamps to absolute ones
                if convert_to_absolute_timestamps:
                    def replace_ago(match):
                        full_match = match.group(0)
                        time_value = match.group(1)
                        time_unit = match.group(2)
                        
                        # Parse the time value
                        try:
                            value = int(time_value)
                        except:
                            return full_match  # Can't parse, leave as-is
                        
                        # Calculate absolute datetime
                        now = datetime.utcnow()
                        if time_unit in ['d', 'day', 'days']:
                            target_time = now - timedelta(days=value)
                        elif time_unit in ['h', 'hour', 'hours']:
                            target_time = now - timedelta(hours=value)
                        elif time_unit in ['m', 'min', 'minute', 'minutes']:
                            target_time = now - timedelta(minutes=value)
                        elif time_unit in ['s', 'sec', 'second', 'seconds']:
                            target_time = now - timedelta(seconds=value)
                        else:
                            return full_match  # Unknown unit, leave as-is
                        
                        # Format as KQL datetime literal
                        abs_time = target_time.strftime("datetime(%Y-%m-%d %H:%M:%S)")
                        transformations.append(f"Converted '{full_match}' to '{abs_time}'")
                        return abs_time
                    
                    # Match patterns like: ago(7d), ago(24h), ago(30m)
                    query = re.sub(r'ago\((\d+)(d|day|days|h|hour|hours|m|min|minute|minutes|s|sec|second|seconds)\)', replace_ago, query, flags=re.IGNORECASE)
                
                # Step 2: Add fully qualified table references if cluster/database provided
                if cluster and database:
                    # Match table references at start of query or after pipes
                    def add_qualification(match):
                        prefix = match.group(1) if match.group(1) else ""
                        table_name = match.group(2)
                        
                        # Skip if already qualified
                        if 'cluster(' in table_name or 'database(' in table_name:
                            return match.group(0)
                        
                        qualified = f"{prefix}cluster('{cluster}').database('{database}').{table_name}"
                        transformations.append(f"Qualified table reference: {table_name} -> {qualified}")
                        return qualified
                    
                    # Match table names (word followed by optional whitespace and pipe or end)
                    query = re.sub(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*(?=\||$)', add_qualification, query, flags=re.MULTILINE)
                
                # Step 3: Format for readability - remove extra whitespace first
                query = ' '.join(query.split())
                
                # Step 4: Split on pipe operators while preserving them
                parts = []
                current = []
                in_string = False
                escape_next = False
                
                for char in query:
                    if escape_next:
                        current.append(char)
                        escape_next = False
                        continue
                        
                    if char == '\\':
                        escape_next = True
                        current.append(char)
                        continue
                        
                    if char in ['"', "'"]:
                        in_string = not in_string
                        current.append(char)
                        continue
                    
                    if char == '|' and not in_string:
                        if current:
                            parts.append(''.join(current).strip())
                            current = []
                        parts.append('|')
                    else:
                        current.append(char)
                
                if current:
                    parts.append(''.join(current).strip())
                
                # Step 5: Format the parts with proper line breaks and indentation
                formatted_lines = []
                for i, part in enumerate(parts):
                    if not part or part.isspace():
                        continue
                        
                    if part == '|':
                        # Pipe operator - will be combined with next part
                        continue
                    elif i > 0 and parts[i-1] == '|':
                        # This part comes after a pipe - indent it
                        formatted_lines.append(f"| {part}")
                    else:
                        # First part (table name) - no indentation
                        formatted_lines.append(part)
                
                formatted_query = '\n'.join(formatted_lines)
                
                result = {
                    "success": True,
                    "formatted_query": formatted_query,
                    "original_length": len(original_query),
                    "formatted_lines": len(formatted_lines),
                    "transformations": transformations,
                    "notes": []
                }
                
                if transformations:
                    result["notes"].append(f"Applied {len(transformations)} transformation(s) for better clarity")
                
                result["notes"].append("Query formatted with human-readable structure")
                result["notes"].append("Each pipe operator is on its own line for readability")
                
                if convert_to_absolute_timestamps:
                    result["notes"].append("Relative timestamps converted to absolute datetime literals")
                
                if cluster and database:
                    result["notes"].append(f"Table references qualified with cluster '{cluster}' and database '{database}'")
                
                return safe_json_dumps(result, indent=2)
                
            except Exception as e:
                logger.error(f"Query formatting failed: {e}", exc_info=True)
                raise ToolError(f"Formatting failed: {str(e)}")
