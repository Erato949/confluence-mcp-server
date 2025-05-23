"""Tests for the update_confluence_page tool."""

import pytest
import json
from unittest.mock import AsyncMock
import httpx

from fastmcp import Client
from fastmcp.exceptions import ToolError
from confluence_mcp_server.mcp_actions.schemas import UpdatePageInput, UpdatePageOutput


@pytest.mark.anyio
async def test_update_page_success_minimal():
    """Test successful page update with minimal changes (just title)."""
    
    # Mock current page data response
    current_page_data = {
        "id": "12345",
        "title": "Old Title",
        "space": {"key": "TEST"},
        "version": {"number": 2},
        "status": "current"
    }
    
    # Mock updated page data response
    updated_page_data = {
        "id": "12345",
        "title": "New Title",
        "space": {"key": "TEST"},
        "version": {"number": 3, "when": "2024-01-15T10:30:00.000Z"},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/TEST/pages/12345/New+Title"
        }
    }
    
    # Create proper httpx.Response objects
    current_page_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345"),
        json=current_page_data
    )
    
    updated_page_response = httpx.Response(
        200,
        request=httpx.Request("PUT", "http://mock.confluence.com/rest/api/content/12345"),
        json=updated_page_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = current_page_response
    mock_client.put.return_value = updated_page_response
    
    # Test inputs
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=3,
        title="New Title"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    result = await update_page_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, UpdatePageOutput)
    assert result.page_id == "12345"
    assert result.title == "New Title"
    assert result.space_key == "TEST"
    assert result.version == 3
    assert str(result.url) == "https://example.atlassian.net/spaces/TEST/pages/12345/New+Title"
    assert result.last_modified_date == "2024-01-15T10:30:00.000Z"
    
    # Verify API calls
    mock_client.get.assert_called_once_with("/rest/api/content/12345", params={"expand": "body.storage,version,space"})
    
    expected_payload = {
        "version": {"number": 3},
        "type": "page",
        "title": "New Title"
    }
    mock_client.put.assert_called_once_with("/rest/api/content/12345", json=expected_payload)


@pytest.mark.anyio
async def test_update_page_success_full_update():
    """Test successful page update with title, content, and parent changes."""
    
    # Mock current page data response
    current_page_data = {
        "id": "12345",
        "title": "Old Title",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "status": "current"
    }
    
    # Mock updated page data response
    updated_page_data = {
        "id": "12345",
        "title": "Updated Title",
        "space": {"key": "TEST"},
        "version": {"number": 2, "when": "2024-01-15T11:00:00.000Z"},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/TEST/pages/12345/Updated+Title"
        }
    }
    
    # Create proper httpx.Response objects
    current_page_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345"),
        json=current_page_data
    )
    
    updated_page_response = httpx.Response(
        200,
        request=httpx.Request("PUT", "http://mock.confluence.com/rest/api/content/12345"),
        json=updated_page_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = current_page_response
    mock_client.put.return_value = updated_page_response
    
    # Test inputs
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=2,
        title="Updated Title",
        content="<p>New content here</p>",
        parent_page_id="67890"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    result = await update_page_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, UpdatePageOutput)
    assert result.page_id == "12345"
    assert result.title == "Updated Title"
    assert result.space_key == "TEST"
    assert result.version == 2
    
    # Verify API calls
    expected_payload = {
        "version": {"number": 2},
        "type": "page",
        "title": "Updated Title",
        "body": {"storage": {"value": "<p>New content here</p>", "representation": "storage"}},
        "ancestors": [{"id": "67890"}]
    }
    mock_client.put.assert_called_once_with("/rest/api/content/12345", json=expected_payload)


@pytest.mark.anyio
async def test_update_page_error_page_not_found():
    """Test error handling when page is not found."""
    
    # Mock 404 response for getting current page
    not_found_response = httpx.Response(
        404,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345"),
        json={"message": "Page not found"}
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = not_found_response
    
    # Test inputs
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=2,
        title="New Title"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    
    with pytest.raises(Exception) as exc_info:
        await update_page_logic(mock_client, inputs)
    
    assert "Page with ID '12345' not found" in str(exc_info.value)


@pytest.mark.anyio
async def test_update_page_error_version_conflict():
    """Test error handling for version conflicts."""
    
    # Mock current page data response
    current_page_data = {
        "id": "12345",
        "title": "Current Title",
        "space": {"key": "TEST"},
        "version": {"number": 5},  # Current version is 5
        "status": "current"
    }
    
    current_page_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345"),
        json=current_page_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = current_page_response
    
    # Test inputs with wrong version number (should be 6, but providing 4)
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=4,  # Wrong version
        title="New Title"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    
    with pytest.raises(Exception) as exc_info:
        await update_page_logic(mock_client, inputs)
    
    error_message = str(exc_info.value)
    assert "Version conflict" in error_message
    assert "Current page version is 5" in error_message
    assert "supplied next version is 4" in error_message
    assert "Expected next version to be 6" in error_message


@pytest.mark.anyio
async def test_update_page_error_api_error():
    """Test error handling for API errors during update."""
    
    # Mock current page data response (successful)
    current_page_data = {
        "id": "12345",
        "title": "Current Title",
        "space": {"key": "TEST"},
        "version": {"number": 2},
        "status": "current"
    }
    
    current_page_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345"),
        json=current_page_data
    )
    
    # Mock 500 error response for the update
    error_response = httpx.Response(
        500,
        request=httpx.Request("PUT", "http://mock.confluence.com/rest/api/content/12345"),
        json={"message": "Internal Server Error"}
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = current_page_response
    mock_client.put.return_value = error_response
    
    # Test inputs
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=3,
        title="New Title"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    
    with pytest.raises(Exception) as exc_info:
        await update_page_logic(mock_client, inputs)
    
    assert "Error updating page" in str(exc_info.value)


@pytest.mark.anyio
async def test_update_page_error_connection_error():
    """Test error handling for connection errors."""
    
    # Create a proper request object for the RequestError
    request = httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345")
    
    # Mock connection error with proper request
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.RequestError("Connection failed", request=request)
    
    # Test inputs
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=2,
        title="New Title"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    
    with pytest.raises(Exception) as exc_info:
        await update_page_logic(mock_client, inputs)
    
    assert "Error connecting to Confluence" in str(exc_info.value)


@pytest.mark.anyio
async def test_update_page_make_top_level_page():
    """Test updating a page to make it a top-level page (remove parent)."""
    
    # Mock current page data response
    current_page_data = {
        "id": "12345",
        "title": "Child Page",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "status": "current"
    }
    
    # Mock updated page data response
    updated_page_data = {
        "id": "12345",
        "title": "Top Level Page",
        "space": {"key": "TEST"},
        "version": {"number": 2, "when": "2024-01-15T12:00:00.000Z"},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/TEST/pages/12345/Top+Level+Page"
        }
    }
    
    # Create proper httpx.Response objects
    current_page_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/12345"),
        json=current_page_data
    )
    
    updated_page_response = httpx.Response(
        200,
        request=httpx.Request("PUT", "http://mock.confluence.com/rest/api/content/12345"),
        json=updated_page_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = current_page_response
    mock_client.put.return_value = updated_page_response
    
    # Test inputs with empty string for parent_page_id (make top-level)
    inputs = UpdatePageInput(
        page_id="12345",
        new_version_number=2,
        title="Top Level Page",
        parent_page_id=""  # Empty string means make it top-level
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import update_page_logic
    result = await update_page_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, UpdatePageOutput)
    assert result.page_id == "12345"
    assert result.title == "Top Level Page"
    
    # Verify API calls - should set ancestors to empty array
    expected_payload = {
        "version": {"number": 2},
        "type": "page",
        "title": "Top Level Page",
        "ancestors": []  # Empty array for top-level page
    }
    mock_client.put.assert_called_once_with("/rest/api/content/12345", json=expected_payload)


# MCP Tool Tests
@pytest.mark.anyio
async def test_update_page_tool_via_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the update_page tool through the MCP interface."""
    
    # Mock current page data response
    current_page_data = {
        "id": "tool-test-12345",
        "title": "Original Title",
        "space": {"key": "MCPTEST"},
        "version": {"number": 1},
        "status": "current"
    }
    
    # Mock updated page data response
    updated_page_data = {
        "id": "tool-test-12345",
        "title": "MCP Updated Title",
        "space": {"key": "MCPTEST"},
        "version": {"number": 2, "when": "2024-01-15T13:00:00.000Z"},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/MCPTEST/pages/tool-test-12345/MCP+Updated+Title"
        }
    }
    
    current_page_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/tool-test-12345"),
        json=current_page_data
    )
    
    updated_page_response = httpx.Response(
        200,
        request=httpx.Request("PUT", "http://mock.confluence.com/rest/api/content/tool-test-12345"),
        json=updated_page_data
    )
    
    mock_httpx_async_client.get.return_value = current_page_response
    mock_httpx_async_client.put.return_value = updated_page_response
    
    # Test MCP tool call
    result = await mcp_client.call_tool(
        "update_confluence_page",
        {"inputs": {
            "page_id": "tool-test-12345",
            "new_version_number": 2,
            "title": "MCP Updated Title",
            "content": "<p>Updated via MCP</p>"
        }}
    )
    
    # Verify result structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == "text"
    
    # Parse the JSON response
    response_data = json.loads(result[0].text)
    assert response_data["page_id"] == "tool-test-12345"
    assert response_data["title"] == "MCP Updated Title"
    assert response_data["space_key"] == "MCPTEST"
    assert response_data["version"] == 2


@pytest.mark.anyio
async def test_update_page_tool_invalid_input_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the update_page tool with invalid input through MCP interface."""
    
    # Test MCP tool call with missing required fields
    with pytest.raises(ToolError):
        await mcp_client.call_tool(
            "update_confluence_page",
            {"inputs": {
                "page_id": "12345",
                "new_version_number": 2
                # Missing any updatable fields (title, content, parent_page_id)
            }}
        )


@pytest.mark.anyio
async def test_update_page_tool_api_error_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the update_page tool API error handling through MCP interface."""
    
    # Mock 404 response
    not_found_response = httpx.Response(
        404,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/nonexistent"),
        json={"message": "Page not found"}
    )
    
    mock_httpx_async_client.get.return_value = not_found_response
    
    # Test MCP tool call
    with pytest.raises(ToolError):
        await mcp_client.call_tool(
            "update_confluence_page",
            {"inputs": {
                "page_id": "nonexistent",
                "new_version_number": 2,
                "title": "New Title"
            }}
        ) 