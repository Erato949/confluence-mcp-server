#!/usr/bin/env python3
"""
Confluence MCP Server - Optimized HTTP Transport for Smithery.ai
Ultra-fast startup with guaranteed lazy loading compliance.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedHttpTransport:
    """Ultra-optimized HTTP transport for Smithery.ai with guaranteed lazy loading."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Confluence MCP Server",
            description="Optimized for Smithery.ai deployment",
            version="1.1.0"
        )
        self._setup_middleware()
        self._setup_routes()
        
        # Pre-compute static tool definitions for fastest response
        self._static_tools = self._get_static_tool_definitions()
    
    def _setup_middleware(self):
        """Setup minimal CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup routes with focus on speed and lazy loading."""
        
        @self.app.get("/health")
        async def health():
            """Ultra-fast health check."""
            return {"status": "healthy"}
        
        @self.app.get("/")
        async def root():
            """Server info with tool count."""
            return {
                "name": "Confluence MCP Server",
                "version": "1.1.0",
                "tools_count": len(self._static_tools),
                "lazy_loading": True
            }
        
        @self.app.get("/mcp")
        async def get_tools(config: Optional[str] = Query(None)):
            """
            SMITHERY.AI LAZY LOADING: Return tools without authentication.
            CRITICAL: This endpoint MUST respond instantly for Smithery tool scanning.
            """
            logger.info("Tool listing requested - returning static definitions (no auth)")
            
            # Apply config to environment if provided (but don't require it) - NON-BLOCKING
            if config:
                try:
                    self._apply_config_if_provided(config)
                except Exception:
                    pass  # Don't let config errors block tool listing
            
            # Return pre-computed static tools instantly - NO DELAYS
            return {"tools": self._static_tools}
        
        @self.app.post("/mcp")
        async def post_mcp(request: Request):
            """Handle JSON-RPC tool execution (authentication happens here)."""
            try:
                body = await request.body()
                message = json.loads(body.decode())
                
                method = message.get("method")
                if method == "tools/list":
                    # Return static tools for JSON-RPC format
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {"tools": self._static_tools}
                    }
                elif method == "tools/call":
                    # Authentication happens here (lazy loading)
                    return await self._execute_tool(message)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}
                    }
                    
            except Exception as e:
                logger.error(f"Error in POST /mcp: {e}")
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)}
                }
        
        @self.app.delete("/mcp")
        async def delete_mcp():
            """Session cleanup for Smithery."""
            return {"status": "cleaned"}
    
    def _get_static_tool_definitions(self) -> list:
        """Pre-computed static tool definitions - NO AUTHENTICATION REQUIRED."""
        return [
            {
                "name": "get_confluence_page",
                "description": "Retrieve a Confluence page by ID or URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Page ID"},
                        "page_url": {"type": "string", "description": "Page URL"}
                    }
                }
            },
            {
                "name": "search_confluence_pages", 
                "description": "Search Confluence pages with CQL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cql": {"type": "string", "description": "CQL query"},
                        "limit": {"type": "integer", "description": "Result limit"}
                    },
                    "required": ["cql"]
                }
            },
            {
                "name": "create_confluence_page",
                "description": "Create a new Confluence page",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "space_key": {"type": "string", "description": "Space key"},
                        "title": {"type": "string", "description": "Page title"},
                        "content": {"type": "string", "description": "Page content"}
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
                        "page_id": {"type": "string", "description": "Page ID"},
                        "title": {"type": "string", "description": "New title"}, 
                        "content": {"type": "string", "description": "New content"}
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "delete_confluence_page",
                "description": "Delete a Confluence page",
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
                "description": "List available Confluence spaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of spaces to return"}
                    }
                }
            },
            {
                "name": "get_page_attachments",
                "description": "Get attachments for a Confluence page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Page ID"}
                    },
                    "required": ["page_id"]
                }
            },
            {
                "name": "add_page_attachment",
                "description": "Add attachment to a Confluence page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Page ID"},
                        "file_path": {"type": "string", "description": "File path"},
                        "filename": {"type": "string", "description": "File name"}
                    },
                    "required": ["page_id", "file_path"]
                }
            },
            {
                "name": "delete_page_attachment",
                "description": "Delete attachment from a Confluence page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "attachment_id": {"type": "string", "description": "Attachment ID"}
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
                        "page_id": {"type": "string", "description": "Page ID"}
                    },
                    "required": ["page_id"]
                }
            }
        ]
    
    def _apply_config_if_provided(self, config: str):
        """Apply base64 config from Smithery if provided (optional)."""
        try:
            decoded = base64.b64decode(config).decode('utf-8')
            config_data = json.loads(decoded)
            
            # Map Smithery config to environment variables
            env_mapping = {
                'confluenceUrl': 'CONFLUENCE_URL',
                'username': 'CONFLUENCE_USERNAME',
                'apiToken': 'CONFLUENCE_API_TOKEN'
            }
            
            for config_key, env_var in env_mapping.items():
                if config_key in config_data:
                    os.environ[env_var] = config_data[config_key]
                    
        except Exception as e:
            logger.warning(f"Could not apply config: {e}")
            # Continue without config - lazy loading allows this
    
    async def _execute_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with authentication (LAZY LOADING - auth happens here)."""
        try:
            # Import heavy dependencies only when needed
            import httpx
            from confluence_mcp_server.mcp_actions.page_actions import ConfluencePageActions
            from confluence_mcp_server.mcp_actions.space_actions import ConfluenceSpaceActions
            from confluence_mcp_server.mcp_actions.attachment_actions import ConfluenceAttachmentActions
            from confluence_mcp_server.mcp_actions.comment_actions import ConfluenceCommentActions
            
            # Get credentials from environment (set by _apply_config_if_provided or user)
            confluence_url = os.getenv('CONFLUENCE_URL')
            username = os.getenv('CONFLUENCE_USERNAME') 
            api_token = os.getenv('CONFLUENCE_API_TOKEN')
            
            if not all([confluence_url, username, api_token]):
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32602,
                        "message": "Missing required configuration: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN"
                    }
                }
            
            # Create authenticated client
            async with httpx.AsyncClient() as client:
                client.auth = (username, api_token)
                client.timeout = 30.0
                
                # Create action handlers
                page_actions = ConfluencePageActions(client, confluence_url)
                space_actions = ConfluenceSpaceActions(client, confluence_url)
                attachment_actions = ConfluenceAttachmentActions(client, confluence_url)
                comment_actions = ConfluenceCommentActions(client, confluence_url)
                
                # Execute the requested tool
                params = message.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Route to appropriate action handler
                if tool_name.startswith("get_confluence_page"):
                    result = await page_actions.get_page(**arguments)
                elif tool_name == "search_confluence_pages":
                    result = await page_actions.search_pages(**arguments)
                elif tool_name == "create_confluence_page":
                    result = await page_actions.create_page(**arguments)
                elif tool_name == "update_confluence_page":
                    result = await page_actions.update_page(**arguments)
                elif tool_name == "delete_confluence_page":
                    result = await page_actions.delete_page(**arguments)
                elif tool_name == "get_confluence_spaces":
                    result = await space_actions.get_spaces(**arguments)
                elif tool_name == "get_page_attachments":
                    result = await attachment_actions.get_attachments(**arguments)
                elif tool_name == "add_page_attachment":
                    result = await attachment_actions.add_attachment(**arguments)
                elif tool_name == "delete_page_attachment":
                    result = await attachment_actions.delete_attachment(**arguments)
                elif tool_name == "get_page_comments":
                    result = await comment_actions.get_comments(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {"content": [{"type": "text", "text": str(result)}]}
                }
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"}
            }

def create_app() -> FastAPI:
    """Create the optimized FastAPI app."""
    transport = OptimizedHttpTransport()
    return transport.app

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the optimized HTTP server."""
    logger.info(f"Starting Optimized Confluence MCP Server on {host}:{port}")
    logger.info("LAZY LOADING: Tool listing requires NO authentication")
    logger.info("AUTHENTICATION: Only happens during tool execution")
    
    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server()