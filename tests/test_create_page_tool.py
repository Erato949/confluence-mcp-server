"""Tests for the create_confluence_page tool."""

import pytest
import json
from unittest.mock import AsyncMock
import httpx

from fastmcp import Client
from fastmcp.exceptions import ToolError
from confluence_mcp_server.mcp_actions.schemas import CreatePageInput, CreatePageOutput


@pytest.mark.anyio
async def test_create_page_success_minimal():
    """Test successful page creation with minimal required fields."""
    
    # Mock API response data
    mock_response_data = {
        "id": "12345",
        "title": "Test Page",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/TEST/pages/12345/Test+Page"
        }
    }
    
    # Create proper httpx.Response object
    mock_api_response = httpx.Response(
        201,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json=mock_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_api_response)
    mock_client.base_url = "https://example.atlassian.net"
    
    # Test inputs
    inputs = CreatePageInput(
        space_key="TEST",
        title="Test Page", 
        content="<p>This is a test page content.</p>"
    )
    
    # Import and call the logic function directly
    from confluence_mcp_server.mcp_actions.page_actions import create_page_logic
    result = await create_page_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, CreatePageOutput)
    assert result.page_id == "12345"
    assert result.title == "Test Page"
    assert result.space_key == "TEST"
    assert result.version == 1
    assert result.status == "current"
    assert "Test+Page" in str(result.url)
    
    # Verify the API call was made correctly
    mock_client.post.assert_called_once_with(
        "/rest/api/content",
        json={
            "type": "page",
            "title": "Test Page",
            "space": {"key": "TEST"},
            "body": {
                "storage": {
                    "value": "<p>This is a test page content.</p>",
                    "representation": "storage"
                }
            }
        }
    )


@pytest.mark.anyio
async def test_create_page_success_with_parent():
    """Test successful page creation with parent page specified."""
    
    # Mock API response data
    mock_response_data = {
        "id": "67890",
        "title": "Child Page",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/TEST/pages/67890/Child+Page"
        },
        "ancestors": [{"id": "11111"}]
    }
    
    # Create proper httpx.Response object
    mock_api_response = httpx.Response(
        201,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json=mock_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_api_response)
    mock_client.base_url = "https://example.atlassian.net"
    
    # Test inputs with parent
    inputs = CreatePageInput(
        space_key="TEST",
        title="Child Page",
        content="<p>This is a child page.</p>",
        parent_page_id="11111"
    )
    
    # Import and call the logic function directly
    from confluence_mcp_server.mcp_actions.page_actions import create_page_logic
    result = await create_page_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, CreatePageOutput)
    assert result.page_id == "67890"
    assert result.title == "Child Page"
    assert result.space_key == "TEST"
    assert result.version == 1
    
    # Verify the API call included parent page
    expected_payload = {
        "type": "page",
        "title": "Child Page",
        "space": {"key": "TEST"},
        "body": {
            "storage": {
                "value": "<p>This is a child page.</p>",
                "representation": "storage"
            }
        },
        "ancestors": [{"id": "11111"}]
    }
    mock_client.post.assert_called_once_with("/rest/api/content", json=expected_payload)


@pytest.mark.anyio
async def test_create_page_error_title_already_exists():
    """Test error handling when page title already exists in space."""
    
    # Mock 400 error response for duplicate title
    mock_api_response = httpx.Response(
        400,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json={
            "data": {
                "errors": [{
                    "message": {
                        "translation": "A page with this title already exists in this space."
                    }
                }]
            }
        }
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_api_response)
    
    # Test inputs
    inputs = CreatePageInput(
        space_key="TEST",
        title="Duplicate Title",
        content="<p>Content</p>"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import create_page_logic
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await create_page_logic(mock_client, inputs)
    
    assert exc_info.value.status_code == 400
    assert "A page titled 'Duplicate Title' already exists in space 'TEST'" in exc_info.value.detail


@pytest.mark.anyio
async def test_create_page_error_space_not_found():
    """Test error handling when space does not exist."""
    
    # Mock 404 error response for missing space
    mock_api_response = httpx.Response(
        404,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json={
            "message": "Space 'NONEXISTENT' does not exist."
        }
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_api_response)
    
    # Test inputs
    inputs = CreatePageInput(
        space_key="NONEXISTENT",
        title="Test Page",
        content="<p>Content</p>"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import create_page_logic
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await create_page_logic(mock_client, inputs)
    
    assert exc_info.value.status_code == 404
    assert "Space 'NONEXISTENT' does not exist" in exc_info.value.detail


@pytest.mark.anyio
async def test_create_page_error_api_error():
    """Test error handling for general API errors."""
    
    # Mock 500 error response
    mock_api_response = httpx.Response(
        500,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json={
            "message": "Internal server error"
        }
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_api_response)
    
    # Test inputs
    inputs = CreatePageInput(
        space_key="TEST",
        title="Test Page",
        content="<p>Content</p>"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import create_page_logic
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await create_page_logic(mock_client, inputs)
    
    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


@pytest.mark.anyio
async def test_create_page_error_connection_error():
    """Test error handling for connection errors."""
    
    # Create a proper request object for the RequestError
    request = httpx.Request("POST", "http://mock.confluence.com/rest/api/content")
    
    # Mock connection error with proper request
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.RequestError("Connection failed", request=request)
    
    # Test inputs
    inputs = CreatePageInput(
        space_key="TEST",
        title="Test Page",
        content="<p>Content</p>"
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import create_page_logic
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await create_page_logic(mock_client, inputs)
    
    assert exc_info.value.status_code == 503
    assert "Error connecting to Confluence" in exc_info.value.detail


@pytest.mark.anyio
async def test_create_page_tool_via_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the create_page tool through the MCP interface."""
    
    # Mock successful page creation
    mock_response_data = {
        "id": "tool-test-12345",
        "title": "MCP Test Page",
        "space": {"key": "MCPTEST"},
        "version": {"number": 1},
        "status": "current",
        "_links": {
            "base": "https://example.atlassian.net",
            "webui": "/spaces/MCPTEST/pages/tool-test-12345/MCP+Test+Page"
        }
    }
    
    mock_api_response = httpx.Response(
        201,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json=mock_response_data
    )
    mock_httpx_async_client.post = AsyncMock(return_value=mock_api_response)

    request_params = CreatePageInput(
        space_key="MCPTEST",
        title="MCP Test Page",
        content="<p>This page was created via MCP.</p>"
    ).model_dump()
        
    # Call the tool through MCP
    result_content_list = await mcp_client.call_tool(
        "create_confluence_page",
        {"inputs": request_params}
    )
    
    # Verify the result
    assert result_content_list is not None
    assert len(result_content_list) == 1
    
    # Parse the JSON response
    actual_result_dict = json.loads(result_content_list[0].text)
    
    # Validate the structure of the result against CreatePageOutput
    result_data = CreatePageOutput(**actual_result_dict)
    assert result_data.page_id == "tool-test-12345"
    assert result_data.title == "MCP Test Page"
    assert result_data.space_key == "MCPTEST"
    assert result_data.version == 1

    mock_httpx_async_client.post.assert_awaited_once()


@pytest.mark.anyio
async def test_create_page_tool_invalid_input(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the create_page tool with invalid input via MCP."""
    
    # Call the tool with missing required fields
    request_params = {
        "space_key": "TEST",
        # Missing title and content (required fields)
    }
    
    # Call the tool and expect ToolError for validation
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool(
            "create_confluence_page",
            {"inputs": request_params}
        )
    
    # ToolError wraps the actual validation error, so we just verify that an error occurred
    error = exc_info.value
    assert error is not None  # Just verify an error was raised

    # Should not make any API calls due to validation failure
    mock_httpx_async_client.post.assert_not_awaited()


@pytest.mark.anyio
async def test_create_page_tool_api_error(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test create page tool when API returns error."""
    
    # Mock 400 error response for duplicate title
    mock_api_response = httpx.Response(
        400,
        request=httpx.Request("POST", "http://mock.confluence.com/rest/api/content"),
        json={
            "data": {
                "errors": [{
                    "message": {
                        "translation": "A page with this title already exists in this space."
                    }
                }]
            }
        }
    )
    mock_httpx_async_client.post = AsyncMock(return_value=mock_api_response)

    request_params = CreatePageInput(
        space_key="TEST",
        title="Duplicate Title",
        content="<p>Content</p>"
    ).model_dump()
    
    # Call the tool and expect ToolError
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool(
            "create_confluence_page",
            {"inputs": request_params}
        )
    
    # ToolError wraps the actual error, so we just verify that an error occurred
    error = exc_info.value
    assert error is not None  # Just verify an error was raised

    mock_httpx_async_client.post.assert_awaited_once() 