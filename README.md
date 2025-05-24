# Confluence MCP Server

![Release](https://img.shields.io/badge/release-v1.1.0-green.svg) ![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Platform](https://img.shields.io/badge/platform-universal-blue.svg)

A **universal, production-ready MCP (Model Context Protocol) server** for Confluence integration. Built with FastMCP, this server provides AI assistants like Claude with direct access to Confluence Cloud functionality through multiple transport protocols and deployment options.

## 🌐 Universal Deployment Platform

**NEW in v1.1.0**: Multi-platform support with HTTP transport alongside the original stdio transport.

### 🚀 Deployment Options

| Platform | Transport | Status | Use Case |
|----------|-----------|--------|----------|
| **Claude Desktop** | stdio | ✅ 100% Compatible | Local development, personal use |
| **Smithery.ai** | HTTP | 🔧 Optimized | Cloud deployment, team sharing (optimized server) |
| **Docker** | HTTP/stdio | ✅ Production Ready | Containerized deployment |
| **Web Clients** | HTTP | ✅ Production Ready | Browser-based AI tools |
| **Cloud Platforms** | HTTP | ✅ Production Ready | Railway, Heroku, AWS, etc. |

## ✨ Features

- **Complete Page Management**: Create, read, update, delete Confluence pages
- **Advanced Search**: Search pages with CQL (Confluence Query Language) support
- **Space Management**: List and explore Confluence spaces with permissions
- **Attachment Handling**: Upload, download, and manage page attachments
- **Comment System**: Access and manage page comments and discussions
- **Multi-Transport**: stdio (Claude Desktop) + HTTP (web/cloud platforms)
- **Universal Launcher**: Auto-detects best transport mode for your environment
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## 🚀 Quick Start

### Option 1: Claude Desktop (stdio transport)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Claude Desktop**:
   ```json
   {
     "mcpServers": {
       "confluence": {
         "command": "python",
         "args": ["-m", "confluence_mcp_server.main"],
         "env": {
           "CONFLUENCE_URL": "https://your-org.atlassian.net",
           "CONFLUENCE_USERNAME": "your-email@domain.com",
           "CONFLUENCE_API_TOKEN": "your-api-token"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** and look for the 🔨 hammer icon

### Option 2: HTTP Server (new in v1.1.0)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export CONFLUENCE_URL="https://your-org.atlassian.net"
   export CONFLUENCE_USERNAME="your-email@domain.com"
   export CONFLUENCE_API_TOKEN="your-api-token"
   ```

3. **Start HTTP Server**:
   ```bash
   python -m confluence_mcp_server.server_http
   ```

4. **Test the Server**:
   ```bash
   curl http://localhost:8000/health
   # Returns: {"status": "healthy", "transport": "http"}
   ```

### Option 3: Docker Deployment (new in v1.1.0)

1. **Build Container**:
   ```bash
   docker build -t confluence-mcp-server .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8000:8000 \
     -e CONFLUENCE_URL="https://your-org.atlassian.net" \
     -e CONFLUENCE_USERNAME="your-email@domain.com" \
     -e CONFLUENCE_API_TOKEN="your-api-token" \
     confluence-mcp-server
   ```

### Option 4: Universal Launcher (new in v1.1.0)

The universal launcher automatically detects the best transport mode:

```bash
# Auto-detect transport mode
python -m confluence_mcp_server.launcher

# Force specific mode
python -m confluence_mcp_server.launcher --http --port 9000
python -m confluence_mcp_server.launcher --stdio
```

### Option 5: Smithery.ai Deployment (new in v1.1.0)

1. **Upload Files**: Upload `smithery.yaml` and server code to Smithery.ai
2. **Configure Credentials**: Set Confluence URL, username, and API token
3. **Deploy**: Smithery.ai handles the rest automatically

## 🛠️ Available Tools

All 10 Confluence tools work across **all transport modes** (stdio and HTTP):

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `get_confluence_page` | Retrieve page content | "Show me the content of page ID 123456" |
| `create_confluence_page` | Create new pages | "Create a meeting notes page in the PROJ space" |
| `update_confluence_page` | Modify existing pages | "Add a new section to page 123456" |
| `delete_confluence_page` | Remove pages | "Delete the outdated page 123456" |
| `search_confluence_pages` | Search with CQL | "Find all pages in PROJ space modified this week" |
| `get_confluence_spaces` | List available spaces | "What spaces do I have access to?" |
| `get_page_attachments` | View page attachments | "Show attachments on page 123456" |
| `add_page_attachment` | Upload files | "Upload this document to page 123456" |
| `delete_page_attachment` | Remove files | "Delete the old attachment from page 123456" |
| `get_page_comments` | Read page comments | "Show me comments on page 123456" |

## 🌐 HTTP API Endpoints (v1.1.0)

The HTTP transport provides these endpoints for web integration:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server information and tool count |
| `/health` | GET | Health check and status |
| `/mcp` | GET | List available tools (lazy loading) |
| `/mcp` | POST | Execute tools via JSON-RPC 2.0 |
| `/mcp` | DELETE | Session cleanup |

### Example HTTP Usage

```bash
# List available tools
curl http://localhost:8000/mcp

# Execute a tool via JSON-RPC
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_confluence_spaces",
      "arguments": {"limit": 10}
    }
  }'
```

## 💬 Example AI Assistant Conversations

**Creating a Page** (works on all platforms):
```
You: Create a new project kickoff page in the ENGINEERING space with a basic template

AI: I'll create a project kickoff page for you in the ENGINEERING space...
[Uses create_confluence_page tool]
✅ Created "Project Kickoff" page (ID: 789123) in ENGINEERING space
```

**Searching Content**:
```
You: Find all pages mentioning "API documentation" that were updated this month

AI: I'll search for pages with "API documentation" updated recently...
[Uses search_confluence_pages tool]
📄 Found 5 pages matching your criteria...
```

## 🔧 Configuration Options

### Platform Compatibility Notes

**Cursor**: Requires installation path with **no spaces**. Your current path `C:/Users/chris/Documents/Confluence-MCP-Server_Claude` is compatible.

**Windsurf**: Full MCP support with both stdio and HTTP transports.

**Smithery.ai**: Uses HTTP transport with automatic configuration management.

**Claude Desktop**: Uses stdio transport with manual configuration.

### Environment Variables (all platforms)
```bash
CONFLUENCE_URL=https://your-org.atlassian.net
CONFLUENCE_USERNAME=your-email@domain.com
CONFLUENCE_API_TOKEN=your-api-token
```

### .env File Support
```env
# .env file in project root
CONFLUENCE_URL=https://your-org.atlassian.net
CONFLUENCE_USERNAME=your-email@domain.com
CONFLUENCE_API_TOKEN=your-api-token
```

### Smithery.ai Configuration
The server automatically handles base64-encoded configuration from Smithery.ai platform.

## 🔒 Security & Authentication

- **API Tokens**: Secure token-based authentication with Confluence
- **HTTPS Only**: All API requests use encrypted connections
- **Permission Inheritance**: Server inherits your Confluence user permissions
- **No Data Storage**: Direct API passthrough, no local data retention
- **Container Security**: Non-root user, minimal attack surface

### Getting Confluence API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API Token"
3. Copy the generated token
4. Use your email address as the username

## 🧪 Testing & Validation

### Run Test Suite
```bash
# Run all tests
python -m pytest tests/ -v

# Test HTTP transport specifically
python -m pytest tests/test_http_transport.py -v

# Test specific functionality
python -m pytest tests/ -k "test_get_page"
```

### Validate Dependencies
```bash
python -c "
import fastmcp, fastapi, uvicorn, pytest_asyncio;
print('✅ All dependencies working correctly')
"
```

### Health Checks
```bash
# stdio transport (Claude Desktop)
python -c "import confluence_mcp_server.main; print('✅ stdio transport ready')"

# HTTP transport
python -m confluence_mcp_server.server_http &
curl http://localhost:8000/health
```

## 🔄 Migration from v1.0.x

**100% Backward Compatible** - no changes needed for existing Claude Desktop setups.

New capabilities in v1.1.0:
- ✅ HTTP transport for web/cloud deployment
- ✅ Docker containerization
- ✅ Smithery.ai integration
- ✅ Universal launcher
- ✅ Enhanced configuration management
- ✅ Production monitoring and health checks

## 🐛 Troubleshooting

### Claude Desktop Issues
- **No hammer icon**: Check config file syntax and restart Claude Desktop
- **Authentication fails**: Verify API token and Confluence URL
- **Tools fail**: Check environment variables and network connectivity

### Cursor Issues
- **"No tools found"**: Ensure installation path contains **no spaces**
  - ❌ `node C:/my projects/mcpserver/build/index.js` (fails due to space)
  - ✅ `node C:/projects/mcpserver/build/index.js` (works)
- **Windows paths**: Use forward slashes or properly escaped backslashes
- **Test manually first**: Verify server starts without errors before adding to Cursor
- **Check task manager**: Look for briefly appearing node processes during refresh

### HTTP Server Issues
- **Port conflicts**: Use `--port` flag to specify different port
- **CORS errors**: Server includes CORS middleware for web clients
- **Tool execution fails**: Check environment variables and Confluence permissions

### Docker Issues
- **Container won't start**: Check environment variables are properly set
- **Health check fails**: Verify Confluence connectivity from container
- **Permission errors**: Container runs as non-root user by default

### General Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m confluence_mcp_server.launcher

# Test Confluence connectivity
curl -u email:token https://your-org.atlassian.net/rest/api/space
```

## 📦 Production Deployment

### Cloud Platforms

**Railway**:
```bash
# Deploy directly from GitHub
railway login
railway link
railway up
```

**Heroku**:
```bash
# Use included Dockerfile
heroku container:push web
heroku container:release web
```

**AWS/GCP/Azure**:
- Use Docker image for container services
- Set environment variables in platform configuration
- Use health check endpoint `/health` for monitoring

### Monitoring

The HTTP server provides monitoring endpoints:
- **Health**: `GET /health` - Server status
- **Metrics**: `GET /` - Tool count and server info
- **Logs**: Structured logging for debugging and monitoring

## 🤝 Development

### Project Structure
```
confluence_mcp_server/
├── main.py                 # stdio transport (Claude Desktop)
├── server_http.py          # HTTP transport (web/cloud)
├── launcher.py             # Universal launcher
├── mcp_actions/           # Tool implementations
│   ├── page_actions.py    # Page management
│   ├── space_actions.py   # Space operations
│   ├── attachment_actions.py # File handling
│   ├── comment_actions.py # Comments
│   └── schemas.py         # Data models
└── utils/
    └── logging_config.py  # Logging setup

tests/                     # Comprehensive test suite
├── test_http_transport.py # HTTP transport tests
└── test_*.py             # Tool-specific tests

Dockerfile                 # Container configuration
smithery.yaml             # Smithery.ai deployment
pyproject.toml            # Package configuration
requirements.txt          # Dependencies
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/ -v`)
5. Test both stdio and HTTP transports
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🚀 Ready to Get Started?

Choose your deployment option:

- **🖥️ Claude Desktop**: Use the stdio transport for local development
- **🌐 Web/Cloud**: Use the HTTP transport for scalable deployment  
- **🐳 Docker**: Use containers for consistent deployment
- **⚡ Smithery.ai**: Use cloud platform for instant deployment

**Transform your Confluence workflow with AI assistance today!** 🎉
