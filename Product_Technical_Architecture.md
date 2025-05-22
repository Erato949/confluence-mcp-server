# Technical Architecture Document - Confluence MCP Server

## 📋 DOCUMENT PURPOSE

This document defines the **authoritative technical architecture** for the Confluence MCP Server. Any deviation from this architecture without explicit approval is **strictly forbidden**.

## 🏗️ ARCHITECTURE OVERVIEW

### Core Principle: **SIMPLICITY FIRST**
- **Direct FastMCP Integration**: No HTTP proxies, no threading, no complex middleware
- **In-Memory Testing**: Use FastMCP's native testing capabilities  
- **Single Responsibility**: Each component has one clear purpose
- **Async-First**: Built for async/await patterns throughout

### Architecture Pattern: **Direct Tool Server**
```
LLM Client → FastMCP Server → Tool Functions → httpx.AsyncClient → Confluence API
```

**NOT** (Complex Proxy Pattern - FORBIDDEN):
```
LLM Client → HTTP Proxy → Thread → FastMCP → HTTP Server → Tool Functions → Confluence API
```

## 🔧 TECHNOLOGY STACK

### Core Framework
- **FastMCP**: `>=0.3.0` - MCP server framework (jlowin/fastmcp)
- **Python**: `>=3.10` - Required for FastMCP
- **httpx**: `>=0.25.0` - Async HTTP client for Confluence API
- **Pydantic**: `>=2.0.0` - Data validation and serialization

### Testing Framework  
- **pytest**: `>=7.0.0` - Test framework
- **pytest-asyncio**: `>=0.21.0` - Async test support
- **pytest-mock**: `>=3.10.0` - Mocking utilities

### Development Tools
- **python-dotenv**: `>=1.0.0` - Environment variable management
- **logging**: Built-in Python logging

## 🏢 COMPONENT ARCHITECTURE

### 1. FastMCP Server (`main.py`)
**Purpose**: Central FastMCP server setup and tool registration  
**Pattern**: Direct tool registration with decorators  
**Responsibilities**:
- Create FastMCP server instance
- Register all tools using `@mcp_server.tool()` decorators
- Setup httpx.AsyncClient for Confluence API
- Handle tool execution and error management

```python
# CORRECT Pattern
@mcp_server.tool(name="delete_confluence_page")
async def delete_page_tool(page_id: str) -> dict:
    # Tool implementation
    pass

# FORBIDDEN Pattern  
def _tool_adapter_factory(...):
    # Complex factory pattern - DELETE THIS
    pass
```

### 2. Tool Logic Layer (`mcp_actions/`)
**Purpose**: Business logic for Confluence operations  
**Pattern**: Pure async functions that accept httpx.AsyncClient  
**Responsibilities**:
- Execute Confluence API calls
- Handle HTTP errors and responses
- Transform data between Confluence and MCP formats
- Input validation using Pydantic schemas

```python
# CORRECT Pattern
async def delete_page_logic(client: httpx.AsyncClient, inputs: DeletePageInput) -> DeletePageOutput:
    response = await client.delete(f"/rest/api/content/{inputs.page_id}")
    # Handle response
    return DeletePageOutput(...)
```

### 3. Schema Layer (`mcp_actions/schemas.py`)
**Purpose**: Data validation and type safety  
**Pattern**: Pydantic models for all inputs and outputs  
**Responsibilities**:
- Define tool input/output schemas
- Validate user inputs
- Ensure type safety across the application

### 4. HTTP Client Layer
**Purpose**: Confluence API communication  
**Pattern**: Single httpx.AsyncClient instance  
**Responsibilities**:
- Make HTTP requests to Confluence
- Handle authentication
- Manage connection pooling and timeouts

## 🧪 TESTING ARCHITECTURE

### Testing Philosophy: **Direct Integration Testing**
- Test tools through FastMCP's native client interface
- Mock httpx.AsyncClient, not Confluence API endpoints
- Use in-memory transport (FastMCPTransport)
- Single async event loop for all tests

### Test Component Structure

#### 1. Test Fixtures (`conftest.py`)
**Maximum Complexity**: 50 lines total  
**Pattern**: Simple, focused fixtures  

```python
@pytest_asyncio.fixture
async def confluence_client_mock() -> AsyncMock:
    """Mock httpx.AsyncClient for Confluence API."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.base_url = "https://test-confluence.example.com"
    return mock_client

@pytest_asyncio.fixture  
async def mcp_server_instance(confluence_client_mock: AsyncMock) -> FastMCP:
    """Create FastMCP server with tools registered."""
    mcp_server = FastMCP(name="TestServer")
    register_confluence_tools(mcp_server)
    mcp_server.state.CONFLUENCE_CLIENT = confluence_client_mock
    return mcp_server

@pytest_asyncio.fixture
async def mcp_client(mcp_server_instance: FastMCP):
    """Create FastMCP client with in-memory transport."""
    from fastmcp import Client
    from fastmcp.transports import FastMCPTransport
    
    transport = FastMCPTransport(mcp_server_instance)
    async with Client(transport=transport) as client:
        yield client
```

#### 2. Test Structure Pattern
**Pattern**: Arrange-Act-Assert with clear test names  

```python
@pytest.mark.asyncio
async def test_delete_page_success(mcp_client: Client, confluence_client_mock: AsyncMock):
    """Test successful page deletion returns correct response."""
    # Arrange
    page_id = "12345"
    mock_response = HTTPXResponse(204, request=HTTPXRequest("DELETE", f"/.../content/{page_id}"))
    confluence_client_mock.delete.return_value = mock_response
    
    # Act  
    result = await mcp_client.call_tool("delete_confluence_page", {"page_id": page_id})
    
    # Assert
    assert result.page_id == page_id
    assert result.status == "success"
    confluence_client_mock.delete.assert_called_once()
```

## 🔌 API INTEGRATION ARCHITECTURE

### Confluence REST API Integration
**Base URL Pattern**: `{confluence_base_url}/rest/api/...`  
**Authentication**: HTTP Basic Auth (username + API token)  
**HTTP Client**: Single httpx.AsyncClient instance  

#### Correct API Endpoints:
```python
# Page Operations
GET    /rest/api/content/{page_id}           # Get page
POST   /rest/api/content                     # Create page  
PUT    /rest/api/content/{page_id}           # Update page
DELETE /rest/api/content/{page_id}           # Delete page (to trash)
GET    /rest/api/content/search              # Search pages

# Attachment Operations  
GET    /rest/api/content/{page_id}/child/attachment  # List attachments
POST   /rest/api/content/{page_id}/child/attachment  # Add attachment
DELETE /rest/api/content/{attachment_id}             # Delete attachment
```

#### FORBIDDEN API Patterns:
```python
❌ DELETE /wiki/rest/api/content/{page_id}  # Wrong - no /wiki prefix
❌ GET    /api/content/{page_id}            # Wrong - missing /rest
❌ POST   /rest/content                     # Wrong - missing /api
```

## 🗂️ FILE ORGANIZATION

### Mandatory Directory Structure:
```
confluence_mcp_server/
├── __init__.py                    # Package initialization
├── main.py                        # FastMCP server setup (SIMPLE)
├── mcp_actions/
│   ├── __init__.py
│   ├── schemas.py                 # Pydantic models
│   ├── page_actions.py            # Page CRUD operations
│   ├── attachment_actions.py      # Attachment operations  
│   └── comment_actions.py         # Comment operations (future)
├── utils/
│   ├── __init__.py
│   ├── logging_config.py          # Logging setup
│   └── error_handling.py          # Error utilities
tests/
├── __init__.py
├── conftest.py                    # Test fixtures (MAX 50 lines)
├── test_delete_page_tool.py       # Delete page tests
├── test_get_page_tool.py          # Get page tests  
├── test_create_page_tool.py       # Create page tests
├── test_search_pages_tool.py      # Search pages tests
├── test_update_page_tool.py       # Update page tests
└── test_integration.py            # Integration tests
```

### File Size Limits:
- `conftest.py`: Maximum 50 lines
- Individual test files: Maximum 200 lines each
- Tool logic files: Maximum 300 lines each
- `main.py`: Maximum 150 lines

## 🔒 SECURITY ARCHITECTURE

### Authentication Pattern:
```python
# Environment Variables (required)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@domain.com  
CONFLUENCE_API_TOKEN=your-api-token

# HTTP Client Setup
auth = (username, api_token)
client = httpx.AsyncClient(base_url=confluence_url, auth=auth, timeout=30.0)
```

### Error Handling Pattern:
```python
try:
    response = await client.delete(f"/rest/api/content/{page_id}")
    response.raise_for_status()
    return DeletePageOutput(page_id=page_id, status="success", message="...")
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Page {page_id} not found")
    elif e.response.status_code == 403:
        raise HTTPException(status_code=403, detail=f"Permission denied for page {page_id}")
    else:
        raise HTTPException(status_code=e.response.status_code, detail=f"API error: {str(e)}")
```

## 🚀 DEPLOYMENT ARCHITECTURE

### Development Environment:
- FastMCP server runs directly (no HTTP proxy)
- Environment variables from `.env` file
- Debug logging enabled

### Testing Environment:  
- FastMCP server with mock httpx.AsyncClient  
- In-memory transport (FastMCPTransport)
- Controlled test data and responses

### Production Environment (Future):
- FastMCP server with real Confluence integration
- Production Confluence API credentials
- Error logging and monitoring

## 📊 PERFORMANCE ARCHITECTURE

### Performance Requirements:
- **Test Suite**: Complete in <10 seconds
- **Individual Tests**: Complete in <2 seconds  
- **Tool Execution**: Complete in <5 seconds
- **Memory Usage**: <100MB for test suite

### Performance Patterns:
```python
# Connection Reuse
async with httpx.AsyncClient(...) as client:
    # Reuse client for multiple requests
    
# Concurrent Testing  
tasks = [mcp_client.call_tool(...) for _ in range(10)]
results = await asyncio.gather(*tasks)

# Timeout Handling
client = httpx.AsyncClient(timeout=30.0)
```

## 🔍 MONITORING & LOGGING

### Logging Architecture:
```python
# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Usage Pattern
logger = logging.getLogger(__name__)
logger.info(f"Deleting page {page_id}")
logger.error(f"Failed to delete page {page_id}: {error}", exc_info=True)
```

### Error Categories:
- **Configuration Errors**: Missing environment variables
- **Authentication Errors**: Invalid Confluence credentials  
- **API Errors**: Confluence REST API failures
- **Validation Errors**: Invalid input parameters
- **Network Errors**: Connection timeouts, DNS failures

## 🚫 ANTI-PATTERNS (STRICTLY FORBIDDEN)

### 1. Complex HTTP Proxy Architecture
```python
❌ # DO NOT DO THIS
def create_root_app():
    # Complex proxy setup with threading
    pass
```

### 2. Manual Tool Registration Loops
```python
❌ # DO NOT DO THIS  
def _tool_adapter_factory(mcp_server, tool_name, ...):
    def generic_tool_logic_adapter(...):
        pass
    mcp_server.add_tool(...)  # Wrong pattern
```

### 3. Complex Async Context Managers
```python
❌ # DO NOT DO THIS
async with app.router.lifespan_context(app):  # This doesn't exist
    pass
```

### 4. Threading in Tests
```python
❌ # DO NOT DO THIS
server_thread = threading.Thread(target=run_server)
server_thread.start()
```

### 5. HTTP TestClient for MCP
```python
❌ # DO NOT DO THIS  
from fastapi.testclient import TestClient
client = TestClient(app)  # Wrong for MCP testing
```

## ✅ APPROVED PATTERNS (USE THESE)

### 1. Direct FastMCP Tool Registration
```python
✅ # CORRECT PATTERN
@mcp_server.tool(name="delete_confluence_page")
async def delete_page_tool(page_id: str) -> dict:
    return await delete_page_logic(confluence_client, DeletePageInput(page_id=page_id))
```

### 2. Simple Test Fixtures
```python
✅ # CORRECT PATTERN
@pytest_asyncio.fixture
async def mcp_client(mcp_server_instance):
    transport = FastMCPTransport(mcp_server_instance)
    async with Client(transport=transport) as client:
        yield client
```

### 3. httpx.AsyncClient Mocking
```python
✅ # CORRECT PATTERN  
confluence_client_mock.delete.return_value = HTTPXResponse(204, ...)
result = await mcp_client.call_tool("delete_confluence_page", {"page_id": "123"})
```

## 🎯 IMPLEMENTATION CHECKLIST

Before any code changes, verify:
- [ ] Architecture follows Direct FastMCP pattern
- [ ] No HTTP proxy or threading code
- [ ] Tools registered with decorators only  
- [ ] Tests use FastMCPTransport (in-memory)
- [ ] httpx.AsyncClient properly mocked
- [ ] File structure matches specification
- [ ] Error handling covers all HTTP codes
- [ ] Performance requirements met
- [ ] Security patterns followed
- [ ] Logging properly configured

**Remember**: This architecture prioritizes simplicity, testability, and maintainability. Complex patterns are explicitly forbidden.