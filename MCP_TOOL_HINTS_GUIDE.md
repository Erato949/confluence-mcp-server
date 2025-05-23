# 🛠️ MCP Tool Hints & Description Guide

## Overview

This guide shows how to add helpful hints and descriptions to MCP tools so that Claude Desktop (and other MCP clients) can better understand how to use them effectively.

## 🎯 Methods for Adding Tool Hints

### 1. **Enhanced Tool Docstrings**

The tool function's docstring serves as the primary description. Use structured sections:

```python
@mcp_server.tool()
async def get_confluence_page(inputs: GetPageInput) -> PageOutput:
    """
    Retrieves a specific Confluence page with its content and metadata.
    
    **Use Cases:**
    - Get page content to read or analyze
    - Retrieve page metadata (author, version, dates)
    - Get page structure information (parent, space)
    
    **Examples:**
    - Get page by ID: `{"page_id": "123456"}`
    - Get page by space and title: `{"space_key": "DOCS", "title": "Meeting Notes"}`
    - Get page with expanded content: `{"page_id": "123456", "expand": "body.view,version,space"}`
    
    **Tips:**
    - Use page_id when you know the exact page ID (faster)
    - Use space_key + title for human-readable page identification
    - Add expand parameter to get page content in the response
    - Common expand values: 'body.view' (HTML content), 'body.storage' (raw format), 'version', 'space'
    """
```

### 2. **Rich Parameter Descriptions**

Enhance Pydantic field descriptions with examples and context:

```python
class GetPageInput(BaseModel):
    page_id: Optional[str] = Field(
        default=None, 
        description="The ID of the page to retrieve. Example: '123456789'. Use this when you know the exact page ID for fastest retrieval."
    )
    space_key: Optional[str] = Field(
        default=None, 
        description="The key of the space where the page resides (used with title). Example: 'DOCS', 'TECH', '~username'. Required when using title parameter."
    )
    expand: Optional[str] = Field(
        default=None, 
        description="Comma-separated list of properties to expand. Examples: 'body.view' (HTML content), 'body.storage' (raw XML), 'version,space,history'. Use to get page content and metadata."
    )
```

### 3. **Validation with Helpful Error Messages**

Use Pydantic validators to provide clear guidance:

```python
@model_validator(mode='after')
def check_page_id_or_space_key_and_title(cls, values):
    page_id = values.page_id
    space_key = values.space_key
    title = values.title
    if page_id is None and not (space_key and title):
        raise ValueError("Either 'page_id' or both 'space_key' and 'title' must be provided.")
    if page_id and (space_key or title):
        raise ValueError("'page_id' cannot be provided together with 'space_key' or 'title'.")
    return values
```

### 4. **Structured Documentation Sections**

Organize your docstrings with clear sections:

- **Use Cases**: When to use this tool
- **Examples**: Concrete JSON examples  
- **Tips**: Best practices and gotchas
- **Important Notes**: Warnings or limitations
- **Format Guidelines**: Expected input formats

## 🏗️ **Docstring Structure Template**

```python
@mcp_server.tool()
async def your_tool(inputs: YourInput) -> YourOutput:
    """
    Brief one-line description of what the tool does.
    
    **Use Cases:**
    - Primary use case 1
    - Primary use case 2
    - Common scenario 3
    
    **Examples:**
    - Basic usage: `{"param": "value"}`
    - Advanced usage: `{"param": "value", "optional": "setting"}`
    - Complex example: `{"param": "value", "filters": {"type": "specific"}}`
    
    **Tips:**
    - Performance tip
    - Best practice
    - Common gotcha to avoid
    
    **Important Notes:**
    - Limitation or warning
    - Side effect to be aware of
    """
```

## 📝 **Parameter Description Best Practices**

### ✅ **Good Parameter Descriptions**

```python
space_key: str = Field(
    ..., 
    description="The key of the space where the page will be created. Example: 'DOCS', 'TECH', '~username'. Required field - get available spaces using get_confluence_spaces."
)

limit: int = Field(
    default=25, 
    ge=1, 
    le=100, 
    description="Maximum number of results to return (1-100). Default: 25. Use higher values for comprehensive searches."
)
```

### ❌ **Poor Parameter Descriptions**

```python
space_key: str = Field(..., description="Space key")
limit: int = Field(default=25, description="Limit")
```

## 🎨 **Advanced Techniques**

### 1. **Context-Aware Examples**

Provide examples that show relationships between tools:

```python
"""
**Workflow Example:**
1. Get spaces: `get_confluence_spaces({"limit": 10})`
2. Create page: `{"space_key": "DOCS", "title": "New Page", "content": "<p>Content</p>"}`
3. Update page: Use page_id from step 2 with incremented version
"""
```

### 2. **Format Specifications**

Be specific about expected formats:

```python
cql: Optional[str] = Field(
    default=None, 
    description="Advanced CQL (Confluence Query Language) query. Examples: 'space = DOCS AND title ~ \"API*\"', 'created >= \"2024-01-01\"', 'creator = currentUser()'. Use for precise searches."
)
```

### 3. **Cross-Tool References**

Help users understand tool relationships:

```python
"""
**Related Tools:**
- Use `get_confluence_spaces()` to find available space keys
- Use `search_confluence_pages()` to find existing pages before creating
- Use `get_confluence_page()` to get current version before updating
"""
```

## 🚀 **Benefits of Rich Tool Descriptions**

1. **Better Tool Discovery**: Claude Desktop can suggest appropriate tools
2. **Reduced Errors**: Clear parameter formats prevent common mistakes
3. **Improved Workflows**: Examples show how tools work together
4. **Faster Adoption**: Users understand capabilities quickly
5. **Self-Documenting**: Tools become easier to maintain

## 📊 **Before vs After Example**

### Before (Basic)
```python
@mcp_server.tool()
async def search_pages(inputs: SearchInput) -> SearchOutput:
    """Search for pages."""
```

### After (Enhanced)
```python
@mcp_server.tool()
async def search_confluence_pages(inputs: SearchPagesInput) -> SearchPagesOutput:
    """
    Search for Confluence pages using text queries or advanced CQL (Confluence Query Language).
    
    **Use Cases:**
    - Find pages containing specific keywords
    - Search within a specific space
    - Use advanced queries with CQL for precise results
    
    **Examples:**
    - Simple search: `{"query": "meeting notes"}`
    - Space-specific: `{"query": "API docs", "space_key": "TECH"}`
    - Advanced CQL: `{"cql": "space = DOCS AND created >= '2024-01-01'"}`
    
    **Tips:**
    - Use 'query' for simple text searches (easier)
    - Use 'cql' for complex searches with precise criteria
    - Add 'expand' to get page content in results
    """
```

## 💡 **Key Takeaways**

1. **Be Specific**: Include concrete examples and formats
2. **Show Context**: Explain when and why to use each tool
3. **Provide Examples**: JSON examples are extremely helpful
4. **Add Tips**: Share best practices and common patterns
5. **Cross-Reference**: Show how tools work together
6. **Consider Errors**: Anticipate common mistakes and provide guidance

This approach makes your MCP tools much more discoverable and usable by AI agents like Claude Desktop! 