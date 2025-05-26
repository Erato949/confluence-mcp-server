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
import sys
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
        
        # Store configuration state for persistence across requests
        self._config_applied = False
    
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
                    self._config_applied = True
                except:
                    pass  # Never let config errors block tool listing
            
            # Return pre-computed static tools instantly - ZERO delays
            return {"tools": self._static_tools}
        
        @self.app.post("/mcp")
        async def post_mcp(request: Request):
            """Handle JSON-RPC tool execution (authentication happens here)."""
            try:
                # Check for configuration in query parameters (Smithery.ai pattern)
                config = request.query_params.get("config")
                if config:
                    try:
                        self._apply_config_async(config)
                        self._config_applied = True
                    except:
                        pass  # Never let config errors block requests
                
                body = await request.body()
                message = json.loads(body.decode())
                
                method = message.get("method")
                message_id = message.get("id")
                
                if method == "initialize":
                    # MCP initialize handshake - required by Smithery
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "Confluence MCP Server",
                                "version": "1.1.0"
                            }
                        }
                    }
                elif method == "initialized":
                    # MCP initialized notification - required by Smithery
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": {}
                    }
                elif method == "tools/list":
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": {"tools": self._static_tools}
                    }
                elif method == "tools/call":
                    return await self._execute_tool(message)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
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
        """Apply configuration from Smithery.ai with comprehensive parsing support."""
        try:
            logger.warning(f"SMITHERY_CONFIG: Received config (length: {len(config)}): {config[:100]}...")
            config_data = self._parse_config_parameter(config)
            if config_data:
                logger.warning(f"SMITHERY_CONFIG: Parsed config with keys: {list(config_data.keys())}")
                
                # ENHANCED DEBUG: Log the actual decoded values (mask sensitive data)
                for key, value in config_data.items():
                    if 'token' in key.lower() or 'password' in key.lower():
                        masked_value = f"[MASKED_{len(str(value))}]" if value else "[EMPTY]"
                        logger.warning(f"SMITHERY_CONFIG: DECODED {key} = {masked_value}")
                    else:
                        logger.warning(f"SMITHERY_CONFIG: DECODED {key} = '{value}'")
                
                applied_config = self._apply_smithery_config_to_env(config_data)
                if applied_config:
                    logger.warning(f"SMITHERY_CONFIG: Applied configuration for: {list(applied_config.keys())}")
                    
                    # ENHANCED DEBUG: Verify what actually got set in environment
                    for env_var in applied_config.keys():
                        env_value = os.getenv(env_var)
                        if 'TOKEN' in env_var:
                            masked_env = f"[MASKED_{len(env_value)}]" if env_value else "[EMPTY]"
                            logger.warning(f"SMITHERY_CONFIG: ENV_VERIFY {env_var} = {masked_env}")
                        else:
                            logger.warning(f"SMITHERY_CONFIG: ENV_VERIFY {env_var} = '{env_value}'")
                else:
                    logger.warning("SMITHERY_CONFIG: No config applied (vars already set)")
            else:
                logger.warning("SMITHERY_CONFIG: Failed to parse config parameter")
                    
        except Exception as e:
            logger.warning(f"SMITHERY_CONFIG: Error applying config: {e}")
            pass  # Silent fail - never block tool listing
    
    def _parse_config_parameter(self, config_param: str) -> Optional[Dict[str, Any]]:
        """Parse configuration parameter (handles both JSON and base64 formats)."""
        try:
            # Try direct JSON parsing first
            if config_param.startswith('{'):
                return json.loads(config_param)
            
            # Try base64 decoding
            try:
                decoded = base64.b64decode(config_param).decode('utf-8')
                return json.loads(decoded)
            except:
                pass
            
            # Try URL decoding + base64 (some environments double-encode)
            try:
                import urllib.parse
                url_decoded = urllib.parse.unquote(config_param)
                if url_decoded.startswith('{'):
                    return json.loads(url_decoded)
                else:
                    decoded = base64.b64decode(url_decoded).decode('utf-8')
                    return json.loads(decoded)
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.warning(f"SMITHERY_CONFIG: Failed to parse config parameter: {e}")
            return None

    def _apply_smithery_config_to_env(self, config_data: Dict[str, Any]) -> Dict[str, str]:
        """Apply Smithery configuration to environment variables."""
        # Map Smithery config keys to environment variable names
        env_mapping = {
            'confluenceUrl': 'CONFLUENCE_URL',
            'username': 'CONFLUENCE_USERNAME', 
            'apiToken': 'CONFLUENCE_API_TOKEN'
        }
        
        applied_config = {}
        
        for config_key, env_var in env_mapping.items():
            if config_key in config_data and config_data[config_key]:
                # Always apply Smithery config when deployed on Smithery
                old_value = os.getenv(env_var)
                os.environ[env_var] = str(config_data[config_key])
                applied_config[env_var] = str(config_data[config_key])
                if old_value:
                    logger.warning(f"SMITHERY_CONFIG: Updated {env_var} (was previously set)")
                else:
                    logger.warning(f"SMITHERY_CONFIG: Set {env_var} from Smithery config")
        
        return applied_config
    
    async def _execute_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with authentication (LAZY LOADING - auth happens here)."""
        try:
            # Import dependencies only when needed (lazy loading)
            import httpx
            
            # Define ToolError locally if not available in fastmcp
            class ToolError(Exception):
                pass
            
            # Get credentials from environment
            confluence_url = os.getenv('CONFLUENCE_URL')
            username = os.getenv('CONFLUENCE_USERNAME') 
            api_token = os.getenv('CONFLUENCE_API_TOKEN')
            
            # Debug logging for tool execution
            logger.warning(f"TOOL_EXECUTION: URL='{confluence_url}', USERNAME='{username}', TOKEN={'SET' if api_token else 'NOT_SET'}")
            logger.warning(f"TOOL_EXECUTION: URL type: {type(confluence_url)}, URL length: {len(confluence_url) if confluence_url else 0}")
            
            # Additional debug info
            logger.warning(f"TOOL_EXECUTION: All env vars - URL={os.getenv('CONFLUENCE_URL')}, USER={os.getenv('CONFLUENCE_USERNAME')}, TOKEN_SET={bool(os.getenv('CONFLUENCE_API_TOKEN'))}")
            
            if not all([confluence_url, username, api_token]):
                missing = []
                if not confluence_url: missing.append("CONFLUENCE_URL")
                if not username: missing.append("CONFLUENCE_USERNAME") 
                if not api_token: missing.append("CONFLUENCE_API_TOKEN")
                
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32602,
                        "message": f"Missing required configuration: {', '.join(missing)}"
                    }
                }
            
            # Clean up the confluence URL to get the base domain for API calls
            # Remove /wiki/ path as Confluence Cloud API endpoints are at the base domain
            
            # First, handle cases where URL might be None or empty
            if not confluence_url or not confluence_url.strip():
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32602,
                        "message": "CONFLUENCE_URL is empty or not set"
                    }
                }
            
            # Parse the URL to extract just the domain
            if confluence_url.startswith(('http://', 'https://')):
                # Extract domain from full URL
                from urllib.parse import urlparse
                parsed = urlparse(confluence_url)
                domain = parsed.netloc
                if not domain:
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {
                            "code": -32602,
                            "message": f"Invalid CONFLUENCE_URL format: {confluence_url}"
                        }
                    }
                # Force HTTPS for Confluence Cloud
                base_url = f'https://{domain}'
            else:
                # Assume it's just a domain name
                domain = confluence_url.strip().rstrip('/').split('/')[0]
                base_url = f'https://{domain}'
            
            logger.warning(f"TOOL_EXECUTION: Original URL='{confluence_url}' -> Base URL='{base_url}'")
            
            # CRITICAL DEBUG: Log exactly what we're passing to httpx
            logger.warning(f"TOOL_EXECUTION: About to create httpx.AsyncClient with base_url='{base_url}' (type: {type(base_url)}, length: {len(base_url)})")
            logger.warning(f"TOOL_EXECUTION: base_url valid URL check: starts_with_http={base_url.startswith(('http://', 'https://'))}, contains_domain={bool(base_url.split('://')[1] if '://' in base_url else '')}")
            
            # Create authenticated HTTP client with proper base URL
            try:
                logger.warning(f"TOOL_EXECUTION: Creating httpx.AsyncClient...")
                async with httpx.AsyncClient(
                    base_url=base_url,
                    auth=(username, api_token),
                    timeout=30.0,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                ) as client:
                    logger.warning(f"TOOL_EXECUTION: httpx client created successfully with base_url='{client.base_url}'")
                
                # Extract tool call parameters
                params = message.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                # Import action modules (lazy loading)
                try:
                    from confluence_mcp_server.mcp_actions import page_actions, space_actions, attachment_actions, comment_actions
                    from confluence_mcp_server.mcp_actions.schemas import (
                        GetPageInput, SearchPagesInput, CreatePageInput, UpdatePageInput, DeletePageInput,
                        GetSpacesInput, GetAttachmentsInput, AddAttachmentInput, DeleteAttachmentInput, GetCommentsInput
                    )
                except ImportError as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {"code": -32603, "message": f"Import error: {str(e)}"}
                    }
                
                # Execute the appropriate tool
                result = None
                if tool_name == "get_confluence_page":
                    inputs = GetPageInput(**tool_args)
                    result = await page_actions.get_page_logic(client, inputs)
                elif tool_name == "search_confluence_pages":
                    inputs = SearchPagesInput(**tool_args)
                    result = await page_actions.search_pages_logic(client, inputs)
                elif tool_name == "create_confluence_page":
                    inputs = CreatePageInput(**tool_args)
                    result = await page_actions.create_page_logic(client, inputs)
                elif tool_name == "update_confluence_page":
                    inputs = UpdatePageInput(**tool_args)
                    result = await page_actions.update_page_logic(client, inputs)
                elif tool_name == "delete_confluence_page":
                    inputs = DeletePageInput(**tool_args)
                    result = await page_actions.delete_page_logic(client, inputs)
                elif tool_name == "get_confluence_spaces":
                    inputs = GetSpacesInput(**tool_args)
                    result = await space_actions.get_spaces_logic(client, inputs)
                elif tool_name == "get_page_attachments":
                    inputs = GetAttachmentsInput(**tool_args)
                    result = await attachment_actions.get_attachments_logic(client, inputs)
                elif tool_name == "add_page_attachment":
                    inputs = AddAttachmentInput(**tool_args)
                    result = await attachment_actions.add_attachment_logic(client, inputs)
                elif tool_name == "delete_page_attachment":
                    inputs = DeleteAttachmentInput(**tool_args)
                    result = await attachment_actions.delete_attachment_logic(client, inputs)
                elif tool_name == "get_page_comments":
                    inputs = GetCommentsInput(**tool_args)
                    result = await comment_actions.get_comments_logic(client, inputs)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    }
                
                # Convert result to MCP response format
                if result:
                    # Convert Pydantic model to dict if needed
                    if hasattr(result, 'model_dump'):
                        result_dict = result.model_dump()
                    else:
                        result_dict = result
                    
                    # Format as MCP tool response
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
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {"content": [{"type": "text", "text": "Tool executed successfully but returned no data"}]}
                    }
            except Exception as httpx_error:
                logger.warning(f"TOOL_EXECUTION: HTTPX CLIENT CREATION FAILED: {type(httpx_error).__name__}: {str(httpx_error)}")
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {"code": -32603, "message": f"HTTP client creation failed: {str(httpx_error)}"}
                }
                
        except ToolError as e:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": str(e)}
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