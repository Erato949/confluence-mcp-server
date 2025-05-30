"""
Operation definitions for Confluence Selective Editing System

This module defines the various types of selective editing operations that can be
performed on Confluence pages, along with their parameters and validation logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass


class OperationType(Enum):
    """Enumeration of supported selective editing operation types."""
    
    # Basic operations
    APPEND_TO_END = "append_to_end"
    PREPEND_TO_BEGINNING = "prepend_to_beginning"
    REPLACE_ENTIRE_CONTENT = "replace_entire_content"
    
    # Section-based operations
    REPLACE_SECTION = "replace_section"
    INSERT_AFTER_HEADING = "insert_after_heading"
    UPDATE_HEADING_CONTENT = "update_heading_content"
    
    # Pattern-based operations
    REPLACE_TEXT_PATTERN = "replace_text_pattern"
    REPLACE_REGEX_PATTERN = "replace_regex_pattern"
    
    # Structural operations
    UPDATE_TABLE_CELL = "update_table_cell"
    ADD_TABLE_ROW = "add_table_row"
    UPDATE_TABLE_COLUMN = "update_table_column"
    ADD_LIST_ITEM = "add_list_item"
    UPDATE_LIST_ITEM = "update_list_item"
    REORDER_LIST_ITEMS = "reorder_list_items"


@dataclass
class OperationResult:
    """Result of a selective editing operation."""
    
    success: bool
    operation_type: OperationType
    modified_content: Optional[str] = None
    changes_made: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    error_message: Optional[str] = None
    backup_content: Optional[str] = None


class SelectiveEditOperation(ABC):
    """Abstract base class for all selective editing operations."""
    
    def __init__(self, operation_type: OperationType, **kwargs):
        self.operation_type = operation_type
        self.parameters = kwargs
        
    @abstractmethod
    def validate_parameters(self) -> bool:
        """Validate that all required parameters are present and valid."""
        pass
        
    @abstractmethod
    def get_required_parameters(self) -> List[str]:
        """Return list of required parameter names for this operation."""
        pass
        
    @abstractmethod
    def get_optional_parameters(self) -> List[str]:
        """Return list of optional parameter names for this operation."""
        pass
        
    def __str__(self):
        return f"{self.operation_type.value}({', '.join(f'{k}={v}' for k, v in self.parameters.items())})"


class AppendToEndOperation(SelectiveEditOperation):
    """Operation to append content to the end of a page."""
    
    def __init__(self, content: str, **kwargs):
        super().__init__(OperationType.APPEND_TO_END, content=content, **kwargs)
        
    def validate_parameters(self) -> bool:
        return bool(self.parameters.get('content'))
        
    def get_required_parameters(self) -> List[str]:
        return ['content']
        
    def get_optional_parameters(self) -> List[str]:
        return ['separator']


class PrependToBeginningOperation(SelectiveEditOperation):
    """Operation to prepend content to the beginning of a page."""
    
    def __init__(self, content: str, **kwargs):
        super().__init__(OperationType.PREPEND_TO_BEGINNING, content=content, **kwargs)
        
    def validate_parameters(self) -> bool:
        return bool(self.parameters.get('content'))
        
    def get_required_parameters(self) -> List[str]:
        return ['content']
        
    def get_optional_parameters(self) -> List[str]:
        return ['separator']


class ReplaceSectionOperation(SelectiveEditOperation):
    """Operation to replace content under a specific heading."""
    
    def __init__(self, heading: str, new_content: str, **kwargs):
        super().__init__(OperationType.REPLACE_SECTION, heading=heading, new_content=new_content, **kwargs)
        
    def validate_parameters(self) -> bool:
        return bool(self.parameters.get('heading')) and bool(self.parameters.get('new_content'))
        
    def get_required_parameters(self) -> List[str]:
        return ['heading', 'new_content']
        
    def get_optional_parameters(self) -> List[str]:
        return ['heading_level', 'exact_match', 'case_sensitive']


class InsertAfterHeadingOperation(SelectiveEditOperation):
    """Operation to insert content after a specific heading."""
    
    def __init__(self, heading: str, content: str, **kwargs):
        super().__init__(OperationType.INSERT_AFTER_HEADING, heading=heading, content=content, **kwargs)
        
    def validate_parameters(self) -> bool:
        return bool(self.parameters.get('heading')) and bool(self.parameters.get('content'))
        
    def get_required_parameters(self) -> List[str]:
        return ['heading', 'content']
        
    def get_optional_parameters(self) -> List[str]:
        return ['heading_level', 'exact_match', 'case_sensitive']


class ReplaceTextPatternOperation(SelectiveEditOperation):
    """Operation to find and replace text patterns."""
    
    def __init__(self, search_pattern: str, replacement: str, **kwargs):
        super().__init__(OperationType.REPLACE_TEXT_PATTERN, search_pattern=search_pattern, replacement=replacement, **kwargs)
        
    def validate_parameters(self) -> bool:
        return bool(self.parameters.get('search_pattern')) and self.parameters.get('replacement') is not None
        
    def get_required_parameters(self) -> List[str]:
        return ['search_pattern', 'replacement']
        
    def get_optional_parameters(self) -> List[str]:
        return ['case_sensitive', 'whole_words_only', 'max_replacements']


class ReplaceRegexPatternOperation(SelectiveEditOperation):
    """Operation to find and replace using regex patterns."""
    
    def __init__(self, regex_pattern: str, replacement: str, **kwargs):
        super().__init__(OperationType.REPLACE_REGEX_PATTERN, regex_pattern=regex_pattern, replacement=replacement, **kwargs)
        
    def validate_parameters(self) -> bool:
        return bool(self.parameters.get('regex_pattern')) and self.parameters.get('replacement') is not None
        
    def get_required_parameters(self) -> List[str]:
        return ['regex_pattern', 'replacement']
        
    def get_optional_parameters(self) -> List[str]:
        return ['regex_flags', 'max_replacements']


class UpdateTableCellOperation(SelectiveEditOperation):
    """Operation to update a specific table cell."""
    
    def __init__(self, table_index: int, row: int, column: int, new_value: str, **kwargs):
        super().__init__(OperationType.UPDATE_TABLE_CELL, 
                         table_index=table_index, row=row, column=column, new_value=new_value, **kwargs)
        
    def validate_parameters(self) -> bool:
        params = self.parameters
        return (isinstance(params.get('table_index'), int) and params['table_index'] >= 0 and
                isinstance(params.get('row'), int) and params['row'] >= 0 and
                isinstance(params.get('column'), int) and params['column'] >= 0 and
                params.get('new_value') is not None)
        
    def get_required_parameters(self) -> List[str]:
        return ['table_index', 'row', 'column', 'new_value']
        
    def get_optional_parameters(self) -> List[str]:
        return ['header_rows']


class AddListItemOperation(SelectiveEditOperation):
    """Operation to add an item to an existing list."""
    
    def __init__(self, list_index: int, item_content: str, **kwargs):
        super().__init__(OperationType.ADD_LIST_ITEM, list_index=list_index, item_content=item_content, **kwargs)
        
    def validate_parameters(self) -> bool:
        params = self.parameters
        return (isinstance(params.get('list_index'), int) and params['list_index'] >= 0 and
                bool(params.get('item_content')))
        
    def get_required_parameters(self) -> List[str]:
        return ['list_index', 'item_content']
        
    def get_optional_parameters(self) -> List[str]:
        return ['position', 'list_type']


class AddTableRowOperation(SelectiveEditOperation):
    """Operation to add a new row to an existing table."""
    
    def __init__(self, table_index: int, row_data: List[str], **kwargs):
        super().__init__(OperationType.ADD_TABLE_ROW, 
                         table_index=table_index, row_data=row_data, **kwargs)
        
    def validate_parameters(self) -> bool:
        params = self.parameters
        return (isinstance(params.get('table_index'), int) and params['table_index'] >= 0 and
                isinstance(params.get('row_data'), list) and len(params['row_data']) > 0)
        
    def get_required_parameters(self) -> List[str]:
        return ['table_index', 'row_data']
        
    def get_optional_parameters(self) -> List[str]:
        return ['insert_position']


class UpdateTableColumnOperation(SelectiveEditOperation):
    """Operation to update an entire column in a table."""
    
    def __init__(self, table_index: int, column_index: int, column_data: List[str], **kwargs):
        super().__init__(OperationType.UPDATE_TABLE_COLUMN,
                         table_index=table_index, column_index=column_index, column_data=column_data, **kwargs)
        
    def validate_parameters(self) -> bool:
        params = self.parameters
        return (isinstance(params.get('table_index'), int) and params['table_index'] >= 0 and
                isinstance(params.get('column_index'), int) and params['column_index'] >= 0 and
                isinstance(params.get('column_data'), list) and len(params['column_data']) > 0)
        
    def get_required_parameters(self) -> List[str]:
        return ['table_index', 'column_index', 'column_data']
        
    def get_optional_parameters(self) -> List[str]:
        return []


class UpdateListItemOperation(SelectiveEditOperation):
    """Operation to update a specific list item."""
    
    def __init__(self, list_index: int, item_index: int, new_content: str, **kwargs):
        super().__init__(OperationType.UPDATE_LIST_ITEM,
                         list_index=list_index, item_index=item_index, new_content=new_content, **kwargs)
        
    def validate_parameters(self) -> bool:
        params = self.parameters
        return (isinstance(params.get('list_index'), int) and params['list_index'] >= 0 and
                isinstance(params.get('item_index'), int) and params['item_index'] >= 0 and
                bool(params.get('new_content')))
        
    def get_required_parameters(self) -> List[str]:
        return ['list_index', 'item_index', 'new_content']
        
    def get_optional_parameters(self) -> List[str]:
        return []


class ReorderListItemsOperation(SelectiveEditOperation):
    """Operation to reorder items in a list."""
    
    def __init__(self, list_index: int, new_order: List[int], **kwargs):
        super().__init__(OperationType.REORDER_LIST_ITEMS,
                         list_index=list_index, new_order=new_order, **kwargs)
        
    def validate_parameters(self) -> bool:
        params = self.parameters
        return (isinstance(params.get('list_index'), int) and params['list_index'] >= 0 and
                isinstance(params.get('new_order'), list) and len(params['new_order']) > 0 and
                all(isinstance(i, int) and i >= 0 for i in params['new_order']))
        
    def get_required_parameters(self) -> List[str]:
        return ['list_index', 'new_order']
        
    def get_optional_parameters(self) -> List[str]:
        return []


def create_operation(operation_type: str, **kwargs) -> SelectiveEditOperation:
    """Factory function to create operation instances from type string and parameters."""
    
    operation_classes = {
        OperationType.APPEND_TO_END.value: AppendToEndOperation,
        OperationType.PREPEND_TO_BEGINNING.value: PrependToBeginningOperation,
        OperationType.REPLACE_SECTION.value: ReplaceSectionOperation,
        OperationType.INSERT_AFTER_HEADING.value: InsertAfterHeadingOperation,
        OperationType.REPLACE_TEXT_PATTERN.value: ReplaceTextPatternOperation,
        OperationType.REPLACE_REGEX_PATTERN.value: ReplaceRegexPatternOperation,
        OperationType.UPDATE_TABLE_CELL.value: UpdateTableCellOperation,
        OperationType.ADD_TABLE_ROW.value: AddTableRowOperation,
        OperationType.UPDATE_TABLE_COLUMN.value: UpdateTableColumnOperation,
        OperationType.ADD_LIST_ITEM.value: AddListItemOperation,
        OperationType.UPDATE_LIST_ITEM.value: UpdateListItemOperation,
        OperationType.REORDER_LIST_ITEMS.value: ReorderListItemsOperation,
    }
    
    if operation_type not in operation_classes:
        raise ValueError(f"Unknown operation type: {operation_type}")
        
    operation_class = operation_classes[operation_type]
    return operation_class(**kwargs) 