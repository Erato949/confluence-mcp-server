import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from confluence_mcp_server.main import app # AVAILABLE_TOOLS is populated when app is imported
from confluence_mcp_server.mcp_actions.schemas import UpdatePageInput, UpdatePageOutput, MCPExecuteRequest

# Ensure the tool is registered before tests run
# This would typically be handled by the app startup, but explicitly ensure for testing context
# Removing this block as main.app import should trigger load_tools()
# if 'update_page' not in TOOL_REGISTRY: 
#     from confluence_mcp_server.mcp_actions.schemas import UpdatePageInput, UpdatePageOutput
#     from confluence_mcp_server.main import MCPToolSchema 
#     TOOL_REGISTRY['update_page'] = MCPToolSchema(
#         name="update_page",
#         description="Update an existing page in Confluence (title, content, or parent). Requires current page version for optimistic locking.",
#         input_schema=UpdatePageInput.model_json_schema(),
#         output_schema=UpdatePageOutput.model_json_schema()
#     )

client = TestClient(app)

@pytest.fixture
def confluence_client_mock():
    mock = MagicMock()
    # Mock the base URL attribute needed by get_confluence_page_url
    mock.url = "https://test.confluence.com"
    return mock

@pytest.fixture
def mock_auth_and_confluence_client(confluence_client_mock):
    # This fixture will patch get_confluence_client from main.py
    # The authenticate_confluence function does not exist in main.py and was causing an AttributeError.
    with patch('confluence_mcp_server.main.get_confluence_client', return_value=confluence_client_mock) as get_client_mock_object:
        # Yielding confluence_client_mock (the mock client instance),
        # None (in place of the removed auth_mock to maintain tuple size for unpacking),
        # and get_client_mock_object (the MagicMock object for the get_confluence_client patch).
        yield confluence_client_mock, None, get_client_mock_object


def test_update_page_success_title_only(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    page_id = "12345"
    current_version = 1
    new_title = "New Awesome Title"
    existing_content = "<p>This is the existing content.</p>"
    space_key = "TESTSPACE"
    expected_new_version = 2

    # Mock the response from client.get_page_by_id (called when content is not being updated)
    confluence_mock.get_page_by_id.return_value = {
        "id": page_id,
        "title": "Old Title", # This won't be used as new_title is provided
        "body": {
            "storage": {
                "value": existing_content,
                "representation": "storage"
            }
        },
        "version": {"number": current_version},
        "space": {"key": space_key} # Ensure space key is available for fallback
    }

    # Mock the response from client.update_page
    confluence_mock.update_page.return_value = {
        "id": page_id,
        "title": new_title,
        "space": {"key": space_key}, # Simulate space info in response
        "version": {"number": expected_new_version, "message": "Version updated"},
        "status": "current",
        "_links": {"webui": f"/spaces/{space_key}/pages/{page_id}/{new_title.replace(' ', '+')}"}
    }

    inputs = {
        "page_id": page_id,
        "title": new_title,
        "current_version_number": current_version
        # Content and parent_page_id are omitted
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "update_page"

    outputs = response_data["outputs"]
    assert outputs["page_id"] == page_id
    assert outputs["title"] == new_title
    assert outputs["space_key"] == space_key
    assert outputs["version"] == expected_new_version
    assert outputs["status"] == "current"
    assert outputs["url"] == f"https://test.confluence.com/spaces/{space_key}/pages/{page_id}/{new_title.replace(' ', '+')}"

    # Verify client.update_page was called correctly
    confluence_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=new_title,
        body=existing_content, # Logic should fetch existing content if not provided
        version=expected_new_version,
        representation="storage" # Should be set if body is present
    )
    confluence_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')


def test_update_page_success_content_only(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    page_id = "67890"
    current_version = 2
    existing_title = "Existing Page Title"
    new_content = "<p>This is the brand new, updated content!</p>"
    space_key = "PROJ"
    expected_new_version = 3

    # Mock the response from client.get_page_by_id (called when title is not being updated)
    confluence_mock.get_page_by_id.return_value = {
        "id": page_id,
        "title": existing_title,
        "body": {
            "storage": {
                "value": "<p>Old content here.</p>",
                "representation": "storage"
            }
        },
        "version": {"number": current_version},
        "space": {"key": space_key}
    }

    # Mock the response from client.update_page
    confluence_mock.update_page.return_value = {
        "id": page_id,
        "title": existing_title, # Title remains unchanged
        "space": {"key": space_key},
        "version": {"number": expected_new_version},
        "status": "current",
        "_links": {"webui": f"/spaces/{space_key}/pages/{page_id}/{existing_title.replace(' ', '+')}"}
    }

    inputs = {
        "page_id": page_id,
        "content": new_content,
        "current_version_number": current_version
        # Title and parent_page_id are omitted
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == page_id
    assert outputs["title"] == existing_title
    assert outputs["space_key"] == space_key
    assert outputs["version"] == expected_new_version
    assert outputs["url"] == f"https://test.confluence.com/spaces/{space_key}/pages/{page_id}/{existing_title.replace(' ', '+')}"

    confluence_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=existing_title, # Logic should fetch existing title
        body=new_content,
        version=expected_new_version,
        representation="storage"
    )
    confluence_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')


def test_update_page_success_title_and_content(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    page_id = "101112"
    current_version = 3
    new_title = "Completely Revamped Title"
    new_content = "<p>Fresh new content to match the new title!</p>"
    space_key = "DOCS"
    expected_new_version = 4

    # No need to mock get_page_by_id if both title and content are provided in input,
    # as the logic should not call it.

    # Mock the response from client.update_page
    confluence_mock.update_page.return_value = {
        "id": page_id,
        "title": new_title,
        "space": {"key": space_key},
        "version": {"number": expected_new_version},
        "status": "current",
        "_links": {"webui": f"/spaces/{space_key}/pages/{page_id}/{new_title.replace(' ', '+')}"}
    }

    inputs = {
        "page_id": page_id,
        "title": new_title,
        "content": new_content,
        "current_version_number": current_version
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == page_id
    assert outputs["title"] == new_title
    assert outputs["space_key"] == space_key
    assert outputs["version"] == expected_new_version
    assert outputs["url"] == f"https://test.confluence.com/spaces/{space_key}/pages/{page_id}/{new_title.replace(' ', '+')}"

    confluence_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=new_title,
        body=new_content,
        version=expected_new_version,
        representation="storage"
    )
    # Ensure get_page_by_id was NOT called
    confluence_mock.get_page_by_id.assert_not_called()


def test_update_page_success_parent_page_id_only(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    page_id = "131415"
    current_version = 1
    existing_title = "Child Page Title"
    existing_content = "<p>Some content.</p>"
    new_parent_page_id = "789"
    space_key = "TEAMSPACE"
    expected_new_version = 2

    # Mock get_page_by_id for fetching existing title and content
    confluence_mock.get_page_by_id.return_value = {
        "id": page_id,
        "title": existing_title,
        "body": {
            "storage": {
                "value": existing_content,
                "representation": "storage"
            }
        },
        "version": {"number": current_version},
        "space": {"key": space_key}
    }

    # Mock client.update_page response
    confluence_mock.update_page.return_value = {
        "id": page_id,
        "title": existing_title, # Title and content remain unchanged
        "space": {"key": space_key},
        "version": {"number": expected_new_version},
        "status": "current",
        "_links": {"webui": f"/spaces/{space_key}/pages/{page_id}/{existing_title.replace(' ', '+')}"},
        "ancestors": [{"id": new_parent_page_id}] # Simulate successful parent update in response
    }

    inputs = {
        "page_id": page_id,
        "parent_page_id": new_parent_page_id,
        "current_version_number": current_version
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    outputs = response_data["outputs"]
    assert outputs["page_id"] == page_id
    assert outputs["title"] == existing_title
    assert outputs["space_key"] == space_key
    assert outputs["version"] == expected_new_version

    confluence_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=existing_title,
        body=existing_content,
        version=expected_new_version,
        parent_id=new_parent_page_id, # Key assertion: parent_id is passed
        representation="storage"
    )
    confluence_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')


# --- Input Validation Tests ---

def test_update_page_input_validation_missing_page_id(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    inputs = {
        # "page_id": "123", # Missing
        "title": "Some Title",
        "current_version_number": 1
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError"
    assert "Input validation failed" in response_data["error_message"]
    assert response_data["validation_details"] is not None
    found_error = False
    for error in response_data["validation_details"]:
        if error["loc"] == ["page_id"] and error["type"] == "missing":
            found_error = True
            break
    assert found_error, "Specific error for missing page_id not found in validation_details"
    confluence_mock.update_page.assert_not_called()

def test_update_page_input_validation_missing_current_version_number(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    inputs = {
        "page_id": "123",
        "title": "Some Title"
        # "current_version_number": 1 # Missing
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError"
    assert "Input validation failed" in response_data["error_message"]
    assert response_data["validation_details"] is not None
    found_error = False
    for error in response_data["validation_details"]:
        if error["loc"] == ["current_version_number"] and error["type"] == "missing":
            found_error = True
            break
    assert found_error, "Specific error for missing current_version_number not found in validation_details"
    confluence_mock.update_page.assert_not_called()

def test_update_page_input_validation_no_updatable_fields(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    inputs = {
        "page_id": "123",
        "current_version_number": 1
        # No title, content, or parent_page_id provided
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError"
    assert "Input validation failed" in response_data["error_message"]

    # Check the specific message within validation_details
    assert any(
        "At least one of 'title', 'content', or 'parent_page_id' must be provided" in error.get('msg', '')
        for error in response_data.get("validation_details", [])
    )
    # assert "At least one of 'title', 'content', or 'parent_page_id' must be provided" in response_data["error_message"] # Check specific message part
    assert response_data["validation_details"] is not None
    found_value_error = False
    for error in response_data["validation_details"]:
        # For model_validator(mode='after') raising ValueError, Pydantic wraps it.
        # The 'loc' is often empty or relates to the whole model, and 'type' can be 'value_error'.
        # The exact 'msg' can also vary based on Pydantic version and how it's wrapped.
        # Let's check for a 'value_error' type and part of the message.
        if error["type"] == "value_error":
            # The specific message from our validator
            if "At least one of 'title', 'content', or 'parent_page_id' must be provided to update the page." in error["msg"]:
                found_value_error = True
                break
    assert found_value_error, "Specific value error for no updatable fields not found in validation_details"
    confluence_mock.update_page.assert_not_called()

# --- API Error Handling Tests ---

def test_update_page_api_error_generic(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    page_id = "err_123"
    current_version = 1
    title_update = "Attempting Update"

    # Configure the mock to raise a generic exception for update_page
    error_message = "Simulated Confluence API KABOOM"
    confluence_mock.update_page.side_effect = Exception(error_message)

    # Mock get_page_by_id if title/content isn't fully provided
    # (needed if only one of title/content is provided or only parent_id)
    confluence_mock.get_page_by_id.return_value = {
        "id": page_id,
        "title": "Original Title for API Error Test",
        "body": {"storage": {"value": "Original content"}},
        "version": {"number": current_version},
        "space": {"key": "ERRSPACE"}
    }

    inputs = {
        "page_id": page_id,
        "title": title_update,
        "current_version_number": current_version
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 500 # As update_page_logic raises HTTPException(500)
    response_data = response.json()

    print("DEBUG: test_update_page_api_error_generic response_data:", response_data) # Debug print

    assert response_data["status"] == "error"
    assert response_data["tool_name"] == "update_page"
    assert response_data["error_type"] == "HTTPException" # This is what main.py's handler will set
    
    # The error message from page_actions.py when raising HTTPException:
    # detail=f"Error updating page in Confluence: Details: {str(e)}"
    # The error message from main.py's final catch-all for HTTPException:
    # error_message=str(http_exc.detail)
    expected_detail_part = f"Error updating page in Confluence: Details: {error_message}"
    assert response_data["error_message"] == expected_detail_part
    
    # Verify update_page was called (and subsequently raised an error)
    confluence_mock.update_page.assert_called_once()

def test_update_page_api_error_version_conflict_simulation(mock_auth_and_confluence_client):
    confluence_mock, _, _ = mock_auth_and_confluence_client

    page_id = "err_409"
    current_version = 1 # User thinks this is the current version
    title_update = "Version Conflict Test"

    # Simulate an error from the Confluence client that might represent a version conflict
    # For example, the client might raise a custom exception or a generic one with a specific message.
    # Let's use a generic Exception here, as our current logic catches 'Exception'.
    # A real client library might raise something like `ConfluenceInteractionError(status_code=409, ...)`
    version_conflict_message = "Version conflict: The provided version number does not match the current page version."
    confluence_mock.update_page.side_effect = Exception(version_conflict_message)

    confluence_mock.get_page_by_id.return_value = {
        "id": page_id,
        "title": "Original Title for Version Conflict Test",
        "body": {"storage": {"value": "Original content"}},
        "version": {"number": current_version + 1}, # Simulate actual version being higher
        "space": {"key": "ERRSPACE"}
    }

    inputs = {
        "page_id": page_id,
        "title": title_update,
        "current_version_number": current_version
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    response = client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 500 # Still 500 due to generic Exception handling in logic
    response_data = response.json()

    print("DEBUG: test_update_page_api_error_version_conflict_simulation response_data:", response_data) # Debug print

    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    expected_detail_part = f"Error updating page in Confluence: Details: {version_conflict_message}"
    assert response_data["error_message"] == expected_detail_part
    
    confluence_mock.update_page.assert_called_once()

# Add more tests for parent update, combo updates, error cases etc.
