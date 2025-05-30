# Confluence MCP Server v2.0 🚀 Revolutionary Selective Editing

![Release](https://img.shields.io/badge/release-v2.0.0-gold.svg) ![Status](https://img.shields.io/badge/status-revolutionary-brightgreen.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Platform](https://img.shields.io/badge/platform-universal-blue.svg)

🎉 **INTRODUCING v2.0: Industry's First XML-Aware Selective Editing System for AI Assistants**

A **revolutionary MCP (Model Context Protocol) server** that transforms how AI assistants interact with Confluence. Beyond basic page management, v2.0 introduces **surgical precision editing** that allows AI to make targeted modifications while preserving all existing content, formatting, and macros.

## ✨ What Makes v2.0 Revolutionary

### 🎯 **Surgical Precision Editing**
Unlike traditional "replace entire page" approaches, v2.0 enables:
- **Section Updates**: Modify specific sections under headings without touching other content
- **Pattern Replacement**: Find and replace text while preserving XML structure and macros
- **Table Cell Editing**: Update individual table cells without affecting table structure
- **Structure Preservation**: Maintains all formatting, layouts, macros, and custom elements

### 🧠 **XML-Aware Intelligence**
- **Confluence Storage Format Expert**: Understands and preserves Confluence's complex XML structure
- **Macro Safety**: Never breaks macros, layouts, or custom elements during edits
- **Content Analysis**: Intelligently identifies safe editing locations and content boundaries
- **Rollback Capability**: Automatic backup creation for safe editing operations

### 🛠️ **13 Powerful Tools**
**Standard Tools (10)**: Complete page, space, attachment, and comment management
**🆕 Selective Editing Tools (3)**: Revolutionary precision editing capabilities

## 🚀 Revolutionary Selective Editing Tools

### 1. `update_page_section` - Surgical Section Replacement
Updates specific sections under headings without affecting surrounding content.

**Example**: Update project status without touching meeting notes
```
AI: "Update the 'Project Status' section to show completed milestones"
✅ Updates only that section, preserves all other content
```

**Features**:
- Intelligent heading detection (H1-H6) with hierarchy support
- Flexible matching: case-sensitive, exact match, or fuzzy search
- Nested heading support for complex document structures
- Preserves all macros, layouts, and formatting outside target section

### 2. `replace_text_pattern` - XML-Aware Find & Replace
Replaces text patterns throughout pages while preserving document structure.

**Example**: Update product version across documentation
```
AI: "Replace all instances of 'v1.2.3' with 'v2.0.0' in the API docs"
✅ Updates version numbers while preserving links, macros, and formatting
```

**Features**:
- Smart content detection distinguishes text from XML markup
- Case sensitivity and whole-word matching options
- Replacement limits for controlled changes
- Never breaks macros, links, or formatting elements

### 3. `update_table_cell` - Precision Table Editing
Updates specific table cells while maintaining table structure and formatting.

**Example**: Update project metrics in status tables
```
AI: "Update the completion percentage in row 2, column 3 to 95%"
✅ Changes only that cell, preserves table formatting and other data
```

**Features**:
- Zero-based indexing for precise cell targeting
- Rich HTML content support within cells
- Table structure preservation (borders, styling, headers)
- Surgical precision - only target cell is modified

## 🌐 Universal Deployment Platform

### 🚀 Deployment Options

| Platform | Transport | Status | Tools Available |
|----------|-----------|--------|-----------------|
| **Claude Desktop** | stdio | ✅ All 13 Tools | Local development, personal use |
| **Smithery.ai** | HTTP | ✅ All 13 Tools | Cloud deployment, team sharing |
| **Docker** | HTTP/stdio | ✅ All 13 Tools | Containerized deployment |
| **Web Clients** | HTTP | ✅ All 13 Tools | Browser-based AI tools |
| **Cloud Platforms** | HTTP | ✅ All 13 Tools | Railway, Heroku, AWS, etc. |

## 🛠️ Complete Tool Suite

### 📄 **Standard Confluence Tools (10)**

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `get_confluence_page` | Retrieve page content | "Show me the content of page ID 123456" |
| `create_confluence_page` | Create new pages | "Create a meeting notes page in the PROJ space" |
| `update_confluence_page` | Modify entire pages | "Replace all content in page 123456" |
| `delete_confluence_page` | Remove pages | "Delete the outdated page 123456" |
| `search_confluence_pages` | Search with CQL | "Find all pages in PROJ space modified this week" |
| `get_confluence_spaces` | List available spaces | "What spaces do I have access to?" |
| `get_page_attachments` | View page attachments | "Show attachments on page 123456" |
| `add_page_attachment` | Upload files | "Upload this document to page 123456" |
| `delete_page_attachment` | Remove files | "Delete the old attachment from page 123456" |
| `get_page_comments` | Read page comments | "Show me comments on page 123456" |

### 🎯 **Revolutionary Selective Editing Tools (3)**

| Tool | Description | Revolutionary Capability |
|------|-------------|--------------------------|
| `update_page_section` | Surgical section replacement | Updates specific headings without touching other sections |
| `replace_text_pattern` | XML-aware pattern replacement | Replaces text while preserving macros and formatting |
| `update_table_cell` | Precision table cell editing | Modifies individual cells without affecting table structure |

## 🚀 Quick Start

### 📚 **New to Selective Editing?** 
👉 **[Complete Step-by-Step Tutorial](TUTORIAL.md)** - Learn revolutionary selective editing with hands-on examples!

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

3. **Restart Claude Desktop** and look for the 🔨 hammer icon showing **13 tools**

### Option 2: HTTP Server

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
   python -m confluence_mcp_server.server_http_optimized
   ```

4. **Test the Server**:
   ```bash
   curl http://localhost:8000/mcp
   # Returns: 13 tools including selective editing capabilities
   ```

### Option 3: Docker Deployment

1. **Build Container**:
   ```bash
   docker build -f Dockerfile.smithery -t confluence-mcp-server-v2 .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8000:8000 \
     -e CONFLUENCE_URL="https://your-org.atlassian.net" \
     -e CONFLUENCE_USERNAME="your-email@domain.com" \
     -e CONFLUENCE_API_TOKEN="your-api-token" \
     confluence-mcp-server-v2
   ```

### Option 4: Smithery.ai Deployment

1. **Upload Files**: Upload `smithery.yaml` and server code to Smithery.ai
2. **Configure Credentials**: Set Confluence URL, username, and API token
3. **Deploy**: Smithery.ai automatically provides all 13 tools including selective editing

## 💬 Revolutionary AI Assistant Workflows

### 🎯 **Selective Editing Examples**

**📚 Need Step-by-Step Guidance?** 
👉 **[Complete Selective Editing Tutorial](TUTORIAL.md)** - Hands-on guide with examples, workflows, and troubleshooting

**Update Project Status Without Disrupting Meeting Notes**:
```
You: Update the project status section to show we completed the API development milestone

AI: I'll update just the project status section while preserving all your meeting notes...
[Uses update_page_section tool]
✅ Updated "Project Status" section only - meeting notes, action items, and formatting preserved
```

**Fix Typos Across Documentation**:
```
You: Fix the typo "recieve" to "receive" throughout our API documentation pages

AI: I'll find and fix that typo while preserving all links and formatting...
[Uses replace_text_pattern tool]  
✅ Fixed 12 instances across 5 pages - all macros, links, and formatting preserved
```

**Update Metrics in Status Dashboard**:
```
You: Update the completion percentage in our project dashboard table to 85%

AI: I'll update that specific table cell without affecting the rest of the dashboard...
[Uses update_table_cell tool]
✅ Updated table cell [2,3] to "85%" - table structure and other metrics preserved
```

### 📄 **Traditional Page Management**:
```
You: Create a new project kickoff page in the ENGINEERING space

AI: I'll create a project kickoff page for you...
[Uses create_confluence_page tool]
✅ Created "Project Kickoff" page (ID: 789123) in ENGINEERING space
```

## 🔧 Advanced Configuration

### v2.0 Selective Editing Features
The selective editing system provides several advanced options:

#### Content Analysis Engine
- **Heading Hierarchy Detection**: Automatically identifies H1-H6 structure
- **Section Boundary Analysis**: Precisely identifies content boundaries
- **Macro Detection**: Recognizes and preserves Confluence macros
- **Table Structure Analysis**: Understands complex table layouts

#### Safety Features
- **Backup Creation**: Automatic content backup before modifications
- **Rollback Capability**: Restore original content if needed
- **Validation Engine**: Ensures modifications won't break page structure
- **Error Recovery**: Graceful handling of complex XML scenarios

### Environment Variables
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

## 🔒 Security & Authentication

- **API Tokens**: Secure token-based authentication with Confluence
- **HTTPS Only**: All API requests use encrypted connections
- **Permission Inheritance**: Server inherits your Confluence user permissions
- **No Data Storage**: Direct API passthrough, no local data retention
- **Selective Editing Security**: Automatic backup creation prevents data loss

## 🧪 Testing & Validation

### Run Complete Test Suite
```bash
# Run all 217 tests (214 selective editing + 3 MCP integration)
python -m pytest tests/ -v

# Test selective editing specifically
python -m pytest tests/test_section_editor.py -v
python -m pytest tests/test_pattern_editor.py -v
python -m pytest tests/test_structural_editor.py -v

# Validate v2.0 functionality
python -c "
from confluence_mcp_server.selective_editing import SectionEditor, PatternEditor, StructuralEditor;
print('✅ v2.0 selective editing modules loaded successfully')
"
```

### Health Checks
```bash
# HTTP transport with selective editing
python -m confluence_mcp_server.server_http_optimized &
curl http://localhost:8000/mcp
# Should show 13 tools including selective editing
```

## 🔄 Migration from v1.x

**100% Backward Compatible** - all existing tools continue working unchanged.

### What's New in v2.0:
- ✅ **3 Revolutionary Selective Editing Tools**: `update_page_section`, `replace_text_pattern`, `update_table_cell`
- ✅ **XML-Aware Content Analysis**: Deep understanding of Confluence storage format
- ✅ **Structure Preservation**: Maintains all formatting, macros, and layouts
- ✅ **Backup & Rollback**: Automatic content backup for safe editing
- ✅ **Enhanced HTTP Servers**: All servers now include selective editing capabilities
- ✅ **217 Comprehensive Tests**: Extensive test coverage for all functionality

### Upgrading from v1.x:
1. **No changes needed** for existing configurations
2. **New tools automatically available** in all deployments
3. **Enhanced capabilities** without breaking changes
4. **Performance improvements** with lazy loading architecture

## 🐛 Troubleshooting

### v2.0 Selective Editing Issues
- **Tool not found**: Verify deployment includes updated server files
- **Section not found**: Check heading text and level parameters
- **XML parsing errors**: Selective editing includes fallback mechanisms
- **Backup not created**: Check page permissions and storage space

### General Issues
- **Authentication fails**: Verify API token and Confluence URL
- **Tools not showing**: Ensure all 13 tools are registered (check tool count)
- **Performance issues**: Selective editing uses lazy loading for optimal performance

## 📦 Production Deployment

### Cloud Platforms with v2.0
All cloud platforms now support the complete selective editing suite:

**Smithery.ai** (Recommended):
- Automatic configuration management
- All 13 tools available immediately
- Optimized for fast tool discovery
- Revolutionary selective editing ready

**Railway/Heroku/AWS**:
- Use updated `Dockerfile.smithery` for v2.0 capabilities
- Set environment variables in platform configuration
- Health check endpoint shows tool count for verification

## 🎯 v2.0 Use Cases

### Content Management Revolution
- **Living Documentation**: Update specific sections as projects evolve
- **Version Management**: Update version numbers across multiple pages instantly
- **Status Dashboards**: Update metrics without affecting layout or other data
- **Collaborative Editing**: Make targeted edits without disrupting team workflows

### Enterprise Scenarios
- **API Documentation**: Update endpoints while preserving examples and troubleshooting
- **Project Tracking**: Update status reports while maintaining historical context
- **Knowledge Base**: Fix typos and update information while preserving formatting
- **Compliance Documentation**: Update policies while maintaining approval workflows

## 🤝 Development

### v2.0 Architecture
```
confluence_mcp_server/
├── main.py                    # stdio transport with all 13 tools
├── server_http_optimized.py   # HTTP transport with all 13 tools
├── selective_editing/         # 🆕 Revolutionary editing engine
│   ├── section_editor.py     # Section-based operations
│   ├── pattern_editor.py     # Pattern replacement operations  
│   ├── structural_editor.py  # Table and list operations
│   ├── content_analyzer.py   # XML content analysis
│   ├── xml_parser.py         # Confluence XML parser
│   └── operations.py         # Operation definitions
├── mcp_actions/              # Standard tool implementations
└── tests/                    # 217 comprehensive tests

Phase Documentation:
├── Phase-1-Foundation.md     # XML parsing and operations
├── Phase-2-ContentAnalysis.md # Content structure analysis  
├── Phase-3-SectionOps.md     # Section-based editing
├── Phase-4-PatternOps.md     # Pattern operations
├── Phase-5-StructuralOps.md  # Table and list editing
└── Phase-6-MCPIntegration.md # MCP tool integration
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🚀 Experience the Future of Confluence AI Integration

### Choose Your Adventure:

- **🎯 Precision Editing**: Use selective editing tools for surgical modifications
- **📄 Complete Management**: Use standard tools for full page operations  
- **🌐 Universal Access**: Deploy anywhere with HTTP transport
- **🖥️ Local Development**: Use Claude Desktop for immediate access

**Transform your Confluence workflow with revolutionary AI-assisted editing!** 🎉

### Ready to Get Started?

1. **Developers**: Try selective editing in Claude Desktop
2. **Teams**: Deploy on Smithery.ai for instant access
3. **Enterprise**: Use Docker deployment for production environments

**Welcome to the future of AI-assisted content management!** ✨
