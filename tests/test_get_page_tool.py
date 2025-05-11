import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, ANY # Add ANY for more flexible mocking if needed

# Import constants, helpers, and fixtures from conftest
from .conftest import (
    MOCK_PAGE_ID,
    MOCK_PAGE_TITLE,
    MOCK_SPACE_KEY,
    MOCK_PAGE_STATUS,
    MOCK_CONFLUENCE_WEB_BASE_URL,
    MOCK_NON_EXISTENT_PAGE_ID,
    MOCK_PAGE_ID_NO_SPACE_TITLE_LOOKUP,
    MOCK_PAGE_ID_MINIMAL_CONTENT,
    MOCK_MINIMAL_PAGE_TITLE,
    MOCK_MINIMAL_SPACE_KEY,
    MOCK_EXPAND_PARAMS,
    get_mock_confluence_page_data,
    confluence_client_mock
)

@pytest.mark.asyncio
async def test_get_page_success(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval of a page by ID."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": MOCK_PAGE_ID}
    }
    mock_api_response = get_mock_confluence_page_data()

    confluence_client_mock.get_page_by_id.return_value = mock_api_response
    # Simulate the structure of client.url for web_url construction in page_actions
    # The logic in page_actions uses client.url.rstrip('/rest/api').rstrip('/') + '/wiki'
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api" 

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "Get_Page"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == MOCK_PAGE_ID
    assert outputs["title"] == MOCK_PAGE_TITLE
    assert outputs["space_key"] == MOCK_SPACE_KEY
    assert outputs["status"] == MOCK_PAGE_STATUS
    # Use the webui link from the mock_api_response as the source of truth for the path
    expected_web_url = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_api_response['_links']['webui']}"
    assert outputs["web_url"] == expected_web_url
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=MOCK_PAGE_ID, expand=None)

@pytest.mark.asyncio
async def test_get_page_with_expand_success(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval with expand parameter."""
    expand_params = "body.storage,version"
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": MOCK_PAGE_ID, "expand": expand_params}
    }
    mock_api_response = get_mock_confluence_page_data(expand=expand_params)

    confluence_client_mock.get_page_by_id.return_value = mock_api_response
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == MOCK_PAGE_ID
    assert outputs["content"] == mock_api_response['body']['storage']['value']
    assert outputs["version"] == mock_api_response['version']['number']
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=MOCK_PAGE_ID, expand=expand_params)

@pytest.mark.asyncio
async def test_get_page_not_found(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool when the page ID is not found."""
    non_existent_page_id = 99999
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": non_existent_page_id}
    }
    
    confluence_client_mock.get_page_by_id.return_value = None # Simulate API not finding the page
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["status"] == "error"
    assert f"Page with ID {non_existent_page_id} not found" in response_data["error_message"]
    assert response_data["error_type"] == "HTTPException" # As raised by get_page_logic
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=non_existent_page_id, expand=None)

@pytest.mark.asyncio
async def test_get_page_invalid_input_type(client: AsyncClient):
    """Test Get_Page tool with invalid input type for page_id."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": "not_an_integer"}
    }
    # No mocking needed as validation happens before API call attempt
    response = await client.post("/execute", json=request_payload)
    
    assert response.status_code == 422 # Changed from 400
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "Get_Page" # Ensure tool_name is in error response
    assert "Input validation failed for tool 'Get_Page'" in response_data["error_message"]
    assert "page_id" in response_data["error_message"] 
    assert "Input should be a valid integer" in response_data["error_message"] # Pydantic's specific message part
    assert response_data["error_type"] == "InputValidationError"

@pytest.mark.asyncio
async def test_get_page_api_error(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool when the Confluence API call raises an unexpected error."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": MOCK_PAGE_ID}
    }

    confluence_client_mock.get_page_by_id.side_effect = RuntimeError("Simulated API error")
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 500 # As converted by main.py's generic exception handler
    response_data = response.json()
    assert response_data["status"] == "error"
    # The error message from main.py's generic handler might be "An unexpected error occurred while executing Get_Page."
    # or include the exception string. Let's be a bit general.
    assert "An unexpected error occurred" in response_data["error_message"] 
    assert "Simulated API error" in response_data["error_message"] # page_actions.py wraps str(e)
    assert response_data["error_type"] == "HTTPException" # get_page_logic converts it to HTTPException(500)
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=MOCK_PAGE_ID, expand=None)

# <START OF NEW TEST CASES>

@pytest.mark.asyncio
async def test_get_page_by_space_key_and_title_success(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval of a page by space_key and title."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"space_key": MOCK_SPACE_KEY, "title": "Test Page For SpaceKey Lookup"}
    }
    # Use the existing mock data structure, but assume get_page_by_title returns it
    mock_api_response = get_mock_confluence_page_data(page_id=MOCK_PAGE_ID, expand=None) 
    # Adjust title in mock if necessary for this specific lookup
    mock_api_response["title"] = "Test Page For SpaceKey Lookup" 

    confluence_client_mock.get_page_by_title.return_value = mock_api_response
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == MOCK_PAGE_ID # get_mock_confluence_page_data provides this
    assert outputs["title"] == "Test Page For SpaceKey Lookup"
    assert outputs["space_key"] == MOCK_SPACE_KEY
    # Use the webui link from the mock_api_response as the source of truth for the path
    expected_web_url = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_api_response['_links']['webui']}"
    assert outputs["web_url"] == expected_web_url
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_title.assert_called_once_with(space=MOCK_SPACE_KEY, title="Test Page For SpaceKey Lookup", expand=None)


@pytest.mark.asyncio
async def test_get_page_by_space_key_and_title_not_found(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool when page by space_key and title is not found."""
    non_existent_title = "This Title Does Not Exist In The Mocked Space"
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"space_key": MOCK_SPACE_KEY, "title": non_existent_title}
    }
    
    confluence_client_mock.get_page_by_title.return_value = None # Simulate API not finding the page
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["status"] == "error"
    assert f"Page with title '{non_existent_title}' in space '{MOCK_SPACE_KEY}' not found" in response_data["error_message"]
    assert response_data["error_type"] == "HTTPException"
    
    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_title.assert_called_once_with(space=MOCK_SPACE_KEY, title=non_existent_title, expand=None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_payload, expected_error_message_part",
    [
        ({"page_id": MOCK_PAGE_ID, "space_key": MOCK_SPACE_KEY}, "If 'page_id' is provided, 'space_key' and 'title' must not be provided."),
        ({"page_id": MOCK_PAGE_ID, "title": "Test Page For SpaceKey Lookup"}, "If 'page_id' is provided, 'space_key' and 'title' must not be provided."),
        ({"page_id": MOCK_PAGE_ID, "space_key": MOCK_SPACE_KEY, "title": "Test Page For SpaceKey Lookup"}, "If 'page_id' is provided, 'space_key' and 'title' must not be provided."),
        ({"space_key": MOCK_SPACE_KEY}, "'title' must be provided if 'space_key' is provided and 'page_id' is not."),
        ({"title": "Test Page For SpaceKey Lookup"}, "'space_key' must be provided if 'title' is provided and 'page_id' is not."),
        ({}, "Either 'page_id' or both 'space_key' and 'title' must be provided."), # Neither provided
        ({"space_key": "  ", "title": "Valid Title"}, "'space_key' must be provided if 'title' is provided and 'page_id' is not."), # Empty space_key
        ({"space_key": "ValidKey", "title": "  "}, "'title' must be provided if 'space_key' is provided and 'page_id' is not."), # Empty title
    ]
)
async def test_get_page_invalid_input_combinations(client: AsyncClient, invalid_payload: dict, expected_error_message_part: str):
    """Test Get_Page tool with various invalid combinations of input parameters."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": invalid_payload
    }
    response = await client.post("/execute", json=request_payload)
    
    assert response.status_code == 422
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "Get_Page"
    assert "Input validation failed for tool 'Get_Page'" in response_data["error_message"]
    assert expected_error_message_part in response_data["error_message"]
    assert response_data["error_type"] == "InputValidationError"

# <END OF NEW TEST CASES>

@pytest.mark.asyncio
async def test_get_page_minimal_content_success(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool for a page that exists but has no content or version, even when expanded."""
    page_id_to_test = MOCK_PAGE_ID_MINIMAL_CONTENT
    mock_page_data_minimal = get_mock_confluence_page_data(
        page_id=page_id_to_test,
        title=MOCK_MINIMAL_PAGE_TITLE,
        space_key=MOCK_MINIMAL_SPACE_KEY,
        has_content=False,
        has_version=False
    )

    confluence_client_mock.get_page_by_id.return_value = mock_page_data_minimal
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {
            "page_id": page_id_to_test,
            "expand": "body.storage,version" # Requesting them, but they won't be there
        }
    }
    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "Get_Page"
    outputs = response_data["outputs"]

    assert outputs["page_id"] == page_id_to_test
    assert outputs["title"] == MOCK_MINIMAL_PAGE_TITLE
    assert outputs["space_key"] == MOCK_MINIMAL_SPACE_KEY
    # Use the webui link from the mock_page_data_minimal as the source of truth for the path
    expected_web_url = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_page_data_minimal['_links']['webui']}"
    assert outputs["web_url"] == expected_web_url
    assert outputs["content"] is None
    assert outputs["version"] is None

    mock_get_client_func.assert_called_once()
    confluence_client_mock.get_page_by_id.assert_called_once_with(
        page_id=page_id_to_test,
        expand="body.storage,version"
    )

@pytest.mark.asyncio
async def test_get_page_minimal_content_no_version_or_body_expand(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page with minimal content (no body/version in expand, or they don't exist on page)."""
    page_id_to_test = MOCK_PAGE_ID_MINIMAL_CONTENT

    # Prepare mock data that reflects a page with no content or version info available
    # even if requested via expand, or expand wasn't asking for them.
    mock_page_data_minimal = get_mock_confluence_page_data(
        page_id=page_id_to_test,
        title=MOCK_MINIMAL_PAGE_TITLE,
        space_key=MOCK_MINIMAL_SPACE_KEY,
        expand=None, # or "other,fields" not including body/version
        has_content=False, 
        has_version=False
    )

    confluence_client_mock.get_page_by_id.return_value = mock_page_data_minimal
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": page_id_to_test, "expand": "some.other.field"} # Test with an expand not asking for body/version
    }

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()["outputs"]
    assert response_data["page_id"] == page_id_to_test
    assert response_data["title"] == MOCK_MINIMAL_PAGE_TITLE
    assert response_data["space_key"] == MOCK_MINIMAL_SPACE_KEY
    # Use the webui link from the mock_page_data_minimal as the source of truth for the path
    expected_web_url = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_page_data_minimal['_links']['webui']}"
    assert response_data["web_url"] == expected_web_url
    assert response_data["content"] is None
    assert response_data["version"] is None

    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=page_id_to_test, expand="some.other.field")
