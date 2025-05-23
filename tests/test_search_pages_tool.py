"""Tests for the search_confluence_pages tool."""

import pytest
import json
from unittest.mock import AsyncMock
import httpx

from fastmcp import Client
from fastmcp.exceptions import ToolError
from confluence_mcp_server.mcp_actions.schemas import SearchPagesInput, SearchPagesOutput


@pytest.mark.anyio
async def test_search_pages_success_simple_query():
    """Test successful page search with simple text query."""
    
    # Mock search results response
    search_response_data = {
        "results": [
            {
                "id": "123456",
                "title": "API Documentation",
                "space": {"key": "DEV"},
                "version": {"when": "2024-01-15T10:00:00.000Z"},
                "excerpt": "This is the <strong>API</strong> documentation...",
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/DEV/pages/123456/API+Documentation"
                }
            },
            {
                "id": "789012",
                "title": "REST API Guide",
                "space": {"key": "DEV"},
                "version": {"when": "2024-01-14T15:30:00.000Z"},
                "excerpt": "Guide for <strong>REST API</strong> usage...",
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/DEV/pages/789012/REST+API+Guide"
                }
            }
        ],
        "start": 0,
        "size": 2,
        "totalSize": 5
    }
    
    # Create proper httpx.Response object
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = search_response
    
    # Test inputs
    inputs = SearchPagesInput(
        query="API",
        limit=25,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    result = await search_pages_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, SearchPagesOutput)
    assert len(result.results) == 2
    assert result.total_available == 5
    assert result.next_start_offset == 2  # start(0) + size(2) = 2
    
    # Verify first result
    first_result = result.results[0]
    assert first_result.page_id == "123456"
    assert first_result.title == "API Documentation"
    assert first_result.space_key == "DEV"
    assert first_result.last_modified_date == "2024-01-15T10:00:00.000Z"
    assert str(first_result.url) == "https://example.atlassian.net/spaces/DEV/pages/123456/API+Documentation"
    assert first_result.excerpt_highlight == "This is the <strong>API</strong> documentation..."
    
    # Verify API call
    expected_params = {
        "cql": 'text ~ "API" OR title ~ "API"',
        "limit": 25,
        "start": 0
    }
    mock_client.get.assert_called_once_with("/rest/api/content/search", params=expected_params)


@pytest.mark.anyio
async def test_search_pages_success_with_space_filter():
    """Test successful page search with space filter."""
    
    # Mock search results response
    search_response_data = {
        "results": [
            {
                "id": "123456",
                "title": "Project Documentation",
                "space": {"key": "PROJ"},
                "version": {"when": "2024-01-15T10:00:00.000Z"},
                "excerpt": "Documentation for the project...",
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/PROJ/pages/123456/Project+Documentation"
                }
            }
        ],
        "start": 0,
        "size": 1,
        "totalSize": 1
    }
    
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = search_response
    
    # Test inputs with space filter
    inputs = SearchPagesInput(
        query="documentation",
        space_key="PROJ",
        limit=10,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    result = await search_pages_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, SearchPagesOutput)
    assert len(result.results) == 1
    assert result.total_available == 1
    assert result.next_start_offset is None  # No more results
    
    # Verify API call includes space filter
    expected_params = {
        "cql": 'text ~ "documentation" OR title ~ "documentation" AND space = "PROJ"',
        "limit": 10,
        "start": 0
    }
    mock_client.get.assert_called_once_with("/rest/api/content/search", params=expected_params)


@pytest.mark.anyio
async def test_search_pages_success_cql_query():
    """Test successful page search with direct CQL query."""
    
    # Mock search results response
    search_response_data = {
        "results": [
            {
                "id": "456789",
                "title": "Recent Updates",
                "space": {"key": "NEWS"},
                "version": {"when": "2024-01-15T09:00:00.000Z"},
                "excerpt": "Latest updates and changes...",
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/NEWS/pages/456789/Recent+Updates"
                }
            }
        ],
        "start": 0,
        "size": 1,
        "totalSize": 3
    }
    
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = search_response
    
    # Test inputs with CQL
    inputs = SearchPagesInput(
        cql='lastModified >= "2024-01-01" AND space = "NEWS"',
        limit=5,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    result = await search_pages_logic(mock_client, inputs)
    
    # Verify the result
    assert isinstance(result, SearchPagesOutput)
    assert len(result.results) == 1
    assert result.total_available == 3
    assert result.next_start_offset == 1  # start(0) + size(1) = 1
    
    # Verify API call uses direct CQL
    expected_params = {
        "cql": '(lastModified >= "2024-01-01" AND space = "NEWS")',
        "limit": 5,
        "start": 0
    }
    mock_client.get.assert_called_once_with("/rest/api/content/search", params=expected_params)


@pytest.mark.anyio
async def test_search_pages_success_with_expand():
    """Test successful page search with expand parameter for content preview."""
    
    # Mock search results response with body.view expanded
    search_response_data = {
        "results": [
            {
                "id": "111222",
                "title": "Meeting Notes",
                "space": {"key": "TEAM"},
                "version": {"when": "2024-01-15T11:00:00.000Z"},
                "excerpt": "Meeting notes from the team...",
                "body": {
                    "view": {
                        "value": "<p>Full content of the meeting notes...</p>"
                    }
                },
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/TEAM/pages/111222/Meeting+Notes"
                }
            }
        ],
        "start": 0,
        "size": 1,
        "totalSize": 1
    }
    
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = search_response
    
    # Test inputs with expand
    inputs = SearchPagesInput(
        query="meeting",
        expand="body.view",
        limit=10,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    result = await search_pages_logic(mock_client, inputs)
    
    # Verify the result includes content preview
    assert isinstance(result, SearchPagesOutput)
    assert len(result.results) == 1
    
    first_result = result.results[0]
    assert first_result.content_preview == "<p>Full content of the meeting notes...</p>"
    
    # Verify API call includes expand parameter
    expected_params = {
        "cql": 'text ~ "meeting" OR title ~ "meeting"',
        "limit": 10,
        "start": 0,
        "expand": "body.view"
    }
    mock_client.get.assert_called_once_with("/rest/api/content/search", params=expected_params)


@pytest.mark.anyio
async def test_search_pages_no_results():
    """Test search that returns no results."""
    
    # Mock empty search results response
    search_response_data = {
        "results": [],
        "start": 0,
        "size": 0,
        "totalSize": 0
    }
    
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = search_response
    
    # Test inputs
    inputs = SearchPagesInput(
        query="nonexistent",
        limit=25,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    result = await search_pages_logic(mock_client, inputs)
    
    # Verify empty results
    assert isinstance(result, SearchPagesOutput)
    assert len(result.results) == 0
    assert result.total_available == 0
    assert result.next_start_offset is None


@pytest.mark.anyio
async def test_search_pages_error_invalid_cql():
    """Test error handling for invalid CQL syntax."""
    
    # Mock 400 error response for invalid CQL
    error_response = httpx.Response(
        400,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json={"message": "Unable to parse CQL query"}
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = error_response
    
    # Test inputs with invalid CQL
    inputs = SearchPagesInput(
        cql='invalid CQL syntax here',
        limit=25,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    
    with pytest.raises(Exception) as exc_info:
        await search_pages_logic(mock_client, inputs)
    
    error_message = str(exc_info.value)
    assert "Invalid CQL syntax" in error_message or "Unable to parse CQL query" in error_message


@pytest.mark.anyio
async def test_search_pages_error_api_error():
    """Test error handling for API errors during search."""
    
    # Mock 500 error response
    error_response = httpx.Response(
        500,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json={"message": "Internal Server Error"}
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = error_response
    
    # Test inputs
    inputs = SearchPagesInput(
        query="test",
        limit=25,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    
    with pytest.raises(Exception) as exc_info:
        await search_pages_logic(mock_client, inputs)
    
    assert "Confluence API Error" in str(exc_info.value)


@pytest.mark.anyio
async def test_search_pages_error_connection_error():
    """Test error handling for connection errors."""
    
    # Create a proper request object for the RequestError
    request = httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search")
    
    # Mock connection error with proper request
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.RequestError("Connection failed", request=request)
    
    # Test inputs
    inputs = SearchPagesInput(
        query="test",
        limit=25,
        start=0
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    
    with pytest.raises(Exception) as exc_info:
        await search_pages_logic(mock_client, inputs)
    
    assert "Error connecting to Confluence" in str(exc_info.value)


@pytest.mark.anyio
async def test_search_pages_pagination():
    """Test search pagination handling."""
    
    # Mock search results response with pagination
    search_response_data = {
        "results": [
            {
                "id": "page1",
                "title": "Page 1",
                "space": {"key": "TEST"},
                "version": {"when": "2024-01-15T10:00:00.000Z"},
                "excerpt": "First page...",
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/TEST/pages/page1/Page+1"
                }
            }
        ],
        "start": 10,  # Starting at offset 10
        "size": 1,    # One result returned
        "totalSize": 25  # Total of 25 results available
    }
    
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    # Mock the httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = search_response
    
    # Test inputs with pagination
    inputs = SearchPagesInput(
        query="test",
        limit=1,
        start=10
    )
    
    # Import and test the logic function
    from confluence_mcp_server.mcp_actions.page_actions import search_pages_logic
    result = await search_pages_logic(mock_client, inputs)
    
    # Verify pagination info
    assert isinstance(result, SearchPagesOutput)
    assert len(result.results) == 1
    assert result.total_available == 25
    assert result.next_start_offset == 11  # start(10) + size(1) = 11


# MCP Tool Tests
@pytest.mark.anyio
async def test_search_pages_tool_via_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the search_pages tool through the MCP interface."""
    
    # Mock search results response
    search_response_data = {
        "results": [
            {
                "id": "mcp-test-123",
                "title": "MCP Test Page",
                "space": {"key": "MCPTEST"},
                "version": {"when": "2024-01-15T12:00:00.000Z"},
                "excerpt": "This is a test page for MCP...",
                "_links": {
                    "base": "https://example.atlassian.net",
                    "webui": "/spaces/MCPTEST/pages/mcp-test-123/MCP+Test+Page"
                }
            }
        ],
        "start": 0,
        "size": 1,
        "totalSize": 1
    }
    
    search_response = httpx.Response(
        200,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json=search_response_data
    )
    
    mock_httpx_async_client.get.return_value = search_response
    
    # Test MCP tool call
    result = await mcp_client.call_tool(
        "search_confluence_pages",
        {"inputs": {
            "query": "MCP",
            "limit": 10,
            "start": 0
        }}
    )
    
    # Verify result structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == "text"
    
    # Parse the JSON response
    response_data = json.loads(result[0].text)
    assert "results" in response_data
    assert "total_available" in response_data
    assert len(response_data["results"]) == 1
    assert response_data["results"][0]["page_id"] == "mcp-test-123"
    assert response_data["results"][0]["title"] == "MCP Test Page"
    assert response_data["total_available"] == 1


@pytest.mark.anyio
async def test_search_pages_tool_invalid_input_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the search_pages tool with invalid input through MCP interface."""
    
    # Test MCP tool call with missing both query and cql
    with pytest.raises(ToolError):
        await mcp_client.call_tool(
            "search_confluence_pages",
            {"inputs": {
                "limit": 10,
                "start": 0
                # Missing both query and cql
            }}
        )


@pytest.mark.anyio
async def test_search_pages_tool_api_error_mcp(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """Test the search_pages tool API error handling through MCP interface."""
    
    # Mock 400 error response
    error_response = httpx.Response(
        400,
        request=httpx.Request("GET", "http://mock.confluence.com/rest/api/content/search"),
        json={"message": "Invalid query"}
    )
    
    mock_httpx_async_client.get.return_value = error_response
    
    # Test MCP tool call
    with pytest.raises(ToolError):
        await mcp_client.call_tool(
            "search_confluence_pages",
            {"inputs": {
                "query": "test",
                "limit": 10,
                "start": 0
            }}
        ) 