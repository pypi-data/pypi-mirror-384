#!/usr/bin/env python3
"""
Enhanced Kusto Table Search MCP Server

A significantly improved MCP server with:
- Lazy-loading schema cache (no expensive upfront caching)
- Query handle system for result caching and analytics
- Query template/workflow system for reusable queries
- Sampling-based query builder for anti-hallucination
- Comprehensive anti-hallucination measures

Inspired by successful patterns from enhanced-ado-mcp.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import Tool, ServerCapabilities, InitializationOptions
from mcp.types import TextContent

# Import core modules
from src.core.logging_config import setup_logging, get_logger
from src.core.config import get_config
from src.core.performance import measure_operation, get_performance_summary
from src.core.exceptions import KustoMCPError, ValidationError

# Import services
from src.services.query_handle_service import get_query_handle_service
from src.services.schema_cache_service import get_schema_cache_service
from src.services.query_template_service import get_query_template_service, QueryParameter, ParameterType
from src.services.kql_query_builder_service import get_kql_builder_service, TableSample

# Import tools
from src.tools.table_discovery import create_smart_table_discovery
from src.tools.query_sampler import create_query_sampler

# Import utilities
from src.utils.kusto_client import get_connection_manager
from src.utils.anti_hallucination import create_anti_hallucination_guard
from src.utils.helpers import safe_json_dumps

# Setup enhanced logging
setup_logging(
    level="INFO",
    log_file="logs/kusto_mcp_enhanced.log",
    enable_console=True,
    enable_performance_logs=True
)
logger = get_logger("server")


class EnhancedKustoMCPServer:
    """Enhanced MCP Server for Kusto with advanced features"""
    
    def __init__(self):
        self.server = Server("enhanced-kusto-search")
        
        # Load configuration
        self.config = get_config()
        
        # Initialize services
        self.query_handle_service = get_query_handle_service()
        self.schema_cache_service = get_schema_cache_service()
        self.template_service = get_query_template_service()
        self.query_builder_service = get_kql_builder_service()
        
        # Initialize advanced tools
        self.table_discovery = create_smart_table_discovery()
        self.query_sampler = create_query_sampler()
        
        # Initialize utilities
        self.connection_manager = get_connection_manager()
        self.hallucination_guard = create_anti_hallucination_guard(self.schema_cache_service)
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Enhanced Kusto MCP Server initialized with advanced features")
    
    def _register_handlers(self):
        """Register all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            return [
                # Core search tool (enhanced)
                Tool(
                    name="search_kusto_tables",
                    description=(
                        "🔍 ENHANCED: Search for Kusto tables using natural language queries. "
                        "Now with lazy-loading schema cache for instant responses!\n\n"
                        "Features:\n"
                        "• Searches 9,799+ tables across multiple clusters\n"
                        "• Lazy-loads schema only when needed (no expensive startup)\n"
                        "• Caches results for super-fast repeat searches\n"
                        "• Returns actual column names and types (anti-hallucination)\n"
                        "• Multiple search strategies (keyword, fuzzy, contextual, hybrid)\n\n"
                        "Returns complete table info including verified schema, time columns, "
                        "and ready-to-run sample queries using ACTUAL column names."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query (e.g., 'WireServer request tables', 'node health monitoring')"
                            },
                            "method": {
                                "type": "string",
                                "enum": ["keyword", "fuzzy", "contextual", "hybrid"],
                                "default": "hybrid",
                                "description": "Search method (hybrid recommended)"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50,
                                "description": "Maximum results to return"
                            },
                            "fetch_schema": {
                                "type": "boolean",
                                "default": True,
                                "description": "Fetch actual schema from Kusto (cached for performance)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                
                # Query handle tools
                Tool(
                    name="kusto_execute_query_with_handle",
                    description=(
                        "🎯 Execute a KQL query and get a QUERY HANDLE instead of raw results.\n\n"
                        "Why use handles?\n"
                        "• Prevents context window pollution with large results\n"
                        "• Enables analytics on results without loading data\n"
                        "• Provides anti-hallucination guarantee (server stores actual results)\n"
                        "• Auto-expires after 1 hour\n\n"
                        "Perfect for: large queries, iterative analysis, result manipulation."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cluster": {"type": "string", "description": "Cluster name"},
                            "database": {"type": "string", "description": "Database name"},
                            "table": {"type": "string", "description": "Table name"},
                            "query": {"type": "string", "description": "KQL query to execute"},
                            "limit": {"type": "integer", "default": 1000, "description": "Row limit"}
                        },
                        "required": ["cluster", "database", "table", "query"]
                    }
                ),
                
                Tool(
                    name="kusto_query_handle_analyze",
                    description=(
                        "📊 Analyze query results WITHOUT loading them into context.\n\n"
                        "Supported operations:\n"
                        "• count - Get row count\n"
                        "• count_by - Count by column values\n"
                        "• unique_values - Get unique values for a column\n"
                        "• aggregate - Perform aggregations (sum, avg, min, max)\n"
                        "• filter - Filter results by condition\n"
                        "• top - Get top N results\n"
                        "• sample - Get random sample\n\n"
                        "Perfect for: exploring large results, data profiling, quick stats."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "handle": {"type": "string", "description": "Query handle from kusto_execute_query_with_handle"},
                            "operation": {
                                "type": "string",
                                "enum": ["count", "count_by", "unique_values", "aggregate", "filter", "top", "sample"],
                                "description": "Analysis operation to perform"
                            },
                            "column": {"type": "string", "description": "Column name (required for most operations)"},
                            "value": {"description": "Value for filter operations"},
                            "operator": {
                                "type": "string",
                                "enum": ["==", "!=", "contains", ">", "<"],
                                "description": "Operator for filter operations"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["sum", "avg", "min", "max", "count"],
                                "description": "Aggregation type"
                            },
                            "n": {"type": "integer", "description": "Number of results (for top/sample)"},
                            "limit": {"type": "integer", "description": "Limit for unique_values"}
                        },
                        "required": ["handle", "operation"]
                    }
                ),
                
                Tool(
                    name="kusto_query_handle_list",
                    description="📋 List all active query handles with metadata and expiration info.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_expired": {"type": "boolean", "default": False}
                        },
                        "required": []
                    }
                ),
                
                Tool(
                    name="kusto_query_handle_validate",
                    description="✅ Validate a query handle and get detailed metadata.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "handle": {"type": "string", "description": "Query handle to validate"}
                        },
                        "required": ["handle"]
                    }
                ),
                
                # Query template tools
                Tool(
                    name="kusto_template_create",
                    description=(
                        "💾 Create a reusable query template with parameters.\n\n"
                        "Perfect for:\n"
                        "• Frequently-run queries with different parameters\n"
                        "• Standardized analysis workflows\n"
                        "• Team query sharing\n\n"
                        "Example: 'recent_errors' template with {timespan} and {error_level} parameters"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Template name"},
                            "description": {"type": "string", "description": "Template description"},
                            "query": {"type": "string", "description": "KQL query with {parameter} placeholders"},
                            "parameters": {
                                "type": "array",
                                "description": "Parameter definitions",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string", "enum": ["string", "number", "datetime", "timespan", "boolean", "list"]},
                                        "description": {"type": "string"},
                                        "default_value": {"description": "Default value (optional)"},
                                        "required": {"type": "boolean", "default": True}
                                    },
                                    "required": ["name", "type", "description"]
                                }
                            },
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for organization"}
                        },
                        "required": ["name", "description", "query", "parameters"]
                    }
                ),
                
                Tool(
                    name="kusto_template_list",
                    description="📚 List all saved query templates with filtering options.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                            "search": {"type": "string", "description": "Search in name/description"}
                        },
                        "required": []
                    }
                ),
                
                Tool(
                    name="kusto_template_render",
                    description="🎨 Render a query template with parameter values.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Template name"},
                            "parameters": {
                                "type": "object",
                                "description": "Parameter values (key-value pairs)"
                            }
                        },
                        "required": ["name", "parameters"]
                    }
                ),
                
                # Query builder tools
                Tool(
                    name="kusto_sample_table",
                    description=(
                        "🔬 Sample a table to discover actual schema and column names.\n\n"
                        "Anti-hallucination feature:\n"
                        "• Fetches real schema from Kusto\n"
                        "• Returns actual column names and types\n"
                        "• Provides sample data for context\n"
                        "• Cached for performance\n\n"
                        "Use before writing queries to ensure correct column names!"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cluster": {"type": "string"},
                            "database": {"type": "string"},
                            "table": {"type": "string"},
                            "sample_size": {"type": "integer", "default": 10, "description": "Number of sample rows"}
                        },
                        "required": ["cluster", "database", "table"]
                    }
                ),
                
                Tool(
                    name="kusto_build_query",
                    description=(
                        "🏗️ Build a KQL query using ACTUAL column names from schema.\n\n"
                        "Query types:\n"
                        "• select - Basic SELECT with columns\n"
                        "• time_range - Time-filtered query\n"
                        "• aggregation - GROUP BY with aggregations\n"
                        "• search - Text search across columns\n\n"
                        "Automatically validates column names against actual schema!"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cluster": {"type": "string"},
                            "database": {"type": "string"},
                            "table": {"type": "string"},
                            "query_type": {
                                "type": "string",
                                "enum": ["select", "time_range", "aggregation", "search"],
                                "description": "Type of query to build"
                            },
                            "columns": {"type": "array", "items": {"type": "string"}, "description": "Column names"},
                            "time_column": {"type": "string", "description": "Time column (auto-detected if not specified)"},
                            "timespan": {"type": "string", "description": "Time range (e.g., '1h', '24h')"},
                            "group_by": {"type": "array", "items": {"type": "string"}},
                            "aggregations": {"type": "array", "items": {"type": "object"}},
                            "search_term": {"type": "string"},
                            "limit": {"type": "integer", "default": 100}
                        },
                        "required": ["cluster", "database", "table", "query_type"]
                    }
                ),
                
                Tool(
                    name="kusto_suggest_columns",
                    description=(
                        "💡 Get AI-powered column suggestions based on query purpose.\n\n"
                        "Purposes:\n"
                        "• time_filtering - Suggest datetime columns\n"
                        "• grouping - Suggest low-cardinality columns\n"
                        "• aggregation - Suggest numeric columns\n\n"
                        "Based on actual schema analysis!"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cluster": {"type": "string"},
                            "database": {"type": "string"},
                            "table": {"type": "string"},
                            "purpose": {
                                "type": "string",
                                "enum": ["time_filtering", "grouping", "aggregation"],
                                "description": "Query purpose"
                            }
                        },
                        "required": ["cluster", "database", "table", "purpose"]
                    }
                ),
                
                # Cache management tools
                Tool(
                    name="kusto_cache_stats",
                    description="📈 Get statistics about schema cache and query handle usage.",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                
                Tool(
                    name="kusto_cache_clear",
                    description="🗑️ Clear expired cache entries (query handles and schema cache).",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                
                # Advanced validation and sampling tools
                Tool(
                    name="kusto_validate_query",
                    description=(
                        "✅ ANTI-HALLUCINATION: Validate a KQL query against actual table schema.\n\n"
                        "Features:\n"
                        "• Validates column names against real schema\n"
                        "• Checks query syntax and safety\n"
                        "• Optional sample execution with limited results\n"
                        "• Provides suggestions for improvements\n\n"
                        "Prevents AI hallucination of column names and query syntax!"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cluster": {"type": "string"},
                            "database": {"type": "string"},
                            "table": {"type": "string"},
                            "query": {"type": "string", "description": "KQL query to validate"},
                            "sample_execution": {"type": "boolean", "default": True, "description": "Test query with small limit"},
                            "get_suggestions": {"type": "boolean", "default": False, "description": "Get improvement suggestions"}
                        },
                        "required": ["cluster", "database", "table", "query"]
                    }
                ),
                
                Tool(
                    name="kusto_get_table_details",
                    description=(
                        "📋 Get comprehensive details about a specific table.\n\n"
                        "Includes:\n"
                        "• Complete schema with column types\n"
                        "• Example queries for common use cases\n"
                        "• Optional sample data\n"
                        "• Performance characteristics\n\n"
                        "Perfect for understanding table structure before writing queries."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cluster": {"type": "string"},
                            "database": {"type": "string"},
                            "table": {"type": "string"},
                            "include_sample": {"type": "boolean", "default": False},
                            "sample_size": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20}
                        },
                        "required": ["cluster", "database", "table"]
                    }
                ),
                
                Tool(
                    name="kusto_performance_stats",
                    description=(
                        "📈 Get performance statistics and monitoring data.\n\n"
                        "Provides:\n"
                        "• Operation performance metrics\n"
                        "• Cache hit rates and statistics\n"
                        "• Query execution times\n"
                        "• System health indicators\n\n"
                        "Useful for optimizing query performance and monitoring system health."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "description": "Specific operation to get stats for (optional)"},
                            "include_cache_stats": {"type": "boolean", "default": True},
                            "include_recent_queries": {"type": "boolean", "default": False}
                        },
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            logger.info(f"Tool call: {name} with args: {arguments}")
            
            try:
                # Route to appropriate handler
                if name == "search_kusto_tables":
                    result = await self._handle_search_tables(arguments)
                elif name == "kusto_execute_query_with_handle":
                    result = await self._handle_execute_with_handle(arguments)
                elif name == "kusto_query_handle_analyze":
                    result = await self._handle_analyze_handle(arguments)
                elif name == "kusto_query_handle_list":
                    result = await self._handle_list_handles(arguments)
                elif name == "kusto_query_handle_validate":
                    result = await self._handle_validate_handle(arguments)
                elif name == "kusto_template_create":
                    result = await self._handle_create_template(arguments)
                elif name == "kusto_template_list":
                    result = await self._handle_list_templates(arguments)
                elif name == "kusto_template_render":
                    result = await self._handle_render_template(arguments)
                elif name == "kusto_sample_table":
                    result = await self._handle_sample_table(arguments)
                elif name == "kusto_build_query":
                    result = await self._handle_build_query(arguments)
                elif name == "kusto_suggest_columns":
                    result = await self._handle_suggest_columns(arguments)
                elif name == "kusto_cache_stats":
                    result = await self._handle_cache_stats(arguments)
                elif name == "kusto_cache_clear":
                    result = await self._handle_cache_clear(arguments)
                elif name == "kusto_validate_query":
                    result = await self._handle_validate_query(arguments)
                elif name == "kusto_get_table_details":
                    result = await self._handle_get_table_details(arguments)
                elif name == "kusto_performance_stats":
                    result = await self._handle_performance_stats(arguments)
                else:
                    result = f"Error: Unknown tool: {name}"
                
                return [TextContent(type="text", text=result)]
            
            except Exception as e:
                logger.error(f"Error in {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    # Tool handler implementations
    
    async def _handle_search_tables(self, args: Dict[str, Any]) -> str:
        """Handle table search requests using enhanced table discovery"""
        with measure_operation("handle_search_tables"):
            query = args.get("query", "").strip()
            method = args.get("method", "hybrid")
            limit = args.get("limit", 10)
            fetch_schema = args.get("fetch_schema", True)
            
            if not query:
                return safe_json_dumps({"error": "Query parameter is required"}, indent=2)
            
            try:
                # Use enhanced table discovery
                results = await self.table_discovery.search_tables(
                    query=query,
                    method=method,
                    limit=limit,
                    fetch_schema=fetch_schema,
                    cache_results=True
                )
                
                return safe_json_dumps(results, indent=2)
                
            except Exception as e:
                logger.error(f"Table search failed: {e}")
                return safe_json_dumps({
                    "error": f"Search failed: {str(e)}",
                    "query": query,
                    "method": method
                }, indent=2)
    
    async def _handle_execute_with_handle(self, args: Dict[str, Any]) -> str:
        """Execute query and return handle"""
        with measure_operation("handle_execute_with_handle"):
            cluster = args["cluster"]
            database = args["database"]
            table = args["table"]
            query = args["query"]
            limit = args.get("limit", 1000)
            
            try:
                # Validate query against schema first
                is_valid, errors, warnings = self.hallucination_guard.validate_query_against_schema(
                    query, cluster, database, table
                )
                
                if not is_valid:
                    return safe_json_dumps({
                        "success": False,
                        "errors": errors,
                        "warnings": warnings
                    }, indent=2)
                
                # Execute query
                start_time = time.perf_counter()
                results, columns = await self.connection_manager.execute_query(
                    cluster, database, query
                )
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                
                # Apply limit if specified
                if limit and len(results) > limit:
                    results = results[:limit]
                
                # Store in query handle service
                handle = self.query_handle_service.store_query_results(
                    query=query,
                    table_path=f"{cluster}.{database}.{table}",
                    cluster=cluster,
                    database=database,
                    table=table,
                    results=results,
                    columns=columns,
                    execution_time_ms=execution_time_ms
                )
                
                result = {
                    "success": True,
                    "handle": handle,
                    "row_count": len(results),
                    "columns": [c["name"] for c in columns],
                    "execution_time_ms": round(execution_time_ms, 2),
                    "expires_in_hours": 1,
                    "warnings": warnings,
                    "usage_instructions": [
                        "Use kusto_query_handle_analyze to analyze results without loading into context",
                        "Use kusto_query_handle_validate to check handle status",
                        "Handle expires after 1 hour"
                    ]
                }
                
                logger.info(f"Query executed successfully: {len(results)} rows in {execution_time_ms:.2f}ms")
                return safe_json_dumps(result, indent=2)
                
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                return safe_json_dumps({
                    "success": False,
                    "error": str(e),
                    "query": query
                }, indent=2)
    
    async def _handle_analyze_handle(self, args: Dict[str, Any]) -> str:
        """Analyze query results via handle"""
        handle = args["handle"]
        operation = args["operation"]
        
        # Extract operation-specific parameters
        kwargs = {}
        for key in ["column", "value", "operator", "type", "n", "limit"]:
            if key in args:
                kwargs[key] = args[key]
        
        # Perform analysis
        result = self.query_handle_service.analyze_results(handle, operation, **kwargs)
        
        if result is None:
            return json.dumps({"error": "Handle not found or expired"}, indent=2)
        
        return json.dumps(result, indent=2)
    
    async def _handle_list_handles(self, args: Dict[str, Any]) -> str:
        """List all query handles"""
        include_expired = args.get("include_expired", False)
        handles = self.query_handle_service.list_handles(include_expired=include_expired)
        
        return json.dumps({
            "total_handles": len(handles),
            "handles": handles
        }, indent=2)
    
    async def _handle_validate_handle(self, args: Dict[str, Any]) -> str:
        """Validate a query handle"""
        handle = args["handle"]
        validation = self.query_handle_service.validate_handle(handle)
        
        return json.dumps(validation, indent=2)
    
    async def _handle_create_template(self, args: Dict[str, Any]) -> str:
        """Create a query template"""
        name = args["name"]
        description = args["description"]
        query = args["query"]
        param_defs = args["parameters"]
        tags = args.get("tags", [])
        
        # Convert parameter definitions
        parameters = []
        for p in param_defs:
            param = QueryParameter(
                name=p["name"],
                type=ParameterType(p["type"]),
                description=p["description"],
                default_value=p.get("default_value"),
                required=p.get("required", True)
            )
            parameters.append(param)
        
        # Create template
        success, error = self.template_service.create_template(
            name=name,
            description=description,
            query=query,
            parameters=parameters,
            tags=tags
        )
        
        result = {
            "success": success,
            "error": error if not success else None,
            "template_name": name if success else None
        }
        
        return json.dumps(result, indent=2)
    
    async def _handle_list_templates(self, args: Dict[str, Any]) -> str:
        """List query templates"""
        tags = args.get("tags")
        search = args.get("search")
        
        templates = self.template_service.list_templates(tags=tags, search=search)
        
        return json.dumps({
            "total_templates": len(templates),
            "templates": templates
        }, indent=2)
    
    async def _handle_render_template(self, args: Dict[str, Any]) -> str:
        """Render a query template"""
        name = args["name"]
        parameters = args["parameters"]
        
        success, query, errors = self.template_service.render_template(name, parameters)
        
        result = {
            "success": success,
            "query": query if success else None,
            "errors": errors if errors else None
        }
        
        return json.dumps(result, indent=2)
    
    async def _handle_sample_table(self, args: Dict[str, Any]) -> str:
        """Sample a table for schema discovery using advanced query sampler"""
        with measure_operation("handle_sample_table"):
            cluster = args["cluster"]
            database = args["database"]
            table = args["table"]
            sample_size = args.get("sample_size", 10)
            
            try:
                # Use advanced query sampler
                sample_result = await self.query_sampler.sample_table_for_query_building(
                    cluster=cluster,
                    database=database,
                    table=table,
                    sample_size=sample_size,
                    include_schema=True
                )
                
                # Convert to TableSample for query builder service compatibility
                if "schema" in sample_result:
                    table_sample = TableSample(
                        table_path=sample_result["table_path"],
                        cluster=cluster,
                        database=database,
                        table=table,
                        sample_rows=sample_result["sample_rows"],
                        columns=[{"name": col["name"], "type": col["type"]} for col in sample_result["schema"]["columns"]],
                        sample_size=sample_result["sample_size"],
                        total_row_count=None,
                        sampled_at=sample_result["sampled_at"]
                    )
                    
                    # Store in query builder service
                    self.query_builder_service.store_sample(table_sample)
                
                logger.info(f"Successfully sampled table {cluster}.{database}.{table}: {sample_result['sample_size']} rows")
                return safe_json_dumps(sample_result, indent=2)
                
            except Exception as e:
                logger.error(f"Table sampling failed: {e}")
                return safe_json_dumps({
                    "error": str(e),
                    "table_path": f"{cluster}.{database}.{table}"
                }, indent=2)
    
    async def _handle_build_query(self, args: Dict[str, Any]) -> str:
        """Build a KQL query using validated schema"""
        cluster = args["cluster"]
        database = args["database"]
        table = args["table"]
        query_type = args["query_type"]
        
        # Get query builder
        builder = self.query_builder_service.create_query_builder(cluster, database, table)
        if not builder:
            return json.dumps({
                "error": "Table not sampled. Use kusto_sample_table first to discover schema."
            }, indent=2)
        
        # Build query based on type
        if query_type == "select":
            columns = args.get("columns")
            limit = args.get("limit", 100)
            success, query, errors = builder.build_select_query(columns, limit)
        
        elif query_type == "time_range":
            time_column = args.get("time_column")
            timespan = args.get("timespan", "1h")
            limit = args.get("limit", 100)
            success, query, errors = builder.build_time_range_query(time_column, timespan, limit)
        
        elif query_type == "aggregation":
            group_by = args.get("group_by", [])
            aggregations = args.get("aggregations", [])
            time_column = args.get("time_column")
            time_bin = args.get("time_bin")
            timespan = args.get("timespan")
            success, query, errors = builder.build_aggregation_query(
                group_by, aggregations, time_column, time_bin, timespan
            )
        
        elif query_type == "search":
            search_term = args.get("search_term", "")
            search_columns = args.get("columns")
            limit = args.get("limit", 100)
            success, query, errors = builder.build_search_query(search_term, search_columns, False, limit)
        
        else:
            success = False
            query = ""
            errors = [f"Unknown query type: {query_type}"]
        
        result = {
            "success": success,
            "query": query if success else None,
            "errors": errors if errors else None,
            "validated_columns": builder.columns if success else None
        }
        
        return json.dumps(result, indent=2)
    
    async def _handle_suggest_columns(self, args: Dict[str, Any]) -> str:
        """Suggest columns based on purpose"""
        cluster = args["cluster"]
        database = args["database"]
        table = args["table"]
        purpose = args["purpose"]
        
        suggestions = self.query_builder_service.suggest_columns(
            cluster, database, table, purpose
        )
        
        return json.dumps({
            "purpose": purpose,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }, indent=2)
    
    async def _handle_cache_stats(self, args: Dict[str, Any]) -> str:
        """Get cache statistics"""
        with measure_operation("handle_cache_stats"):
            result = {
                "schema_cache": self.schema_cache_service.get_stats(),
                "query_handles": self.query_handle_service.get_stats(),
                "query_templates": self.template_service.get_stats(),
                "table_discovery": self.table_discovery.get_cache_stats(),
                "timestamp": datetime.now().isoformat()
            }
            
            return safe_json_dumps(result, indent=2)
    
    async def _handle_cache_clear(self, args: Dict[str, Any]) -> str:
        """Clear expired cache entries"""
        with measure_operation("handle_cache_clear"):
            schema_cleared = self.schema_cache_service.clear_expired()
            handles_cleared = self.query_handle_service.cleanup_expired()
            
            # Also clear search cache
            self.table_discovery.clear_search_cache()
            
            result = {
                "schema_cache_cleared": schema_cleared,
                "query_handles_cleared": handles_cleared,
                "search_cache_cleared": True,
                "total_cleared": schema_cleared + handles_cleared
            }
            
            logger.info(f"Cache cleanup completed: {result['total_cleared']} items cleared")
            return safe_json_dumps(result, indent=2)
    
    async def _handle_validate_query(self, args: Dict[str, Any]) -> str:
        """Validate a KQL query against schema with anti-hallucination checks"""
        with measure_operation("handle_validate_query"):
            cluster = args["cluster"]
            database = args["database"]
            table = args["table"]
            query = args["query"]
            sample_execution = args.get("sample_execution", True)
            get_suggestions = args.get("get_suggestions", False)
            
            try:
                # Use query sampler for comprehensive validation
                validation_result = await self.query_sampler.validate_query_with_sampling(
                    cluster=cluster,
                    database=database,
                    table=table,
                    query=query,
                    sample_execution=sample_execution
                )
                
                # Add suggestions if requested
                if get_suggestions and validation_result["valid"]:
                    suggestions = await self.query_sampler.suggest_query_improvements(
                        cluster=cluster,
                        database=database,
                        table=table,
                        query=query
                    )
                    validation_result["suggestions"] = suggestions
                
                logger.info(f"Query validation completed: {'VALID' if validation_result['valid'] else 'INVALID'}")
                return safe_json_dumps(validation_result, indent=2)
                
            except Exception as e:
                logger.error(f"Query validation failed: {e}")
                return safe_json_dumps({
                    "valid": False,
                    "errors": [str(e)],
                    "warnings": [],
                    "query": query
                }, indent=2)
    
    async def _handle_get_table_details(self, args: Dict[str, Any]) -> str:
        """Get comprehensive table details with schema and examples"""
        with measure_operation("handle_get_table_details"):
            cluster = args["cluster"]
            database = args["database"]
            table = args["table"]
            include_sample = args.get("include_sample", False)
            sample_size = args.get("sample_size", 5)
            
            try:
                # Use table discovery for comprehensive details
                details = await self.table_discovery.get_table_details(
                    cluster=cluster,
                    database=database,
                    table=table,
                    include_sample=include_sample,
                    sample_size=sample_size
                )
                
                logger.info(f"Retrieved table details for {cluster}.{database}.{table}")
                return safe_json_dumps(details, indent=2)
                
            except Exception as e:
                logger.error(f"Failed to get table details: {e}")
                return safe_json_dumps({
                    "error": str(e),
                    "table_path": f"{cluster}.{database}.{table}"
                }, indent=2)
    
    async def _handle_performance_stats(self, args: Dict[str, Any]) -> str:
        """Get performance statistics and monitoring data"""
        with measure_operation("handle_performance_stats"):
            operation = args.get("operation")
            include_cache_stats = args.get("include_cache_stats", True)
            include_recent_queries = args.get("include_recent_queries", False)
            
            try:
                # Get overall performance summary
                perf_summary = get_performance_summary()
                
                result = {
                    "performance_summary": perf_summary,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add specific operation stats if requested
                if operation:
                    from src.core.performance import get_operation_stats
                    op_stats = get_operation_stats(operation)
                    if op_stats:
                        result["operation_stats"] = op_stats
                    else:
                        result["operation_stats"] = f"No stats found for operation: {operation}"
                
                # Add cache statistics if requested
                if include_cache_stats:
                    result["cache_stats"] = {
                        "schema_cache": self.schema_cache_service.get_stats(),
                        "query_handles": self.query_handle_service.get_stats(),
                        "query_templates": self.template_service.get_stats(),
                        "table_discovery": self.table_discovery.get_cache_stats()
                    }
                
                # Add recent query information if requested
                if include_recent_queries:
                    recent_handles = self.query_handle_service.list_handles(include_expired=False)
                    result["recent_queries"] = recent_handles[-10:]  # Last 10 queries
                
                return safe_json_dumps(result, indent=2)
                
            except Exception as e:
                logger.error(f"Failed to get performance stats: {e}")
                return safe_json_dumps({"error": str(e)}, indent=2)
    
    async def run(self):
        """Run the MCP server"""
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Starting Enhanced Kusto MCP Server...")
                logger.info(f"Services initialized:")
                logger.info(f"  - Query Handle Service: ✓")
                logger.info(f"  - Schema Cache Service: ✓")
                logger.info(f"  - Query Template Service: ✓")
                logger.info(f"  - Query Builder Service: ✓")
                
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="enhanced-kusto-search",
                        server_version="2.0.0",
                        capabilities=ServerCapabilities(tools={})
                    )
                )
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            raise


async def main():
    """Main entry point"""
    server = EnhancedKustoMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
