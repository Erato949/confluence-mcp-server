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
import httpx

# Setup logging
logger = logging.getLogger(__name__)

class HttpTransport:
    """HTTP transport adapter for MCP server with lazy loading."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Confluence MCP Server",
            description="HTTP transport for Confluence MCP Server - Compatible with Smithery.ai",
            version="1.1.0"
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
                # Return the result directly, not wrapped in JSON-RPC format for GET requests
                return tools_response["result"]
                
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
            tools_response = await self._get_tools_list()
            tools_count = len(tools_response.get("result", {}).get("tools", []))
            return {
                "name": "Confluence MCP Server",
                "version": "1.1.0",
                "transport": "http",
                "endpoints": {
                    "mcp": "/mcp",
                    "health": "/health"
                },
                "tools_count": tools_count
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
        """Get list of available tools for lazy loading (no authentication required)."""
        try:
            # Static tool definitions for lazy loading - no Confluence connection needed
            tools_list = [
                {
                    "name": "get_confluence_page",
                    "description": "Retrieve a Confluence page by ID or URL with full content and metadata",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Confluence page ID"},
                            "page_url": {"type": "string", "description": "Confluence page URL"},
                            "expand": {"type": "string", "description": "Comma-separated list of properties to expand"}
                        }
                    }
                },
                {
                    "name": "search_confluence_pages",
                    "description": "Search for Confluence pages using CQL (Confluence Query Language)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "cql": {"type": "string", "description": "CQL query string"},
                            "limit": {"type": "integer", "description": "Maximum number of results"},
                            "start": {"type": "integer", "description": "Starting index for pagination"}
                        },
                        "required": ["cql"]
                    }
                },
                {
                    "name": "create_confluence_page",
                    "description": "Create a new Confluence page in a specified space",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "space_key": {"type": "string", "description": "Space key where to create the page"},
                            "title": {"type": "string", "description": "Page title"},
                            "content": {"type": "string", "description": "Page content in Confluence storage format"},
                            "parent_id": {"type": "string", "description": "Parent page ID (optional)"}
                        },
                        "required": ["space_key", "title", "content"]
                    }
                },
                {
                    "name": "update_confluence_page",
                    "description": "Update an existing Confluence page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Page ID to update"},
                            "title": {"type": "string", "description": "New page title"},
                            "content": {"type": "string", "description": "New page content in Confluence storage format"},
                            "version_number": {"type": "integer", "description": "Current version number"}
                        },
                        "required": ["page_id", "title", "content"]
                    }
                },
                {
                    "name": "delete_confluence_page",
                    "description": "Delete a Confluence page (moves to trash)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Page ID to delete"}
                        },
                        "required": ["page_id"]
                    }
                },
                {
                    "name": "get_confluence_spaces",
                    "description": "List available Confluence spaces with metadata",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Maximum number of spaces to return"},
                            "start": {"type": "integer", "description": "Starting index for pagination"}
                        }
                    }
                },
                {
                    "name": "get_page_attachments",
                    "description": "Get list of attachments for a Confluence page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Page ID to get attachments from"}
                        },
                        "required": ["page_id"]
                    }
                },
                {
                    "name": "add_page_attachment",
                    "description": "Add an attachment to a Confluence page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Page ID to attach file to"},
                            "file_path": {"type": "string", "description": "Local path to file to upload"},
                            "comment": {"type": "string", "description": "Optional comment for the attachment"}
                        },
                        "required": ["page_id", "file_path"]
                    }
                },
                {
                    "name": "delete_page_attachment",
                    "description": "Delete an attachment from a Confluence page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "attachment_id": {"type": "string", "description": "Attachment ID to delete"}
                        },
                        "required": ["attachment_id"]
                    }
                },
                {
                    "name": "get_page_comments",
                    "description": "Get comments for a Confluence page",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Page ID to get comments from"},
                            "expand": {"type": "string", "description": "Comma-separated list of properties to expand"}
                        },
                        "required": ["page_id"]
                    }
                }
            ]
            
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
        """Process MCP JSON-RPC message."""
        try:
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
            # Use the same static tool definitions as _get_tools_list
            tools_response = await self._get_tools_list()
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": tools_response["result"]
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
    
    async def _get_confluence_client(self) -> httpx.AsyncClient:
        """Create authenticated Confluence client."""
        confluence_url = os.getenv("CONFLUENCE_URL")
        username = os.getenv("CONFLUENCE_USERNAME") 
        api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        if not all([confluence_url, username, api_token]):
            raise HTTPException(status_code=400, detail="Missing Confluence credentials")
        
        base_url = confluence_url.rstrip('/')
        
        client = httpx.AsyncClient(
            base_url=base_url,
            auth=(username, api_token),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        return client
    
    async def _handle_tool_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call requests."""
        try:
            params = message.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Import tool logic only when needed (lazy loading)
            try:
                from confluence_mcp_server.mcp_actions import page_actions, space_actions, attachment_actions, comment_actions
            except ImportError as e:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Failed to load tool actions: {str(e)}"
                    }
                }
            
            # Execute tool based on name
            try:
                async with await self._get_confluence_client() as client:
                    if tool_name == "get_confluence_page":
                        from confluence_mcp_server.mcp_actions.schemas import GetPageInput
                        inputs = GetPageInput(**arguments)
                        result = await page_actions.get_page_logic(client, inputs)
                    elif tool_name == "search_confluence_pages":
                        from confluence_mcp_server.mcp_actions.schemas import SearchPagesInput
                        inputs = SearchPagesInput(**arguments)
                        result = await page_actions.search_pages_logic(client, inputs)
                    elif tool_name == "create_confluence_page":
                        from confluence_mcp_server.mcp_actions.schemas import CreatePageInput
                        inputs = CreatePageInput(**arguments)
                        result = await page_actions.create_page_logic(client, inputs)
                    elif tool_name == "update_confluence_page":
                        from confluence_mcp_server.mcp_actions.schemas import UpdatePageInput
                        inputs = UpdatePageInput(**arguments)
                        result = await page_actions.update_page_logic(client, inputs)
                    elif tool_name == "delete_confluence_page":
                        from confluence_mcp_server.mcp_actions.schemas import DeletePageInput
                        inputs = DeletePageInput(**arguments)
                        result = await page_actions.delete_page_logic(client, inputs)
                    elif tool_name == "get_confluence_spaces":
                        from confluence_mcp_server.mcp_actions.schemas import GetSpacesInput
                        inputs = GetSpacesInput(**arguments)
                        result = await space_actions.get_spaces_logic(client, inputs)
                    elif tool_name == "get_page_attachments":
                        from confluence_mcp_server.mcp_actions.schemas import GetAttachmentsInput
                        inputs = GetAttachmentsInput(**arguments)
                        result = await attachment_actions.get_attachments_logic(client, inputs)
                    elif tool_name == "add_page_attachment":
                        from confluence_mcp_server.mcp_actions.schemas import AddAttachmentInput
                        inputs = AddAttachmentInput(**arguments)
                        result = await attachment_actions.add_attachment_logic(client, inputs)
                    elif tool_name == "delete_page_attachment":
                        from confluence_mcp_server.mcp_actions.schemas import DeleteAttachmentInput
                        inputs = DeleteAttachmentInput(**arguments)
                        result = await attachment_actions.delete_attachment_logic(client, inputs)
                    elif tool_name == "get_page_comments":
                        from confluence_mcp_server.mcp_actions.schemas import GetCommentsInput
                        inputs = GetCommentsInput(**arguments)
                        result = await comment_actions.get_comments_logic(client, inputs)
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "error": {
                                "code": -32602,
                                "message": f"Unknown tool: {tool_name}"
                            }
                        }
                
                # Convert result to dict if it's a Pydantic model
                if hasattr(result, 'model_dump'):
                    # Use mode='json' to ensure HttpUrl objects are serialized as strings
                    result_dict = result.model_dump(mode='json')
                else:
                    result_dict = result
                
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_dict, indent=2)
                            }
                        ]
                    }
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