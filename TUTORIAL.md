# 🎯 Confluence MCP Server v2.0 - Selective Editing Tutorial

Welcome to the revolutionary world of **surgical precision editing** for Confluence! This tutorial will guide you through using the industry's first XML-aware selective editing tools that allow AI assistants to make targeted modifications while preserving all existing content, formatting, and macros.

## 📚 **Table of Contents**

1. [Getting Started](#getting-started)
2. [Tutorial 1: Section-Based Editing](#tutorial-1-section-based-editing)
3. [Tutorial 2: Pattern-Based Text Replacement](#tutorial-2-pattern-based-text-replacement)
4. [Tutorial 3: Precision Table Editing](#tutorial-3-precision-table-editing)
5. [Advanced Workflows](#advanced-workflows)
6. [Best Practices](#best-practices)
7. [Common Scenarios](#common-scenarios)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 **Getting Started**

### **Prerequisites**
- Confluence MCP Server v2.0 installed and configured
- AI assistant with MCP support (Claude Desktop, Smithery.ai, etc.)
- Access to a Confluence Cloud instance
- Basic understanding of Confluence page structure

### **Quick Verification**
Verify you have the selective editing tools available:

**Ask your AI assistant:**
> "What tools do you have available for Confluence?"

**Expected Response:** You should see 13 tools total, including:
- `update_page_section` - Surgical section replacement
- `replace_text_pattern` - XML-aware pattern replacement  
- `update_table_cell` - Precision table cell editing

If you don't see these tools, check your deployment follows the [v2.0 setup instructions](README.md#quick-start).

---

## 📝 **Tutorial 1: Section-Based Editing**

### **Scenario: Update Project Status Without Affecting Meeting Notes**

Let's say you have a page with this structure:
```
# Project Alpha - Weekly Update

## Project Status
Last updated: Q3 2024
Current phase: Planning
Completion: 25%

## Meeting Notes  
- Discussed requirements with stakeholders
- Reviewed budget constraints
- Scheduled design review for next week

## Action Items
- [ ] Complete requirements document
- [ ] Set up development environment
```

**Goal:** Update only the "Project Status" section to reflect new progress.

### **Step 1: Traditional Approach (Don't Do This)**
❌ **Old way:** Replace entire page content
```
You: "Update the page to show we're now in development phase with 60% completion"

AI: I'll replace the entire page content...
[Risk: Overwrites meeting notes and action items]
```

### **Step 2: Revolutionary Approach (Do This)**
✅ **New way:** Surgical section replacement
```
You: "Update just the 'Project Status' section to show we're now in development phase with 60% completion"

AI: I'll update only the Project Status section while preserving all other content...
[Uses update_page_section tool]

Parameters:
- page_id: "123456"  
- heading: "Project Status"
- new_content: "Last updated: Q4 2024\nCurrent phase: Development\nCompletion: 60%"
- heading_level: 2
```

**Result:**
```
# Project Alpha - Weekly Update

## Project Status
Last updated: Q4 2024
Current phase: Development  
Completion: 60%

## Meeting Notes  
- Discussed requirements with stakeholders
- Reviewed budget constraints
- Scheduled design review for next week

## Action Items
- [ ] Complete requirements document
- [ ] Set up development environment
```

### **Advanced Section Editing Options**

#### **Exact vs Fuzzy Matching**
```
# Exact match (case-sensitive)
You: "Update the 'Project Status' section with exact matching"
AI uses: exact_match=True, case_sensitive=True

# Fuzzy match (flexible)  
You: "Update the project status section (flexible matching)"
AI uses: exact_match=False, case_sensitive=False
```

#### **Targeting Specific Heading Levels**
```
# Target only H2 headings
You: "Update the 'Status' section but only if it's a level 2 heading"
AI uses: heading_level=2

# Any heading level
You: "Find any 'Status' heading regardless of level"  
AI uses: heading_level=None
```

---

## 🔍 **Tutorial 2: Pattern-Based Text Replacement**

### **Scenario: Update Version Numbers Across Documentation**

You have multiple pages with version references like:
- "API v1.2.3 documentation"
- "Compatible with v1.2.3 and later" 
- "Download v1.2.3 from..."

**Goal:** Update all version references to v2.0.0 while preserving links, formatting, and macros.

### **Step 1: Simple Pattern Replacement**
```
You: "Replace all instances of 'v1.2.3' with 'v2.0.0' in this page"

AI: I'll find and replace that version number while preserving all formatting...
[Uses replace_text_pattern tool]

Parameters:
- page_id: "123456"
- search_text: "v1.2.3"  
- replacement_text: "v2.0.0"
- case_sensitive: False
- max_replacements: 50
```

### **Step 2: Advanced Pattern Options**

#### **Case-Sensitive Replacement**
```
You: "Replace 'API' with 'REST API' but preserve existing capitalization"

AI uses:
- search_text: "API"
- replacement_text: "REST API"  
- case_sensitive: True
```

#### **Whole Word Matching**
```
You: "Replace 'test' with 'verification' but only whole words"

AI uses:
- search_text: "test"
- replacement_text: "verification"
- whole_words: True
# This replaces "test" but not "testing" or "latest"
```

#### **Limited Replacements**
```
You: "Replace the first 3 instances of 'server' with 'cloud server'"

AI uses:
- search_text: "server"
- replacement_text: "cloud server"
- max_replacements: 3
```

### **Step 3: Pattern Replacement Best Practices**

#### **Preview Before Replace**
```
You: "How many instances of 'v1.2.3' are in this page?"

AI: Let me check the page content first...
[Uses get_confluence_page tool]
AI: I found 7 instances of 'v1.2.3' in the page. Would you like me to replace all of them?
```

#### **Smart Content Preservation**
The `replace_text_pattern` tool automatically:
- ✅ Preserves XML structure and macros
- ✅ Maintains links and formatting
- ✅ Protects Confluence-specific elements
- ✅ Prevents breaking page structure

**Example - What Gets Preserved:**
```xml
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>Version v1.2.3 is now available</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

After replacement:
```xml
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>Version v2.0.0 is now available</p>
  </ac:rich-text-body>
</ac:structured-macro>
```
*Note: Macro structure completely preserved*

---

## 📊 **Tutorial 3: Precision Table Editing**

### **Scenario: Update Project Metrics in Status Dashboard**

You have a project dashboard table:

| Project | Status | Completion | Last Updated |
|---------|--------|------------|--------------|
| Alpha   | Planning | 25% | 2024-10-15 |
| Beta    | Development | 60% | 2024-11-01 |
| Gamma   | Testing | 80% | 2024-11-15 |

**Goal:** Update Alpha project completion to 45% without affecting other data.

### **Step 1: Understanding Table Indexing**

Tables use **zero-based indexing**:
```
Table: 0 (first table on page)
Row: 0 = Header row, 1 = Alpha, 2 = Beta, 3 = Gamma  
Column: 0 = Project, 1 = Status, 2 = Completion, 3 = Last Updated
```

### **Step 2: Precision Cell Update**
```
You: "Update Alpha project completion to 45%"

AI: I'll update that specific table cell while preserving all other data...
[Uses update_table_cell tool]

Parameters:
- page_id: "123456"
- table_index: 0      # First table
- row_index: 1        # Alpha project row  
- column_index: 2     # Completion column
- new_content: "45%"
```

**Result:**
| Project | Status | Completion | Last Updated |
|---------|--------|------------|--------------|
| Alpha   | Planning | **45%** | 2024-10-15 |
| Beta    | Development | 60% | 2024-11-01 |
| Gamma   | Testing | 80% | 2024-11-15 |

*Only the target cell changed*

### **Step 3: Advanced Table Operations**

#### **Rich Content in Cells**
```
You: "Update the Alpha status to show 'In Progress' with a green checkmark"

AI uses:
- new_content: "In Progress ✅"
# or with HTML:
- new_content: "<span style='color: green;'>In Progress ✅</span>"
```

#### **Multiple Cell Updates**
```
You: "Update Alpha project: status to 'Development' and completion to '45%'"

AI: I'll make two precision updates...
[Makes two separate update_table_cell calls]
1. Row 1, Column 1: "Development"  
2. Row 1, Column 2: "45%"
```

#### **Working with Multiple Tables**
```
You: "Update the completion in the second table on this page"

AI uses:
- table_index: 1  # Second table (zero-based indexing)
```

---

## 🔗 **Advanced Workflows**

### **Workflow 1: Content Migration and Updates**

**Scenario:** Migrating content from old product names to new branding

```
You: "I need to update our documentation: replace 'OldProduct' with 'NewProduct' everywhere, but also update the Product Overview section to mention the rebrand"

AI: I'll handle this with a two-step approach:
1. First, I'll use pattern replacement for the global name change
2. Then, I'll update the Product Overview section specifically

Step 1: [Uses replace_text_pattern]
- Replaces "OldProduct" → "NewProduct" globally

Step 2: [Uses update_page_section] 
- Updates "Product Overview" section with rebrand announcement
```

### **Workflow 2: Data Synchronization**

**Scenario:** Updating metrics across multiple sections

```
You: "Our Q4 revenue was $2.5M. Update this in both the Executive Summary section and the Q4 row in the financial table"

AI: I'll update both locations with the new revenue figure:

Step 1: [Uses update_page_section]
- Updates "Executive Summary" section with Q4 revenue

Step 2: [Uses update_table_cell]  
- Updates Q4 row in financial table with $2.5M
```

### **Workflow 3: Collaborative Documentation**

**Scenario:** Team members updating different sections

```
Team Lead: "Update the project timeline section to show we're ahead of schedule"
[Uses update_page_section on "Timeline" section]

Developer: "Update the API status in the technical details table to 'Complete'"  
[Uses update_table_cell on technical status table]

Designer: "Replace all instances of 'wireframe' with 'prototype' since we've moved beyond wireframes"
[Uses replace_text_pattern]
```

**Result:** Three team members made targeted updates without conflicts!

---

## ✅ **Best Practices**

### **1. Preview Before Editing**
Always understand your content structure first:
```
You: "Show me the content structure of this page before I make changes"

AI: [Uses get_confluence_page tool]
AI: This page has:
- 4 main sections (H2 headings)
- 2 tables  
- 1 info macro
- Several bullet lists

What would you like to update?
```

### **2. Use the Right Tool for the Job**

| Scenario | Recommended Tool | Why |
|----------|------------------|-----|
| Update project status | `update_page_section` | Targets specific section |
| Fix typos across page | `replace_text_pattern` | Global text changes |  
| Update metrics in table | `update_table_cell` | Precision data updates |
| Add new content | `update_confluence_page` | Full page operations |

### **3. Backup Strategy**
Selective editing tools automatically create backups, but consider:
```
You: "Before making changes, can you show me what the current Project Status section contains?"

AI: [Retrieves and shows current content]
AI: Here's the current content. I'll automatically backup this before making changes.
```

### **4. Test with Small Changes First**
```
You: "Let's start by updating just one cell in the table to make sure this works correctly"

AI: Good approach! I'll update just the target cell first, then we can proceed with other changes.
```

### **5. Communicate Intent Clearly**
```
✅ Good: "Update the 'Project Status' section to show 60% completion"
❌ Vague: "Update the status"

✅ Good: "Replace 'v1.2.3' with 'v2.0.0' in the entire page"  
❌ Unclear: "Update the version"

✅ Good: "Update row 2, column 3 in the first table to '75%'"
❌ Ambiguous: "Update the table"
```

---

## 🎯 **Common Scenarios**

### **Scenario 1: Weekly Status Updates**
```
Page Structure:
# Team Weekly Update
## Last Week's Accomplishments
## This Week's Goals  
## Blockers and Issues
## Metrics Dashboard (table)
```

**Weekly Update Workflow:**
```
You: "Update last week's accomplishments and this week's goals, plus update our velocity in the metrics table"

AI: I'll make three targeted updates:
1. Update "Last Week's Accomplishments" section
2. Update "This Week's Goals" section  
3. Update velocity cell in metrics table

This preserves all other content including blockers and historical metrics.
```

### **Scenario 2: API Documentation Maintenance**
```
Page Structure:
# API Reference v1.2.3
## Authentication
## Endpoints
### GET /users  
### POST /users
## Error Codes (table)
```

**Version Update Workflow:**
```
You: "We've released v1.3.0 with a new DELETE /users endpoint and updated error codes"

AI: I'll handle this comprehensively:
1. Replace all "v1.2.3" references with "v1.3.0"
2. Add new DELETE /users endpoint to the Endpoints section
3. Update specific error codes in the Error Codes table

All authentication and existing endpoint documentation preserved.
```

### **Scenario 3: Project Handoff Documentation**
```
Page Structure:
# Project Handoff: Alpha
## Project Overview
## Technical Architecture  
## Known Issues (table)
## Contact Information
```

**Handoff Update Workflow:**
```
You: "Update the contact information section for the new team lead, and mark the database issue as resolved in the known issues table"

AI: I'll make these handoff updates:
1. Update "Contact Information" section with new team lead details
2. Update the specific database issue row in Known Issues table

Project overview and technical architecture remain unchanged for continuity.
```

---

## 🐛 **Troubleshooting**

### **Common Issues and Solutions**

#### **Issue: "Section not found"**
```
Error: Could not find section "Project Status"

Solutions:
1. Check exact heading text: "Project Status" vs "Project status"
2. Verify heading level: Is it H2 (##) or H3 (###)?
3. Use fuzzy matching: exact_match=False
4. Check page content first with get_confluence_page
```

#### **Issue: "Table index out of range"**
```
Error: Table index 1 not found (only 1 table on page)

Solutions:
1. Remember zero-based indexing: First table = 0
2. Count tables carefully, including hidden ones
3. Use get_confluence_page to verify table structure
```

#### **Issue: "Pattern replacement affects formatting"**
```
Issue: Text replacement broke a macro or link

Solutions:
1. This shouldn't happen with replace_text_pattern (it's XML-aware)
2. If it does, there may be malformed XML - check page structure
3. Consider using update_page_section for more complex changes
```

#### **Issue: "Changes not visible immediately"**
```
Issue: Made changes but don't see them in Confluence

Solutions:
1. Check if the operation returned success
2. Refresh the Confluence page (browser cache)
3. Verify you're looking at the correct page version
4. Check if you have edit permissions
```

### **Debugging Commands**

#### **Verify Page Structure**
```
You: "Show me the page structure and all headings on this page"

AI: [Uses get_confluence_page with expand=body.storage]
AI: Here's what I found:
- H1: Main Title
- H2: Section 1 
- H2: Section 2
- H3: Subsection 2.1
- Tables: 1 found
- Macros: 2 info boxes
```

#### **Test Pattern Matching**
```
You: "Before replacing text, show me all instances of 'v1.2.3' you can find"

AI: [Analyzes page content]
AI: Found 5 instances:
1. Line 12: "API v1.2.3 documentation"
2. Line 24: "Compatible with v1.2.3"
3. Table cell [2,1]: "v1.2.3"
...
```

#### **Verify Table Structure**  
```
You: "Show me the structure of all tables on this page"

AI: [Analyzes page content]
AI: Found 2 tables:
Table 0: 4 rows x 3 columns (Headers: Name, Status, Date)
Table 1: 6 rows x 2 columns (Headers: Item, Value)
```

---

## 🎉 **Congratulations!**

You've learned how to use the revolutionary selective editing capabilities of Confluence MCP Server v2.0! These tools enable:

- ✅ **Surgical precision editing** without affecting surrounding content
- ✅ **XML-aware intelligence** that preserves macros and formatting  
- ✅ **Collaborative workflows** where multiple people can edit different sections
- ✅ **Efficient updates** with minimal content disruption
- ✅ **Safe operations** with automatic backup and rollback capabilities

### **Next Steps**

1. **Practice with your own pages** - Start with simple section updates
2. **Explore advanced workflows** - Combine multiple selective editing operations  
3. **Share with your team** - Enable collaborative documentation workflows
4. **Provide feedback** - Help us improve these revolutionary capabilities

### **Getting Help**

- **Documentation**: [README.md](README.md) for complete feature overview
- **Release Notes**: [RELEASE_v2.0.md](RELEASE_v2.0.md) for technical details
- **Issues**: GitHub repository for bug reports and feature requests

**Welcome to the future of AI-assisted content management!** 🚀✨ 