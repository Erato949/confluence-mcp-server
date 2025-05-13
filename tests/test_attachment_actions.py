# Test file for attachment actions
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from fastapi import HTTPException
from atlassian import Confluence
from atlassian.errors import ApiError

from confluence_mcp_server.mcp_actions.attachment_actions import get_attachments_logic, add_attachment_logic
from confluence_mcp_server.mcp_actions.schemas import (
    GetAttachmentsInput,
    AttachmentOutputItem,
    GetAttachmentsOutput,
    AddAttachmentInput,
    AddAttachmentOutput
)

pytestmark = pytest.mark.anyio

@pytest.fixture
def confluence_client_mock():
    mock = AsyncMock(spec=Confluence)
    # Ensure the method we are calling exists on the mock
    # and that it's a MagicMock to allow direct return_value/side_effect setting
    mock.get_attachments_from_content = MagicMock()
    mock.attach_file = MagicMock() # Added for add_attachment tests
    return mock

# --- Test Data ---
MOCK_PAGE_ID = "12345"
MOCK_FILE_PATH = "/fake/path/to/attachment.txt"
MOCK_FILENAME = "attachment.txt"
MOCK_COMMENT = "This is a test attachment."
MOCK_MEDIA_TYPE = "text/plain"

MOCK_UPLOADED_ATTACHMENT_API_RESPONSE = {
    'id': 'attNew123',
    'type': 'attachment',
    'status': 'current',
    'title': MOCK_FILENAME,
    'metadata': {'mediaType': MOCK_MEDIA_TYPE, 'comment': MOCK_COMMENT},
    'version': {'number': 1, 'when': '2023-10-27T10:00:00.000Z'},
    'extensions': {'fileSize': 12345},
    '_links': {'webui': '/display/SPACE/Page?preview=/attNew123/attachment.txt', 'download': '/download/attNew123/attachment.txt'}
}

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
    inputs = GetAttachmentsInput(page_id="nonexistentpage")
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_request = Mock()
    mock_request_url = "http://fake.url/api/content/nonexistentpage/child/attachment" # Ensure this matches logic's source
    mock_request.url = mock_request_url
    mock_response.request = mock_request
    
    error_instance = ApiError("Page not found") 
    error_instance.response = mock_response 
    confluence_client_mock.get_attachments_from_content.side_effect = error_instance
    
    with pytest.raises(HTTPException) as exc_info:
        await get_attachments_logic(confluence_client_mock, inputs)
    
    assert exc_info.value.status_code == 404
    expected_detail = (
        f"Page with ID '{inputs.page_id}' not found, or attachments endpoint not available for it. "
        f"[Confluence API: Status 404, Reason: 'Not Found', URL: '{mock_request_url}']"
    )
    assert exc_info.value.detail == expected_detail

async def test_get_attachments_error_api_error_other(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID)
    mock_response = Mock()
    mock_response.status_code = 500 # Changed to 500 to match previous fix attempt, can be any non-404
    mock_response.reason = "Internal Server Error"
    mock_request = Mock()
    mock_request_url = f"http://fake.url/api/content/{MOCK_PAGE_ID}/child/attachment"
    mock_request.url = mock_request_url
    mock_response.request = mock_request

    error_instance = ApiError("Some API Error")
    error_instance.response = mock_response
    confluence_client_mock.get_attachments_from_content.side_effect = error_instance

    with pytest.raises(HTTPException) as exc_info:
        await get_attachments_logic(confluence_client_mock, inputs)
    
    assert exc_info.value.status_code == 500
    expected_detail = (
        f"Error getting attachments from Confluence: Status 500. Reason: 'Internal Server Error'_ "
        f"URL: '{mock_request_url}'_ "
        f"(Attempted for Page ID: '{MOCK_PAGE_ID}')"
    )
    assert exc_info.value.detail == expected_detail

async def test_get_attachments_error_unexpected_exception(confluence_client_mock):
    inputs = GetAttachmentsInput(page_id=MOCK_PAGE_ID)
    error_message = "Network error"
    confluence_client_mock.get_attachments_from_content.side_effect = Exception(error_message)

    with pytest.raises(HTTPException) as exc_info:
        await get_attachments_logic(confluence_client_mock, inputs)
    
    assert exc_info.value.status_code == 500
    assert f"An unexpected error occurred while processing attachments: {error_message}" == exc_info.value.detail

# --- Tests for add_attachment_logic ---

@patch('os.path.exists', return_value=True)
@patch('os.path.isfile', return_value=True)
async def test_add_attachment_success(mock_isfile, mock_exists, confluence_client_mock):
    inputs = AddAttachmentInput(
        page_id=MOCK_PAGE_ID,
        file_path=MOCK_FILE_PATH,
        filename=MOCK_FILENAME,
        comment=MOCK_COMMENT
    )
    # Simulate the API response the logic expects after a successful attachment
    mock_api_response = {
        "id": "attNew123",
        "title": MOCK_FILENAME, # The filename on Confluence
        "status": "current",
        "metadata": {"mediaType": MOCK_MEDIA_TYPE, "comment": MOCK_COMMENT},
        "extensions": {"fileSize": 5120},
        "version": {"number": 1, "when": "2023-10-27T14:00:00Z"},
        "_links": {"download": "/download/attNew123", "webui": "/view/attNew123"}
    }
    confluence_client_mock.attach_file.return_value = mock_api_response

    result = await add_attachment_logic(confluence_client_mock, inputs)

    confluence_client_mock.attach_file.assert_called_once_with(
        page_id=MOCK_PAGE_ID,
        filepath=MOCK_FILE_PATH,   # Corrected from filename to filepath
        name=MOCK_FILENAME,        # This is the desired name of the attachment on Confluence
        comment=MOCK_COMMENT,
        content_type=None          # Logic doesn't explicitly pass content_type, so it's None
    )

    assert isinstance(result, AddAttachmentOutput)
    assert result.attachment_id == mock_api_response["id"]
    assert result.title == mock_api_response["title"]
    assert result.status == mock_api_response["status"]
    assert result.media_type == mock_api_response["metadata"]["mediaType"]
    assert result.file_size == mock_api_response["extensions"]["fileSize"]
    assert result.created_date == mock_api_response["version"]["when"]
    assert result.version_number == mock_api_response["version"]["number"]
    assert result.download_link == mock_api_response["_links"]["download"]
    assert result.web_ui_link == mock_api_response["_links"]["webui"]
    assert result.comment == mock_api_response["metadata"]["comment"]


@patch('os.path.exists', return_value=True)
@patch('os.path.isfile', return_value=True)
async def test_add_attachment_error_page_not_found(mock_isfile, mock_exists, confluence_client_mock):
    non_existent_page_id = "nonexistentpage123"
    inputs = AddAttachmentInput(
        page_id=non_existent_page_id,
        file_path=MOCK_FILE_PATH,
        filename=MOCK_FILENAME
    )

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_request = Mock()
    mock_request_url = f"http://fake.url/api/content/{non_existent_page_id}/child/attachment"
    mock_request.url = mock_request_url
    mock_response.request = mock_request

    error_instance = ApiError("Page not found during attach") 
    error_instance.response = mock_response
    confluence_client_mock.attach_file.side_effect = error_instance

    with pytest.raises(HTTPException) as exc_info:
        await add_attachment_logic(confluence_client_mock, inputs)

    assert exc_info.value.status_code == 404
    expected_detail = (
        f"Page with ID '{non_existent_page_id}' not found, or attachments cannot be added to it. "
        f"[Confluence API: Status 404, Reason: 'Not Found', URL: '{mock_request_url}']"
    )
    assert exc_info.value.detail == expected_detail


@patch('os.path.exists', return_value=True)
@patch('os.path.isfile', return_value=True)
async def test_add_attachment_error_conflict(mock_isfile, mock_exists, confluence_client_mock):
    inputs = AddAttachmentInput(
        page_id=MOCK_PAGE_ID,
        file_path=MOCK_FILE_PATH,
        filename=MOCK_FILENAME 
    )

    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_request = Mock()
    mock_request_url = f"http://fake.url/api/content/{MOCK_PAGE_ID}/child/attachment"
    mock_request.url = mock_request_url
    mock_response.request = mock_request

    error_instance = ApiError("Conflict during attach")
    error_instance.response = mock_response
    confluence_client_mock.attach_file.side_effect = error_instance

    with pytest.raises(HTTPException) as exc_info:
        await add_attachment_logic(confluence_client_mock, inputs)

    assert exc_info.value.status_code == 409
    # The logic uses inputs.filename or os.path.basename(inputs.file_path) for the name in the message
    conflict_name = inputs.filename or os.path.basename(inputs.file_path)
    expected_detail = (
        f"Conflict adding attachment (e.g., name '{conflict_name}' may already exist and versioning not supported/allowed). "
        f"[Confluence API: Status 409, Reason: 'Conflict', URL: '{mock_request_url}']"
    )
    assert exc_info.value.detail == expected_detail


@patch('os.path.exists', return_value=True)
@patch('os.path.isfile', return_value=True)
async def test_add_attachment_error_other_api_error(mock_isfile, mock_exists, confluence_client_mock):
    inputs = AddAttachmentInput(
        page_id=MOCK_PAGE_ID,
        file_path=MOCK_FILE_PATH,
        filename=MOCK_FILENAME
    )

    mock_response = Mock()
    mock_response.status_code = 500 # Example: Internal Server Error
    mock_response.reason = "Internal Server Error"
    mock_request = Mock()
    mock_request_url = f"http://fake.url/api/content/{MOCK_PAGE_ID}/child/attachment"
    mock_request.url = mock_request_url
    mock_response.request = mock_request

    error_instance = ApiError("Some API Error")
    error_instance.response = mock_response
    confluence_client_mock.attach_file.side_effect = error_instance

    with pytest.raises(HTTPException) as exc_info:
        await add_attachment_logic(confluence_client_mock, inputs)

    assert exc_info.value.status_code == 500
    # The logic uses inputs.filename or os.path.basename(inputs.file_path) for the file name part of the message
    error_file_name = inputs.filename or os.path.basename(inputs.file_path)
    expected_detail = (
        f"Error adding attachment to Confluence: Status 500. Reason: 'Internal Server Error'_ "
        f"URL: '{mock_request_url}'_ "
        f"(Attempted for Page ID: '{MOCK_PAGE_ID}', File: '{error_file_name}')"
    )
    assert exc_info.value.detail == expected_detail


@patch('os.path.exists', return_value=True) 
@patch('os.path.isfile', return_value=True)
async def test_add_attachment_error_unexpected_exception(mock_isfile, mock_exists, confluence_client_mock):
    inputs = AddAttachmentInput(
        page_id=MOCK_PAGE_ID,
        file_path=MOCK_FILE_PATH,
        filename=MOCK_FILENAME
    )
    error_message = "Something went very wrong"
    confluence_client_mock.attach_file.side_effect = Exception(error_message)

    with pytest.raises(HTTPException) as exc_info:
        await add_attachment_logic(confluence_client_mock, inputs)

    assert exc_info.value.status_code == 500
    assert f"An unexpected error occurred while adding attachment: {error_message}" == exc_info.value.detail
