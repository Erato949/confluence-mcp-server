import pytest
import asyncio
import httpx # For spec in AsyncMock
from typing import AsyncGenerator, Generator # Keep AsyncGenerator for mcp_client
from unittest.mock import AsyncMock

from fastmcp import FastMCP, Client
from pytest_mock import MockerFixture

from confluence_mcp_server.main import mcp_server as global_mcp_server


@pytest.fixture(scope="function")
def mcp_server_instance() -> FastMCP:
    """
    Fixture to provide the global FastMCP server instance from main.py.
    """
    return global_mcp_server

@pytest.fixture(scope="function")
def mock_httpx_async_client() -> AsyncMock: # Synchronous fixture
    """
    Provides a mock httpx.AsyncClient instance.
    Individual tests can configure its behavior (return_value, side_effect) as needed.
    """
    return AsyncMock(spec=httpx.AsyncClient)

@pytest.fixture(scope="function", autouse=True)
def patch_get_confluence_client(
    mocker: MockerFixture, 
    mock_httpx_async_client: AsyncMock # Receives the direct AsyncMock instance
) -> AsyncMock: # Return the mock for potential inspection, though autouse makes it implicit
    """
    Patches 'get_confluence_client' in main.py to return a mock async context manager
    whose __aenter__ returns the mock_httpx_async_client.
    This prevents real API calls during tests.
    """
    # Create a mock that can be used as an async context manager
    mock_context_manager = AsyncMock()
    # When this context manager is entered (async with ... as client), 
    # it should yield our mock_httpx_async_client as 'client'
    mock_context_manager.__aenter__.return_value = mock_httpx_async_client
    # __aexit__ should also be an AsyncMock or a suitable coroutine function
    mock_context_manager.__aexit__ = AsyncMock(return_value=None) # Or a simple async def func

    mocker.patch(
        "confluence_mcp_server.main.get_confluence_client",
        return_value=mock_context_manager 
    )
    return mock_httpx_async_client # Still return the underlying client mock for tests to configure 

@pytest.fixture(scope="function")
async def mcp_client(mcp_server_instance: FastMCP) -> AsyncGenerator[Client, None]:
    """
    Fixture to create a FastMCP Client that communicates with the server via in-memory transport.
    """
    async with Client(mcp_server_instance) as client:
        yield client