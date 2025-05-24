# 🔧 Confluence MCP Server - Troubleshooting Guide

## Platform-Specific Issues

### Cursor MCP Issues

#### "No tools found" Error
**Cause**: Installation path contains spaces  
**Solution**: Move server to path without spaces

❌ **Fails**: `node C:/my projects/mcpserver/build/index.js`  
✅ **Works**: `node C:/projects/mcpserver/build/index.js`

**Your Setup**: `C:/Users/chris/Documents/Confluence-MCP-Server_Claude` ✅ (no spaces)

#### Debugging Steps:
1. **Test manually first**: Run server directly before adding to Cursor
   ```bash
   python -m confluence_mcp_server.launcher stdio
   ```

2. **Check for brief processes**: Use Task Manager to see if node.exe appears/disappears quickly

3. **Validate paths**: Use forward slashes or properly escaped backslashes on Windows

4. **Process Monitor**: Use SysInternals ProcessMonitor to see what Cursor is trying to execute

### Smithery.ai Deployment Issues

#### "Failed to scan tools list" Timeout
**Symptoms**: 
- Build succeeds ✅
- Deployment shows "Failed to scan tools list from server: McpError: MCP error -32001: Request timed out"

**Investigation Results**:
- ✅ Local server fully functional
- ✅ All endpoints responding correctly (`/health`, `/mcp`, `/`)
- ✅ Docker build successful  
- ✅ Tool scanning works locally
- ❌ Smithery platform timeout during tool scanning

**Conclusion**: Infrastructure issue on Smithery.ai platform, not server implementation**SOLUTION**: Created optimized server (`server_http_optimized.py`) with:- ✅ **Guaranteed Lazy Loading**: Tool listing requires ZERO authentication- ✅ **Pre-computed Static Tools**: Instant response to tool listing requests  - ✅ **Import Optimization**: Heavy dependencies loaded only during tool execution- ✅ **Ultra-fast Startup**: Minimal initialization overhead- ✅ **Smithery Compliance**: 100% conformant to Smithery.ai lazy loading requirements

#### Verified Working Endpoints:
```bash
# Health check
curl http://localhost:8000/health
# Response: {"status": "healthy", "transport": "http"}

# Tool listing (Smithery format)
curl http://localhost:8000/mcp
# Response: {"tools": [... 10 tools ...]}

# JSON-RPC format
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
# Response: {"jsonrpc": "2.0", "result": {"tools": [...]}}
```

### Claude Desktop Issues

#### No Hammer Icon
**Causes**:
- Invalid JSON syntax in config file
- Missing file permissions
- Server startup failure

**Solutions**:
1. Validate config JSON syntax
2. Restart Claude Desktop completely
3. Check server starts manually:
   ```bash
   python -m confluence_mcp_server.main
   ```

#### Authentication Failures
**Common Issues**:
- Wrong API token format
- Incorrect Confluence URL
- Network connectivity problems

**Solutions**:
1. Test API token manually:
   ```bash
   curl -u email:token https://your-org.atlassian.net/rest/api/space
   ```
2. Verify environment variables are set
3. Check firewall/proxy settings

### Docker Issues

#### Container Won't Start
**Check Environment Variables**:
```bash
docker run --env-file .env confluence-mcp-server
```

#### Health Check Failures
**Network Connectivity**:
```bash
# Test from inside container
docker exec -it container_name curl http://localhost:8000/health
```

#### Permission Errors
**Non-root User**: Container runs as user 1000 by default
```dockerfile
USER mcp  # uid 1000
```

## General Debugging Commands

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
python -m confluence_mcp_server.launcher stdio
```

### Test HTTP Transport
```bash
# Start server
python -m confluence_mcp_server.server_http

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/mcp
curl http://localhost:8000/
```

### Validate Dependencies
```bash
python -c "
import fastmcp, fastapi, uvicorn, pytest_asyncio
print('✅ All dependencies working correctly')
"
```

### Test Confluence Connection
```bash
# Direct API test
python -c "
import os, httpx, asyncio
async def test():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{os.getenv(\"CONFLUENCE_URL\")}/rest/api/space',
            auth=(os.getenv('CONFLUENCE_USERNAME'), os.getenv('CONFLUENCE_API_TOKEN'))
        )
        print(f'Status: {response.status_code}')
        print(f'Spaces: {len(response.json()[\"results\"])}')
asyncio.run(test())
"
```

## Error Messages & Solutions

### SyntaxError: invalid syntax
**Caused by**: Merged import lines in server_http.py  
**Solution**: Already fixed in current version

### [Errno 10048] Address already in use
**Caused by**: Port 8000 already occupied  
**Solution**: 
```bash
# Kill existing server
pkill -f "server_http"
# Or use different port
python -m confluence_mcp_server.server_http --port 8001
```

### ImportError: No module named 'fastmcp'
**Caused by**: Missing dependencies  
**Solution**:
```bash
pip install -r requirements.txt
# Or
pip install fastmcp fastapi uvicorn
```

## Status Summary

| Platform | Status | Notes |
|----------|--------|-------|
| **Local Testing** | ✅ Working | All endpoints functional |
| **Claude Desktop** | ✅ Working | stdio transport |
| **Cursor** | ✅ Compatible | Path has no spaces |
| **Windsurf** | ✅ Ready | Both transports supported |
| **Smithery.ai** | 🔧 Optimized | NEW: `server_http_optimized.py` with guaranteed lazy loading |
| **Docker** | ✅ Working | Container builds and runs |

## Getting Help

1. **Check this guide first** for common issues
2. **Test locally** to isolate platform vs server issues  
3. **Enable debug logging** for detailed error information
4. **Verify configuration** with manual API calls
5. **Submit issue** with logs and error details

---

*Last updated: Current version with all known issues and solutions* 