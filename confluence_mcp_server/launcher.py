#!/usr/bin/env python3
"""
Confluence MCP Server - Universal Launcher
Automatically detects and launches the appropriate transport mode (stdio or HTTP)
"""

import asyncio
import os
import sys
import argparse
import logging
from typing import Optional

def detect_transport_mode() -> str:
    """
    Detect which transport mode to use based on environment and context.
    
    Returns:
        str: 'stdio' or 'http'
    """
    # Check for explicit environment variable
    if os.getenv('MCP_TRANSPORT'):
        return os.getenv('MCP_TRANSPORT').lower()
    
    # Check for HTTP-specific environment variables (Smithery, cloud deployment)
    if os.getenv('PORT') or os.getenv('HOST'):
        return 'http'
    
    # Check if running in a container/cloud environment
    if os.getenv('KUBERNETES_SERVICE_HOST') or os.getenv('RAILWAY_ENVIRONMENT'):
        return 'http'
    
    # Check if stdout is a TTY (interactive terminal)
    if not sys.stdout.isatty():
        # Non-interactive, likely being called by MCP client
        return 'stdio'
    
    # Default to stdio for local development
    return 'stdio'


def setup_logging_for_mode(mode: str):
    """Setup appropriate logging for the transport mode."""
    if mode == 'stdio':
        # For stdio, only log to files to avoid interfering with JSON-RPC
        from confluence_mcp_server.utils.logging_config import setup_logging
        setup_logging()
    else:
        # For HTTP, can use console logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


async def launch_stdio():
    """Launch the stdio transport version."""
    try:
        from confluence_mcp_server.main import main
        await main()
    except ImportError as e:
        print(f"Failed to import stdio server: {e}", file=sys.stderr)
        sys.exit(1)


def launch_http(host: str = "0.0.0.0", port: int = 8000):
    """Launch the HTTP transport version."""
    try:
        from confluence_mcp_server.server_http import run_http_server
        run_http_server(host, port)
    except ImportError as e:
        print(f"Failed to import HTTP server: {e}", file=sys.stderr)
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Confluence MCP Server - Universal Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --stdio                    # Force stdio transport
  %(prog)s --http                     # Force HTTP transport  
  %(prog)s --http --port 9000         # HTTP on custom port
  %(prog)s                            # Auto-detect transport mode
  
Environment Variables:
  MCP_TRANSPORT      Force transport mode (stdio|http)
  CONFLUENCE_URL     Your Confluence instance URL
  CONFLUENCE_USERNAME Your Confluence username (email)
  CONFLUENCE_API_TOKEN Your Confluence API token
  PORT               HTTP server port (implies HTTP mode)
  HOST               HTTP server host (implies HTTP mode)
        """
    )
    
    # Transport selection
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument(
        '--stdio', 
        action='store_true',
        help='Force stdio transport (for Claude Desktop, etc.)'
    )
    transport_group.add_argument(
        '--http', 
        action='store_true',
        help='Force HTTP transport (for Smithery.ai, web clients, etc.)'
    )
    
    # HTTP-specific options
    parser.add_argument(
        '--host',
        default=os.getenv('HOST', '0.0.0.0'),
        help='HTTP server host (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('PORT', '8000')),
        help='HTTP server port (default: 8000)'
    )
    
    # General options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main launcher function."""
    args = parse_args()
    
    # Determine transport mode
    if args.stdio:
        mode = 'stdio'
    elif args.http:
        mode = 'http'
    else:
        mode = detect_transport_mode()
    
    # Setup logging
    setup_logging_for_mode(mode)
    logger = logging.getLogger(__name__)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting Confluence MCP Server in {mode} mode")
    
    try:
        if mode == 'stdio':
            logger.info("Using stdio transport (JSON-RPC over stdin/stdout)")
            asyncio.run(launch_stdio())
        else:
            logger.info(f"Using HTTP transport on {args.host}:{args.port}")
            launch_http(args.host, args.port)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 