#!/usr/bin/env python3
"""
Confluence MCP Server - HTTP Transport
A Model Context Protocol server for Confluence integration with HTTP transport support.
This enables deployment on platforms like Smithery.ai while maintaining compatibility with stdio transport.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any, Optional
from urllib.parse import unquote

# Third-Party Imports
from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# FastMCP and MCP Imports
from mcp.types import JSONRPCMessage

# Local imports - reuse the existing MCP server instance
from confluence_mcp_server.main import mcp_server

# Setup logging
logger = logging.getLogger(__name__)

class HttpTransport:
    """HTTP transport adapter for FastMCP server."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Confluence MCP Server",
            description="HTTP transport for Confluence MCP Server - Compatible with Smithery.ai",
            version="1.0.0"
        )
        self.setup_routes()
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup HTTP routes following MCP HTTP specification."""
        
        @self.app.get("/mcp")
        async def handle_mcp_get(config: Optional[str] = Query(None)):
            """Handle GET requests for tool listing (Smithery requirement)."""
            try:
                # Apply configuration if provided (base64 encoded)
                if config:
                    config_data = self._decode_config(config)
                    self._apply_config(config_data)
                
                # Get tools list without requiring authentication
                tools_response = await self._get_tools_list()
                return tools_response
                
            except Exception as e:
                logger.error(f"Error in GET /mcp: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp")
        async def handle_mcp_post(request: Request, config: Optional[str] = Query(None)):
            """Handle POST requests for tool execution."""
            try:
                # Apply configuration if provided
                if config:
                    config_data = self._decode_config(config)
                    self._apply_config(config_data)
                
                # Get the JSON-RPC message from request body
                body = await request.body()
                message = json.loads(body.decode())
                
                # Process the MCP request
                response = await self._process_mcp_message(message)
                return response
                
            except Exception as e:
                logger.error(f"Error in POST /mcp: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/mcp")
        async def handle_mcp_delete(config: Optional[str] = Query(None)):
            """Handle DELETE requests for session cleanup."""
            try:
                # Smithery.ai may send DELETE requests for cleanup
                return {"status": "success", "message": "Session cleaned up"}
                
            except Exception as e:
                logger.error(f"Error in DELETE /mcp: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "transport": "http"}
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            tools = await mcp_server._mcp_list_tools()
            return {
                "name": "Confluence MCP Server",
                "version": "1.0.0",
                "transport": "http",
                "endpoints": {
                    "mcp": "/mcp",
                    "health": "/health"
                },
                "tools_count": len(tools)
            }
    
    def _decode_config(self, config: str) -> Dict[str, Any]:
        """Decode base64 configuration from Smithery."""
        try:
            decoded = base64.b64decode(config).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            logger.error(f"Failed to decode config: {str(e)}")
            return {}
    
    def _apply_config(self, config_data: Dict[str, Any]):
        """Apply configuration to environment variables."""
        try:
            # Map configuration to environment variables
            env_mapping = {
                'confluenceUrl': 'CONFLUENCE_URL',
                'username': 'CONFLUENCE_USERNAME', 
                'apiToken': 'CONFLUENCE_API_TOKEN'
            }
            
            for config_key, env_var in env_mapping.items():
                if config_key in config_data:
                    os.environ[env_var] = config_data[config_key]
                    
        except Exception as e:
            logger.error(f"Failed to apply config: {str(e)}")
    
    async def _get_tools_list(self) -> Dict[str, Any]:
        """Get list of available tools for lazy loading."""
        try:
            # Get tools from FastMCP server using the correct method
            tools = await mcp_server._mcp_list_tools()
            
            # Convert to the expected format
            tools_list = []
            for tool in tools:
                tool_metadata = {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "inputSchema": tool.inputSchema
                }
                tools_list.append(tool_metadata)
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": tools_list
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tools list: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error getting tools: {str(e)}"
                }
            }
    
    async def _process_mcp_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process MCP JSON-RPC message through FastMCP server."""
        try:
            # Create a mock stdio transport for processing
            # This bridges HTTP requests to the FastMCP server
            
            if message.get("method") == "tools/list":
                return await self._handle_tools_list(message)
            elif message.get("method") == "tools/call":
                return await self._handle_tool_call(message)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {message.get('method')}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing MCP message: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_tools_list(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list requests."""
        try:
            tools = await mcp_server._mcp_list_tools()
            tools_list = []
            for tool in tools:
                tool_data = {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "inputSchema": tool.inputSchema
                }
                tools_list.append(tool_data)
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "tools": tools_list
                }
            }
            
        except Exception as e:
            logger.error(f"Error in tools/list: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_tool_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call requests."""
        try:
            params = message.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Get tools from FastMCP server
            tools = await mcp_server._mcp_list_tools()
            tool_map = {tool.name: tool for tool in tools}
            
            if tool_name not in tool_map:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            # Execute the tool through FastMCP's call mechanism
            try:
                # Use FastMCP's internal tool calling mechanism
                # FastMCP expects arguments to be wrapped in an 'inputs' object
                wrapped_arguments = {"inputs": arguments}
                result = await mcp_server._mcp_call_tool(tool_name, wrapped_arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": result
                }
                
            except Exception as tool_error:
                logger.error(f"Tool execution error for {tool_name}: {str(tool_error)}")
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(tool_error)}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in tools/call: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Load environment variables
    load_dotenv()
    
    # Create HTTP transport
    transport = HttpTransport()
    return transport.app


def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # For local development
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    print(f"Starting Confluence MCP Server (HTTP) on {host}:{port}")
    run_http_server(host, port) 