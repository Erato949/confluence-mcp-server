# confluence_mcp_server/main.py (CLEAN VERSION - NO STDOUT/STDERR INTERFERENCE)
# Standard Library Imports
import asyncio
import os
import logging

# Third-Party Imports
from dotenv import load_dotenv
import httpx # For making HTTP requests to Confluence API
from fastmcp import FastMCP # Corrected import for FastMCP
from fastmcp.exceptions import McpError # Corrected to McpError (lowercase 'c')
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

# --- FastMCP Server Instance ---
# Create the FastMCP server instance here so it can be used by tool decorators
mcp_server = FastMCP(
    name="ConfluenceMCPServer"
)

# --- Authentication Functions ---
async def get_confluence_client() -> httpx.AsyncClient:
    """
    Creates an authenticated httpx client for Confluence API requests.
    
    Returns:
        httpx.AsyncClient: An authenticated client configured for Confluence API
        
    Raises:
        McpError: If authentication credentials are missing or invalid
    """
    confluence_url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME") 
    api_token = os.getenv("CONFLUENCE_API_TOKEN")
    
    if not all([confluence_url, username, api_token]):
        raise McpError("Missing Confluence credentials in environment variables")
    
    # Remove trailing slash if present
    base_url = confluence_url.rstrip('/')
    
    # Create the authenticated client
    client = httpx.AsyncClient(
        base_url=base_url,
        auth=(username, api_token),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        timeout=30.0
    )
    
    return client

# --- MCP Tool Definitions ---

@mcp_server.tool()
async def get_confluence_page(inputs: GetPageInput) -> PageOutput:
    """
    Retrieves a specific Confluence page with its content and metadata.
    
    **Use Cases:**
    - Get page content to read or analyze
    - Retrieve page metadata (author, version, dates)
    - Get page structure information (parent, space)
    
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
        raise McpError(f"Failed to retrieve page: {str(e)}")

@mcp_server.tool()
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
        raise McpError(f"Failed to search pages: {str(e)}")

@mcp_server.tool()
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
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.create_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in create_confluence_page: {str(e)}")
        raise McpError(f"Failed to create page: {str(e)}")

@mcp_server.tool()
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
        raise McpError(f"Failed to update page: {str(e)}")

@mcp_server.tool()
async def delete_confluence_page(inputs: DeletePageInput) -> DeletePageOutput:
    """
    Deletes a Confluence page by moving it to trash (not permanent deletion).
    
    **Use Cases:**
    - Remove outdated or incorrect pages
    - Clean up test or draft pages
    - Remove duplicate content
    - Archive pages that are no longer relevant
    
    **Examples:**
    - Delete a page: `{"page_id": "123456"}`
    
    **Important Notes:**
    - Pages are moved to trash, not permanently deleted
    - Pages can be restored from trash via Confluence UI
    - Deleting parent pages may affect child page hierarchy
    - Consider updating content instead of deleting when possible
    
    **Tips:**
    - Use search_confluence_pages first to confirm you have the right page
    - Consider the impact on child pages and page links
    - Deleted pages can still be referenced but won't be accessible
    - For permanent deletion, use Confluence admin interface
    """
    try:
        async with await get_confluence_client() as client:
            result = await page_actions.delete_page_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in delete_confluence_page: {str(e)}")
        raise McpError(f"Failed to delete page: {str(e)}")

@mcp_server.tool()
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
        raise McpError(f"Failed to retrieve spaces: {str(e)}")

@mcp_server.tool()
async def get_page_attachments(inputs: GetAttachmentsInput) -> GetAttachmentsOutput:
    """
    Retrieves all attachments associated with a specific Confluence page.
    
    **Use Cases:**
    - List files attached to a page
    - Get attachment metadata (size, type, version)
    - Find specific attachments by filename
    - Download attachment information for processing
    
    **Examples:**
    - Get all attachments: `{"page_id": "123456"}`
    - Find specific file: `{"page_id": "123456", "filename": "document.pdf"}`
    - Get attachments with pagination: `{"page_id": "123456", "limit": 10, "start": 10}`
    
    **Attachment Information:**
    - Filename and media type
    - File size in bytes
    - Upload date and author
    - Version number
    - Download and web UI links
    
    **Tips:**
    - Use filename filter to find specific attachments
    - Check file size before downloading large attachments
    - Attachment links may need base URL prepended
    - Multiple versions of the same file are tracked
    """
    try:
        async with await get_confluence_client() as client:
            result = await attachment_actions.get_attachments_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_page_attachments: {str(e)}")
        raise McpError(f"Failed to retrieve attachments: {str(e)}")

@mcp_server.tool()
async def add_page_attachment(inputs: AddAttachmentInput) -> AddAttachmentOutput:
    """
    Uploads a file as an attachment to a specific Confluence page.
    
    **Use Cases:**
    - Add documents, images, or files to pages
    - Upload supporting materials for documentation
    - Attach reference files or resources
    - Create new versions of existing attachments
    
    **Examples:**
    - Upload file: `{"page_id": "123456", "file_path": "/path/to/document.pdf"}`
    - Upload with custom name: `{"page_id": "123456", "file_path": "/path/to/file.txt", "filename_on_confluence": "Requirements.txt"}`
    - Upload with comment: `{"page_id": "123456", "file_path": "/path/to/image.png", "comment": "Updated screenshot"}`
    
    **File Requirements:**
    - File must be accessible to the server process
    - File path should be absolute for reliability
    - Confluence may have file size and type restrictions
    - Uploading same filename creates new version
    
    **Tips:**
    - Verify file exists and is readable before upload
    - Use descriptive filenames for better organization
    - Consider file size limits (varies by Confluence instance)
    - Add meaningful comments for version tracking
    """
    try:
        async with await get_confluence_client() as client:
            result = await attachment_actions.add_attachment_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in add_page_attachment: {str(e)}")
        raise McpError(f"Failed to add attachment: {str(e)}")

@mcp_server.tool()
async def delete_page_attachment(inputs: DeleteAttachmentInput) -> DeleteAttachmentOutput:
    """
    Permanently deletes an attachment from a Confluence page.
    
    **Use Cases:**
    - Remove outdated or incorrect files
    - Clean up unnecessary attachments
    - Delete sensitive files that were uploaded by mistake
    - Free up storage space
    
    **Examples:**
    - Delete attachment: `{"attachment_id": "att123456"}`
    
    **Important Notes:**
    - Deletion is permanent and cannot be undone
    - Get attachment ID using get_page_attachments first
    - Deleting attachments may break links in page content
    - Consider the impact on page references
    
    **Tips:**
    - Use get_page_attachments to find the attachment ID
    - Verify you're deleting the correct attachment
    - Check if attachment is referenced in page content
    - Consider updating page content that references deleted files
    """
    try:
        async with await get_confluence_client() as client:
            result = await attachment_actions.delete_attachment_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in delete_page_attachment: {str(e)}")
        raise McpError(f"Failed to delete attachment: {str(e)}")

@mcp_server.tool()
async def get_page_comments(inputs: GetCommentsInput) -> GetCommentsOutput:
    """
    Retrieves all comments associated with a specific Confluence page.
    
    **Use Cases:**
    - Read feedback and discussions on pages
    - Get comment metadata (author, dates)
    - Analyze page engagement and collaboration
    - Extract comment threads and replies
    
    **Examples:**
    - Get all comments: `{"page_id": "123456"}`
    - Get comments with pagination: `{"page_id": "123456", "limit": 10, "start": 10}`
    - Get comments with history: `{"page_id": "123456", "expand": "history"}`
    
    **Comment Information:**
    - Comment content and author
    - Creation and update timestamps
    - Comment hierarchy (replies to other comments)
    - Direct links to comments
    
    **Comment Structure:**
    - Top-level comments have no parent
    - Reply comments reference parent_comment_id
    - Comments may be in storage or view format
    - Author information includes display name
    
    **Tips:**
    - Use expand parameter to get additional comment details
    - Check parent_comment_id to understand comment hierarchy
    - Comments are ordered chronologically by default
    - Use pagination for pages with many comments
    """
    try:
        async with await get_confluence_client() as client:
            result = await comment_actions.get_comments_logic(client, inputs)
            return result
    except Exception as e:
        logger.error(f"Error in get_page_comments: {str(e)}")
        raise McpError(f"Failed to retrieve comments: {str(e)}")

# --- Main Execution Block ---
if __name__ == "__main__":
    try:
        # Load environment variables from .env file with explicit path
        import sys
        from pathlib import Path
        
        # First check if environment variables are already set (e.g., from Claude Desktop)
        required_env_vars = ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN"]
        already_set = all(os.getenv(var) for var in required_env_vars)
        
        if already_set:
            logger.info("Environment variables already set (likely from Claude Desktop config)")
        else:
            # Try to load from .env file if environment variables aren't already set
            logger.info("Environment variables not set, attempting to load from .env file")
            
            # Try multiple possible locations for .env file
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
                    # Force load without checking existence (file might be hidden)
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
                load_dotenv()
                logger.info("Using fallback load_dotenv() without explicit path")
        
        # Setup logging configuration (to file, not stderr)
        try:
            setup_logging()
        except:
            # Fail silently - don't interfere with MCP protocol
            pass

        # Validate environment variables are now available
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            # Log but don't print to stderr
            logger.critical(f"Missing required environment variables: {', '.join(missing_vars)}")
            if not already_set:
                logger.critical(f"Tried env file locations: {[str(p) for p in env_locations] if 'env_locations' in locals() else 'None'}")
            exit(1)
        
        # Log successful environment loading
        logger.info(f"Environment variables loaded successfully")
        logger.info(f"CONFLUENCE_URL: {os.getenv('CONFLUENCE_URL')}")
        logger.info(f"CONFLUENCE_USERNAME: {os.getenv('CONFLUENCE_USERNAME')}")
        
        # Start the MCP server (pure stdio, no extra output)
        mcp_server.run()
        
    except Exception as e:
        # Log error but don't print to stderr to avoid interfering with MCP protocol
        logger.critical(f"Critical error starting server: {str(e)}")
        exit(1)
