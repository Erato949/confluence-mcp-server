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
    *   [x] Create `tests/test_get_spaces_tool.py`.
    *   [x] Implement automated tests for the `get_spaces` tool in `tests/test_get_spaces_tool.py` covering:
        *   [x] Successful execution with no inputs.
        *   [ ] Successful execution with `limit` parameter.
        *   [ ] Successful execution with `start` parameter.
        *   [ ] Successful execution with `space_ids` parameter (list of space IDs).
        *   [ ] Successful execution with `space_keys` parameter (list of space keys).
        *   [ ] Successful execution with `space_type` parameter (e.g., 'global', 'personal').
        *   [ ] Successful execution with `space_status` parameter (e.g., 'current', 'archived').
        *   [ ] Successful execution with a combination of parameters (e.g., `limit`, `space_type`, `space_status`).
        *   [ ] Error handling for invalid input types (e.g., non-integer `limit`).
        *   [ ] Behavior when no spaces match the filter criteria.
    *   [x] Address `PendingDeprecationWarning` for `python-multipart` (suppressed via `pytest.ini` as it's internal to Starlette).
*   **`Get_Page` Action:**
    *   [ ] Define `Get_Page` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `get_page_logic` function in `mcp_actions/page_actions.py`
    *   [ ] Integrate `Get_Page` into `main.py`'s `execute_tool`
*   **`search_pages` Action:**
    *   [ ] Define `search_pages` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `search_pages_logic` function in `mcp_actions/page_actions.py`
    *   [ ] Integrate `search_pages` into `main.py`'s `execute_tool`
*   **`update_page` Action:**
    *   [ ] Define `update_page` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `update_page_logic` function in `mcp_actions/page_actions.py`
    *   [ ] Integrate `update_page` into `main.py`'s `execute_tool`
*   **`create_page` Action:**
    *   [ ] Define `create_page` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `create_page_logic` function in `mcp_actions/page_actions.py`
    *   [ ] Integrate `create_page` into `main.py`'s `execute_tool`
*   **`get_comments` Action:**
    *   [ ] Define `get_comments` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `get_comments_logic` function in `mcp_actions/comment_actions.py`
    *   [ ] Integrate `get_comments` into `main.py`'s `execute_tool`
*   **`add_comment` Action:**
    *   [ ] Define `add_comment` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `add_comment_logic` function in `mcp_actions/comment_actions.py`
    *   [ ] Integrate `add_comment` into `main.py`'s `execute_tool`
*   **`get_attachments` Action:**
    *   [ ] Define `get_attachments` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `get_attachments_logic` function in `mcp_actions/attachment_actions.py`
    *   [ ] Integrate `get_attachments` into `main.py`'s `execute_tool`
*   **`add_attachment` Action:**
    *   [ ] Define `add_attachment` input/output schema in `mcp_actions/schemas.py`
    *   [ ] Implement `add_attachment_logic` function in `mcp_actions/attachment_actions.py`
    *   [ ] Integrate `add_attachment` into `main.py`'s `execute_tool`

## Phase 4: Testing, Refinement & Documentation
*   [ ] Review all code for clarity, efficiency, and error handling
*   [ ] Add comprehensive comments and docstrings throughout the codebase
*   [ ] Finalize `README.md` with detailed setup, configuration (including `.env` setup), and usage instructions for each tool.
*   [ ] Perform exploratory testing and verify automated test coverage.

## Phase 5: Test Automation (using pytest and httpx)

*   [ ] Add `pytest` and `httpx` to `requirements.txt`.
*   [ ] Create `tests/` directory structure (`tests/__init__.py`, `tests/conftest.py`).
*   [/] Implement a `pytest` fixture in `conftest.py` for an `httpx.AsyncClient` to test the FastAPI app.
*   [/] Write initial automated tests for basic endpoints in `tests/test_main_endpoints.py`:
    *   [/] Test `/health` endpoint.
    *   [/] Test `/tools` endpoint (verify it lists `get_spaces` and its schema).
*   [ ] Create `tests/test_get_spaces_tool.py`.
*   [x] Implement automated tests for the `get_spaces` tool in `tests/test_get_spaces_tool.py` covering:
    *   [x] Successful execution with no inputs.
    *   [ ] Successful execution with `limit` parameter.
    *   [ ] Successful execution with `start` parameter.
    *   [ ] Successful execution with `space_ids` parameter (list of space IDs).
    *   [ ] Successful execution with `space_keys` parameter (list of space keys).
    *   [ ] Successful execution with `space_type` parameter (e.g., 'global', 'personal').
    *   [ ] Successful execution with `space_status` parameter (e.g., 'current', 'archived').
    *   [ ] Successful execution with a combination of parameters (e.g., `limit`, `space_type`, `space_status`).
    *   [ ] Error handling for invalid input types (e.g., non-integer `limit`).
*   [ ] Research and implement mocking for `atlassian.Confluence` API calls to make tests independent of the live Confluence instance and faster.
    *   [ ] Apply mocking to `get_spaces` tests.
*   [ ] Ensure all future tools are developed with corresponding automated tests.
*   [ ] Integrate test execution into the development workflow (e.g., a simple script or command to run all tests).
