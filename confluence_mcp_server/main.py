#!/usr/bin/env python3
"""
Confluence MCP Server v1.2.0 - Production Ready
A Model Context Protocol server for Confluence integration
"""

# confluence_mcp_server/main.py (CLEAN VERSION - NO STDOUT/STDERR INTERFERENCE)
# Standard Library Imports
import asyncio
import os
import logging
import sys
import base64
import json
from typing import Optional, Dict, Any

# Third-Party Imports
from dotenv import load_dotenv
import httpx # For making HTTP requests to Confluence API
from fastmcp import FastMCP # Corrected import for FastMCP
from fastmcp.exceptions import ToolError # Using ToolError instead of McpError
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError
from mcp.types import ErrorData

# Local Application/Library Specific Imports
try:
    from confluence_mcp_server.utils.logging_config import setup_logging
    from confluence_mcp_server.mcp_actions import page_actions, space_actions, attachment_actions, comment_actions
    from confluence_mcp_server.mcp_actions.schemas import (
        # Page Schemas
        GetPageInput, PageOutput,
        SearchPagesInput, SearchPagesOutput,
        CreatePageInput, CreatePageOutput,
        UpdatePageInput, UpdatePageOutput,
        DeletePageInput, DeletePageOutput,
        # Space Schemas
        GetSpacesInput, GetSpacesOutput,
        # Attachment Schemas
        GetAttachmentsInput, GetAttachmentsOutput,
        AddAttachmentInput, AddAttachmentOutput,
        DeleteAttachmentInput, DeleteAttachmentOutput,
        # Comment Schemas
        GetCommentsInput, GetCommentsOutput
    )
except ImportError as e:
    # Fail silently - don't write to stderr as it can interfere with MCP protocol
    pass

# --- Setup Logging (No stderr output) ---
logger = logging.getLogger(__name__)

# --- Tool Calling Convention Detection ---
def detect_calling_convention() -> str:
    """
    Detect which MCP tool calling convention to use.
    
    Returns:
        'direct' for modern direct parameter calling
        'schema' for legacy schema-based calling with inputs wrapper
    """
    try:
        # Method 1: Check for explicit environment variable override
        convention = os.getenv('MCP_TOOL_CONVENTION', '').lower()
        if convention in ['direct', 'schema']:
            logger.info(f"TOOL_CONVENTION: Using explicit override - {convention}")
            return convention
        
        # Method 2: Detect test environment (pytest execution)
        # Our tests expect schema-based tools with {"inputs": {...}} format
        if 'pytest' in sys.modules or any('pytest' in arg for arg in sys.argv) or 'test' in sys.argv[0]:
            logger.info("TOOL_CONVENTION: Test environment detected - using schema convention")
            return 'schema'
        
        # Method 3: Check for Smithery.ai deployment indicators (uses modern conventions)
        if (os.getenv('SMITHERY_CONFIG') or 
            os.getenv('MCP_CONFIG') or 
            os.getenv('SMITHERY_CONFLUENCE_URL') or
            any('config' in arg for arg in sys.argv)):
            logger.info("TOOL_CONVENTION: Detected Smithery deployment - using direct parameter convention")
            return 'direct'
        
        # Method 4: Check for known direct-parameter clients
        # Cursor and newer Claude Desktop versions prefer direct parameters
        client_hint = os.getenv('MCP_CLIENT') or os.getenv('USER_AGENT') or ''
        if any(hint in client_hint.lower() for hint in ['cursor', 'claude-desktop-2', 'windsurf']):
            logger.info(f"TOOL_CONVENTION: Detected modern client ({client_hint}) - using direct convention")
            return 'direct'
        
        # Method 5: Check FastMCP version - but be more conservative
        # Only use direct for very new versions that explicitly support it well
        try:
            import fastmcp
            if hasattr(fastmcp, '__version__'):
                version_str = fastmcp.__version__
                # Parse version to compare - only use direct for 3.0+ for now
                if version_str and version_str.startswith('3.'):
                    logger.info(f"TOOL_CONVENTION: FastMCP version {version_str} - using direct convention")
                    return 'direct'
                else:
                    logger.info(f"TOOL_CONVENTION: FastMCP version {version_str} - using schema convention for compatibility")
        except:
            pass
        
        # Method 6: Default strategy based on deployment context
        # If we're in a containerized/cloud environment, prefer direct
        if os.getenv('KUBERNETES_SERVICE_HOST') or os.getenv('DOCKER_CONTAINER') or os.getenv('DYNO'):
            logger.info("TOOL_CONVENTION: Cloud deployment detected - using direct convention")
            return 'direct'
        
        # Default: Use schema-based for maximum backward compatibility
        logger.info("TOOL_CONVENTION: Using schema-based convention (default for backward compatibility)")
        return 'schema'
        
    except Exception as e:
        logger.warning(f"TOOL_CONVENTION: Error in detection, defaulting to schema: {e}")
        return 'schema'

# Detect convention once at module load
TOOL_CONVENTION = detect_calling_convention()
logger.info(f"TOOL_CONVENTION: Selected '{TOOL_CONVENTION}' convention")

# --- Configuration Support for Multiple Deployment Contexts ---
def detect_and_apply_smithery_config() -> Optional[Dict[str, str]]:
    """
    Detects and applies Smithery.ai configuration parameters.
    
    Smithery.ai passes configuration in several ways:
    1. Via command line arguments with base64-encoded config
    2. Via environment variables with base64-encoded config
    3. Via query parameters (for HTTP mode)
    
    This function checks for these patterns and extracts Confluence credentials
    that can be used alongside or instead of environment variables.
    
    Returns:
        Dict containing Confluence credentials if found, None otherwise
    """
    try:
        # Method 1: Check command line arguments for config parameter
        # Smithery might pass: python main.py --config <base64_encoded_json>
        config_data = None
        
        for i, arg in enumerate(sys.argv):
            if arg in ['--config', '-c'] and i + 1 < len(sys.argv):
                config_param = sys.argv[i + 1]
                config_data = _parse_config_parameter(config_param)
                if config_data:
                    logger.info("SMITHERY_CONFIG: Found config via command line arguments")
                    break
        
        # Method 2: Check environment variables for Smithery config
        if not config_data:
            env_config = os.getenv('SMITHERY_CONFIG') or os.getenv('MCP_CONFIG')
            if env_config:
                config_data = _parse_config_parameter(env_config)
                if config_data:
                    logger.info("SMITHERY_CONFIG: Found config via environment variable")
        
        # Method 3: Check for individual Smithery environment variables
        # (This handles cases where Smithery sets individual env vars instead of JSON)
        if not config_data:
            smithery_url = os.getenv('SMITHERY_CONFLUENCE_URL')
            smithery_username = os.getenv('SMITHERY_USERNAME') 
            smithery_token = os.getenv('SMITHERY_API_TOKEN')
            
            if smithery_url or smithery_username or smithery_token:
                config_data = {
                    'confluenceUrl': smithery_url,
                    'username': smithery_username,
                    'apiToken': smithery_token
                }
                logger.info("SMITHERY_CONFIG: Found config via individual Smithery env vars")
        
        if config_data:
            # Apply Smithery config to environment variables for compatibility
            return _apply_smithery_config_to_env(config_data)
        
        return None
        
    except Exception as e:
        logger.warning(f"SMITHERY_CONFIG: Error detecting Smithery config: {e}")
        return None

def _parse_config_parameter(config_param: str) -> Optional[Dict[str, Any]]:
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
        logger.debug(f"SMITHERY_CONFIG: Failed to parse config parameter: {e}")
        return None

def _apply_smithery_config_to_env(config_data: Dict[str, Any]) -> Dict[str, str]:
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
                logger.info(f"SMITHERY_CONFIG: Set {env_var} from Smithery config")
            else:
                logger.info(f"SMITHERY_CONFIG: {env_var} already set, preserving existing value")
    
    return applied_config

# --- FastMCP Server Instance ---
# Create the FastMCP server instance here so it can be used by tool decorators
mcp_server = FastMCP(
    name="ConfluenceMCPServer"
)

# --- Authentication Functions ---
async def get_confluence_client() -> httpx.AsyncClient:
    """
    Creates an authenticated httpx client for Confluence API requests.
    
    Supports dual configuration sources:
    1. Environment variables (for Claude Desktop and local development)
    2. Smithery.ai configuration parameters (for Smithery deployment)
    
    Returns:
        httpx.AsyncClient: An authenticated client configured for Confluence API
        
    Raises:
        ToolError: If authentication credentials are missing or invalid
    """
    # First, try to detect and apply Smithery.ai configuration
    smithery_config = detect_and_apply_smithery_config()
    
    # Retrieve required credentials from environment variables
    # (These may have been set by Smithery config detection above)
    confluence_url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME") 
    api_token = os.getenv("CONFLUENCE_API_TOKEN")
    
    # Enhanced error message for debugging deployment issues
    if not all([confluence_url, username, api_token]):
        missing_vars = []
        if not confluence_url:
            missing_vars.append("CONFLUENCE_URL")
        if not username:
            missing_vars.append("CONFLUENCE_USERNAME")
        if not api_token:
            missing_vars.append("CONFLUENCE_API_TOKEN")
        
        # Provide detailed error for troubleshooting
        error_details = f"Missing config: {', '.join(missing_vars)}"
        if smithery_config:
            error_details += f". Smithery config detected but incomplete: {list(smithery_config.keys())}"
        else:
            error_details += ". No Smithery config detected. Ensure credentials are provided via environment variables or Smithery configuration."
            
        logger.error(f"CONFLUENCE_AUTH_ERROR: {error_details}")
        raise ToolError(error_details)
    
    # Normalize URL by removing trailing slash to ensure consistent API endpoint construction
    base_url = confluence_url.rstrip('/')
    
    # Create authenticated HTTP client with Confluence-specific configuration
    # Uses basic auth with username (email) and API token
    client = httpx.AsyncClient(
        base_url=base_url,
        auth=(username, api_token),  # Basic auth: username and API token
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        timeout=30.0  # 30 second timeout for API requests
    )
    
    return client

# --- MCP Tool Definitions ---

# Placeholder for the utility function if not created yet
# In a real scenario, this would be in confluence_mcp_server/utils/confluence_utils.py
def get_page_url_from_api_response(page_data: Dict[str, Any], base_confluence_url: Optional[str]) -> Optional[str]:
    if not base_confluence_url:
        return None
    api_links = page_data.get('_links', {})
    webui_link = api_links.get('webui') # typically like '/display/SPACEKEY/Page+Title' or '/pages/12345'
    base_link = api_links.get('base') # typically the Confluence base URL

    if webui_link and base_link:
        # Ensure no double slashes if webui_link is absolute or base_link already has context path
        # This logic might need refinement based on actual link formats
        if webui_link.startswith('http'): # if webui_link is already absolute
            return webui_link
        return str(base_link).rstrip('/') + str(webui_link)
    
    # Fallback if _links.webui is not present but page_id is
    page_id = page_data.get('id')
    if page_id:
        return f"{str(base_confluence_url).rstrip('/')}/pages/viewpage.action?pageId={page_id}"
    return None

# --- NEW DUAL CALLING CONVENTION TOOL WRAPPERS ---
# These support both old {"inputs": {...}} and new {...} calling conventions

async def get_confluence_page(inputs: GetPageInput) -> PageOutput:
    """
    Retrieves a specific Confluence page with its content and metadata.
    
    **Use Cases:**
    - Get page content to read or analyze
    - Retrieve page metadata (author, version, dates)
    - Get page structure information (parent, space)
    - Access page content for AI processing
    
    **Examples:**
    - Get page by ID: `{"page_id": "123456"}`
    - Get page by space and title: `{"space_key": "DOCS", "title": "Meeting Notes"}`
    - Get page with expanded content: `{"page_id": "123456", "expand": "body.view,version,space"}`
    
    **Tips:**
    - Use page_id when you know the exact page ID (faster)
    - Use space_key + title for human-readable page identification
    - Add expand parameter to get page content in the response
    - Common expand values: 'body.view' (HTML content), 'body.storage' (raw format), 'version', 'space'
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.get_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_confluence_page: {str(e)}")
        raise ToolError(f"Failed to retrieve page: {str(e)}")

async def get_confluence_page_direct(
    page_id: Optional[str] = None,
    space_key: Optional[str] = None,
    title: Optional[str] = None,
    expand: Optional[str] = None
) -> PageOutput:
    """
    Retrieves a specific Confluence page with its content and metadata.
    
    **Use Cases:**
    - Get page content to read or analyze
    - Retrieve page metadata (author, version, dates)
    - Get page structure information (parent, space)
    - Get current version before updating a page
    
    **Examples:**
    - Get page by ID: `{"page_id": "123456"}`
    - Get page by space and title: `{"space_key": "DOCS", "title": "Meeting Notes"}`
    - Get page with expanded content: `{"page_id": "123456", "expand": "body.view,version,space"}`
    
    **Tips:**
    - Use page_id when you know the exact page ID (faster)
    - Use space_key + title for human-readable page identification
    - Add expand parameter to get page content in the response
    - Common expand values: 'body.view' (HTML content), 'body.storage' (raw format), 'version', 'space'
    
    **Related Tools:**
    - Use `search_confluence_pages()` to find page IDs when you only know partial information
    - Use `get_confluence_spaces()` to find available space keys
    - Use `update_confluence_page()` with the version number from this response
    - Use `get_page_attachments()` to get files associated with this page
    - Use `get_page_comments()` to get discussions on this page
    
    **Workflow Example:**
    1. Find page: `search_confluence_pages({"query": "API documentation", "space_key": "TECH"})`
    2. Get full page: `get_confluence_page({"page_id": "123456", "expand": "body.view,version"})`
    3. Update page: `update_confluence_page({"page_id": "123456", "new_version_number": 6, "content": "..."})`
    """
    try:
        # Construct schema object from direct parameters
        inputs = GetPageInput(
            page_id=page_id,
            space_key=space_key,
            title=title,
            expand=expand
        )
        async with await get_confluence_client() as client:
            result = await page_actions.get_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_confluence_page: {str(e)}")
        raise ToolError(f"Failed to retrieve page: {str(e)}")

async def search_confluence_pages(inputs: SearchPagesInput) -> SearchPagesOutput:
    """
    Search for Confluence pages using text queries or advanced CQL (Confluence Query Language).
    
    **Use Cases:**
    - Find pages containing specific keywords
    - Search within a specific space
    - Use advanced queries with CQL for precise results
    - Discover content by topic or metadata
    
    **Examples:**
    - Simple text search: `{"query": "meeting notes"}`
    - Search in specific space: `{"query": "API documentation", "space_key": "TECH"}`
    - Advanced CQL search: `{"cql": "space = DOCS AND created >= '2024-01-01'"}`
    - Search with content preview: `{"query": "project", "expand": "body.view", "excerpt": "highlight"}`
    
    **CQL Examples:**
    - Find pages by title: `title ~ "API*"`
    - Find recent pages: `created >= '2024-01-01'`
    - Find pages by author: `creator = currentUser()`
    - Combine criteria: `space = DOCS AND type = page AND title ~ "meeting*"`
    
    **Tips:**
    - Use 'query' for simple text searches (easier)
    - Use 'cql' for complex searches with precise criteria
    - Add 'expand' to get page content in results
    - Use 'excerpt' to get highlighted search matches
    - Increase 'limit' for more results (max 100)
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.search_pages_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in search_confluence_pages: {str(e)}")
        raise ToolError(f"Failed to search pages: {str(e)}")

async def search_confluence_pages_direct(
    query: Optional[str] = None,
    cql: Optional[str] = None,
    space_key: Optional[str] = None,
    limit: int = 25,
    start: int = 0,
    expand: Optional[str] = None,
    excerpt: Optional[str] = None
) -> SearchPagesOutput:
    """
    Retrieves a list of Confluence pages using text queries or advanced CQL (Confluence Query Language).
    
    **Use Cases:**
    - Find pages containing specific keywords
    - Search within a specific space
    - Use advanced queries with CQL for precise results
    - Discover content by topic or metadata
    
    **Examples:**
    - Simple text search: `{"query": "meeting notes"}`
    - Search in specific space: `{"query": "API documentation", "space_key": "TECH"}`
    - Advanced CQL search: `{"cql": "space = DOCS AND created >= '2024-01-01'"}`
    - Search with content preview: `{"query": "project", "expand": "body.view", "excerpt": "highlight"}`
    
    **CQL Examples:**
    - Find pages by title: `title ~ "API*"`
    - Find recent pages: `created >= '2024-01-01'`
    - Find pages by author: `creator = currentUser()`
    - Combine criteria: `space = DOCS AND type = page AND title ~ "meeting*"`
    
    **Tips:**
    - Use 'query' for simple text searches (easier)
    - Use 'cql' for complex searches with precise criteria
    - Add 'expand' to get page content in results
    - Use 'excerpt' to get highlighted search matches
    - Increase 'limit' for more results (max 100)
    """
    try:
        # Construct schema object from direct parameters
        inputs = SearchPagesInput(
            query=query,
            cql=cql,
            space_key=space_key,
            limit=limit,
            start=start,
            expand=expand,
            excerpt=excerpt
        )
        async with await get_confluence_client() as client:
            result = await page_actions.search_pages_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in search_confluence_pages_direct: {str(e)}")
        raise ToolError(f"Failed to search pages: {str(e)}")

async def create_confluence_page(inputs: CreatePageInput) -> CreatePageOutput:
    """
    Creates a new page in Confluence with specified content and structure.
    
    **Use Cases:**
    - Create documentation pages
    - Add meeting notes or reports
    - Create child pages under existing pages
    - Generate pages from templates or structured content
    
    **Examples:**
    - Basic page: `{"space_key": "DOCS", "title": "New Feature Guide", "content": "<p>Feature overview...</p>"}`
    - Child page: `{"space_key": "DOCS", "title": "Sub-section", "content": "<p>Details...</p>", "parent_page_id": "123456"}`
    - Rich content page with formatting, tables, and links
    
    **Content Format:**
    - Use Confluence Storage Format (XML-based)
    - Basic HTML tags: `<p>`, `<h1>`, `<h2>`, `<strong>`, `<em>`, `<ul>`, `<li>`
    - Tables: `<table><tr><td>Cell content</td></tr></table>`
    - Links: `<ac:link><ri:page ri:content-title="Page Title"/></ac:link>`
    
    **Tips:**
    - Always specify space_key (required)
    - Use descriptive, unique titles
    - Add parent_page_id to create hierarchical structure
    - Start with simple HTML, enhance later via Confluence UI
    - Consider page templates for consistent formatting
    
    **Related Tools:**
    - Use `get_confluence_spaces()` to find available space keys before creating
    - Use `search_confluence_pages()` to check if page with similar title already exists
    - Use `get_confluence_page()` to find parent page IDs for hierarchical structure
    - Use `add_page_attachment()` after creation to upload supporting files
    - Use `update_confluence_page()` later to modify the created page
    
    **Workflow Example:**
    1. Get spaces: `get_confluence_spaces({"limit": 50})`
    2. Check existing: `search_confluence_pages({"query": "New Feature", "space_key": "DOCS"})`
    3. Create page: `create_confluence_page({"space_key": "DOCS", "title": "New Feature Guide", "content": "..."})`
    4. Add files: `add_page_attachment({"page_id": "new_page_id", "file_path": "/path/to/diagram.png"})`
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.create_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in create_confluence_page: {str(e)}")
        raise ToolError(f"Failed to create page: {str(e)}")

async def create_confluence_page_direct(
    space_key: str,
    title: str,
    content: str,
    parent_page_id: Optional[str] = None
) -> CreatePageOutput:
    """
    Creates a new page in Confluence with specified content and structure.
    
    **Use Cases:**
    - Create documentation pages
    - Add meeting notes or reports
    - Create child pages under existing pages
    - Generate pages from templates or structured content
    
    **Examples:**
    - Basic page: `{"space_key": "DOCS", "title": "New Feature Guide", "content": "<p>Feature overview...</p>"}`
    - Child page: `{"space_key": "DOCS", "title": "Sub-section", "content": "<p>Details...</p>", "parent_page_id": "123456"}`
    - Rich content page with formatting, tables, and links
    
    **Content Format:**
    - Use Confluence Storage Format (XML-based)
    - Basic HTML tags: `<p>`, `<h1>`, `<h2>`, `<strong>`, `<em>`, `<ul>`, `<li>`
    - Tables: `<table><tr><td>Cell content</td></tr></table>`
    - Links: `<ac:link><ri:page ri:content-title="Page Title"/></ac:link>`
    
    **Tips:**
    - Always specify space_key (required)
    - Use descriptive, unique titles
    - Add parent_page_id to create hierarchical structure
    - Start with simple HTML, enhance later via Confluence UI
    - Consider page templates for consistent formatting
    """
    try:
        # Construct schema object from direct parameters
        inputs = CreatePageInput(
            space_key=space_key,
            title=title,
            content=content,
            parent_page_id=parent_page_id
        )
        async with await get_confluence_client() as client:
            result = await page_actions.create_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in create_confluence_page_direct: {str(e)}")
        raise ToolError(f"Failed to create page: {str(e)}")

async def update_confluence_page(inputs: UpdatePageInput) -> UpdatePageOutput:
    """
    Updates an existing Confluence page's title, content, or position in the page hierarchy.
    
    **Use Cases:**
    - Modify page content or structure
    - Update page titles for better organization
    - Move pages to different parents (restructure hierarchy)
    - Make incremental content updates
    
    **Examples:**
    - Update content: `{"page_id": "123456", "new_version_number": 2, "content": "<p>Updated content...</p>"}`
    - Change title: `{"page_id": "123456", "new_version_number": 2, "title": "New Title"}`
    - Move to different parent: `{"page_id": "123456", "new_version_number": 2, "parent_page_id": "789012"}`
    - Make top-level: `{"page_id": "123456", "new_version_number": 2, "parent_page_id": ""}`
    
    **Version Management:**
    - Always increment version number (get current version first)
    - Confluence tracks all page versions
    - Failed updates often due to incorrect version number
    
    **Tips:**
    - Get current page first to know the version number
    - Use get_confluence_page to see current state before updating
    - You can update multiple fields in one operation
    - Empty parent_page_id makes page top-level in space
    - Preserve existing formatting when updating content
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.update_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in update_confluence_page: {str(e)}")
        raise ToolError(f"Failed to update page: {str(e)}")

async def update_confluence_page_direct(
    page_id: str,
    new_version_number: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    parent_page_id: Optional[str] = None
) -> UpdatePageOutput:
    """
    Updates an existing Confluence page's title, content, or position in the page hierarchy.
    
    **Use Cases:**
    - Modify page content or structure
    - Update page titles for better organization
    - Move pages to different parents (restructure hierarchy)
    - Make incremental content updates
    
    **Examples:**
    - Update content: `{"page_id": "123456", "new_version_number": 2, "content": "<p>Updated content...</p>"}`
    - Change title: `{"page_id": "123456", "new_version_number": 2, "title": "New Title"}`
    - Move to different parent: `{"page_id": "123456", "new_version_number": 2, "parent_page_id": "789012"}`
    - Make top-level: `{"page_id": "123456", "new_version_number": 2, "parent_page_id": ""}`
    
    **Version Management:**
    - Always increment version number (get current version first)
    - Confluence tracks all page versions
    - Failed updates often due to incorrect version number
    
    **Tips:**
    - Get current page first to know the version number
    - Use get_confluence_page to see current state before updating
    - You can update multiple fields in one operation
    - Empty parent_page_id makes page top-level in space
    - Preserve existing formatting when updating content
    """
    try:
        # Construct schema object from direct parameters
        inputs = UpdatePageInput(
            page_id=page_id,
            new_version_number=new_version_number,
            title=title,
            content=content,
            parent_page_id=parent_page_id
        )
        async with await get_confluence_client() as client:
            result = await page_actions.update_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in update_confluence_page_direct: {str(e)}")
        raise ToolError(f"Failed to update page: {str(e)}")

async def delete_confluence_page(inputs: DeletePageInput) -> DeletePageOutput:
    """
    Permanently moves a Confluence page to trash (soft delete).
    
    **Use Cases:**
    - Remove outdated or incorrect pages
    - Clean up draft pages that are no longer needed
    - Archive pages that shouldn't be visible anymore
    - Free up space organization
    
    **Examples:**
    - Delete page: `{"page_id": "123456"}`
    
    **Important Notes:**
    - Pages are moved to trash, not permanently deleted
    - Deleted pages can be restored from trash by admins
    - Child pages may also be affected (check Confluence behavior)
    - Consider the impact on page links and references
    
    **Tips:**
    - Get page information first to confirm you're deleting the right page
    - Check for child pages that might be affected
    - Consider updating links that point to the page being deleted
    - Notify users if the page was widely referenced
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.delete_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in delete_confluence_page: {str(e)}")
        raise ToolError(f"Failed to delete page: {str(e)}")

async def delete_confluence_page_direct(page_id: str) -> DeletePageOutput:
    """
    Permanently moves a Confluence page to trash (soft delete).
    
    **Use Cases:**
    - Remove outdated or incorrect pages
    - Clean up draft pages that are no longer needed
    - Archive pages that shouldn't be visible anymore
    - Free up space organization
    
    **Examples:**
    - Delete page: `{"page_id": "123456"}`
    
    **Important Notes:**
    - Pages are moved to trash, not permanently deleted
    - Deleted pages can be restored from trash by admins
    - Child pages may also be affected (check Confluence behavior)
    - Consider the impact on page links and references
    
    **Tips:**
    - Get page information first to confirm you're deleting the right page
    - Check for child pages that might be affected
    - Consider updating links that point to the page being deleted
    - Notify users if the page was widely referenced
    """
    try:
        # Construct schema object from direct parameters
        inputs = DeletePageInput(page_id=page_id)
        async with await get_confluence_client() as client:
            result = await page_actions.delete_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in delete_confluence_page_direct: {str(e)}")
        raise ToolError(f"Failed to delete page: {str(e)}")

async def get_confluence_spaces(inputs: GetSpacesInput) -> GetSpacesOutput:
    """
    Retrieves a list of Confluence spaces that the user has access to.
    
    **Use Cases:**
    - Discover available spaces for content creation
    - Get space keys for page operations
    - Browse space structure and organization
    - Verify access permissions to spaces
    
    **Examples:**
    - Get all spaces: `{"limit": 50}`
    - Get spaces with pagination: `{"limit": 25, "start": 25}`
    
    **Space Information:**
    - Space key: Short identifier (e.g., "DOCS", "TECH")
    - Space name: Full display name
    - Space type: global, personal, etc.
    - Access URL for space homepage
    
    **Tips:**
    - Use space keys in page creation and search operations
    - Space keys are required for creating pages
    - Personal spaces usually have keys like "~username"
    - Global spaces are shared across the organization
    """
    try:
        async with await get_confluence_client() as client:
            result = await space_actions.get_spaces_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_confluence_spaces: {str(e)}")
        raise ToolError(f"Failed to get spaces: {str(e)}")

async def get_confluence_spaces_direct(
    limit: int = 25,
    start: int = 0
) -> GetSpacesOutput:
    """
    Retrieves a list of Confluence spaces that the user has access to.
    
    **Use Cases:**
    - Discover available spaces for content creation
    - Get space keys for page operations
    - Browse space structure and organization
    - Verify access permissions to spaces
    
    **Examples:**
    - Get all spaces: `{"limit": 50}`
    - Get spaces with pagination: `{"limit": 25, "start": 25}`
    
    **Space Information:**
    - Space key: Short identifier (e.g., "DOCS", "TECH")
    - Space name: Full display name
    - Space type: global, personal, etc.
    - Access URL for space homepage
    
    **Tips:**
    - Use space keys in page creation and search operations
    - Space keys are required for creating pages
    - Personal spaces usually have keys like "~username"
    - Global spaces are shared across the organization
    """
    try:
        async with await get_confluence_client() as client:
            result = await space_actions.get_spaces_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_confluence_spaces_direct: {str(e)}")
        raise ToolError(f"Failed to get spaces: {str(e)}")

async def get_page_attachments(inputs: GetAttachmentsInput) -> GetAttachmentsOutput:
    """
    Retrieves a list of attachments from a specific Confluence page.
    
    **Use Cases:**
    - List all files attached to a page
    - Find specific attachments by name or type
    - Get attachment metadata (size, type, upload date)
    - Download or reference files from pages
    
    **Examples:**
    - Get all attachments: `{"page_id": "123456"}`
    - Search for specific file: `{"page_id": "123456", "filename": "diagram.png"}`
    - Filter by file type: `{"page_id": "123456", "media_type": "image/png"}`
    - Get with pagination: `{"page_id": "123456", "limit": 25, "start": 25}`
    
    **Attachment Information:**
    - Filename and file extension
    - File size and media type
    - Upload date and author
    - Download URL for file access
    
    **Tips:**
    - Use filename parameter for exact filename searches
    - Use media_type to filter by file type (image/*, application/pdf, etc.)
    - Large pages may have many attachments - use pagination
    - Download URLs are temporary and should be used promptly
    """
    try:
        async with await get_confluence_client() as client:
            result = await attachment_actions.get_attachments_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_page_attachments: {str(e)}")
        raise ToolError(f"Failed to get attachments: {str(e)}")

async def get_page_attachments_direct(
    page_id: str,
    limit: int = 50,
    start: int = 0,
    filename: Optional[str] = None,
    media_type: Optional[str] = None
) -> GetAttachmentsOutput:
    """
    Retrieves a list of attachments from a specific Confluence page.
    
    **Use Cases:**
    - List all files attached to a page
    - Find specific attachments by name or type
    - Get attachment metadata (size, type, upload date)
    - Download or reference files from pages
    
    **Examples:**
    - Get all attachments: `{"page_id": "123456"}`
    - Search for specific file: `{"page_id": "123456", "filename": "diagram.png"}`
    - Filter by file type: `{"page_id": "123456", "media_type": "image/png"}`
    - Get with pagination: `{"page_id": "123456", "limit": 25, "start": 25}`
    
    **Attachment Information:**
    - Filename and file extension
    - File size and media type
    - Upload date and author
    - Download URL for file access
    
    **Tips:**
    - Use filename parameter for exact filename searches
    - Use media_type to filter by file type (image/*, application/pdf, etc.)
    - Large pages may have many attachments - use pagination
    - Download URLs are temporary and should be used promptly
    """
    try:
        # Construct schema object from direct parameters
        inputs = GetAttachmentsInput(
            page_id=page_id,
            limit=limit,
            start=start,
            filename=filename,
            media_type=media_type
        )
        async with await get_confluence_client() as client:
            result = await attachment_actions.get_attachments_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_page_attachments_direct: {str(e)}")
        raise ToolError(f"Failed to get attachments: {str(e)}")

async def add_page_attachment(inputs: AddAttachmentInput) -> AddAttachmentOutput:
    """
    Uploads a file as an attachment to a specific Confluence page.
    
    **Use Cases:**
    - Add supporting documents to pages
    - Upload images for page content
    - Attach spreadsheets, PDFs, or other files
    - Share files with page viewers
    
    **Examples:**
    - Upload file: `{"page_id": "123456", "file_path": "/path/to/document.pdf"}`
    - Custom filename: `{"page_id": "123456", "file_path": "/path/to/file.txt", "filename_on_confluence": "report.txt"}`
    - With comment: `{"page_id": "123456", "file_path": "/path/to/image.png", "comment": "Updated diagram"}`
    
    **File Requirements:**
    - File must exist and be readable
    - Check Confluence file size limits (usually 50MB-100MB)
    - Supported file types vary by Confluence configuration
    - Binary files (images, PDFs) and text files both supported
    
    **Tips:**
    - Use descriptive filenames for better organization
    - Add comments to explain file purpose or version
    - Check existing attachments first to avoid duplicates
    - Some file types may be restricted by admin policies
    """
    try:
        async with await get_confluence_client() as client:
            result = await attachment_actions.add_attachment_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in add_page_attachment: {str(e)}")
        raise ToolError(f"Failed to add attachment: {str(e)}")

async def add_page_attachment_direct(
    page_id: str,
    file_path: str,
    filename_on_confluence: Optional[str] = None,
    comment: Optional[str] = None
) -> AddAttachmentOutput:
    """
    Uploads a file as an attachment to a specific Confluence page.
    
    **Use Cases:**
    - Add supporting documents to pages
    - Upload images for page content
    - Attach spreadsheets, PDFs, or other files
    - Share files with page viewers
    
    **Examples:**
    - Upload file: `{"page_id": "123456", "file_path": "/path/to/document.pdf"}`
    - Custom filename: `{"page_id": "123456", "file_path": "/path/to/file.txt", "filename_on_confluence": "report.txt"}`
    - With comment: `{"page_id": "123456", "file_path": "/path/to/image.png", "comment": "Updated diagram"}`
    
    **File Requirements:**
    - File must exist and be readable
    - Check Confluence file size limits (usually 50MB-100MB)
    - Supported file types vary by Confluence configuration
    - Binary files (images, PDFs) and text files both supported
    
    **Tips:**
    - Use descriptive filenames for better organization
    - Add comments to explain file purpose or version
    - Check existing attachments first to avoid duplicates
    - Some file types may be restricted by admin policies
    """
    try:
        # Construct schema object from direct parameters
        inputs = AddAttachmentInput(
            page_id=page_id,
            file_path=file_path,
            filename_on_confluence=filename_on_confluence,
            comment=comment
        )
        async with await get_confluence_client() as client:
            result = await attachment_actions.add_attachment_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in add_page_attachment_direct: {str(e)}")
        raise ToolError(f"Failed to add attachment: {str(e)}")

async def delete_page_attachment(inputs: DeleteAttachmentInput) -> DeleteAttachmentOutput:
    """
    Permanently deletes an attachment from a Confluence page.
    
    **Use Cases:**
    - Remove outdated or incorrect files
    - Clean up duplicate attachments
    - Free up storage space
    - Remove sensitive files
    
    **Examples:**
    - Delete attachment: `{"attachment_id": "att123456"}`
    
    **Important Notes:**
    - Attachment deletion is permanent (cannot be undone)
    - Get attachment ID from get_page_attachments first
    - Deleting attachments may break page content that references them
    - Consider the impact on users who might be downloading the file
    
    **Tips:**
    - List attachments first to get the correct attachment ID
    - Verify you're deleting the right file before proceeding
    - Check if the attachment is referenced in page content
    - Consider notifying users if the file was widely used
    """
    try:
        async with await get_confluence_client() as client:
            result = await attachment_actions.delete_attachment_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in delete_page_attachment: {str(e)}")
        raise ToolError(f"Failed to delete attachment: {str(e)}")

async def delete_page_attachment_direct(attachment_id: str) -> DeleteAttachmentOutput:
    """
    Permanently deletes an attachment from a Confluence page.
    
    **Use Cases:**
    - Remove outdated or incorrect files
    - Clean up duplicate attachments
    - Free up storage space
    - Remove sensitive files
    
    **Examples:**
    - Delete attachment: `{"attachment_id": "att123456"}`
    
    **Important Notes:**
    - Attachment deletion is permanent (cannot be undone)
    - Get attachment ID from get_page_attachments first
    - Deleting attachments may break page content that references them
    - Consider the impact on users who might be downloading the file
    
    **Tips:**
    - List attachments first to get the correct attachment ID
    - Verify you're deleting the right file before proceeding
    - Check if the attachment is referenced in page content
    - Consider notifying users if the file was widely used
    """
    try:
        # Construct schema object from direct parameters
        inputs = DeleteAttachmentInput(attachment_id=attachment_id)
        async with await get_confluence_client() as client:
            result = await attachment_actions.delete_attachment_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in delete_page_attachment_direct: {str(e)}")
        raise ToolError(f"Failed to delete attachment: {str(e)}")

async def get_page_comments(inputs: GetCommentsInput) -> GetCommentsOutput:
    """
    Retrieves comments and discussions from a specific Confluence page.
    
    **Use Cases:**
    - Read feedback and discussions on pages
    - Get comment metadata (author, date, replies)
    - Monitor page engagement and collaboration
    - Export comments for reporting or analysis
    
    **Examples:**
    - Get all comments: `{"page_id": "123456"}`
    - Get with pagination: `{"page_id": "123456", "limit": 25, "start": 25}`
    - Get expanded details: `{"page_id": "123456", "expand": "body.view,version"}`
    
    **Comment Information:**
    - Comment content and formatting
    - Author name and profile
    - Creation and modification dates
    - Comment hierarchy (replies to comments)
    
    **Tips:**
    - Use expand parameter to get comment content
    - Comments are paginated - use start/limit for large discussions
    - Comment hierarchy shows reply relationships
    - Some comments may be restricted based on permissions
    """
    try:
        async with await get_confluence_client() as client:
            result = await comment_actions.get_comments_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_page_comments: {str(e)}")
        raise ToolError(f"Failed to get comments: {str(e)}")

async def get_page_comments_direct(
    page_id: str,
    limit: int = 25,
    start: int = 0,
    expand: Optional[str] = None
) -> GetCommentsOutput:
    """
    Retrieves comments and discussions from a specific Confluence page.
    
    **Use Cases:**
    - Read feedback and discussions on pages
    - Get comment metadata (author, date, replies)
    - Monitor page engagement and collaboration
    - Export comments for reporting or analysis
    
    **Examples:**
    - Get all comments: `{"page_id": "123456"}`
    - Get with pagination: `{"page_id": "123456", "limit": 25, "start": 25}`
    - Get expanded details: `{"page_id": "123456", "expand": "body.view,version"}`
    
    **Comment Information:**
    - Comment content and formatting
    - Author name and profile
    - Creation and modification dates
    - Comment hierarchy (replies to comments)
    
    **Tips:**
    - Use expand parameter to get comment content
    - Comments are paginated - use start/limit for large discussions
    - Comment hierarchy shows reply relationships
    - Some comments may be restricted based on permissions
    """
    try:
        # Construct schema object from direct parameters
        inputs = GetCommentsInput(
            page_id=page_id,
            limit=limit,
            start=start,
            expand=expand
        )
        async with await get_confluence_client() as client:
            result = await comment_actions.get_comments_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_page_comments_direct: {str(e)}")
        raise ToolError(f"Failed to get comments: {str(e)}")

# --- Conditional Tool Registration ---
def register_schema_tools():
    """Register schema-based tools (legacy format with inputs wrapper)."""
    logger.info("TOOL_REGISTRATION: Registering schema-based tools (legacy format)")
    
    # Register all schema-based tool functions
    mcp_server.tool()(get_confluence_page)
    mcp_server.tool()(search_confluence_pages)
    mcp_server.tool()(create_confluence_page)
    mcp_server.tool()(update_confluence_page)
    mcp_server.tool()(delete_confluence_page)
    mcp_server.tool()(get_confluence_spaces)
    mcp_server.tool()(get_page_attachments)
    mcp_server.tool()(add_page_attachment)
    mcp_server.tool()(delete_page_attachment)
    mcp_server.tool()(get_page_comments)
    
    logger.info("TOOL_REGISTRATION: Registered 10 schema-based tools")

def register_direct_tools():
    """Register direct parameter tools (modern format)."""
    logger.info("TOOL_REGISTRATION: Registering direct parameter tools (modern format)")
    
    # Register all direct parameter tool functions with clean names
    # The _direct functions will be registered with the standard names
    mcp_server.tool(name="get_confluence_page")(get_confluence_page_direct)
    mcp_server.tool(name="search_confluence_pages")(search_confluence_pages_direct)
    mcp_server.tool(name="create_confluence_page")(create_confluence_page_direct)
    mcp_server.tool(name="update_confluence_page")(update_confluence_page_direct)
    mcp_server.tool(name="delete_confluence_page")(delete_confluence_page_direct)
    mcp_server.tool(name="get_confluence_spaces")(get_confluence_spaces_direct)
    mcp_server.tool(name="get_page_attachments")(get_page_attachments_direct)
    mcp_server.tool(name="add_page_attachment")(add_page_attachment_direct)
    mcp_server.tool(name="delete_page_attachment")(delete_page_attachment_direct)
    mcp_server.tool(name="get_page_comments")(get_page_comments_direct)
    
    logger.info("TOOL_REGISTRATION: Registered 10 direct parameter tools")

def register_tools_conditionally():
    """Register tools based on detected calling convention."""
    global TOOL_CONVENTION
    
    logger.info(f"TOOL_REGISTRATION: Using '{TOOL_CONVENTION}' convention")
    
    if TOOL_CONVENTION == 'direct':
        register_direct_tools()
    else:  # 'schema' or any other value defaults to schema
        register_schema_tools()
    
    logger.info("TOOL_REGISTRATION: Conditional tool registration complete")

# Register tools immediately when module is imported (for test compatibility)
register_tools_conditionally()

# --- Main Functions ---
def main():
    """Main function for stdio transport mode."""
    try:
        # Environment setup (convert to sync)
        import asyncio
        asyncio.run(setup_environment())
        
        # Register tools based on detected calling convention
        register_tools_conditionally()
        
        # Start the MCP server using stdio transport
        # Use synchronous run() method
        mcp_server.run()
        
    except Exception as e:
        logger.critical(f"Critical error starting stdio server: {str(e)}")
        raise


async def setup_environment():
    """Setup environment variables and logging for the server."""
    # Load environment variables from .env file with explicit path
    from pathlib import Path
    
    # STEP 1: Try to detect and apply Smithery.ai configuration first
    # This must happen before checking existing environment variables
    smithery_config = detect_and_apply_smithery_config()
    if smithery_config:
        logger.info(f"SMITHERY_CONFIG: Applied configuration for: {list(smithery_config.keys())}")
    
    # STEP 2: Environment variable loading strategy:
    # 1. Check if already set (e.g., from Claude Desktop config or Smithery config above)
    # 2. Try loading from .env file in multiple locations
    # 3. Fallback to default load_dotenv() behavior
    required_env_vars = ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN"]
    already_set = all(os.getenv(var) for var in required_env_vars)
    
    if already_set:
        config_source = "Smithery configuration" if smithery_config else "Claude Desktop config or existing environment"
        logger.info(f"Environment variables already set (likely from {config_source})")
    else:
        # Try to load from .env file if environment variables aren't already set
        logger.info("Environment variables not set, attempting to load from .env file")
        
        # Try multiple possible locations for .env file
        # This handles different execution contexts (direct run vs module run)
        env_locations = [
            # Current directory (when run from project root)
            Path.cwd() / ".env",
            # Parent of main.py file (project root)  
            Path(__file__).parent.parent / ".env",
            # Absolute path based on current working directory
            Path.cwd().resolve() / ".env",
        ]
        
        env_loaded = False
        for env_path in env_locations:
            try:
                # Force load without checking existence (file might be hidden by IDE)
                result = load_dotenv(env_path)
                if result:  # load_dotenv returns True if file was loaded
                    logger.info(f"Successfully loaded environment from: {env_path}")
                    env_loaded = True
                    break
                else:
                    logger.debug(f"Tried to load from {env_path} but got False result")
            except Exception as e:
                logger.debug(f"Failed to load env from {env_path}: {e}")
                continue
        
        if not env_loaded:
            # Final fallback - try load_dotenv() without path
            # This lets python-dotenv search in its default locations
            load_dotenv()
            logger.info("Using fallback load_dotenv() without explicit path")
    
    # Setup logging configuration (file-based to avoid stdout interference)
    # CRITICAL: All logging must go to files, not stdout/stderr
    # Stdout interference breaks JSON-RPC protocol used by Claude Desktop
    try:
        setup_logging()
    except:
        # Fail silently - don't interfere with MCP protocol
        pass

    # Validate environment variables are now available
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        # Log but don't print to stderr (would interfere with MCP protocol)
        logger.critical(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.critical(f"Tried env file locations: {[str(p) for p in env_locations] if 'env_locations' in locals() else 'None'}")
        # Only raise error if we're sure the env vars should be available
        # When run from Claude Desktop, they should be set via env config
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Log successful environment loading for debugging
    logger.info(f"Environment variables loaded successfully")
    logger.info(f"CONFLUENCE_URL: {os.getenv('CONFLUENCE_URL')}")
    logger.info(f"CONFLUENCE_USERNAME: {os.getenv('CONFLUENCE_USERNAME')}")
    
    # 🔒 SECURITY: Never log API tokens - only confirm they exist
    api_token = os.getenv("CONFLUENCE_API_TOKEN")
    if api_token:
        logger.info("CONFLUENCE_API_TOKEN: ******* (loaded successfully)")
    else:
        logger.error("CONFLUENCE_API_TOKEN: Not found in environment variables")
        

# --- Main Execution Block ---
if __name__ == "__main__":
    try:
        # Run the main function (now synchronous)
        main()
        
    except Exception as e:
        # Log error but don't print to stderr to avoid interfering with MCP protocol
        # All error output must go to log files only
        logger.critical(f"Critical error starting server: {str(e)}")
        exit(1)
