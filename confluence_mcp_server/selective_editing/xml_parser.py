"""
XML Parser for Confluence Storage Format

This module provides safe parsing and manipulation of Confluence Storage Format XML,
handling the complexity of mixed HTML and custom Confluence elements.

Key Features:
- Safe XML parsing with fallback to string manipulation
- Preservation of custom Confluence elements (macros, layouts, etc.)
- Error recovery and validation
- Content reconstruction while maintaining structure
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any, Tuple
import re
import logging
from copy import deepcopy

from .exceptions import XMLParsingError, ContentStructureError, ValidationError

logger = logging.getLogger(__name__)


class ConfluenceXMLParser:
    """
    Parser for Confluence Storage Format XML with safety features and error handling.
    
    Handles the complex XML structure used by Confluence including:
    - Standard HTML elements (p, h1-h6, table, ul, ol, etc.)
    - Confluence custom elements (ac:structured-macro, ac:layout, etc.)
    - Resource identifiers (ri:page, ri:attachment, etc.)
    - Mixed content and nested structures
    """
    
    # XML namespaces used by Confluence
    CONFLUENCE_NAMESPACES = {
        'ac': 'http://www.atlassian.com/schema/confluence/4/ac/',
        'ri': 'http://www.atlassian.com/schema/confluence/4/ri/',
        'at': 'http://www.atlassian.com/schema/confluence/4/at/'
    }
    
    # Common Confluence custom elements
    CONFLUENCE_ELEMENTS = {
        'macros': ['ac:structured-macro', 'ac:macro'],
        'layouts': ['ac:layout', 'ac:layout-section', 'ac:layout-cell'],
        'resources': ['ri:page', 'ri:attachment', 'ri:url', 'ri:user'],
        'special': ['ac:emoticon', 'ac:placeholder', 'ac:task-list', 'ac:task']
    }
    
    def __init__(self, preserve_whitespace: bool = True, validate_on_parse: bool = True):
        """
        Initialize the XML parser.
        
        Args:
            preserve_whitespace: Whether to preserve whitespace in content
            validate_on_parse: Whether to validate XML structure during parsing
        """
        self.preserve_whitespace = preserve_whitespace
        self.validate_on_parse = validate_on_parse
        self._original_content = None
        self._parsed_tree = None
        self._parse_errors = []
        
    def parse(self, xml_content: str) -> ET.Element:
        """
        Parse Confluence Storage Format XML content.
        
        Args:
            xml_content: Raw XML content string
            
        Returns:
            Parsed XML element tree root
            
        Raises:
            XMLParsingError: If XML parsing fails completely
        """
        self._original_content = xml_content
        self._parse_errors = []
        
        # Store original content for fallback
        if not xml_content or not xml_content.strip():
            raise XMLParsingError("Empty or whitespace-only content provided")
            
        try:
            # First, try to parse as-is
            return self._parse_xml_safely(xml_content)
            
        except XMLParsingError as e:
            logger.warning(f"Initial XML parsing failed: {e}")
            
            # Try to fix common issues and re-parse
            try:
                fixed_content = self._fix_common_xml_issues(xml_content)
                return self._parse_xml_safely(fixed_content)
                
            except XMLParsingError as e2:
                logger.error(f"XML parsing failed even after fixes: {e2}")
                
                # Last resort: try to extract content using string manipulation
                return self._parse_as_text_fallback(xml_content)
                
    def _parse_xml_safely(self, xml_content: str) -> ET.Element:
        """
        Safely parse XML content with proper namespace handling.
        
        Args:
            xml_content: XML content to parse
            
        Returns:
            Parsed XML element tree root
        """
        try:
            # Check if we need to wrap in root and add namespace declarations
            needs_root = (not xml_content.strip().startswith('<') or 
                         not self._has_single_root(xml_content))
            
            if needs_root:
                # Build namespace declarations for root wrapper
                ns_declarations = []
                for prefix, uri in self.CONFLUENCE_NAMESPACES.items():
                    if f'{prefix}:' in xml_content:
                        ns_declarations.append(f'xmlns:{prefix}="{uri}"')
                
                if ns_declarations:
                    ns_string = ' ' + ' '.join(ns_declarations)
                    xml_content = f"<root{ns_string}>{xml_content}</root>"
                else:
                    xml_content = f"<root>{xml_content}</root>"
            else:
                # Single root element - add namespaces to it if needed
                xml_content = self._add_namespace_declarations(xml_content)
                
            # Register namespaces for output
            for prefix, uri in self.CONFLUENCE_NAMESPACES.items():
                ET.register_namespace(prefix, uri)
                
            # Parse the XML
            root = ET.fromstring(xml_content)
            self._parsed_tree = ET.ElementTree(root)
            
            if self.validate_on_parse:
                self._validate_structure(root)
                
            return root
            
        except ET.ParseError as e:
            raise XMLParsingError(f"XML parsing failed: {str(e)}", xml_content)
            
    def _add_namespace_declarations(self, xml_content: str) -> str:
        """
        Add namespace declarations to XML content if Confluence elements are detected.
        
        Args:
            xml_content: Original XML content
            
        Returns:
            XML content with namespace declarations
        """
        # Check if content contains Confluence elements
        has_confluence_elements = any(
            prefix + ':' in xml_content 
            for prefix in self.CONFLUENCE_NAMESPACES.keys()
        )
        
        if not has_confluence_elements:
            return xml_content
            
        # If we're going to wrap in root, add namespaces to root
        needs_root = (not xml_content.strip().startswith('<') or 
                     not self._has_single_root(xml_content))
        
        if needs_root:
            # Will be wrapped in root, so add namespaces to root
            return xml_content
        else:
            # Single root element - add namespaces to it
            return self._add_namespaces_to_root_element(xml_content)
            
    def _add_namespaces_to_root_element(self, xml_content: str) -> str:
        """Add namespace declarations to the root element of XML content."""
        # Find the first tag
        import re
        tag_match = re.match(r'(\s*<[^>\s]+)', xml_content)
        if not tag_match:
            return xml_content
            
        tag_part = tag_match.group(1)
        
        # Build namespace declarations
        ns_declarations = []
        for prefix, uri in self.CONFLUENCE_NAMESPACES.items():
            if f'{prefix}:' in xml_content:
                ns_declarations.append(f'xmlns:{prefix}="{uri}"')
                
        if not ns_declarations:
            return xml_content
            
        # Insert namespace declarations into the root tag
        ns_string = ' ' + ' '.join(ns_declarations)
        
        # Handle self-closing tags
        if tag_part.endswith('/>'):
            new_tag = tag_part[:-2] + ns_string + '/>'
        elif tag_part.endswith('>'):
            new_tag = tag_part[:-1] + ns_string + '>'
        else:
            # Tag not closed yet, add space and let normal parsing handle it
            new_tag = tag_part + ns_string
            
        return new_tag + xml_content[len(tag_part):]
        
    def _has_single_root(self, xml_content: str) -> bool:
        """Check if XML content has a single root element."""
        try:
            # Quick check by trying to parse
            ET.fromstring(xml_content)
            return True
        except ET.ParseError:
            return False
            
    def _fix_common_xml_issues(self, xml_content: str) -> str:
        """
        Fix common XML issues that prevent parsing.
        
        Args:
            xml_content: Original XML content
            
        Returns:
            Fixed XML content
        """
        fixed = xml_content
        
        # Fix unclosed br tags
        fixed = re.sub(r'<br(?:\s+[^>]*)?>(?!</br>)', '<br/>', fixed)
        
        # Fix unclosed hr tags  
        fixed = re.sub(r'<hr(?:\s+[^>]*)?>(?!</hr>)', '<hr/>', fixed)
        
        # Fix unclosed img tags
        fixed = re.sub(r'<img([^>]*?)(?<!/)>(?!</img>)', r'<img\1/>', fixed)
        
        # Fix ampersands that aren't part of entities
        fixed = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', fixed)
        
        # Fix quotes in attributes
        fixed = re.sub(r'(\w+)=([^"\s>]+)(?=\s|>)', r'\1="\2"', fixed)
        
        return fixed
        
    def _parse_as_text_fallback(self, xml_content: str) -> ET.Element:
        """
        Fallback method to create a basic structure when XML parsing fails.
        
        Args:
            xml_content: Original content that failed to parse
            
        Returns:
            Simple element structure with content
        """
        logger.warning("Using text fallback for XML parsing")
        
        # Create a simple structure
        root = ET.Element("div")
        root.text = xml_content
        root.set("data-parse-method", "text-fallback")
        
        self._parse_errors.append("XML parsing failed, using text fallback")
        return root
        
    def _validate_structure(self, root: ET.Element) -> None:
        """
        Validate the XML structure for common issues.
        
        Args:
            root: Root element to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for deeply nested structures that might cause issues
        max_depth = self._get_max_depth(root)
        if max_depth > 20:
            self._parse_errors.append(f"Very deep nesting detected: {max_depth} levels")
            
        # Check for very large number of elements
        element_count = len(list(root.iter()))
        if element_count > 10000:
            self._parse_errors.append(f"Very large number of elements: {element_count}")
            
        # Check for malformed macro structures
        self._validate_macro_structures(root)
        
    def _get_max_depth(self, element: ET.Element, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of XML structure."""
        max_child_depth = current_depth
        for child in element:
            child_depth = self._get_max_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        return max_child_depth
        
    def _validate_macro_structures(self, root: ET.Element) -> None:
        """Validate that macro structures are well-formed."""
        for macro in root.iter():
            if macro.tag in ['ac:structured-macro', 'ac:macro']:
                # Check if macro has required name attribute
                if 'ac:name' not in macro.attrib and 'name' not in macro.attrib:
                    self._parse_errors.append(f"Macro missing name attribute: {ET.tostring(macro, encoding='unicode')[:100]}...")
                    
    def to_string(self, element: Optional[ET.Element] = None, 
                  include_root: bool = False, pretty: bool = False) -> str:
        """
        Convert element tree back to string format.
        
        Args:
            element: Element to convert (uses parsed tree root if None)
            include_root: Whether to include the root wrapper element
            pretty: Whether to pretty-print the output
            
        Returns:
            XML string representation
        """
        if element is None:
            if self._parsed_tree is None:
                raise ValueError("No parsed tree available")
            element = self._parsed_tree.getroot()
            
        try:
            # Convert to string
            xml_str = ET.tostring(element, encoding='unicode', method='xml')
            
            # Remove root wrapper if it was added during parsing
            if not include_root and element.tag == 'root':
                # Extract content between root tags
                xml_str = re.sub(r'^<root[^>]*>', '', xml_str)
                xml_str = re.sub(r'</root>$', '', xml_str)
                
            # Pretty print if requested
            if pretty:
                xml_str = self._pretty_print_xml(xml_str)
                
            return xml_str
            
        except Exception as e:
            raise XMLParsingError(f"Failed to convert element to string: {str(e)}")
            
    def _pretty_print_xml(self, xml_str: str) -> str:
        """Basic XML pretty printing."""
        # This is a simple implementation - for production, consider using a proper XML formatter
        lines = []
        indent_level = 0
        indent_str = "  "
        
        for line in xml_str.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Handle closing tags
            if line.startswith('</'):
                indent_level -= 1
                
            lines.append(indent_str * indent_level + line)
            
            # Handle opening tags
            if line.startswith('<') and not line.startswith('</') and not line.endswith('/>'):
                indent_level += 1
                
        return '\n'.join(lines)
        
    def find_elements_by_tag(self, tag_name: str, root: Optional[ET.Element] = None) -> List[ET.Element]:
        """
        Find all elements with the specified tag name.
        
        Args:
            tag_name: Tag name to search for
            root: Root element to search in (uses parsed tree if None)
            
        Returns:
            List of matching elements
        """
        if root is None:
            if self._parsed_tree is None:
                raise ValueError("No parsed tree available")
            root = self._parsed_tree.getroot()
            
        return list(root.iter(tag_name))
        
    def find_elements_by_attribute(self, attr_name: str, attr_value: str, 
                                   root: Optional[ET.Element] = None) -> List[ET.Element]:
        """
        Find all elements with the specified attribute value.
        
        Args:
            attr_name: Attribute name
            attr_value: Attribute value to match
            root: Root element to search in
            
        Returns:
            List of matching elements
        """
        if root is None:
            if self._parsed_tree is None:
                raise ValueError("No parsed tree available")
            root = self._parsed_tree.getroot()
            
        matches = []
        for element in root.iter():
            if element.get(attr_name) == attr_value:
                matches.append(element)
                
        return matches
        
    def get_parse_errors(self) -> List[str]:
        """Get list of parse errors and warnings."""
        return self._parse_errors.copy()
        
    def has_parse_errors(self) -> bool:
        """Check if there were any parse errors."""
        return len(self._parse_errors) > 0
        
    def clone_element(self, element: ET.Element) -> ET.Element:
        """Create a deep copy of an element."""
        return deepcopy(element)
        
    def is_confluence_macro(self, element: ET.Element) -> bool:
        """Check if element is a Confluence macro."""
        return element.tag in ['ac:structured-macro', 'ac:macro']
        
    def is_confluence_layout(self, element: ET.Element) -> bool:
        """Check if element is part of Confluence layout system."""
        return element.tag in ['ac:layout', 'ac:layout-section', 'ac:layout-cell'] 