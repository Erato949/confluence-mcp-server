# tests/test_get_page_tool.py
import pytest
import json
from unittest.mock import AsyncMock
import httpx
import os

from fastmcp import Client
from fastmcp.exceptions import ToolError

# Schemas defined in our project for tool input/output
from confluence_mcp_server.mcp_actions.schemas import PageOutput, GetPageInput

# Fixtures mcp_client, mock_httpx_async_client are auto-imported from conftest.py

@pytest.mark.anyio
async def test_get_page_by_id_success(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test successful retrieval of a Confluence page by page ID.
    """
    page_id = "123456"
    
    # Mock API response data - typical Confluence page response
    mock_response_data = {
        "id": page_id,
        "title": "Test Page Title",
        "space": {
            "key": "DEV"
        },
        "version": {
            "number": 5,
            "when": "2023-12-01T10:30:00.000Z"
        },
        "history": {
            "createdBy": {
                "accountId": "user123"
            },
            "createdDate": "2023-11-01T09:00:00.000Z"
        },
        "_links": {
            "base": "https://test-confluence.example.com",
            "webui": "/display/DEV/Test+Page+Title"
        }
    }
    
    mock_api_response = httpx.Response(
        200, 
        request=httpx.Request("GET", f"http://mock.confluence.com/rest/api/content/{page_id}"),
        json=mock_response_data
    )
    mock_httpx_async_client.get = AsyncMock(return_value=mock_api_response)

    request_params = GetPageInput(page_id=page_id).model_dump()
    
    # Call the tool
    result_content_list = await mcp_client.call_tool(
        "get_confluence_page",
        {"inputs": request_params}
    )
    
    # Assertions
    assert result_content_list is not None
    assert len(result_content_list) == 1
    
    # Parse the JSON response
    actual_result_dict = json.loads(result_content_list[0].text)

    # Validate the structure of the result against PageOutput
    result_data = PageOutput(**actual_result_dict)
    assert result_data.page_id == page_id
    assert result_data.title == "Test Page Title"
    assert result_data.space_key == "DEV"
    assert result_data.version == 5
    assert result_data.author_id == "user123"
    assert result_data.created_date == "2023-11-01T09:00:00.000Z"
    assert result_data.last_modified_date == "2023-12-01T10:30:00.000Z"
    assert str(result_data.url) == "https://test-confluence.example.com/display/DEV/Test+Page+Title"

    mock_httpx_async_client.get.assert_awaited_once()


@pytest.mark.anyio
async def test_get_page_by_space_and_title_success(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test successful retrieval of a Confluence page by space key and title.
    """
    space_key = "DEV"
    title = "My Test Page"
    page_id = "789012"
    
    # Mock API response data for search by space and title
    mock_response_data = {
        "results": [{
            "id": page_id,
            "title": title,
            "space": {
                "key": space_key
            },
            "version": {
                "number": 3,
                "when": "2023-12-02T14:15:00.000Z"
            },
            "history": {
                "createdBy": {
                    "accountId": "user456"
                },
                "createdDate": "2023-11-15T12:00:00.000Z"
            },
            "_links": {
                "base": "https://test-confluence.example.com",
                "webui": "/display/DEV/My+Test+Page"
            }
        }]
    }
    
    mock_api_response = httpx.Response(
        200, 
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content"),
        json=mock_response_data
    )
    mock_httpx_async_client.get = AsyncMock(return_value=mock_api_response)

    request_params = GetPageInput(space_key=space_key, title=title).model_dump()
    
    # Call the tool
    result_content_list = await mcp_client.call_tool(
        "get_confluence_page",
        {"inputs": request_params}
    )
    
    # Assertions
    assert result_content_list is not None
    assert len(result_content_list) == 1
    
    # Parse the JSON response
    actual_result_dict = json.loads(result_content_list[0].text)

    # Validate the structure of the result against PageOutput
    result_data = PageOutput(**actual_result_dict)
    assert result_data.page_id == page_id
    assert result_data.title == title
    assert result_data.space_key == space_key
    assert result_data.version == 3
    assert result_data.author_id == "user456"
    assert str(result_data.url) == "https://test-confluence.example.com/display/DEV/My+Test+Page"

    mock_httpx_async_client.get.assert_awaited_once()


@pytest.mark.anyio
async def test_get_page_not_found(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test get page when page is not found (404 error).
    """
    page_id = "nonexistent"
    
    # Mock 404 response
    mock_api_response = httpx.Response(
        404, 
        request=httpx.Request("GET", f"http://mock.confluence.com/rest/api/content/{page_id}")
    )
    mock_httpx_async_client.get = AsyncMock(return_value=mock_api_response)

    request_params = GetPageInput(page_id=page_id).model_dump()
    
    # Call the tool and expect ToolError
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool(
            "get_confluence_page",
            {"inputs": request_params}
        )
    
    # ToolError wraps the actual error, so we just verify that an error occurred
    # The specific error details are logged but may not be in the ToolError message
    error = exc_info.value
    assert error is not None  # Just verify an error was raised

    mock_httpx_async_client.get.assert_awaited_once()


@pytest.mark.anyio
async def test_get_page_api_error(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test get page when API returns 500 error.
    """
    page_id = "123456"
    
    # Mock 500 response
    mock_api_response = httpx.Response(
        500, 
        request=httpx.Request("GET", f"http://mock.confluence.com/rest/api/content/{page_id}")
    )
    mock_httpx_async_client.get = AsyncMock(return_value=mock_api_response)

    request_params = GetPageInput(page_id=page_id).model_dump()
    
    # Call the tool and expect ToolError
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool(
            "get_confluence_page",
            {"inputs": request_params}
        )
    
    # ToolError wraps the actual error, so we just verify that an error occurred
    error = exc_info.value
    assert error is not None  # Just verify an error was raised

    mock_httpx_async_client.get.assert_awaited_once()


@pytest.mark.anyio
async def test_get_page_invalid_input_missing_identifiers(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test get page with invalid input - no page_id or space_key/title provided.
    """
    # Invalid request params - no identifiers provided
    request_params = {}
    
    # Call the tool and expect ToolError for validation
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool(
            "get_confluence_page",
            {"inputs": request_params}
        )
    
    # ToolError wraps the actual validation error, so we just verify that an error occurred
    error = exc_info.value
    assert error is not None  # Just verify an error was raised

    # Should not make any API calls due to validation failure
    mock_httpx_async_client.get.assert_not_awaited()


@pytest.mark.anyio
async def test_get_page_invalid_input_conflicting_identifiers(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test get page with invalid input - both page_id and space_key/title provided.
    """
    # Invalid request params - conflicting identifiers
    request_params = {
        "page_id": "123456",
        "space_key": "DEV", 
        "title": "Test Page"
    }
    
    # Call the tool and expect ToolError for validation
    with pytest.raises(ToolError) as exc_info:
        await mcp_client.call_tool(
            "get_confluence_page",
            {"inputs": request_params}
        )
    
    # ToolError wraps the actual validation error, so we just verify that an error occurred
    error = exc_info.value
    assert error is not None  # Just verify an error was raised

    # Should not make any API calls due to validation failure
    mock_httpx_async_client.get.assert_not_awaited()


@pytest.mark.anyio
async def test_get_page_with_content_expansion(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test successful retrieval of a Confluence page with content expansion.
    """
    page_id = "123456"
    expand_param = "body.view"
    page_content = "<p>This is the page content in HTML format.</p>"
    
    # Mock API response data with expanded content
    mock_response_data = {
        "id": page_id,
        "title": "Test Page with Content",
        "space": {
            "key": "DEV"
        },
        "version": {
            "number": 2,
            "when": "2023-12-01T10:30:00.000Z"
        },
        "history": {
            "createdBy": {
                "accountId": "user123"
            },
            "createdDate": "2023-11-01T09:00:00.000Z"
        },
        "body": {
            "view": {
                "value": page_content
            }
        },
        "_links": {
            "base": "https://test-confluence.example.com",
            "webui": "/display/DEV/Test+Page+with+Content"
        }
    }
    
    mock_api_response = httpx.Response(
        200, 
        request=httpx.Request("GET", f"http://mock.confluence.com/rest/api/content/{page_id}"),
        json=mock_response_data
    )
    mock_httpx_async_client.get = AsyncMock(return_value=mock_api_response)

    request_params = GetPageInput(page_id=page_id, expand=expand_param).model_dump()
    
    # Call the tool
    result_content_list = await mcp_client.call_tool(
        "get_confluence_page",
        {"inputs": request_params}
    )
    
    # Assertions
    assert result_content_list is not None
    assert len(result_content_list) == 1
    
    # Parse the JSON response
    actual_result_dict = json.loads(result_content_list[0].text)

    # Validate the structure of the result against PageOutput
    result_data = PageOutput(**actual_result_dict)
    assert result_data.page_id == page_id
    assert result_data.title == "Test Page with Content"
    assert result_data.content == page_content
    assert result_data.space_key == "DEV"

    mock_httpx_async_client.get.assert_awaited_once() 