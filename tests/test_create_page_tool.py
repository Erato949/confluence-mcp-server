# tests/test_create_page_tool.py

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
import os # For accessing environment variables if needed for CONFLUENCE_URL

# Assuming your FastAPI app instance is named 'app' in 'confluence_mcp_server.main'
# and CONFLUENCE_URL is accessible or mockable for tests.

BASE_CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "http://test-confluence.com") # Get from env or use a default for tests

@pytest.mark.asyncio
async def test_create_page_success_top_level(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful creation of a top-level page."""
    tool_name = "create_page"
    mock_page_id = 12345
    mock_title = "My New Test Page"
    mock_space_key = "TESTSPACE"
    mock_content = "<p>This is a test page content.</p>"

    inputs = {
        "space_key": mock_space_key,
        "title": mock_title,
        "content": mock_content,
        "parent_page_id": None  # Explicitly None for top-level
    }

    # Mock the response from confluence_client.create_page
    mock_api_response = {
        "id": str(mock_page_id),  # Confluence API often returns ID as string
        "title": mock_title,
        "space": {"key": mock_space_key}, # Though not directly used by logic, good to have for realism
        "version": {"number": 1, "message": "", "minorEdit": False},
        "status": "current",
        "_links": {
            "webui": f"/display/{mock_space_key}/My+New+Test+Page",
            "self": f"{BASE_CONFLUENCE_URL}/rest/api/content/{mock_page_id}"
        }
    }
    confluence_client_mock.create_page.return_value = mock_api_response

    execute_payload = {
        "tool_name": tool_name,
        "inputs": inputs
    }

    response = await client.post("/execute", json=execute_payload)

    print(f"Test Response Status: {response.status_code}")
    print(f"Test Response JSON: {response.json()}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "success"
    assert "outputs" in response_data

    outputs = response_data["outputs"]
    assert outputs["page_id"] == mock_page_id
    assert outputs["title"] == mock_title
    assert outputs["space_key"] == mock_space_key
    assert outputs["version"] == 1
    assert outputs["status"] == "current"
    assert outputs["url"] == f"{BASE_CONFLUENCE_URL.rstrip('/')}/display/{mock_space_key}/My+New+Test+Page"

    # Verify the mock was called correctly
    confluence_client_mock.create_page.assert_called_once_with(
        space=mock_space_key,
        title=mock_title,
        body=mock_content,
        parent_id=None,
        type='page',
        representation='storage',
        editor='v2'
    )

@pytest.mark.asyncio
async def test_create_page_success_child_page(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful creation of a page as a child of another page."""
    tool_name = "create_page"
    mock_page_id = 56789
    mock_parent_page_id = 12345 # Assuming parent exists
    mock_title = "My New Child Page"
    mock_space_key = "TESTSPACE"
    mock_content = "<p>This is a child page content.</p>"

    inputs = {
        "space_key": mock_space_key,
        "title": mock_title,
        "content": mock_content,
        "parent_page_id": mock_parent_page_id
    }

    mock_api_response = {
        "id": str(mock_page_id),
        "title": mock_title,
        "space": {"key": mock_space_key},
        "ancestors": [{"id": str(mock_parent_page_id)}], # Indicate parentage
        "version": {"number": 1, "message": "", "minorEdit": False},
        "status": "current",
        "_links": {
            "webui": f"/display/{mock_space_key}/My+New+Child+Page",
            "self": f"{BASE_CONFLUENCE_URL}/rest/api/content/{mock_page_id}"
        }
    }
    confluence_client_mock.create_page.return_value = mock_api_response

    execute_payload = {
        "tool_name": tool_name,
        "inputs": inputs
    }

    response = await client.post("/execute", json=execute_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == mock_page_id
    assert outputs["title"] == mock_title
    assert outputs["space_key"] == mock_space_key
    assert outputs["version"] == 1
    assert outputs["status"] == "current"
    assert outputs["url"] == f"{BASE_CONFLUENCE_URL.rstrip('/')}/display/{mock_space_key}/My+New+Child+Page"

    confluence_client_mock.create_page.assert_called_once_with(
        space=mock_space_key,
        title=mock_title,
        body=mock_content,
        parent_id=str(mock_parent_page_id), # Ensure parent_id is string if API expects it
        type='page',
        representation='storage',
        editor='v2'
    )

@pytest.mark.parametrize(
    "invalid_input, expected_error_loc_suffix, expected_error_msg_part",
    [
        ({"title": "Test", "content": "Content"}, "space_key", "Field required"), # Missing space_key
        ({"space_key": "SP", "content": "Content"}, "title", "Field required"),     # Missing title
        ({"space_key": "SP", "title": "Test"}, "content", "Field required"),       # Missing content
        ({"space_key": "SP", "title": "Test", "content": "C", "parent_page_id": "not_an_int"}, "parent_page_id", "Input should be a valid integer"), # Invalid parent_page_id type
    ]
)
@pytest.mark.asyncio
async def test_create_page_invalid_inputs(client: AsyncClient, confluence_client_mock: MagicMock, invalid_input: dict, expected_error_loc_suffix: str, expected_error_msg_part: str):
    """Test create_page tool with various invalid inputs."""
    tool_name = "create_page"
    
    # Base valid input - we'll override parts of this with invalid_input
    base_inputs = {
        "space_key": "VALIDSPACE",
        "title": "Valid Title",
        "content": "<p>Valid Content</p>",
        "parent_page_id": None
    }
    
    # Construct the actual inputs for this test case
    current_inputs = base_inputs.copy()
    # Remove keys from current_inputs if they are meant to be missing in invalid_input
    # This ensures that if invalid_input = {"title": "T"}, it means space_key and content are MISSING, not taken from base_inputs.
    # However, for this test, invalid_input directly provides the field that's problematic or omits the required one.
    
    # A more direct way for these specific test cases:
    # If a key is in invalid_input, use its value. If a key is *missing* from invalid_input that's *required* by the schema, Pydantic handles it.
    # For cases where we test *missing* fields, invalid_input itself will be incomplete.
    # For cases testing *wrong type*, invalid_input provides the bad value.

    final_inputs = {k: v for k, v in invalid_input.items() if v is not None} # Use only provided invalid inputs
    # For missing field tests, final_inputs will be {'title': 'Test', 'content': 'Content'} for the first case for example.

    execute_payload = {
        "tool_name": tool_name,
        "inputs": final_inputs # Use the specifically crafted invalid input
    }

    response = await client.post("/execute", json=execute_payload)

    print(f"Test Invalid Input: {final_inputs}")
    print(f"Test Response Status: {response.status_code}")
    print(f"Test Response JSON: {response.json()}")

    assert response.status_code == 422  # HTTP 422 Unprocessable Entity for validation errors
    response_data = response.json()
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError"
    assert "validation_details" in response_data

    validation_errors = response_data["validation_details"]
    assert isinstance(validation_errors, list)
    assert len(validation_errors) > 0

    # Check if the expected error is present in the validation details
    found_error = False
    for error in validation_errors:
        # error['loc'] is a list, e.g., ['body', 'inputs', 'space_key']
        # We are interested in the last part for field-specific errors
        if error['loc'][-1] == expected_error_loc_suffix and expected_error_msg_part in error['msg']:
            found_error = True
            break
    assert found_error, f"Expected error for '{expected_error_loc_suffix}' with message part '{expected_error_msg_part}' not found in {validation_errors}"

    # Ensure Confluence API was not called
    confluence_client_mock.create_page.assert_not_called()

@pytest.mark.asyncio
async def test_create_page_api_error(client: AsyncClient, confluence_client_mock: MagicMock):
    """Test handling of an API error during page creation."""
    tool_name = "create_page"
    inputs = {
        "space_key": "TESTSPACE",
        "title": "API Error Test Page",
        "content": "<p>Content</p>",
        "parent_page_id": None
    }

    # Simulate an API error
    # The atlassian-python-api might raise various exceptions, 
    # often subclasses of requests.exceptions.HTTPError, or its own custom exceptions.
    # We'll use a generic RuntimeError for simplicity, as our logic catches Exception.
    error_message = "Simulated Confluence API Error during page creation"
    confluence_client_mock.create_page.side_effect = RuntimeError(error_message)

    execute_payload = {
        "tool_name": tool_name,
        "inputs": inputs
    }

    response = await client.post("/execute", json=execute_payload)

    assert response.status_code == 500 # Or appropriate error code based on main.py's handling
    response_data = response.json()
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException" # Changed from ToolLogicError
    expected_api_error_detail = f"Server Error (RuntimeError): Error during page creation: {error_message}"
    assert response_data["error_message"] == expected_api_error_detail

    confluence_client_mock.create_page.assert_called_once()
