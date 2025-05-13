# Test file for attachment actions
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from fastapi import HTTPException
from atlassian import Confluence
from atlassian.errors import ApiError

from confluence_mcp_server.mcp_actions.attachment_actions import get_attachments_logic
from confluence_mcp_server.mcp_actions.schemas import (
    GetAttachmentsInput,
    AttachmentOutputItem,
    GetAttachmentsOutput,
)

pytestmark = pytest.mark.anyio

@pytest.fixture
def confluence_client_mock():
    mock = AsyncMock(spec=Confluence)
    # Ensure the method we are calling exists on the mock
    # and that it's a MagicMock to allow direct return_value/side_effect setting
    mock.get_attachments_from_content = MagicMock()
    return mock

# --- Test Data ---
MOCK_PAGE_ID = "12345"
MOCK_ATTACHMENT_1 = {
    'id': 'att1',
    'type': 'attachment',
    'status': 'current',
    'title': 'document.pdf',
    'metadata': {'mediaType': 'application/pdf', 'comment': 'Test PDF document'},
    'version': {'number': 1, 'when': '2023-01-01T10:00:00.000Z'},
    'extensions': {'fileSize': 102400},
    '_links': {'webui': '/display/SPACE/Page?preview=/att1/doc.pdf', 'download': '/download/att1/doc.pdf'}
}
MOCK_ATTACHMENT_2 = {
    'id': 'att2',
    'type': 'attachment',
    'status': 'current',
    'title': 'image.png',
    'metadata': {'mediaType': 'image/png', 'comment': 'Test PNG image'},
    'version': {'number': 2, 'when': '2023-01-02T11:00:00.000Z'},
    'extensions': {'fileSize': 51200},
    '_links': {'webui': '/display/SPACE/Page?preview=/att2/img.png', 'download': '/download/att2/img.png'}
}
MOCK_ATTACHMENT_3_TEXT = {
    'id': 'att3',
    'type': 'attachment',
    'status': 'current',
    'title': 'notes.txt',
    'metadata': {'mediaType': 'text/plain', 'comment': 'Plain text notes'},
    'version': {'number': 1, 'when': '2023-01-03T12:00:00.000Z'},
    'extensions': {'fileSize': 1024},
    '_links': {'webui': '/display/SPACE/Page?preview=/att3/notes.txt', 'download': '/download/att3/notes.txt'}
}

# --- Test Cases ---

async def test_get_attachments_success_default_params(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID)
    mock_api_response = {
        'results': [MOCK_ATTACHMENT_1, MOCK_ATTACHMENT_2],
        'start': 0,
        'limit': 25, # Default limit the API might use or library passes
        'size': 2,
        '_links': {}
    }
    confluence_client_mock.get_attachments_from_content.return_value = mock_api_response

    result = await get_attachments_logic(confluence_client_mock, inputs)

    confluence_client_mock.get_attachments_from_content.assert_called_once_with(
        page_id=MOCK_PAGE_ID, filename=None, media_type=None, limit=25, start=0
    )
    assert isinstance(result, GetAttachmentsOutput)
    assert len(result.attachments) == 2
    assert result.retrieved_count == 2
    assert result.attachments[0].attachment_id == "att1"
    assert result.attachments[0].title == MOCK_ATTACHMENT_1['title']
    assert result.attachments[0].media_type == MOCK_ATTACHMENT_1['metadata']['mediaType']
    assert result.attachments[0].file_size == MOCK_ATTACHMENT_1['extensions']['fileSize']
    assert result.attachments[1].attachment_id == "att2"
    assert result.next_start_offset is None # No 'next' link in mock response
    assert result.limit_used == 25
    assert result.start_used == 0

async def test_get_attachments_success_custom_params_and_pagination(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID, limit=1, start=0)
    mock_api_response = {
        'results': [MOCK_ATTACHMENT_1],
        'start': 0,
        'limit': 1,
        'size': 1,
        '_links': {'next': '/rest/api/content/12345/child/attachment?limit=1&start=1'}
    }
    confluence_client_mock.get_attachments_from_content.return_value = mock_api_response

    result = await get_attachments_logic(confluence_client_mock, inputs)

    confluence_client_mock.get_attachments_from_content.assert_called_once_with(
        page_id=MOCK_PAGE_ID, filename=None, media_type=None, limit=1, start=0
    )
    assert len(result.attachments) == 1
    assert result.retrieved_count == 1
    assert result.attachments[0].attachment_id == MOCK_ATTACHMENT_1['id']
    assert result.next_start_offset == 1 # Calculated: inputs.start + result.retrieved_count
    assert result.limit_used == 1
    assert result.start_used == 0

async def test_get_attachments_success_no_attachments(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID)
    mock_api_response = {
        'results': [],
        'start': 0,
        'limit': 25,
        'size': 0,
        '_links': {}
    }
    confluence_client_mock.get_attachments_from_content.return_value = mock_api_response

    result = await get_attachments_logic(confluence_client_mock, inputs)

    confluence_client_mock.get_attachments_from_content.assert_called_once_with(
        page_id=MOCK_PAGE_ID, filename=None, media_type=None, limit=25, start=0
    )
    assert len(result.attachments) == 0
    assert result.retrieved_count == 0
    assert result.next_start_offset is None

async def test_get_attachments_success_with_filtering(confluence_client_mock):
    # This test assumes the client.get_attachments_from_content itself handles filtering
    # or that the mock is set up to simulate it.
    # The current logic passes filename and media_type to the API call.
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID, filename="document.pdf", media_type="application/pdf")
    # Mock response if only MOCK_ATTACHMENT_1 matches these filters
    mock_api_response = {
        'results': [MOCK_ATTACHMENT_1],
        'start': 0,
        'limit': 25,
        'size': 1,
        '_links': {}
    }
    confluence_client_mock.get_attachments_from_content.return_value = mock_api_response

    result = await get_attachments_logic(confluence_client_mock, inputs)

    confluence_client_mock.get_attachments_from_content.assert_called_once_with(
        page_id=MOCK_PAGE_ID, filename="document.pdf", media_type="application/pdf", limit=25, start=0
    )
    assert len(result.attachments) == 1
    assert result.retrieved_count == 1
    assert result.attachments[0].title == "document.pdf"
    assert result.attachments[0].media_type == "application/pdf"

async def test_get_attachments_error_page_not_found(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id="nonexistent_page")
    
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    # Create a mock for the request object within the response
    mock_request = Mock()
    mock_request.url = "http://fake.url/api/content/nonexistent_page/child/attachment"
    mock_response.request = mock_request # Assign it here

    # Instantiate ApiError and then manually set response to bypass MRO __init__ issues
    error_instance = ApiError("Page not found")
    error_instance.response = mock_response
    confluence_client_mock.get_attachments_from_content.side_effect = error_instance
    
    with pytest.raises(HTTPException) as exc_info:
        await get_attachments_logic(confluence_client_mock, inputs)
    
    assert exc_info.value.status_code == 404
    assert "Page with ID 'nonexistent_page' not found" in exc_info.value.detail

async def test_get_attachments_error_api_error_other(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID)

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    # Create a mock for the request object within the response
    mock_request = Mock()
    mock_request.url = f"http://fake.url/api/content/{MOCK_PAGE_ID}/child/attachment"
    mock_response.request = mock_request # Assign it here

    # Instantiate ApiError and then manually set response to bypass MRO __init__ issues
    error_instance = ApiError("Internal Server Error")
    error_instance.response = mock_response
    confluence_client_mock.get_attachments_from_content.side_effect = error_instance

    with pytest.raises(HTTPException) as exc_info:
        await get_attachments_logic(confluence_client_mock, inputs)
    
    assert exc_info.value.status_code == 500
    assert "Error getting attachments from Confluence: Status 500" in exc_info.value.detail

async def test_get_attachments_error_unexpected_exception(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID)
    confluence_client_mock.get_attachments_from_content.side_effect = Exception("Something broke badly")

    with pytest.raises(HTTPException) as exc_info:
        await get_attachments_logic(confluence_client_mock, inputs)
    
    assert exc_info.value.status_code == 500
    assert "An unexpected error occurred while processing attachments: Something broke badly" in exc_info.value.detail
