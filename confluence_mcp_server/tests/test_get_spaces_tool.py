import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from confluence_mcp_server.mcp_actions.schemas import GetSpacesOutput, SpaceSchema

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
    """Test successful execution of get_spaces tool with the limit parameter."""
    limit_value = 1
    mock_spaces_data_full = {
        "results": [
            {"id": 123, "key": "SPACE1", "name": "My First Space", "type": "global", "status": "CURRENT"},
            {"id": 456, "key": "DEV", "name": "Development Space", "type": "global", "status": "CURRENT"},
            {"id": 789, "key": "PROD", "name": "Production Space", "type": "global", "status": "CURRENT"}
        ],
        "start": 0,
        "limit": 3, # Mock API might return more than requested limit due to its own pagination
        "size": 3
    }

    # Expected output should respect the limit_value applied by our tool's logic
    expected_limited_spaces = [
        SpaceSchema(id=123, key="SPACE1", name="My First Space", type="global", status="CURRENT")
    ]

    mock_confluence_instance = MagicMock()
    # The actual call to get_all_spaces will use effective_limit_for_fetch
    # which defaults to inputs.limit if max_results_to_fetch is not set.
    mock_confluence_instance.get_all_spaces.return_value = mock_spaces_data_full

    with patch('confluence_mcp_server.main.get_confluence_client', return_value=mock_confluence_instance) as mock_get_client:
        request_payload = {
            "tool_name": "get_spaces",
            "inputs": {"limit": limit_value}
        }

        response = await client.post("/execute", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["tool_name"] == "get_spaces"
        assert response_json["status"] == "success"
        assert "outputs" in response_json
       
        api_output = GetSpacesOutput(**response_json["outputs"])
       
        assert len(api_output.spaces) == limit_value
        assert api_output.count == limit_value
        for i, space_out in enumerate(api_output.spaces):
            assert space_out.id == expected_limited_spaces[i].id
            assert space_out.key == expected_limited_spaces[i].key
            assert space_out.name == expected_limited_spaces[i].name
            assert space_out.type == expected_limited_spaces[i].type
            assert space_out.status == expected_limited_spaces[i].status

        # get_spaces_logic might call get_all_spaces with limit=limit_value
        # or it might fetch more and then slice. The most robust check for the mock
        # is that it was called. The exact args might vary if max_results_to_fetch is involved.
        # For this test, assuming max_results_to_fetch is not set in inputs, 
        # effective_limit_for_fetch in get_spaces_logic should be limit_value.
        mock_confluence_instance.get_all_spaces.assert_called_once_with(limit=limit_value)
