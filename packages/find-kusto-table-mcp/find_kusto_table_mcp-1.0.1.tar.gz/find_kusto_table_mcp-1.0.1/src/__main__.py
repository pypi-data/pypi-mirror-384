"""
Kusto MCP Server Entry Point

This module provides the main entry point for the find-kusto-table-mcp package.
It can be run as a module using: python -m kusto_mcp

The actual server code is in kusto_server.py at the root of the repository.
This entry point imports and runs it.
"""

import sys
import os

def main():
    """Main entry point for the MCP server"""
    # Set environment variables for proper operation
    os.environ['MCP_SERVER_MODE'] = 'true'
    os.environ['FASTMCP_QUIET'] = '1'
    
    # Fix Unicode encoding for Windows console
    if sys.platform == 'win32':
        try:
            import io
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass
    
    # Add the repository root to sys.path
    # When installed via pip/pipx, the package files are in site-packages
    # But kusto_server.py expects to be run from the repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to import from the installed location first
    try:
        # This import path works when installed via pip/pipx
        import kusto_server
        import asyncio
        
        # Run the FastMCP server
        asyncio.run(kusto_server.mcp.run())
    except ImportError:
        # Fallback: try to find kusto_server.py in parent directory (development mode)
        parent_dir = os.path.dirname(script_dir)
        kusto_server_path = os.path.join(parent_dir, 'kusto_server.py')
        
        if os.path.exists(kusto_server_path):
            sys.path.insert(0, parent_dir)
            import kusto_server
            import asyncio
            asyncio.run(kusto_server.mcp.run())
        else:
            print("Error: Could not find kusto_server.py", file=sys.stderr)
            print(f"Looked in: {parent_dir}", file=sys.stderr)
            print("Make sure the package is properly installed or run from the repository root", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
