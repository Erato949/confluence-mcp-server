"""
Exceptions for Confluence Selective Editing System

This module defines custom exceptions used throughout the selective editing system
to provide clear error messages and enable proper error handling and rollback.
"""

from typing import Optional, Dict, Any


class EditingError(Exception):
    """Base exception for all selective editing operations."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}
        
    def __str__(self):
        base_msg = super().__str__()
        if self.operation:
            base_msg = f"[{self.operation}] {base_msg}"
        return base_msg


class XMLParsingError(EditingError):
    """Raised when XML parsing fails."""
    
    def __init__(self, message: str, xml_content: Optional[str] = None, line_number: Optional[int] = None):
        super().__init__(message, "XML_PARSING")
        self.xml_content = xml_content
        self.line_number = line_number


class ContentStructureError(EditingError):
    """Raised when content structure analysis fails or finds unexpected structure."""
    
    def __init__(self, message: str, expected_structure: Optional[str] = None, found_structure: Optional[str] = None):
        super().__init__(message, "CONTENT_STRUCTURE")
        self.expected_structure = expected_structure
        self.found_structure = found_structure


class SectionNotFoundError(EditingError):
    """Raised when a target section cannot be found in the content."""
    
    def __init__(self, section_identifier: str, search_type: str = "heading"):
        message = f"Section not found: {section_identifier} (search type: {search_type})"
        super().__init__(message, "SECTION_NOT_FOUND")
        self.section_identifier = section_identifier
        self.search_type = search_type


class MacroIntegrityError(EditingError):
    """Raised when macro structure would be compromised by an edit operation."""
    
    def __init__(self, message: str, macro_name: Optional[str] = None, macro_id: Optional[str] = None):
        super().__init__(message, "MACRO_INTEGRITY")
        self.macro_name = macro_name
        self.macro_id = macro_id


class ValidationError(EditingError):
    """Raised when content validation fails before or after an edit operation."""
    
    def __init__(self, message: str, validation_type: str, failed_content: Optional[str] = None):
        super().__init__(message, "VALIDATION")
        self.validation_type = validation_type
        self.failed_content = failed_content


class RollbackError(EditingError):
    """Raised when a rollback operation fails."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "ROLLBACK")
        self.original_error = original_error


class OperationNotSupportedError(EditingError):
    """Raised when an operation is not supported for the given content type or structure."""
    
    def __init__(self, operation: str, reason: str, content_type: Optional[str] = None):
        message = f"Operation '{operation}' not supported: {reason}"
        super().__init__(message, "OPERATION_NOT_SUPPORTED")
        self.operation_name = operation
        self.reason = reason
        self.content_type = content_type


class ConcurrentEditError(EditingError):
    """Raised when concurrent edits are detected and cannot be safely merged."""
    
    def __init__(self, message: str, current_version: Optional[int] = None, expected_version: Optional[int] = None):
        super().__init__(message, "CONCURRENT_EDIT")
        self.current_version = current_version
        self.expected_version = expected_version


class ContentTooComplexError(EditingError):
    """Raised when content is too complex to safely parse or edit."""
    
    def __init__(self, message: str, complexity_metric: Optional[str] = None, threshold: Optional[str] = None):
        super().__init__(message, "CONTENT_TOO_COMPLEX")
        self.complexity_metric = complexity_metric
        self.threshold = threshold 