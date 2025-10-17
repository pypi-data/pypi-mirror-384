"""
Analytics tools for Kusto MCP server.

This module provides correlation analysis for cached query results:
- analytics_correlation: Calculate correlation between two numeric columns
"""

from typing import Optional
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..utils.helpers import safe_json_dumps

logger = get_logger("mcp_tools.analytics")


def register_analytics_tools(mcp, services: dict):
    """Register analytics tools with the MCP server."""
    # Analytics tools removed - correlation analysis can be done directly in KQL
    # using built-in functions like toscalar(), correlation(), covariance(), etc.
    pass
