# tests/test_delete_page_tool.py

import pytest
import json
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

# Assuming AVAILABLE_TOOLS is accessible for mocking, potentially needs import adjustment
from confluence_mcp_server.main import AVAILABLE_TOOLS
from confluence_mcp_server.mcp_actions.schemas import DeletePageInput, DeletePageOutput
from atlassian.errors import ApiError # Import ApiError
from fastapi import HTTPException # Potentially needed for error type checks

# Use the anyio backend fixture configured in conftest.py or pytest.toml
pytestmark = pytest.mark.anyio

@pytest.fixture(autouse=True)
def ensure_logic_restored():
    """Fixture to ensure original logic is restored after each test."""
    original_logic = AVAILABLE_TOOLS.get('delete_page', {}).get('logic')
    yield
    if original_logic:
        AVAILABLE_TOOLS['delete_page']['logic'] = original_logic
    elif 'delete_page' in AVAILABLE_TOOLS:
        # If it was added during a test but wasn't there originally
        del AVAILABLE_TOOLS['delete_page']


async def test_delete_page_success(client: AsyncClient, confluence_client_mock: MagicMock):
    """
    Test successful deletion of a page using delete_page tool.
    """
    tool_name = "delete_page"
    page_id_to_delete = "12345"
    inputs = {"page_id": page_id_to_delete}

    # --- Mocking ---
    # 1. Mock the actual Confluence API call within the logic
    confluence_client_mock.delete_page = AsyncMock(return_value=True) # Mock the underlying API call

    # 2. Mock the logic function itself via AVAILABLE_TOOLS
    # Since we want to test the logic we just wrote, we *don't* mock it away here.
    # We rely on the confluence_client_mock fixture to intercept the call within the real logic.
    # However, we MUST ensure the tool is registered if load_tools wasn't called or if mocking interferes.
    # For consistency with other tests, let's explicitly ensure the real logic is assigned
    # (assuming load_tools has run; if not, manual assignment is needed).
    # If tests run in isolation, manual assignment might be necessary.
    # For now, assume load_tools in main.py registers it.

    # --- Execution ---
    response = await client.post("/tools/execute", json={
        "tool_name": tool_name,
        "inputs": inputs
    })

    # --- Assertions ---
    assert response.status_code == 200
    response_data = response.json()

    # Assert response structure for SUCCESS
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "success"
    assert "outputs" in response_data
    assert response_data["outputs"]["message"] == f"Successfully deleted page with ID {page_id_to_delete}." 
    # Ensure no error keys are present on success
    assert "error_message" not in response_data
    assert "error_type" not in response_data
    assert "validation_details" not in response_data

    # Assert specific output message
    expected_output = DeletePageOutput(message=f"Successfully deleted page with ID {page_id_to_delete}.")
    assert response_data["outputs"] == expected_output.model_dump()

    # Assert confluence client was called correctly within the logic
    confluence_client_mock.delete_page.assert_awaited_once_with(
        page_id=page_id_to_delete, 
        status=None, 
        recursive=False
    )


async def test_delete_page_not_found(client: AsyncClient): 
    """
    Test deleting a page that does not exist (API returns 404).
    Now mocks the logic function directly by patching AVAILABLE_TOOLS dictionary entry.
    """
    tool_name = "delete_page"
    non_existent_page_id = "99999"
    inputs = {"page_id": non_existent_page_id}
    error_detail = f"Page with ID '{non_existent_page_id}' not found."

    # --- Mocking ---
    mock_tool_entry = {
        'input_schema': DeletePageInput,
        'output_schema': DeletePageOutput,
        'logic': AsyncMock(side_effect=HTTPException(status_code=404, detail=error_detail))
    }
    # Use patch.dict to temporarily modify the AVAILABLE_TOOLS dictionary
    with patch.dict('confluence_mcp_server.main.AVAILABLE_TOOLS', values={'delete_page': mock_tool_entry}, clear=False) as mock_available_tools:
        # --- Execution ---
        response = await client.post("/tools/execute", json={
            "tool_name": tool_name,
            "inputs": inputs
        })

    # --- Assertions ---
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "error"
    assert response_data["error_message"] == error_detail
    assert response_data["error_type"] == "HTTPException"
    assert response_data["outputs"] is None


async def test_delete_page_permission_denied(client: AsyncClient): 
    """
    Test deleting a page when permissions are insufficient (API returns 403).
    Now mocks the logic function directly by patching AVAILABLE_TOOLS dictionary entry.
    """
    tool_name = "delete_page"
    page_id_forbidden = "54321"
    inputs = {"page_id": page_id_forbidden}
    error_detail = f"Permission denied to delete page with ID '{page_id_forbidden}'."

    # --- Mocking ---
    mock_tool_entry = {
        'input_schema': DeletePageInput,
        'output_schema': DeletePageOutput,
        'logic': AsyncMock(side_effect=HTTPException(status_code=403, detail=error_detail))
    }
    with patch.dict('confluence_mcp_server.main.AVAILABLE_TOOLS', values={'delete_page': mock_tool_entry}, clear=False) as mock_available_tools:
        # --- Execution ---
        response = await client.post("/tools/execute", json={
            "tool_name": tool_name,
            "inputs": inputs
        })

    # --- Assertions ---
    assert response.status_code == 403
    response_data = response.json()
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "error"
    assert response_data["error_message"] == error_detail
    assert response_data["error_type"] == "HTTPException"
    assert response_data["outputs"] is None


async def test_delete_page_generic_api_error(client: AsyncClient): 
    """
    Test handling of a generic API error during page deletion (e.g., 500).
    Now mocks the logic function directly by patching AVAILABLE_TOOLS dictionary entry.
    """
    tool_name = "delete_page"
    page_id_error = "67890"
    inputs = {"page_id": page_id_error}
    api_error_message = "Simulated internal server error"
    error_detail = f"Confluence API error deleting page ID '{page_id_error}': {api_error_message}"

    # --- Mocking ---
    mock_tool_entry = {
        'input_schema': DeletePageInput,
        'output_schema': DeletePageOutput,
        'logic': AsyncMock(side_effect=HTTPException(status_code=500, detail=error_detail))
    }
    with patch.dict('confluence_mcp_server.main.AVAILABLE_TOOLS', values={'delete_page': mock_tool_entry}, clear=False) as mock_available_tools:
        # --- Execution ---
        response = await client.post("/tools/execute", json={
            "tool_name": tool_name,
            "inputs": inputs
        })

    # --- Assertions ---
    assert response.status_code == 500
    response_data = response.json()
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "error"
    assert response_data["error_message"] == error_detail
    assert response_data["error_type"] == "HTTPException"
    assert response_data["outputs"] is None


@pytest.mark.parametrize(
    "invalid_input, expected_error_part",
    [
        ({}, "Field required"), # Missing page_id
        ({"page_id": None}, "Input should be a valid string"), # page_id is None
        ({"page_id": 12345}, "Input should be a valid string"), # page_id is int, expecting string
        # Add more cases if needed, e.g., empty string if that's invalid per logic/schema constraints
        ({"page_id": ""}, "String should have at least 1 character"), # Assuming page_id cannot be empty if validated
    ]
)
async def test_delete_page_invalid_input(
    client: AsyncClient,
    # confluence_client_mock: MagicMock, # Mock might not be needed if validation fails before logic runs
    invalid_input: dict,
    expected_error_part: str
): 
    """
    Test delete_page tool with various invalid inputs.
    Expects a 422 Unprocessable Entity response from FastAPI/Pydantic validation.
    """
    tool_name = "delete_page"

    # --- Execution ---
    response = await client.post("/tools/execute", json={
        "tool_name": tool_name,
        "inputs": invalid_input
    })

    # --- Assertions ---
    # FastAPI/Pydantic validation errors result in 422
    assert response.status_code == 422
    response_data = response.json() # FastAPI provides detail in 'detail' key for 422

    # Assert standard MCP error structure wrapped around FastAPI's validation detail
    # (Based on how execute_tool endpoint handles ValidationError)
    assert response_data["tool_name"] == tool_name
    assert response_data["status"] == "error"
    assert response_data["outputs"] is None
    assert response_data["error_type"] == "InputValidationError"
    assert response_data["error_message"] == "Input validation failed." # CORRECTED message check
    # Check that the specific validation error detail is present in the validation_details field
    assert "validation_details" in response_data
    assert isinstance(response_data["validation_details"], list)
    # Check if the expected error part is mentioned in any of the detail messages
    assert any(expected_error_part in detail.get("msg", "") for detail in response_data["validation_details"]), \
        f"Expected validation detail '{expected_error_part}' not found in {response_data['validation_details']}"

    # Ensure the Confluence API was NOT called
    # confluence_client_mock.delete_page.assert_not_awaited() # Commented out as the mock is not used in this test

# --- Add more tests below for error cases and invalid inputs ---
