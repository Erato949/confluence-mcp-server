"""
Tests for Confluence Content Structure Analyzer

This module tests the ContentStructureAnalyzer class and its ability to analyze
Confluence page structure for intelligent selective editing operations.
"""

import pytest
import xml.etree.ElementTree as ET
from typing import List

from confluence_mcp_server.selective_editing.content_analyzer import (
    ContentStructureAnalyzer, ContentStructure, HeadingInfo, SectionInfo,
    ContentBlock, ContentBlockType, InsertionPoint
)
from confluence_mcp_server.selective_editing.xml_parser import ConfluenceXMLParser
from confluence_mcp_server.selective_editing.exceptions import ContentStructureError


class TestContentStructureAnalyzer:
    """Test the content structure analyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ContentStructureAnalyzer()
        
    def test_analyze_simple_content(self):
        """Test analysis of simple content with headings and paragraphs."""
        content = """
        <h1>Introduction</h1>
        <p>This is the introduction paragraph.</p>
        <h2>Overview</h2>
        <p>This is the overview section.</p>
        <h2>Details</h2>
        <p>This section contains details.</p>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Check headings
        assert len(structure.headings) == 3
        assert structure.headings[0].level == 1
        assert structure.headings[0].text == "Introduction"
        assert structure.headings[1].level == 2
        assert structure.headings[1].text == "Overview"
        assert structure.headings[2].level == 2
        assert structure.headings[2].text == "Details"
        
        # Check sections
        assert len(structure.sections) == 3
        
        # Check content blocks
        assert len(structure.content_blocks) > 0
        
        # Check insertion points
        assert len(structure.insertion_points) > 0
        
    def test_find_headings(self):
        """Test heading detection functionality."""
        content = """
        <h1>Main Title</h1>
        <h2>Section 1</h2>
        <p>Content here</p>
        <h3>Subsection 1.1</h3>
        <p>More content</p>
        <h2>Section 2</h2>
        """
        
        structure = self.analyzer.analyze(content)
        headings = structure.headings
        
        assert len(headings) == 4
        
        # Check heading levels and text
        assert headings[0].level == 1 and headings[0].text == "Main Title"
        assert headings[1].level == 2 and headings[1].text == "Section 1"
        assert headings[2].level == 3 and headings[2].text == "Subsection 1.1"
        assert headings[3].level == 2 and headings[3].text == "Section 2"
        
        # Check positions are in order
        positions = [h.position for h in headings]
        assert positions == sorted(positions)
        
    def test_find_sections(self):
        """Test section identification based on headings."""
        content = """
        <h1>Chapter 1</h1>
        <p>Chapter 1 content</p>
        <h2>Section 1.1</h2>
        <p>Section 1.1 content</p>
        <h2>Section 1.2</h2>
        <p>Section 1.2 content</p>
        <h1>Chapter 2</h1>
        <p>Chapter 2 content</p>
        """
        
        structure = self.analyzer.analyze(content)
        sections = structure.sections
        
        assert len(sections) == 4
        
        # Check section hierarchy
        chapter1 = sections[0]
        assert chapter1.heading.text == "Chapter 1"
        assert chapter1.heading.level == 1
        
        section11 = sections[1]
        assert section11.heading.text == "Section 1.1"
        assert section11.heading.level == 2
        
        section12 = sections[2]
        assert section12.heading.text == "Section 1.2"
        assert section12.heading.level == 2
        
        chapter2 = sections[3]
        assert chapter2.heading.text == "Chapter 2"
        assert chapter2.heading.level == 1
        
    def test_content_block_classification(self):
        """Test classification of different content block types."""
        content = """
        <h1>Title</h1>
        <p>Paragraph content</p>
        <table>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <ac:structured-macro ac:name="info">
            <ac:rich-text-body>
                <p>Macro content</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        """
        
        structure = self.analyzer.analyze(content)
        blocks = structure.content_blocks
        
        # Find blocks by type
        heading_blocks = [b for b in blocks if b.block_type == ContentBlockType.HEADING]
        paragraph_blocks = [b for b in blocks if b.block_type == ContentBlockType.PARAGRAPH]
        table_blocks = [b for b in blocks if b.block_type == ContentBlockType.TABLE]
        list_blocks = [b for b in blocks if b.block_type == ContentBlockType.LIST]
        macro_blocks = [b for b in blocks if b.block_type == ContentBlockType.MACRO]
        
        assert len(heading_blocks) >= 1
        assert len(paragraph_blocks) >= 1
        assert len(table_blocks) >= 1
        assert len(list_blocks) >= 1
        assert len(macro_blocks) >= 1
        
    def test_insertion_points(self):
        """Test identification of safe insertion points."""
        content = """
        <h1>Introduction</h1>
        <p>Introduction content</p>
        <h2>Section 1</h2>
        <p>Section 1 content</p>
        """
        
        structure = self.analyzer.analyze(content)
        insertion_points = structure.insertion_points
        
        # Should have multiple insertion points
        assert len(insertion_points) > 0
        
        # Check for expected types
        point_types = [p.location_type for p in insertion_points]
        assert "start_of_page" in point_types
        assert "after_heading" in point_types
        assert "end_of_section" in point_types
        assert "end_of_page" in point_types
        
        # Check positions are in order
        positions = [p.position for p in insertion_points]
        assert positions == sorted(positions)
        
    def test_heading_hierarchy(self):
        """Test building of heading hierarchy structure."""
        content = """
        <h1>Chapter 1</h1>
        <h2>Section 1.1</h2>
        <h3>Subsection 1.1.1</h3>
        <h3>Subsection 1.1.2</h3>
        <h2>Section 1.2</h2>
        <h1>Chapter 2</h1>
        """
        
        structure = self.analyzer.analyze(content)
        hierarchy = structure.heading_hierarchy
        
        assert "levels" in hierarchy
        assert "structure" in hierarchy
        assert "max_level" in hierarchy
        assert "min_level" in hierarchy
        
        # Check level counts
        assert 1 in hierarchy["levels"]
        assert 2 in hierarchy["levels"]
        assert 3 in hierarchy["levels"]
        
        assert len(hierarchy["levels"][1]) == 2  # 2 H1 headings
        assert len(hierarchy["levels"][2]) == 2  # 2 H2 headings
        assert len(hierarchy["levels"][3]) == 2  # 2 H3 headings
        
        # Check min/max levels
        assert hierarchy["min_level"] == 1
        assert hierarchy["max_level"] == 3
        
        # Check nested structure
        nested = hierarchy["structure"]
        assert len(nested) == 2  # 2 top-level chapters
        
        chapter1 = nested[0]
        assert chapter1["text"] == "Chapter 1"
        assert chapter1["level"] == 1
        assert len(chapter1["children"]) == 2  # 2 sections
        
        section11 = chapter1["children"][0]
        assert section11["text"] == "Section 1.1"
        assert section11["level"] == 2
        assert len(section11["children"]) == 2  # 2 subsections
        
    def test_find_section_by_heading(self):
        """Test finding sections by heading text."""
        content = """
        <h1>Introduction</h1>
        <p>Intro content</p>
        <h2>Overview</h2>
        <p>Overview content</p>
        <h2>Details</h2>
        <p>Details content</p>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Test exact match
        section = structure.get_section_by_heading("Overview")
        assert section is not None
        assert section.heading.text == "Overview"
        assert section.heading.level == 2
        
        # Test case insensitive
        section = structure.get_section_by_heading("OVERVIEW", case_sensitive=False)
        assert section is not None
        assert section.heading.text == "Overview"
        
        # Test not found
        section = structure.get_section_by_heading("Nonexistent")
        assert section is None
        
    def test_confluence_macro_detection(self):
        """Test detection of Confluence macros."""
        content = """
        <h1>Page with Macros</h1>
        <ac:structured-macro ac:name="info">
            <ac:parameter ac:name="title">Information</ac:parameter>
            <ac:rich-text-body>
                <p>This is an info macro</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        <p>Regular paragraph</p>
        <ac:structured-macro ac:name="toc">
            <ac:parameter ac:name="maxLevel">3</ac:parameter>
        </ac:structured-macro>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Check macro detection
        assert structure.has_macros is True
        
        # Find macro blocks
        macro_blocks = [b for b in structure.content_blocks if b.block_type == ContentBlockType.MACRO]
        assert len(macro_blocks) >= 1
        
        # Check macro metadata
        for block in macro_blocks:
            if "macro_name" in block.metadata:
                assert block.metadata["macro_name"] in ["info", "toc"]
                
    def test_confluence_layout_detection(self):
        """Test detection of Confluence layouts."""
        content = """
        <h1>Page with Layout</h1>
        <ac:layout>
            <ac:layout-section ac:type="single">
                <ac:layout-cell>
                    <p>Layout content here</p>
                </ac:layout-cell>
            </ac:layout-section>
        </ac:layout>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Check layout detection
        assert structure.has_layouts is True
        
        # Find layout blocks
        layout_blocks = [b for b in structure.content_blocks if b.block_type == ContentBlockType.LAYOUT]
        assert len(layout_blocks) >= 1
        
    def test_table_analysis(self):
        """Test analysis of table structures."""
        content = """
        <h1>Table Example</h1>
        <table>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
                <th>Header 3</th>
            </tr>
            <tr>
                <td>Cell 1</td>
                <td>Cell 2</td>
                <td>Cell 3</td>
            </tr>
            <tr>
                <td>Cell 4</td>
                <td>Cell 5</td>
                <td>Cell 6</td>
            </tr>
        </table>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Find table blocks
        table_blocks = [b for b in structure.content_blocks if b.block_type == ContentBlockType.TABLE]
        assert len(table_blocks) >= 1
        
        # Check table metadata
        table_block = None
        for block in table_blocks:
            if block.element.tag.lower() == "table":
                table_block = block
                break
                
        if table_block:
            metadata = table_block.metadata
            # Should detect table structure
            assert "row_count" in metadata
            assert "column_count" in metadata
            
    def test_list_analysis(self):
        """Test analysis of list structures."""
        content = """
        <h1>List Example</h1>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        <ol>
            <li>Numbered item 1</li>
            <li>Numbered item 2</li>
        </ol>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Find list blocks
        list_blocks = [b for b in structure.content_blocks if b.block_type == ContentBlockType.LIST]
        assert len(list_blocks) >= 1
        
        # Check list metadata
        for block in list_blocks:
            if block.element.tag.lower() in ["ul", "ol"]:
                metadata = block.metadata
                assert "item_count" in metadata
                
    def test_empty_content(self):
        """Test analysis of empty or minimal content."""
        content = "<p>Just one paragraph</p>"
        
        structure = self.analyzer.analyze(content)
        
        assert len(structure.headings) == 0
        assert len(structure.sections) == 0
        assert len(structure.content_blocks) >= 1  # At least the paragraph
        assert len(structure.insertion_points) >= 2  # Start and end of page
        
    def test_complex_confluence_content(self):
        """Test analysis of complex Confluence content with mixed elements."""
        content = """
        <h1>Project Documentation</h1>
        <ac:structured-macro ac:name="toc" ac:schema-version="1">
            <ac:parameter ac:name="maxLevel">2</ac:parameter>
        </ac:structured-macro>
        
        <h2>Overview</h2>
        <p>This project provides comprehensive documentation.</p>
        
        <ac:layout>
            <ac:layout-section ac:type="two_equal">
                <ac:layout-cell>
                    <h3>Features</h3>
                    <ul>
                        <li>Feature 1</li>
                        <li>Feature 2</li>
                    </ul>
                </ac:layout-cell>
                <ac:layout-cell>
                    <h3>Benefits</h3>
                    <p>Key benefits include...</p>
                </ac:layout-cell>
            </ac:layout-section>
        </ac:layout>
        
        <h2>Technical Details</h2>
        <table>
            <tr><th>Component</th><th>Description</th></tr>
            <tr><td>Parser</td><td>XML parsing component</td></tr>
            <tr><td>Analyzer</td><td>Content analysis component</td></tr>
        </table>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Should detect all major components
        assert len(structure.headings) >= 4  # H1, H2s, H3s
        assert len(structure.sections) >= 4
        assert structure.has_macros is True
        assert structure.has_layouts is True
        
        # Should find various content types
        block_types = {block.block_type for block in structure.content_blocks}
        assert ContentBlockType.HEADING in block_types
        assert ContentBlockType.PARAGRAPH in block_types
        assert ContentBlockType.TABLE in block_types
        assert ContentBlockType.LIST in block_types
        assert ContentBlockType.MACRO in block_types
        assert ContentBlockType.LAYOUT in block_types
        
        # Should provide useful insertion points
        assert len(structure.insertion_points) > 5
        
    def test_content_structure_methods(self):
        """Test ContentStructure helper methods."""
        content = """
        <h1>Level 1 A</h1>
        <p>Content A</p>
        <h2>Level 2 A</h2>
        <p>Content 2A</p>
        <h1>Level 1 B</h1>
        <p>Content B</p>
        <h2>Level 2 B</h2>
        <p>Content 2B</p>
        """
        
        structure = self.analyzer.analyze(content)
        
        # Test get_sections_by_level
        h1_sections = structure.get_sections_by_level(1)
        h2_sections = structure.get_sections_by_level(2)
        
        assert len(h1_sections) == 2
        assert len(h2_sections) == 2
        
        # Test get_top_level_sections
        top_sections = structure.get_top_level_sections()
        assert len(top_sections) == 2
        assert all(section.heading.level == 1 for section in top_sections)
        
    def test_error_handling(self):
        """Test error handling in content analysis."""
        # Test with malformed content that should trigger text fallback
        malformed_content = "<p>Unclosed paragraph<div>Nested without closing"
        
        # Should not raise exception, but use fallback parsing
        structure = self.analyzer.analyze(malformed_content)
        assert structure is not None
        
    def test_section_text_extraction(self):
        """Test extraction of text content from sections."""
        content = """
        <h1>Introduction</h1>
        <p>This is the introduction text.</p>
        <p>It has multiple paragraphs.</p>
        <h2>Details</h2>
        <p>This is detailed information.</p>
        """
        
        structure = self.analyzer.analyze(content)
        
        intro_section = structure.get_section_by_heading("Introduction")
        assert intro_section is not None
        
        section_text = intro_section.section_text
        assert "introduction text" in section_text.lower()
        assert "multiple paragraphs" in section_text.lower()


class TestIntegrationWithXMLParser:
    """Test integration between ContentStructureAnalyzer and ConfluenceXMLParser."""
    
    def test_analyzer_with_custom_parser(self):
        """Test analyzer using custom XML parser instance."""
        parser = ConfluenceXMLParser(preserve_whitespace=False)
        analyzer = ContentStructureAnalyzer(xml_parser=parser)
        
        content = "<h1>Title</h1><p>Content</p>"
        structure = analyzer.analyze(content)
        
        assert len(structure.headings) == 1
        assert structure.headings[0].text == "Title"
        
    def test_parser_error_handling_integration(self):
        """Test that parser errors are properly handled by analyzer."""
        analyzer = ContentStructureAnalyzer()
        
        # Content that should trigger parser fallback
        problematic_content = '<p>Content with &invalid entity & unclosed <img src="test.jpg">'
        
        # Should handle gracefully using parser's fallback mechanisms
        structure = analyzer.analyze(problematic_content)
        assert structure is not None
        
        # Should contain content even if parsing was imperfect
        assert structure.total_elements > 0 