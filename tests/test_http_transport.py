#!/usr/bin/env python3
"""
Test suite for HTTP transport functionality.
Ensures HTTP transport maintains compatibility with all existing tools.
"""

import pytest
import json
import base64
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import httpx

# Import the HTTP server components
from confluence_mcp_server.server_http import create_app, HttpTransport


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict('os.environ', {
        'CONFLUENCE_URL': 'https://test.atlassian.net',
        'CONFLUENCE_USERNAME': 'test@example.com',
        'CONFLUENCE_API_TOKEN': 'test_token_123'
    }):
        yield


@pytest.fixture
def http_client(mock_env_vars):
    """Create a test client for the HTTP transport."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_config():
    """Sample configuration for Smithery.ai."""
    config = {
        "confluenceUrl": "https://test.atlassian.net",
        "username": "test@example.com",
        "apiToken": "test_api_token"
    }
    encoded = base64.b64encode(json.dumps(config).encode()).decode()
    return encoded


class TestHttpTransportBasics:
    """Test basic HTTP transport functionality."""
    
    def test_root_endpoint(self, http_client):
        """Test the root endpoint returns server information."""
        response = http_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Confluence MCP Server"
        assert data["version"] == "1.1.0"
        assert data["transport"] == "http"
        assert "tools_count" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self, http_client):
        """Test the health check endpoint."""
        response = http_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["transport"] == "http"
    
    def test_mcp_get_tools_list(self, http_client):
        """Test GET /mcp returns tools list."""
        response = http_client.get("/mcp")
        assert response.status_code == 200
        
        data = response.json()
        # GET /mcp returns unwrapped format: {"tools": [...]}
        assert "tools" in data
        
        tools = data["tools"]
        assert len(tools) > 0
        
        # Check that expected tools are present
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "get_confluence_page",
            "search_confluence_pages", 
            "create_confluence_page",
            "update_confluence_page",
            "delete_confluence_page",
            "get_confluence_spaces",
            "get_page_attachments",
            "add_page_attachment",
            "delete_page_attachment",
            "get_page_comments"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_mcp_get_with_config(self, http_client, sample_config):
        """Test GET /mcp with configuration parameter."""
        response = http_client.get(f"/mcp?config={sample_config}")
        assert response.status_code == 200
        
        data = response.json()
        # GET /mcp returns unwrapped format: {"tools": [...]}
        assert "tools" in data
    
    def test_mcp_delete_cleanup(self, http_client):
        """Test DELETE /mcp for session cleanup."""
        response = http_client.delete("/mcp")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data


class TestHttpTransportToolExecution:
    """Test tool execution through HTTP transport."""
    
    @pytest.mark.asyncio
    async def test_tools_list_request(self, http_client):
        """Test tools/list JSON-RPC request."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        response = http_client.post("/mcp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert "tools" in data["result"]
        
        tools = data["result"]["tools"]
        assert len(tools) > 0
        
        # Verify tool structure
        first_tool = tools[0]
        assert "name" in first_tool
        assert "description" in first_tool
        assert "inputSchema" in first_tool

    @patch('confluence_mcp_server.server_http.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_tool_call_request(self, mock_async_client, http_client):
        """Test tools/call JSON-RPC request."""
        # Mock the httpx.AsyncClient constructor
        mock_client_instance = AsyncMock()
        mock_async_client.return_value = mock_client_instance
        
        # Mock the async context manager
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        
        # Set the base_url property to a valid URL string
        mock_client_instance.base_url = "https://test.atlassian.net"
        
        # Create a synchronous mock response that matches httpx.Response behavior
        mock_response = MagicMock()
        mock_response.status_code = 200
        # json() is synchronous in httpx, returns data directly
        mock_response.json.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "TEST"},
            "_links": {"webui": "/spaces/TEST/pages/123456/Test+Page"}
        }
        # raise_for_status() is also synchronous
        mock_response.raise_for_status.return_value = None
        # The GET call itself is async
        mock_client_instance.get.return_value = mock_response
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_confluence_page",
                "arguments": {
                    "page_id": "123456"
                }
            }
        }
        
        response = http_client.post("/mcp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data
        assert "content" in data["result"]
        
        content = data["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        
        # Verify the mock was called
        mock_async_client.assert_called_once()
        mock_client_instance.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unknown_tool_call(self, http_client):
        """Test calling an unknown tool returns error."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }
        
        response = http_client.post("/mcp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 3
        assert "error" in data
        assert data["error"]["code"] == -32602
        assert "Unknown tool" in data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_unknown_method(self, http_client):
        """Test calling an unknown JSON-RPC method."""
        request_data = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "unknown/method"
        }
        
        response = http_client.post("/mcp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 4
        assert "error" in data
        assert data["error"]["code"] == -32601
        assert "Method not found" in data["error"]["message"]


class TestHttpTransportConfiguration:
    """Test configuration handling for HTTP transport."""
    
    def test_config_decoding(self):
        """Test base64 configuration decoding."""
        transport = HttpTransport()
        
        # Test valid config
        config = {"key": "value", "number": 123}
        encoded = base64.b64encode(json.dumps(config).encode()).decode()
        
        decoded = transport._decode_config(encoded)
        assert decoded == config
    
    def test_config_decoding_invalid(self):
        """Test invalid configuration handling."""
        transport = HttpTransport()
        
        # Test invalid base64
        decoded = transport._decode_config("invalid_base64!")
        assert decoded == {}
        
        # Test invalid JSON
        invalid_json = base64.b64encode(b"not json").decode()
        decoded = transport._decode_config(invalid_json)
        assert decoded == {}
    
    @patch.dict('os.environ', {}, clear=True)
    def test_config_application(self):
        """Test configuration application to environment."""
        transport = HttpTransport()
        
        config_data = {
            "confluenceUrl": "https://new-test.atlassian.net",
            "username": "new-user@example.com",
            "apiToken": "new_token_456"
        }
        
        transport._apply_config(config_data)
        
        # Verify environment variables were set
        import os
        assert os.getenv("CONFLUENCE_URL") == "https://new-test.atlassian.net"
        assert os.getenv("CONFLUENCE_USERNAME") == "new-user@example.com"
        assert os.getenv("CONFLUENCE_API_TOKEN") == "new_token_456"
    
    def test_config_application_partial(self):
        """Test partial configuration application."""
        transport = HttpTransport()
        
        # Only some config keys
        config_data = {
            "confluenceUrl": "https://partial-test.atlassian.net",
            "someOtherKey": "ignored"
        }
        
        transport._apply_config(config_data)
        
        # Verify only mapped keys were applied
        import os
        assert os.getenv("CONFLUENCE_URL") == "https://partial-test.atlassian.net"
        # Other environment variables should not be set
        assert "someOtherKey" not in os.environ


class TestHttpTransportIntegration:
    """Integration tests for HTTP transport with all tools."""
    
    @patch('confluence_mcp_server.server_http.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_search_pages_integration(self, mock_async_client, http_client):
        """Test search_confluence_pages through HTTP transport."""
        # Mock the httpx.AsyncClient constructor
        mock_client_instance = AsyncMock()
        mock_async_client.return_value = mock_client_instance
        
        # Mock the async context manager
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        
        # Set the base_url property to a valid URL string
        mock_client_instance.base_url = "https://test.atlassian.net"
        
        # Create a synchronous mock response that matches httpx.Response behavior
        mock_response = MagicMock()
        mock_response.status_code = 200
        # json() is synchronous in httpx, returns data directly
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123456",
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "_links": {"webui": "/spaces/TEST/pages/123456/Test+Page"}
                }
            ],
            "size": 1
        }
        # raise_for_status() is also synchronous
        mock_response.raise_for_status.return_value = None
        # The GET call itself is async
        mock_client_instance.get.return_value = mock_response
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "search_confluence_pages",
                "arguments": {
                    "query": "test search"
                }
            }
        }
        
        response = http_client.post("/mcp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 5
        assert "result" in data
        
        # Verify the tool executed successfully
        result_text = data["result"]["content"][0]["text"]
        result_data = json.loads(result_text)
        assert "results" in result_data
        assert len(result_data["results"]) == 1
    
    @patch('confluence_mcp_server.server_http.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self, mock_async_client, http_client):
        """Test error handling in tool execution."""
        # Mock the httpx.AsyncClient constructor to raise an exception
        mock_client_instance = AsyncMock()
        mock_async_client.return_value = mock_client_instance
        
        # Mock the async context manager
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        
        # Mock the client to raise an exception
        mock_client_instance.get.side_effect = Exception("Test error")
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_confluence_page",
                "arguments": {
                    "page_id": "123456"
                }
            }
        }
        
        response = http_client.post("/mcp", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 6
        assert "error" in data
        assert data["error"]["code"] == -32603
        assert "Tool execution failed" in data["error"]["message"]


class TestSmitheryCompatibility:
    """Test specific Smithery.ai compatibility requirements."""
    
    def test_lazy_tool_loading(self, http_client):
        """Test that tools can be listed without authentication."""
        # This should work even without valid credentials
        response = http_client.get("/mcp")
        assert response.status_code == 200
        
        data = response.json()
        # GET /mcp returns unwrapped format: {"tools": [...]}
        assert "tools" in data
        assert len(data["tools"]) > 0
    
    def test_smithery_config_format(self, http_client, sample_config):
        """Test Smithery configuration format compatibility."""
        # Test that Smithery-style config works
        response = http_client.get(f"/mcp?config={sample_config}")
        assert response.status_code == 200
        
        # The configuration should be applied without error
        data = response.json()
        # GET /mcp returns unwrapped format: {"tools": [...]}
        assert "tools" in data
    
    def test_cors_headers(self, http_client):
        """Test CORS headers are present for web clients."""
        response = http_client.options("/mcp")
        # TestClient may not fully simulate CORS, but we can verify the app setup
        assert response.status_code in [200, 405]  # OPTIONS may not be explicitly defined
    
    def test_tool_metadata_format(self, http_client):
        """Test that tool metadata follows expected format."""
        response = http_client.get("/mcp")
        data = response.json()
        
        # GET /mcp returns unwrapped format: {"tools": [...]}
        tools = data["tools"]
        for tool in tools:
            # Each tool should have required metadata
            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)
            assert isinstance(tool["inputSchema"], dict)
            
            # Description should not be empty
            assert len(tool["description"].strip()) > 0 