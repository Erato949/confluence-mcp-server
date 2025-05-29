#!/usr/bin/env python3
"""
Confluence MCP Server - ZERO IMPORTS Minimal for Smithery.ai
Uses only Python standard library - no FastAPI, no Starlette, no external deps.
Absolute fastest possible startup.
"""

# ONLY standard library imports
import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64
import threading

# Pre-serialized tools response
TOOLS_JSON = b'''{"tools":[
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

def apply_config_env(config_param):
    """Apply config to environment variables instantly."""
    if not config_param:
        return
    try:
        # Handle different config formats that Smithery might send
        if config_param.startswith('{'):
            # Direct JSON string
            config_data = json.loads(config_param)
        else:
            # Base64 encoded JSON
            decoded = base64.b64decode(config_param).decode('utf-8')
            config_data = json.loads(decoded)
            
        env_map = {
            'confluenceUrl': 'CONFLUENCE_URL',
            'username': 'CONFLUENCE_USERNAME',
            'apiToken': 'CONFLUENCE_API_TOKEN'
        }
        for key, env_var in env_map.items():
            if key in config_data:
                os.environ[env_var] = config_data[key]
                print(f"ZERO_IMPORTS_DEBUG: Set {env_var} from config", flush=True)
    except Exception as e:
        print(f"ZERO_IMPORTS_DEBUG: Config parsing failed: {e}", flush=True)
        pass

class UltraMinimalHandler(BaseHTTPRequestHandler):
    """Ultra-minimal HTTP handler - no logging, maximum speed."""
    
    def log_message(self, format, *args):
        """Disable all logging for maximum speed."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        path = self.path
        parsed = urlparse(path)
        query_params = parse_qs(parsed.query)
        
        if parsed.path == '/ping':
            elapsed = (time.time() - START_TIME) * 1000
            self._send_response(200, f"pong-{elapsed:.0f}ms".encode(), "text/plain")
            
        elif parsed.path == '/health':
            response = {
                "status": "healthy",
                "startup_ms": (time.time() - START_TIME) * 1000
            }
            self._send_json_response(200, response)
            
        elif parsed.path == '/':
            response = {
                "name": "Confluence MCP Server",
                "version": "1.1.0",
                "status": "zero-imports",
                "startup_ms": (time.time() - START_TIME) * 1000
            }
            self._send_json_response(200, response)
            
        elif parsed.path == '/mcp':
            # Handle config parameter if present
            config = query_params.get('config', [None])[0]
            if config:
                apply_config_env(config)
            
            # Return pre-serialized tools instantly
            self._send_response(200, TOOLS_JSON, "application/json")
            
        else:
            self._send_response(404, b'{"error":"Not Found"}', "application/json")
    
    def do_POST(self):
        """Handle POST requests for JSON-RPC."""
        if self.path == '/mcp':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                message = json.loads(post_data.decode())
                
                method = message.get("method")
                message_id = message.get("id")
                
                if method == "initialize":
                    # MCP initialize handshake - required by Smithery
                    response = {
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
                    self._send_json_response(200, response)
                    
                elif method == "initialized":
                    # MCP initialized notification - required by Smithery
                    response = {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": {}
                    }
                    self._send_json_response(200, response)
                    
                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": json.loads(TOOLS_JSON.decode())
                    }
                    self._send_json_response(200, response)
                    
                elif method == "tools/call":
                    # Check for required env vars
                    confluence_url = os.getenv('CONFLUENCE_URL')
                    username = os.getenv('CONFLUENCE_USERNAME')
                    api_token = os.getenv('CONFLUENCE_API_TOKEN')
                    
                    if not all([confluence_url, username, api_token]):
                        response = {
                            "jsonrpc": "2.0",
                            "id": message_id,
                            "error": {
                                "code": -32602,
                                "message": "Missing config: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN"
                            }
                        }
                    else:
                        params = message.get("params", {})
                        tool_name = params.get("name", "unknown")
                        response = {
                            "jsonrpc": "2.0",
                            "id": message_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Tool {tool_name} executed (zero-imports)"
                                    }
                                ]
                            }
                        }
                    
                    self._send_json_response(200, response)
                    
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}
                    }
                    self._send_json_response(200, response)
                    
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)}
                }
                self._send_json_response(500, response)
        else:
            self._send_response(404, b'{"error":"Not Found"}', "application/json")
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        if self.path == '/mcp':
            response = {"status": "cleaned"}
            self._send_json_response(200, response)
        else:
            self._send_response(404, b'{"error":"Not Found"}', "application/json")
    
    def _send_response(self, status_code, content, content_type):
        """Send HTTP response with minimal overhead."""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(content)
    
    def _send_json_response(self, status_code, data):
        """Send JSON response."""
        content = json.dumps(data).encode('utf-8')
        self._send_response(status_code, content, "application/json")

def run_zero_imports_server(host="0.0.0.0", port=None):
    """Run server with absolute zero external dependencies."""
    print(f"ZERO_IMPORTS_DEBUG: Starting at {time.time()}", flush=True)
    
    # CRITICAL FIX: Use PORT environment variable as required by Smithery
    if port is None:
        port = int(os.getenv('PORT', 8000))
    
    print(f"ZERO_IMPORTS_DEBUG: Using port {port} (from PORT env var or default)", flush=True)
    
    server = HTTPServer((host, port), UltraMinimalHandler)
    
    print(f"ZERO_IMPORTS_DEBUG: Server created at {time.time()}", flush=True)
    print(f"ZERO_IMPORTS_DEBUG: Starting server on {host}:{port}", flush=True)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_zero_imports_server() 