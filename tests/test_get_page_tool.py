# tests/test_get_page_tool.py

import pytest
from httpx import AsyncClient
from unittest.mock import patch

# Mock data for a Confluence page
MOCK_PAGE_ID = 12345
MOCK_PAGE_TITLE = "Test Page Title"
MOCK_SPACE_KEY = "TESTSPACE"
MOCK_PAGE_STATUS = "current"
MOCK_PAGE_CONTENT = "<p>This is test page content.</p>"
MOCK_PAGE_VERSION = 2
MOCK_WEB_UI_LINK_SUFFIX = f"/spaces/{MOCK_SPACE_KEY}/pages/{MOCK_PAGE_ID}"
MOCK_CONFLUENCE_INSTANCE_URL = "https://example.atlassian.net" # Simulates the base part of client.url
MOCK_CONFLUENCE_WEB_BASE_URL = f"{MOCK_CONFLUENCE_INSTANCE_URL}/wiki" # What the constructed web base URL should be

def get_mock_confluence_page_data(page_id=MOCK_PAGE_ID, expand: str = None):
    base_page = {
        "id": page_id,
        "title": MOCK_PAGE_TITLE,
        "status": MOCK_PAGE_STATUS,
        # Simulate structure where space key might be if 'space' is expanded or part of default return
        "space": {"key": MOCK_SPACE_KEY},
        "_links": {"webui": MOCK_WEB_UI_LINK_SUFFIX} # Usually a relative path
    }
    if expand:
        if "body.storage" in expand:
            base_page["body"] = {"storage": {"value": MOCK_PAGE_CONTENT}}
        if "version" in expand:
            base_page["version"] = {"number": MOCK_PAGE_VERSION}
    return base_page

@pytest.mark.asyncio
async def test_get_page_success(client: AsyncClient):
    """Test successful retrieval of a page by ID."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": MOCK_PAGE_ID}
    }
    mock_api_response = get_mock_confluence_page_data()

    with patch('confluence_mcp_server.main.confluence_client.get_page_by_id', return_value=mock_api_response) as mock_api_call, \
         patch('confluence_mcp_server.main.confluence_client.url', MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api") as mock_client_url:
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
    expected_web_url = f"{MOCK_CONFLUENCE_WEB_BASE_URL}{MOCK_WEB_UI_LINK_SUFFIX}"
    assert outputs["web_url"] == expected_web_url
    mock_api_call.assert_called_once_with(page_id=MOCK_PAGE_ID, expand=None)

@pytest.mark.asyncio
async def test_get_page_with_expand_success(client: AsyncClient):
    """Test successful retrieval with expand parameter."""
    expand_params = "body.storage,version"
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": MOCK_PAGE_ID, "expand": expand_params}
    }
    mock_api_response = get_mock_confluence_page_data(expand=expand_params)

    with patch('confluence_mcp_server.main.confluence_client.get_page_by_id', return_value=mock_api_response) as mock_api_call, \
         patch('confluence_mcp_server.main.confluence_client.url', MOCK_CONFLUENCE_INSTANCE_URL + "/rest/api") as mock_client_url:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == MOCK_PAGE_ID
    assert outputs["content"] == MOCK_PAGE_CONTENT
    assert outputs["version"] == MOCK_PAGE_VERSION
    mock_api_call.assert_called_once_with(page_id=MOCK_PAGE_ID, expand=expand_params)

@pytest.mark.asyncio
async def test_get_page_not_found(client: AsyncClient):
    """Test Get_Page tool when the page ID is not found."""
    non_existent_page_id = 99999
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": non_existent_page_id}
    }
    with patch('confluence_mcp_server.main.confluence_client.get_page_by_id', return_value=None) as mock_api_call:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["status"] == "error"
    assert f"Page with ID {non_existent_page_id} not found" in response_data["error_message"]
    assert response_data["error_type"] == "HTTPException"
    mock_api_call.assert_called_once_with(page_id=non_existent_page_id, expand=None)

@pytest.mark.asyncio
async def test_get_page_invalid_input_type(client: AsyncClient):
    """Test Get_Page tool with invalid input type for page_id."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": "not_an_integer"}
    }
    response = await client.post("/execute", json=request_payload)
    assert response.status_code == 400 
    response_data = response.json()
    assert response_data["status"] == "error"
    assert "Input validation failed" in response_data["error_message"]
    assert "page_id" in response_data["error_message"]
    assert response_data["error_type"] == "InputValidationError"

@pytest.mark.asyncio
async def test_get_page_api_error(client: AsyncClient):
    """Test Get_Page tool when the Confluence API call raises an unexpected error."""
    request_payload = {
        "tool_name": "Get_Page",
        "inputs": {"page_id": MOCK_PAGE_ID}
    }
    with patch('confluence_mcp_server.main.confluence_client.get_page_by_id', side_effect=RuntimeError("Simulated API error")) as mock_api_call:
        response = await client.post("/execute", json=request_payload)

    assert response.status_code == 500
    response_data = response.json()
    assert response_data["status"] == "error"
    assert "An unexpected error occurred" in response_data["error_message"]
    assert response_data["error_type"] == "HTTPException" # Logic converts to HTTPException(500)
    mock_api_call.assert_called_once_with(page_id=MOCK_PAGE_ID, expand=None)
