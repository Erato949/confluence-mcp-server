# conftest.py for shared pytest fixtures

import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from unittest.mock import MagicMock

# Import the FastAPI app instance. Ensure PYTHONPATH or editable install is set up.
# For now, assuming pytest is run from the root of Confluence-MCP-Server_Claude
# or that confluence_mcp_server is otherwise discoverable.
from confluence_mcp_server.main import app as fastapi_app

# --- Mock Constants for Confluence Tests ---
MOCK_CONFLUENCE_INSTANCE_URL = "https://feedbackloopai.atlassian.net" # Base instance URL
MOCK_CONFLUENCE_WEB_BASE_URL = f"{MOCK_CONFLUENCE_INSTANCE_URL}/wiki" # Full base for web links

MOCK_PAGE_ID = 12345
MOCK_PAGE_TITLE = "Test Page Title"
MOCK_SPACE_KEY = "TESTSPACE"
MOCK_PAGE_VERSION = 1 # A generic version number for mocks
MOCK_PAGE_STATUS = "current"

MOCK_EXPAND_PARAMS = "body.storage,version"
MOCK_NON_EXISTENT_PAGE_ID = 99999
MOCK_PAGE_ID_NO_SPACE_TITLE_LOOKUP = 12346 # For specific test scenarios

# New constants for minimal content test
MOCK_PAGE_ID_MINIMAL_CONTENT = 98765
MOCK_MINIMAL_PAGE_TITLE = "Minimal Page Title Example"
MOCK_MINIMAL_SPACE_KEY = "MINSPACEKEY"

# --- Helper Function to Generate Mock Confluence Page Data ---
def get_mock_confluence_page_data(
    page_id=MOCK_PAGE_ID, 
    title=MOCK_PAGE_TITLE, 
    space_key=MOCK_SPACE_KEY, 
    expand: str = None, 
    has_content=True, 
    has_version=True,
    version_number=MOCK_PAGE_VERSION
):
    """Generates mock Confluence page data similar to API responses."""
    page_data = {
        "id": str(page_id), # API usually returns ID as string
        "title": title,
        "status": MOCK_PAGE_STATUS,
        "space": {"key": space_key}, # For space_key extraction
        "_links": {
            # This path will be appended to "INSTANCE_URL/wiki"
            # Format can vary, but this is a common one for web UI links.
            "webui": f"/spaces/{space_key}/pages/{page_id}/{title.replace(' ', '+')}"
        }
    }
    
    # Mocking expanded content based on 'expand' string and flags
    if expand:
        if "body.storage" in expand:
            if has_content:
                # Using a dynamic content string based on title for clarity
                page_data["body"] = {"storage": {"value": f"<p>Content for page '{title}' (ID: {page_id}).</p>"}}
            else:
                page_data["body"] = {"storage": {"value": None}} # Ensure key exists even if no content
        
        if "version" in expand:
            if has_version:
                page_data["version"] = {"number": version_number}
            else:
                page_data["version"] = {"number": None} # Ensure key exists even if no version
    return page_data

# --- Helper Function to Generate Mock Confluence CQL Search Results --- 
def get_mock_cql_search_results(cql_query: str, results: list, limit: int, start: int, total_size: int):
    """
    Generates a mock dictionary structure similar to Confluence API CQL search responses.
    """
    mock_response = {
        "results": results, 
        "start": start,
        "limit": limit,
        "size": total_size, # This represents the total number of results matching the query
        "_links": {
            "base": MOCK_CONFLUENCE_WEB_BASE_URL,
            "context": "/wiki"
        }
    }
    if start + len(results) < total_size:
        # Simplified next link for pagination indication
        mock_response["_links"]["next"] = f"/rest/api/content/search?cql={cql_query}&start={start + limit}&limit={limit}"
    
    return mock_response

# --- Pytest Fixtures ---

# Custom event_loop fixture removed.
# Pytest-asyncio will provide the event loop based on the asyncio marker's scope in test files.

@pytest.fixture(scope="function")
def client(request) -> AsyncClient:
    """
    An asynchronous test client for the FastAPI application, function-scoped.
    Returns an AsyncClient instance directly. Attempts teardown (aclose) in finalizer.
    Uses ASGITransport for httpx.
    """
    transport = ASGITransport(app=fastapi_app)
    ac = AsyncClient(transport=transport, base_url="http://test")

    def finalizer():
        print("DEBUG: Client fixture finalizer called. Attempting ac.aclose().")
        try:
            # Try to run ac.aclose(). This creates a new event loop or uses the existing one
            # if not running. If called from within a running loop, it will raise RuntimeError.
            asyncio.run(ac.aclose()) # This is the simplest way to call an async func from sync
            print("DEBUG: AsyncClient.aclose() completed via asyncio.run().")
        except RuntimeError as e:
            # This typically means asyncio.run() was called from an already running event loop.
            print(f"DEBUG: Could not close AsyncClient via asyncio.run() in finalizer: {e}. Client might remain open.")
        except Exception as e:
            print(f"DEBUG: General error during AsyncClient.aclose() attempt in finalizer: {e}")

    request.addfinalizer(finalizer)
    return ac

@pytest.fixture
def confluence_client_mock() -> MagicMock:
    """Provides a MagicMock for the atlassian.Confluence client."""
    mock = MagicMock()
    # This URL is used by page_actions.py to construct the full web_url for pages.
    # It should be the base instance URL, e.g., "https://your-domain.atlassian.net"
    mock.url = MOCK_CONFLUENCE_INSTANCE_URL 
    return mock
