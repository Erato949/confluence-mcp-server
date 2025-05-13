import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from typing import AsyncGenerator
from atlassian import Confluence
from atlassian.errors import ApiError

from confluence_mcp_server.main import app 
from confluence_mcp_server.mcp_actions.schemas import GetCommentsInput, GetCommentsOutput, MCPExecuteResponse

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
