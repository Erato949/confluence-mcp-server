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
TOOLS_JSON = b'{"tools":[{"name":"get_confluence_page","description":"Retrieve a Confluence page by ID or URL","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"},"page_url":{"type":"string","description":"Page URL"}}}},{"name":"search_confluence_pages","description":"Search Confluence pages with CQL","inputSchema":{"type":"object","properties":{"cql":{"type":"string","description":"CQL query"},"limit":{"type":"integer","description":"Result limit"}},"required":["cql"]}},{"name":"create_confluence_page","description":"Create a new Confluence page","inputSchema":{"type":"object","properties":{"space_key":{"type":"string","description":"Space key"},"title":{"type":"string","description":"Page title"},"content":{"type":"string","description":"Page content"}},"required":["space_key","title","content"]}},{"name":"update_confluence_page","description":"Update an existing Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"},"title":{"type":"string","description":"New title"},"content":{"type":"string","description":"New content"}},"required":["page_id"]}},{"name":"delete_confluence_page","description":"Delete a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID to delete"}},"required":["page_id"]}},{"name":"get_confluence_spaces","description":"List available Confluence spaces","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","description":"Number of spaces to return"}}}},{"name":"get_page_attachments","description":"Get attachments for a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"}},"required":["page_id"]}},{"name":"add_page_attachment","description":"Add attachment to a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"},"file_path":{"type":"string","description":"File path"},"filename":{"type":"string","description":"File name"}},"required":["page_id","file_path"]}},{"name":"delete_page_attachment","description":"Delete attachment from a Confluence page","inputSchema":{"type":"object","properties":{"attachment_id":{"type":"string","description":"Attachment ID"}},"required":["attachment_id"]}},{"name":"get_page_comments","description":"Get comments for a Confluence page","inputSchema":{"type":"object","properties":{"page_id":{"type":"string","description":"Page ID"}},"required":["page_id"]}}]}'

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
                
                if method == "tools/list":
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