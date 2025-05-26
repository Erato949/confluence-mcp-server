#!/usr/bin/env python3
"""
Confluence MCP Server - Starlette Ultra-Minimal for Smithery.ai
Absolute fastest possible startup using Starlette directly.
Zero dependencies at import time.
"""

# ABSOLUTE MINIMUM imports at module level
import os
import json
import time

# Pre-serialized response for maximum speed
TOOLS_JSON = '{"tools":[{"name":"get_confluence_page","description":"Retrieve a Confluence page by ID or URL","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"},"page_url":{"type":"string","description":"Page URL"}}}},{"name":"search_confluence_pages","description":"Search Confluence pages with CQL","inputSchema":{"type":"object","properties":{"cql":{"type":"string","description":"CQL query"},"limit":{"type":"integer","description":"Result limit"}},"required":["cql"]}},{"name":"create_confluence_page","description":"Create a new Confluence page","inputSchema":{"type":"object","properties":{"space_key":{"type":"string","description":"Space key"},"title":{"type":"string","description":"Page title"},"content":{"type":"string","description":"Page content"}},"required":["space_key","title","content"]}},{"name":"update_confluence_page","description":"Update an existing Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"},"title":{"type":"string","description":"New title"},"content":{"type":"string","description":"New content"}},"required":["page_id"]}},{"name":"delete_confluence_page","description":"Delete a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID to delete"}},"required":["page_id"]}},{"name":"get_confluence_spaces","description":"List available Confluence spaces","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","description":"Number of spaces to return"}}}},{"name":"get_page_attachments","description":"Get attachments for a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"}},"required":["page_id"]}},{"name":"add_page_attachment","description":"Add attachment to a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"},"file_path":{"type":"string","description":"File path"},"filename":{"type":"string","description":"File name"}},"required":["page_id","file_path"]}},{"name":"delete_page_attachment","description":"Delete attachment from a Confluence page","inputSchema":{"type":"object","properties":{"attachment_id":{"type":"string","description":"Attachment ID"}},"required":["attachment_id"]}},{"name":"get_page_comments","description":"Get comments for a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"}},"required":["page_id"]}}]}'

START_TIME = time.time()

def apply_config_instantly(config_param):
    """Instant config application with comprehensive Smithery.ai support."""
    if not config_param:
        return
    try:
        config_data = parse_config_parameter(config_param)
        if config_data:
            applied_config = apply_smithery_config_to_env(config_data)
            if applied_config:
                print(f"SMITHERY_CONFIG: Applied configuration for: {list(applied_config.keys())}", flush=True)
            else:
                print("SMITHERY_CONFIG: No config applied (vars already set)", flush=True)
        else:
            print("SMITHERY_CONFIG: Failed to parse config parameter", flush=True)
    except Exception as e:
        print(f"SMITHERY_CONFIG: Error applying config: {e}", flush=True)
        pass

def parse_config_parameter(config_param):
    """Parse configuration parameter (handles both JSON and base64 formats)."""
    try:
        # Try direct JSON parsing first
        if config_param.startswith('{'):
            return json.loads(config_param)
        
        # Try base64 decoding
        try:
            import base64
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
                import base64
                decoded = base64.b64decode(url_decoded).decode('utf-8')
                return json.loads(decoded)
        except:
            pass
            
        return None
        
    except Exception as e:
        print(f"SMITHERY_CONFIG: Failed to parse config parameter: {e}", flush=True)
        return None

def apply_smithery_config_to_env(config_data):
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
            # Only override if environment variable isn't already set
            # This preserves Claude Desktop config when available
            if not os.getenv(env_var):
                os.environ[env_var] = str(config_data[config_key])
                applied_config[env_var] = str(config_data[config_key])
                print(f"SMITHERY_CONFIG: Set {env_var} from Smithery config", flush=True)
            else:
                print(f"SMITHERY_CONFIG: {env_var} already set, preserving existing value", flush=True)
    
    return applied_config

async def ping_endpoint(request):
    """Ultra-fast ping for debugging."""
    from starlette.responses import PlainTextResponse
    elapsed = (time.time() - START_TIME) * 1000
    return PlainTextResponse(f"pong-{elapsed:.0f}ms")

async def health_endpoint(request):
    """Ultra-fast health check."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "startup_ms": (time.time() - START_TIME) * 1000})

async def root_endpoint(request):
    """Root endpoint."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "name": "Confluence MCP Server",
        "version": "1.1.0",
        "status": "starlette-minimal",
        "startup_ms": (time.time() - START_TIME) * 1000
    })

async def get_tools_instant(request):
    """
    SMITHERY.AI INSTANT RESPONSE: Pre-serialized JSON.
    GUARANTEED sub-50ms response.
    """
    from starlette.responses import Response
    
    # Handle config parameter
    config = request.query_params.get('config')
    if config:
        apply_config_instantly(config)
    
    # Return pre-serialized JSON instantly
    return Response(content=TOOLS_JSON, media_type="application/json")

async def post_mcp_handler(request):
    """Minimal JSON-RPC POST handler."""
    from starlette.responses import JSONResponse
    
    try:
        body = await request.body()
        message = json.loads(body.decode())
        
        method = message.get("method")
        message_id = message.get("id")
        
        if method == "initialize":
            # MCP initialize handshake - required by Smithery
            return JSONResponse({
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
            })
        elif method == "initialized":
            # MCP initialized notification - required by Smithery
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {}
            })
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": message_id,
                "result": json.loads(TOOLS_JSON)
            })
        elif method == "tools/call":
            return await execute_tool_minimal(message)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            })
            
    except Exception as e:
        from starlette.responses import JSONResponse
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)}
        })

async def delete_mcp_handler(request):
    """Session cleanup."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "cleaned"})

async def execute_tool_minimal(message):
    """Tool execution with real Confluence API calls (lazy imports)."""
    from starlette.responses import JSONResponse
    
    try:
        # Check environment
        confluence_url = os.getenv('CONFLUENCE_URL')
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([confluence_url, username, api_token]):
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Missing config: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN"
                }
            })
        
        # Import dependencies only when needed (lazy loading)
        import httpx
        
        # Create authenticated HTTP client
        async with httpx.AsyncClient(
            auth=(username, api_token),
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        ) as client:
            
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
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {"code": -32603, "message": f"Import error: {str(e)}"}
                })
            
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
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                })
            
            # Convert result to MCP response format
            if result:
                # Convert Pydantic model to dict if needed
                if hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                else:
                    result_dict = result
                
                # Format as MCP tool response
                return JSONResponse({
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
                })
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {"content": [{"type": "text", "text": "Tool executed successfully but returned no data"}]}
                })
        
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {"code": -32603, "message": f"Tool failed: {str(e)}"}
        })

def create_starlette_app():
    """Create ultra-minimal Starlette app."""
    print(f"STARLETTE_DEBUG: Creating app at {time.time()}", flush=True)
    
    # Import only when creating app
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    
    # Minimal middleware
    middleware = [
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])
    ]
    
    # Define routes
    routes = [
        Route('/ping', ping_endpoint, methods=["GET"]),
        Route('/health', health_endpoint, methods=["GET"]),
        Route('/', root_endpoint, methods=["GET"]),
        Route('/mcp', get_tools_instant, methods=["GET"]),
        Route('/mcp', post_mcp_handler, methods=["POST"]),
        Route('/mcp', delete_mcp_handler, methods=["DELETE"]),
    ]
    
    app = Starlette(routes=routes, middleware=middleware)
    
    print(f"STARLETTE_DEBUG: App created at {time.time()}", flush=True)
    return app

def run_starlette_server(host: str = "0.0.0.0", port: int = None):
    """Run Starlette server with absolute minimum overhead."""
    print(f"STARLETTE_DEBUG: Starting at {time.time()}", flush=True)
    
    # CRITICAL FIX: Use PORT environment variable as required by Smithery
    if port is None:
        port = int(os.getenv('PORT', 8000))
    
    print(f"STARLETTE_DEBUG: Using port {port} (from PORT env var or default)", flush=True)
    
    # Import uvicorn only when running
    import uvicorn
    
    app = create_starlette_app()
    
    print(f"STARLETTE_DEBUG: Starting uvicorn at {time.time()}", flush=True)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="critical",  # Absolute minimum logging
        access_log=False,
        server_header=False,
        date_header=False,
        loop="asyncio"  # Use fastest event loop
    )

if __name__ == "__main__":
    run_starlette_server() 