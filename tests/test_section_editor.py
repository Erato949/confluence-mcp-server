"""
Tests for Section Editor - Phase 3 of Confluence Selective Editing System

This test suite validates the section-based editing operations that provide
surgical editing capabilities for Confluence pages.
"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

from confluence_mcp_server.selective_editing.section_editor import SectionEditor
from confluence_mcp_server.selective_editing.xml_parser import ConfluenceXMLParser
from confluence_mcp_server.selective_editing.content_analyzer import ContentStructureAnalyzer
from confluence_mcp_server.selective_editing.operations import (
    OperationType, ReplaceSectionOperation, InsertAfterHeadingOperation
)
from confluence_mcp_server.selective_editing.exceptions import (
    SectionNotFoundError, ContentStructureError
)


class TestSectionEditor:
    """Test suite for the SectionEditor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.section_editor = SectionEditor()
        
        # Sample Confluence content for testing
        self.sample_content = """
        <div>
            <h1>Introduction</h1>
            <p>This is the introduction section.</p>
            <p>It has multiple paragraphs.</p>
            
            <h2>Getting Started</h2>
            <p>This section explains how to get started.</p>
            <ul>
                <li>Step 1: Install the software</li>
                <li>Step 2: Configure settings</li>
            </ul>
            
            <h2>Advanced Topics</h2>
            <p>This section covers advanced topics.</p>
            <ac:structured-macro ac:name="info">
                <ac:parameter ac:name="title">Important Note</ac:parameter>
                <ac:rich-text-body>
                    <p>This is an important note about advanced topics.</p>
                </ac:rich-text-body>
            </ac:structured-macro>
            
            <h1>Conclusion</h1>
            <p>This is the conclusion section.</p>
        </div>
        """
        
        self.simple_content = """
        <div>
            <h1>Section One</h1>
            <p>Content of section one.</p>
            
            <h1>Section Two</h1>
            <p>Content of section two.</p>
        </div>
        """
    
    def test_section_editor_initialization(self):
        """Test that SectionEditor initializes correctly."""
        editor = SectionEditor()
        assert editor.xml_parser is not None
        assert editor.content_analyzer is not None
        assert editor._backup_content is None
        
        # Test with custom parser
        custom_parser = ConfluenceXMLParser()
        editor_with_parser = SectionEditor(custom_parser)
        assert editor_with_parser.xml_parser is custom_parser
    
    def test_replace_section_success(self):
        """Test successful section replacement."""
        new_content = "<p>This is the new content for getting started.</p><p>It replaces the old content.</p>"
        
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="Getting Started",
            new_content=new_content
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.REPLACE_SECTION
        assert result.modified_content is not None
        assert "Replaced content under heading 'Getting Started'" in result.changes_made
        assert result.backup_content == self.sample_content
        
        # Verify the content was actually replaced
        assert "This is the new content for getting started" in result.modified_content
        assert "Step 1: Install the software" not in result.modified_content  # Old content removed
        assert "This section covers advanced topics" in result.modified_content  # Other sections preserved
    
    def test_replace_section_heading_not_found(self):
        """Test section replacement when heading is not found."""
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="Nonexistent Section",
            new_content="<p>New content</p>"
        )
        
        assert result.success is False
        assert result.operation_type == OperationType.REPLACE_SECTION
        assert "Section with heading 'Nonexistent Section' not found" in result.error_message
        assert result.backup_content == self.sample_content
    
    def test_replace_section_with_heading_level_validation(self):
        """Test section replacement with heading level validation."""
        # Should succeed - correct level
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="Getting Started",
            new_content="<p>New content</p>",
            heading_level=2
        )
        assert result.success is True
        
        # Should fail - wrong level
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="Getting Started",
            new_content="<p>New content</p>",
            heading_level=1
        )
        assert result.success is False
        assert "level 2 doesn't match required level 1" in result.error_message
    
    def test_replace_section_case_sensitivity(self):
        """Test section replacement with case sensitivity options."""
        # Case insensitive (default)
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="getting started",  # lowercase
            new_content="<p>New content</p>",
            case_sensitive=False
        )
        assert result.success is True
        
        # Case sensitive - should fail
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="getting started",  # lowercase
            new_content="<p>New content</p>",
            case_sensitive=True
        )
        assert result.success is False
    
    def test_replace_section_with_confluence_macros(self):
        """Test that section replacement preserves Confluence macros in other sections."""
        result = self.section_editor.replace_section(
            content=self.sample_content,
            heading="Getting Started",
            new_content="<p>Replaced content</p>"
        )
        
        assert result.success is True
        # Verify macro is preserved in the Advanced Topics section
        assert "ac:structured-macro" in result.modified_content
        assert "Important Note" in result.modified_content
    
    def test_insert_after_heading_success(self):
        """Test successful content insertion after heading."""
        insert_content = "<p>This content is inserted after the heading.</p>"
        
        result = self.section_editor.insert_after_heading(
            content=self.simple_content,
            heading="Section One",
            insert_content=insert_content
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.INSERT_AFTER_HEADING
        assert result.modified_content is not None
        assert "Inserted content after heading 'Section One'" in result.changes_made
        assert result.backup_content == self.simple_content
        
        # Verify content was inserted
        assert "This content is inserted after the heading" in result.modified_content
        assert "Content of section one" in result.modified_content  # Original content preserved
    
    def test_insert_after_heading_not_found(self):
        """Test content insertion when heading is not found."""
        result = self.section_editor.insert_after_heading(
            content=self.simple_content,
            heading="Nonexistent Section",
            insert_content="<p>New content</p>"
        )
        
        assert result.success is False
        assert result.operation_type == OperationType.INSERT_AFTER_HEADING
        assert "Section with heading 'Nonexistent Section' not found" in result.error_message
    
    def test_update_section_heading_success(self):
        """Test successful heading update."""
        result = self.section_editor.update_section_heading(
            content=self.simple_content,
            old_heading="Section One",
            new_heading="Updated Section One"
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.UPDATE_HEADING_CONTENT
        assert result.modified_content is not None
        assert "Updated heading from 'Section One' to 'Updated Section One'" in result.changes_made
        
        # Verify heading was updated
        assert "Updated Section One" in result.modified_content
        assert "Section One" not in result.modified_content or result.modified_content.count("Section One") == 1  # Only in "Section Two"
    
    def test_update_section_heading_with_level_change(self):
        """Test heading update with level change."""
        result = self.section_editor.update_section_heading(
            content=self.simple_content,
            old_heading="Section One",
            new_heading="Updated Section",
            new_level=2
        )
        
        assert result.success is True
        assert len(result.changes_made) == 2  # Text change and level change
        assert "Updated heading from 'Section One' to 'Updated Section'" in result.changes_made
        assert "Changed heading level from 1 to 2" in result.changes_made
        
        # Verify level was changed (should be h2 instead of h1)
        assert "<h2>Updated Section</h2>" in result.modified_content
    
    def test_update_section_heading_not_found(self):
        """Test heading update when heading is not found."""
        result = self.section_editor.update_section_heading(
            content=self.simple_content,
            old_heading="Nonexistent Section",
            new_heading="New Heading"
        )
        
        assert result.success is False
        assert "Section with heading 'Nonexistent Section' not found" in result.error_message
    
    def test_execute_operation_replace_section(self):
        """Test executing a replace section operation."""
        operation = ReplaceSectionOperation(
            heading="Section One",
            new_content="<p>Replaced via operation</p>"
        )
        
        result = self.section_editor.execute_operation(operation, self.simple_content)
        
        assert result.success is True
        assert result.operation_type == OperationType.REPLACE_SECTION
        assert "Replaced via operation" in result.modified_content
    
    def test_execute_operation_insert_after_heading(self):
        """Test executing an insert after heading operation."""
        operation = InsertAfterHeadingOperation(
            heading="Section One",
            content="<p>Inserted via operation</p>"
        )
        
        result = self.section_editor.execute_operation(operation, self.simple_content)
        
        assert result.success is True
        assert result.operation_type == OperationType.INSERT_AFTER_HEADING
        assert "Inserted via operation" in result.modified_content
    
    def test_execute_operation_invalid_parameters(self):
        """Test executing operation with invalid parameters."""
        # Create operation with missing required parameter
        operation = ReplaceSectionOperation(
            heading="",  # Empty heading - should be invalid
            new_content="<p>Content</p>"
        )
        
        result = self.section_editor.execute_operation(operation, self.simple_content)
        
        assert result.success is False
        assert "Invalid operation parameters" in result.error_message
    
    def test_execute_operation_unsupported_type(self):
        """Test executing an unsupported operation type."""
        # Create a mock operation with unsupported type
        mock_operation = Mock()
        mock_operation.operation_type = OperationType.REPLACE_TEXT_PATTERN
        mock_operation.validate_parameters.return_value = True
        
        result = self.section_editor.execute_operation(mock_operation, self.simple_content)
        
        assert result.success is False
        assert "not yet implemented" in result.error_message
    
    def test_rollback_functionality(self):
        """Test the rollback functionality."""
        # Initially no backup
        assert self.section_editor.rollback() is None
        
        # Perform an operation to create backup
        self.section_editor.replace_section(
            content=self.simple_content,
            heading="Section One",
            new_content="<p>Modified content</p>"
        )
        
        # Now rollback should return the original content
        backup = self.section_editor.rollback()
        assert backup == self.simple_content
    
    def test_malformed_xml_handling(self):
        """Test handling of malformed XML content."""
        malformed_content = "<div><h1>Broken XML<p>Missing closing tags"
        
        result = self.section_editor.replace_section(
            content=malformed_content,
            heading="Broken XML",
            new_content="<p>New content</p>"
        )
        
        # Should handle gracefully - either succeed with recovery or fail with clear error
        if not result.success:
            assert "Failed to parse XML content" in result.error_message
        assert result.backup_content == malformed_content
    
    def test_empty_content_handling(self):
        """Test handling of empty or whitespace-only content."""
        empty_content = ""
        whitespace_content = "   \n\t   "
        
        for content in [empty_content, whitespace_content]:
            result = self.section_editor.replace_section(
                content=content,
                heading="Any Heading",
                new_content="<p>New content</p>"
            )
            
            # Should fail gracefully
            assert result.success is False
            assert result.backup_content == content
    
    def test_complex_confluence_content(self):
        """Test with complex Confluence content including layouts and macros."""
        complex_content = """
        <div>
            <h1>Main Section</h1>
            <ac:layout>
                <ac:layout-section ac:type="single">
                    <ac:layout-cell>
                        <p>Layout content</p>
                    </ac:layout-cell>
                </ac:layout-section>
            </ac:layout>
            
            <h2>Subsection</h2>
            <ac:structured-macro ac:name="code">
                <ac:parameter ac:name="language">python</ac:parameter>
                <ac:plain-text-body>
                    def hello_world():
                        print("Hello, World!")
                </ac:plain-text-body>
            </ac:structured-macro>
        </div>
        """
        
        result = self.section_editor.replace_section(
            content=complex_content,
            heading="Subsection",
            new_content="<p>Replaced subsection content</p>"
        )
        
        assert result.success is True
        # Verify layout is preserved
        assert "ac:layout" in result.modified_content
        assert "Layout content" in result.modified_content
        # Verify subsection was replaced
        assert "Replaced subsection content" in result.modified_content
        assert "def hello_world" not in result.modified_content  # Old code macro removed
    
    def test_nested_headings_handling(self):
        """Test handling of nested heading structures."""
        nested_content = """
        <div>
            <h1>Level 1</h1>
            <p>Level 1 content</p>
            
            <h2>Level 2A</h2>
            <p>Level 2A content</p>
            
            <h3>Level 3</h3>
            <p>Level 3 content</p>
            
            <h2>Level 2B</h2>
            <p>Level 2B content</p>
            
            <h1>Another Level 1</h1>
            <p>Another level 1 content</p>
        </div>
        """
        
        # Replace Level 2A - should only replace until Level 2B
        result = self.section_editor.replace_section(
            content=nested_content,
            heading="Level 2A",
            new_content="<p>New Level 2A content</p>"
        )
        
        assert result.success is True
        assert "New Level 2A content" in result.modified_content
        assert "<p>Level 2A content</p>" not in result.modified_content  # Original content removed
        assert "Level 3 content" not in result.modified_content  # Subsection removed
        assert "Level 2B content" in result.modified_content  # Next section preserved
        assert "Another level 1 content" in result.modified_content  # Other sections preserved


class TestSectionEditorIntegration:
    """Integration tests for SectionEditor with real XML parsing."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.section_editor = SectionEditor()
    
    def test_end_to_end_section_replacement(self):
        """Test complete end-to-end section replacement workflow."""
        original_content = """
        <div>
            <h1>Documentation</h1>
            <p>Welcome to our documentation.</p>
            
            <h2>Installation</h2>
            <p>Follow these steps to install:</p>
            <ol>
                <li>Download the package</li>
                <li>Run the installer</li>
            </ol>
            
            <h2>Configuration</h2>
            <p>Configure the application by editing config.json</p>
        </div>
        """
        
        new_installation_content = """
        <p>Updated installation instructions:</p>
        <ol>
            <li>Download from our new repository</li>
            <li>Use the automated installer</li>
            <li>Verify the installation</li>
        </ol>
        <ac:structured-macro ac:name="tip">
            <ac:rich-text-body>
                <p>Make sure to check system requirements first!</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        """
        
        # Replace the Installation section
        result = self.section_editor.replace_section(
            content=original_content,
            heading="Installation",
            new_content=new_installation_content
        )
        
        assert result.success is True
        
        # Verify the replacement worked correctly
        modified = result.modified_content
        assert "Updated installation instructions" in modified
        assert "Download from our new repository" in modified
        assert "ac:structured-macro" in modified  # Macro was preserved
        assert "Follow these steps to install" not in modified  # Old content removed
        assert "Configure the application" in modified  # Other sections preserved
        assert "Welcome to our documentation" in modified  # Other sections preserved
        
        # Verify we can parse the result
        parser = ConfluenceXMLParser()
        assert parser.parse(modified) is not None
    
    def test_multiple_operations_sequence(self):
        """Test performing multiple operations in sequence."""
        content = """
        <div>
            <h1>Guide</h1>
            <p>Original guide content</p>
            
            <h2>Step 1</h2>
            <p>Original step 1</p>
            
            <h2>Step 2</h2>
            <p>Original step 2</p>
        </div>
        """
        
        # Operation 1: Replace Step 1
        result1 = self.section_editor.replace_section(
            content=content,
            heading="Step 1",
            new_content="<p>Updated step 1 content</p>"
        )
        assert result1.success is True
        
        # Operation 2: Insert content after Guide heading
        result2 = self.section_editor.insert_after_heading(
            content=result1.modified_content,
            heading="Guide",
            insert_content="<p>This guide has been updated recently.</p>"
        )
        assert result2.success is True
        
        # Operation 3: Update Step 2 heading
        result3 = self.section_editor.update_section_heading(
            content=result2.modified_content,
            old_heading="Step 2",
            new_heading="Final Step"
        )
        assert result3.success is True
        
        # Verify all changes are present
        final_content = result3.modified_content
        assert "Updated step 1 content" in final_content
        assert "This guide has been updated recently" in final_content
        assert "Final Step" in final_content
        assert "Step 2" not in final_content or final_content.count("Step 2") == 0
        assert "Original step 1" not in final_content
        assert "Original step 2" in final_content  # Content preserved, just heading changed 