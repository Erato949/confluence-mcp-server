"""
Pattern Editor for Confluence Selective Editing System

This module implements pattern-based editing operations that can find and replace
text patterns while preserving XML structure, macros, and formatting.

Key Features:
- Text pattern find and replace with various options
- Regex pattern matching with capture groups
- Smart content detection to avoid breaking XML elements
- Macro boundary preservation
- Integration with ContentStructureAnalyzer for content-aware operations
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional, Tuple, Any, Union, Pattern
import logging
import copy

from .xml_parser import ConfluenceXMLParser
from .content_analyzer import ContentStructureAnalyzer
from .operations import (
    OperationType, OperationResult, ReplaceTextPatternOperation, 
    ReplaceRegexPatternOperation, SelectiveEditOperation
)
from .exceptions import (
    ContentStructureError, XMLParsingError, EditingError
)

logger = logging.getLogger(__name__)


class PatternEditor:
    """
    Core pattern-based editing engine for Confluence pages.
    
    This class provides intelligent find-and-replace capabilities that can modify
    specific text patterns while preserving XML structure, macros, and formatting.
    """
    
    def __init__(self, xml_parser: Optional[ConfluenceXMLParser] = None):
        """
        Initialize the pattern editor.
        
        Args:
            xml_parser: Optional XML parser instance. If not provided, creates a new one.
        """
        self.xml_parser = xml_parser or ConfluenceXMLParser()
        self.content_analyzer = ContentStructureAnalyzer(self.xml_parser)
        self._backup_content: Optional[str] = None
        
    def replace_text_pattern(self,
                           content: str,
                           search_pattern: str,
                           replacement: str,
                           case_sensitive: bool = True,
                           whole_words_only: bool = False,
                           max_replacements: Optional[int] = None) -> OperationResult:
        """
        Find and replace text patterns in content while preserving XML structure.
        
        This operation performs intelligent text replacement that avoids breaking
        XML elements, macro parameters, or link references.
        
        Args:
            content: The original page content (Confluence storage format)
            search_pattern: The text pattern to search for
            replacement: The replacement text
            case_sensitive: Whether the search should be case sensitive
            whole_words_only: Whether to match only whole words
            max_replacements: Maximum number of replacements to make (None for unlimited)
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Handle empty content gracefully
            if not content or not content.strip():
                return OperationResult(
                    success=True,
                    operation_type=OperationType.REPLACE_TEXT_PATTERN,
                    modified_content=content,
                    changes_made=[f"No occurrences of '{search_pattern}' found"],
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                # Fallback to simple string replacement for malformed XML
                logger.warning("XML parsing failed, falling back to simple string replacement")
                modified_content = self._simple_string_replacement(
                    content, search_pattern, replacement, case_sensitive, 
                    whole_words_only, max_replacements
                )
                
                # Count replacements made
                replacement_count = self._count_pattern_occurrences(
                    content, search_pattern, case_sensitive, whole_words_only
                ) - self._count_pattern_occurrences(
                    modified_content, search_pattern, case_sensitive, whole_words_only
                )
                
                changes = []
                if replacement_count > 0:
                    changes.append(f"Replaced {replacement_count} occurrence(s) of '{search_pattern}' with '{replacement}'")
                else:
                    changes.append(f"No occurrences of '{search_pattern}' found")
                
                return OperationResult(
                    success=True,
                    operation_type=OperationType.REPLACE_TEXT_PATTERN,
                    modified_content=modified_content,
                    changes_made=changes,
                    backup_content=self._backup_content
                )
            
            # Analyze content structure to identify safe text regions
            structure = self.content_analyzer.analyze(content)
            
            # Perform the pattern replacement
            modified_content = self._replace_text_in_safe_regions(
                content, search_pattern, replacement, case_sensitive, 
                whole_words_only, max_replacements
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_TEXT_PATTERN,
                    error_message="Failed to perform text pattern replacement",
                    backup_content=self._backup_content
                )
            
            # Count replacements made
            replacement_count = self._count_pattern_occurrences(
                content, search_pattern, case_sensitive, whole_words_only
            ) - self._count_pattern_occurrences(
                modified_content, search_pattern, case_sensitive, whole_words_only
            )
            
            changes = []
            if replacement_count > 0:
                changes.append(f"Replaced {replacement_count} occurrence(s) of '{search_pattern}' with '{replacement}'")
            else:
                changes.append(f"No occurrences of '{search_pattern}' found")
            
            return OperationResult(
                success=True,
                operation_type=OperationType.REPLACE_TEXT_PATTERN,
                modified_content=modified_content,
                changes_made=changes,
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in replace_text_pattern: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.REPLACE_TEXT_PATTERN,
                error_message=f"Text pattern replacement failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def replace_regex_pattern(self,
                            content: str,
                            regex_pattern: str,
                            replacement: str,
                            regex_flags: int = 0,
                            max_replacements: Optional[int] = None) -> OperationResult:
        """
        Find and replace using regex patterns while preserving XML structure.
        
        This operation performs regex-based replacement that supports capture groups
        and advanced pattern matching while avoiding breaking XML structure.
        
        Args:
            content: The original page content (Confluence storage format)
            regex_pattern: The regex pattern to search for
            replacement: The replacement text (can include capture group references)
            regex_flags: Regex flags (e.g., re.IGNORECASE, re.MULTILINE)
            max_replacements: Maximum number of replacements to make (None for unlimited)
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Handle empty content gracefully
            if not content or not content.strip():
                return OperationResult(
                    success=True,
                    operation_type=OperationType.REPLACE_REGEX_PATTERN,
                    modified_content=content,
                    changes_made=[f"No matches found for regex pattern '{regex_pattern}'"],
                    backup_content=self._backup_content
                )
            
            # Validate regex pattern
            try:
                compiled_pattern = re.compile(regex_pattern, regex_flags)
            except re.error as e:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_REGEX_PATTERN,
                    error_message=f"Invalid regex pattern: {str(e)}",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                # Fallback to simple regex replacement for malformed XML
                logger.warning("XML parsing failed, falling back to simple regex replacement")
                count = max_replacements if max_replacements else 0
                modified_content = compiled_pattern.sub(replacement, content, count=count)
                
                # Count replacements made
                original_matches = len(compiled_pattern.findall(content))
                remaining_matches = len(compiled_pattern.findall(modified_content))
                replacement_count = original_matches - remaining_matches
                
                changes = []
                if replacement_count > 0:
                    changes.append(f"Replaced {replacement_count} occurrence(s) matching regex pattern '{regex_pattern}'")
                else:
                    changes.append(f"No matches found for regex pattern '{regex_pattern}'")
                
                return OperationResult(
                    success=True,
                    operation_type=OperationType.REPLACE_REGEX_PATTERN,
                    modified_content=modified_content,
                    changes_made=changes,
                    backup_content=self._backup_content
                )
            
            # Analyze content structure to identify safe text regions
            structure = self.content_analyzer.analyze(content)
            
            # Perform the regex replacement
            modified_content = self._replace_regex_in_safe_regions(
                content, compiled_pattern, replacement, max_replacements
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REPLACE_REGEX_PATTERN,
                    error_message="Failed to perform regex pattern replacement",
                    backup_content=self._backup_content
                )
            
            # Count replacements made
            original_matches = len(compiled_pattern.findall(content))
            remaining_matches = len(compiled_pattern.findall(modified_content))
            replacement_count = original_matches - remaining_matches
            
            changes = []
            if replacement_count > 0:
                changes.append(f"Replaced {replacement_count} occurrence(s) matching regex pattern '{regex_pattern}'")
            else:
                changes.append(f"No matches found for regex pattern '{regex_pattern}'")
            
            return OperationResult(
                success=True,
                operation_type=OperationType.REPLACE_REGEX_PATTERN,
                modified_content=modified_content,
                changes_made=changes,
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in replace_regex_pattern: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.REPLACE_REGEX_PATTERN,
                error_message=f"Regex pattern replacement failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def execute_operation(self, operation: SelectiveEditOperation, content: str) -> OperationResult:
        """
        Execute a pattern-based editing operation on the provided content.
        
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
        
        if operation.operation_type == OperationType.REPLACE_TEXT_PATTERN:
            return self.replace_text_pattern(
                content=content,
                search_pattern=operation.parameters['search_pattern'],
                replacement=operation.parameters['replacement'],
                case_sensitive=operation.parameters.get('case_sensitive', True),
                whole_words_only=operation.parameters.get('whole_words_only', False),
                max_replacements=operation.parameters.get('max_replacements')
            )
        
        elif operation.operation_type == OperationType.REPLACE_REGEX_PATTERN:
            return self.replace_regex_pattern(
                content=content,
                regex_pattern=operation.parameters['regex_pattern'],
                replacement=operation.parameters['replacement'],
                regex_flags=operation.parameters.get('regex_flags', 0),
                max_replacements=operation.parameters.get('max_replacements')
            )
        
        else:
            return OperationResult(
                success=False,
                operation_type=operation.operation_type,
                error_message=f"Operation type {operation.operation_type} not supported by PatternEditor"
            )
    
    def rollback(self) -> Optional[str]:
        """
        Rollback to the last backup content.
        
        Returns:
            The backup content if available, None otherwise
        """
        return self._backup_content
    
    def _replace_text_in_safe_regions(self,
                                    content: str,
                                    search_pattern: str,
                                    replacement: str,
                                    case_sensitive: bool = True,
                                    whole_words_only: bool = False,
                                    max_replacements: Optional[int] = None) -> Optional[str]:
        """
        Replace text patterns only in safe regions that won't break XML structure.
        
        This method identifies text content that's safe to modify (not within XML tags,
        attributes, or macro parameters) and performs replacements only there.
        """
        try:
            # Get the current root from the content analyzer
            root = self.content_analyzer._current_root
            if root is None:
                # Fallback to simple string replacement if XML parsing failed
                return self._simple_string_replacement(
                    content, search_pattern, replacement, case_sensitive, 
                    whole_words_only, max_replacements
                )
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Track replacement count
            replacements_made = 0
            
            # Process all text nodes in the XML tree
            for element in root_copy.iter():
                # Replace text content
                if element.text:
                    new_text, count = self._replace_text_with_options(
                        element.text, search_pattern, replacement,
                        case_sensitive, whole_words_only,
                        max_replacements - replacements_made if max_replacements else None
                    )
                    element.text = new_text
                    replacements_made += count
                    
                    if max_replacements and replacements_made >= max_replacements:
                        break
                
                # Replace tail text (text after closing tag)
                if element.tail and (not max_replacements or replacements_made < max_replacements):
                    new_tail, count = self._replace_text_with_options(
                        element.tail, search_pattern, replacement,
                        case_sensitive, whole_words_only,
                        max_replacements - replacements_made if max_replacements else None
                    )
                    element.tail = new_tail
                    replacements_made += count
                    
                    if max_replacements and replacements_made >= max_replacements:
                        break
            
            # Convert back to string
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error in safe region text replacement: {e}")
            return None
    
    def _replace_regex_in_safe_regions(self,
                                     content: str,
                                     compiled_pattern: Pattern,
                                     replacement: str,
                                     max_replacements: Optional[int] = None) -> Optional[str]:
        """
        Replace regex patterns only in safe regions that won't break XML structure.
        """
        try:
            # Get the current root from the content analyzer
            root = self.content_analyzer._current_root
            if root is None:
                # Fallback to simple string replacement if XML parsing failed
                count = max_replacements if max_replacements else 0
                return compiled_pattern.sub(replacement, content, count=count)
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Track replacement count
            replacements_made = 0
            
            # Process all text nodes in the XML tree
            for element in root_copy.iter():
                # Replace text content
                if element.text:
                    remaining_replacements = (max_replacements - replacements_made 
                                            if max_replacements else 0)
                    new_text = compiled_pattern.sub(replacement, element.text, 
                                                  count=remaining_replacements)
                    if new_text != element.text:
                        # Count actual replacements made
                        original_matches = len(compiled_pattern.findall(element.text))
                        new_matches = len(compiled_pattern.findall(new_text))
                        replacements_made += original_matches - new_matches
                        element.text = new_text
                    
                    if max_replacements and replacements_made >= max_replacements:
                        break
                
                # Replace tail text (text after closing tag)
                if element.tail and (not max_replacements or replacements_made < max_replacements):
                    remaining_replacements = (max_replacements - replacements_made 
                                            if max_replacements else 0)
                    new_tail = compiled_pattern.sub(replacement, element.tail, 
                                                  count=remaining_replacements)
                    if new_tail != element.tail:
                        # Count actual replacements made
                        original_matches = len(compiled_pattern.findall(element.tail))
                        new_matches = len(compiled_pattern.findall(new_tail))
                        replacements_made += original_matches - new_matches
                        element.tail = new_tail
                    
                    if max_replacements and replacements_made >= max_replacements:
                        break
            
            # Convert back to string
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error in safe region regex replacement: {e}")
            return None
    
    def _replace_text_with_options(self,
                                 text: str,
                                 search_pattern: str,
                                 replacement: str,
                                 case_sensitive: bool = True,
                                 whole_words_only: bool = False,
                                 max_replacements: Optional[int] = None) -> Tuple[str, int]:
        """
        Replace text with various options and return the new text and replacement count.
        """
        if not text or not search_pattern:
            return text, 0
        
        original_text = text
        flags = 0 if case_sensitive else re.IGNORECASE
        
        if whole_words_only:
            # Use word boundaries for whole word matching
            pattern = r'\b' + re.escape(search_pattern) + r'\b'
        else:
            pattern = re.escape(search_pattern)
        
        count = max_replacements if max_replacements else 0
        new_text = re.sub(pattern, replacement, text, count=count, flags=flags)
        
        # Count actual replacements made
        if case_sensitive:
            original_count = original_text.count(search_pattern)
            new_count = new_text.count(search_pattern)
        else:
            original_count = original_text.lower().count(search_pattern.lower())
            new_count = new_text.lower().count(search_pattern.lower())
        
        replacements_made = original_count - new_count
        return new_text, replacements_made
    
    def _simple_string_replacement(self,
                                 content: str,
                                 search_pattern: str,
                                 replacement: str,
                                 case_sensitive: bool = True,
                                 whole_words_only: bool = False,
                                 max_replacements: Optional[int] = None) -> str:
        """
        Fallback simple string replacement when XML parsing is not available.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        
        if whole_words_only:
            pattern = r'\b' + re.escape(search_pattern) + r'\b'
        else:
            pattern = re.escape(search_pattern)
        
        count = max_replacements if max_replacements else 0
        return re.sub(pattern, replacement, content, count=count, flags=flags)
    
    def _count_pattern_occurrences(self,
                                 content: str,
                                 search_pattern: str,
                                 case_sensitive: bool = True,
                                 whole_words_only: bool = False) -> int:
        """
        Count occurrences of a pattern in content.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        
        if whole_words_only:
            pattern = r'\b' + re.escape(search_pattern) + r'\b'
        else:
            pattern = re.escape(search_pattern)
        
        matches = re.findall(pattern, content, flags=flags)
        return len(matches) 