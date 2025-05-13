# Test file for the Add_Attachment tool endpoint
import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from atlassian.errors import ApiError

from httpx import AsyncClient
from fastapi.testclient import TestClient # For creating temp files if needed with app context

from confluence_mcp_server.main import app # FastAPI app instance
# Assuming the Confluence client is initialized in main.py and accessible for patching
# e.g., from confluence_mcp_server.main import client as global_confluence_client

# Mock data similar to what's in test_attachment_actions.py
MOCK_PAGE_ID_TOOL = "t12345"
MOCK_FILENAME_TOOL = "tool_attachment.txt"
MOCK_COMMENT_TOOL = "Tool test attachment comment."
MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL = {
    'id': 'attToolNew789',
    'type': 'attachment',
    'status': 'current',
    'title': MOCK_FILENAME_TOOL,
    'metadata': {'mediaType': 'text/plain', 'comment': MOCK_COMMENT_TOOL},
    'version': {'number': 1, 'when': '2023-10-28T12:00:00.000Z'},
    'extensions': {'fileSize': 54321},
    '_links': {'webui': f'/display/SPACE/Page?preview=/attToolNew789/{MOCK_FILENAME_TOOL}', 'download': f'/download/attToolNew789/{MOCK_FILENAME_TOOL}'}
}

pytestmark = pytest.mark.anyio

@pytest.fixture
def temp_file():
    # Create a temporary file that actually exists for the test
    # tempfile.NamedTemporaryFile creates a file and deletes it on close.
    # We need to ensure it's not deleted before the test client uses it.
    # For robust testing, it's often easier to manage creation and deletion manually or ensure it persists for the test's duration.
    # Here, we'll create it, write to it, and provide its path.
    # The test itself will be responsible if it needs to ensure closure/deletion *after* the client call if the file handle is passed around.
    # However, for sending file paths to an API, the file just needs to exist at the time of Pydantic validation.
    
    fd, path = tempfile.mkstemp(suffix='.txt', prefix='test_attach_')
    with os.fdopen(fd, 'w') as tmp:
        tmp.write("This is a test file for attachment upload.")
    yield path
    os.remove(path) # Cleanup

@patch('confluence_mcp_server.main.get_confluence_client') # Patch where get_confluence_client is defined and used by endpoints
async def test_add_attachment_tool_success(mock_get_confluence_client, temp_file, client: AsyncClient):
    mock_confluence_instance = MagicMock()
    mock_confluence_instance.attach_file.return_value = MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL
    mock_get_confluence_client.return_value = mock_confluence_instance

    payload = {
        "tool_name": "Add-Attachment",
        "inputs": {
            "page_id": MOCK_PAGE_ID_TOOL,
            "file_path": temp_file, # Use the actual path of the temporary file
            "filename": MOCK_FILENAME_TOOL,
            "comment": MOCK_COMMENT_TOOL
        }
    }

    response = await client.post("/tools/execute", json=payload)

    print(f"DEBUG: Response Status Code: {response.status_code}")
    print(f"DEBUG: Response JSON: {response.json()}")

    assert response.status_code == 200
    response_data = response.json()
    
    # Check if the structure matches AddAttachmentOutput
    assert response_data["outputs"]["attachment_id"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['id']
    assert response_data["outputs"]["title"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['title']
    assert response_data["outputs"]["status"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['status']
    assert response_data["outputs"]["media_type"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['metadata']['mediaType']
    assert response_data["outputs"]["file_size"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['extensions']['fileSize']
    assert response_data["outputs"]["created_date"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['version']['when']
    assert response_data["outputs"]["version_number"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['version']['number']
    assert response_data["outputs"]["download_link"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['_links']['download']
    assert response_data["outputs"]["web_ui_link"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['_links']['webui']
    # The input comment is for the upload action, the response_comment is what API might return as stored with the attachment
    assert response_data["outputs"]["comment"] == MOCK_UPLOADED_ATTACHMENT_API_RESPONSE_TOOL['metadata']['comment']

    mock_confluence_instance.attach_file.assert_called_once_with(
        page_id=MOCK_PAGE_ID_TOOL,
        filepath=temp_file,
        name=MOCK_FILENAME_TOOL,
        comment=MOCK_COMMENT_TOOL,
        content_type=None
    )

async def test_add_attachment_tool_error_missing_filepath(client: AsyncClient):
    payload = {
        "tool_name": "Add-Attachment",
        "inputs": {
            "page_id": MOCK_PAGE_ID_TOOL,
            # "file_path": "/some/path/file.txt", # Intentionally missing
            "filename": MOCK_FILENAME_TOOL
        }
    }

    response = await client.post("/tools/execute", json=payload)

    assert response.status_code == 422 # InputValidationError
    response_data = response.json()
    assert response_data["error_type"] == "InputValidationError"
    assert "validation_details" in response_data
    # Check for the specific missing field error
    found_error = False
    for error_detail in response_data["validation_details"]:
        if error_detail["loc"] == ["file_path"] and error_detail["type"] == "missing":
            found_error = True
            break
    assert found_error, "Error detail for missing file_path not found"


async def test_add_attachment_tool_error_filepath_not_exists(client: AsyncClient):
    non_existent_path = "/path/to/a/very/non_existent/file/that/should/not/be/there.txt"
    payload = {
        "tool_name": "Add-Attachment",
        "inputs": {
            "page_id": MOCK_PAGE_ID_TOOL,
            "file_path": non_existent_path,
            "filename": MOCK_FILENAME_TOOL
        }
    }

    response = await client.post("/tools/execute", json=payload)

    assert response.status_code == 422 # InputValidationError from Pydantic model
    response_data = response.json()
    assert response_data["error_type"] == "InputValidationError"
    assert "validation_details" in response_data
    found_error = False
    for error_detail in response_data["validation_details"]:
        # Pydantic v2 style for validator errors on fields
        if error_detail["loc"] == ["file_path"] and "File not found at path" in error_detail["msg"]:
            found_error = True
            break
    assert found_error, f"Specific file not found error not in validation_details: {response_data['validation_details']}"



@patch('confluence_mcp_server.main.get_confluence_client')
async def test_add_attachment_tool_error_api_page_not_found(mock_get_confluence_client, temp_file, client: AsyncClient):
    mock_confluence_instance = MagicMock()

    # Simulate ApiError for page not found
    mock_api_error_response = MagicMock()
    mock_api_error_response.status_code = 404
    mock_api_error_response.reason = "Not Found"
    mock_api_error_request = MagicMock()
    # Note: The URL might be constructed by the underlying atlassian-python-api library,
    # so for mocking, it's often enough that the status code and reason are correct.
    # However, if the logic specifically uses response.request.url, it should be mocked accurately.
    mock_api_error_request.url = f"http://fake.url/api/content/{MOCK_PAGE_ID_TOOL}/child/attachment"
    mock_api_error_response.request = mock_api_error_request

    api_error = ApiError("Page not found from API")
    api_error.response = mock_api_error_response
    mock_confluence_instance.attach_file.side_effect = api_error

    mock_get_confluence_client.return_value = mock_confluence_instance

    payload = {
        "tool_name": "Add-Attachment",
        "inputs": {
            "page_id": MOCK_PAGE_ID_TOOL,
            "file_path": temp_file,
            "filename": MOCK_FILENAME_TOOL
        }
    }

    response = await client.post("/tools/execute", json=payload)

    assert response.status_code == 404 # This comes from the custom ApiError handler in main.py
    response_data = response.json()
    assert response_data["tool_name"] == "Add-Attachment" # or a guessed name if logic fails early
    assert response_data["status"] == "error"
    assert response_data["error_type"] == "HTTPException"
    # The custom ApiError handler in main.py constructs a specific error_detail string.
    # The attachment_actions.py logic raises an HTTPException for 404 from ApiError.
    # Let's check for the expected detail string from the add_attachment_logic's HTTPException
    expected_detail_string = f"Page with ID '{MOCK_PAGE_ID_TOOL}' not found, or attachments cannot be added to it. [Confluence API: Status 404, Reason: 'Not Found', URL: 'http://fake.url/api/content/{MOCK_PAGE_ID_TOOL}/child/attachment']"
    assert response_data["error_message"] == expected_detail_string
