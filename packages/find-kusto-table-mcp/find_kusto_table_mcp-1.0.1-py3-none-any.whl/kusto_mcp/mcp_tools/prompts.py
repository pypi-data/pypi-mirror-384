"""
MCP prompts for Kusto server - reusable interaction patterns.

This module provides MCP prompts that load from the prompts/ directory.
"""

from ..core.logging_config import get_logger
from ..utils.prompt_loader import format_prompt, load_prompt

logger = get_logger("mcp_tools.prompts")


def register_prompts(mcp):
    """Register MCP prompts with the server."""

    @mcp.prompt()
    def prompt_discover_and_build_workflows() -> str:
        """
        Discover Kusto queries across multiple sources and build workflow templates.
        
        Systematically extracts KQL queries from files/directories, identifies parameters,
        groups related queries, and creates reusable templates.
        """
        return load_prompt("discover_and_build_workflows")
