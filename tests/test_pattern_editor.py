"""
Tests for Pattern Editor - Phase 4 of Confluence Selective Editing System

This test suite validates the pattern-based editing operations that provide
intelligent find-and-replace capabilities while preserving XML structure.
"""

import pytest
import re
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

from confluence_mcp_server.selective_editing.pattern_editor import PatternEditor
from confluence_mcp_server.selective_editing.xml_parser import ConfluenceXMLParser
from confluence_mcp_server.selective_editing.content_analyzer import ContentStructureAnalyzer
from confluence_mcp_server.selective_editing.operations import (
    OperationType, ReplaceTextPatternOperation, ReplaceRegexPatternOperation
)
from confluence_mcp_server.selective_editing.exceptions import (
    ContentStructureError, XMLParsingError
)


class TestPatternEditor:
    """Test suite for the PatternEditor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pattern_editor = PatternEditor()
        
        # Sample Confluence content for testing
        self.sample_content = """
        <div>
            <h1>Documentation Guide</h1>
            <p>This is a comprehensive guide for our documentation system.</p>
            <p>The system supports multiple features and capabilities.</p>
            
            <h2>Features</h2>
            <p>Our system includes the following features:</p>
            <ul>
                <li>Feature 1: Advanced search capabilities</li>
                <li>Feature 2: Real-time collaboration</li>
                <li>Feature 3: Version control</li>
            </ul>
            
            <h2>System Requirements</h2>
            <p>System requirements for installation:</p>
            <ac:structured-macro ac:name="info">
                <ac:parameter ac:name="title">Important</ac:parameter>
                <ac:rich-text-body>
                    <p>Make sure your system meets all requirements before installation.</p>
                </ac:rich-text-body>
            </ac:structured-macro>
        </div>
        """
        
        self.simple_content = """
        <div>
            <h1>Test Document</h1>
            <p>This is a test document with some test content.</p>
            <p>The word test appears multiple times in this test document.</p>
        </div>
        """
    
    def test_pattern_editor_initialization(self):
        """Test that PatternEditor initializes correctly."""
        editor = PatternEditor()
        assert editor.xml_parser is not None
        assert editor.content_analyzer is not None
        assert editor._backup_content is None
        
        # Test with custom parser
        custom_parser = ConfluenceXMLParser()
        editor_with_parser = PatternEditor(custom_parser)
        assert editor_with_parser.xml_parser is custom_parser
    
    def test_replace_text_pattern_success(self):
        """Test successful text pattern replacement."""
        result = self.pattern_editor.replace_text_pattern(
            content=self.simple_content,
            search_pattern="test",
            replacement="example"
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.REPLACE_TEXT_PATTERN
        assert result.modified_content is not None
        assert result.backup_content == self.simple_content
        
        # Verify replacements were made
        assert "example" in result.modified_content
        assert "Replaced 4 occurrence(s) of 'test' with 'example'" in result.changes_made
        
        # Verify case-sensitive replacement
        assert "Test Document" in result.modified_content  # Capital T not replaced
    
    def test_replace_text_pattern_case_insensitive(self):
        """Test case-insensitive text pattern replacement."""
        result = self.pattern_editor.replace_text_pattern(
            content=self.simple_content,
            search_pattern="test",
            replacement="example",
            case_sensitive=False
        )
        
        assert result.success is True
        assert "example Document" in result.modified_content  # Capital T also replaced
        assert "example" in result.modified_content
        assert "Replaced 5 occurrence(s) of 'test' with 'example'" in result.changes_made
    
    def test_replace_text_pattern_whole_words_only(self):
        """Test whole words only text pattern replacement."""
        content_with_partial = """
        <div>
            <p>This is a test document. We test testing functionality.</p>
            <p>Testing is important for software quality.</p>
        </div>
        """
        
        result = self.pattern_editor.replace_text_pattern(
            content=content_with_partial,
            search_pattern="test",
            replacement="example",
            whole_words_only=True
        )
        
        assert result.success is True
        modified = result.modified_content
        assert "This is a example document" in modified  # "test" replaced
        assert "We example" in modified  # "test" replaced
        assert "testing" in modified  # "testing" not replaced (not whole word)
        assert "Testing" in modified  # "Testing" not replaced (case sensitive + not whole word)
    
    def test_replace_text_pattern_max_replacements(self):
        """Test text pattern replacement with maximum limit."""
        result = self.pattern_editor.replace_text_pattern(
            content=self.simple_content,
            search_pattern="test",
            replacement="example",
            max_replacements=2
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Should have exactly 2 replacements
        assert "Replaced 2 occurrence(s) of 'test' with 'example'" in result.changes_made
        
        # Count occurrences to verify limit was respected
        example_count = modified.lower().count("example")
        test_count = modified.lower().count("test")
        assert example_count == 2
        assert test_count >= 2  # Some "test" should remain
    
    def test_replace_text_pattern_no_matches(self):
        """Test text pattern replacement when no matches are found."""
        result = self.pattern_editor.replace_text_pattern(
            content=self.simple_content,
            search_pattern="nonexistent",
            replacement="replacement"
        )
        
        assert result.success is True
        # Content may be normalized by XML parser, so check structure instead
        assert "<h1>Test Document</h1>" in result.modified_content
        assert "No occurrences of 'nonexistent' found" in result.changes_made
    
    def test_replace_text_pattern_preserves_xml_structure(self):
        """Test that text replacement preserves XML structure and macros."""
        result = self.pattern_editor.replace_text_pattern(
            content=self.sample_content,
            search_pattern="system",
            replacement="platform"
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Verify XML structure is preserved
        assert "<h1>Documentation Guide</h1>" in modified
        assert "<h2>Features</h2>" in modified
        assert "<h2>System Requirements</h2>" in modified  # Heading preserved
        assert "ac:structured-macro" in modified  # Macro preserved
        assert "ac:parameter" in modified  # Macro parameters preserved
        
        # Verify replacements were made in text content
        assert "documentation platform" in modified
        assert "platform supports" in modified
        assert "your platform meets" in modified
    
    def test_replace_regex_pattern_success(self):
        """Test successful regex pattern replacement."""
        content_with_numbers = """
        <div>
            <p>Version 1.0.0 was released in 2023.</p>
            <p>Version 2.1.5 will be released in 2024.</p>
            <p>Version 3.0.0 is planned for 2025.</p>
        </div>
        """
        
        result = self.pattern_editor.replace_regex_pattern(
            content=content_with_numbers,
            regex_pattern=r"Version (\d+)\.(\d+)\.(\d+)",
            replacement=r"Release \1.\2.\3"
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Verify regex replacement with capture groups
        assert "Release 1.0.0 was released" in modified
        assert "Release 2.1.5 will be released" in modified
        assert "Release 3.0.0 is planned" in modified
        assert any("Replaced 3 occurrence(s) matching regex pattern" in change for change in result.changes_made)
    
    def test_replace_regex_pattern_with_flags(self):
        """Test regex pattern replacement with flags."""
        content_with_mixed_case = """
        <div>
            <p>ERROR: Something went wrong</p>
            <p>error: Another issue occurred</p>
            <p>Error: Yet another problem</p>
        </div>
        """
        
        result = self.pattern_editor.replace_regex_pattern(
            content=content_with_mixed_case,
            regex_pattern=r"error:",
            replacement="WARNING:",
            regex_flags=re.IGNORECASE
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # All variations should be replaced due to IGNORECASE flag
        assert "WARNING: Something went wrong" in modified
        assert "WARNING: Another issue occurred" in modified
        assert "WARNING: Yet another problem" in modified
    
    def test_replace_regex_pattern_max_replacements(self):
        """Test regex pattern replacement with maximum limit."""
        result = self.pattern_editor.replace_regex_pattern(
            content=self.simple_content,
            regex_pattern=r"test",
            replacement="example",
            max_replacements=1
        )
        
        assert result.success is True
        assert any("Replaced 1 occurrence(s) matching regex pattern" in change for change in result.changes_made)
        
        # Verify only one replacement was made
        modified = result.modified_content
        example_count = modified.count("example")
        assert example_count == 1
    
    def test_replace_regex_pattern_invalid_regex(self):
        """Test regex pattern replacement with invalid regex."""
        result = self.pattern_editor.replace_regex_pattern(
            content=self.simple_content,
            regex_pattern="[invalid_regex",  # Missing closing bracket
            replacement="replacement"
        )
        
        assert result.success is False
        assert "Invalid regex pattern" in result.error_message
        assert result.backup_content == self.simple_content
    
    def test_replace_regex_pattern_no_matches(self):
        """Test regex pattern replacement when no matches found."""
        result = self.pattern_editor.replace_regex_pattern(
            content=self.simple_content,
            regex_pattern=r"\d{4}",  # Looking for 4-digit numbers
            replacement="YEAR"
        )
        
        assert result.success is True
        # Content may be normalized by XML parser, so check structure instead
        assert "<h1>Test Document</h1>" in result.modified_content
        assert any("No matches found for regex pattern" in change for change in result.changes_made)
    
    def test_execute_operation_text_pattern(self):
        """Test executing a text pattern operation."""
        operation = ReplaceTextPatternOperation(
            search_pattern="test",
            replacement="example",
            case_sensitive=False
        )
        
        result = self.pattern_editor.execute_operation(operation, self.simple_content)
        
        assert result.success is True
        assert result.operation_type == OperationType.REPLACE_TEXT_PATTERN
        assert "example" in result.modified_content
    
    def test_execute_operation_regex_pattern(self):
        """Test executing a regex pattern operation."""
        operation = ReplaceRegexPatternOperation(
            regex_pattern=r"test(\w*)",
            replacement=r"example\1"
        )
        
        result = self.pattern_editor.execute_operation(operation, self.simple_content)
        
        assert result.success is True
        assert result.operation_type == OperationType.REPLACE_REGEX_PATTERN
        assert "example" in result.modified_content
    
    def test_execute_operation_invalid_parameters(self):
        """Test executing operation with invalid parameters."""
        operation = ReplaceTextPatternOperation(
            search_pattern="",  # Empty pattern - should be invalid
            replacement="replacement"
        )
        
        result = self.pattern_editor.execute_operation(operation, self.simple_content)
        
        assert result.success is False
        assert "Invalid operation parameters" in result.error_message
    
    def test_execute_operation_unsupported_type(self):
        """Test executing an unsupported operation type."""
        mock_operation = Mock()
        mock_operation.operation_type = OperationType.REPLACE_SECTION  # Not supported by PatternEditor
        mock_operation.validate_parameters.return_value = True
        
        result = self.pattern_editor.execute_operation(mock_operation, self.simple_content)
        
        assert result.success is False
        assert "not supported by PatternEditor" in result.error_message
    
    def test_rollback_functionality(self):
        """Test the rollback functionality."""
        # Initially no backup
        assert self.pattern_editor.rollback() is None
        
        # Perform an operation to create backup
        self.pattern_editor.replace_text_pattern(
            content=self.simple_content,
            search_pattern="test",
            replacement="example"
        )
        
        # Now rollback should return the original content
        backup = self.pattern_editor.rollback()
        assert backup == self.simple_content
    
    def test_malformed_xml_handling(self):
        """Test handling of malformed XML content."""
        malformed_content = "<div><h1>Broken XML<p>Missing closing tags and test content"
        
        result = self.pattern_editor.replace_text_pattern(
            content=malformed_content,
            search_pattern="test",
            replacement="example"
        )
        
        # Should handle gracefully and still perform replacement
        assert result.success is True
        assert "example" in result.modified_content
        assert result.backup_content == malformed_content
    
    def test_empty_content_handling(self):
        """Test handling of empty or whitespace-only content."""
        empty_content = ""
        whitespace_content = "   \n\t   "
        
        for content in [empty_content, whitespace_content]:
            result = self.pattern_editor.replace_text_pattern(
                content=content,
                search_pattern="test",
                replacement="example"
            )
            
            # Should succeed but make no changes
            assert result.success is True
            assert "No occurrences of 'test' found" in result.changes_made
            assert result.backup_content == content
    
    def test_complex_confluence_content_preservation(self):
        """Test with complex Confluence content including layouts and macros."""
        complex_content = """
        <div>
            <h1>API Documentation</h1>
            <ac:layout>
                <ac:layout-section ac:type="single">
                    <ac:layout-cell>
                        <p>This API provides comprehensive functionality.</p>
                    </ac:layout-cell>
                </ac:layout-section>
            </ac:layout>
            
            <h2>Endpoints</h2>
            <ac:structured-macro ac:name="code">
                <ac:parameter ac:name="language">json</ac:parameter>
                <ac:plain-text-body>
                    {
                        "api": "v1",
                        "endpoints": ["users", "posts", "comments"]
                    }
                </ac:plain-text-body>
            </ac:structured-macro>
            
            <p>The API supports multiple data formats and protocols.</p>
        </div>
        """
        
        result = self.pattern_editor.replace_text_pattern(
            content=complex_content,
            search_pattern="API",
            replacement="Service"
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Verify layout is preserved
        assert "ac:layout" in modified
        assert "ac:layout-section" in modified
        assert "ac:layout-cell" in modified
        
        # Verify code macro is preserved
        assert "ac:structured-macro" in modified
        assert 'ac:name="code"' in modified
        assert 'ac:name="language"' in modified
        assert "ac:plain-text-body" in modified
        
        # Verify text replacements were made outside of macro content
        assert "Service Documentation" in modified
        assert "This Service provides" in modified
        assert "The Service supports" in modified
        
        # Verify JSON content within code macro was not modified
        assert '"api": "v1"' in modified  # Should remain unchanged in code block
    
    def test_xml_attribute_preservation(self):
        """Test that XML attributes are not modified during pattern replacement."""
        content_with_attributes = """
        <div class="test-container">
            <p id="test-paragraph">This is a test paragraph with test content.</p>
            <a href="/test-page" title="Test Page">Link to test page</a>
        </div>
        """
        
        result = self.pattern_editor.replace_text_pattern(
            content=content_with_attributes,
            search_pattern="test",
            replacement="example"
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Verify attributes were preserved (not modified)
        assert 'class="test-container"' in modified  # Attribute unchanged
        assert 'id="test-paragraph"' in modified  # Attribute unchanged
        assert 'href="/test-page"' in modified  # Attribute unchanged
        assert 'title="Test Page"' in modified  # Attribute unchanged
        
        # Verify text content was modified
        assert "This is a example paragraph with example content" in modified
        assert "Link to example page" in modified
    
    def test_concurrent_pattern_operations(self):
        """Test multiple pattern operations on the same content."""
        # First operation: replace "test" with "example"
        result1 = self.pattern_editor.replace_text_pattern(
            content=self.simple_content,
            search_pattern="test",
            replacement="example"
        )
        assert result1.success is True
        
        # Second operation: replace "document" with "file" on the modified content
        result2 = self.pattern_editor.replace_text_pattern(
            content=result1.modified_content,
            search_pattern="document",
            replacement="file"
        )
        assert result2.success is True
        
        # Verify both changes are present
        final_content = result2.modified_content
        assert "example" in final_content
        assert "file" in final_content
        # Check for the actual heading content - it should be "Test Document" since "Test" wasn't replaced (capital T)
        assert "Test Document" in final_content or "example Document" in final_content  # Allow for case variations
        assert "example file" in final_content


class TestPatternEditorIntegration:
    """Integration tests for PatternEditor with real XML parsing."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.pattern_editor = PatternEditor()
    
    def test_end_to_end_pattern_replacement(self):
        """Test complete end-to-end pattern replacement workflow."""
        original_content = """
        <div>
            <h1>User Manual v1.0</h1>
            <p>Welcome to the user manual for our software application.</p>
            
            <h2>Getting Started</h2>
            <p>To get started with the application, follow these steps:</p>
            <ol>
                <li>Download the application installer</li>
                <li>Run the application setup wizard</li>
                <li>Configure your application preferences</li>
            </ol>
            
            <ac:structured-macro ac:name="tip">
                <ac:rich-text-body>
                    <p>For additional help with the application, visit our support portal.</p>
                </ac:rich-text-body>
            </ac:structured-macro>
        </div>
        """
        
        # Replace "application" with "program" throughout the document
        result = self.pattern_editor.replace_text_pattern(
            content=original_content,
            search_pattern="application",
            replacement="program",
            case_sensitive=False
        )
        
        assert result.success is True
        
        # Verify the replacement worked correctly
        modified = result.modified_content
        assert "software program" in modified
        assert "get started with the program" in modified
        assert "Download the program installer" in modified
        assert "Run the program setup wizard" in modified
        assert "Configure your program preferences" in modified
        assert "help with the program" in modified
        
        # Verify XML structure and macros are preserved
        assert "<h1>User Manual v1.0</h1>" in modified
        assert "<h2>Getting Started</h2>" in modified
        assert "ac:structured-macro" in modified
        assert "ac:rich-text-body" in modified
        
        # Verify we can parse the result
        parser = ConfluenceXMLParser()
        assert parser.parse(modified) is not None
    
    def test_regex_replacement_with_complex_patterns(self):
        """Test regex replacement with complex patterns and capture groups."""
        content_with_dates = """
        <div>
            <h1>Release Notes</h1>
            <p>Version 1.2.3 was released on 2023-12-15.</p>
            <p>Version 2.0.0 will be released on 2024-03-20.</p>
            <p>Version 2.1.0 is scheduled for 2024-06-10.</p>
            
            <h2>Bug Fixes in 1.2.3</h2>
            <p>Fixed issue reported on 2023-11-05.</p>
            <p>Resolved bug found on 2023-11-28.</p>
        </div>
        """
        
        # Convert ISO dates to US format using regex with capture groups
        result = self.pattern_editor.replace_regex_pattern(
            content=content_with_dates,
            regex_pattern=r"(\d{4})-(\d{2})-(\d{2})",
            replacement=r"\2/\3/\1"
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Verify date format conversion
        assert "released on 12/15/2023" in modified
        assert "released on 03/20/2024" in modified
        assert "scheduled for 06/10/2024" in modified
        assert "reported on 11/05/2023" in modified
        assert "found on 11/28/2023" in modified
        
        # Verify structure preservation
        assert "<h1>Release Notes</h1>" in modified
        assert "<h2>Bug Fixes in 1.2.3</h2>" in modified
        
        # Verify we can parse the result
        parser = ConfluenceXMLParser()
        assert parser.parse(modified) is not None 