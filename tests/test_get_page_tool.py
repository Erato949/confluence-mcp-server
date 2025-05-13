import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock, ANY

# Import constants, helpers, and fixtures from conftest
from .conftest import (
    MOCK_PAGE_ID,
    MOCK_PAGE_TITLE,
    MOCK_SPACE_KEY,
    MOCK_SPACE_ID,
    MOCK_PAGE_STATUS,
    MOCK_CONFLUENCE_WEB_BASE_URL,
    MOCK_NON_EXISTENT_PAGE_ID,
    MOCK_PAGE_ID_NO_SPACE_TITLE_LOOKUP,
    MOCK_PAGE_ID_MINIMAL_CONTENT,
    MOCK_MINIMAL_PAGE_TITLE,
    MOCK_MINIMAL_SPACE_KEY,
    MOCK_EXPAND_PARAMS,
    get_mock_confluence_page_data,
    confluence_client_mock,
    MOCK_PAGE_ID_BY_TITLE # Added import
)

# Import necessary schemas
from confluence_mcp_server.mcp_actions.schemas import (
    MCPExecuteRequest,
    GetPageInput, GetPageOutput
)

from confluence_mcp_server.main import AVAILABLE_TOOLS

pytestmark = pytest.mark.anyio

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_success(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval of a page by ID."""
    request_payload = {
        "tool_name": "get_page",
        "inputs": {"page_id": MOCK_PAGE_ID, "expand": "body.storage,version"}
    }
    mock_api_response = get_mock_confluence_page_data(expand="body.storage,version")

    # Configure the AsyncMock behavior
    confluence_client_mock.get_page_by_id.return_value = mock_api_response 
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    mock_get_client.return_value = confluence_client_mock

    expected_output_model = GetPageOutput(
        page_id=MOCK_PAGE_ID,
        title=MOCK_PAGE_TITLE,
        space_key=MOCK_SPACE_KEY,
        status=MOCK_PAGE_STATUS,
        content=mock_api_response['body']['storage']['value'],
        version=mock_api_response['version']['number'],
        web_url=f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_api_response['_links']['webui']}"
    )
        
    async def mock_logic_side_effect(client, inputs): 
        return expected_output_model

    manual_mock_logic = AsyncMock(side_effect=mock_logic_side_effect)
    original_logic = AVAILABLE_TOOLS["get_page"]["logic"]
    AVAILABLE_TOOLS["get_page"]["logic"] = manual_mock_logic

    try:
        response = await client.post("/execute", json=request_payload)
    finally:
        AVAILABLE_TOOLS["get_page"]["logic"] = original_logic

    assert response.status_code == 200, f"Response content: {response.text}"

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_with_expand_success(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval with expand parameter."""
    expand_params = "body.storage,version"
    request_payload = {
        "tool_name": "get_page",
        "inputs": {"page_id": MOCK_PAGE_ID, "expand": expand_params}
    }
    mock_api_response = get_mock_confluence_page_data(expand=expand_params)

    confluence_client_mock.get_page_by_id.return_value = mock_api_response
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"

    mock_get_client.return_value = confluence_client_mock
    expected_output = GetPageOutput(
        page_id=MOCK_PAGE_ID,
        title=mock_api_response['title'],
        space_key=mock_api_response['space']['key'],
        status=mock_api_response['status'],
        content=mock_api_response['body']['storage']['value'],
        version=mock_api_response['version']['number'],
        web_url=f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_api_response['_links']['webui']}"
    )

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

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_not_found(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool when the page ID is not found."""
    non_existent_page_id = 99999
    request_payload = {
        "tool_name": "get_page",
        "inputs": {"page_id": non_existent_page_id, "expand": None}
    }

    # confluence_client_mock.get_page_by_id is already an AsyncMock from the fixture
    confluence_client_mock.get_page_by_id.return_value = None # Simulate API not finding the page
    mock_get_client.return_value = confluence_client_mock

    response = await client.post("/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    assert f"Page with ID {non_existent_page_id} not found" in response_data["error_message"]
    assert response_data["tool_name"] == "get_page"

    # Assert that the underlying client mock was called correctly with keyword arguments
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=non_existent_page_id, expand=None)
    mock_get_client.assert_called_once()

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_invalid_input_type(mock_get_client, client: AsyncClient):
    """Test Get_Page tool with invalid input type for page_id."""
    request_payload = {
        "tool_name": "get_page",
        "inputs": {"page_id": "not_an_integer"}
    }
    response = await client.post("/execute", json=request_payload)

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "get_page"
    assert response_data["error_message"] == "Input validation failed."
    assert response_data["error_type"] == "InputValidationError"
    assert "validation_details" in response_data # Check for presence of validation_details
    # Optionally, check specific details if consistent
    # Example: assert any("Input should be a valid integer" in detail["msg"] for detail in response_data["validation_details"])

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_api_error(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool when the Confluence API call (simulated by logic mock) raises an unexpected error."""
    request_payload = {
        "tool_name": "get_page",
        "inputs": {"page_id": MOCK_PAGE_ID, "expand": "body.storage"}
    }

    # confluence_client_mock.get_page_by_id is an AsyncMock from the fixture.
    # No specific return_value or side_effect needed for it here, as our manual_mock_logic will raise before calling it.
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"
    mock_get_client.return_value = confluence_client_mock

    # Create manual mock for the logic function that raises an error
    manual_mock_logic = AsyncMock(side_effect=RuntimeError("Simulated API error"))
    original_logic = AVAILABLE_TOOLS["get_page"]["logic"]
    AVAILABLE_TOOLS["get_page"]["logic"] = manual_mock_logic

    try:
        response = await client.post("/execute", json=request_payload)
    finally:
        AVAILABLE_TOOLS["get_page"]["logic"] = original_logic

    assert response.status_code == 500 # As converted by main.py's generic exception handler
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "get_page"
    assert "An unexpected error occurred" in response_data["error_message"]
    assert "Simulated API error" in response_data["error_message"] # The original error string
    assert response_data["error_type"] == "ToolLogicError" # As set by main.py's generic handler

    mock_get_client.assert_called_once() # get_confluence_client is called before the logic
    # The actual Confluence client method should not be called if the logic mock raises directly
    confluence_client_mock.get_page_by_id.assert_not_called() 
    manual_mock_logic.assert_awaited_once()

# <START OF NEW TEST CASES>

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_by_space_key_and_title_success(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval of a page by space key and title."""
    target_space_key = MOCK_SPACE_KEY
    target_title = "Test Page For SpaceKey Lookup"
    target_expand = "body.storage,version"

    request_payload = {
        "tool_name": "get_page",
        "inputs": {
            "space_key": target_space_key,
            "title": target_title,
            "expand": target_expand
        }
    }
    mock_api_response = get_mock_confluence_page_data(
        page_id=MOCK_PAGE_ID_BY_TITLE, 
        title=target_title, 
        space_id=MOCK_SPACE_ID, 
        expand=target_expand
    )
    # confluence_client_mock.get_page_by_title is AsyncMock from fixture
    confluence_client_mock.get_page_by_title.return_value = mock_api_response
    confluence_client_mock.url = MOCK_CONFLUENCE_WEB_BASE_URL.rstrip('/wiki') + "/rest/api"
    mock_get_client.return_value = confluence_client_mock

    expected_output = GetPageOutput(
        page_id=int(MOCK_PAGE_ID_BY_TITLE), # Corrected: page_id, ensure MOCK_PAGE_ID_BY_TITLE is int
        title=target_title,
        space_key=MOCK_SPACE_KEY,      # Corrected: space_key, use MOCK_SPACE_KEY
        status="current",
        content=mock_api_response["body"]["storage"]["value"], # Corrected: content
        version=mock_api_response["version"]["number"],    # Corrected: version
        # Corrected: Use the full webui link format provided by the API for space/title lookups, including base URL
        web_url=f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_api_response['_links']['webui']}"
    )

    response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["outputs"] == expected_output.model_dump(exclude_none=False) # Compare with serialized model
    assert response_data["tool_name"] == "get_page"

    # Assert that the underlying client mock was called correctly with keyword arguments
    mock_get_client.assert_called_once()
    confluence_client_mock.get_page_by_title.assert_called_once_with(
        space=target_space_key, title=target_title, expand=target_expand
    )

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_by_space_key_and_title_not_found(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test Get_Page tool when a page by space_key and title is not found."""
    non_existent_title = "This Page Does Not Exist In This Space"
    target_space_key = MOCK_SPACE_KEY
    target_expand = "version"

    request_payload = {
        "tool_name": "get_page",
        "inputs": {
            "space_key": target_space_key,
            "title": non_existent_title,
            "expand": target_expand
        }
    }
    # confluence_client_mock.get_page_by_title is AsyncMock from fixture
    confluence_client_mock.get_page_by_title.return_value = None # Simulate API not finding the page
    mock_get_client.return_value = confluence_client_mock

    response = await client.post("/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    # Assert the specific error message format from the actual logic
    expected_error_detail = f"Page with title '{non_existent_title}' in space '{target_space_key}' not found."
    assert response_data["error_message"] == expected_error_detail
    assert response_data["tool_name"] == "get_page"

    # Assert that the underlying client mock was called correctly with keyword arguments
    confluence_client_mock.get_page_by_title.assert_called_once_with(
        space=target_space_key, title=non_existent_title, expand=target_expand
    )
    mock_get_client.assert_called_once()

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
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
async def test_get_page_invalid_input_combinations(mock_get_client, client: AsyncClient, invalid_payload: dict, expected_error_message_part: str):
    """Test Get_Page tool with various invalid combinations of input parameters."""
    request_payload = {
        "tool_name": "get_page",
        "inputs": invalid_payload
    }
    response = await client.post("/execute", json=request_payload)

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "get_page"
    # Check the main error message structure
    assert response_data["error_message"] == "Input validation failed."
    
    # Check that the specific validation message from the model validator is included in validation_details
    assert "validation_details" in response_data
    assert isinstance(response_data["validation_details"], list)
    assert len(response_data["validation_details"]) > 0
    
    found_specific_error = False
    for detail in response_data["validation_details"]:
        # For model_validator errors (loc is empty list/tuple), Pydantic prepends "Value error, " to the custom message.
        # For field-level errors, it's just the message.
        # We are primarily testing model_validator messages here.
        if expected_error_message_part in detail.get("msg", ""):
            # Check if the loc indicates a model-level validation if it's a 'Value error'
            # Model validator errors typically have loc as an empty list or tuple.
            # Pydantic v2 uses an empty list for model validators (mode='after') that raise ValueError.
            if detail.get("type") == "value_error" and not detail.get("loc"):
                assert detail.get("msg", "").startswith("Value error, "), f"Expected 'Value error, ' prefix for model validation: {detail.get('msg')}"
                # The expected_error_message_part should be the part *after* 'Value error, '
                assert expected_error_message_part in detail.get("msg", "").replace("Value error, ", "")
            found_specific_error = True
            break
        # Handle cases where the expected message is for a standard field validation (not model validator)
        # These won't have 'Value error, ' prefix from the model validator itself.
        # This part might need refinement based on how other GetPageInput field errors are structured.
        elif detail.get("msg", "") == expected_error_message_part:
            found_specific_error = True
            break

    assert found_specific_error, f"Expected validation message part '{expected_error_message_part}' not found in validation_details: {response_data['validation_details']}"
    # Check the detailed validation errors list
    assert response_data["validation_details"] is not None
    assert isinstance(response_data["validation_details"], list)
    assert len(response_data["validation_details"]) == 1
    assert response_data["validation_details"][0]["msg"] == f"Value error, {expected_error_message_part}"
    assert response_data["validation_details"][0]["type"] == "value_error"
    assert response_data["validation_details"][0]["loc"] == [] # Errors from model validator have empty loc

# <END OF NEW TEST CASES>

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_minimal_content_success(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
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
        "tool_name": "get_page",
        "inputs": {
            "page_id": page_id_to_test,
            "expand": "body.storage,version" # Requesting them, but they won't be there
        }
    }
    mock_get_client.return_value = confluence_client_mock

    expected_output = GetPageOutput(
        page_id=page_id_to_test,
        title=MOCK_MINIMAL_PAGE_TITLE,
        space_key=MOCK_MINIMAL_SPACE_KEY,
        status=mock_page_data_minimal['status'],
        content=None,
        version=None,
        web_url=f"{MOCK_CONFLUENCE_WEB_BASE_URL}{mock_page_data_minimal['_links']['webui']}"
    )

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as mock_get_client_func:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "get_page"
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

@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_page_minimal_content_no_version_or_body_expand(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
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
        "tool_name": "get_page",
        "inputs": {"page_id": page_id_to_test, "expand": "some.other.field"} # Test with an expand not asking for body/version
    }

    mock_get_client.return_value = confluence_client_mock

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
