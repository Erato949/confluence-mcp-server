"""
Section Editor for Confluence Selective Editing System

This module implements section-based editing operations that can surgically modify
specific parts of Confluence pages while preserving the rest of the content.

Key Features:
- Replace content of specific sections by heading
- Insert content after specific headings
- Update heading text while preserving structure
- Safe editing with validation and rollback capabilities
- Macro and layout preservation
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
import copy

from .xml_parser import ConfluenceXMLParser
from .content_analyzer import ContentStructureAnalyzer, SectionInfo, HeadingInfo
from .operations import (
    OperationType, OperationResult, ReplaceSectionOperation, 
    InsertAfterHeadingOperation, SelectiveEditOperation
)
from .exceptions import (
    SectionNotFoundError, ContentStructureError, 
    XMLParsingError, EditingError
)

logger = logging.getLogger(__name__)


class SectionEditor:
    """
    Core section-based editing engine for Confluence pages.
    
    This class provides surgical editing capabilities that can modify specific
    sections of a Confluence page while preserving the rest of the content,
    including macros, layouts, and complex formatting.
    """
    
    def __init__(self, xml_parser: Optional[ConfluenceXMLParser] = None):
        """
        Initialize the section editor.
        
        Args:
            xml_parser: Optional XML parser instance. If not provided, creates a new one.
        """
        self.xml_parser = xml_parser or ConfluenceXMLParser()
        self.content_analyzer = ContentStructureAnalyzer(self.xml_parser)
        self._backup_content: Optional[str] = None
        
    def replace_section(self, 
                       content: str,
                       heading: str,
                       new_content: str,
                       heading_level: Optional[int] = None,
                       exact_match: bool = True,
                       case_sensitive: bool = False,
                       preserve_heading: bool = True) -> OperationResult:
        """
        Replace the content of a specific section identified by its heading.
        
        This operation finds a section by its heading and replaces all content
        under that heading (until the next heading of the same or higher level)
        with the provided new content.
        
        Args:
            content: The original page content (Confluence storage format)
            heading: The heading text to search for
            new_content: The new content to replace the section with
            heading_level: Optional specific heading level to match (1-6)
            exact_match: Whether to require exact heading text match
            case_sensitive: Whether heading search should be case sensitive
            preserve_heading: Whether to keep the original heading (default: True)
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_SECTION,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Analyze content structure
            structure = self.content_analyzer.analyze(content)
            
            # Find the target section
            target_section = structure.get_section_by_heading(heading, case_sensitive)
            if not target_section:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_SECTION,
                    error_message=f"Section with heading '{heading}' not found",
                    backup_content=self._backup_content
                )
            
            # Validate heading level if specified
            if heading_level and target_section.heading.level != heading_level:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_SECTION,
                    error_message=f"Found heading '{heading}' but level {target_section.heading.level} doesn't match required level {heading_level}",
                    backup_content=self._backup_content
                )
            
            # Perform the replacement
            modified_content = self._replace_section_content(
                target_section, new_content, preserve_heading
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_SECTION,
                    error_message="Failed to replace section content",
                    backup_content=self._backup_content
                )
            
            return OperationResult(
                success=True,
                operation_type=OperationType.REPLACE_SECTION,
                modified_content=modified_content,
                changes_made=[f"Replaced content under heading '{heading}'"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in replace_section: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.REPLACE_SECTION,
                error_message=f"Section replacement failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def insert_after_heading(self,
                           content: str,
                           heading: str,
                           insert_content: str,
                           heading_level: Optional[int] = None,
                           exact_match: bool = True,
                           case_sensitive: bool = False) -> OperationResult:
        """
        Insert content immediately after a specific heading.
        
        This operation finds a heading and inserts new content right after it,
        before any existing content in that section.
        
        Args:
            content: The original page content (Confluence storage format)
            heading: The heading text to search for
            insert_content: The content to insert after the heading
            heading_level: Optional specific heading level to match (1-6)
            exact_match: Whether to require exact heading text match
            case_sensitive: Whether heading search should be case sensitive
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.INSERT_AFTER_HEADING,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Analyze content structure
            structure = self.content_analyzer.analyze(content)
            
            # Find the target section
            target_section = structure.get_section_by_heading(heading, case_sensitive)
            if not target_section:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.INSERT_AFTER_HEADING,
                    error_message=f"Section with heading '{heading}' not found",
                    backup_content=self._backup_content
                )
            
            # Validate heading level if specified
            if heading_level and target_section.heading.level != heading_level:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.INSERT_AFTER_HEADING,
                    error_message=f"Found heading '{heading}' but level {target_section.heading.level} doesn't match required level {heading_level}",
                    backup_content=self._backup_content
                )
            
            # Perform the insertion
            modified_content = self._insert_after_heading_element(
                target_section.heading, insert_content
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.INSERT_AFTER_HEADING,
                    error_message="Failed to insert content after heading",
                    backup_content=self._backup_content
                )
            
            return OperationResult(
                success=True,
                operation_type=OperationType.INSERT_AFTER_HEADING,
                modified_content=modified_content,
                changes_made=[f"Inserted content after heading '{heading}'"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in insert_after_heading: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.INSERT_AFTER_HEADING,
                error_message=f"Content insertion failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def update_section_heading(self,
                             content: str,
                             old_heading: str,
                             new_heading: str,
                             new_level: Optional[int] = None,
                             case_sensitive: bool = False) -> OperationResult:
        """
        Update the text and/or level of a section heading while preserving structure.
        
        Args:
            content: The original page content (Confluence storage format)
            old_heading: The current heading text to find
            new_heading: The new heading text
            new_level: Optional new heading level (1-6)
            case_sensitive: Whether heading search should be case sensitive
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_HEADING_CONTENT,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Analyze content structure
            structure = self.content_analyzer.analyze(content)
            
            # Find the target section
            target_section = structure.get_section_by_heading(old_heading, case_sensitive)
            if not target_section:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_HEADING_CONTENT,
                    error_message=f"Section with heading '{old_heading}' not found",
                    backup_content=self._backup_content
                )
            
            # Perform the heading update
            modified_content = self._update_heading_element(
                target_section.heading, new_heading, new_level
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_HEADING_CONTENT,
                    error_message="Failed to update heading",
                    backup_content=self._backup_content
                )
            
            changes = [f"Updated heading from '{old_heading}' to '{new_heading}'"]
            if new_level and new_level != target_section.heading.level:
                changes.append(f"Changed heading level from {target_section.heading.level} to {new_level}")
            
            return OperationResult(
                success=True,
                operation_type=OperationType.UPDATE_HEADING_CONTENT,
                modified_content=modified_content,
                changes_made=changes,
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in update_section_heading: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.UPDATE_HEADING_CONTENT,
                error_message=f"Heading update failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def execute_operation(self, operation: SelectiveEditOperation, content: str) -> OperationResult:
        """
        Execute a selective editing operation on the provided content.
        
        Args:
            operation: The operation to execute
            content: The content to operate on
            
        Returns:
            OperationResult with the outcome of the operation
        """
        if not operation.validate_parameters():
            return OperationResult(
                success=False,
                operation_type=operation.operation_type,
                error_message="Invalid operation parameters"
            )
        
        if operation.operation_type == OperationType.REPLACE_SECTION:
            return self.replace_section(
                content=content,
                heading=operation.parameters['heading'],
                new_content=operation.parameters['new_content'],
                heading_level=operation.parameters.get('heading_level'),
                exact_match=operation.parameters.get('exact_match', True),
                case_sensitive=operation.parameters.get('case_sensitive', False)
            )
        
        elif operation.operation_type == OperationType.INSERT_AFTER_HEADING:
            return self.insert_after_heading(
                content=content,
                heading=operation.parameters['heading'],
                insert_content=operation.parameters['content'],
                heading_level=operation.parameters.get('heading_level'),
                exact_match=operation.parameters.get('exact_match', True),
                case_sensitive=operation.parameters.get('case_sensitive', False)
            )
        
        else:
            return OperationResult(
                success=False,
                operation_type=operation.operation_type,
                error_message=f"Operation type {operation.operation_type} not yet implemented"
            )
    
    def rollback(self) -> Optional[str]:
        """
        Rollback to the last backup content.
        
        Returns:
            The backup content if available, None otherwise
        """
        return self._backup_content
    
    def _replace_section_content(self, 
                               section: SectionInfo, 
                               new_content: str,
                               preserve_heading: bool = True) -> Optional[str]:
        """
        Replace the content of a section while preserving structure.
        
        Args:
            section: The section to replace content for
            new_content: The new content to insert
            preserve_heading: Whether to keep the original heading
            
        Returns:
            Modified content string or None if failed
        """
        try:
            # Get the current root from the content analyzer
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find the heading element and its parent in the copy
            heading_element = None
            parent = None
            parent_map = {child: parent for parent in root_copy.iter() for child in parent}
            
            for element in root_copy.iter():
                if (element.tag.lower() == f"h{section.heading.level}" and 
                    self.content_analyzer._get_element_text(element).strip() == section.heading.text.strip()):
                    heading_element = element
                    parent = parent_map.get(element)
                    break
            
            if heading_element is None:
                logger.error(f"Could not find heading element for '{section.heading.text}'")
                return None
            
            if parent is None:
                logger.error("Could not find parent element for heading")
                return None
            
            # Find the index of the heading in parent
            heading_index = list(parent).index(heading_element)
            
            # Remove all elements after the heading until next heading of same/higher level
            elements_to_remove = []
            for i in range(heading_index + 1, len(parent)):
                element = parent[i]
                if (element.tag.lower().startswith('h') and 
                    len(element.tag) == 2 and 
                    element.tag[1].isdigit()):
                    # This is a heading
                    heading_level = int(element.tag[1])
                    if heading_level <= section.heading.level:
                        break  # Stop at same or higher level heading
                elements_to_remove.append(element)
            
            # Remove the identified elements
            for element in elements_to_remove:
                parent.remove(element)
            
            # Parse and insert new content
            if new_content.strip():
                try:
                    # Wrap content in a temporary container for parsing
                    wrapped_content = f"<div>{new_content}</div>"
                    temp_parser = ConfluenceXMLParser()
                    temp_root = temp_parser.parse(wrapped_content)
                    if temp_root is not None:
                        # Insert each child of the temp div after the heading
                        insert_index = heading_index + 1
                        for child in temp_root:
                            parent.insert(insert_index, child)
                            insert_index += 1
                except Exception as e:
                    logger.warning(f"Could not parse new content as XML, inserting as text: {e}")
                    # Fallback: create a simple paragraph element
                    p_element = ET.Element('p')
                    p_element.text = new_content
                    parent.insert(heading_index + 1, p_element)
            
            # Convert back to string
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error replacing section content: {e}")
            return None
    
    def _insert_after_heading_element(self, 
                                    heading: HeadingInfo, 
                                    insert_content: str) -> Optional[str]:
        """
        Insert content immediately after a heading element.
        
        Args:
            heading: The heading to insert content after
            insert_content: The content to insert
            
        Returns:
            Modified content string or None if failed
        """
        try:
            # Get the current root from the content analyzer
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find the heading element and its parent in the copy
            heading_element = None
            parent = None
            parent_map = {child: parent for parent in root_copy.iter() for child in parent}
            
            for element in root_copy.iter():
                if (element.tag.lower() == f"h{heading.level}" and 
                    self.content_analyzer._get_element_text(element).strip() == heading.text.strip()):
                    heading_element = element
                    parent = parent_map.get(element)
                    break
            
            if heading_element is None:
                logger.error(f"Could not find heading element for '{heading.text}'")
                return None
            
            if parent is None:
                logger.error("Could not find parent element for heading")
                return None
            
            # Find the index of the heading in parent
            heading_index = list(parent).index(heading_element)
            
            # Parse and insert new content
            if insert_content.strip():
                try:
                    # Wrap content in a temporary container for parsing
                    wrapped_content = f"<div>{insert_content}</div>"
                    temp_parser = ConfluenceXMLParser()
                    temp_root = temp_parser.parse(wrapped_content)
                    if temp_root is not None:
                        # Insert each child of the temp div after the heading
                        insert_index = heading_index + 1
                        for child in temp_root:
                            parent.insert(insert_index, child)
                            insert_index += 1
                except Exception as e:
                    logger.warning(f"Could not parse insert content as XML, inserting as text: {e}")
                    # Fallback: create a simple paragraph element
                    p_element = ET.Element('p')
                    p_element.text = insert_content
                    parent.insert(heading_index + 1, p_element)
            
            # Convert back to string
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error inserting content after heading: {e}")
            return None
    
    def _update_heading_element(self, 
                              heading: HeadingInfo, 
                              new_text: str,
                              new_level: Optional[int] = None) -> Optional[str]:
        """
        Update a heading element's text and/or level.
        
        Args:
            heading: The heading to update
            new_text: The new heading text
            new_level: Optional new heading level
            
        Returns:
            Modified content string or None if failed
        """
        try:
            # Get the current root from the content analyzer
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find the heading element in the copy
            heading_element = None
            for element in root_copy.iter():
                if (element.tag.lower() == f"h{heading.level}" and 
                    self.content_analyzer._get_element_text(element).strip() == heading.text.strip()):
                    heading_element = element
                    break
            
            if heading_element is None:
                logger.error(f"Could not find heading element for '{heading.text}'")
                return None
            
            # Update the heading text
            heading_element.text = new_text
            
            # Update the heading level if specified
            if new_level and new_level != heading.level:
                if 1 <= new_level <= 6:
                    heading_element.tag = f"h{new_level}"
                else:
                    logger.warning(f"Invalid heading level {new_level}, keeping original level {heading.level}")
            
            # Convert back to string
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error updating heading element: {e}")
            return None 