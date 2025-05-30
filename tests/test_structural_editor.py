"""
Tests for Structural Editor - Phase 5 of Confluence Selective Editing System

This test suite validates the advanced structural editing operations for tables and lists
while ensuring XML structure preservation and robust error handling.
"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

from confluence_mcp_server.selective_editing.structural_editor import StructuralEditor
from confluence_mcp_server.selective_editing.xml_parser import ConfluenceXMLParser
from confluence_mcp_server.selective_editing.content_analyzer import ContentStructureAnalyzer
from confluence_mcp_server.selective_editing.operations import (
    OperationType, AddTableRowOperation, UpdateTableCellOperation, 
    UpdateTableColumnOperation, AddListItemOperation, UpdateListItemOperation,
    ReorderListItemsOperation
)
from confluence_mcp_server.selective_editing.exceptions import (
    ContentStructureError, XMLParsingError
)


class TestStructuralEditor:
    """Test suite for the StructuralEditor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.structural_editor = StructuralEditor()
        
        # Sample content with tables and lists
        self.table_content = """
        <div>
            <h1>Product Comparison</h1>
            <table>
                <tr>
                    <th>Product</th>
                    <th>Price</th>
                    <th>Rating</th>
                </tr>
                <tr>
                    <td>Product A</td>
                    <td>$100</td>
                    <td>4.5</td>
                </tr>
                <tr>
                    <td>Product B</td>
                    <td>$150</td>
                    <td>4.8</td>
                </tr>
            </table>
            
            <h2>Additional Information</h2>
            <table>
                <tr>
                    <td>Version</td>
                    <td>1.0</td>
                </tr>
                <tr>
                    <td>Release Date</td>
                    <td>2024-01-01</td>
                </tr>
            </table>
        </div>
        """
        
        self.list_content = """
        <div>
            <h1>Development Tasks</h1>
            <ul>
                <li>Design user interface</li>
                <li>Implement backend API</li>
                <li>Write unit tests</li>
                <li>Deploy to production</li>
            </ul>
            
            <h2>Priority Features</h2>
            <ol>
                <li>User authentication</li>
                <li>Data visualization</li>
                <li>Export functionality</li>
            </ol>
        </div>
        """
        
        self.mixed_content = """
        <div>
            <h1>Project Overview</h1>
            <p>This project includes both tables and lists for comprehensive data presentation.</p>
            
            <h2>Team Members</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Experience</th>
                </tr>
                <tr>
                    <td>Alice</td>
                    <td>Developer</td>
                    <td>5 years</td>
                </tr>
                <tr>
                    <td>Bob</td>
                    <td>Designer</td>
                    <td>3 years</td>
                </tr>
            </table>
            
            <h2>Project Milestones</h2>
            <ul>
                <li>Project planning</li>
                <li>Requirements gathering</li>
                <li>Development phase</li>
                <li>Testing and QA</li>
            </ul>
        </div>
        """
    
    def test_structural_editor_initialization(self):
        """Test that StructuralEditor initializes correctly."""
        editor = StructuralEditor()
        assert editor.xml_parser is not None
        assert editor.content_analyzer is not None
        assert editor._backup_content is None
        
        # Test with custom parser
        custom_parser = ConfluenceXMLParser()
        editor_with_parser = StructuralEditor(custom_parser)
        assert editor_with_parser.xml_parser is custom_parser
    
    # Table Cell Operations
    
    def test_update_table_cell_success(self):
        """Test successful table cell update."""
        result = self.structural_editor.update_table_cell(
            content=self.table_content,
            table_index=0,
            row_index=1,
            column_index=1,
            new_cell_content="$120"
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.UPDATE_TABLE_CELL
        assert result.modified_content is not None
        assert result.backup_content == self.table_content
        
        # Verify the cell was updated
        modified = result.modified_content
        assert "$120" in modified
        assert "$100" not in modified  # Old value should be replaced
        assert "Updated table[0] row[1] column[1] with new content" in result.changes_made
    
    def test_update_table_cell_second_table(self):
        """Test updating a cell in the second table."""
        result = self.structural_editor.update_table_cell(
            content=self.table_content,
            table_index=1,
            row_index=0,
            column_index=1,
            new_cell_content="2.0"
        )
        
        assert result.success is True
        modified = result.modified_content
        assert "2.0" in modified
        assert "Updated table[1] row[0] column[1] with new content" in result.changes_made
    
    def test_update_table_cell_invalid_table_index(self):
        """Test table cell update with invalid table index."""
        result = self.structural_editor.update_table_cell(
            content=self.table_content,
            table_index=5,  # Only 2 tables exist
            row_index=0,
            column_index=0,
            new_cell_content="new value"
        )
        
        assert result.success is False
        assert "Failed to update table cell" in result.error_message
        assert result.backup_content == self.table_content
    
    def test_update_table_cell_invalid_row_index(self):
        """Test table cell update with invalid row index."""
        result = self.structural_editor.update_table_cell(
            content=self.table_content,
            table_index=0,
            row_index=10,  # Row doesn't exist
            column_index=0,
            new_cell_content="new value"
        )
        
        assert result.success is False
        assert "Failed to update table cell" in result.error_message
    
    def test_update_table_cell_invalid_column_index(self):
        """Test table cell update with invalid column index."""
        result = self.structural_editor.update_table_cell(
            content=self.table_content,
            table_index=0,
            row_index=0,
            column_index=10,  # Column doesn't exist
            new_cell_content="new value"
        )
        
        assert result.success is False
        assert "Failed to update table cell" in result.error_message
    
    def test_update_table_cell_empty_content(self):
        """Test table cell update with empty content."""
        result = self.structural_editor.update_table_cell(
            content="",
            table_index=0,
            row_index=0,
            column_index=0,
            new_cell_content="new value"
        )
        
        assert result.success is False
        assert "Cannot update table cell in empty content" in result.error_message
    
    # Table Row Operations
    
    def test_add_table_row_success(self):
        """Test successful table row addition."""
        new_row_data = ["Product C", "$200", "4.9"]
        
        result = self.structural_editor.add_table_row(
            content=self.table_content,
            table_index=0,
            row_data=new_row_data
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.ADD_TABLE_ROW
        assert result.modified_content is not None
        
        # Verify the row was added
        modified = result.modified_content
        assert "Product C" in modified
        assert "$200" in modified
        assert "4.9" in modified
        assert "Added new row to table[0] at end with 3 cells" in result.changes_made
    
    def test_add_table_row_with_position(self):
        """Test adding table row at specific position."""
        new_row_data = ["Product Z", "$75", "4.0"]
        
        result = self.structural_editor.add_table_row(
            content=self.table_content,
            table_index=0,
            row_data=new_row_data,
            insert_position=1
        )
        
        assert result.success is True
        modified = result.modified_content
        assert "Product Z" in modified
        assert "Added new row to table[0] at position 1 with 3 cells" in result.changes_made
    
    def test_add_table_row_empty_data(self):
        """Test adding table row with empty data."""
        result = self.structural_editor.add_table_row(
            content=self.table_content,
            table_index=0,
            row_data=[]
        )
        
        assert result.success is False
        assert "Row data cannot be empty" in result.error_message
    
    def test_add_table_row_invalid_table_index(self):
        """Test adding row to non-existent table."""
        result = self.structural_editor.add_table_row(
            content=self.table_content,
            table_index=5,
            row_data=["data1", "data2"]
        )
        
        assert result.success is False
        assert "Failed to add row to table[5]" in result.error_message
    
    # Table Column Operations
    
    def test_update_table_column_success(self):
        """Test successful table column update."""
        new_column_data = ["Price", "$99", "$149", "$199"]
        
        result = self.structural_editor.update_table_column(
            content=self.table_content,
            table_index=0,
            column_index=1,
            column_data=new_column_data
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.UPDATE_TABLE_COLUMN
        
        # Verify the column was updated
        modified = result.modified_content
        assert "$99" in modified
        assert "$149" in modified
        assert "Updated column[1] in table[0] with 4 cells" in result.changes_made
    
    def test_update_table_column_empty_data(self):
        """Test updating table column with empty data."""
        result = self.structural_editor.update_table_column(
            content=self.table_content,
            table_index=0,
            column_index=0,
            column_data=[]
        )
        
        assert result.success is False
        assert "Column data cannot be empty" in result.error_message
    
    def test_update_table_column_invalid_table_index(self):
        """Test updating column in non-existent table."""
        result = self.structural_editor.update_table_column(
            content=self.table_content,
            table_index=5,
            column_index=0,
            column_data=["data1", "data2"]
        )
        
        assert result.success is False
        assert "Failed to update column[0] in table[5]" in result.error_message
    
    # List Item Operations
    
    def test_add_list_item_success(self):
        """Test successful list item addition."""
        result = self.structural_editor.add_list_item(
            content=self.list_content,
            list_index=0,
            new_item_content="Create documentation"
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.ADD_LIST_ITEM
        assert result.modified_content is not None
        
        # Verify the item was added
        modified = result.modified_content
        assert "Create documentation" in modified
        assert "Added new item to list[0] at end" in result.changes_made
    
    def test_add_list_item_with_position(self):
        """Test adding list item at specific position."""
        result = self.structural_editor.add_list_item(
            content=self.list_content,
            list_index=0,
            new_item_content="Review requirements",
            insert_position=1
        )
        
        assert result.success is True
        modified = result.modified_content
        assert "Review requirements" in modified
        assert "Added new item to list[0] at position 1" in result.changes_made
    
    def test_add_list_item_ordered_list(self):
        """Test adding item to ordered list (second list)."""
        result = self.structural_editor.add_list_item(
            content=self.list_content,
            list_index=1,
            new_item_content="Performance optimization"
        )
        
        assert result.success is True
        modified = result.modified_content
        assert "Performance optimization" in modified
        assert "Added new item to list[1] at end" in result.changes_made
    
    def test_add_list_item_empty_content(self):
        """Test adding list item with empty content."""
        result = self.structural_editor.add_list_item(
            content=self.list_content,
            list_index=0,
            new_item_content=""
        )
        
        assert result.success is False
        assert "List item content cannot be empty" in result.error_message
    
    def test_add_list_item_invalid_list_index(self):
        """Test adding item to non-existent list."""
        result = self.structural_editor.add_list_item(
            content=self.list_content,
            list_index=5,
            new_item_content="New item"
        )
        
        assert result.success is False
        assert "Failed to add item to list[5]" in result.error_message
    
    def test_update_list_item_success(self):
        """Test successful list item update."""
        result = self.structural_editor.update_list_item(
            content=self.list_content,
            list_index=0,
            item_index=1,
            new_item_content="Implement REST API"
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.UPDATE_LIST_ITEM
        
        # Verify the item was updated
        modified = result.modified_content
        assert "Implement REST API" in modified
        assert "Implement backend API" not in modified  # Old content should be replaced
        assert "Updated item[1] in list[0]" in result.changes_made
    
    def test_update_list_item_invalid_indices(self):
        """Test updating list item with invalid indices."""
        # Invalid list index
        result = self.structural_editor.update_list_item(
            content=self.list_content,
            list_index=5,
            item_index=0,
            new_item_content="New content"
        )
        assert result.success is False
        
        # Invalid item index
        result = self.structural_editor.update_list_item(
            content=self.list_content,
            list_index=0,
            item_index=10,
            new_item_content="New content"
        )
        assert result.success is False
    
    def test_reorder_list_items_success(self):
        """Test successful list item reordering."""
        # Reorder: [0,1,2,3] -> [3,0,1,2] (move last item to first)
        new_order = [3, 0, 1, 2]
        
        result = self.structural_editor.reorder_list_items(
            content=self.list_content,
            list_index=0,
            new_order=new_order
        )
        
        assert result.success is True
        assert result.operation_type == OperationType.REORDER_LIST_ITEMS
        assert "Reordered 4 items in list[0]" in result.changes_made
        
        # Verify the reordering (this is complex to verify exactly, but we can check structure)
        modified = result.modified_content
        assert "<li>" in modified  # List structure preserved
        assert all(task in modified for task in ["Design user interface", "Implement backend API", 
                                                "Write unit tests", "Deploy to production"])
    
    def test_reorder_list_items_invalid_order(self):
        """Test reordering with invalid order specification."""
        # Invalid order - index out of range
        result = self.structural_editor.reorder_list_items(
            content=self.list_content,
            list_index=0,
            new_order=[0, 1, 2, 10]  # Index 10 doesn't exist
        )
        
        assert result.success is False
        assert "Failed to reorder items in list[0]" in result.error_message
    
    def test_reorder_list_items_empty_order(self):
        """Test reordering with empty order."""
        result = self.structural_editor.reorder_list_items(
            content=self.list_content,
            list_index=0,
            new_order=[]
        )
        
        assert result.success is False
        assert "New order cannot be empty" in result.error_message
    
    # Rollback functionality
    
    def test_rollback_functionality(self):
        """Test the rollback functionality."""
        # Initially no backup
        assert self.structural_editor.rollback() is None
        
        # Perform an operation to create backup
        self.structural_editor.update_table_cell(
            content=self.table_content,
            table_index=0,
            row_index=1,
            column_index=1,
            new_cell_content="$999"
        )
        
        # Now rollback should return the original content
        backup = self.structural_editor.rollback()
        assert backup == self.table_content
    
    # Integration and complex scenarios
    
    def test_mixed_content_operations(self):
        """Test operations on content with both tables and lists."""
        # Update table cell
        result1 = self.structural_editor.update_table_cell(
            content=self.mixed_content,
            table_index=0,
            row_index=1,
            column_index=2,
            new_cell_content="7 years"
        )
        assert result1.success is True
        
        # Add list item to the modified content
        result2 = self.structural_editor.add_list_item(
            content=result1.modified_content,
            list_index=0,
            new_item_content="Final deployment"
        )
        assert result2.success is True
        
        # Verify both changes are present
        final_content = result2.modified_content
        assert "7 years" in final_content
        assert "Final deployment" in final_content
    
    def test_malformed_xml_handling(self):
        """Test handling of malformed XML content."""
        malformed_content = "<div><table><tr><td>Broken XML without proper closing"
        
        result = self.structural_editor.update_table_cell(
            content=malformed_content,
            table_index=0,
            row_index=0,
            column_index=0,
            new_cell_content="new value"
        )
        
        # Should fail gracefully
        assert result.success is False
        assert "Failed to parse XML content" in result.error_message
        assert result.backup_content == malformed_content
    
    def test_preserve_xml_structure(self):
        """Test that XML structure and attributes are preserved."""
        content_with_attributes = """
        <div class="container">
            <table id="main-table" class="data-table">
                <tr>
                    <td class="header">Name</td>
                    <td class="value">Value</td>
                </tr>
                <tr>
                    <td>Item 1</td>
                    <td>Data 1</td>
                </tr>
            </table>
        </div>
        """
        
        result = self.structural_editor.update_table_cell(
            content=content_with_attributes,
            table_index=0,
            row_index=1,
            column_index=1,
            new_cell_content="Updated Data"
        )
        
        assert result.success is True
        modified = result.modified_content
        
        # Verify attributes are preserved
        assert 'class="container"' in modified
        assert 'id="main-table"' in modified
        assert 'class="data-table"' in modified
        assert 'class="value"' in modified
        
        # Verify content was updated
        assert "Updated Data" in modified
        assert "Data 1" not in modified


class TestStructuralEditorIntegration:
    """Integration tests for StructuralEditor with complex scenarios."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.structural_editor = StructuralEditor()
    
    def test_end_to_end_table_editing(self):
        """Test complete table editing workflow."""
        table_content = """
        <div>
            <h1>Sales Report</h1>
            <table>
                <tr>
                    <th>Month</th>
                    <th>Sales</th>
                    <th>Target</th>
                </tr>
                <tr>
                    <td>January</td>
                    <td>$10,000</td>
                    <td>$12,000</td>
                </tr>
                <tr>
                    <td>February</td>
                    <td>$15,000</td>
                    <td>$14,000</td>
                </tr>
            </table>
        </div>
        """
        
        # Step 1: Update a cell
        result1 = self.structural_editor.update_table_cell(
            content=table_content,
            table_index=0,
            row_index=1,
            column_index=1,
            new_cell_content="$11,500"
        )
        assert result1.success is True
        
        # Step 2: Add a new row
        result2 = self.structural_editor.add_table_row(
            content=result1.modified_content,
            table_index=0,
            row_data=["March", "$18,000", "$16,000"]
        )
        assert result2.success is True
        
        # Step 3: Update entire column
        result3 = self.structural_editor.update_table_column(
            content=result2.modified_content,
            table_index=0,
            column_index=2,
            column_data=["Target", "$13,000", "$15,000", "$17,000"]
        )
        assert result3.success is True
        
        # Verify final result
        final_content = result3.modified_content
        assert "$11,500" in final_content  # Updated cell
        assert "March" in final_content    # New row
        assert "$13,000" in final_content  # Updated column
        
        # Verify we can parse the final result
        parser = ConfluenceXMLParser()
        assert parser.parse(final_content) is not None
    
    def test_end_to_end_list_editing(self):
        """Test complete list editing workflow."""
        list_content = """
        <div>
            <h1>Project Roadmap</h1>
            <ol>
                <li>Phase 1: Planning</li>
                <li>Phase 2: Development</li>
                <li>Phase 3: Testing</li>
            </ol>
        </div>
        """
        
        # Step 1: Add new item
        result1 = self.structural_editor.add_list_item(
            content=list_content,
            list_index=0,
            new_item_content="Phase 4: Deployment",
            insert_position=3
        )
        assert result1.success is True
        
        # Step 2: Update existing item
        result2 = self.structural_editor.update_list_item(
            content=result1.modified_content,
            list_index=0,
            item_index=1,
            new_item_content="Phase 2: Implementation & Development"
        )
        assert result2.success is True
        
        # Step 3: Reorder items
        result3 = self.structural_editor.reorder_list_items(
            content=result2.modified_content,
            list_index=0,
            new_order=[0, 2, 1, 3]  # Move testing before development
        )
        assert result3.success is True
        
        # Verify final result contains all expected content
        final_content = result3.modified_content
        assert "Phase 1: Planning" in final_content
        assert "Phase 2: Implementation &amp; Development" in final_content
        assert "Phase 3: Testing" in final_content
        assert "Phase 4: Deployment" in final_content
        
        # Verify we can parse the final result
        parser = ConfluenceXMLParser()
        assert parser.parse(final_content) is not None 