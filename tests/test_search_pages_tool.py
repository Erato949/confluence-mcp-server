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
    assert "RuntimeError: Error during CQL search: Simulated Confluence API Error during CQL search" in response_data["error_message"]
    assert response_data["error_type"] == "HTTPException" 
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.cql.assert_called_once_with(
        cql=error_cql_query,
        limit=25, # Default from SearchPagesInput schema
        start=0,  # Default from SearchPagesInput schema
        expand=None,
        excerpt=None
    )

@pytest.mark.asyncio
async def test_search_pages_with_expand_and_excerpt(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test search_pages with 'expand' and 'excerpt' parameters."""
    cql_query = "text ~ 'documentation' and type=page"
    expand_options = "body.storage,version" # CHANGED: Now a string
    excerpt_strategy = "highlight"
    
    request_payload = {
        "tool_name": "search_pages",
        "inputs": {
            "cql": cql_query,
            "limit": 1,
            "start": 0,
            "expand": expand_options, # This will now pass the string
            "excerpt": excerpt_strategy
        }
    }

    # Prepare mock results that would reflect expanded data and an excerpt
    # For simplicity, we'll assume the mock generator can handle this.
    # In a real scenario, you might need to adjust get_mock_cql_search_results
    # or create a more specific mock response for this test.
    mock_results = [
        {
            "id": "789012",
            "type": "page",
            "status": "current",
            "title": "Page with Expanded View",
            "space": {"key": "TEST", "name": "Test Space"},
            "version": {"number": 3, "when": "2023-01-03T00:00:00.000Z"},
            "body": {
                "storage": {
                    "value": "<p>This is the storage format content.</p>",
                    "representation": "storage"
                },
                "view": {
                    "value": "<p>This is the full <b>view</b> of the page content with documentation.</p>",
                    "representation": "view" 
                }
            },
            "_links": {"webui": "/display/TEST/Page+With+Expanded+View", "self": MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api/content/789012"},
            "excerpt": "highlighted documentation excerpt" # Assuming the API would return this
        }
    ]
    
    mock_api_response = get_mock_cql_search_results(
        cql_query=cql_query,
        results=mock_results,
        limit=1,
        start=0,
        total_size=1
    )

    confluence_client_mock.cql.return_value = mock_api_response
    confluence_client_mock.url = MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    # Explicitly assert how the mock cql method was called by the logic
    confluence_client_mock.cql.assert_called_once_with(
        cql=cql_query,
        limit=1,
        start=0,
        expand='body.storage,version', # Corrected: expand is a string
        excerpt=excerpt_strategy
    )

    assert response.status_code == 200
    response_data = response.json()
    print(f"DEBUG test_search_pages_with_expand_and_excerpt: Response Data: {response_data}")

    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "search_pages"
    
    outputs = response_data["outputs"]
    assert outputs["cql_query_used"] == cql_query
    assert outputs["limit_used"] == 1
    assert outputs["start_used"] == 0
    assert outputs["expand_used"] == expand_options
    assert outputs["excerpt_used"] == excerpt_strategy
    assert outputs["count"] == 1
    assert outputs["total_available"] == 1
    assert len(outputs["results"]) == 1
    
    mock_get_client_func.assert_called_once()
    # Check if the returned result reflects the expanded data (e.g., body.view exists)
    # and includes the excerpt. This depends on how get_mock_cql_search_results structures
    # the mock data and how SearchedPageSchema serializes it.
    # We'll assume SearchedPageSchema includes 'body' and 'excerpt' if present.
    first_result = outputs["results"][0]
    assert "content" in first_result
    assert first_result["content"] == "<p>This is the storage format content.</p>" # Cascade: New assertion based on body.storage
    
    assert "version" in first_result
    assert first_result["version"] == 3
    
    # The field 'content_preview' does not exist in SearchedPageSchema.
    # 'content' holds body.storage and 'excerpt_highlight' holds the excerpt.
    assert "excerpt_highlight" in first_result

@pytest.mark.asyncio
async def test_search_pages_invalid_cql_syntax(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test search_pages when the Confluence API reports an invalid CQL syntax."""
    invalid_cql_query = "label ==== 'bad-syntax'"  # Example of invalid CQL
    request_payload = {
        "tool_name": "search_pages",
        "inputs": {"cql": invalid_cql_query}
    }

    # Simulate an API error due to bad CQL.
    # The atlassian-python-api might raise various exceptions, often HTTPError from requests.
    # For this test, we'll use a generic Exception to simulate a server-side rejection of CQL.
    # In a real scenario, Confluence might return a 400 Bad Request.
    # Our search_pages_logic catches generic Exception and converts to HTTPException 500.
    simulated_api_error = Exception("Confluence API: Invalid CQL syntax provided.")
    confluence_client_mock.cql.side_effect = simulated_api_error
    confluence_client_mock.url = MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 500 # search_pages_logic converts generic exceptions to 500
    response_data = response.json()
    
    print(f"DEBUG test_search_pages_invalid_cql_syntax: Response Data: {response_data}")

    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "search_pages"
    assert "Exception: Error during CQL search: Confluence API: Invalid CQL syntax provided." in response_data["error_message"]
    assert response_data["error_type"] == "HTTPException" 
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.cql.assert_called_once_with(
        cql=invalid_cql_query,
        limit=ANY, # Default or whatever is sent
        start=ANY,
        expand=ANY,
        excerpt=ANY
    )

@pytest.mark.parametrize(
    "invalid_input, expected_error_loc_suffix, expected_error_msg_part",
    [
        # Type errors
        ({"cql": 123}, ("cql",), "Input should be a valid string"),
        ({"limit": "not-an-integer"}, ("limit",), "Input should be a valid integer, unable to parse string as an integer"), 
        ({"start": "not-an-integer"}, ("start",), "Input should be a valid integer, unable to parse string as an integer"), 
        ({"expand": ["invalid", "list"]}, ("expand",), "Input should be a valid string"), # expand is string
        ({"excerpt": 123}, ("excerpt",), "Input should be a valid string"), # excerpt is string enum

        # Value errors (from Pydantic constraints)
        ({"limit": 0}, ("limit",), "Input should be greater than 0"), # gt=0
        ({"limit": -1}, ("limit",), "Input should be greater than 0"), # gt=0
        ({"limit": 101}, ("limit",), "Input should be less than or equal to 100"), # le=100
        ({"start": -1}, ("start",), "Input should be greater than or equal to 0"), # ge=0
        ({"excerpt": "invalid_excerpt_value"}, ("excerpt",), "String should match pattern '^(highlight|none)$'"), # Literal error / Pydantic pattern message

        # Model validator errors (e.g. cql_and_space_key_exclusive)
        ({"cql": "some cql", "space_key_for_cql": "KEY", "title_for_cql": "Title"}, (), "Value error, If 'cql' is provided, 'space_key_for_cql' and 'title_for_cql' must not be present."),
        ({"space_key_for_cql": "KEY"}, (), "Value error, If 'cql' is provided, 'space_key_for_cql' and 'title_for_cql' must not be present."),
        ({"title_for_cql": "Title"}, (), "Value error, If 'cql' is provided, 'space_key_for_cql' and 'title_for_cql' must not be present.")
    ]
)
@pytest.mark.asyncio
async def test_search_pages_invalid_input_types(
    client: AsyncClient,
    confluence_client_mock: MagicMock, # Not used directly as validation happens before API call
    invalid_input: dict,
    expected_error_loc_suffix: tuple,
    expected_error_msg_part: str
):
    """Test search_pages with various invalid input data types."""
    base_inputs = {"cql": "type=page"} # Valid base
    request_payload = {
        "tool_name": "search_pages",
        "inputs": {**base_inputs, **invalid_input} # Merge to override with invalid part
    }
    
    # No need to mock confluence_client_mock.cql as validation should fail before it's called.
    # The get_confluence_client might still be called by the endpoint decorator.
    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock):
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation errors
    response_data = response.json()

    print(f"DEBUG test_search_pages_invalid_input_types ({invalid_input}): Response Data: {response_data}")

    assert response_data["status"] == "error"
    assert "error_message" in response_data
    assert response_data["error_type"] == "InputValidationError"

    error_message = response_data["error_message"]
    # Expected format: "Input validation failed for tool 'search_pages'. Details: '{field_or_model}': {message}"
    # or for model validation: "Input validation failed for tool 'search_pages'. Details: model: Value error, {message}"
    assert f"Input validation failed for tool 'search_pages'. Details: " in error_message

    if expected_error_loc_suffix:  # Field-specific error
        # e.g. ('limit',)
        loc_repr = f"'{expected_error_loc_suffix[0]}':"
        expected_detail_substring = f"{loc_repr} {expected_error_msg_part}"
    else:  # Model-level error (from model_validator, loc is empty)
        # main.py uses '' as the key for model-level errors when error['loc'] is empty.
        # expected_error_msg_part from parameters like "Value error, If 'cql' is provided..."
        loc_repr = "'':"
        expected_detail_substring = f"{loc_repr} {expected_error_msg_part}"

    assert expected_detail_substring in error_message, \
        f"Expected detail '{expected_detail_substring}' not found in error message '{error_message}' for input {invalid_input}"
