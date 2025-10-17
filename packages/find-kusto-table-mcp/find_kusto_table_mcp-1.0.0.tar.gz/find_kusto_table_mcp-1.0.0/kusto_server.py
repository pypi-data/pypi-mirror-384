#!/usr/bin/env python3
"""
Enhanced Kusto Table Search MCP Server - FastMCP Edition

A modern, production-ready MCP server built with FastMCP for Kusto table discovery,
query building, and anti-hallucination query execution.

Features:
- Smart table search across 9,799+ tables with lazy schema caching
- Query handle system to prevent context window pollution
- Reusable query templates and multi-query workflows
- Anti-hallucination: schema validation, sampling-based query building
- Analytics operations on cached results (4 powerful tools)
- Performance monitoring and metrics
- 26 focused, high-value tools

Usage:
    # Run locally with stdio (default)
    python kusto_server.py
    
    # Run with HTTP transport
    fastmcp run kusto_server.py --transport http --port 8000
    
    # Deploy to FastMCP Cloud
    fastmcp deploy kusto_server.py
"""

import sys
import os
import argparse

# CRITICAL: Set environment variables BEFORE any other imports
# This prevents FastMCP banner and fixes Unicode encoding issues
os.environ['MCP_SERVER_MODE'] = 'true'
os.environ['FASTMCP_QUIET'] = '1'  # Suppress FastMCP ASCII banner

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        # Set UTF-8 encoding for stderr to handle Unicode characters
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback silently if reconfiguration fails

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse command line arguments for configuration
parser = argparse.ArgumentParser(description='Enhanced Kusto MCP Server')
parser.add_argument('--cache-dir', default='cache', 
                   help='Directory for cache files (default: cache)')
parser.add_argument('--export-dir', default='exports',
                   help='Default directory for exports (default: exports)')
args, unknown = parser.parse_known_args()

# Global configuration
CACHE_DIR = os.path.abspath(args.cache_dir)
DEFAULT_EXPORT_DIR = os.path.abspath(args.export_dir)

# Create directories if they don't exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DEFAULT_EXPORT_DIR, exist_ok=True)

from fastmcp import FastMCP

# Import core services
from src.core.logging_config import setup_logging, get_logger
from src.server_init import initialize_services, load_confidential_templates
from src.mcp_tools import register_all_tools

# Setup logging - quiet mode for MCP server
setup_logging(
    level="INFO",
    log_file="logs/kusto_mcp.log",
    enable_console=True,
    enable_performance_logs=True
)
logger = get_logger("kusto_server")

# Initialize FastMCP server
mcp = FastMCP("Kusto Table Search")

# Initialize all services
services = initialize_services(CACHE_DIR)

# Auto-load confidential templates on server startup
load_confidential_templates(services['templates'])

# Register all MCP tools, resources, and prompts
register_all_tools(mcp, services, DEFAULT_EXPORT_DIR)


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Run the FastMCP server with configurable directories
    
    Command line options:
        --cache-dir DIR     Directory for cache files (default: cache)
        --export-dir DIR    Default directory for exports (default: exports)
    
    Examples:
        python kusto_server.py
        python kusto_server.py --cache-dir /tmp/kusto-cache --export-dir /tmp/exports
        fastmcp run kusto_server.py --transport http --port 8000
    
    The default transport is STDIO for local tool usage.
    For web deployment, use: fastmcp run kusto_server.py --transport http --port 8000
    For SSE compatibility: fastmcp run kusto_server.py --transport sse
    """
    # Quiet startup - logging goes to file only (console set to WARNING level)
    logger.info("Enhanced Kusto MCP Server starting...")
    logger.info(f"Services: Schema Cache, Query Handles, Templates, Discovery (9,799+ tables)")
    
    # Run with default STDIO transport
    mcp.run()
