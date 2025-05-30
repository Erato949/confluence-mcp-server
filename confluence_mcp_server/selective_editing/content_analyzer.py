"""
Content Structure Analyzer for Confluence Selective Editing System

This module provides intelligent analysis of Confluence page structure,
enabling surgical editing operations by understanding content organization,
heading hierarchy, and element relationships.

Key Features:
- Heading hierarchy analysis (H1-H6)
- Section boundary detection
- Content block classification
- Insertion point identification
- Table and list structure analysis
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from .xml_parser import ConfluenceXMLParser
from .exceptions import ContentStructureError, SectionNotFoundError

logger = logging.getLogger(__name__)


class ContentBlockType(Enum):
    """Types of content blocks that can be identified."""
    
    PARAGRAPH = "paragraph"
    HEADING = "heading" 
    TABLE = "table"
    LIST = "list"
    MACRO = "macro"
    LAYOUT = "layout"
    IMAGE = "image"
    LINK = "link"
    CODE_BLOCK = "code_block"
    QUOTE = "quote"
    UNKNOWN = "unknown"


@dataclass
class HeadingInfo:
    """Information about a heading element."""
    
    level: int
    text: str
    element: ET.Element
    position: int
    element_index: int = 0  # Index in parent's children
    
    def __str__(self):
        return f"H{self.level}: {self.text} (pos: {self.position})"


@dataclass
class SectionInfo:
    """Information about a content section (heading + content until next heading)."""
    
    heading: HeadingInfo
    content_elements: List[ET.Element] = field(default_factory=list)
    start_position: int = 0
    end_position: int = 0
    subsections: List['SectionInfo'] = field(default_factory=list)
    
    @property
    def section_text(self) -> str:
        """Get the text content of this section."""
        texts = []
        for element in self.content_elements:
            if element.text:
                texts.append(element.text.strip())
            if element.tail:
                texts.append(element.tail.strip())
        return ' '.join(filter(None, texts))
    
    def __str__(self):
        return f"Section: {self.heading.text} ({len(self.content_elements)} elements)"


@dataclass
class ContentBlock:
    """Information about a content block (paragraph, table, etc.)."""
    
    block_type: ContentBlockType
    element: ET.Element
    position: int
    text_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        preview = self.text_content[:50] + "..." if len(self.text_content) > 50 else self.text_content
        return f"{self.block_type.value}: {preview}"


@dataclass
class InsertionPoint:
    """Represents a location where content can be safely inserted."""
    
    location_type: str  # 'after_heading', 'before_heading', 'end_of_section', 'start_of_page'
    reference_element: Optional[ET.Element] = None
    reference_heading: Optional[HeadingInfo] = None
    position: int = 0
    description: str = ""
    
    def __str__(self):
        return f"{self.location_type}: {self.description}"


class ContentStructure:
    """Complete analysis of content structure."""
    
    def __init__(self):
        self.headings: List[HeadingInfo] = []
        self.sections: List[SectionInfo] = []
        self.content_blocks: List[ContentBlock] = []
        self.insertion_points: List[InsertionPoint] = []
        self.heading_hierarchy: Dict[str, Any] = {}
        self.total_elements: int = 0
        self.has_macros: bool = False
        self.has_layouts: bool = False
        
    def get_section_by_heading(self, heading_text: str, case_sensitive: bool = False) -> Optional[SectionInfo]:
        """Find a section by its heading text."""
        search_text = heading_text if case_sensitive else heading_text.lower()
        
        for section in self.sections:
            section_heading = section.heading.text if case_sensitive else section.heading.text.lower()
            if section_heading == search_text:
                return section
                
        return None
        
    def get_sections_by_level(self, level: int) -> List[SectionInfo]:
        """Get all sections at a specific heading level."""
        return [section for section in self.sections if section.heading.level == level]
        
    def get_top_level_sections(self) -> List[SectionInfo]:
        """Get all top-level sections (usually H1 or the highest level present)."""
        if not self.sections:
            return []
            
        min_level = min(section.heading.level for section in self.sections)
        return self.get_sections_by_level(min_level)


class ContentStructureAnalyzer:
    """
    Analyzes Confluence page structure for intelligent editing operations.
    
    This class provides comprehensive analysis of Confluence Storage Format content,
    identifying headings, sections, content blocks, and safe insertion points.
    """
    
    def __init__(self, xml_parser: Optional[ConfluenceXMLParser] = None):
        """
        Initialize the content structure analyzer.
        
        Args:
            xml_parser: Optional XML parser instance (creates new one if None)
        """
        self.xml_parser = xml_parser or ConfluenceXMLParser()
        self._current_root: Optional[ET.Element] = None
        self._element_positions: Dict[ET.Element, int] = {}
        
    def analyze(self, content: str) -> ContentStructure:
        """
        Perform complete analysis of content structure.
        
        Args:
            content: Confluence Storage Format content to analyze
            
        Returns:
            ContentStructure object with complete analysis
            
        Raises:
            ContentStructureError: If analysis fails
        """
        try:
            # Parse the content
            self._current_root = self.xml_parser.parse(content)
            
            # Build element position mapping
            self._build_element_positions()
            
            # Create structure object
            structure = ContentStructure()
            
            # Perform analysis
            structure.headings = self.find_headings()
            structure.sections = self.find_sections(structure.headings)
            structure.content_blocks = self.get_content_blocks()
            structure.insertion_points = self.find_insertion_points(structure.headings, structure.sections)
            structure.heading_hierarchy = self.build_heading_hierarchy(structure.headings)
            
            # Set metadata
            structure.total_elements = len(list(self._current_root.iter()))
            structure.has_macros = self._has_confluence_macros()
            structure.has_layouts = self._has_confluence_layouts()
            
            return structure
            
        except Exception as e:
            raise ContentStructureError(f"Content analysis failed: {str(e)}")
            
    def find_headings(self) -> List[HeadingInfo]:
        """
        Find all headings in the content.
        
        Returns:
            List of HeadingInfo objects for all headings found
        """
        if self._current_root is None:
            return []
            
        headings = []
        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        for element in self._current_root.iter():
            if element.tag.lower() in heading_tags:
                level = int(element.tag.lower()[1])  # Extract number from h1, h2, etc.
                text = self._get_element_text(element)
                position = self._element_positions.get(element, 0)
                
                # For now, use position as element_index (simple approach)
                # This can be enhanced later when parent-child relationships are needed
                element_index = position
                
                heading = HeadingInfo(
                    level=level,
                    text=text,
                    element=element,
                    position=position,
                    element_index=element_index
                )
                headings.append(heading)
                
        # Sort by position
        headings.sort(key=lambda h: h.position)
        return headings
        
    def find_sections(self, headings: List[HeadingInfo]) -> List[SectionInfo]:
        """
        Identify content sections based on heading structure.
        
        Args:
            headings: List of headings to use for section identification
            
        Returns:
            List of SectionInfo objects
        """
        if not headings or self._current_root is None:
            return []
            
        sections = []
        all_elements = list(self._current_root.iter())
        
        for i, heading in enumerate(headings):
            section = SectionInfo(heading=heading)
            
            # Find start position (after this heading)
            heading_pos = all_elements.index(heading.element)
            section.start_position = heading_pos + 1
            
            # Find end position (before next heading of same or higher level)
            section.end_position = len(all_elements)
            
            for j in range(i + 1, len(headings)):
                next_heading = headings[j]
                if next_heading.level <= heading.level:
                    next_heading_pos = all_elements.index(next_heading.element)
                    section.end_position = next_heading_pos
                    break
                    
            # Collect content elements in this section
            section.content_elements = all_elements[section.start_position:section.end_position]
            
            # Find subsections (headings with higher level in this range)
            subsection_headings = [
                h for h in headings[i+1:]
                if h.level > heading.level and h.position < section.end_position
            ]
            
            # Build subsections recursively
            if subsection_headings:
                section.subsections = self.find_sections(subsection_headings)
                
            sections.append(section)
            
        return sections
        
    def build_heading_hierarchy(self, headings: List[HeadingInfo]) -> Dict[str, Any]:
        """
        Build a hierarchical structure of headings.
        
        Args:
            headings: List of headings to organize
            
        Returns:
            Nested dictionary representing heading hierarchy
        """
        if not headings:
            return {}
            
        hierarchy = {
            "levels": {},
            "structure": [],
            "max_level": 0,
            "min_level": 6
        }
        
        # Group by level
        for heading in headings:
            level = heading.level
            if level not in hierarchy["levels"]:
                hierarchy["levels"][level] = []
            hierarchy["levels"][level].append({
                "text": heading.text,
                "position": heading.position,
                "element_index": heading.element_index
            })
            
            hierarchy["max_level"] = max(hierarchy["max_level"], level)
            hierarchy["min_level"] = min(hierarchy["min_level"], level)
            
        # Build nested structure
        hierarchy["structure"] = self._build_nested_structure(headings)
        
        return hierarchy
        
    def _build_nested_structure(self, headings: List[HeadingInfo]) -> List[Dict[str, Any]]:
        """Build nested structure from flat heading list."""
        if not headings:
            return []
            
        structure = []
        stack = []  # Stack to track current hierarchy
        
        for heading in headings:
            node = {
                "text": heading.text,
                "level": heading.level,
                "position": heading.position,
                "children": []
            }
            
            # Pop from stack until we find the right parent level
            while stack and stack[-1]["level"] >= heading.level:
                stack.pop()
                
            if stack:
                # Add as child to current parent
                stack[-1]["children"].append(node)
            else:
                # Top-level heading
                structure.append(node)
                
            stack.append(node)
            
        return structure
        
    def get_content_blocks(self) -> List[ContentBlock]:
        """
        Identify and classify content blocks.
        
        Returns:
            List of ContentBlock objects
        """
        if self._current_root is None:
            return []
            
        blocks = []
        
        for element in self._current_root.iter():
            block_type = self._classify_element(element)
            if block_type != ContentBlockType.UNKNOWN:
                text_content = self._get_element_text(element)
                position = self._element_positions.get(element, 0)
                metadata = self._extract_element_metadata(element)
                
                block = ContentBlock(
                    block_type=block_type,
                    element=element,
                    position=position,
                    text_content=text_content,
                    metadata=metadata
                )
                blocks.append(block)
                
        return blocks
        
    def find_insertion_points(self, headings: List[HeadingInfo], 
                            sections: List[SectionInfo]) -> List[InsertionPoint]:
        """
        Identify safe locations for content insertion.
        
        Args:
            headings: List of headings
            sections: List of sections
            
        Returns:
            List of InsertionPoint objects
        """
        insertion_points = []
        
        # Start of page
        insertion_points.append(InsertionPoint(
            location_type="start_of_page",
            position=0,
            description="Beginning of page content"
        ))
        
        # After each heading
        for heading in headings:
            insertion_points.append(InsertionPoint(
                location_type="after_heading",
                reference_element=heading.element,
                reference_heading=heading,
                position=heading.position + 1,
                description=f"After heading: {heading.text}"
            ))
            
        # End of each section
        for section in sections:
            insertion_points.append(InsertionPoint(
                location_type="end_of_section",
                reference_heading=section.heading,
                position=section.end_position,
                description=f"End of section: {section.heading.text}"
            ))
            
        # End of page
        if self._current_root is not None:
            total_elements = len(list(self._current_root.iter()))
            insertion_points.append(InsertionPoint(
                location_type="end_of_page",
                position=total_elements,
                description="End of page content"
            ))
            
        # Sort by position
        insertion_points.sort(key=lambda p: p.position)
        return insertion_points
        
    def find_section_by_heading(self, heading_text: str, 
                               case_sensitive: bool = False,
                               exact_match: bool = True) -> Optional[SectionInfo]:
        """
        Find a section by its heading text.
        
        Args:
            heading_text: Text to search for
            case_sensitive: Whether search should be case sensitive
            exact_match: Whether to require exact match or allow partial
            
        Returns:
            SectionInfo if found, None otherwise
        """
        if self._current_root is None:
            return None
            
        # Get current structure
        try:
            structure = self.analyze(self.xml_parser.to_string(self._current_root))
            return structure.get_section_by_heading(heading_text, case_sensitive)
        except Exception as e:
            logger.warning(f"Error finding section by heading: {e}")
            return None
            
    def _build_element_positions(self) -> None:
        """Build mapping of elements to their positions."""
        if self._current_root is None:
            return
            
        self._element_positions.clear()
        for i, element in enumerate(self._current_root.iter()):
            self._element_positions[element] = i
            
    def _get_element_text(self, element: ET.Element) -> str:
        """Extract text content from an element."""
        texts = []
        if element.text:
            texts.append(element.text.strip())
        if element.tail:
            texts.append(element.tail.strip())
            
        # Get text from child elements
        for child in element:
            child_text = self._get_element_text(child)
            if child_text:
                texts.append(child_text)
                
        return ' '.join(filter(None, texts))
        
    def _classify_element(self, element: ET.Element) -> ContentBlockType:
        """Classify an element into a content block type."""
        tag = element.tag.lower()
        
        # Skip root wrapper elements
        if tag == 'root':
            return ContentBlockType.UNKNOWN
        
        # Handle heading elements
        if re.match(r'^h[1-6]$', tag):
            return ContentBlockType.HEADING
            
        # Handle paragraph elements
        if tag in ['p', 'div']:
            return ContentBlockType.PARAGRAPH
            
        # Handle table elements
        if tag in ['table', 'tbody', 'tr', 'td', 'th']:
            return ContentBlockType.TABLE
            
        # Handle list elements
        if tag in ['ul', 'ol', 'li']:
            return ContentBlockType.LIST
            
        # Handle image elements
        if tag in ['img']:
            return ContentBlockType.IMAGE
            
        # Handle link elements
        if tag in ['a']:
            return ContentBlockType.LINK
            
        # Handle code elements
        if tag in ['code', 'pre']:
            return ContentBlockType.CODE_BLOCK
            
        # Handle quote elements
        if tag in ['blockquote']:
            return ContentBlockType.QUOTE
            
        # Handle Confluence-specific elements
        if 'structured-macro' in tag or 'macro' in tag:
            return ContentBlockType.MACRO
            
        if 'layout' in tag:
            return ContentBlockType.LAYOUT
            
        # For any other element with text content, classify as paragraph
        text_content = self._get_element_text(element)
        if text_content and text_content.strip():
            return ContentBlockType.PARAGRAPH
            
        return ContentBlockType.UNKNOWN
        
    def _extract_element_metadata(self, element: ET.Element) -> Dict[str, Any]:
        """Extract metadata from an element."""
        metadata = {}
        
        # Basic attributes
        metadata["tag"] = element.tag
        metadata["attributes"] = dict(element.attrib)
        
        # Special handling for different element types
        if 'structured-macro' in element.tag:
            # Try different ways to get the macro name (namespace-aware)
            macro_name = (element.get("ac:name") or 
                         element.get("name") or 
                         element.get("{http://www.atlassian.com/schema/confluence/4/ac/}name"))
            metadata["macro_name"] = macro_name
            
        if element.tag.lower() == 'table':
            # Count rows and columns
            rows = element.findall('.//tr')
            metadata["row_count"] = len(rows)
            if rows:
                metadata["column_count"] = len(rows[0].findall('.//td') + rows[0].findall('.//th'))
                
        if element.tag.lower() in ['ul', 'ol']:
            items = element.findall('.//li')
            metadata["item_count"] = len(items)
            
        return metadata
        
    def _has_confluence_macros(self) -> bool:
        """Check if content contains Confluence macros."""
        if self._current_root is None:
            return False
            
        for element in self._current_root.iter():
            if 'macro' in element.tag:
                return True
        return False
        
    def _has_confluence_layouts(self) -> bool:
        """Check if content contains Confluence layouts."""
        if self._current_root is None:
            return False
            
        for element in self._current_root.iter():
            if 'layout' in element.tag:
                return True
        return False 