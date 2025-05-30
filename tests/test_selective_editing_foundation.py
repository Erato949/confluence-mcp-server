"""
Tests for Confluence Selective Editing Foundation Components

This module tests the foundational components of the selective editing system
including the XML parser, operations, and exception handling.
"""

import pytest
import xml.etree.ElementTree as ET
from typing import List

from confluence_mcp_server.selective_editing.exceptions import (
    EditingError, XMLParsingError, ContentStructureError, SectionNotFoundError
)
from confluence_mcp_server.selective_editing.operations import (
    OperationType, AppendToEndOperation, PrependToBeginningOperation,
    ReplaceSectionOperation, create_operation
)
from confluence_mcp_server.selective_editing.xml_parser import ConfluenceXMLParser
from confluence_mcp_server.selective_editing.content_analyzer import (
    ContentStructureAnalyzer, ContentStructure, ContentBlockType
)


class TestEditingExceptions:
    """Test the custom exception classes."""
    
    def test_editing_error_basic(self):
        """Test basic EditingError functionality."""
        error = EditingError("Test error message")
        assert str(error) == "Test error message"
        assert error.operation is None
        assert error.details == {}
        
    def test_editing_error_with_operation(self):
        """Test EditingError with operation context."""
        error = EditingError("Test error", operation="TEST_OP")
        assert str(error) == "[TEST_OP] Test error"
        assert error.operation == "TEST_OP"
        
    def test_xml_parsing_error(self):
        """Test XMLParsingError with XML content."""
        xml_content = "<invalid><xml></invalid>"
        error = XMLParsingError("Parsing failed", xml_content=xml_content)
        assert "Parsing failed" in str(error)
        assert error.xml_content == xml_content
        assert error.operation == "XML_PARSING"
        
    def test_section_not_found_error(self):
        """Test SectionNotFoundError formatting."""
        error = SectionNotFoundError("My Heading", "heading")
        assert "Section not found: My Heading" in str(error)
        assert error.section_identifier == "My Heading"
        assert error.search_type == "heading"


class TestSelectiveEditOperations:
    """Test the operation classes and factory."""
    
    def test_append_to_end_operation(self):
        """Test AppendToEndOperation creation and validation."""
        op = AppendToEndOperation(content="New content")
        assert op.operation_type == OperationType.APPEND_TO_END
        assert op.validate_parameters() is True
        assert "content" in op.get_required_parameters()
        assert "separator" in op.get_optional_parameters()
        
    def test_append_to_end_operation_invalid(self):
        """Test AppendToEndOperation with invalid parameters."""
        op = AppendToEndOperation(content="")
        assert op.validate_parameters() is False
        
    def test_prepend_to_beginning_operation(self):
        """Test PrependToBeginningOperation creation and validation."""
        op = PrependToBeginningOperation(content="Header content")
        assert op.operation_type == OperationType.PREPEND_TO_BEGINNING
        assert op.validate_parameters() is True
        
    def test_replace_section_operation(self):
        """Test ReplaceSectionOperation creation and validation."""
        op = ReplaceSectionOperation(heading="Introduction", new_content="New intro")
        assert op.operation_type == OperationType.REPLACE_SECTION
        assert op.validate_parameters() is True
        assert "heading" in op.get_required_parameters()
        assert "new_content" in op.get_required_parameters()
        assert "heading_level" in op.get_optional_parameters()
        
    def test_operation_factory(self):
        """Test the operation factory function."""
        op = create_operation("append_to_end", content="Test content")
        assert isinstance(op, AppendToEndOperation)
        assert op.parameters["content"] == "Test content"
        
    def test_operation_factory_invalid(self):
        """Test operation factory with invalid operation type."""
        with pytest.raises(ValueError, match="Unknown operation type"):
            create_operation("invalid_operation", content="test")
            
    def test_operation_string_representation(self):
        """Test operation string representation."""
        op = AppendToEndOperation(content="Test", separator="\n")
        str_repr = str(op)
        assert "append_to_end" in str_repr
        assert "content=Test" in str_repr
        assert "separator=" in str_repr  # Just check that separator is present


class TestConfluenceXMLParser:
    """Test the XML parser for Confluence Storage Format."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ConfluenceXMLParser()
        
    def test_parse_simple_html(self):
        """Test parsing simple HTML content."""
        content = "<p>Hello world</p>"
        root = self.parser.parse(content)
        assert root is not None
        # Single element gets parsed as-is, not wrapped
        if root.tag == "p":
            # Direct parsing without wrapper
            assert root.text == "Hello world"
        else:
            # Wrapped in root element
            assert root.tag == "root"
            p_element = root.find("p")
            assert p_element is not None
            assert p_element.text == "Hello world"
        
    def test_parse_confluence_macro(self):
        """Test parsing Confluence macro content."""
        content = '''<ac:structured-macro ac:name="info">
            <ac:parameter ac:name="title">Information</ac:parameter>
            <ac:rich-text-body>
                <p>This is important information.</p>
            </ac:rich-text-body>
        </ac:structured-macro>'''
        
        root = self.parser.parse(content)
        assert root is not None
        
        # Find the macro - look for elements containing "structured-macro" in the tag name
        # because namespaces might convert the tag to full URI
        macro = None
        for elem in root.iter():
            if "structured-macro" in elem.tag:
                macro = elem
                break
                
        assert macro is not None
        
        # Find parameter
        param = None
        for elem in root.iter():
            if "parameter" in elem.tag:
                # Check for title parameter with different possible attribute formats
                if (elem.get("ac:name") == "title" or 
                    elem.get("name") == "title" or
                    any("name" in attr and elem.get(attr) == "title" for attr in elem.attrib)):
                    param = elem
                    break
        
        assert param is not None
        
    def test_parse_mixed_content(self):
        """Test parsing mixed HTML and Confluence content."""
        content = '''<h1>My Page</h1>
        <p>Introduction paragraph</p>
        <ac:structured-macro ac:name="toc">
            <ac:parameter ac:name="maxLevel">3</ac:parameter>
        </ac:structured-macro>
        <h2>Section 1</h2>
        <p>Section content</p>'''
        
        root = self.parser.parse(content)
        assert root is not None
        
        # Check structure
        headings = self.parser.find_elements_by_tag("h1", root)
        assert len(headings) >= 1
        
        macros = []
        for elem in root.iter():
            if "structured-macro" in elem.tag:
                macros.append(elem)
        assert len(macros) == 1
        
        # Check attributes with namespace-aware access
        macro = macros[0]
        name_attr = (macro.get("ac:name") or 
                    macro.get("name") or 
                    macro.get("{http://www.atlassian.com/schema/confluence/4/ac/}name"))
        assert name_attr == "toc"
        
    def test_parse_malformed_xml_recovery(self):
        """Test recovery from malformed XML."""
        content = '<p>Unclosed paragraph<br>Line break<img src="test.jpg">Unclosed img'
        root = self.parser.parse(content)
        assert root is not None
        # Should recover using text fallback
        assert root.get("data-parse-method") == "text-fallback"
        # Should contain the original content as text
        assert content in root.text
        
    def test_parse_empty_content(self):
        """Test parsing empty content."""
        with pytest.raises(XMLParsingError, match="Empty or whitespace-only content"):
            self.parser.parse("")
            
    def test_to_string_conversion(self):
        """Test converting parsed content back to string."""
        content = "<p>Hello world</p><h1>Title</h1>"
        root = self.parser.parse(content)
        
        # Convert back to string
        result = self.parser.to_string(root, include_root=False)
        # Should contain the original elements
        assert "<p>Hello world</p>" in result
        assert "<h1>Title</h1>" in result
        
    def test_find_elements_by_tag(self):
        """Test finding elements by tag name."""
        content = "<h1>Title 1</h1><p>Content</p><h1>Title 2</h1>"
        root = self.parser.parse(content)
        
        headings = self.parser.find_elements_by_tag("h1", root)
        assert len(headings) == 2
        assert headings[0].text == "Title 1"
        assert headings[1].text == "Title 2"
        
    def test_find_elements_by_attribute(self):
        """Test finding elements by attribute value."""
        content = '''<div class="info">Info 1</div>
                     <div class="warning">Warning</div>
                     <div class="info">Info 2</div>'''
        root = self.parser.parse(content)
        
        info_divs = self.parser.find_elements_by_attribute("class", "info", root)
        assert len(info_divs) == 2
        
    def test_confluence_element_detection(self):
        """Test detection of Confluence-specific elements."""
        macro_content = '<ac:structured-macro ac:name="test"/>'
        layout_content = '<ac:layout><ac:layout-section/></ac:layout>'
        
        # Parse macro
        root1 = self.parser.parse(macro_content)
        macro_elem = None
        for elem in root1.iter():
            if "structured-macro" in elem.tag:
                macro_elem = elem
                break
        assert macro_elem is not None
        
        # Parse layout
        root2 = self.parser.parse(layout_content)
        layout_elem = None
        for elem in root2.iter():
            if "layout" in elem.tag and elem.tag != "root":  # Avoid matching our wrapper
                layout_elem = elem
                break
        assert layout_elem is not None
        
    def test_error_collection(self):
        """Test that parse errors are collected."""
        # This should trigger some warnings
        very_deep_content = "<div>" * 25 + "content" + "</div>" * 25
        root = self.parser.parse(very_deep_content)
        
        errors = self.parser.get_parse_errors()
        assert self.parser.has_parse_errors() is True
        assert any("deep nesting" in error for error in errors)


class TestSelectiveEditingIntegration:
    """Integration tests for selective editing components."""
    
    def test_basic_workflow(self):
        """Test a basic workflow using multiple components."""
        # Create an operation
        operation = create_operation("append_to_end", content="New content")
        assert operation.validate_parameters() is True
        
        # Parse some content  
        parser = ConfluenceXMLParser()
        original_content = "<p>Existing content</p>"
        root = parser.parse(original_content)
        
        # Verify structure
        assert root is not None
        paragraphs = parser.find_elements_by_tag("p", root)
        assert len(paragraphs) == 1
        assert paragraphs[0].text == "Existing content"
        
    def test_complex_confluence_content(self):
        """Test with complex Confluence content including macros and layouts."""
        content = '''
        <h1>Project Documentation</h1>
        <ac:structured-macro ac:name="toc" ac:schema-version="1">
            <ac:parameter ac:name="maxLevel">2</ac:parameter>
        </ac:structured-macro>
        
        <h2>Overview</h2>
        <p>This project provides...</p>
        
        <ac:layout>
            <ac:layout-section ac:type="single">
                <ac:layout-cell>
                    <p>Layout content here</p>
                </ac:layout-cell>
            </ac:layout-section>
        </ac:layout>
        '''
        
        parser = ConfluenceXMLParser()
        root = parser.parse(content)
        
        # Verify we can parse complex structure
        assert root is not None
        
        # Check that macros are preserved
        macros = []
        for elem in root.iter():
            if "structured-macro" in elem.tag:
                macros.append(elem)
        assert len(macros) == 1
        
        # Check attributes with namespace-aware access
        macro = macros[0]
        name_attr = (macro.get("ac:name") or 
                    macro.get("name") or 
                    macro.get("{http://www.atlassian.com/schema/confluence/4/ac/}name"))
        assert name_attr == "toc"
        
        # Check that layouts are preserved
        layouts = []
        for elem in root.iter():
            if "layout" in elem.tag and elem.tag != "root":  # Avoid matching our wrapper
                layouts.append(elem)
        assert len(layouts) >= 1
        
        # Convert back to string
        result = parser.to_string(root, include_root=False)
        assert "ac:structured-macro" in result
        assert "ac:layout" in result 