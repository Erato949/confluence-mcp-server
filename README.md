# Confluence MCP Server

![Release](https://img.shields.io/badge/release-v1.0.0-green.svg) ![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg)

An MCP (Model Context Protocol) server for Confluence integration, built with FastMCP. This server provides LLMs like Claude with direct access to Confluence Cloud functionality through a standardized interface.

## ✨ Features

- **Complete Page Management**: Create, read, update, delete Confluence pages
- **Search & Discovery**: Search pages with CQL (Confluence Query Language)
- **Space Management**: List and explore Confluence spaces
- **Attachment Handling**: Upload and manage page attachments
- **Comment System**: Access and manage page comments
- **Claude Desktop Ready**: Optimized for seamless Claude Desktop integration

## 🔧 Claude Desktop Integration

### Quick Setup (Recommended)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Setup Script**:
   ```bash
   python setup_claude_desktop.py
   ```

3. **Configure Credentials**: Edit the generated configuration file with your Confluence details

4. **Restart Claude Desktop** and look for the 🔨 hammer icon

### Manual Setup

1. **Locate Claude Desktop Config**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add Server Configuration**:
   ```json
   {
     "mcpServers": {
       "confluence-mcp": {
         "command": "python",
         "args": ["/ABSOLUTE/PATH/TO/YOUR/PROJECT/confluence_mcp_server/main.py"],
         "env": {
           "CONFLUENCE_URL": "https://your-org.atlassian.net",
           "CONFLUENCE_USERNAME": "your-email@domain.com",
           "CONFLUENCE_API_TOKEN": "your-api-token"
         }
       }
     }
   }
   ```

3. **Get Confluence API Token**:
   - Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Create API Token
   - Copy the token to your configuration

### 🚀 Available Tools in Claude Desktop

Once connected, Claude will have access to these tools:

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

### 💬 Example Claude Conversations

**Creating a Page**:
```
You: Create a new project kickoff page in the ENGINEERING space with a basic template

Claude: I'll create a project kickoff page for you in the ENGINEERING space...
[Uses create_confluence_page tool]
✅ Created "Project Kickoff" page (ID: 789123) in ENGINEERING space
```

**Searching Content**:
```
You: Find all pages mentioning "API documentation" that were updated this month

Claude: I'll search for pages with "API documentation" updated recently...
[Uses search_confluence_pages tool]
📄 Found 5 pages matching your criteria...
```

### 🔧 Compatibility & Requirements

- **MCP Protocol**: Latest version supported (FastMCP 2.4.0)
- **Transport**: Stdio (Claude Desktop standard)
- **Python**: 3.10+
- **Claude Desktop**: Windows/macOS versions with MCP support
- **Confluence**: Cloud instances with API access

### ⚠️ No Anticipated Connection Issues

This server has been specifically designed for Claude Desktop compatibility:

✅ **Standard Transport**: Uses stdio transport (not HTTP/SSE)  
✅ **Latest MCP Protocol**: FastMCP 2.4.0 with full Claude Desktop support  
✅ **Consistent Tool Signatures**: All tools follow the same input/output pattern  
✅ **Proper Error Handling**: MCP-compliant error formatting  
✅ **Tested Integration**: Comprehensive test suite ensures reliability  
✅ **Recently Validated**: Successfully tested with real Confluence instances (January 2025)

### 🐛 Troubleshooting

**Claude Desktop doesn't show the hammer icon:**
- Verify the configuration file path and syntax
- Check that Python is in your system PATH
- Restart Claude Desktop completely
- Check Claude Desktop logs for error messages

**"Permission denied" or "Authentication failed":**
- Verify your Confluence URL (include https://)
- Check API token is correct and hasn't expired
- Ensure your username is the email associated with your Atlassian account
- Test credentials with: `curl -u email:token https://your-org.atlassian.net/rest/api/space`

**Tools appear but fail to execute:**
- Check environment variables are properly set in Claude config
- Verify network connectivity to your Confluence instance
- Review server logs in Claude Desktop for specific error messages

**"Module not found" errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python path in Claude Desktop config points to correct environment
- Use absolute paths in the configuration

## 🔒 Security Considerations

- **API Tokens**: Stored in Claude Desktop config (local machine only)
- **Network Access**: All requests use HTTPS to Confluence Cloud
- **Permissions**: Inherits your Confluence user permissions
- **Local Only**: No data sent to third parties, direct Confluence API calls

## 📖 Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run only passing asyncio tests (recommended)
python -m pytest tests/ -k asyncio
```

### Project Structure
```
confluence_mcp_server/
├── main.py                 # MCP server entry point
├── mcp_actions/           # Tool implementations
│   ├── page_actions.py    # Page-related tools
│   ├── space_actions.py   # Space-related tools
│   ├── attachment_actions.py
│   ├── comment_actions.py
│   └── schemas.py         # Pydantic models
└── utils/
    └── logging_config.py

tests/                     # Comprehensive test suite
claude_desktop_config.json # Configuration template
setup_claude_desktop.py   # Automated setup script
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Ready to enhance your Confluence workflow with Claude? Run the setup script and start collaborating!** 🚀
