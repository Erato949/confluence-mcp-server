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
TOOLS_JSON = '''{"tools":[
    {
        "name": "get_confluence_page",
        "description": "Retrieves a specific Confluence page with its content and metadata. Use page_id for fastest retrieval or space_key + title for human-readable identification. Add expand parameter to get page content in the response.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page to retrieve. Example: '123456789'. Use this when you know the exact page ID for fastest retrieval."
                },
                "space_key": {
                    "type": "string",
                    "description": "The key of the space where the page resides (used with title). Example: 'DOCS', 'TECH', '~username'. Required when using title parameter."
                },
                "title": {
                    "type": "string",
                    "description": "The title of the page to retrieve (used with space_key). Example: 'Meeting Notes', 'API Documentation'. Must be exact match."
                },
                "expand": {
                    "type": "string",
                    "description": "Comma-separated list of properties to expand. Examples: 'body.view' (HTML content), 'body.storage' (raw XML), 'version,space,history'. Use to get page content and metadata."
                }
            }
        }
    },
    {
        "name": "search_confluence_pages",
        "description": "Search for Confluence pages using text queries or advanced CQL (Confluence Query Language). Use 'query' for simple text searches or 'cql' for complex searches with precise criteria. Add 'expand' to get page content in results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Simple text search query. Example: 'meeting notes', 'API documentation', 'project status'. Searches page titles and content."
                },
                "cql": {
                    "type": "string",
                    "description": "Advanced CQL (Confluence Query Language) query. Examples: 'space = DOCS AND title ~ \\"API*\\"', 'created >= \\"2024-01-01\\"', 'creator = currentUser()'. Use for precise searches."
                },
                "space_key": {
                    "type": "string",
                    "description": "Limit search to specific space. Example: 'DOCS', 'TECH'. Can be combined with query or cql parameters."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-100). Default: 25. Use higher values for comprehensive searches."
                },
                "start": {
                    "type": "integer",
                    "description": "Starting offset for pagination. Default: 0. Use with limit for paging through large result sets."
                },
                "expand": {
                    "type": "string",
                    "description": "Expand properties for search results. Examples: 'body.view' (get content preview), 'version,space'. Adds detail to results but increases response size."
                },
                "excerpt": {
                    "type": "string",
                    "description": "Type of content excerpt to include. Options: 'none' (no excerpt), 'highlight' (highlighted matches), 'indexed' (plain excerpt). Default: none."
                }
            }
        }
    },
    {
        "name": "create_confluence_page",
        "description": "Creates a new page in Confluence with specified content and structure. Always specify space_key (required), use descriptive unique titles, and add parent_page_id to create hierarchical structure. Content should be in Confluence Storage Format (XML-based).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "space_key": {
                    "type": "string",
                    "description": "The key of the space where the page will be created. Example: 'DOCS', 'TECH', '~username'. Required field - get available spaces using get_confluence_spaces."
                },
                "title": {
                    "type": "string",
                    "description": "The title of the new page. Example: 'API Documentation', 'Meeting Notes 2024-01-15'. Must be unique within the space."
                },
                "content": {
                    "type": "string",
                    "description": "Page content in Confluence Storage Format (XML). Example: '<p>Hello world</p>', '<h1>Title</h1><p>Content...</p>'. Use HTML-like tags for formatting."
                },
                "parent_page_id": {
                    "type": "string",
                    "description": "ID of parent page to create child page. Example: '123456789'. Leave empty to create top-level page in space."
                }
            },
            "required": ["space_key", "title", "content"]
        }
    },
    {
        "name": "update_confluence_page",
        "description": "Updates an existing Confluence page's title, content, or position in the page hierarchy. Always increment version number (get current version first). You can update multiple fields in one operation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page to update. Example: '123456789'. Get this from get_confluence_page or search_confluence_pages."
                },
                "new_version_number": {
                    "type": "integer",
                    "description": "The new version number for the page (must be current version + 1). Example: if current version is 5, use 6. Get current version from get_confluence_page."
                },
                "title": {
                    "type": "string",
                    "description": "New title for the page. Example: 'Updated API Documentation'. Leave empty to keep current title unchanged."
                },
                "content": {
                    "type": "string",
                    "description": "New content in Confluence Storage Format (XML). Example: '<p>Updated content...</p>'. Leave empty to keep current content unchanged."
                },
                "parent_page_id": {
                    "type": "string",
                    "description": "ID of new parent page to move this page. Example: '987654321'. Use empty string '' to make page top-level. Leave as None to keep current parent."
                }
            },
            "required": ["page_id", "new_version_number"]
        }
    },
    {
        "name": "delete_confluence_page",
        "description": "Permanently moves a Confluence page to trash (soft delete). Pages are moved to trash, not permanently deleted. Deleted pages can be restored from trash by admins. Consider the impact on page links and references.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page to be moved to trash. Example: '123456789'. Get page information first to confirm you're deleting the right page."
                }
            },
            "required": ["page_id"]
        }
    },
    {
        "name": "get_confluence_spaces",
        "description": "Retrieves a list of Confluence spaces that the user has access to. Use space keys in page creation and search operations. Space keys are required for creating pages. Personal spaces usually have keys like '~username'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of spaces to return (1-100). Default: 25. Use higher values for comprehensive listing."
                },
                "start": {
                    "type": "integer",
                    "description": "Starting offset for pagination. Default: 0. Use with limit for paging through large result sets."
                }
            }
        }
    },
    {
        "name": "get_page_attachments",
        "description": "Retrieves all attachments associated with a specific Confluence page. Use filename filter to find specific attachments. Check file size before downloading large attachments. Multiple versions of the same file are tracked.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page from which to retrieve attachments. Example: '123456789'."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of attachments to return (1-200). Default: 50."
                },
                "start": {
                    "type": "integer",
                    "description": "Starting offset for pagination. Default: 0."
                },
                "filename": {
                    "type": "string",
                    "description": "Filter attachments by filename. Example: 'document.pdf', 'screenshot.png'."
                },
                "media_type": {
                    "type": "string",
                    "description": "Filter attachments by media type. Examples: 'image/png', 'application/pdf', 'text/plain'."
                }
            },
            "required": ["page_id"]
        }
    },
    {
        "name": "add_page_attachment",
        "description": "Uploads a file as an attachment to a specific Confluence page. File must be accessible to the server process. Use descriptive filenames for better organization. Uploading same filename creates new version.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page to add the attachment to. Example: '123456789'."
                },
                "file_path": {
                    "type": "string",
                    "description": "The local path to the file to be uploaded. File path should be absolute for reliability. Example: '/path/to/document.pdf'."
                },
                "filename_on_confluence": {
                    "type": "string",
                    "description": "Optional name for the file on Confluence. If None, uses the local filename. Example: 'Requirements.txt'."
                },
                "comment": {
                    "type": "string",
                    "description": "Optional comment for the attachment version. Example: 'Updated screenshot', 'Latest requirements'."
                }
            },
            "required": ["page_id", "file_path"]
        }
    },
    {
        "name": "delete_page_attachment",
        "description": "Permanently deletes an attachment from a Confluence page. Deletion is permanent and cannot be undone. Get attachment ID using get_page_attachments first. Deleting attachments may break links in page content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "attachment_id": {
                    "type": "string",
                    "description": "The ID of the attachment to be permanently deleted. Example: 'att123456'. Use get_page_attachments to find the attachment ID."
                }
            },
            "required": ["attachment_id"]
        }
    },
    {
        "name": "get_page_comments",
        "description": "Retrieves all comments associated with a specific Confluence page. Use pagination for pages with many comments. Comments may be in storage format (XML) or view format (HTML). Check parent_comment_id to understand reply structure.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "The ID of the page from which to retrieve comments. Example: '123456789'."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of comments to return (1-100). Default: 25."
                },
                "start": {
                    "type": "integer",
                    "description": "Starting offset for pagination. Default: 0."
                },
                "expand": {
                    "type": "string",
                    "description": "Comma-separated list of properties to expand for each comment. Examples: 'history', 'restrictions.read.restrictions.user'."
                }
            },
            "required": ["page_id"]
        }
    }
]}'''

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
        print(f"SMITHERY_CONFIG: Parsing config parameter (length: {len(config_param)})", flush=True)
        
        # Try direct JSON parsing first
        if config_param.startswith('{'):
            print("SMITHERY_CONFIG: Attempting direct JSON parsing", flush=True)
            parsed = json.loads(config_param)
            print(f"SMITHERY_CONFIG: Direct JSON success - keys: {list(parsed.keys())}", flush=True)
            return parsed
        
        # Try base64 decoding
        try:
            print("SMITHERY_CONFIG: Attempting base64 decoding", flush=True)
            import base64
            decoded = base64.b64decode(config_param).decode('utf-8')
            print(f"SMITHERY_CONFIG: Base64 decoded to: {decoded[:100]}..." if len(decoded) > 100 else f"SMITHERY_CONFIG: Base64 decoded to: {decoded}", flush=True)
            parsed = json.loads(decoded)
            print(f"SMITHERY_CONFIG: Base64 JSON success - keys: {list(parsed.keys())}", flush=True)
            return parsed
        except Exception as e:
            print(f"SMITHERY_CONFIG: Base64 decode failed: {e}", flush=True)
        
        # Try URL decoding + base64 (some environments double-encode)
        try:
            print("SMITHERY_CONFIG: Attempting URL decode + base64", flush=True)
            import urllib.parse
            url_decoded = urllib.parse.unquote(config_param)
            print(f"SMITHERY_CONFIG: URL decoded to: {url_decoded[:100]}..." if len(url_decoded) > 100 else f"SMITHERY_CONFIG: URL decoded to: {url_decoded}", flush=True)
            
            if url_decoded.startswith('{'):
                parsed = json.loads(url_decoded)
                print(f"SMITHERY_CONFIG: URL JSON success - keys: {list(parsed.keys())}", flush=True)
                return parsed
            else:
                import base64
                decoded = base64.b64decode(url_decoded).decode('utf-8')
                print(f"SMITHERY_CONFIG: URL+Base64 decoded to: {decoded[:100]}..." if len(decoded) > 100 else f"SMITHERY_CONFIG: URL+Base64 decoded to: {decoded}", flush=True)
                parsed = json.loads(decoded)
                print(f"SMITHERY_CONFIG: URL+Base64 JSON success - keys: {list(parsed.keys())}", flush=True)
                return parsed
        except Exception as e:
            print(f"SMITHERY_CONFIG: URL+Base64 decode failed: {e}", flush=True)
            
        print("SMITHERY_CONFIG: All parsing methods failed", flush=True)
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
        print(f"SMITHERY_DEBUG: Raw config parameter received: {config[:100]}..." if len(config) > 100 else f"SMITHERY_DEBUG: Raw config parameter: {config}", flush=True)
        apply_config_instantly(config)
        
        # Debug: Check environment variables after config application
        print(f"SMITHERY_DEBUG: Environment after config:", flush=True)
        print(f"  CONFLUENCE_URL: {'SET' if os.getenv('CONFLUENCE_URL') else 'NOT SET'}", flush=True)
        print(f"  CONFLUENCE_USERNAME: {'SET' if os.getenv('CONFLUENCE_USERNAME') else 'NOT SET'}", flush=True)
        print(f"  CONFLUENCE_API_TOKEN: {'SET' if os.getenv('CONFLUENCE_API_TOKEN') else 'NOT SET'}", flush=True)
    else:
        print("SMITHERY_DEBUG: No config parameter in GET request", flush=True)
    
    # Return pre-serialized JSON instantly
    return Response(content=TOOLS_JSON, media_type="application/json")

async def post_mcp_handler(request):
    """Minimal JSON-RPC POST handler."""
    from starlette.responses import JSONResponse
    
    try:
        # Check if config is in query parameters for POST as well
        config = request.query_params.get('config')
        if config:
            print(f"SMITHERY_DEBUG: Config found in POST query parameters", flush=True)
            apply_config_instantly(config)
        
        body = await request.body()
        message = json.loads(body.decode())
        
        method = message.get("method")
        message_id = message.get("id")
        
        print(f"SMITHERY_DEBUG: POST method: {method}", flush=True)
        
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
        # Debug: Log current environment state
        print("SMITHERY_TOOL_DEBUG: Tool execution starting", flush=True)
        print(f"  CONFLUENCE_URL: {'SET' if os.getenv('CONFLUENCE_URL') else 'NOT SET'}", flush=True)
        print(f"  CONFLUENCE_USERNAME: {'SET' if os.getenv('CONFLUENCE_USERNAME') else 'NOT SET'}", flush=True)
        print(f"  CONFLUENCE_API_TOKEN: {'SET' if os.getenv('CONFLUENCE_API_TOKEN') else 'NOT SET'}", flush=True)
        
        # Check environment
        confluence_url = os.getenv('CONFLUENCE_URL')
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([confluence_url, username, api_token]):
            print(f"SMITHERY_TOOL_DEBUG: Missing credentials - URL: {bool(confluence_url)}, Username: {bool(username)}, Token: {bool(api_token)}", flush=True)
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
                    # Use mode='json' to ensure HttpUrl objects are serialized as strings
                    result_dict = result.model_dump(mode='json')
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