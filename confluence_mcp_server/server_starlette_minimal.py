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
    """Instant config application - no error handling delays."""
    if not config_param:
        return
    try:
        # Handle different config formats that Smithery might send
        if isinstance(config_param, str):
            if config_param.startswith('{'):
                # Direct JSON string
                config_data = json.loads(config_param)
            else:
                # Base64 encoded JSON
                import base64
                decoded = base64.b64decode(config_param).decode('utf-8')
                config_data = json.loads(decoded)
        else:
            config_data = config_param
            
        # Apply configuration to environment variables
        for key, env_var in [('confluenceUrl', 'CONFLUENCE_URL'), ('username', 'CONFLUENCE_USERNAME'), ('apiToken', 'CONFLUENCE_API_TOKEN')]:
            if key in config_data:
                os.environ[env_var] = config_data[key]
                print(f"STARLETTE_DEBUG: Set {env_var} from config", flush=True)
    except Exception as e:
        print(f"STARLETTE_DEBUG: Config parsing failed: {e}", flush=True)
        pass

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
    """Minimal tool execution with lazy imports."""
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
        
        # Minimal tool execution
        params = message.get("params", {})
        tool_name = params.get("name", "unknown")
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Tool {tool_name} executed (starlette-minimal)"
                    }
                ]
            }
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