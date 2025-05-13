import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from typing import AsyncGenerator
from atlassian import Confluence
from atlassian.errors import ApiError

from confluence_mcp_server.main import app 
from confluence_mcp_server.mcp_actions.schemas import GetCommentsInput, GetCommentsOutput, MCPExecuteResponse, AddCommentInput, AddCommentOutput

BASE_URL = "" # Changed from "/api/v1/mcp"

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # Use ASGITransport instead of app=
    transport = ASGITransport(app=app) # Create transport
    async with AsyncClient(transport=transport, base_url="http://test") as ac: # Use transport
        yield ac

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_get_comments_success(
    mock_get_confluence_client, 
    client: AsyncClient
):
    mock_returned_confluence_client = MagicMock(spec=Confluence)

    mock_api_response = {
        "results": [
            {
                "id": "1001",
                "extensions": {
                    "author": {"accountId": "user123", "displayName": "Test User"},
                    "when": "2023-01-01T12:00:00.000Z",
                    "lastModifiedDate": "2023-01-01T12:00:00.000Z"
                },
                "body": {"storage": {"value": "<p>This is comment one.</p>"}},
            },
            {
                "id": "1002",
                "extensions": {
                    "author": {"accountId": "user456", "displayName": "Another User"},
                    "when": "2023-01-02T14:30:00.000Z",
                    # Simulating a parent comment for a reply
                    "parentComment": {"id": "1001"} 
                },
                "body": {"view": {"value": "This is comment two in view format."}},
            }
        ],
        "start": 0,
        "limit": 2,
        "size": 2,
        "_links": {"next": "/rest/api/content/999/child/comment?limit=2&start=2"}
    }
    mock_returned_confluence_client.get_page_comments.return_value = mock_api_response

    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = GetCommentsInput(page_id="999", limit=2, start=0, expand="body.view") # Added expand for test
    
    request_payload = {
        "tool_name": "get_comments",
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "get_comments"
    
    outputs = response_data.get("outputs")
    assert outputs is not None
    
    assert "comments" in outputs
    assert len(outputs["comments"]) == 2
    assert outputs["retrieved_count"] == 2
    assert outputs["next_start_offset"] == 2
    assert outputs["limit_used"] == 2
    assert outputs["start_used"] == 0

    first_comment = outputs["comments"][0]
    assert first_comment["comment_id"] == "1001"
    assert first_comment["author_display_name"] == "Test User"
    assert first_comment["body_storage"] == "<p>This is comment one.</p>"
    assert first_comment["parent_comment_id"] is None # First comment is not a reply

    second_comment = outputs["comments"][1]
    assert second_comment["comment_id"] == "1002"
    assert second_comment["author_display_name"] == "Another User"
    assert second_comment["body_view"] == "This is comment two in view format."
    assert second_comment["parent_comment_id"] == "1001" # Second comment replies to first

    mock_returned_confluence_client.get_page_comments.assert_called_once_with(
        page_id="999",
        limit=2,
        start=0,
        expand="body.view"
    )


@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_get_comments_page_not_found(
    mock_get_confluence_client,
    client: AsyncClient
):
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    # Simulate Confluence API returning a 404 Not Found error
    error_instance = ApiError(reason="Page not found")
    error_instance.status_code = 404 # Directly set the attribute
    # For the current error message formatting, we also need e.text and e.url if not 404,
    # and e.reason for 404. The e.reason is set by constructor.
    # If the logic were to use e.response.text for the 404 message, we'd need this:
    # error_instance.response = MagicMock(status_code=404, text='{"statusCode":404,"message":"No content found with id=123"}')

    mock_returned_confluence_client.get_page_comments.side_effect = error_instance
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = GetCommentsInput(page_id="123") # Non-existent page_id
    request_payload = {
        "tool_name": "get_comments",
        "inputs": tool_inputs.model_dump()
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()

    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"

    expected_detail = f"Page with ID '{tool_inputs.page_id}' not found or user lacks permission."
    assert response_data["error_message"] == expected_detail

    mock_returned_confluence_client.get_page_comments.assert_called_once_with(
        page_id=tool_inputs.page_id,
        limit=tool_inputs.limit,
        start=tool_inputs.start,
        expand=tool_inputs.expand
    )


@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_get_comments_no_comments(
    mock_get_confluence_client,
    client: AsyncClient
):
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    mock_api_response = {
        "results": [],
        "start": 0,
        "limit": 25,
        "size": 0,
        "_links": {} # No 'next' link
    }
    mock_returned_confluence_client.get_page_comments.return_value = mock_api_response
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = GetCommentsInput(page_id="123", limit=25, start=0)
    request_payload = {
        "tool_name": "get_comments",
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["status"] == "success"
    outputs = response_data.get("outputs")
    assert outputs is not None
    assert outputs["comments"] == []
    assert outputs["retrieved_count"] == 0
    assert outputs["limit_used"] == 25
    assert outputs["start_used"] == 0
    assert outputs["next_start_offset"] is None # Expect None if no more comments

    mock_returned_confluence_client.get_page_comments.assert_called_once_with(
        page_id="123",
        limit=25,
        start=0,
        expand=None # Default if not provided in GetCommentsInput
    )


@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_get_comments_other_api_error(
    mock_get_confluence_client,
    client: AsyncClient
):
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    error_reason = "Simulated Confluence Internal Server Error"
    error_url = "https://mocked.confluence.instance/rest/api/content/123/child/comment"
    error_status = 503

    error_instance = ApiError(reason=error_reason)
    error_instance.status_code = error_status # Directly set the attribute
    error_instance.url = error_url # Directly set the attribute
    # error_instance.response = MagicMock(status_code=error_status, text=error_reason, url=error_url)

    mock_returned_confluence_client.get_page_comments.side_effect = error_instance
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = GetCommentsInput(page_id="123")
    request_payload = {
        "tool_name": "get_comments",
        "inputs": tool_inputs.model_dump()
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    # --- Final Assertions for Specific HTTPException Handling ---
    # Expecting 503 because the specific HTTPException handler in main.py is now catching the exception
    assert response.status_code == error_status # Should be 503
    response_data = response.json()

    assert response_data["status"] == "error"
    # Expecting HTTPException type as set by the specific handler
    assert response_data["error_type"] == "HTTPException"

    # Construct the exact detail message that get_comments_logic puts into its HTTPException
    expected_detail_message = (
        f"Error getting comments from Confluence: Details: Received {error_status} "
        f"{error_reason} for url: {error_url}"
    )

    # Verify that the error message matches exactly
    assert response_data["error_message"] == expected_detail_message
    # --- END Final Assertions ---

    mock_returned_confluence_client.get_page_comments.assert_called_once_with(
        page_id="123",
        limit=GetCommentsInput.model_fields['limit'].default, # Default limit
        start=GetCommentsInput.model_fields['start'].default, # Default start
        expand=GetCommentsInput.model_fields['expand'].default # Default expand
    )


# TODO:
# - test_get_comments_with_different_expand_parameter (e.g., only body.storage)
# - test_get_comments_pagination_no_next_link (when last page of comments is fetched)
# - test_get_comments_input_validation_page_id_missing (FastAPI/Pydantic validation)
# - test_get_comments_input_validation_limit_invalid (e.g., string, negative, zero)
# - test_get_comments_input_validation_start_invalid (e.g., negative)


# --- Tests for add_comment ---

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_success(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test successfully adding a top-level comment."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    mock_api_response = {"id": "67890"}
    mock_returned_confluence_client.add_comment.return_value = mock_api_response
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="12345", body="<p>Test top-level comment</p>")
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["status"] == "success"
    assert response_data["tool_name"] == "add_comment"
    outputs = response_data.get("outputs")
    assert outputs is not None
    assert outputs["comment_id"] == "67890"
    assert outputs["page_id"] == "12345"

    mock_returned_confluence_client.add_comment.assert_called_once_with(
        page_id="12345",
        body="<p>Test top-level comment</p>",
        parent_id=None # Check parent_id is None for top-level
    )

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_reply_success(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test successfully adding a reply to a comment."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    mock_api_response = {"id": "67891"} # Different ID for reply
    mock_returned_confluence_client.add_comment.return_value = mock_api_response
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(
        page_id="12345", 
        body="<p>Test reply comment</p>", 
        parent_comment_id="67890" # Provide parent ID
    )
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["status"] == "success"
    outputs = response_data.get("outputs")
    assert outputs is not None
    assert outputs["comment_id"] == "67891"
    assert outputs["page_id"] == "12345"

    mock_returned_confluence_client.add_comment.assert_called_once_with(
        page_id="12345",
        body="<p>Test reply comment</p>",
        parent_id="67890" # Check parent_id is passed correctly
    )

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_page_not_found(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test adding comment when the page ID is not found (404)."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    error_instance = ApiError(reason="Page Not Found")
    error_instance.status_code = 404
    error_instance.url = "mock_url"
    mock_returned_confluence_client.add_comment.side_effect = error_instance
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="invalid-page", body="<p>Test comment</p>")
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    expected_detail = f"Could not add comment: Page ID 'invalid-page' not found, or Parent Comment ID 'None' not found, or user lacks permission to view/comment."
    assert response_data["error_message"] == expected_detail

    mock_returned_confluence_client.add_comment.assert_called_once_with(
        page_id="invalid-page", body="<p>Test comment</p>", parent_id=None
    )

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_parent_not_found(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test adding comment when the parent comment ID is not found (also 404)."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    error_instance = ApiError(reason="Parent Not Found") # Reason might vary
    error_instance.status_code = 404
    error_instance.url = "mock_url"
    mock_returned_confluence_client.add_comment.side_effect = error_instance
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="12345", body="<p>Test reply</p>", parent_comment_id="invalid-parent")
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 404
    response_data = response.json()
    
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    # Note: The error message might be identical to page_not_found based on current logic
    expected_detail = f"Could not add comment: Page ID '12345' not found, or Parent Comment ID 'invalid-parent' not found, or user lacks permission to view/comment."
    assert response_data["error_message"] == expected_detail

    mock_returned_confluence_client.add_comment.assert_called_once_with(
        page_id="12345", body="<p>Test reply</p>", parent_id="invalid-parent"
    )

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_forbidden(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test adding comment when user lacks permissions (403)."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    error_instance = ApiError(reason="Forbidden")
    error_instance.status_code = 403
    error_instance.url = "mock_url"
    mock_returned_confluence_client.add_comment.side_effect = error_instance
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="restricted-page", body="<p>Test comment</p>")
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 403
    response_data = response.json()
    
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    expected_detail = f"Error adding comment: User does not have permission to comment on page ID 'restricted-page'. Details: Received 403 Forbidden for url: mock_url."
    assert response_data["error_message"] == expected_detail

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_bad_request(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test adding comment with invalid input format (400)."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    error_instance = ApiError(reason="Bad Request - Invalid Body")
    error_instance.status_code = 400
    error_instance.url = "mock_url"
    mock_returned_confluence_client.add_comment.side_effect = error_instance
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="12345", body="Invalid body format") # Not valid storage format
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 400
    response_data = response.json()
    
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    expected_detail = f"Error adding comment: Invalid input provided. Details: Received 400 Bad Request - Invalid Body for url: mock_url. Check body format."
    assert response_data["error_message"] == expected_detail

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_api_returns_no_id(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test handling when API succeeds (2xx) but response lacks 'id'."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    # Simulate a successful API call returning an unexpected structure
    mock_api_response = {"type": "comment", "status": "created"} 
    mock_returned_confluence_client.add_comment.return_value = mock_api_response
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="12345", body="<p>Test comment</p>")
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 500 # Should raise HTTPException(500) due to ValueError
    response_data = response.json()
    
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    # Check for the detail message coming from the ValueError raised in the logic
    assert "Internal processing error after adding comment: Confluence API succeeded but did not return a comment ID." in response_data["error_message"]

@pytest.mark.anyio
@patch("confluence_mcp_server.main.get_confluence_client")
async def test_add_comment_unexpected_error(
    mock_get_confluence_client, 
    client: AsyncClient
):
    """Test handling of unexpected exceptions during logic execution."""
    mock_returned_confluence_client = MagicMock(spec=Confluence)
    mock_returned_confluence_client.add_comment.side_effect = Exception("Something went wrong unexpectedly")
    mock_get_confluence_client.return_value = mock_returned_confluence_client

    tool_inputs = AddCommentInput(page_id="12345", body="<p>Test comment</p>")
    request_payload = {
        "tool_name": "add_comment", 
        "inputs": tool_inputs.model_dump(exclude_none=True)
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 500
    response_data = response.json()
    
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    assert "An unexpected server error occurred while adding the comment: Something went wrong unexpectedly" in response_data["error_message"]

@pytest.mark.anyio
async def test_add_comment_input_validation_missing_required(client: AsyncClient):
    """Test input validation failure (missing required fields -> 422)."""
    # Missing 'body' which is required
    invalid_inputs = {"page_id": "12345"} 
    request_payload = {
        "tool_name": "add_comment",
        "inputs": invalid_inputs
    }

    response = await client.post(f"{BASE_URL}/execute", json=request_payload)

    assert response.status_code == 422 # FastAPI validation error
    response_data = response.json()

    assert response_data["status"] == "error"
    assert response_data["error_type"] == "InputValidationError"
    assert response_data["error_message"] == "Input validation failed."
    assert "validation_details" in response_data
    assert isinstance(response_data["validation_details"], list)
    # Check that the error detail mentions the missing 'body' field
    assert any(detail.get("loc") == ["body"] and "Field required" in detail.get("msg", "") for detail in response_data["validation_details"])

# TODO: Add more validation tests if needed (e.g., invalid types, constraints)
