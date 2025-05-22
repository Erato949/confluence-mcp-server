# confluence_mcp_server/main.py (NEW - REPLACE ENTIRE FILE)
# Standard Library Imports
import asyncio
import os
import logging

# Third-Party Imports
from dotenv import load_dotenv
import httpx # For making HTTP requests to Confluence API
from fastmcp import FastMCP, Context # Corrected import for FastMCP
from fastmcp.exceptions import McpError # Corrected to McpError (lowercase 'c')
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

# Local Application/Library Specific Imports
from confluence_mcp_server.utils.logging_config import setup_logging
from .mcp_actions import page_actions, space_actions, attachment_actions, comment_actions # Assuming these exist
from .mcp_actions.schemas import (
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

# Initialize logging
logger = logging.getLogger(__name__)

# --- FastMCP Server Instance ---
# Create the FastMCP server instance here so it can be used by tool decorators
mcp_server = FastMCP(
    name="ConfluenceMCPServer",
    description="An MCP server for interacting with Confluence Cloud API."
    # dependencies=[] # Add if any server-level dependencies are needed
)

# --- Confluence Client Setup ---
def get_confluence_client() -> httpx.AsyncClient:
    """
    Creates and configures an httpx.AsyncClient for interacting with the Confluence API.
    Reads configuration from environment variables.
    """
    confluence_url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    api_token = os.getenv("CONFLUENCE_API_TOKEN")

    if not all([confluence_url, username, api_token]):
        logger.error("Confluence API credentials or URL are not fully configured in .env file.")
        raise McpError(code=-32000, message="Server configuration error: Confluence credentials missing.")

    if not confluence_url.endswith('/'):
        confluence_url += '/'
    
    auth = httpx.BasicAuth(username, api_token)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    return httpx.AsyncClient(base_url=confluence_url, auth=auth, headers=headers)

# --- Tool Definitions ---

@mcp_server.tool()
async def get_confluence_page(inputs: GetPageInput, context: Context) -> PageOutput:
    """Retrieves a specific page from Confluence by its ID."""
    logger.info(f"Executing get_confluence_page tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await page_actions.get_page_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in get_confluence_page: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in get_confluence_page: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def search_confluence_pages(inputs: SearchPagesInput, context: Context) -> SearchPagesOutput:
    """Searches for pages in Confluence based on CQL query."""
    logger.info(f"Executing search_confluence_pages tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await page_actions.search_pages_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in search_confluence_pages: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in search_confluence_pages: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def create_confluence_page(inputs: CreatePageInput, context: Context) -> CreatePageOutput:
    """Creates a new page in Confluence."""
    logger.info(f"Executing create_confluence_page tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await page_actions.create_page_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in create_confluence_page: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in create_confluence_page: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def update_confluence_page(inputs: UpdatePageInput, context: Context) -> UpdatePageOutput:
    """Updates an existing page in Confluence."""
    logger.info(f"Executing update_confluence_page tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await page_actions.update_page_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in update_confluence_page: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in update_confluence_page: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def delete_confluence_page(inputs: DeletePageInput, context: Context) -> DeletePageOutput:
    """Deletes a page from Confluence by its ID."""
    logger.info(f"Executing delete_confluence_page tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await page_actions.delete_page_logic(client, inputs) # Removed context
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in delete_confluence_page: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        # McpError does not take 'code'. It takes 'message' and optionally 'data'.
        # We can pass the structured errors in 'data' if needed, or just a message.
        raise McpError(msg=f"Invalid parameters: {error_details}", data=ve.errors())
    except HTTPException as http_exc: # More specific handling for HTTPExceptions from logic layer
        logger.error(f"HTTPException in delete_confluence_page: {http_exc.status_code} - {http_exc.detail}", exc_info=True)
        raise McpError(msg=f"Confluence API error: {http_exc.detail}")
    except Exception as e:
        logger.error(f"Unexpected error in delete_confluence_page: {e}", exc_info=True)
        # McpError does not take 'code'.
        raise McpError(msg=f"Tool execution error: {str(e)}")

@mcp_server.tool()
async def get_confluence_spaces(inputs: GetSpacesInput, context: Context) -> GetSpacesOutput:
    """Retrieves a list of spaces from Confluence."""
    logger.info(f"Executing get_confluence_spaces tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await space_actions.get_spaces_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in get_confluence_spaces: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in get_confluence_spaces: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def get_page_attachments(inputs: GetAttachmentsInput, context: Context) -> GetAttachmentsOutput:
    """Retrieves attachments for a specific Confluence page."""
    logger.info(f"Executing get_page_attachments tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await attachment_actions.get_attachments_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in get_page_attachments: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in get_page_attachments: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def add_page_attachment(inputs: AddAttachmentInput, context: Context) -> AddAttachmentOutput:
    """Adds an attachment to a specific Confluence page."""
    logger.info(f"Executing add_page_attachment tool with inputs: {{page_id: {inputs.page_id}, filename: {inputs.filename}, media_type: {inputs.media_type}, comment: {inputs.comment}, content_length: {inputs.content_length}}}") # Avoid logging potentially large content
    try:
        async with get_confluence_client() as client:
            return await attachment_actions.add_attachment_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in add_page_attachment: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in add_page_attachment: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def delete_page_attachment(inputs: DeleteAttachmentInput, context: Context) -> DeleteAttachmentOutput:
    """Deletes an attachment from a Confluence page."""
    logger.info(f"Executing delete_page_attachment tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await attachment_actions.delete_attachment_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in delete_page_attachment: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in delete_page_attachment: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

@mcp_server.tool()
async def get_page_comments(inputs: GetCommentsInput, context: Context) -> GetCommentsOutput:
    """Retrieves comments for a specific Confluence page."""
    logger.info(f"Executing get_page_comments tool with inputs: {inputs}")
    try:
        async with get_confluence_client() as client:
            return await comment_actions.get_comments_logic(client, inputs, context)
    except McpError:
        raise
    except ValidationError as ve:
        logger.error(f"Input validation error in get_page_comments: {ve.errors()}", exc_info=True)
        error_details = ", ".join([f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()])
        raise McpError(code=-32602, message=f"Invalid parameters: {error_details}")
    except Exception as e:
        logger.error(f"Unexpected error in get_page_comments: {e}", exc_info=True)
        raise McpError(code=-32000, message=f"Tool execution error: {e}")

# --- MCP Server Setup ---
def create_mcp_server() -> FastMCP:
    """
    Returns the globally configured FastMCP server instance.
    Tools are registered via decorators on the global 'mcp_server' instance.
    """
    logger.info("Returning pre-configured FastMCP server instance.")
    # The mcp_server instance is already created and tools are registered on it via @mcp_server.tool()
    return mcp_server

# --- Main Execution Block ---
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    # Setup logging configuration
    setup_logging()

    logger.info("Starting Confluence MCP Server...")

    mcp_port = int(os.getenv("MCP_PORT", "8077"))
    mcp_host = os.getenv("MCP_HOST", "0.0.0.0")

    try:
        # The mcp_server instance is now created globally and configured with tools.
        # create_mcp_server() simply returns this instance.
        server_to_run = create_mcp_server()
        logger.info(f"FastMCP server retrieved. Attempting to serve on {mcp_host}:{mcp_port}")
        
        asyncio.run(server_to_run.serve(host=mcp_host, port=mcp_port))
        
    except McpError as e:
        logger.critical(f"Failed to start MCP server due to McpError: {e.message} (Code: {e.code})", exc_info=True)
    except Exception as e:
        logger.critical(f"An unexpected error occurred while trying to start or run the MCP server: {e}", exc_info=True)
    finally:
        logger.info("Confluence MCP Server has shut down.")
