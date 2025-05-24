#!/usr/bin/env python3
"""
Entry point for running the Confluence MCP Server modules directly.
"""

import sys

if __name__ == "__main__":
    # Support different module execution modes
    if len(sys.argv) > 1 and sys.argv[1] == "server_http_optimized":
        from confluence_mcp_server.server_http_optimized import run_server
        run_server()
    elif len(sys.argv) > 1 and sys.argv[1] == "server_http":
        from confluence_mcp_server.server_http import run_http_server
        run_http_server()
    else:
        # Default to stdio server (Claude Desktop)
        from confluence_mcp_server.main import main
        main() 