# TASK.md - Confluence MCP Server Implementation

## 🎯 PROJECT OVERVIEW

**Project Name**: Confluence MCP Server  
**Framework**: FastMCP (jlowin/fastmcp)  
**Purpose**: MCP server providing Confluence integration tools for LLMs  
**Architecture**: Simplified Direct FastMCP (NO HTTP Proxy, NO Threading)  

## 🚨 CRITICAL RULES - DO NOT DEVIATE

### ❌ FORBIDDEN APPROACHES
1. **NO HTTP Proxy Architecture** - Do not create HTTP servers or proxy endpoints
2. **NO Threading** - Do not run FastMCP in separate threads
3. **NO Complex Lifespan Management** - Use simple, direct FastMCP patterns
4. **NO Manual Tool Registration Loops** - Use FastMCP decorators only
5. **NO `app.router.lifespan_context()`** - This method doesn't exist

### ✅ MANDATORY APPROACHES  
1. **Direct FastMCP Testing** - Use in-memory FastMCPTransport
2. **Decorator Pattern** - Register tools with `@mcp_server.tool()` decorators
3. **Simple Fixtures** - Minimal pytest fixtures with clear responsibilities
4. **Mock httpx.AsyncClient** - Mock the HTTP client, not the Confluence API
5. **Single Process Testing** - All tests run in single async event loop

## 📋 TASK BREAKDOWN

### Phase 1: Core Architecture (PRIORITY 1)
- [x] **T1.1**: Fix main.py tool registration (Remove `_tool_adapter_factory`)
- [x] **T1.2**: Implement proper FastMCP tool decorators  
- [x] **T1.3**: Fix Confluence API URLs (remove `/wiki` prefix)
- [x] **T1.4**: Simplify application startup (no threading)
- [x] **T1.5**: Create proper httpx.AsyncClient setup

### Phase 2: Testing Infrastructure (PRIORITY 1)
- [x] **T2.1**: Create simplified conftest.py (max 50 lines)
- [x] **T2.2**: Implement FastMCPTransport testing
- [x] **T2.3**: Create httpx.AsyncClient mock fixtures
- [x] **T2.4**: Remove all HTTP proxy test code
- [x] **T2.5**: Verify pytest-asyncio configuration (Resolved: Migrated to and configured pytest-anyio, removed pytest-asyncio, suppressed related warnings)

### Phase 3: Test Implementation (PRIORITY 2)
- [x] **T3.1**: Implement delete_page tool tests (1 test case complete: `test_delete_page_success` - PASSING)
- [x] **T3.2**: Implement get_page tool tests (7 test cases completed: success by ID, success by space+title, not found, API error, invalid input variations, content expansion - ALL PASSING)
- [x] **T3.3**: Implement create_page tool tests (9 test cases completed: success minimal, success with parent, title already exists error, space not found error, API error, connection error, MCP tool tests - ALL PASSING)
- [ ] **T3.4**: Implement update_page tool tests
- [ ] **T3.5**: Implement search_pages tool tests

### Phase 4: Validation & Documentation (PRIORITY 3)
- [ ] **T4.1**: Final architectural review
- [ ] **T4.2**: Update README.md with setup and usage
- [ ] **T4.3**: Add inline code comments for clarity
- [ ] **T4.4**: Ensure all dependencies are pinned
- [ ] **T4.5**: Create a `requirements-dev.txt` (or ensure pyproject.toml dev group is complete)

## ✅ CHECKLISTS (Mark as [x] when complete)

### Architectural Validation
- [x] FastMCP server initialized directly (no HTTP proxy)
- [x] FastMCP server NOT run in a separate thread for testing
- [x] All tools registered using FastMCP decorators
- [x] Confluence API URLs are correct
- [x] httpx.AsyncClient is used for API calls
- [x] Async context management is simple and direct
- [x] No complex lifespan events for FastMCP
- [x] FastMCP tools registered with decorators only
- [x] Single async event loop for all tests (managed by pytest-anyio)

### Code Quality Validation  
- [ ] All imports are absolute (no relative imports)
- [x] httpx.AsyncClient properly mocked in tests
- [ ] Error handling covers all HTTP status codes (Partially for delete_page)
- [x] Logging configured and working
- [x] Type hints present and correct (Largely, ongoing)

### Test Validation
- [x] Tests use FastMCPTransport (in-memory via Client)
- [x] Fixtures are simple and focused  
- [x] Mock strategies are consistent
- [x] Test data is realistic (For `test_delete_page_success`)
- [ ] Edge cases are covered (Partially for delete_page)

## 🔄 IMPLEMENTATION ORDER

**DO NOT CHANGE THIS ORDER WITHOUT APPROVAL**

1. **First**: Fix main.py (T1.1-T1.5) - **DONE**
2. **Second**: Create new conftest.py (T2.1-T2.5) - **DONE** 
3. **Third**: Implement delete_page tests (T3.1) - **IN PROGRESS**
4. **Fourth**: Verify everything works before proceeding - **DONE for current progress**
5. **Fifth**: Add remaining tool tests (T3.2-T3.5)
6. **Sixth**: Validation and documentation (T4.1-T4.5)

## 💀 COMMON MISTAKES TO AVOID

1. **DO NOT** create complex HTTP proxy setups
2. **DO NOT** use threading for FastMCP server
3. **DO NOT** try to fix the current `_tool_adapter_factory` - DELETE IT
4. **DO NOT** create manual tool registration loops
5. **DO NOT** use `TestClient` - use `FastMCPTransport`
6. **DO NOT** mock Confluence API endpoints - mock httpx.AsyncClient
7. **DO NOT** create complex lifespan management code
8. **DO NOT** use relative imports in tests

## 📞 ESCALATION CRITERIA

Stop work and escalate if:
- Tests still fail after implementing recommended approach
- You're tempted to use HTTP proxy or threading
- FastMCP tool registration isn't working with decorators
- You need to create complex async context managers
- Any single test takes >2 seconds to run

## 🏆 DEFINITION OF DONE

Task is complete when:
- All tests pass consistently (5+ runs)
- Test suite runs in <10 seconds total  
- Code follows architectural principles
- No forbidden approaches are used
- Documentation is updated

**Remember**: Simplicity is the goal. If it feels complex, you're probably doing it wrong.

## 📝 RECENT COMPLETION SUMMARY

### ✅ Session Accomplishments (Latest)
- **Fixed ALL remaining tool registration issues**: Removed incorrect context parameters from all remaining tools:
  - ✅ search_confluence_pages: Removed context parameter from search_pages_logic call
  - ✅ update_confluence_page: Removed context parameter from update_page_logic call
  - ✅ get_confluence_spaces: Removed context parameter from get_spaces_logic call
  - ✅ get_page_attachments: Removed context parameter from get_attachments_logic call
  - ✅ add_page_attachment: Removed context parameter from add_attachment_logic call
  - ✅ delete_page_attachment: Removed context parameter from delete_attachment_logic call
  - ✅ get_page_comments: Removed context parameter from get_comments_logic call
- **Fixed Claude Desktop compatibility**: Switched from custom HTTP server to standard stdio transport
- **Updated dependencies**: Upgraded to FastMCP 2.4.0 for latest MCP protocol compatibility
- **Created Claude Desktop integration files**:
  - ✅ claude_desktop_config.json template
  - ✅ setup_claude_desktop.py automated setup script
- **Verified compatibility**: All 17 asyncio tests passing, no tool registration errors

### 🔧 Claude Desktop Compatibility Fixes Applied
1. **Transport Protocol**: Changed from `asyncio.run(server_to_run.serve())` to `server_to_run.run()` (stdio transport)
2. **Dependency Updates**: FastMCP 2.4.0, removed unused FastAPI/Uvicorn dependencies
3. **Tool Consistency**: All tools now follow the same (client, inputs) pattern without context mismatches
4. **Configuration**: Provided proper Claude Desktop config template and setup automation
5. **Error Handling**: Maintained proper McpError/ErrorData format for MCP protocol compliance

### 📋 Claude Desktop Connection Status
- **Ready for Claude Desktop**: ✅ Server now uses stdio transport (Claude Desktop standard)
- **No anticipated errors**: ✅ All tool signatures consistent, latest FastMCP version
- **Setup automation**: ✅ Run `python setup_claude_desktop.py` for automatic configuration
- **Environment setup**: ✅ Credentials configured via Claude Desktop config (secure)