# Confluence MCP Server Development Tasks

## Phase 1: Project Setup & Core MCP Framework

*   [x] Define project structure
*   [x] Create main project directory (`confluence_mcp_server`)
*   [x] Create `mcp_actions` subdirectory
*   [x] Create `task.md` file
*   [x] Create `requirements.txt` and define initial dependencies (FastAPI, Uvicorn, python-dotenv, atlassian-python-api, pydantic)
*   [x] Create `.env_example` for environment variable guidance
*   [x] Create `README.md` with project overview and setup instructions
*   [x] Create `mcp_actions/__init__.py` (to make `mcp_actions` a Python package)
*   [x] Create `mcp_actions/schemas.py` (for Pydantic tool input/output models and common MCP structures)
*   [x] Create `main.py` (main FastAPI application file)
*   [x] Implement basic FastAPI application in `main.py` (including health check endpoint)
*   [x] Implement core MCP endpoints in `main.py` (`/tools` to list, `/execute` to run tools)
*   [x] Define initial Pydantic schemas in `mcp_actions/schemas.py` (generic MCP request/response, and for one simple tool like `get_spaces` to start)

## Phase 2: Confluence API Integration & Authentication
*   **Authentication & Configuration:**
    *   [x] Implement secure loading of Confluence credentials (URL, Username, API Key via environment variables using `python-dotenv` in `main.py` or a config module)
    *   [x] Implement Confluence API client initialization (using `atlassian-python-api`)
    *   [x] Test basic connection to Confluence instance (e.g., by trying to fetch current user details or a known space)

## Phase 3: MCP Tool Implementation (Develop each action)

*   **`get_spaces` Action:**
    *   [x] Define `GetSpacesInput` and `GetSpacesOutput` schemas in `mcp_actions/schemas.py`.
    *   [x] Implement `get_spaces` tool logic in `mcp_actions/space_actions.py`.
    *   [x] Integrate `get_spaces` into `main.py`'s `/execute` endpoint.
    *   [x] Test `/health` endpoint.
    *   [x] Test `/tools` endpoint (verify it lists `get_spaces` and its schema).
    *   [x] Implement automated tests for the `get_spaces` tool in `tests/test_get_spaces_tool.py` covering:
        *   [x] Successful execution with no inputs.
        *   [x] Successful execution with `limit` parameter.
        *   [x] Successful execution with `start` parameter.
        *   [x] Successful execution with `space_ids` parameter (list of space IDs).
        *   [x] Successful execution with `space_keys` parameter (list of space keys).
        *   [x] Successful execution with `space_type` parameter (e.g., 'global', 'personal').
        *   [x] Successful execution with `space_status` parameter (e.g., 'current', 'archived').
        *   [x] Successful execution with a combination of parameters (e.g., `limit`, `space_type`, `space_status`).
        *   [x] Error handling for invalid input types (e.g., non-integer `limit`).
        *   [x] Behavior when no spaces match the filter criteria.
    *   [x] Address `PendingDeprecationWarning` for `python-multipart` (suppressed via `pytest.ini` as it's internal to Starlette).
    *   [x] Resolve all test failures in `tests/test_get_spaces_tool.py` (manual mocking refactor for consistency).
*   **`Get Page` Action:**
    *   [x] Define `Get_Page` input/output schema in `mcp_actions/schemas.py`
    *   [x] Implement `get_page_logic` function in `mcp_actions/page_actions.py`
    *   [x] Integrate `Get_Page` into `main.py`'s `execute_tool`
    *   [x] Create `tests/test_get_page_tool.py` and implement automated tests for `Get_Page` tool, covering:
        *   [x] Successful execution with valid `page_id`.
        *   [x] Successful execution with valid `space_key` and `title`.
        *   [x] Error handling: non-existent `page_id`.
        *   [x] Error handling: non-existent `space_key` / `title` combination.
        *   [x] Error handling: `page_id` provided with `space_key` or `title`.
        *   [x] Error handling: `space_key` provided without `title`.
        *   [x] Error handling: `title` provided without `space_key`.
        *   [x] Error handling: invalid input type for `page_id` (e.g., string).
        *   [x] Behavior: page has specific content (verify basic structure).
        *   [x] Behavior: page has no content (or minimal default).
*   **`search_pages` Action:**
    *   [x] Define `search_pages` input/output schema in `mcp_actions/schemas.py`
    *   [x] Implement `search_pages_logic` function in `mcp_actions/page_actions.py`
    *   [x] Integrate `search_pages` into `main.py`'s `execute_tool`
    *   [x] Implement automated tests for `search_pages` tool, covering:
        *   [x] Successful execution with a simple CQL query.
        *   [x] Successful execution with `limit` and `start` parameters.
        *   [x] Successful execution with different `excerpt` strategies (e.g., 'highlight').
        *   [x] Successful execution with `expand` options (e.g., 'body.storage', 'version'). Refactored to use comma-separated string.
        *   [x] Behavior: query returns multiple results.
        *   [x] Behavior: query returns no results.
        *   [x] Error handling: invalid CQL query syntax.
        *   [x] Error handling: invalid input types for parameters.
*   **`update_page` Action:**
    *   [x] Define `update_page` input/output schema in `mcp_actions/schemas.py`
    *   [x] Implement `update_page_logic` function in `mcp_actions/page_actions.py`
    *   [x] Integrate `update_page` into `main.py`'s `execute_tool`
    *   [x] Implement automated tests for `update_page` tool, covering:
        *   [x] Successful execution: updating page title.
        *   [x] Successful execution: updating page body content.
        *   [x] Successful execution: updating page parent.
        *   [x] Successful execution: providing `current_version_number` for conflict resolution.
        *   [x] Error handling: page not found.
        *   [x] Error handling: version conflict (if `current_version_number` is stale).
        *   [x] Error handling: invalid input types.
*   **`create_page` Action:**
    *   [x] Define `create_page` input/output schema in `mcp_actions/schemas.py`
    *   [x] Implement `create_page_logic` function in `mcp_actions/page_actions.py`
    *   [x] Integrate `create_page` into `main.py`'s `execute_tool`
    *   [x] Implement automated tests for `create_page` tool, covering:
        *   [x] Successful execution: creating a new page with title, space_key, and body.
        *   [x] Successful execution: creating a page under a parent page (`parent_page_id`).
        *   [x] Error handling: space not found (invalid `space_key`).
        *   [x] Error handling: parent page not found (invalid `parent_page_id`).
        *   [x] Error handling: page with the same title already exists in the space (if not allowed).
        *   [x] Error handling: invalid input types.
*   **`delete_page` Action:**
    *   [x] Define `delete_page` input/output schema in `mcp_actions/schemas.py` (Input: `page_id`, Output: `message` or success bool)
    *   [x] Implement `delete_page_logic` function in `mcp_actions/page_actions.py`
    *   [x] Integrate `delete_page` into `main.py`'s `execute_tool`
    *   [x] Implement automated tests for `delete_page` tool, covering:
        *   [x] Successful execution: deleting an existing page.
        *   [x] Error handling: page not found.
        *   [x] Error handling: insufficient permissions (if possible to simulate).
        *   [x] Error handling: invalid input types (e.g., non-string page_id).
*   **`get_comments` Action:**
    *   [x] Define `get_comments` input/output schema in `mcp_actions/schemas.py`
    *   [x] Implement `get_comments_logic` function in `mcp_actions/comment_actions.py`
    *   [x] Integrate `get_comments` into `main.py`'s `execute_tool`
    *   [x] Implement automated tests for `get_comments` tool, covering:
        *   [x] Successful execution: fetching comments for a page with comments.
        *   [x] Successful execution: with `limit` and `start` parameters.
        *   [x] Behavior: page has no comments.
        *   [x] Error handling: page not found.
        *   [x] Error handling: invalid input types.
*   **`add_comment` Action:**
    *   [x] Define `add_comment` input/output schema in `mcp_actions/schemas.py`
    *   [x] Implement `add_comment_logic` function in `mcp_actions/comment_actions.py`
    *   [x] Integrate `add_comment` into `main.py`'s `execute_tool`
    *   [x] Implement automated tests for `add_comment` tool, covering:
        *   [x] Successful execution: adding a top-level comment to a page.
        *   [x] Successful execution: replying to an existing comment (`parent_comment_id`).
        *   [x] Error handling: page not found.
        *   [x] Error handling: parent comment not found.
        *   [x] Error handling: invalid input types.
*   **`get_attachments` Action:**
    *   [ ] Define `get_attachments` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `get_attachments_logic` function in `mcp_actions/attachment_actions.py`
    *   [ ] Integrate `get_attachments` into `main.py`'s `execute_tool`
    *   [ ] Implement automated tests for `get_attachments` tool, covering:
        *   [ ] Successful execution: fetching attachments for a page with attachments.
        *   [ ] Successful execution: filtering by `filename`.
        *   [ ] Successful execution: filtering by `media_type`.
        *   [ ] Successful execution: with `limit` and `start` parameters.
        *   [ ] Behavior: page has no attachments.
        *   [ ] Behavior: page has no attachments matching filters.
        *   [ ] Error handling: page not found.
        *   [ ] Error handling: invalid input types.
*   **`add_attachment` Action:**
    *   [ ] Define `add_attachment` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `add_attachment_logic` function in `mcp_actions/attachment_actions.py`
    *   [ ] Integrate `add_attachment` into `main.py`'s `execute_tool`
    *   [ ] Implement automated tests for `add_attachment` tool, covering:
        *   [ ] Successful execution: adding a new attachment to a page.
        *   [ ] Successful execution: adding an attachment with a comment.
        *   [ ] Successful execution: updating an existing attachment (new version).
        *   [ ] Error handling: page not found.
        *   [ ] Error handling: file data issues (e.g., empty, too large if there are limits).
        *   [ ] Error handling: invalid input types.

## Phase 4: Testing, Refinement & Documentation
*   [x] Set up GitHub repository and push initial project state.
*   [x] Pushed get_page tool implementation and test directory normalization to GitHub.
*   [x] Refactor FastAPI error handling in main.py to return correct HTTP status codes and serialize GetSpacesOutput correctly.
*   [ ] Review all code for clarity, efficiency, and error handling
*   [ ] Add comprehensive comments and docstrings throughout the codebase
*   [ ] Finalize `README.md` with detailed setup, configuration (including `.env` setup), and usage instructions for each tool.
*   [ ] Perform exploratory testing and verify automated test coverage.

## Phase 5: Test Automation (using pytest and httpx)

*   [x] Refactor project structure: Moved `tests` directory to project root, updated relative imports in `main.py`, and corrected `pytest.ini` to resolve import errors and ensure all tests pass.
*   [x] Add `pytest` and `httpx` to `requirements.txt`.
*   [x] Create `tests/` directory structure (`tests/__init__.py`, `tests/conftest.py`).
*   [x] Implement a `pytest` fixture in `conftest.py` for an `httpx.AsyncClient` to test the FastAPI app.
*   [x] Write initial automated tests for basic endpoints in `tests/test_main_endpoints.py`:
    *   [x] Test `/health` endpoint.
    *   [x] Test `/tools` endpoint (verify it lists `get_spaces` and its schema).
*   [x] Implement automated tests for the `get_spaces` tool in `tests/test_get_spaces_tool.py`.
    *   [x] Successful execution with no inputs.
    *   [x] Successful execution with `limit` parameter.
*   [x] Research and implement mocking for `atlassian.Confluence` API calls to make tests independent of the live Confluence instance and faster.
    *   [x] Apply mocking to `get_spaces` tests.
    *   [x] Apply mocking to `Get_Page` tests.
*   [x] Resolve all test failures for `Get_Spaces` tests (manual mocking refactor).
*   [ ] Ensure all future tools are developed with corresponding automated tests.
*   [ ] Integrate test execution into the development workflow (e.g., a simple script or command to run all tests).
