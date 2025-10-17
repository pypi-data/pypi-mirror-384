"""
Query flow management tools for Kusto MCP server.

This module provides tools for creating and managing reusable query flows:
- flow_create: Create and save a new query flow (all flows are auto-saved)
- flow_list: List all available flows with full details
- flow_execute: Execute a flow end-to-end (renders and runs the query)
- flow_find: Find the right flow based on natural language description

Note: Flows are reusable parameterized KQL queries that are automatically saved to disk.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps
from ..services.query_template_service import QueryParameter, ParameterType

logger = get_logger("mcp_tools.templates")


def register_flow_tools(mcp, services: dict):
    """Register flow tools with the MCP server."""
    flows = services['templates']  # Service still named templates internally for backward compatibility
    connection_manager = services['connection_manager']

    @mcp.tool()
    def flow_create(
        name: str,
        description: str,
        query: str,
        parameters: List[Dict[str, Any]],
        cluster: str,
        database: str,
        tags: List[str] = None,
        filename: str = None,
        ctx: Context = None
    ) -> str:
        """
        💾 Create and save a reusable query flow with parameters.
        
        All flows are automatically saved to cache/templates/ for persistence and
        are available immediately through flow_execute(). Perfect for standardized
        analysis workflows that need to be reused.
        
        **IMPORTANT**: You MUST provide cluster and database to make the flow executable!
        **NOTE**: The query will be validated for syntax errors before saving.
        
        Args:
            name: Flow name (unique identifier)
            description: What this flow does
            query: KQL query with {parameter} placeholders
            parameters: List of parameter definitions with name, type, description
            cluster: Kusto cluster name (REQUIRED - e.g., "azcore", "admeus")
            database: Database name (REQUIRED - e.g., "AtScale", "AdmProd")
            tags: Optional tags for organization (e.g., ["troubleshooting", "wireserver"])
            filename: Optional custom filename (without .json extension)
        
        Example parameters:
            [
                {"name": "timespan", "type": "timespan", "description": "Time range", "default_value": "1h"},
                {"name": "threshold", "type": "number", "description": "Error threshold", "required": true}
            ]
        
        Returns:
            JSON with success status, flow name, and file path
        """
        with measure_operation("create_flow"):
            try:
                # Convert parameter dictionaries to QueryParameter objects
                param_objects = []
                for p in parameters:
                    param = QueryParameter(
                        name=p["name"],
                        type=ParameterType(p["type"]),
                        description=p["description"],
                        default_value=p.get("default_value"),
                        required=p.get("required", True)
                    )
                    param_objects.append(param)
                
                # Create metadata with cluster and database
                metadata = {
                    "cluster": cluster,
                    "database": database,
                    "confidential": True
                }
                
                # Validate query syntax before creating flow
                if ctx:
                    ctx.info("Validating query syntax...")
                
                valid, validation_error = flows.validate_query_syntax(
                    query=query,
                    parameters=param_objects,
                    cluster=cluster,
                    database=database,
                    connection_manager=connection_manager
                )
                
                if not valid:
                    error_msg = f"Query syntax validation failed: {validation_error}"
                    logger.error(error_msg)
                    return safe_json_dumps({
                        "success": False,
                        "flow_name": None,
                        "error": error_msg,
                        "note": "Please fix the query syntax before creating the flow"
                    }, indent=2)
                
                if ctx:
                    ctx.info("Query syntax validated successfully")
                
                # Delete existing if present
                if name in flows.templates:
                    flows.delete_template(name)
                
                # Create flow in memory
                success, error = flows.create_template(
                    name=name,
                    description=description,
                    query=query,
                    parameters=param_objects,
                    tags=tags or [],
                    metadata=metadata
                )
                
                if not success:
                    raise ToolError(f"Failed to create flow: {error}")
                
                # Save to disk
                import sys
                flow_dir = Path(sys.path[0]) / "cache" / "templates"
                flow_dir.mkdir(parents=True, exist_ok=True)
                
                save_filename = f"{filename}.json" if filename else f"{name}.json"
                filepath = flow_dir / save_filename
                
                flow_json = {
                    "name": name,
                    "description": description,
                    "query": query,
                    "parameters": [
                        {
                            "name": p["name"],
                            "type": p["type"],
                            "description": p["description"],
                            "default_value": p.get("default_value"),
                            "required": p.get("required", True)
                        }
                        for p in parameters
                    ],
                    "metadata": metadata,
                    "tags": tags or []
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(flow_json, f, indent=2, ensure_ascii=False)
                
                if ctx:
                    ctx.info(f"Flow saved to {filepath}")
                
                return safe_json_dumps({
                    "success": True,
                    "flow_name": name,
                    "filepath": str(filepath),
                    "cluster": cluster,
                    "database": database,
                    "note": "Flow saved to disk and available via flow_execute()"
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Flow creation failed: {e}", exc_info=True)
                raise ToolError(f"Flow creation failed: {str(e)}")



    @mcp.tool()
    def flow_list(
        tags: List[str] = None, 
        search: str = None,
        ctx: Context = None
    ) -> str:
        """
        📚 List all available query flows with full details.
        
        This is the BEST way to discover flows you can execute with flow_execute.
        Shows complete information including:
        - Flow name and description
        - Required parameters with types and defaults
        - Cluster/database configuration
        - Tags and categories for filtering
        - Usage statistics and performance notes
        - Example usage
        
        Perfect for: Finding the right flow to execute
        
        Args:
            tags: Filter by tags (e.g., ["imds", "wireserver", "subscriptions"])
            search: Search in flow names and descriptions
        
        Returns:
            JSON with:
            - total_flows: Number of flows found
            - categories: List of all available tags/categories
            - flows: Detailed flow information
            - quick_start: How to execute a flow
        """
        with measure_operation("flow_list"):
            try:
                # Get all flows
                all_flows = flows.list_templates(tags=tags, search=search)
                
                # Collect all unique categories/tags
                all_categories = set()
                for flow in all_flows:
                    if isinstance(flow, dict):
                        tags_list = flow.get("tags", [])
                        if isinstance(tags_list, str):
                            tags_list = [tags_list]
                        elif not isinstance(tags_list, list):
                            tags_list = []
                        
                        for tag in tags_list:
                            if tag and isinstance(tag, str):
                                all_categories.add(tag)
                
                # Build detailed flow information
                flow_details = []
                for flow in all_flows:
                    if not isinstance(flow, dict):
                        continue
                    
                    metadata = flow.get("metadata", {})
                    if not isinstance(metadata, dict):
                        metadata = {}
                    
                    parameters = flow.get("parameters", [])
                    if not isinstance(parameters, list):
                        parameters = []
                    
                    tags_list = flow.get("tags", [])
                    if isinstance(tags_list, str):
                        tags_list = [tags_list]
                    elif not isinstance(tags_list, list):
                        tags_list = []
                    
                    flow_info = {
                        "name": flow.get("name", "unnamed"),
                        "description": flow.get("description", ""),
                        "parameters": [
                            {
                                "name": p.get("name", "unknown") if isinstance(p, dict) else str(p),
                                "type": p.get("type", "string") if isinstance(p, dict) else "string",
                                "description": p.get("description", "") if isinstance(p, dict) else "",
                                "required": p.get("required", True) if isinstance(p, dict) else True,
                                "default": p.get("default_value") if isinstance(p, dict) else None
                            }
                            for p in parameters if p
                        ],
                        "configuration": {
                            "cluster": metadata.get("cluster", "Not specified"),
                            "database": metadata.get("database", "Not specified"),
                            "query_type": metadata.get("query_type", "unknown")
                        },
                        "tags": tags_list,
                        "performance_notes": metadata.get("performance_notes", ""),
                        "usage_stats": {
                            "use_count": flow.get("use_count", 0),
                            "last_used": flow.get("last_used"),
                            "avg_execution_time_ms": flow.get("estimated_execution_time_ms")
                        }
                    }
                    
                    usage_example = flow.get("usage_example") or metadata.get("usage_example")
                    if usage_example:
                        flow_info["usage_example"] = usage_example
                    
                    flow_details.append(flow_info)
                
                flow_details.sort(key=lambda x: x["name"])
                
                response = {
                    "success": True,
                    "total_flows": len(flow_details),
                    "categories": sorted(list(all_categories)),
                    "filters_applied": {
                        "tags": tags,
                        "search": search
                    },
                    "flows": flow_details,
                    "quick_start": {
                        "description": "To execute a flow, use flow_execute",
                        "example": 'flow_execute(name="flow_name", parameters={"param1": "value1"})'
                    }
                }
                
                if not flow_details:
                    if tags:
                        response["hint"] = f"No flows found with tags {tags}. Try flow_list() to see all categories."
                    elif search:
                        response["hint"] = f"No flows found matching '{search}'. Try flow_list() to see all flows."
                    else:
                        response["hint"] = "No flows available. Create flows using flow_create or add files to cache/templates/"
                else:
                    if len(flow_details) == 1:
                        response["hint"] = f"Found 1 flow. Execute it with: flow_execute(name='{flow_details[0]['name']}', parameters={{...}})"
                    else:
                        response["hint"] = f"Found {len(flow_details)} flows. Use tags filter to narrow down (e.g., flow_list(tags=['imds']))"
                
                return safe_json_dumps(response, indent=2)
                
            except Exception as e:
                logger.error(f"Failed to list flows: {e}", exc_info=True)
                raise ToolError(f"Failed to list flows: {str(e)}")

    @mcp.tool()
    async def flow_execute(
        name: str,
        parameters: Dict[str, Any],
        limit: int = 100,
        ctx: Context = None
    ) -> str:
        """
        ⚡ Execute a flow in ONE step - render and run the query, return results directly.
        
        This is the SIMPLEST way to run flows:
        - Renders the flow with your parameters
        - Executes the query on the configured cluster
        - Returns results directly (no manual query execution needed)
        - Exports data to file for further analysis
        
        Perfect for: Running pre-built flows like attested_endpoint_subs or reverse_schenker_affected_subs
        
        Args:
            name: Flow name (e.g., "attested_endpoint_subs")
            parameters: Parameter values (e.g., {"start_time": "ago(24h)", "end_time": "now()"})
            limit: Max rows to return (default: 100, max: 10000)
        
        Returns:
            JSON with:
            - success: Execution status
            - flow_name: Flow that was executed
            - results: Query results (first 100 rows for preview)
            - row_count: Total rows returned
            - columns: Column names
            - execution_time_ms: Query execution time
            - export_path: Path to exported data file (if results > 100 rows)
            - metadata: Flow metadata (cluster, database, tags, etc.)
        """
        if ctx:
            await ctx.info(f"Executing flow: {name}")
        
        with measure_operation("flow_execute"):
            try:
                # Get flow metadata
                flow_list = flows.list_templates(search=name)
                if not flow_list or flow_list[0]["name"] != name:
                    raise ToolError(f"Flow not found: {name}")
                
                flow_meta = flow_list[0]
                
                # Render flow
                success, query, errors = flows.render_template(name, parameters)
                if not success:
                    raise ToolError(f"Flow rendering failed: {errors}")
                
                if ctx:
                    await ctx.info("Flow rendered successfully")
                
                # Extract cluster/database from flow metadata
                metadata = flow_meta.get("metadata", {})
                cluster = metadata.get("cluster")
                database = metadata.get("database")
                
                if not cluster or not database:
                    available_metadata = list(metadata.keys()) if metadata else []
                    raise ToolError(
                        f"Flow '{name}' is missing required cluster/database metadata.\n"
                        f"Available metadata keys: {available_metadata}\n"
                        f"Required: cluster={cluster or 'MISSING'}, database={database or 'MISSING'}\n"
                        f"Please ensure the flow JSON contains: 'metadata': {{'cluster': 'cluster_name', 'database': 'database_name'}}"
                    )
                
                if ctx:
                    await ctx.info(f"Executing on {cluster}.{database}")
                
                # Execute query
                start_time = datetime.now()
                results, columns = await connection_manager.execute_query(
                    cluster=cluster,
                    database=database,
                    query=query,
                    timeout_seconds=None
                )
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                row_count = len(results)
                
                if ctx:
                    await ctx.info(f"Query completed: {row_count} rows in {execution_time_ms:.0f}ms")
                
                # Build response
                response = {
                    "success": True,
                    "flow_name": name,
                    "flow_description": flow_meta.get("description", ""),
                    "row_count": row_count,
                    "columns": [col["name"] for col in columns],
                    "column_types": {col["name"]: col["type"] for col in columns},
                    "execution_time_ms": execution_time_ms,
                    "parameters_used": parameters,
                    "metadata": {
                        "cluster": cluster,
                        "database": database,
                        "tags": flow_meta.get("tags", []),
                        "query_type": metadata.get("query_type", "unknown"),
                        "performance_notes": metadata.get("performance_notes", "")
                    }
                }
                
                # Always show preview (first 100 rows)
                preview_size = min(100, row_count)
                response["results"] = results[:preview_size]
                response["preview_size"] = preview_size
                
                # If more than 100 rows, export to file
                if row_count > 100:
                    import sys
                    export_dir = Path(sys.path[0]) / "exports"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{name}_{timestamp}.json"
                    filepath = export_dir / filename
                    
                    export_data = {
                        "flow_name": name,
                        "executed_at": datetime.now().isoformat(),
                        "parameters": parameters,
                        "row_count": row_count,
                        "columns": columns,
                        "results": results
                    }
                    
                    # Use safe JSON serialization to handle datetime objects in results
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(safe_json_dumps(export_data, indent=2))
                    
                    response["export_path"] = str(filepath)
                    response["note"] = f"Showing first {preview_size} rows. Full results exported to {filepath}"
                    
                    if ctx:
                        await ctx.info(f"Full results exported to {filepath}")
                
                return safe_json_dumps(response, indent=2)
                
            except Exception as e:
                logger.error(f"Flow execution failed: {e}", exc_info=True)
                if ctx:
                    await ctx.error(f"Flow execution failed: {str(e)}")
                raise ToolError(f"Flow execution failed: {str(e)}")

    @mcp.tool()
    def flow_find(
        request: str,
        tags: List[str] = None,
        ctx: Context = None
    ) -> str:
        """
        🔍 Find the right flow based on a natural language description.
        
        This tool helps you discover which flow to use by searching flow names,
        descriptions, and tags based on your natural language request.
        
        Perfect for: "I need to troubleshoot WireServer issues" or "Show me flows for subscription analysis"
        
        Args:
            request: Natural language description of what you want to do
            tags: Optional tags to filter by (e.g., ["wireserver", "troubleshooting"])
        
        Returns:
            JSON with:
            - matched_flows: List of flows that match your request
            - best_match: The most relevant flow for your request
            - suggestions: How to execute the matched flows
        """
        with measure_operation("flow_find"):
            try:
                # Get all flows
                all_flows = flows.list_templates(tags=tags)
                
                if not all_flows:
                    return safe_json_dumps({
                        "success": False,
                        "matched_flows": [],
                        "hint": "No flows available. Create flows using flow_create()"
                    }, indent=2)
                
                # Simple keyword-based matching
                request_lower = request.lower()
                keywords = request_lower.split()
                
                # Score each flow
                scored_flows = []
                for flow in all_flows:
                    if not isinstance(flow, dict):
                        continue
                    
                    score = 0
                    name = flow.get("name", "").lower()
                    description = flow.get("description", "").lower()
                    flow_tags = flow.get("tags", [])
                    if isinstance(flow_tags, str):
                        flow_tags = [flow_tags]
                    flow_tags_str = " ".join(str(t).lower() for t in flow_tags if t)
                    
                    # Check for keyword matches
                    for keyword in keywords:
                        if len(keyword) < 3:  # Skip very short words
                            continue
                        if keyword in name:
                            score += 10
                        if keyword in description:
                            score += 5
                        if keyword in flow_tags_str:
                            score += 7
                    
                    # Exact phrase match (bonus)
                    if request_lower in name or request_lower in description:
                        score += 20
                    
                    if score > 0:
                        scored_flows.append((score, flow))
                
                # Sort by score
                scored_flows.sort(key=lambda x: x[0], reverse=True)
                
                if not scored_flows:
                    return safe_json_dumps({
                        "success": False,
                        "matched_flows": [],
                        "hint": f"No flows matched '{request}'. Try flow_list() to see all available flows."
                    }, indent=2)
                
                # Format results
                matched_flows = []
                for score, flow in scored_flows[:5]:  # Top 5 matches
                    metadata = flow.get("metadata", {})
                    if not isinstance(metadata, dict):
                        metadata = {}
                    
                    matched_flows.append({
                        "name": flow.get("name"),
                        "description": flow.get("description"),
                        "relevance_score": score,
                        "tags": flow.get("tags", []),
                        "cluster": metadata.get("cluster"),
                        "database": metadata.get("database"),
                        "parameters": [p.get("name") if isinstance(p, dict) else str(p) 
                                     for p in flow.get("parameters", []) if p]
                    })
                
                best_match = matched_flows[0] if matched_flows else None
                
                response = {
                    "success": True,
                    "request": request,
                    "matched_flows": matched_flows,
                    "best_match": best_match,
                    "total_matches": len(matched_flows),
                    "suggestions": {
                        "description": "To execute a flow, use flow_execute",
                        "example": f'flow_execute(name="{best_match["name"]}", parameters={{...}})' if best_match else "flow_execute(name=flow_name, parameters={...})"
                    }
                }
                
                if ctx:
                    if best_match:
                        ctx.info(f"Best match: {best_match['name']} (score: {best_match['relevance_score']})")
                    ctx.info(f"Found {len(matched_flows)} matching flows")
                
                return safe_json_dumps(response, indent=2)
                
            except Exception as e:
                logger.error(f"Flow find failed: {e}", exc_info=True)
                raise ToolError(f"Flow find failed: {str(e)}")
