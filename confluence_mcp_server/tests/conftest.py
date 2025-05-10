# conftest.py for shared pytest fixtures

import pytest
from httpx import AsyncClient, ASGITransport
import asyncio

# Import the FastAPI app instance. Ensure PYTHONPATH or editable install is set up.
# For now, assuming pytest is run from the root of Confluence-MCP-Server_Claude
# or that confluence_mcp_server is otherwise discoverable.
from confluence_mcp_server.main import app as fastapi_app

# Custom event_loop fixture removed.
# Pytest-asyncio will provide the event loop based on the asyncio marker's scope in test files.

@pytest.fixture(scope="function")
def client(request) -> AsyncClient:
    """
    An asynchronous test client for the FastAPI application, function-scoped.
    Returns an AsyncClient instance directly. Attempts teardown (aclose) in finalizer.
    Uses ASGITransport for httpx.
    """
    transport = ASGITransport(app=fastapi_app)
    ac = AsyncClient(transport=transport, base_url="http://test")

    def finalizer():
        print("DEBUG: Client fixture finalizer called. Attempting ac.aclose().")
        try:
            # Try to run ac.aclose(). This creates a new event loop or uses the existing one
            # if not running. If called from within a running loop, it will raise RuntimeError.
            asyncio.run(ac.aclose()) # This is the simplest way to call an async func from sync
            print("DEBUG: AsyncClient.aclose() completed via asyncio.run().")
        except RuntimeError as e:
            # This typically means asyncio.run() was called from an already running event loop.
            print(f"DEBUG: Could not close AsyncClient via asyncio.run() in finalizer: {e}. Client might remain open.")
        except Exception as e:
            print(f"DEBUG: General error during AsyncClient.aclose() attempt in finalizer: {e}")

    request.addfinalizer(finalizer)
    return ac
