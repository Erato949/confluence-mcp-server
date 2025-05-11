import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, ANY

# Import constants, helpers, and fixtures from conftest
from .conftest import (
    MOCK_CONFLUENCE_INSTANCE_URL,
    MOCK_CONFLUENCE_WEB_BASE_URL,
    get_mock_confluence_page_data, # For creating individual page mocks
    get_mock_cql_search_results,  # For creating mock search API responses
    confluence_client_mock        # Fixture for mocked Confluence client
)

# Basic test data
MOCK_CQL_QUERY = "label = 'test-label' and type = page"
MOCK_SEARCH_PAGE_1_ID = 701
MOCK_SEARCH_PAGE_1_TITLE = "First Page from Search"
MOCK_SEARCH_PAGE_1_SPACE = "DOC"

MOCK_SEARCH_PAGE_2_ID = 702
MOCK_SEARCH_PAGE_2_TITLE = "Second Page for Testing Search"
MOCK_SEARCH_PAGE_2_SPACE = "DOC"


@pytest.mark.asyncio
async def test_search_pages_success_basic(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful search_pages with a basic CQL query."""
    request_payload = {
        "tool_name": "search_pages",
        "inputs": {
            "cql": MOCK_CQL_QUERY,
            "limit": 10,
            "start": 0
        }
    }

    # Prepare mock data for individual pages that will be part of the search result
    mock_page1_data = get_mock_confluence_page_data(
        page_id=MOCK_SEARCH_PAGE_1_ID, 
        title=MOCK_SEARCH_PAGE_1_TITLE, 
        space_key=MOCK_SEARCH_PAGE_1_SPACE
    )
    mock_page2_data = get_mock_confluence_page_data(
        page_id=MOCK_SEARCH_PAGE_2_ID, 
        title=MOCK_SEARCH_PAGE_2_TITLE, 
        space_key=MOCK_SEARCH_PAGE_2_SPACE
    )
    
    # Prepare the overall mock API response for the CQL search
    mock_api_cql_response = get_mock_cql_search_results(
        cql_query=MOCK_CQL_QUERY,
        results=[mock_page1_data, mock_page2_data],
        limit=10,
        start=0,
        total_size=2 
    )

    confluence_client_mock.cql.return_value = mock_api_cql_response
    # Ensure the client.url is set for web_url construction in search_pages_logic
    confluence_client_mock.url = MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api" 

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    
    print(f"DEBUG test_search_pages_success_basic: Response Data: {response_data}") # Debugging output

    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "search_pages"
    
    outputs = response_data["outputs"]
    assert outputs["cql_query_used"] == MOCK_CQL_QUERY
    assert outputs["limit_used"] == 10
    assert outputs["start_used"] == 0
    assert outputs["count"] == 2  # Number of results in this response
    assert outputs["total_available"] == 2 # Total matching results on server

    assert len(outputs["results"]) == 2
    
    # Check first page
    page1_output = outputs["results"][0]
    assert page1_output["page_id"] == MOCK_SEARCH_PAGE_1_ID
    assert page1_output["title"] == MOCK_SEARCH_PAGE_1_TITLE
    assert page1_output["space_key"] == MOCK_SEARCH_PAGE_1_SPACE
    # Construct expected web_url based on logic in search_pages_logic and mock_page1_data
    expected_web_url1 = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_page1_data['_links']['webui']}"
    assert page1_output["web_url"] == expected_web_url1

    # Check second page
    page2_output = outputs["results"][1]
    assert page2_output["page_id"] == MOCK_SEARCH_PAGE_2_ID
    assert page2_output["title"] == MOCK_SEARCH_PAGE_2_TITLE
    assert page2_output["space_key"] == MOCK_SEARCH_PAGE_2_SPACE
    expected_web_url2 = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_page2_data['_links']['webui']}"
    assert page2_output["web_url"] == expected_web_url2
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.cql.assert_called_once_with(
        cql=MOCK_CQL_QUERY,
        limit=10,
        start=0,
        expand=None, # default
        excerpt=None  # default
    )

@pytest.mark.asyncio
async def test_search_pages_empty_results(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test search_pages when the CQL query yields no results."""
    empty_cql_query = "text ~ 'nonexistentuniquestring123xyz' and type=page"
    request_payload = {
        "tool_name": "search_pages",
        "inputs": {
            "cql": empty_cql_query,
            "limit": 10,
            "start": 0
        }
    }

    # Mock API response for an empty result set
    mock_api_empty_response = get_mock_cql_search_results(
        cql_query=empty_cql_query,
        results=[], # Empty list of results
        limit=10,
        start=0,
        total_size=0
    )

    confluence_client_mock.cql.return_value = mock_api_empty_response
    confluence_client_mock.url = MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200 # Should still be a success, just with no results
    response_data = response.json()
    
    print(f"DEBUG test_search_pages_empty_results: Response Data: {response_data}")

    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "search_pages"
    
    outputs = response_data["outputs"]
    assert outputs["cql_query_used"] == empty_cql_query
    assert outputs["limit_used"] == 10
    assert outputs["start_used"] == 0
    assert outputs["count"] == 0  # No results in this response
    assert outputs["total_available"] == 0 # No results on server
    assert len(outputs["results"]) == 0
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.cql.assert_called_once_with(
        cql=empty_cql_query,
        limit=10,
        start=0,
        expand=None,
        excerpt=None
    )

@pytest.mark.asyncio
async def test_search_pages_api_error(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test search_pages when the Confluence API cql call raises an unexpected error."""
    error_cql_query = "label = 'cause-api-error'"
    request_payload = {
        "tool_name": "search_pages",
        "inputs": {"cql": error_cql_query} # Using defaults for limit/start
    }

    # Simulate an API error
    # For atlassian-python-api, errors are often subclasses of requests.exceptions.HTTPError
    # or a custom AtlassianError. We'll use a generic RuntimeError for simplicity here,
    # as the logic in search_pages_logic should catch generic Exception.
    simulated_error = RuntimeError("Simulated Confluence API Error during CQL search")
    confluence_client_mock.cql.side_effect = simulated_error
    confluence_client_mock.url = MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 500 # As converted by main.py's/search_pages_logic generic exception handler
    response_data = response.json()
    
    print(f"DEBUG test_search_pages_api_error: Response Data: {response_data}")

    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "search_pages"
    assert "RuntimeError: Error during CQL search:" in response_data["error_message"]
    assert "Simulated Confluence API Error during CQL search" in response_data["error_message"]
    # The error type in main.py for generic exceptions is "InternalServerError" after the logic in search_pages_logic converts it.
    # The search_pages_logic itself raises an HTTPException for caught errors.
    assert response_data["error_type"] == "HTTPException" 
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.cql.assert_called_once_with(
        cql=error_cql_query,
        limit=25, # Default from SearchPagesInput schema
        start=0,  # Default from SearchPagesInput schema
        expand=None,
        excerpt=None
    )
