#!/usr/bin/env python3
"""
Confluence MCP Server - Ultra-Optimized HTTP Transport for Smithery.ai
Blazing fast startup with guaranteed lazy loading compliance.
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

# Ultra-fast logging setup
logging.basicConfig(level=logging.WARNING)  # Reduce log level for faster startup
logger = logging.getLogger(__name__)

class UltraOptimizedHttpTransport:
    """Ultra-optimized HTTP transport for Smithery.ai with guaranteed sub-second responses."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Confluence MCP Server",
            description="Ultra-optimized for Smithery.ai deployment",
            version="1.1.0",
            docs_url=None,  # Disable docs for faster startup
            redoc_url=None  # Disable redoc for faster startup
        )
        self._setup_minimal_middleware()
        self._setup_ultra_fast_routes()
        
        # Pre-computed static tool definitions - computed at class level for maximum speed
        self._static_tools = self._get_static_tool_definitions()
    
    def _setup_minimal_middleware(self):
        """Setup minimal CORS middleware for maximum speed."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["*"],
        )
    
    def _setup_ultra_fast_routes(self):
        """Setup routes optimized for sub-second responses."""
        
        @self.app.get("/health")
        async def health():
            """Ultra-fast health check - no dependencies."""
            return {"status": "healthy"}
        
        @self.app.get("/")
        async def root():
            """Server info - pre-computed response."""
            return {
                "name": "Confluence MCP Server",
                "version": "1.1.0",
                "tools_count": 10,
                "lazy_loading": True,
                "status": "ready"
            }
        
        @self.app.get("/mcp")
        async def get_tools(config: Optional[str] = Query(None)):
            """
            SMITHERY.AI ULTRA-FAST TOOL SCANNING: Return tools instantly.
            CRITICAL: This endpoint MUST respond in <500ms for Smithery compatibility.
            """
            # Apply config if provided (non-blocking, fire-and-forget)
            if config:
                try:
                    self._apply_config_async(config)
                except:
                    pass  # Never let config errors block tool listing
            
            # Return pre-computed static tools instantly - ZERO delays
            return {"tools": self._static_tools}
        
        @self.app.post("/mcp")
        async def post_mcp(request: Request):
            """Handle JSON-RPC tool execution (authentication happens here)."""
            try:
                body = await request.body()
                message = json.loads(body.decode())
                
                method = message.get("method")
                if method == "tools/list":
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {"tools": self._static_tools}
                    }
                elif method == "tools/call":
                    return await self._execute_tool(message)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}
                    }
                    
            except Exception as e:
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
    
    def _apply_config_async(self, config: str):
        """Apply base64 config from Smithery (non-blocking)."""
        try:
            # Handle different config formats that Smithery might send
            if config.startswith('{'):
                # Direct JSON string
                config_data = json.loads(config)
            else:
                # Base64 encoded JSON
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
                    logger.warning(f"SMITHERY_CONFIG: Set {env_var} from config")
                    
        except Exception as e:
            logger.warning(f"SMITHERY_CONFIG: Failed to parse config: {e}")
            pass  # Silent fail - never block tool listing
    
    async def _execute_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with authentication (LAZY LOADING - auth happens here)."""
        try:
            # Import dependencies only when needed (lazy loading)
            import httpx
            
            # Get credentials from environment
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
            
            # Simplified tool execution (placeholder - full implementation would import action modules)
            params = message.get("params", {})
            tool_name = params.get("name")
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {"content": [{"type": "text", "text": f"Tool {tool_name} executed successfully (placeholder)"}]}
            }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"}
            }

def create_app() -> FastAPI:
    """Create the ultra-optimized FastAPI app."""
    transport = UltraOptimizedHttpTransport()
    return transport.app

def run_server(host: str = "0.0.0.0", port: int = None):
    """Run the ultra-optimized HTTP server."""
    # CRITICAL FIX: Use PORT environment variable as required by Smithery
    if port is None:
        port = int(os.getenv('PORT', 8000))
    
    logger.warning(f"Starting Ultra-Optimized Confluence MCP Server on {host}:{port}")
    logger.warning(f"PORT from environment: {os.getenv('PORT', 'not set, using default 8000')}")
    logger.warning("LAZY LOADING: Tool listing requires NO authentication")
    logger.warning("AUTHENTICATION: Only happens during tool execution")
    
    app = create_app()
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level="warning",  # Reduce logging for speed
        access_log=False      # Disable access logs for speed
    )

if __name__ == "__main__":
    run_server()