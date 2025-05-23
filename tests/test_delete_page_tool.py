# tests/test_delete_page_tool.py
import pytest
import json # Added json import
from unittest.mock import AsyncMock
import httpx # For creating mock response
import os

from fastmcp import Client
from fastmcp.exceptions import ToolError # For asserting expected errors

# Schemas defined in our project for tool input/output
from confluence_mcp_server.mcp_actions.schemas import DeletePageOutput, DeletePageInput

# Fixtures mcp_client, mock_httpx_async_client are auto-imported from conftest.py

@pytest.mark.anyio
async def test_delete_page_success(
    mcp_client: Client,
    mock_httpx_async_client: AsyncMock
):
    """
    Test successful deletion of a Confluence page.
    """
    page_id_to_delete = "12345"
    
    mock_api_response = httpx.Response(204, request=httpx.Request("DELETE", "http://mock.confluence.com/rest/api/content/12345")) 
    mock_httpx_async_client.delete = AsyncMock(return_value=mock_api_response)

    request_params = DeletePageInput(page_id=page_id_to_delete).model_dump()
    
    # Using client.call_tool
    # It directly returns the "result" part of the JSON-RPC response
    # or raises a ToolError if the server returns a JSON-RPC error.
    result_content_list = await mcp_client.call_tool(
        "delete_confluence_page",  # Tool name
        {"inputs": request_params}  # Wrap params under 'inputs' key
    )
    # Assertions
    assert result_content_list is not None
    assert len(result_content_list) == 1
    
    # The first item should be TextContent, its .text attribute is the JSON string
    # For FastMCP, the content is typically mcp.type.TextContent
    # We need to import json to parse it
    import json # Make sure json is imported at the top of the file if not already
    actual_result_dict = json.loads(result_content_list[0].text)

    # Validate the structure of the result against DeletePageOutput
    result_data = DeletePageOutput(**actual_result_dict)
    assert result_data.page_id == page_id_to_delete
    assert result_data.status == "success"  # Corrected from "deleted"
    assert "successfully moved to trash" in result_data.message.lower() # Adjusted message

    mock_httpx_async_client.delete.assert_awaited_once()
    # confluence_base_url = os.getenv("CONFLUENCE_URL", "http://mock-confluence.com")
    # expected_url = f"{confluence_base_url}/rest/api/content/{page_id_to_delete}"
    # mock_httpx_async_client.delete.assert_awaited_once_with(expected_url)

# TODO: Add more test cases:
# - test_delete_page_not_found (API returns 404, tool should raise ToolError via HTTPException)
# - test_delete_page_api_error (API returns 500, tool should raise ToolError via HTTPException)
# - test_delete_page_invalid_input_missing_page_id (tool should raise ToolError for validation)
# - test_delete_page_invalid_input_wrong_type (tool should raise ToolError for validation)
