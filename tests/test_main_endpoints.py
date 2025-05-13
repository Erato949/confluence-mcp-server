# tests/test_main_endpoints.py

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from confluence_mcp_server.main import app, AVAILABLE_TOOLS
from confluence_mcp_server.mcp_actions.schemas import GetSpacesOutput, SpaceSchema, GetSpacesInput

pytestmark = pytest.mark.anyio

async def test_health_check(client: AsyncClient):
    """Test the /health endpoint with diagnostics."""
    print(f"DEBUG: Inside test_health_check, client object is: {client}")
    print(f"DEBUG: Type of client object is: {type(client)}")

    # Attempt the GET request
    response = await client.get("/health")
    assert response.status_code == 200
    # Expect 'initialized' since .env is loaded
    assert response.json() == {"status": "ok", "message": "Confluence MCP Server is running", "confluence_client_status": "initialized"}

async def test_tools_get_spaces_action(client: AsyncClient):
    """Test the /execute endpoint with the 'get_spaces' tool, mocking the logic layer manually."""
    print(f"DEBUG: Inside test_tools_get_spaces_action, client object is: {client}")
    
    tool_name = "get_spaces"
    # Arrange: Define the mock return value for the logic function
    mock_output = GetSpacesOutput(
        spaces=[
            SpaceSchema(id=101, key="API", name="API Space", type="global", status="CURRENT"),
        ],
        count=1,
        total_available=1 # Ensure total_available is provided if known
    )
    
    # Manually create the mock for the logic
    manual_mock_logic = AsyncMock(return_value=mock_output)
    
    # Store original logic and replace it in the dictionary
    original_logic = AVAILABLE_TOOLS[tool_name]["logic"]
    AVAILABLE_TOOLS[tool_name]["logic"] = manual_mock_logic

    try:
        request_payload = {
            "tool_name": tool_name,
            "inputs": {} # Example: use default inputs for GetSpacesInput
        }

        # Act
        response = await client.post("/execute", json=request_payload)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["tool_name"] == tool_name
        
        # Assert based on the mock_output structure
        expected_outputs_dict = mock_output.model_dump()
        assert response_data["outputs"] == expected_outputs_dict

        # Verify the manual mock was called correctly
        manual_mock_logic.assert_awaited_once()
        call_args, call_kwargs = manual_mock_logic.call_args
        assert isinstance(call_kwargs.get('inputs'), GetSpacesInput) # Logic receives parsed input
        # We don't strictly need to check the confluence client passed here
        # as the logic is mocked, but could assert 'client' key exists if needed.

    finally:
        # Restore the original logic
        AVAILABLE_TOOLS[tool_name]["logic"] = original_logic
