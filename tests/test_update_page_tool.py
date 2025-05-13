import pytest
from unittest.mock import MagicMock, patch, AsyncMock, Mock
from fastapi import HTTPException
from httpx import AsyncClient
from pydantic import ValidationError # Import for catching Pydantic errors
from atlassian.errors import ApiError # Import ApiError

from confluence_mcp_server.main import app # AVAILABLE_TOOLS is populated when app is imported
from confluence_mcp_server.mcp_actions.schemas import UpdatePageInput, UpdatePageOutput, MCPExecuteRequest

@pytest.fixture
def confluence_client_mock():
    mock = MagicMock(spec=["get_page_by_id", "update_page", "url"]) # Specify mocked methods
    # Mock the base URL attribute needed by get_confluence_page_url
    # Use a URL that urljoin will handle well
    mock.url = "https://test.confluence.com/wiki/"
    # Ensure mocked methods are awaitable if needed by logic (using MagicMock here for sync methods)
    mock.get_page_by_id = MagicMock()
    mock.update_page = MagicMock()
    return mock

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_success_title_only(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test updating only the title successfully."""
    # Ensure the app uses the provided mock
    mock_get_client.return_value = confluence_client_mock

    page_id = "12345"
    current_version = 1
    new_title = "New Awesome Title"
    existing_content = "<p>This is the existing content.</p>"
    space_key = "TESTSPACE"
    expected_new_version = 2

    # Mock the response from client.get_page_by_id (called when content is not being updated)
    get_page_response = {
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
    confluence_client_mock.get_page_by_id.return_value = get_page_response

    # Mock the response from client.update_page
    update_page_response = {
        "id": page_id,
        "title": new_title,
        "space": {"key": space_key}, # Simulate space info in response
        "version": {"number": expected_new_version},
        "status": "current",
        # Simulate a realistic webui link structure that urljoin can handle
        "_links": {"webui": f"/display/{space_key}/{page_id}"}
    }
    confluence_client_mock.update_page.return_value = update_page_response

    inputs = {
        "page_id": page_id,
        "title": new_title,
        "current_version_number": current_version
        # Content and parent_page_id are omitted
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    # Construct expected output using the helper function logic
    expected_url = f"https://test.confluence.com/wiki/display/{space_key}/{page_id}"
    expected_output = UpdatePageOutput(
        page_id=page_id,
        title=new_title,
        space_key=space_key,
        version=expected_new_version,
        status="current",
        url=expected_url
    )

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}" # Add detail
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "update_page"

    # Assert the full output matches the expected schema object dump
    assert response_data["outputs"] == expected_output.model_dump()

    # Verify client.update_page was called correctly
    confluence_client_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=new_title,
        body=existing_content, # Logic should fetch existing content if not provided
        version=expected_new_version,
        representation="storage" # Should be set if body is present
        # parent_id should NOT be present
    )
    # Verify get_page_by_id was called to fetch content and space key
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_success_content_only(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test updating only the content successfully."""
    mock_get_client.return_value = confluence_client_mock

    page_id = "67890"
    current_version = 2
    existing_title = "Existing Page Title"
    new_content = "<p>This is the brand new, updated content!</p>"
    space_key = "PROJ"
    expected_new_version = 3

    # Mock the response from client.get_page_by_id (called when title is not being updated)
    get_page_response = {
        "id": page_id,
        "title": existing_title,
        "body": { "storage": { "value": "<p>Old content here.</p>", "representation": "storage" } },
        "version": {"number": current_version},
        "space": {"key": space_key}
    }
    confluence_client_mock.get_page_by_id.return_value = get_page_response

    # Mock the response from client.update_page
    update_page_response = {
        "id": page_id,
        "title": existing_title, # Title remains unchanged
        "space": {"key": space_key},
        "version": {"number": expected_new_version},
        "status": "current",
        "_links": {"webui": f"/display/{space_key}/{page_id}"}
    }
    confluence_client_mock.update_page.return_value = update_page_response

    inputs = {
        "page_id": page_id,
        "content": new_content,
        "current_version_number": current_version
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    expected_url = f"https://test.confluence.com/wiki/display/{space_key}/{page_id}"
    expected_output = UpdatePageOutput(
        page_id=page_id,
        title=existing_title,
        space_key=space_key,
        version=expected_new_version,
        status="current",
        url=expected_url
    )

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["outputs"] == expected_output.model_dump()

    confluence_client_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=existing_title, # Logic should fetch existing title
        body=new_content,
        version=expected_new_version,
        representation="storage"
        # parent_id should NOT be present
    )
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')


@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_success_title_and_content(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test updating both title and content successfully."""
    mock_get_client.return_value = confluence_client_mock

    page_id = "101112"
    new_title = "Updated Title and Content"
    new_content = "<p>Both are new!</p>"
    current_version = 3
    space_key = "DOCS"
    expected_new_version = 4

    # No need to mock get_page_by_id if both title and content are provided in input,
    # as the refactored logic should not call it.

    # Mock the response from client.update_page
    update_page_response = {
        "id": page_id,
        "title": new_title,
        "space": {"key": space_key},
        "version": {"number": expected_new_version},
        "status": "current",
        "_links": {"webui": f"/display/{space_key}/{page_id}"}
    }
    confluence_client_mock.update_page.return_value = update_page_response

    inputs = {
        "page_id": page_id,
        "title": new_title,
        "content": new_content,
        "current_version_number": current_version
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    expected_url = f"https://test.confluence.com/wiki/display/{space_key}/{page_id}"
    expected_output = UpdatePageOutput(
        page_id=page_id,
        title=new_title,
        space_key=space_key,
        version=expected_new_version,
        status="current",
        url=expected_url
    )

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["outputs"] == expected_output.model_dump()

    confluence_client_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=new_title,
        body=new_content,
        version=expected_new_version,
        representation="storage"
        # parent_id should NOT be present
    )
    # Ensure get_page_by_id was NOT called
    confluence_client_mock.get_page_by_id.assert_not_called()

# ----- START OF FIXED PARENT/VALIDATION TESTS -----

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_success_parent_page_id_only(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test 'updating' parent_page_id: logic fetches others & updates without parent_id."""
    # NOTE: This test confirms the logic *ignores* parent_page_id for update,
    # as changing parent requires a different operation not supported by this tool.
    mock_get_client.return_value = confluence_client_mock

    page_id = "131415"
    current_version = 4
    new_parent_page_id = "99999" # This will be provided but should be ignored
    existing_title = "Page with Parent Ignored on Update"
    existing_content = "<p>Content here.</p>"
    space_key = "PARENT"
    expected_new_version = 5 # Version still increments

    # Mock get_page_by_id to fetch title and content (since only parent_id is *provided*)
    get_page_response = {
        "id": page_id,
        "title": existing_title,
        "body": {"storage": {"value": existing_content, "representation": "storage"}},
        "version": {"number": current_version},
        "space": {"key": space_key}
    }
    confluence_client_mock.get_page_by_id.return_value = get_page_response

    # Mock update_page - it should be called WITHOUT parent_id
    update_page_response = {
        "id": page_id,
        "title": existing_title, # Title fetched
        "space": {"key": space_key},
        "version": {"number": expected_new_version},
        "status": "current",
        "_links": {"webui": f"/display/{space_key}/{page_id}"}
    }
    confluence_client_mock.update_page.return_value = update_page_response

    inputs = {
        "page_id": page_id,
        "parent_page_id": new_parent_page_id, # Provide parent_id
        "current_version_number": current_version
    }

    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    expected_url = f"https://test.confluence.com/wiki/display/{space_key}/{page_id}"
    expected_output = UpdatePageOutput(
        page_id=page_id,
        title=existing_title, # Expected title is the fetched one
        space_key=space_key,
        version=expected_new_version,
        status="current",
        url=expected_url
    )

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "success"
    # Should succeed, but parent won't actually change via this tool
    assert response_data["outputs"] == expected_output.model_dump()

    # Verify update_page was called WITHOUT parent_id
    confluence_client_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=existing_title, # Fetched title
        body=existing_content, # Fetched content
        version=expected_new_version,
        representation="storage"
        # Ensure parent_id is NOT passed to the actual update call
    )
    # Verify get_page_by_id was called because title and content were missing from input
    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')


# === Input Validation Tests ===

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client') # Still need to patch
async def test_update_page_missing_page_id(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test request missing required page_id."""
    mock_get_client.return_value = confluence_client_mock # Assign mock

    inputs = {
        # "page_id": "missing",
        "title": "Test Title",
        "current_version_number": 1
    }
    # Use exclude_none=True or similar if necessary to ensure the key is actually missing
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    payload_dict = request_payload.model_dump()
    # Manually remove the key if model_dump doesn't handle missing optional keys correctly
    # for testing purposes (Pydantic usually requires it unless Optional)
    if "page_id" not in inputs:
         if "inputs" in payload_dict and "page_id" in payload_dict["inputs"]:
             del payload_dict["inputs"]["page_id"] # Actually remove if present from default

    response = await client.post("/execute", json=payload_dict) # Send potentially modified dict

    assert response.status_code == 422, f"Expected 422, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError" # Changed from "ValidationError"
    # Check details for the specific missing field - corrected loc
    assert any(err["loc"] == ['page_id'] and err["msg"] == "Field required" for err in response_data.get("validation_details", [])), "Missing page_id error not found"
    confluence_client_mock.update_page.assert_not_called() # API should not be called

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_missing_version(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test request missing required current_version_number."""
    mock_get_client.return_value = confluence_client_mock

    inputs = {
        "page_id": "12345",
        "title": "Test Title"
        # "current_version_number": missing
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    payload_dict = request_payload.model_dump()
    if "current_version_number" not in inputs:
         if "inputs" in payload_dict and "current_version_number" in payload_dict["inputs"]:
             del payload_dict["inputs"]["current_version_number"]

    response = await client.post("/execute", json=payload_dict)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError" # Changed from "ValidationError"
    # Corrected loc
    assert any(err["loc"] == ['current_version_number'] and err["msg"] == "Field required" for err in response_data.get("validation_details", [])), "Missing version error not found"
    confluence_client_mock.update_page.assert_not_called()

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_missing_title_and_content_and_parent(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test request missing all updatable fields (model validator)."""
    # This test is for the model-level validation (@model_validator)
    mock_get_client.return_value = confluence_client_mock

    inputs = {
        "page_id": "12345",
        "current_version_number": 1
        # title, content, parent_page_id are all missing
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)
    payload_dict = request_payload.model_dump()
    # Ensure the optional fields are truly absent if not provided
    if "title" not in inputs and "inputs" in payload_dict and "title" in payload_dict["inputs"]:
        del payload_dict["inputs"]["title"]
    if "content" not in inputs and "inputs" in payload_dict and "content" in payload_dict["inputs"]:
        del payload_dict["inputs"]["content"]
    if "parent_page_id" not in inputs and "inputs" in payload_dict and "parent_page_id" in payload_dict["inputs"]:
        del payload_dict["inputs"]["parent_page_id"]

    response = await client.post("/execute", json=payload_dict)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError" # Changed from "ValidationError"

    details = response_data.get("validation_details", [])
    assert len(details) == 1, f"Expected 1 validation error, got {len(details)}: {details}"
    model_error = details[0]
    expected_msg = "Value error, At least one of 'title', 'content', or 'parent_page_id' must be provided to update the page."
    assert model_error.get("msg") == expected_msg, f"Expected msg '{expected_msg}', got '{model_error.get('msg')}'"
    assert model_error.get("loc") == [], f"Expected loc [], got '{model_error.get('loc')}'"
    assert model_error.get("type") == "value_error", f"Expected type 'value_error', got '{model_error.get('type')}'"

    confluence_client_mock.update_page.assert_not_called()


@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_invalid_input_types(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test request with invalid data types for inputs."""
    mock_get_client.return_value = confluence_client_mock

    inputs = {
        "page_id": 12345, # Should be string
        "title": ["Not", "a", "string"], # Should be string
        "content": {"wrong": "type"}, # Should be string
        "parent_page_id": False, # Should be string
        "current_version_number": "not-an-int" # Should be int
    }
    # Send raw payload as these types won't fit the MCPExecuteRequest schema directly
    raw_payload = {
        "tool_name": "update_page",
        "inputs": inputs
    }

    response = await client.post("/execute", json=raw_payload) # Send raw payload

    assert response.status_code == 422, f"Expected 422, got {response.status_code}. Response: {response.text}"
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError" # Changed from "ValidationError"
    details = response_data.get("validation_details", [])
    # Check for specific type errors using more robust checks
    assert any(err["loc"] == ['page_id'] and err["type"] == "string_type" for err in details), "Page ID type error not found"
    assert any(err["loc"] == ['title'] and err["type"] == "string_type" for err in details), "Title type error not found"
    assert any(err["loc"] == ['content'] and err["type"] == "string_type" for err in details), "Content type error not found"
    assert any(err["loc"] == ['parent_page_id'] and err["type"] == "string_type" for err in details), "Parent Page ID type error not found"
    assert any(err["loc"] == ['current_version_number'] and err["type"] == "int_parsing" for err in details), "Version type error not found"
    confluence_client_mock.update_page.assert_not_called()


# ----- START OF UNFIXED ERROR HANDLING TESTS -----

# === Error Handling Tests ===

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_api_error_on_get(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test handling of Atlassian API error during the initial get_page_by_id call."""
    mock_get_client.return_value = confluence_client_mock

    page_id = "err-get"
    current_version = 1
    new_title = "Title Update"
    error_message = "Page not found or permission denied"
    status_code = 404

    # Configure get_page_by_id to raise ApiError with a mock response
    mock_response_get = Mock()
    mock_response_get.status_code = status_code
    api_error_get = ApiError(error_message)
    api_error_get.response = mock_response_get # Assign mock response
    confluence_client_mock.get_page_by_id.side_effect = api_error_get

    inputs = {
        "page_id": page_id,
        "title": new_title, # Need title or content to trigger the get call
        "current_version_number": current_version
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == status_code # Should map ApiError status code
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException" # Mapped from ApiError
    # Assert the specific detail message generated by the handler for 404 is in 'error_message'
    assert response_data["error_message"] == f"Page with ID {page_id} not found."
    # Check that update_page was not called
    confluence_client_mock.update_page.assert_not_called() # Update should not be attempted

    confluence_client_mock.get_page_by_id.assert_called_once_with(page_id=page_id, expand='body.storage,version,space')

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_api_error_on_update(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test handling of Atlassian API error during the update_page call."""
    mock_get_client.return_value = confluence_client_mock

    page_id = "err-update"
    current_version = 2
    new_title = "Update Title"
    new_content = "<p>Update Content</p>"
    space_key = "ERRORSPACE"
    expected_new_version = 3
    error_message = "Version conflict or invalid permissions"
    status_code = 409 # Conflict

    # No need to mock get_page_by_id if title and content provided

    # Configure update_page to raise ApiError with a mock response
    mock_response_update = Mock()
    mock_response_update.status_code = status_code
    api_error_update = ApiError(error_message)
    api_error_update.response = mock_response_update # Assign mock response
    confluence_client_mock.update_page.side_effect = api_error_update

    inputs = {
        "page_id": page_id,
        "title": new_title,
        "content": new_content,
        "current_version_number": current_version
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == status_code
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    # Assert the detail message for 409 includes the original reason, check 'error_message'
    assert error_message in response_data["error_message"] # Check if original message is included for non-404 errors

    confluence_client_mock.get_page_by_id.assert_not_called() # Should not be called
    confluence_client_mock.update_page.assert_called_once_with(
        page_id=page_id,
        title=new_title,
        body=new_content,
        version=expected_new_version,
        representation="storage"
    )

@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client')
async def test_update_page_unexpected_error(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test handling of an unexpected error during processing."""
    mock_get_client.return_value = confluence_client_mock

    page_id = "unexpected-err"
    error_message = "Something completely unexpected happened!"

    # Configure update_page to raise a generic Exception
    confluence_client_mock.update_page.side_effect = RuntimeError(error_message)

    inputs = {
        "page_id": page_id,
        "title": "Title",
        "content": "Content",
        "current_version_number": 1
    }
    request_payload = MCPExecuteRequest(tool_name="update_page", inputs=inputs)

    response = await client.post("/execute", json=request_payload.model_dump())

    assert response.status_code == 500 # Internal Server Error for unexpected exceptions
    response_data = response.json()
    assert response_data["status"] == "error"
    # The specific error_type might depend on the global exception handler
    # It could be "Exception", "RuntimeError", or mapped to "HTTPException" with 500
    # Let's check if the message indicates a server error (actual message format from main.py handler)
    # Based on Memory 2b0636ac, the format is "Server Error ({ExcType}): {OriginalMsg}"
    # Updated format based on observed test failure:
    expected_error_detail = f"Internal Server Error: Unexpected error updating page. Details: {error_message}"
    assert response_data["error_message"] == expected_error_detail # Updated assertion


    # Verify the mock was called, leading to the error
    confluence_client_mock.update_page.assert_called_once()

# Add more tests for parent update, combo updates, error cases etc.
