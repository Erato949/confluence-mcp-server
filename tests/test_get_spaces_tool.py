import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock

from confluence_mcp_server.main import app, AVAILABLE_TOOLS
from confluence_mcp_server.mcp_actions.schemas import (
    MCPExecuteRequest,
    GetSpacesInput, 
    GetSpacesOutput,
    SpaceSchema
)

@pytest.mark.asyncio
async def test_get_spaces_no_input_successful(client: AsyncClient):
    """Test successful execution of get_spaces tool with no inputs."""
    mock_spaces_data = {
        "results": [
            {"id": 123, "key": "SPACE1", "name": "My First Space", "type": "global", "status": "CURRENT"},
            {"id": 456, "key": "DEV", "name": "Development Space", "type": "global", "status": "CURRENT"}
        ],
        "start": 0,
        "limit": 2,
        "size": 2
    }

    expected_output_spaces = [
        SpaceSchema(id=123, key="SPACE1", name="My First Space", type="global", status="CURRENT"),
        SpaceSchema(id=456, key="DEV", name="Development Space", type="global", status="CURRENT")
    ]

    mock_confluence_instance = MagicMock()
    mock_confluence_instance.get_all_spaces.return_value = mock_spaces_data

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {}
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json is not None, "Response JSON should not be None"
        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status

        mock_confluence_instance.get_all_spaces.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_spaces_with_limit(client: AsyncClient): 
    limit_value = 1
    payload = {
        "tool_name": "get_spaces",
        "inputs": {"limit": limit_value}
    }

    # Define the full set of spaces the API *could* return
    all_mock_spaces_data = [
        {"id": "123", "key": "SPACE1", "name": "My First Space", "type": "global", "status": "CURRENT"},
        {"id": "456", "key": "DEV", "name": "Development Space", "type": "global", "status": "CURRENT"},
        {"id": "789", "key": "PROD", "name": "Production Space", "type": "global", "status": "CURRENT"}
    ]

    # Define a side_effect function for get_all_spaces
    def mock_get_all_spaces_side_effect(*args, **kwargs):
        limit = kwargs.get('limit')
        start = kwargs.get('start', 0) # Default start to 0 if not provided
        
        # Slice the data based on start and limit
        # If limit is None, slice to the end. Python handles None in slices appropriately.
        end = None if limit is None else start + limit
        sliced_results = all_mock_spaces_data[start:end]
        
        return {
            "results": sliced_results,
            "start": start,
            "limit": limit if limit is not None else len(sliced_results), # API might report requested limit or actual size
            "size": len(sliced_results),
            "_links": {}
        }

    local_mock_confluence_instance = MagicMock()
    local_mock_confluence_instance.get_all_spaces.side_effect = mock_get_all_spaces_side_effect
    
    # Expected output based on the limit
    expected_output_spaces = [
        SpaceSchema(id=123, key="SPACE1", name="My First Space", type="global", status="CURRENT")
    ]

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=local_mock_confluence_instance) as mock_get_client:
        response = await client.post("/execute", json=payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == limit_value
        assert api_output.count == limit_value
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status

        local_mock_confluence_instance.get_all_spaces.assert_called_once_with(
            limit=limit_value
            # No other params expected if not provided in inputs and defaults are None
        )


@pytest.mark.asyncio
async def test_get_spaces_with_start(client: AsyncClient):
    """Test successful execution of get_spaces tool with the start parameter."""
    start_value = 1
    limit_value = 1 # Keep limit small to easily verify the offset

    # Mock data representing the full list if API was called with start=0, limit=3
    # However, our test will call it with start=1, limit=1
    mock_api_response_for_call = {
        "results": [
            # This space should be returned if API is called with start=1, limit=1
            {"id": 456, "key": "DEV", "name": "Development Space", "type": "global", "status": "CURRENT"}
        ],
        "start": start_value, # API confirms its start
        "limit": limit_value, # API confirms its limit
        "size": 1 # API confirms total size of this specific paginated response
    }

    # This is what we expect in the final MCP output
    expected_output_spaces = [
        SpaceSchema(id=456, key="DEV", name="Development Space", type="global", status="CURRENT")
    ]

    mock_confluence_instance = MagicMock()
    mock_confluence_instance.get_all_spaces.return_value = mock_api_response_for_call

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {"start": start_value, "limit": limit_value}
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        assert api_output.count == len(expected_output_spaces) # Count should reflect the number of items returned in this batch
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status

        # Assert that get_all_spaces was called with the correct start and limit
        mock_confluence_instance.get_all_spaces.assert_called_once_with(
            start=start_value,
            limit=limit_value
            # No other params expected if not provided in inputs and defaults are None
        )


@pytest.mark.asyncio
async def test_get_spaces_with_space_ids(client: AsyncClient):
    """Test successful execution of get_spaces tool with the space_ids parameter."""
    space_id_to_fetch = 123
    mock_space_data = { # Data for a single space, as if fetched by ID
        "id": space_id_to_fetch, 
        "key": "SPACE1", 
        "name": "My Specific Space", 
        "type": "global", 
        "status": "CURRENT"
    }

    # The get_all_spaces when filtered by a single ID might return it in a 'results' list
    # or it might be a direct object. The atlassian-python-api.get_space(space_id=...)
    # returns a dict. get_all_spaces is typically for broader queries.
    # Let's assume our logic iterates and calls get_space for each ID in space_ids.
    # Or, if get_all_spaces *can* take a list of IDs, we mock that.
    # The doc for atlassian-python-api's get_all_spaces indicates space_id is singular.
    # So, the logic in `space_actions.py` would likely loop through `inputs.space_ids`
    # and call `confluence.get_space(space_id=sid)` for each.
    # For this test, we will mock `confluence.get_space`.

    expected_output_spaces = [
        SpaceSchema(id=space_id_to_fetch, key="SPACE1", name="My Specific Space", type="global", status="CURRENT")
    ]

    mock_confluence_instance = MagicMock()
    # Mocking get_space as it's more direct for fetching by a single ID
    mock_confluence_instance.get_space.return_value = mock_space_data

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {"space_ids": [space_id_to_fetch]} # Pass as a list, even if one
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        assert api_output.count == len(expected_output_spaces)
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status

        # Assert that get_space was called correctly, not get_all_spaces
        mock_confluence_instance.get_space.assert_called_once_with(
            space_id=str(space_id_to_fetch) # API client expects string ID
        )
        mock_confluence_instance.get_all_spaces.assert_not_called() # Ensure get_all_spaces wasn't called


@pytest.mark.asyncio
async def test_get_spaces_with_space_keys(client: AsyncClient):
    """Test successful execution of get_spaces tool with the space_keys parameter."""
    space_key_to_fetch = "TESTKEY"
    mock_space_data = { # Data for a single space, as if fetched by key
        "id": 789, 
        "key": space_key_to_fetch, 
        "name": "My Specific Keyed Space", 
        "type": "global", 
        "status": "CURRENT"
    }

    # Similar to space_ids, the logic in `space_actions.py` should iterate 
    # through `inputs.space_keys` and call `confluence.get_space(space_key=skey)` for each.
    # This test will mock `confluence.get_space`.

    expected_output_spaces = [
        SpaceSchema(id=789, key=space_key_to_fetch, name="My Specific Keyed Space", type="global", status="CURRENT")
    ]

    mock_confluence_instance = MagicMock()
    mock_confluence_instance.get_space.return_value = mock_space_data

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {"space_keys": [space_key_to_fetch]} # Pass as a list
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        assert api_output.count == len(expected_output_spaces)
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status
            
        # Assert that get_space was called correctly
        mock_confluence_instance.get_space.assert_called_once_with(
            space_key=space_key_to_fetch
        )
        mock_confluence_instance.get_all_spaces.assert_not_called()


@pytest.mark.asyncio
async def test_get_spaces_with_space_type(client: AsyncClient):
    """Test successful execution of get_spaces tool with the space_type parameter."""
    space_type_value = "personal"
    mock_spaces_data = {
        "results": [
            {"id": 101, "key": "PERS", "name": "Personal Space 1", "type": "personal", "status": "CURRENT"},
        ],
        "start": 0,
        "limit": 1,
        "size": 1
    }

    expected_output_spaces = [
        SpaceSchema(id=101, key="PERS", name="Personal Space 1", type="personal", status="CURRENT")
    ]

    mock_confluence_instance = MagicMock()
    mock_confluence_instance.get_all_spaces.return_value = mock_spaces_data

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {"space_type": space_type_value, "limit": 1} # Added limit for predictability
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        assert api_output.count == len(expected_output_spaces)
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type # Verify type matches
            assert space_out.status == expected_output_spaces[i].status

        # Assert that get_all_spaces was called with the correct parameters
        mock_confluence_instance.get_all_spaces.assert_called_once_with(
            space_type=space_type_value,
            limit=1 # Ensure other params passed are as expected
        )


@pytest.mark.asyncio
async def test_get_spaces_with_space_status(client: AsyncClient):
    """Test successful execution of get_spaces tool with the space_status parameter."""
    space_status_value = "archived"
    mock_spaces_data = {
        "results": [
            {"id": 202, "key": "ARCH", "name": "Archived Project Space", "type": "global", "status": "archived"},
        ],
        "start": 0,
        "limit": 1,
        "size": 1
    }

    expected_output_spaces = [
        SpaceSchema(id=202, key="ARCH", name="Archived Project Space", type="global", status="archived")
    ]

    mock_confluence_instance = MagicMock()
    mock_confluence_instance.get_all_spaces.return_value = mock_spaces_data

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {"status": space_status_value, "limit": 1} # Added limit
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        assert api_output.count == len(expected_output_spaces)
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status # Verify status matches

        # Assert that get_all_spaces was called with the correct parameters    
        mock_confluence_instance.get_all_spaces.assert_called_once_with(
            status=space_status_value,
            limit=1
        )


@pytest.mark.asyncio
async def test_get_spaces_with_combination_of_parameters(client: AsyncClient):
    """Test successful execution with a combination of limit, space_type, and status."""
    limit_value = 1
    space_type_value = "personal"
    status_value = "current"

    mock_spaces_data = {
        "results": [
            {"id": 303, "key": "COMBO", "name": "Combo Personal Current", "type": "personal", "status": "current"},
        ],
        "start": 0,
        "limit": limit_value,
        "size": 1
    }

    expected_output_spaces = [
        SpaceSchema(id=303, key="COMBO", name="Combo Personal Current", type="personal", status="current")
    ]

    mock_confluence_instance = MagicMock()
    mock_confluence_instance.get_all_spaces.return_value = mock_spaces_data

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {
                "limit": limit_value,
                "space_type": space_type_value,
                "status": status_value
            }
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == len(expected_output_spaces)
        assert api_output.count == len(expected_output_spaces)
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_output_spaces[i].id
            assert space_out.key == expected_output_spaces[i].key
            assert space_out.name == expected_output_spaces[i].name
            assert space_out.type == expected_output_spaces[i].type
            assert space_out.status == expected_output_spaces[i].status

        # Assert that get_all_spaces was called with the correct parameters
        mock_confluence_instance.get_all_spaces.assert_called_once_with(
            limit=limit_value,
            space_type=space_type_value,
            status=status_value
        )


@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_spaces_successful(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful retrieval of spaces using manual logic mock."""
    inputs = {
        # Optional: Add inputs like 'limit', 'start', 'type' if needed for the test
    }

    # Mock the response that the *real* logic would get from the client
    mock_api_response = {
        "results": [
            {"id": 101, "key": "DS", "name": "Demonstration Space", "type": "global", "status": "current"},
            {"id": 102, "key": "PS", "name": "Project Space", "type": "global", "status": "current"}
        ],
        "start": 0,
        "limit": 2,
        "size": 2
    }
    # Set up the mock get_client to return our mocked confluence client first
    mock_get_client.return_value = confluence_client_mock
    confluence_client_mock.get_all_spaces.return_value = mock_api_response

    # Define the expected output that the *manual mock* should return
    # (or what the real logic would return given the mock_api_response)
    expected_spaces = [
        SpaceSchema(id=101, key="DS", name="Demonstration Space", type="global", status="current"),
        SpaceSchema(id=102, key="PS", name="Project Space", type="global", status="current")
    ]
    expected_output_model = GetSpacesOutput(
        spaces=expected_spaces, 
        count=len(expected_spaces), 
        total_available=mock_api_response["size"]
    )

    # Create and configure the manual mock for the logic function
    manual_mock_logic = AsyncMock()
    manual_mock_logic.return_value = expected_output_model

    # Store original logic and replace it with the mock
    original_logic = AVAILABLE_TOOLS["get_spaces"]["logic"]
    AVAILABLE_TOOLS["get_spaces"]["logic"] = manual_mock_logic

    try:
        request_payload = MCPExecuteRequest(
            tool_name="get_spaces",
            inputs=GetSpacesInput(**inputs).model_dump(exclude_none=True)
        )

        response = await client.post("/execute", json=request_payload.model_dump()) # Keep model_dump for now

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "success"
        assert response_data["tool_name"] == "get_spaces"
        assert response_data["outputs"] == expected_output_model.model_dump(exclude_none=True)

        # Assert the *manual mock* logic function was called
        manual_mock_logic.assert_awaited_once()

        # Assert the underlying confluence client method was *not* called directly by the test
        # (it would have been called inside the *real* logic if we hadn't mocked it)
        # Since we mocked the logic itself, the client method won't be called in this flow.
        confluence_client_mock.get_all_spaces.assert_not_called()

        # Assert the get_confluence_client function *was* called by main.py
        mock_get_client.assert_called_once()

    finally:
        # Restore the original logic function
        AVAILABLE_TOOLS["get_spaces"]["logic"] = original_logic


@pytest.mark.asyncio
@patch('confluence_mcp_server.main.get_confluence_client') # Keep mocking client retrieval
async def test_get_spaces_no_match(mock_get_client, client: AsyncClient, confluence_client_mock: MagicMock):
    """Test successful execution of get_spaces when the logic function returns no results (manual mock)."""
    # Arrange: Setup mock logic to return empty output
    expected_empty_output = GetSpacesOutput(spaces=[], count=0, total_available=0)
    
    manual_mock_logic = AsyncMock()
    manual_mock_logic.return_value = expected_empty_output

    # Mock the confluence client retrieval, though it won't be used by the mocked logic directly
    mock_get_client.return_value = confluence_client_mock

    original_logic = AVAILABLE_TOOLS["get_spaces"]["logic"]
    AVAILABLE_TOOLS["get_spaces"]["logic"] = manual_mock_logic

    try:
        request_payload = MCPExecuteRequest(
            tool_name="get_spaces",
            inputs=GetSpacesInput(space_type="non_existent").model_dump() # Input likely to yield no results
        )

        # Act
        response = await client.post("/execute", json=request_payload.model_dump()) # Changed .dict() to .model_dump()

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["tool_name"] == "get_spaces"
        assert response_data["outputs"] == expected_empty_output.model_dump(exclude_none=True)
        
        manual_mock_logic.assert_awaited_once()
        # Ensure the actual client API was not called because the logic was mocked
        confluence_client_mock.get_all_spaces.assert_not_called()
        mock_get_client.assert_called_once()

    finally:
        AVAILABLE_TOOLS["get_spaces"]["logic"] = original_logic


# --- API Error Handling Tests ---
