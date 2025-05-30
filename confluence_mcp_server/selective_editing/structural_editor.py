"""
Structural Editor for Confluence Selective Editing System

This module implements advanced structural editing operations for tables and lists
while preserving XML structure, macros, and formatting.

Key Features:
- Table cell editing with row/column targeting
- Table row insertion and modification
- List item manipulation and reordering
- Smart structure detection and preservation
- Integration with ContentStructureAnalyzer
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
import copy

from .xml_parser import ConfluenceXMLParser
from .content_analyzer import ContentStructureAnalyzer
from .operations import (
    OperationType, OperationResult, SelectiveEditOperation
)
from .exceptions import (
    ContentStructureError, XMLParsingError, EditingError
)

logger = logging.getLogger(__name__)


class StructuralEditor:
    """
    Core structural editing engine for Confluence tables and lists.
    
    This class provides intelligent table and list manipulation capabilities
    that preserve XML structure, macros, and formatting while allowing
    precise modifications to structural elements.
    """
    
    def __init__(self, xml_parser: Optional[ConfluenceXMLParser] = None):
        """
        Initialize the structural editor.
        
        Args:
            xml_parser: Optional XML parser instance. If not provided, creates a new one.
        """
        self.xml_parser = xml_parser or ConfluenceXMLParser()
        self.content_analyzer = ContentStructureAnalyzer(self.xml_parser)
        self._backup_content: Optional[str] = None
        
    def update_table_cell(self,
                         content: str,
                         table_index: int,
                         row_index: int,
                         column_index: int,
                         new_cell_content: str) -> OperationResult:
        """
        Update a specific table cell with new content.
        
        Args:
            content: The original page content (Confluence storage format)
            table_index: Zero-based index of the table (0 for first table)
            row_index: Zero-based index of the row within the table
            column_index: Zero-based index of the column within the row
            new_cell_content: New content for the cell (can include HTML)
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Handle empty content
            if not content or not content.strip():
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_TABLE_CELL,
                    error_message="Cannot update table cell in empty content",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_TABLE_CELL,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Find and update the table cell
            modified_content = self._update_table_cell_content(
                content, table_index, row_index, column_index, new_cell_content
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_TABLE_CELL,
                    error_message=f"Failed to update table cell at table[{table_index}], row[{row_index}], column[{column_index}]",
                    backup_content=self._backup_content
                )
            
            return OperationResult(
                success=True,
                operation_type=OperationType.UPDATE_TABLE_CELL,
                modified_content=modified_content,
                changes_made=[f"Updated table[{table_index}] row[{row_index}] column[{column_index}] with new content"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in update_table_cell: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.UPDATE_TABLE_CELL,
                error_message=f"Table cell update failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def add_table_row(self,
                     content: str,
                     table_index: int,
                     row_data: List[str],
                     insert_position: Optional[int] = None) -> OperationResult:
        """
        Add a new row to an existing table.
        
        Args:
            content: The original page content (Confluence storage format)
            table_index: Zero-based index of the table to modify
            row_data: List of cell contents for the new row
            insert_position: Position to insert row (None = append to end)
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Validate input
            if not row_data:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.ADD_TABLE_ROW,
                    error_message="Row data cannot be empty",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.ADD_TABLE_ROW,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Add the table row
            modified_content = self._add_table_row_content(
                content, table_index, row_data, insert_position
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.ADD_TABLE_ROW,
                    error_message=f"Failed to add row to table[{table_index}]",
                    backup_content=self._backup_content
                )
            
            position_desc = f"at position {insert_position}" if insert_position is not None else "at end"
            return OperationResult(
                success=True,
                operation_type=OperationType.ADD_TABLE_ROW,
                modified_content=modified_content,
                changes_made=[f"Added new row to table[{table_index}] {position_desc} with {len(row_data)} cells"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in add_table_row: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.ADD_TABLE_ROW,
                error_message=f"Table row addition failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def update_table_column(self,
                           content: str,
                           table_index: int,
                           column_index: int,
                           column_data: List[str]) -> OperationResult:
        """
        Update an entire column in a table with new data.
        
        Args:
            content: The original page content (Confluence storage format)
            table_index: Zero-based index of the table to modify
            column_index: Zero-based index of the column to update
            column_data: List of new cell contents for the column
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Validate input
            if not column_data:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_TABLE_COLUMN,
                    error_message="Column data cannot be empty",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_TABLE_COLUMN,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Update the table column
            modified_content = self._update_table_column_content(
                content, table_index, column_index, column_data
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_TABLE_COLUMN,
                    error_message=f"Failed to update column[{column_index}] in table[{table_index}]",
                    backup_content=self._backup_content
                )
            
            return OperationResult(
                success=True,
                operation_type=OperationType.UPDATE_TABLE_COLUMN,
                modified_content=modified_content,
                changes_made=[f"Updated column[{column_index}] in table[{table_index}] with {len(column_data)} cells"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in update_table_column: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.UPDATE_TABLE_COLUMN,
                error_message=f"Table column update failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def add_list_item(self,
                     content: str,
                     list_index: int,
                     new_item_content: str,
                     insert_position: Optional[int] = None) -> OperationResult:
        """
        Add a new item to an existing list.
        
        Args:
            content: The original page content (Confluence storage format)
            list_index: Zero-based index of the list to modify (0 for first list)
            new_item_content: Content for the new list item
            insert_position: Position to insert item (None = append to end)
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Validate input
            if not new_item_content or not new_item_content.strip():
                return OperationResult(
                    success=False,
                    operation_type=OperationType.ADD_LIST_ITEM,
                    error_message="List item content cannot be empty",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.ADD_LIST_ITEM,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Add the list item
            modified_content = self._add_list_item_content(
                content, list_index, new_item_content, insert_position
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.ADD_LIST_ITEM,
                    error_message=f"Failed to add item to list[{list_index}]",
                    backup_content=self._backup_content
                )
            
            position_desc = f"at position {insert_position}" if insert_position is not None else "at end"
            return OperationResult(
                success=True,
                operation_type=OperationType.ADD_LIST_ITEM,
                modified_content=modified_content,
                changes_made=[f"Added new item to list[{list_index}] {position_desc}"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in add_list_item: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.ADD_LIST_ITEM,
                error_message=f"List item addition failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def update_list_item(self,
                        content: str,
                        list_index: int,
                        item_index: int,
                        new_item_content: str) -> OperationResult:
        """
        Update a specific list item with new content.
        
        Args:
            content: The original page content (Confluence storage format)
            list_index: Zero-based index of the list
            item_index: Zero-based index of the item within the list
            new_item_content: New content for the list item
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Validate input
            if not new_item_content or not new_item_content.strip():
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_LIST_ITEM,
                    error_message="List item content cannot be empty",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_LIST_ITEM,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Update the list item
            modified_content = self._update_list_item_content(
                content, list_index, item_index, new_item_content
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.UPDATE_LIST_ITEM,
                    error_message=f"Failed to update item[{item_index}] in list[{list_index}]",
                    backup_content=self._backup_content
                )
            
            return OperationResult(
                success=True,
                operation_type=OperationType.UPDATE_LIST_ITEM,
                modified_content=modified_content,
                changes_made=[f"Updated item[{item_index}] in list[{list_index}]"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in update_list_item: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.UPDATE_LIST_ITEM,
                error_message=f"List item update failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def reorder_list_items(self,
                          content: str,
                          list_index: int,
                          new_order: List[int]) -> OperationResult:
        """
        Reorder items in a list according to the specified order.
        
        Args:
            content: The original page content (Confluence storage format)
            list_index: Zero-based index of the list to reorder
            new_order: List of item indices in the desired order
            
        Returns:
            OperationResult with success status and modified content
        """
        try:
            # Create backup
            self._backup_content = content
            
            # Validate input
            if not new_order:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REORDER_LIST_ITEMS,
                    error_message="New order cannot be empty",
                    backup_content=self._backup_content
                )
            
            # Parse the content
            if not self.xml_parser.parse(content):
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REORDER_LIST_ITEMS,
                    error_message="Failed to parse XML content",
                    backup_content=self._backup_content
                )
            
            # Reorder the list items
            modified_content = self._reorder_list_items_content(
                content, list_index, new_order
            )
            
            if modified_content is None:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.REORDER_LIST_ITEMS,
                    error_message=f"Failed to reorder items in list[{list_index}]",
                    backup_content=self._backup_content
                )
            
            return OperationResult(
                success=True,
                operation_type=OperationType.REORDER_LIST_ITEMS,
                modified_content=modified_content,
                changes_made=[f"Reordered {len(new_order)} items in list[{list_index}]"],
                backup_content=self._backup_content
            )
            
        except Exception as e:
            logger.error(f"Error in reorder_list_items: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.REORDER_LIST_ITEMS,
                error_message=f"List item reordering failed: {str(e)}",
                backup_content=self._backup_content
            )
    
    def rollback(self) -> Optional[str]:
        """
        Rollback to the last backup content.
        
        Returns:
            The backup content if available, None otherwise
        """
        return self._backup_content
    
    # Internal implementation methods
    
    def _update_table_cell_content(self,
                                  content: str,
                                  table_index: int,
                                  row_index: int,
                                  column_index: int,
                                  new_cell_content: str) -> Optional[str]:
        """Update specific table cell content."""
        try:
            # Analyze the content first to set the _current_root
            structure = self.content_analyzer.analyze(content)
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find all tables
            tables = root_copy.findall(".//table")
            if table_index >= len(tables):
                logger.error(f"Table index {table_index} out of range (found {len(tables)} tables)")
                return None
            
            target_table = tables[table_index]
            
            # Find all rows in the table
            rows = target_table.findall(".//tr")
            if row_index >= len(rows):
                logger.error(f"Row index {row_index} out of range (found {len(rows)} rows)")
                return None
            
            target_row = rows[row_index]
            
            # Find all cells in the row (both td and th)
            cells = target_row.findall("td") + target_row.findall("th")
            if column_index >= len(cells):
                logger.error(f"Column index {column_index} out of range (found {len(cells)} cells)")
                return None
            
            target_cell = cells[column_index]
            
            # Clear existing content and set new content
            target_cell.clear()
            target_cell.text = new_cell_content
            
            # Convert back to string
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error updating table cell: {e}")
            return None
    
    def _add_table_row_content(self,
                              content: str,
                              table_index: int,
                              row_data: List[str],
                              insert_position: Optional[int] = None) -> Optional[str]:
        """Add a new row to table content."""
        try:
            # Analyze the content first to set the _current_root
            structure = self.content_analyzer.analyze(content)
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find all tables
            tables = root_copy.findall(".//table")
            if table_index >= len(tables):
                logger.error(f"Table index {table_index} out of range")
                return None
            
            target_table = tables[table_index]
            
            # Create new row element
            new_row = ET.Element("tr")
            
            # Add cells to the row
            for cell_content in row_data:
                cell = ET.SubElement(new_row, "td")
                cell.text = cell_content
            
            # Insert the row at the specified position
            existing_rows = target_table.findall(".//tr")
            if insert_position is None or insert_position >= len(existing_rows):
                # Append to end
                target_table.append(new_row)
            else:
                # Insert at specific position
                target_table.insert(insert_position, new_row)
            
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error adding table row: {e}")
            return None
    
    def _update_table_column_content(self,
                                    content: str,
                                    table_index: int,
                                    column_index: int,
                                    column_data: List[str]) -> Optional[str]:
        """Update entire table column content."""
        try:
            # Analyze the content first to set the _current_root
            structure = self.content_analyzer.analyze(content)
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find all tables
            tables = root_copy.findall(".//table")
            if table_index >= len(tables):
                logger.error(f"Table index {table_index} out of range")
                return None
            
            target_table = tables[table_index]
            
            # Find all rows in the table
            rows = target_table.findall(".//tr")
            
            # Update each row's cell at the specified column index
            for row_idx, row in enumerate(rows):
                if row_idx < len(column_data):
                    cells = row.findall("td") + row.findall("th")
                    if column_index < len(cells):
                        target_cell = cells[column_index]
                        target_cell.clear()
                        target_cell.text = column_data[row_idx]
            
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error updating table column: {e}")
            return None
    
    def _add_list_item_content(self,
                              content: str,
                              list_index: int,
                              new_item_content: str,
                              insert_position: Optional[int] = None) -> Optional[str]:
        """Add new item to list content."""
        try:
            # Analyze the content first to set the _current_root
            structure = self.content_analyzer.analyze(content)
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find all lists (ul and ol)
            lists = root_copy.findall(".//ul") + root_copy.findall(".//ol")
            if list_index >= len(lists):
                logger.error(f"List index {list_index} out of range")
                return None
            
            target_list = lists[list_index]
            
            # Create new list item
            new_item = ET.Element("li")
            new_item.text = new_item_content
            
            # Insert the item at the specified position
            existing_items = target_list.findall("li")
            if insert_position is None or insert_position >= len(existing_items):
                # Append to end
                target_list.append(new_item)
            else:
                # Insert at specific position
                target_list.insert(insert_position, new_item)
            
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error adding list item: {e}")
            return None
    
    def _update_list_item_content(self,
                                 content: str,
                                 list_index: int,
                                 item_index: int,
                                 new_item_content: str) -> Optional[str]:
        """Update specific list item content."""
        try:
            # Analyze the content first to set the _current_root
            structure = self.content_analyzer.analyze(content)
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find all lists (ul and ol)
            lists = root_copy.findall(".//ul") + root_copy.findall(".//ol")
            if list_index >= len(lists):
                logger.error(f"List index {list_index} out of range")
                return None
            
            target_list = lists[list_index]
            
            # Find all list items
            items = target_list.findall("li")
            if item_index >= len(items):
                logger.error(f"Item index {item_index} out of range")
                return None
            
            target_item = items[item_index]
            
            # Update item content
            target_item.clear()
            target_item.text = new_item_content
            
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error updating list item: {e}")
            return None
    
    def _reorder_list_items_content(self,
                                   content: str,
                                   list_index: int,
                                   new_order: List[int]) -> Optional[str]:
        """Reorder list items according to new order."""
        try:
            # Analyze the content first to set the _current_root
            structure = self.content_analyzer.analyze(content)
            root = self.content_analyzer._current_root
            if root is None:
                return None
            
            # Create a copy to work with
            root_copy = copy.deepcopy(root)
            
            # Find all lists (ul and ol)
            lists = root_copy.findall(".//ul") + root_copy.findall(".//ol")
            if list_index >= len(lists):
                logger.error(f"List index {list_index} out of range")
                return None
            
            target_list = lists[list_index]
            
            # Find all list items
            items = target_list.findall("li")
            
            # Validate new order indices
            if max(new_order) >= len(items) or min(new_order) < 0:
                logger.error(f"Invalid order indices for {len(items)} items")
                return None
            
            # Create a copy of items in the new order
            reordered_items = [copy.deepcopy(items[i]) for i in new_order]
            
            # Clear the list and add items in new order
            target_list.clear()
            for item in reordered_items:
                target_list.append(item)
            
            return self.xml_parser.to_string(root_copy)
            
        except Exception as e:
            logger.error(f"Error reordering list items: {e}")
            return None 