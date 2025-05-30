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

# Lazy imports for selective editing (loaded only when needed)
_selective_editing_loaded = False
def _load_selective_editing():
    """Lazy load selective editing modules for performance."""
    global _selective_editing_loaded
    if not _selective_editing_loaded:
        global SectionEditor, PatternEditor, StructuralEditor
        from confluence_mcp_server.selective_editing.section_editor import SectionEditor
        from confluence_mcp_server.selective_editing.pattern_editor import PatternEditor  
        from confluence_mcp_server.selective_editing.structural_editor import StructuralEditor
        _selective_editing_loaded = True

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
                "tools_count": 13,
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
                elif method == "resources/list":
                    # Return empty resources list - not used by this server
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": {"resources": []}
                    }
                elif method == "prompts/list":
                    # Return empty prompts list - not used by this server
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "result": {"prompts": []}
                    }
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
                "description": """Retrieves a specific Confluence page with its content and metadata.

**Use Cases:**
- Get page content to read or analyze
- Retrieve page metadata (author, version, dates)
- Get page structure information (parent, space)
- Access page content for AI processing

**Examples:**
- Get page by ID: {"page_id": "123456"}
- Get page by space and title: {"space_key": "DOCS", "title": "Meeting Notes"}
- Get page with expanded content: {"page_id": "123456", "expand": "body.view,version,space"}

**Tips:**
- Use page_id when you know the exact page ID (faster)
- Use space_key + title for human-readable page identification
- Add expand parameter to get page content in the response
- Common expand values: 'body.view' (HTML content), 'body.storage' (raw format), 'version', 'space'""",
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
                "description": """Search for Confluence pages using text queries or advanced CQL (Confluence Query Language).

**Use Cases:**
- Find pages containing specific keywords
- Search within a specific space
- Use advanced queries with CQL for precise results
- Discover content by topic or metadata

**Examples:**
- Simple text search: {"query": "meeting notes"}
- Search in specific space: {"query": "API documentation", "space_key": "TECH"}
- Advanced CQL search: {"cql": "space = DOCS AND created >= '2024-01-01'"}
- Search with content preview: {"query": "project", "expand": "body.view", "excerpt": "highlight"}

**Tips:**
- Use 'query' for simple text searches (easier)
- Use 'cql' for complex searches with precise criteria
- Add 'expand' to get page content in results
- Use 'excerpt' to get highlighted search matches
- Increase 'limit' for more results (max 100)""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "Simple text search query. Example: 'meeting notes', 'API documentation', 'project status'. Searches page titles and content."
                        },
                        "cql": {
                            "type": "string", 
                            "description": "Advanced CQL (Confluence Query Language) query. Examples: 'space = DOCS AND title ~ \"API*\"', 'created >= \"2024-01-01\"', 'creator = currentUser()'. Use for precise searches."
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
                "description": """Creates a new page in Confluence with specified content and structure.

**Use Cases:**
- Create documentation pages
- Add meeting notes or reports
- Create child pages under existing pages
- Generate pages from templates or structured content

**Examples:**
- Basic page: {"space_key": "DOCS", "title": "New Feature Guide", "content": "<p>Feature overview...</p>"}
- Child page: {"space_key": "DOCS", "title": "Sub-section", "content": "<p>Details...</p>", "parent_page_id": "123456"}
- Rich content page with formatting, tables, and links

**Tips:**
- Always specify space_key (required)
- Use descriptive, unique titles
- Add parent_page_id to create hierarchical structure
- Start with simple HTML, enhance later via Confluence UI
- Consider page templates for consistent formatting""",
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
                "description": """Updates an existing Confluence page's title, content, or position in the page hierarchy.

**Use Cases:**
- Modify page content or structure
- Update page titles for better organization
- Move pages to different parents (restructure hierarchy)
- Make incremental content updates

**Examples:**
- Update content: {"page_id": "123456", "new_version_number": 2, "content": "<p>Updated content...</p>"}
- Change title: {"page_id": "123456", "new_version_number": 2, "title": "New Title"}
- Move to different parent: {"page_id": "123456", "new_version_number": 2, "parent_page_id": "789012"}
- Make top-level: {"page_id": "123456", "new_version_number": 2, "parent_page_id": ""}

**Tips:**
- Get current page first to know the version number
- Use get_confluence_page to see current state before updating
- You can update multiple fields in one operation
- Empty parent_page_id makes page top-level in space
- Preserve existing formatting when updating content""",
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
                "description": """Permanently moves a Confluence page to trash (soft delete).

**Use Cases:**
- Remove outdated or incorrect pages
- Clean up draft pages that are no longer needed
- Archive pages that shouldn't be visible anymore
- Free up space organization

**Examples:**
- Delete page: {"page_id": "123456"}

**Tips:**
- Pages are moved to trash, not permanently deleted
- Deleted pages can be restored from trash by admins
- Check for child pages that might be affected
- Consider the impact on page links and references""",
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
                "description": """Retrieves a list of Confluence spaces that the user has access to.

**Use Cases:**
- Discover available spaces for content creation
- Get space keys for page operations
- Browse space structure and organization
- Verify access permissions to spaces

**Examples:**
- Get all spaces: {"limit": 50}
- Get spaces with pagination: {"limit": 25, "start": 25}

**Tips:**
- Use space keys in page creation and search operations
- Space keys are required for creating pages
- Personal spaces usually have keys like '~username'
- Global spaces are shared across the organization""",
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
                "description": """Retrieves a list of attachments from a specific Confluence page.

**Use Cases:**
- List all files attached to a page
- Find specific attachments by name or type
- Get attachment metadata (size, type, upload date)
- Download or reference files from pages

**Examples:**
- Get all attachments: {"page_id": "123456"}
- Search for specific file: {"page_id": "123456", "filename": "diagram.png"}
- Filter by file type: {"page_id": "123456", "media_type": "image/png"}
- Get with pagination: {"page_id": "123456", "limit": 25, "start": 25}

**Tips:**
- Use filename parameter for exact filename searches
- Use media_type to filter by file type (image/*, application/pdf, etc.)
- Large pages may have many attachments - use pagination
- Download URLs are temporary and should be used promptly""",
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
                "description": """Uploads a file as an attachment to a specific Confluence page.

**Use Cases:**
- Add supporting documents to pages
- Upload images for page content
- Attach spreadsheets, PDFs, or other files
- Share files with page viewers

**Examples:**
- Upload file: {"page_id": "123456", "file_path": "/path/to/document.pdf"}
- Custom filename: {"page_id": "123456", "file_path": "/path/to/file.txt", "filename_on_confluence": "report.txt"}
- With comment: {"page_id": "123456", "file_path": "/path/to/image.png", "comment": "Updated diagram"}

**Tips:**
- File must exist and be readable
- Check Confluence file size limits (usually 50MB-100MB)
- Use descriptive filenames for better organization
- Add comments to explain file purpose or version""",
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
                "description": """Permanently deletes an attachment from a Confluence page.

**Use Cases:**
- Remove outdated or incorrect files
- Clean up duplicate attachments
- Free up storage space
- Remove sensitive files

**Examples:**
- Delete attachment: {"attachment_id": "att123456"}

**Tips:**
- Attachment deletion is permanent (cannot be undone)
- Get attachment ID from get_page_attachments first
- Deleting attachments may break page content that references them
- Consider the impact on users who might be downloading the file""",
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
                "description": """Retrieves comments and discussions from a specific Confluence page.

**Use Cases:**
- Read feedback and discussions on pages
- Get comment metadata (author, date, replies)
- Monitor page engagement and collaboration
- Export comments for reporting or analysis

**Examples:**
- Get all comments: {"page_id": "123456"}
- Get with pagination: {"page_id": "123456", "limit": 25, "start": 25}
- Get expanded details: {"page_id": "123456", "expand": "body.view,version"}

**Tips:**
- Use expand parameter to get comment content
- Comments are paginated - use start/limit for large discussions
- Comment hierarchy shows reply relationships
- Some comments may be restricted based on permissions""",
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
            },
            {
                "name": "update_page_section",
                "description": """Updates a specific section of a Confluence page by replacing content under a heading.

🚀 **Revolutionary Capability:** Industry's first XML-aware selective editing system that allows surgical precision modifications without affecting surrounding content.

**Use Cases:**
- Update project status sections without touching meeting notes
- Refresh API documentation while preserving examples and troubleshooting  
- Update progress reports while maintaining historical context
- Modify specific sections of large documentation pages

**Examples:**
- Update status: {"page_id": "123456789", "heading": "Project Status", "new_content": "<p><strong>Status:</strong> Completed ✅</p>"}
- Precise targeting: {"page_id": "456789123", "heading": "Overview", "heading_level": 2, "exact_match": true, "new_content": "<p>Updated overview...</p>"}

**Key Features:**
- Structure Preservation: Maintains all macros, layouts, and formatting outside target section
- Intelligent Targeting: Finds headings by text with flexible matching options
- Nested Support: Handles complex heading hierarchies correctly
- Safe Editing: Automatic backup creation for rollback capability""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the page to update"
                        },
                        "heading": {
                            "type": "string", 
                            "description": "The heading text to find (case-insensitive by default)"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "New content to replace the section with (Confluence storage format)"
                        },
                        "heading_level": {
                            "type": "integer",
                            "description": "Specific heading level to match (1-6). Optional."
                        },
                        "exact_match": {
                            "type": "boolean", 
                            "description": "Whether to require exact heading text match. Default: false."
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether heading search should be case-sensitive. Default: false."
                        }
                    },
                    "required": ["page_id", "heading", "new_content"]
                }
            },
            {
                "name": "replace_text_pattern", 
                "description": """Replaces text patterns throughout a Confluence page with intelligent content preservation.

🚀 **Revolutionary Capability:** XML-aware pattern replacement that preserves macros, formatting, and document structure while performing precise text substitutions across entire pages.

**Use Cases:**
- Update product names, versions, or terminology across documentation
- Fix typos or standardize spelling throughout pages
- Replace outdated URLs, email addresses, or contact information
- Update status indicators, dates, or version numbers globally
- Rebrand content by replacing company names or product references

**Examples:**
- Update version: {"page_id": "123456789", "search_pattern": "v1.2.3", "replacement": "v2.0.0", "case_sensitive": true}
- Fix typos: {"page_id": "987654321", "search_pattern": "recieve", "replacement": "receive"}
- Limited changes: {"page_id": "789123456", "search_pattern": "TODO", "replacement": "✅ COMPLETED", "max_replacements": 3}

**Key Features:**
- XML Structure Preservation: Never breaks macros, links, or formatting elements
- Smart Content Detection: Distinguishes between content text and XML markup
- Flexible Matching: Case sensitivity, whole words, and replacement limits
- Safe Operations: Preserves document structure while changing text""",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the page to update"
                        },
                        "search_pattern": {
                            "type": "string",
                            "description": "Text pattern to search for"
                        },
                        "replacement": {
                            "type": "string",
                            "description": "Text to replace matches with"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether search should be case-sensitive. Default: false."
                        },
                        "whole_words_only": {
                            "type": "boolean", 
                            "description": "Whether to match whole words only. Default: false."
                        },
                        "max_replacements": {
                            "type": "integer",
                            "description": "Maximum number of replacements to make. Optional."
                        }
                    },
                    "required": ["page_id", "search_pattern", "replacement"]
                }
            },
            {
                "name": "update_table_cell",
                "description": """Updates a specific cell in a table within a Confluence page with surgical precision.

🚀 **Revolutionary Capability:** Direct table cell editing that preserves table structure, formatting, and all surrounding content while modifying specific data points with zero-based indexing.

**Use Cases:**
- Update project status tables with current progress
- Modify data in comparison or feature matrices
- Update metrics, dates, or values in tracking tables
- Correct information in existing documentation tables
- Update pricing, specifications, or contact information

**Examples:**
- Update status: {"page_id": "123456789", "table_index": 0, "row_index": 2, "column_index": 1, "new_cell_content": "<strong>Completed ✅</strong>"}
- Update metrics: {"page_id": "456789123", "table_index": 1, "row_index": 1, "column_index": 0, "new_cell_content": "<strong>99.9%</strong> <em>(improved)</em>"}

**Key Features:**
- Zero-Based Indexing: table_index=0 (first table), row_index=0 (first row), column_index=0 (first column)
- Structure Preservation: Maintains table formatting, borders, and styling
- Rich Content Support: Supports HTML, links, formatting within cells
- Surgical Precision: Only the target cell is modified, all other data unchanged

**Index Reference:**
- table_index: 0=first table, 1=second table, 2=third table
- row_index: 0=first row (including headers), 1=second row
- column_index: 0=first column, 1=second column""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the page to update"
                        },
                        "table_index": {
                            "type": "integer",
                            "description": "Zero-based index of the table (0 for first table)"
                        },
                        "row_index": {
                            "type": "integer", 
                            "description": "Zero-based index of the row within the table"
                        },
                        "column_index": {
                            "type": "integer",
                            "description": "Zero-based index of the column within the row"
                        },
                        "new_cell_content": {
                            "type": "string",
                            "description": "New content for the cell (can include HTML)"
                        }
                    },
                    "required": ["page_id", "table_index", "row_index", "column_index", "new_cell_content"]
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
            
            # Parse the URL to extract the base URL properly for Confluence Cloud
            if confluence_url.startswith(('http://', 'https://')):
                # Extract the full URL up to /wiki path for Confluence Cloud
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
                # Force HTTPS and include /wiki path for Confluence Cloud API
                base_url = f'https://{domain}/wiki'
            else:
                # Assume it's just a domain name
                domain = confluence_url.strip().rstrip('/').split('/')[0]
                base_url = f'https://{domain}/wiki'
            
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
                    logger.warning(f"TOOL_EXECUTION: httpx client created successfully with base_url='{str(client.base_url)}'")
                    
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
                    elif tool_name == "update_page_section":
                        # Load selective editing modules
                        _load_selective_editing()
                        
                        # Get current page content
                        page_response = await client.get(f"/rest/api/content/{tool_args['page_id']}?expand=body.storage,version")
                        page_response.raise_for_status()
                        page_data = page_response.json()
                        
                        current_content = page_data['body']['storage']['value']
                        current_version = page_data['version']['number']
                        
                        # Initialize section editor and perform replacement
                        section_editor = SectionEditor()
                        edit_result = section_editor.replace_section(
                            content=current_content,
                            heading=tool_args['heading'],
                            new_content=tool_args['new_content'],
                            heading_level=tool_args.get('heading_level'),
                            exact_match=tool_args.get('exact_match', False),
                            case_sensitive=tool_args.get('case_sensitive', False)
                        )
                        
                        if not edit_result.success:
                            return {
                                "jsonrpc": "2.0",
                                "id": message.get("id"),
                                "error": {"code": -32603, "message": f"Failed to update section: {edit_result.error_message}"}
                            }
                        
                        # Update the page
                        update_data = {
                            "version": {"number": current_version + 1},
                            "body": {"storage": {"value": edit_result.modified_content, "representation": "storage"}}
                        }
                        update_response = await client.put(f"/rest/api/content/{tool_args['page_id']}", json=update_data)
                        update_response.raise_for_status()
                        
                        result = {
                            "success": True,
                            "message": f"Successfully updated section '{tool_args['heading']}'",
                            "changes_made": edit_result.changes_made or [f"Updated section under heading '{tool_args['heading']}'"],
                            "backup_available": edit_result.backup_content is not None
                        }
                    elif tool_name == "replace_text_pattern":
                        # Load selective editing modules
                        _load_selective_editing()
                        
                        # Get current page content
                        page_response = await client.get(f"/rest/api/content/{tool_args['page_id']}?expand=body.storage,version")
                        page_response.raise_for_status()
                        page_data = page_response.json()
                        
                        current_content = page_data['body']['storage']['value']
                        current_version = page_data['version']['number']
                        
                        # Initialize pattern editor and perform replacement
                        pattern_editor = PatternEditor()
                        edit_result = pattern_editor.replace_text_pattern(
                            content=current_content,
                            search_pattern=tool_args['search_pattern'],
                            replacement=tool_args['replacement'],
                            case_sensitive=tool_args.get('case_sensitive', False),
                            whole_words_only=tool_args.get('whole_words_only', False),
                            max_replacements=tool_args.get('max_replacements')
                        )
                        
                        if not edit_result.success:
                            return {
                                "jsonrpc": "2.0",
                                "id": message.get("id"),
                                "error": {"code": -32603, "message": f"Failed to replace text pattern: {edit_result.error_message}"}
                            }
                        
                        # Count replacements made
                        replacements_made = len([change for change in (edit_result.changes_made or []) if "replacement" in change.lower()])
                        
                        # Update the page
                        update_data = {
                            "version": {"number": current_version + 1},
                            "body": {"storage": {"value": edit_result.modified_content, "representation": "storage"}}
                        }
                        update_response = await client.put(f"/rest/api/content/{tool_args['page_id']}", json=update_data)
                        update_response.raise_for_status()
                        
                        result = {
                            "success": True,
                            "message": f"Successfully replaced {replacements_made} instances of '{tool_args['search_pattern']}'",
                            "replacements_made": replacements_made,
                            "changes_made": edit_result.changes_made or [f"Replaced text pattern '{tool_args['search_pattern']}' with '{tool_args['replacement']}'"],
                            "backup_available": edit_result.backup_content is not None
                        }
                    elif tool_name == "update_table_cell":
                        # Load selective editing modules
                        _load_selective_editing()
                        
                        # Get current page content
                        page_response = await client.get(f"/rest/api/content/{tool_args['page_id']}?expand=body.storage,version")
                        page_response.raise_for_status()
                        page_data = page_response.json()
                        
                        current_content = page_data['body']['storage']['value']
                        current_version = page_data['version']['number']
                        
                        # Initialize structural editor and perform table cell update
                        structural_editor = StructuralEditor()
                        edit_result = structural_editor.update_table_cell(
                            content=current_content,
                            table_index=tool_args['table_index'],
                            row_index=tool_args['row_index'],
                            column_index=tool_args['column_index'],
                            new_cell_content=tool_args['new_cell_content']
                        )
                        
                        if not edit_result.success:
                            return {
                                "jsonrpc": "2.0",
                                "id": message.get("id"),
                                "error": {"code": -32603, "message": f"Failed to update table cell: {edit_result.error_message}"}
                            }
                        
                        # Update the page
                        update_data = {
                            "version": {"number": current_version + 1},
                            "body": {"storage": {"value": edit_result.modified_content, "representation": "storage"}}
                        }
                        update_response = await client.put(f"/rest/api/content/{tool_args['page_id']}", json=update_data)
                        update_response.raise_for_status()
                        
                        result = {
                            "success": True,
                            "message": f"Successfully updated table[{tool_args['table_index']}] cell at row {tool_args['row_index']}, column {tool_args['column_index']}",
                            "changes_made": edit_result.changes_made or [f"Updated table cell at [{tool_args['row_index']}, {tool_args['column_index']}]"],
                            "backup_available": edit_result.backup_content is not None
                        }
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
                            # Use mode='json' to ensure HttpUrl objects are serialized as strings
                            result_dict = result.model_dump(mode='json')
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