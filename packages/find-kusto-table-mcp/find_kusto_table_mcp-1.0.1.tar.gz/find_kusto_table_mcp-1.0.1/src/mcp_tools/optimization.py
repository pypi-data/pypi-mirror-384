"""
Query optimization tools for Kusto MCP server.

This module previously contained query optimization tools that have been removed
to maintain focus on core Kusto discovery functionality.

For query optimization, users should:
- Use KQL's built-in query analysis features
- Leverage Kusto's native performance insights
- Follow KQL best practices documentation
"""

from ..core.logging_config import get_logger

logger = get_logger("mcp_tools.optimization")


def register_optimization_tools(mcp, services: dict):
    """
    Optimization tools have been removed to focus on core discovery features.
    
    This function is kept for backward compatibility but registers no tools.
    """
    pass  # No tools to register
