# conftest.py for shared pytest fixtures

import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

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
MOCK_SPACE_ID = "CONFLTESTSPACEID"  # Added MOCK_SPACE_ID
MOCK_PAGE_VERSION = 1 # A generic version number for mocks
MOCK_PAGE_STATUS = "current"

MOCK_EXPAND_PARAMS = "body.storage,version"
MOCK_NON_EXISTENT_PAGE_ID = 99999
MOCK_PAGE_ID_NO_SPACE_TITLE_LOOKUP = 12346 # For specific test scenarios
MOCK_PAGE_ID_BY_TITLE = 54321  # Added for tests needing a specific ID for title lookups

# New constants for minimal content test
MOCK_PAGE_ID_MINIMAL_CONTENT = 98765
MOCK_MINIMAL_PAGE_TITLE = "Minimal Page Title Example"
MOCK_MINIMAL_SPACE_KEY = "MINSPACEKEY"

# --- Helper Function to Generate Mock Confluence Page Data ---
def get_mock_confluence_page_data(
    page_id=MOCK_PAGE_ID, 
    title=MOCK_PAGE_TITLE, 
    space_key=MOCK_SPACE_KEY, 
    space_id=None, 
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
    
    if space_id is not None:
        page_data["space"]["id"] = str(space_id) # Add space id to the space object if provided

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
    Returns an AsyncClient instance directly. 
    Uses ASGITransport for httpx.
    """
    transport = ASGITransport(app=fastapi_app)
    ac = AsyncClient(transport=transport, base_url="http://test")

    # Finalizer removed to prevent RuntimeError from asyncio.run()
    # within the pytest-asyncio managed event loop.
    return ac # Return the client directly

@pytest.fixture
def confluence_client_mock() -> MagicMock:
    """Provides a MagicMock for the atlassian.Confluence client,
    and patches 'get_confluence_client' in main.py to return this mock."""
    mock = MagicMock()
    # This URL is used by some logic if base_url isn't explicitly passed.
    # It should be the base instance URL, e.g., "https://your-domain.atlassian.net"
    mock.url = MOCK_CONFLUENCE_INSTANCE_URL 

    # Patch the get_confluence_client function in the main module
    # This ensures that when the app calls get_confluence_client(), it gets our mock.
    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock) as patched_get_client:
        yield mock # The test will use this mock directly

    # The patch is automatically undone when the 'with' block exits.
