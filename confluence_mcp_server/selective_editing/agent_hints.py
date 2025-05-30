"""
Agent Documentation and Tool Hints for Confluence Selective Editing System

This module provides comprehensive guidance for AI agents on when and how to use
the selective editing capabilities instead of full page replacement.

The selective editing system provides three main categories of operations:
1. Section-Based Operations: Target specific sections by heading
2. Pattern-Based Operations: Find and replace text/regex patterns
3. Combined Operations: Use section targeting with pattern matching

Key Principle: Use selective editing when you want to preserve existing content
and make targeted changes, rather than rewriting entire pages.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum


class EditingScenario(Enum):
    """Common editing scenarios that benefit from selective editing."""
    
    # Section-based scenarios
    UPDATE_SECTION_CONTENT = "update_section_content"
    INSERT_NEW_SECTION = "insert_new_section"
    REPLACE_DOCUMENTATION_SECTION = "replace_documentation_section"
    UPDATE_FAQ_SECTION = "update_faq_section"
    
    # Pattern-based scenarios
    UPDATE_TERMINOLOGY = "update_terminology"
    FIX_TYPOS = "fix_typos"
    UPDATE_VERSION_NUMBERS = "update_version_numbers"
    STANDARDIZE_FORMAT = "standardize_format"
    UPDATE_LINKS = "update_links"
    
    # Combined scenarios
    UPDATE_API_DOCUMENTATION = "update_api_documentation"
    REFRESH_PRODUCT_INFO = "refresh_product_info"
    LOCALIZE_CONTENT = "localize_content"


class AgentHints:
    """
    Comprehensive guidance for AI agents using selective editing operations.
    
    This class provides decision trees, use cases, and best practices for
    choosing between different selective editing approaches.
    """
    
    @staticmethod
    def get_operation_decision_tree() -> Dict[str, Any]:
        """
        Decision tree for choosing the right selective editing operation.
        
        Returns:
            Dict mapping scenarios to recommended operations
        """
        return {
            "goal": "modify_confluence_page",
            "questions": [
                {
                    "question": "What type of change do you need to make?",
                    "options": {
                        "replace_entire_page": {
                            "recommendation": "Use full page update_page tool",
                            "reason": "Selective editing is not needed for complete rewrites"
                        },
                        "update_specific_section": {
                            "follow_up": "section_targeting_decision"
                        },
                        "find_and_replace_text": {
                            "follow_up": "pattern_matching_decision"
                        },
                        "complex_multi_part_update": {
                            "follow_up": "combined_operations_decision"
                        }
                    }
                },
                {
                    "id": "section_targeting_decision",
                    "question": "How do you want to target the section?",
                    "options": {
                        "by_heading_text": {
                            "operations": ["replace_section", "insert_after_heading", "update_section_heading"],
                            "tools": "SectionEditor",
                            "examples": [
                                "Replace content under 'Getting Started' heading",
                                "Insert new content after 'Prerequisites' section",
                                "Update 'API v1.0' heading to 'API v2.0'"
                            ]
                        },
                        "by_content_pattern": {
                            "follow_up": "pattern_matching_decision"
                        }
                    }
                },
                {
                    "id": "pattern_matching_decision", 
                    "question": "What type of pattern do you need to match?",
                    "options": {
                        "simple_text": {
                            "operation": "replace_text_pattern",
                            "tools": "PatternEditor",
                            "options": "case_sensitive, whole_words_only, max_replacements",
                            "examples": [
                                "Replace 'old_product_name' with 'new_product_name'",
                                "Update 'Version 1.0' to 'Version 2.0' (case insensitive)",
                                "Fix typo: 'recieve' → 'receive' (whole words only)"
                            ]
                        },
                        "regex_pattern": {
                            "operation": "replace_regex_pattern",
                            "tools": "PatternEditor", 
                            "options": "regex_flags, capture_groups, max_replacements",
                            "examples": [
                                "Convert dates: '2023-12-15' → '12/15/2023'",
                                "Update versions: 'v1.2.3' → 'version 1.2.3'",
                                "Standardize emails: 'Email: user@domain' → 'Contact: user@domain'"
                            ]
                        }
                    }
                },
                {
                    "id": "combined_operations_decision",
                    "question": "Do you need multiple operations?",
                    "options": {
                        "sequential_operations": {
                            "strategy": "Chain multiple operations",
                            "pattern": "operation1(content) → operation2(result1) → operation3(result2)",
                            "examples": [
                                "1. Replace 'Installation' section content, 2. Update version numbers throughout",
                                "1. Insert new 'Troubleshooting' section, 2. Fix typos in existing content"
                            ]
                        },
                        "section_specific_patterns": {
                            "strategy": "Get section content, apply patterns, replace section",
                            "pattern": "get_section → apply_patterns → replace_section",
                            "examples": [
                                "Update only API endpoints in 'Reference' section",
                                "Fix formatting only in 'Code Examples' section"
                            ]
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def get_use_case_examples() -> Dict[EditingScenario, Dict[str, Any]]:
        """
        Comprehensive examples for each editing scenario.
        
        Returns:
            Dict mapping scenarios to detailed examples with code
        """
        return {
            EditingScenario.UPDATE_SECTION_CONTENT: {
                "description": "Replace content under a specific heading while preserving page structure",
                "when_to_use": [
                    "Updating installation instructions",
                    "Refreshing API documentation sections", 
                    "Replacing outdated feature descriptions"
                ],
                "example_code": '''
# Replace the "Installation" section with new content
result = section_editor.replace_section(
    content=page_content,
    heading="Installation",
    new_content="""
    <h3>Prerequisites</h3>
    <ul>
        <li>Python 3.8 or higher</li>
        <li>pip package manager</li>
    </ul>
    <h3>Install Steps</h3>
    <ol>
        <li>Run: pip install our-package</li>
        <li>Verify: our-package --version</li>
    </ol>
    """
)
                ''',
                "preserves": ["Other sections", "Page macros", "Layout structure", "Navigation"],
                "modifies": ["Only content under 'Installation' heading"]
            },
            
            EditingScenario.UPDATE_TERMINOLOGY: {
                "description": "Find and replace terminology throughout document while preserving XML structure",
                "when_to_use": [
                    "Product rebranding (old name → new name)",
                    "API version updates (v1 → v2)",
                    "Terminology standardization"
                ],
                "example_code": '''
# Update product name throughout the document
result = pattern_editor.replace_text_pattern(
    content=page_content,
    search_pattern="OldProductName", 
    replacement="NewProductName",
    case_sensitive=False,  # Match "oldproductname", "OLDPRODUCTNAME"
    whole_words_only=True  # Don't match "OldProductNameHelper"
)
                ''',
                "preserves": ["XML tags", "Macro parameters", "Link URLs", "Code blocks"],
                "modifies": ["Only text content matching the pattern"]
            },
            
            EditingScenario.UPDATE_VERSION_NUMBERS: {
                "description": "Use regex to update version numbers with format conversion",
                "when_to_use": [
                    "Release documentation updates",
                    "API version migration guides",
                    "Changelog formatting standardization"
                ],
                "example_code": '''
# Convert version format: "v1.2.3" → "Version 1.2.3"
result = pattern_editor.replace_regex_pattern(
    content=page_content,
    regex_pattern=r"v(\d+)\.(\d+)\.(\d+)",
    replacement=r"Version \1.\2.\3",
    regex_flags=re.IGNORECASE
)
                ''',
                "preserves": ["Document structure", "Non-version text", "Formatting"],
                "modifies": ["Version number format only"]
            },
            
            EditingScenario.UPDATE_API_DOCUMENTATION: {
                "description": "Combined section and pattern operations for comprehensive API updates",
                "when_to_use": [
                    "API version upgrades",
                    "Endpoint changes with examples",
                    "Authentication method updates"
                ],
                "example_code": '''
# Step 1: Update the Authentication section
auth_result = section_editor.replace_section(
    content=page_content,
    heading="Authentication", 
    new_content="<p>New OAuth 2.0 authentication required...</p>"
)

# Step 2: Update API endpoint URLs throughout
url_result = pattern_editor.replace_regex_pattern(
    content=auth_result.modified_content,
    regex_pattern=r"https://api\.v1\.example\.com/",
    replacement="https://api.v2.example.com/"
)

# Step 3: Update response format examples
format_result = pattern_editor.replace_text_pattern(
    content=url_result.modified_content,
    search_pattern='"status": "ok"',
    replacement='"success": true'
)
                ''',
                "preserves": ["Page layout", "Navigation", "Non-API content"],
                "modifies": ["Authentication section", "API URLs", "Response examples"]
            }
        }
    
    @staticmethod
    def get_best_practices() -> Dict[str, List[str]]:
        """
        Best practices for using selective editing operations.
        
        Returns:
            Dict of categories with best practice guidelines
        """
        return {
            "before_editing": [
                "Always get the current page content first",
                "Review the page structure to identify target sections/patterns",
                "Test patterns on a small scale before applying broadly",
                "Consider the impact on macros, layouts, and links"
            ],
            
            "section_targeting": [
                "Use exact heading text for reliable section identification",
                "Check heading hierarchy (h1, h2, h3) to target the right level",
                "Use case_sensitive=False for flexible heading matching",
                "Verify section exists before attempting replacement"
            ],
            
            "pattern_matching": [
                "Use whole_words_only=True to avoid partial word matches",
                "Start with case_sensitive=False for broader matching", 
                "Use max_replacements to limit changes for testing",
                "Test regex patterns before applying to production content",
                "Use capture groups for complex pattern transformations"
            ],
            
            "error_handling": [
                "Check operation result.success before proceeding",
                "Use backup_content for rollback if needed",
                "Handle malformed XML gracefully with fallback strategies",
                "Validate modified content before saving to Confluence"
            ],
            
            "performance": [
                "Combine related pattern operations to minimize API calls",
                "Use specific targeting to avoid unnecessary content processing",
                "Consider content size when choosing between operations",
                "Cache page content when performing multiple operations"
            ]
        }
    
    @staticmethod
    def get_antipatterns() -> Dict[str, Dict[str, str]]:
        """
        Common mistakes to avoid when using selective editing.
        
        Returns:
            Dict of antipatterns with explanations and alternatives
        """
        return {
            "overuse_full_replacement": {
                "mistake": "Using update_page for small changes",
                "problem": "Overwrites entire page, loses concurrent edits, poor version history",
                "solution": "Use selective editing for targeted changes, reserve full updates for complete rewrites"
            },
            
            "incorrect_pattern_scope": {
                "mistake": "Using overly broad patterns without restrictions",
                "problem": "Unintended matches in code blocks, URLs, or macro parameters",
                "solution": "Use whole_words_only, test patterns, consider XML structure"
            },
            
            "ignoring_xml_structure": {
                "mistake": "Applying patterns that could break XML tags or attributes",
                "problem": "Corrupted page content, broken macros, invalid markup",
                "solution": "Trust the selective editing system's XML preservation, test thoroughly"
            },
            
            "sequential_dependency_errors": {
                "mistake": "Not using results from previous operations as input to next",
                "problem": "Operations work on stale content, changes not cumulative",
                "solution": "Chain operations: op2(content=op1.modified_content)"
            },
            
            "insufficient_error_checking": {
                "mistake": "Not checking result.success before proceeding",
                "problem": "Failed operations propagate errors, data loss risk",
                "solution": "Always check success, use backup_content for recovery"
            }
        }
    
    @staticmethod
    def get_operation_matrix() -> Dict[str, Dict[str, str]]:
        """
        Matrix showing when to use each operation type.
        
        Returns:
            Decision matrix for operation selection
        """
        return {
            "target_by_heading": {
                "replace_content": "replace_section() - Replace all content under heading",
                "add_content": "insert_after_heading() - Add content after heading",
                "update_heading": "update_section_heading() - Change heading text/level"
            },
            
            "target_by_text_pattern": {
                "simple_find_replace": "replace_text_pattern() - Case sensitivity, whole words",
                "regex_patterns": "replace_regex_pattern() - Advanced patterns, capture groups",
                "multiple_replacements": "Use max_replacements parameter for control"
            },
            
            "complex_scenarios": {
                "section_then_pattern": "Replace section content, then apply patterns within",
                "pattern_then_section": "Update patterns globally, then replace specific sections",
                "multiple_sections": "Sequential section operations on the same content"
            },
            
            "content_preservation": {
                "preserve_macros": "All operations automatically preserve Confluence macros",
                "preserve_layout": "XML structure and layout elements are maintained",
                "preserve_links": "Internal and external links remain functional"
            }
        }
    
    @staticmethod 
    def format_agent_prompt(scenario: EditingScenario, context: Dict[str, Any]) -> str:
        """
        Generate a formatted prompt for agents based on editing scenario.
        
        Args:
            scenario: The editing scenario
            context: Additional context (page_title, target_content, etc.)
            
        Returns:
            Formatted prompt text for the agent
        """
        examples = AgentHints.get_use_case_examples()
        best_practices = AgentHints.get_best_practices()
        
        if scenario not in examples:
            return f"Scenario {scenario} not found in examples"
        
        example = examples[scenario]
        
        prompt = f"""
# Selective Editing Guidance: {scenario.value.replace('_', ' ').title()}

## Scenario Description
{example['description']}

## When to Use This Approach
{chr(10).join('• ' + item for item in example['when_to_use'])}

## Example Implementation
```python
{example['example_code'].strip()}
```

## What This Preserves
{chr(10).join('• ' + item for item in example['preserves'])}

## What This Modifies  
{chr(10).join('• ' + item for item in example['modifies'])}

## Key Best Practices
{chr(10).join('• ' + item for item in best_practices['before_editing'][:3])}

## Context for This Operation
Page: {context.get('page_title', 'Unknown')}
Target: {context.get('target_content', 'Not specified')}
Change Type: {context.get('change_type', 'Update')}
        """
        
        return prompt.strip()


# Exported constants for easy reference
SELECTIVE_EDITING_DECISION_TREE = AgentHints.get_operation_decision_tree()
USE_CASE_EXAMPLES = AgentHints.get_use_case_examples()
BEST_PRACTICES = AgentHints.get_best_practices()
ANTIPATTERNS = AgentHints.get_antipatterns()
OPERATION_MATRIX = AgentHints.get_operation_matrix() 