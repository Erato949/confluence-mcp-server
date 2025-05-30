"""
Confluence MCP Server v2.0 - Selective Page Editing System

This module provides intelligent selective editing capabilities for Confluence pages,
allowing surgical modifications to page content without requiring full page replacement.

Key Components:
- ConfluenceXMLParser: Safe parsing and manipulation of Confluence Storage Format
- ContentStructureAnalyzer: Analysis of page structure and content organization  
- SelectiveContentEditor: Transaction-based editing with rollback capabilities
- MacroPreservationHandler: Protection of macros and custom elements during edits

Version: 2.0.0
Authors: Confluence MCP Server Team
"""

__version__ = "2.0.0"
__all__ = [
    "ConfluenceXMLParser",
    "ContentStructureAnalyzer", 
    "SelectiveContentEditor",
    "MacroPreservationHandler",
    "SelectiveEditOperation",
    "EditingError",
]

# Import main classes when available
try:
    from .xml_parser import ConfluenceXMLParser
    from .content_analyzer import ContentStructureAnalyzer
    from .content_editor import SelectiveContentEditor
    from .macro_handler import MacroPreservationHandler
    from .operations import SelectiveEditOperation
    from .exceptions import EditingError
except ImportError:
    # Classes not yet implemented - this is expected during development
    pass 