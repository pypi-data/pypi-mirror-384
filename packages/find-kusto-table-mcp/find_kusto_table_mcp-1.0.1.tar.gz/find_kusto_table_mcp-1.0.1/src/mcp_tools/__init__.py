"""
MCP Tools Registration System

This module provides a centralized registration system for all MCP tools.
All tool modules are imported and registered here.
"""

from ..core.logging_config import get_logger

# Import individual tool registration functions
from .core_search import register_core_search_tools
from .query_execution import register_query_execution_tools
from .data_export import register_data_export_tools
from .query_development import register_query_development_tools
from .natural_language_query import register_natural_language_query_tool
from .analytics import register_analytics_tools
from .optimization import register_optimization_tools
from .templates import register_flow_tools
from .cache_management import register_cache_management_tools
from .verification import register_verification_tools
from .resources import register_resources
from .prompts import register_prompts

logger = get_logger("mcp_tools")


# ============================================================================
# BROAD CATEGORY ACTIVATION FUNCTIONS
# ============================================================================

def activate_query_tools(mcp, services: dict, default_export_dir: str):
    """
    Activate all QUERY-related tools (16 tools total)
    
    This category includes:
    - Table discovery and search (4 tools)
    - Query execution (1 tool - direct execution with auto-export)
    - Natural language query building (1 tool)
    - Query development (2 tools: validation, formatting)
    - Flow management (4 tools: create, list, execute, find)
    - Data export (1 tool: save_chart)
    - Verification & trust (3 tools: verify results, validate schema, create verification links)
    
    Use this when you need to:
    - Find and explore Kusto tables
    - Build and execute KQL queries
    - Work with reusable query flows
    - Export data to various formats
    - Verify AI responses and prevent hallucination
    
    Note: Query handles removed - execute_query now exports large results automatically.
    All query results include verification metadata for trust validation.
    """
    logger.info("Activating QUERY tools category...")
    
    # Core discovery and search (4 tools)
    register_core_search_tools(mcp, services)
    
    # Query execution (1 tool - simplified)
    register_query_execution_tools(mcp, services)
    
    # Natural language query (1 tool)
    register_natural_language_query_tool(mcp, services)
    
    # Query development (2 tools)
    register_query_development_tools(mcp, services)
    
    # Flows (4 tools: create, list, execute, find)
    register_flow_tools(mcp, services)
    
    # Data export (moved here from analytics)
    register_data_export_tools(mcp, services, default_export_dir)
    
    # Verification tools (3 tools) - NEW for trust/anti-hallucination
    register_verification_tools(mcp, services)
    
    logger.info("QUERY tools activated: 16 tools ready")


def activate_analytics_tools(mcp, services: dict, default_export_dir: str):
    """
    Activate all ANALYTICS-related tools (0 tools - REMOVED)
    
    Analytics tools have been removed. Use KQL's built-in functions instead:
    - Correlation: corr() function in KQL
    - Statistics: summarize avg(), stdev(), percentiles()
    - Anomalies: series_decompose_anomalies()
    - Time series: make-series, series_stats
    
    This function is kept for backwards compatibility but does nothing.
    """
    logger.info("ANALYTICS tools category is empty (tools removed - use KQL built-ins)")
    
    # All analytics tools removed - use KQL instead
    register_analytics_tools(mcp, services)
    
    logger.info("ANALYTICS tools: 0 tools (use KQL for analytics)")


def activate_admin_tools(mcp, services: dict):
    """
    Activate all ADMIN-related tools (2 tools total)
    
    This category includes:
    - Cache management and statistics
    - Performance monitoring
    
    Use this when you need to:
    - Monitor server performance
    - Manage cache and memory
    - Troubleshoot issues
    
    Note: Query optimization tools have been removed. Use KQL's native features instead.
    """
    logger.info("Activating ADMIN tools category...")
    
    # Cache management (2 tools)
    register_cache_management_tools(mcp, services)
    
    logger.info("ADMIN tools activated: 2 tools ready")


# ============================================================================
# MAIN REGISTRATION FUNCTION
# ============================================================================

def register_all_tools(mcp, services: dict, default_export_dir: str):
    """
    Register all MCP tools, resources, and prompts with the FastMCP server.
    
    This is the single entry point for registering all server capabilities.
    Uses 3 broad activation categories for simplified tool management.
    
    Args:
        mcp: FastMCP server instance
        services: Dictionary of initialized service objects
        default_export_dir: Default directory for data exports
    
    Tool Categories (3 broad groups):
        1. QUERY (16 tools): Discovery, execution, flows, natural language, export, verification
        2. ANALYTICS (0 tools): Removed - use KQL built-ins
        3. ADMIN (2 tools): Cache management, performance monitoring
    
    Total: 18 tools + 2 resources + 1 prompt
    """
    logger.info("Registering MCP tools with FastMCP server (3-category system)...")
    
    # Activate broad tool categories
    activate_query_tools(mcp, services, default_export_dir)
    activate_analytics_tools(mcp, services, default_export_dir)
    activate_admin_tools(mcp, services)
    
    # Register resources and prompts (always available)
    register_resources(mcp)
    logger.debug("Registered MCP resources (2 resources)")
    
    register_prompts(mcp)
    logger.debug("Registered MCP prompts (1 prompt)")
    
    logger.info("All MCP tools registered successfully")
    logger.info("  - QUERY: 16 tools (includes 3 verification tools)")
    logger.info("  - ANALYTICS: 0 tools (use KQL)")
    logger.info("  - ADMIN: 2 tools")
    logger.info("  - Resources: 2, Prompts: 1")


__all__ = [
    'register_all_tools',
    'activate_query_tools',
    'activate_analytics_tools', 
    'activate_admin_tools'
]
