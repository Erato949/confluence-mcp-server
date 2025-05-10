# tests/test_main_endpoints.py

import pytest
from httpx import AsyncClient

# Mark all tests in this file for pytest-asyncio with a session-scoped event loop
pytestmark = pytest.mark.asyncio(scope='session')

async def test_health_check(client: AsyncClient):
    """Test the /health endpoint with diagnostics."""
    print(f"DEBUG: Inside test_health_check, client object is: {client}")
    print(f"DEBUG: Type of client object is: {type(client)}")

    # Attempt the GET request
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "message" in data
    assert "confluence_client_status" in data

@pytest.mark.asyncio
async def test_tools_get_spaces_action(client: AsyncClient):
    """Test the /execute endpoint with the 'get_spaces' tool."""
    print(f"DEBUG: Inside test_tools_get_spaces_action, client object is: {client}")
    request_payload = {
        "tool_name": "get_spaces",
        "inputs": {}
    }
    response = await client.post("/execute", json=request_payload)
    assert response.status_code == 200
    data = response.json()

    # Assertions adjusted to observed output structure
    assert data.get("status") == "success"
    assert data.get("tool_name") == "get_spaces"
    assert "outputs" in data
    assert data.get("error_message") is None
    assert data.get("error_type") is None
    
    tool_outputs = data.get("outputs")
    assert tool_outputs is not None
    assert "spaces" in tool_outputs
    assert "count" in tool_outputs
    assert isinstance(tool_outputs.get("spaces"), list)
    assert tool_outputs.get("count") == len(tool_outputs.get("spaces"))

    if tool_outputs.get("spaces"):
        space_item = tool_outputs.get("spaces")[0]
        assert "id" in space_item
        assert "key" in space_item
        assert "name" in space_item
