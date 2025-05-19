# Confluence MCP Server Rebuild: Task List

This task list outlines the steps to rebuild the Confluence MCP Server using FastMCP.

## Phase 1: Setup & Core Infrastructure

-   [ ] **Project Structure**: Create the new directory structure as defined in `Product_Technical_Architecture_and_Rebuild_Plan.md` (e.g., `confluence_mcp_server/`, `mcp_actions/`, `utils/`, `tests/`).
-   [ ] **Dependencies**: Initialize `pyproject.toml` (with Poetry/PDM) or `requirements.txt`. Add `fastmcp`, `atlassian-python-api`, `pydantic`, `python-dotenv`, `uvicorn`.
-   [ ] **Virtual Environment**: Create/Re-initialize and activate a new Python virtual environment and install dependencies.
-   [ ] **`.env` File**: Ensure `.env` is present with necessary `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`, and `LOG_LEVEL` variables.
-   [ ] **Logging**: Set up basic logging configuration (e.g., in `main.py` or a separate logging config file if FastMCP allows).
-   [ ] **Confluence Client (`confluence_client.py`)**: Implement the Confluence API client instantiation and management. Decide on resource injection strategy with FastMCP.
-   [ ] **Basic Server (`main.py`)**: 
    -   [ ] Instantiate `FastMCP` server.
    -   [ ] Register the Confluence client manager as a resource (if applicable).
    -   [ ] Implement a simple health check/ping tool (e.g., `/tools/ping` that returns `{"status": "ok"}`) to verify FastMCP setup.
    -   [ ] Ensure the server can start (e.g., `python -m confluence_mcp_server.main` or FastMCP's run command).
-   [ ] **Claude Desktop Manifest**: Create or define the structure for `claude_desktop_config.json` (or `tool.json`) required for Claude Desktop integration.
-   [ ] **Testing Setup (`conftest.py`)**: 
    -   [ ] Configure `pytest` and `pytest-asyncio`.
    -   [ ] Create a fixture for the `FastMCP` server instance.
    -   [ ] Create a fixture for an `httpx.AsyncClient` pointing to the test server instance.
    -   [ ] Create a fixture for a mocked `Confluence` API client.
-   [ ] **Error Handling Utilities (`utils/error_handling.py`)**: Implement initial structure for `handle_confluence_api_error` function.

## Phase 2: Implement Page Tools

For each page tool (`get_page`, `search_pages`, `create_page`, `update_page`, `delete_page`):

**Tool: Get Page (`get_confluence_page`)**
-   [ ] **Schemas (`schemas.py`)**: Define `GetPageInput` and `PageOutput` Pydantic models.
-   [ ] **Logic (`page_actions.py`)**: Implement `async def get_page_logic(...)` using the Confluence client and error handling.
-   [ ] **Registration (`main.py`)**: Register the `get_confluence_page` tool with FastMCP, linking to its logic and schemas.
-   [ ] **Unit Tests (`tests/test_page_actions.py`)**: Test `get_page_logic` with mocked Confluence client (success, page not found, API errors).
-   [ ] **Integration Tests (`tests/test_page_actions.py`)**: Test the full `/tools/get_confluence_page` endpoint (valid inputs, input validation errors, API errors resulting in MCPError).

**Tool: Search Pages (`search_confluence_pages`)**
-   [ ] **Schemas**: Define `SearchPagesInput` and `SearchPagesOutput` (with `PageOutputItem` or re-using `PageOutput`).
-   [ ] **Logic**: Implement `async def search_pages_logic(...)`.
-   [ ] **Registration**: Register in `main.py`.
-   [ ] **Unit Tests**: For `search_pages_logic`.
-   [ ] **Integration Tests**: For `/tools/search_confluence_pages`.

**Tool: Create Page (`create_confluence_page`)**
-   [ ] **Schemas**: Define `CreatePageInput` (output can be `PageOutput`).
-   [ ] **Logic**: Implement `async def create_page_logic(...)`.
-   [ ] **Registration**: Register in `main.py`.
-   [ ] **Unit Tests**: For `create_page_logic`.
-   [ ] **Integration Tests**: For `/tools/create_confluence_page`.

**Tool: Update Page (`update_confluence_page`)**
-   [ ] **Schemas**: Define `UpdatePageInput` (output can be `PageOutput`).
-   [ ] **Logic**: Implement `async def update_page_logic(...)` (remember to fetch current version).
-   [ ] **Registration**: Register in `main.py`.
-   [ ] **Unit Tests**: For `update_page_logic`.
-   [ ] **Integration Tests**: For `/tools/update_confluence_page`.

**Tool: Delete Page (`delete_confluence_page`)**
-   [ ] **Schemas**: Define `DeletePageInput` and `DeletePageOutput`.
-   [ ] **Logic**: Implement `async def delete_page_logic(...)`.
-   [ ] **Registration**: Register in `main.py`.
-   [ ] **Unit Tests**: For `delete_page_logic`.
-   [ ] **Integration Tests**: For `/tools/delete_confluence_page`.

## Phase 3: Implement Space Tools

**Tool: Get Spaces (`get_confluence_spaces`)**
-   [ ] **Schemas (`schemas.py`)**: Define `GetSpacesInput`, `GetSpacesOutputItem`, `GetSpacesOutput`.
-   [ ] **Logic (`space_actions.py`)**: Implement `async def get_spaces_logic(...)`.
-   [ ] **Registration (`main.py`)**: Register the `get_confluence_spaces` tool.
-   [ ] **Unit Tests (`tests/test_space_actions.py`)**: For `get_spaces_logic`.
-   [ ] **Integration Tests (`tests/test_space_actions.py`)**: For `/tools/get_confluence_spaces`.

## Phase 4: Implement Comment Tools

**Tool: Get Comments (`get_confluence_page_comments`)**
-   [ ] **Schemas (`schemas.py`)**: Define `GetCommentsInput`, `CommentOutputItem`, `GetCommentsOutput`.
-   [ ] **Logic (`comment_actions.py`)**: Implement `async def get_comments_logic(...)`.
-   [ ] **Registration (`main.py`)**: Register the `get_confluence_page_comments` tool.
-   [ ] **Unit Tests (`tests/test_comment_actions.py`)**: For `get_comments_logic`.
-   [ ] **Integration Tests (`tests/test_comment_actions.py`)**: For `/tools/get_confluence_page_comments`.

## Phase 5: Implement Attachment Tools

*(Review existing `attachment_actions.py` and `test_attachment_actions.py` from previous work if it's already FastMCP compatible and high quality. Refactor or rewrite as needed to align with the new architecture.)*

**Tool: Get Attachments (`get_confluence_page_attachments`)**
-   [ ] **Schemas (`schemas.py`)**: Define/Review `GetAttachmentsInput`, `AttachmentOutputItem`, `GetAttachmentsOutput`.
-   [ ] **Logic (`attachment_actions.py`)**: Implement/Review `async def get_attachments_logic(...)`.
-   [ ] **Registration (`main.py`)**: Register the `get_confluence_page_attachments` tool.
-   [ ] **Unit Tests (`tests/test_attachment_actions.py`)**: For `get_attachments_logic`.
-   [ ] **Integration Tests (`tests/test_attachment_actions.py`)**: For `/tools/get_confluence_page_attachments`.

**Tool: Add Attachment (`add_confluence_page_attachment`)**
-   [ ] **Schemas (`schemas.py`)**: Define/Review `AddAttachmentInput` and `AddAttachmentOutput`.
-   [ ] **Logic (`attachment_actions.py`)**: Implement/Review `async def add_attachment_logic(...)`.
-   [ ] **Registration (`main.py`)**: Register the `add_confluence_page_attachment` tool.
-   [ ] **Unit Tests (`tests/test_attachment_actions.py`)**: For `add_attachment_logic`.
-   [ ] **Integration Tests (`tests/test_attachment_actions.py`)**: For `/tools/add_confluence_page_attachment`.

## Phase 6: Productionization, Deployment & Final Review

### 6.1 MCP Compliance & Claude Desktop Integration
-   [ ] **Tool Listing & Execution**: Verify all tools are correctly listed and executable via MCP protocol (e.g., using a generic MCP client or through Claude Desktop).
-   [ ] **Error Handling Review**: Ensure consistent `MCPError` responses as per `utils/error_handling.py` and MCP standards.
-   [ ] **Claude Desktop Manifest (`tool.json` / `claude_desktop_config.json`)**: Finalize and validate the manifest file for Claude Desktop. Ensure it accurately reflects tools, schemas, and execution commands.
-   [ ] **CORS Configuration**: Confirm CORS is correctly handled by FastMCP for Claude Desktop interactions.
-   [ ] **Claude Desktop End-to-End Testing**: Conduct thorough testing of all tools through the Claude Desktop interface.

### 6.2 Deployment Operations
-   [ ] **Configuration Management**: Document final strategy for managing `.env` files or other configurations in a deployed environment.
-   [ ] **Structured Logging Review**: Ensure logging is structured, provides sufficient detail for troubleshooting, and sensitive information is not logged.
-   [ ] **Health Check Endpoint**: Confirm the simple health check/ping tool is operational for monitoring.
-   [ ] **(Optional) Packaging/Containerization**: 
    -   [ ] Consider packaging using Poetry or PDM if not already done.
    -   [ ] (If applicable) Create `Dockerfile` and `.dockerignore`.
    -   [ ] (If applicable) Create `docker-compose.yml` for local testing of the containerized application.

### 6.3 Security Review
-   [ ] **API Token Permissions**: Verify the Confluence API token has only the minimum necessary permissions.
-   [ ] **Input Validation/Sanitization Audit**: Review all tool inputs, especially those used in CQL or sensitive operations, for robust validation (Pydantic) and sanitization.
-   [ ] **Dependency Audit**: Run a security audit on dependencies (e.g., `pip-audit`) and plan updates for any vulnerable packages.
-   [ ] **Error Message Security**: Confirm error messages do not leak sensitive internal details.

### 6.4 Performance Considerations
-   [ ] **Performance Review**: Briefly review tool logic for any obvious performance issues. Note that primary dependency is Confluence API responsiveness.
-   [ ] **Asynchronous Code Review**: Ensure `async/await` is used appropriately for non-blocking operations.

### 6.5 Final Documentation & Code Quality
-   [ ] **Comprehensive Error Handling**: Ensure `utils/error_handling.py` is robust and consistently used by all tool logic functions to return `MCPError` instances.
-   [ ] **Input Validation Review**: Double-check all Pydantic model validators and any custom validation logic in tools.
-   [ ] **Full Test Suite**: Run `pytest` and ensure all (100%) tests pass.
-   [ ] **Code Linting & Formatting**: Apply a consistent code style (e.g., Black, Flake8).
-   [ ] **`README.md` Updates**: Update (or write new) `README.md` with:
    -   Project overview.
    -   Setup instructions (virtual env, dependencies, `.env` file).
    -   How to run the server (including for Claude Desktop).
    -   How to run tests.
    -   List of available tools with brief descriptions and example MCP requests.
    -   Key configuration options.
-   [ ] **Code Cleanup**: Remove any unused code, comments, or print statements.
-   [ ] **Final Review**: Perform a self-review of the entire codebase for consistency, clarity, and correctness.

### 6.6 Release Management (Optional - for more formal releases)
-   [ ] **Versioning**: Decide on a versioning scheme (e.g., SemVer).
-   [ ] **Changelog**: Maintain a `CHANGELOG.md`.

This task list provides a structured approach to the rebuild. Tasks within each phase can often be parallelized for different tools once the foundational elements are in place.