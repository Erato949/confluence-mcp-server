# Product Technical Architecture and Rebuild Plan: Confluence MCP Server (FastMCP)

## 1. Introduction

This document outlines the technical architecture for rebuilding the Confluence MCP Server. The primary goal is to create a robust, maintainable, and testable server using the FastMCP framework, ensuring seamless integration with Claude Desktop and other MCP clients. The previous implementation faced challenges due to not initially leveraging FastMCP.

## 2. Core Technologies

-   **MCP Framework**: FastMCP
-   **Language**: Python (3.9+)
-   **API Client**: `atlassian-python-api` (for Confluence)
-   **Schema Validation**: Pydantic (via FastMCP)
-   **Testing**: Pytest, `httpx.AsyncClient`
-   **ASGI Server**: Uvicorn (typically managed by FastMCP)

## 3. Server Structure

```
confluence-mcp-server/
├── confluence_mcp_server/            # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastMCP server instantiation, tool registration
│   ├── confluence_client.py          # Confluence API client setup and management
│   ├── mcp_actions/                  # Directory for tool logic and schemas
│   │   ├── __init__.py
│   │   ├── schemas.py                # All Pydantic input/output models
│   │   ├── page_actions.py           # Logic for page-related tools
│   │   ├── space_actions.py          # Logic for space-related tools
│   │   ├── comment_actions.py        # Logic for comment-related tools
│   │   ├── attachment_actions.py     # Logic for attachment-related tools
│   ├── utils/                        # Utility functions
│   │   ├── __init__.py
│   │   └── error_handling.py       # Mapping API/internal errors to MCPError
│   └── .env                          # Environment variables (Confluence URL, token, etc.)
├── claude_desktop_config.json        # Example: Manifest file for Claude Desktop integration
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures (e.g., API client mocks, test client)
│   ├── test_page_actions.py
│   ├── test_space_actions.py
│   ├── test_comment_actions.py
│   └── test_attachment_actions.py
├── pyproject.toml                    # Project metadata and dependencies (or requirements.txt)
├── README.md                         # Project overview, setup, usage
└── task.md                           # Development tasks
```

## 4. Confluence Client Management (`confluence_client.py`)

-   A module responsible for initializing and providing the Confluence API client.
-   It should read configuration (URL, username, API token) from environment variables.
-   Consider making the client instance available as a FastMCP resource or a managed singleton to be injected into tool logic functions.

**Example FastMCP Resource Approach (Conceptual):**

```python
# confluence_client.py
from atlassian import Confluence
import os

class ConfluenceClientManager:
    def __init__(self):
        self.confluence_url = os.getenv("CONFLUENCE_URL")
        self.confluence_username = os.getenv("CONFLUENCE_USERNAME")
        self.confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        if not all([self.confluence_url, self.confluence_username, self.confluence_api_token]):
            raise ValueError("Missing Confluence configuration in .env")
        self._client = None

    def get_client(self) -> Confluence:
        if self._client is None:
            self._client = Confluence(
                url=self.confluence_url,
                username=self.confluence_username,
                password=self.confluence_api_token,
                cloud=True # Assuming Confluence Cloud, adjust if server
            )
        return self._client

# main.py (conceptual integration)
# from .confluence_client import ConfluenceClientManager
# server = FastMCP()
# server.add_resource("confluence_client_manager", ConfluenceClientManager())

# In tool logic:
# async def get_page_logic(inputs: GetPageInput, confluence_client_manager: ConfluenceClientManager = server.requires_resource("confluence_client_manager")):
#     client = confluence_client_manager.get_client()
#     # ... use client
```
Refer to FastMCP documentation for the canonical way to manage and inject resources.

## 5. Tool Definitions

All tools will be defined with Pydantic input/output schemas and `async` logic functions.
Error handling will map underlying exceptions (e.g., `requests.exceptions.HTTPError` from the Confluence client, custom validation errors) to `fastmcp.error.MCPError` with appropriate codes.

### General Error Handling Strategy (`utils/error_handling.py`)

Create a utility to wrap Confluence API calls or handle exceptions from them:

```python
from fastapi import HTTPException # Or directly use fastmcp.error.MCPError
from fastmcp.error import MCPError, MCPErrorCode
from requests.exceptions import HTTPError
import logging

logger = logging.getLogger(__name__)

def handle_confluence_api_error(e: Exception, operation: str) -> MCPError:
    if isinstance(e, HTTPError):
        status_code = e.response.status_code
        error_details = e.response.text
        logger.error(f"Confluence API error during {operation} ({status_code}): {error_details}")
        if status_code == 401:
            return MCPError(code=MCPErrorCode.AuthorizationFailed, message=f"Confluence authorization failed during {operation}.")
        if status_code == 403:
            return MCPError(code=MCPErrorCode.PermissionDenied, message=f"Permission denied by Confluence during {operation}.")
        if status_code == 404:
            return MCPError(code=MCPErrorCode.ResourceNotFound, message=f"Confluence resource not found during {operation}.")
        # General server error for other client errors (4xx)
        return MCPError(code=MCPErrorCode.ServerError, message=f"Confluence API client error ({status_code}) during {operation}: {error_details}")
    elif isinstance(e, ValueError):
         logger.warning(f"Validation error during {operation}: {str(e)}")
         return MCPError(code=MCPErrorCode.InvalidParams, message=f"Invalid parameters for {operation}: {str(e)}")
    else:
        logger.exception(f"Unexpected error during {operation}: {str(e)}")
        return MCPError(code=MCPErrorCode.ServerError, message=f"An unexpected server error occurred during {operation}.")

# Example usage in tool logic:
# try:
#     # ... confluence_client call ...
# except Exception as e:
#     raise handle_confluence_api_error(e, "fetching page")
```

### Tool: `get_page`

-   **Tool Name (FastMCP)**: `get_confluence_page` (or similar)
-   **Description**: Retrieves a Confluence page by its ID or by Space Key and Title.
-   **Input Schema (`GetPageInput` in `schemas.py`)**: 
    -   `page_id: Optional[str]`
    -   `space_key: Optional[str]`
    -   `title: Optional[str]`
    -   `expand: Optional[str]` (comma-separated list of fields to expand, e.g., "body.view,version")
    -   *Validator*: Ensure either `page_id` or (`space_key` and `title`) is provided.
-   **Output Schema (`PageOutput` in `schemas.py`)**: 
    -   `id: str`
    -   `status: str`
    -   `title: str`
    -   `space_key: str` (extracted from `_expandable.space` or similar)
    -   `version: int` (extracted from `version.number`)
    -   `url: str` (constructed from Confluence base URL and page ID/title)
    -   `body: Optional[str]` (HTML content, if requested via `expand`)
    -   `author_id: Optional[str]`
    -   `created_date: Optional[str]`
    -   `last_modified_date: Optional[str]`
-   **Core Logic (`page_actions.py`)**: 
    -   If `page_id` provided, use `client.get_page_by_id()`.
    -   If `space_key` and `title`, use `client.get_page_by_title()`.
    -   Map Confluence API response to `PageOutput`.
-   **Error Handling**: Page not found (404) -> `MCPError(code=MCPErrorCode.ResourceNotFound)`. API errors -> appropriate `MCPError`.

### Tool: `search_pages`

-   **Tool Name (FastMCP)**: `search_confluence_pages`
-   **Description**: Searches Confluence pages using Confluence Query Language (CQL).
-   **Input Schema (`SearchPagesInput` in `schemas.py`)**: 
    -   `cql: str` (the CQL query string)
    -   `limit: Optional[int]` (default 25, max 100)
    -   `start: Optional[int]` (default 0)
    -   `expand: Optional[str]` (comma-separated)
    -   `excerpt: Optional[str]` (e.g., "highlight")
-   **Output Schema (`SearchPagesOutput` in `schemas.py`)**: 
    -   `results: List[PageOutput]` (re-use `PageOutput` or a slimmer version)
    -   `total_available: int`
    -   `next_start_offset: Optional[int]`
-   **Core Logic (`page_actions.py`)**: Use `client.cql()`.
-   **Error Handling**: Invalid CQL syntax, API errors -> `MCPError`.

### Tool: `create_page`

-   **Tool Name (FastMCP)**: `create_confluence_page`
-   **Description**: Creates a new Confluence page.
-   **Input Schema (`CreatePageInput` in `schemas.py`)**: 
    -   `space_key: str`
    -   `title: str`
    -   `body: str` (HTML content)
    -   `parent_page_id: Optional[str]`
    -   `update_message: Optional[str]` (for page history)
-   **Output Schema (`PageOutput` from `schemas.py` - for the created page)**.
-   **Core Logic (`page_actions.py`)**: Use `client.create_page()`.
-   **Error Handling**: Space not found, parent page not found, title conflict, permissions -> `MCPError`.

### Tool: `update_page`

-   **Tool Name (FastMCP)**: `update_confluence_page`
-   **Description**: Updates an existing Confluence page.
-   **Input Schema (`UpdatePageInput` in `schemas.py`)**: 
    -   `page_id: str`
    -   `new_version_number: int` (current version + 1, fetched first)
    -   `title: Optional[str]`
    -   `body: Optional[str]`
    -   `parent_page_id: Optional[str]`
    -   `update_message: Optional[str]`
    -   *Validator*: At least one of `title`, `body`, or `parent_page_id` must be provided for an update.
-   **Output Schema (`PageOutput` from `schemas.py` - for the updated page)**.
-   **Core Logic (`page_actions.py`)**: 
    1.  Fetch current page details (including current version) using `client.get_page_by_id(page_id, expand='version')`.
    2.  Use `client.update_page()` or `client.update_existing_page()` with the incremented version number and new content.
-   **Error Handling**: Page not found, version conflict, permissions -> `MCPError`.

### Tool: `delete_page`

-   **Tool Name (FastMCP)**: `delete_confluence_page`
-   **Description**: Deletes a Confluence page.
-   **Input Schema (`DeletePageInput` in `schemas.py`)**: 
    -   `page_id: str`
-   **Output Schema (`DeletePageOutput` in `schemas.py`)**: 
    -   `status: str` (e.g., "success")
    -   `message: str` (e.g., "Page with ID {page_id} deleted successfully.")
-   **Core Logic (`page_actions.py`)**: Use `client.delete_page()`.
-   **Error Handling**: Page not found, permissions -> `MCPError`.

### Tool: `get_spaces`

-   **Tool Name (FastMCP)**: `get_confluence_spaces`
-   **Description**: Retrieves a list of Confluence spaces.
-   **Input Schema (`GetSpacesInput` in `schemas.py`)**: 
    -   `space_keys: Optional[List[str]]`
    -   `type: Optional[str]` (e.g., "global", "personal")
    -   `status: Optional[str]` (e.g., "current")
    -   `limit: Optional[int]` (default 25)
    -   `start: Optional[int]` (default 0)
    -   `expand: Optional[str]`
-   **Output Schema (`GetSpacesOutputItem`, `GetSpacesOutput` in `schemas.py`)**: 
    -   `GetSpacesOutputItem`: `id: int`, `key: str`, `name: str`, `type: str`, `status: str`, `url: str`.
    -   `GetSpacesOutput`: `spaces: List[GetSpacesOutputItem]`, `total_available: int`, `next_start_offset: Optional[int]`.
-   **Core Logic (`space_actions.py`)**: Use `client.get_all_spaces()` with filtering parameters.
-   **Error Handling**: API errors -> `MCPError`.

### Tool: `get_comments`

-   **Tool Name (FastMCP)**: `get_confluence_page_comments`
-   **Description**: Retrieves comments for a specific Confluence page.
-   **Input Schema (`GetCommentsInput` in `schemas.py`)**: 
    -   `page_id: str`
    -   `limit: Optional[int]` (default 25)
    -   `start: Optional[int]` (default 0)
    -   `expand: Optional[str]`
-   **Output Schema (`CommentOutputItem`, `GetCommentsOutput` in `schemas.py`)**: 
    -   `CommentOutputItem`: `id: str`, `author_id: Optional[str]`, `created_date: str`, `body: str` (potentially needs format specification e.g. view), `url: str`.
    -   `GetCommentsOutput`: `comments: List[CommentOutputItem]`, `total_returned: int`, `next_start_offset: Optional[int]`.
-   **Core Logic (`comment_actions.py`)**: Use `client.get_page_comments()`.
-   **Error Handling**: Page not found -> `MCPError(code=MCPErrorCode.ResourceNotFound)`. API errors -> `MCPError`.

### Tool: `get_attachments`

-   **Tool Name (FastMCP)**: `get_confluence_page_attachments`
-   **Description**: Retrieves attachments for a specific Confluence page.
-   **Input Schema (`GetAttachmentsInput` in `schemas.py`)**: 
    -   `page_id: str`
    -   `filename: Optional[str]` (filter by filename)
    -   `limit: Optional[int]` (default 25)
    -   `start: Optional[int]` (default 0)
    -   `media_type: Optional[str]` (filter by media type)
-   **Output Schema (`AttachmentOutputItem`, `GetAttachmentsOutput` in `schemas.py`)**: 
    -   `AttachmentOutputItem`: `id: str`, `title: str` (filename), `media_type: str`, `file_size: int`, `created_date: str`, `download_link: str`.
    -   `GetAttachmentsOutput`: `attachments: List[AttachmentOutputItem]`, `total_available: int`, `next_start_offset: Optional[int]`.
-   **Core Logic (`attachment_actions.py`)**: Use `client.get_attachments_from_content()`.
-   **Error Handling**: Page not found -> `MCPError(code=MCPErrorCode.ResourceNotFound)`. API errors -> `MCPError`.

### Tool: `add_attachment`

-   **Tool Name (FastMCP)**: `add_confluence_page_attachment`
-   **Description**: Adds an attachment to a Confluence page from a local file path.
-   **Input Schema (`AddAttachmentInput` in `schemas.py`)**: 
    -   `page_id: str`
    -   `file_path: str` (absolute path to the local file)
    -   `comment: Optional[str]`
    -   `content_type: Optional[str]` (e.g., "image/png")
-   **Output Schema (`AddAttachmentOutput` from `schemas.py`)**: 
    -   `id: str` (ID of the created attachment)
    -   `title: str` (filename)
    -   `media_type: str`
    -   `file_size: int`
    -   `download_link: str`
    -   `message: str` (e.g., "Attachment added successfully.")
-   **Core Logic (`attachment_actions.py`)**: Use `client.attach_file()`.
-   **Error Handling**: Page not found, file not found locally, permissions, API errors -> `MCPError`.

## 6. Testing Strategy

-   **Unit Tests**: 
    -   Test individual logic functions in `*_actions.py` files.
    -   Mock the `Confluence` client instance to simulate various API responses (success, errors, empty data).
    -   Verify correct data transformation and error propagation.
-   **Integration Tests**: 
    -   Test the full FastMCP tool execution flow from HTTP request to response.
    -   Use `httpx.AsyncClient` with `ASGITransport(app=server.app)` (where `server` is your `FastMCP` instance) to send requests to the in-memory server.
    -   Mock the Confluence client at a higher level or use a test Confluence instance if available (less common for automated tests).
    -   Test:
        -   Successful tool execution with valid inputs.
        -   Input validation errors (Pydantic and custom).
        -   Correct `MCPError` responses for various failure scenarios (API errors, resource not found, etc.).
        -   Consider potential concurrency scenarios if tools become more complex, though initial Confluence operations are largely atomic.
    -   **Fixtures (`conftest.py`)**: 
    -   `event_loop`: Standard for `pytest-asyncio`.
    -   `fastmcp_server_instance`: A fixture to provide a configured `FastMCP` server instance for tests.
    -   `test_client(fastmcp_server_instance)`: An `httpx.AsyncClient` configured to talk to the `fastmcp_server_instance`.
    -   `mock_confluence_client`: A fixture providing a `MagicMock` instance of the `Confluence` client, pre-configured for common methods.

## 7. Scalability and Performance

-   The server will leverage FastMCP's asynchronous capabilities, allowing for efficient handling of concurrent requests.
-   Performance will be monitored post-deployment, and optimizations will be implemented if specific bottlenecks are identified.
-   For typical Confluence operations, the primary performance dependency will be the Confluence API itself.

## 8. Configuration (`.env`)

Store sensitive and environment-specific configurations in a `.env` file:

```
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your_api_token
LOG_LEVEL=INFO
# MCP_PORT=8080 (FastMCP might pick this up, or use for Uvicorn if run manually)
```

## 9. Deployment and Claude Desktop Integration

-   **Packaging**: The server is a standard Python application. Dependencies will be managed via `requirements.txt` or `pyproject.toml` (if Poetry/PDM is adopted).
-   **Execution**: The server is intended to be run directly using `python -m confluence_mcp_server.main` or similar, as configured in the Claude Desktop tool manifest.
-   **Claude Desktop Manifest (`tool.json` / `claude_desktop_config.json`)**:
    -   A manifest file will be required to register the server and its tools with Claude Desktop.
    -   FastMCP may provide capabilities to assist in generating or serving parts of this manifest. The specifics of its structure and maintenance will need to align with Claude Desktop requirements.
-   **CORS**: Cross-Origin Resource Sharing will be handled by FastMCP, which is typically configured to allow requests from the Claude Desktop environment.

## 10. Logging

-   Use standard Python `logging` module.
-   Configure logging level via `.env`.
-   Log key events: server startup, tool invocations (input parameters, sanitized if sensitive), errors, Confluence API interactions (request/response summaries).
-   FastMCP may have its own logging mechanisms; integrate with them or configure them as needed.

## 11. Security Considerations

-   **API Token Management**:
    -   Confluence API tokens and other secrets will be managed exclusively through the `.env` file and environment variables, never hard-coded.
    -   The `.env` file must be included in `.gitignore`.
-   **Principle of Least Privilege**: The Confluence API token used by the server should be granted only the minimum necessary permissions required for the implemented tools to function.
-   **Input Validation and Sanitization**: All inputs received from the MCP client will be rigorously validated by Pydantic schemas defined for each tool. Special care will be taken for any inputs used in constructing CQL queries or other potentially sensitive API parameters to prevent injection attacks.
-   **Dependency Management**: Regularly review and update dependencies (e.g., using `pip-audit` or GitHub's Dependabot) to patch known vulnerabilities.
-   **Error Handling**: Ensure that error messages returned to the client do not expose sensitive internal system details or stack traces. FastMCP's error handling should facilitate this.

## 12. Dependencies (Example `pyproject.toml` or `requirements.txt`)

-   `fastmcp`
-   `atlassian-python-api`
-   `pydantic`
-   `python-dotenv`
-   `uvicorn` (often a dependency of FastMCP or used to run it)
-   `pytest`, `pytest-asyncio`, `httpx`, `respx` (for mocking HTTPX calls if needed)

This architecture provides a solid foundation for building the new Confluence MCP Server. Each tool will be developed incrementally, focusing on clear schemas, robust logic, and comprehensive tests.
