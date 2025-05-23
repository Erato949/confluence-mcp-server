#!/usr/bin/env python3
"""Debug script to understand FastMCP tools structure."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from confluence_mcp_server.main import mcp_server

async def debug_tools():
    """Debug the tools structure."""
    try:
        print("Getting tools from FastMCP server...")
        tools = await mcp_server.get_tools()
        
        print(f"Tools type: {type(tools)}")
        print(f"Tools length: {len(tools) if tools else 0}")
        
        if tools:
            print(f"Tools keys: {list(tools.keys())}")
            
            first_key = list(tools.keys())[0]
            first_tool = tools[first_key]
            print(f"First tool key: {first_key}")
            print(f"First tool: {first_tool}")
            print(f"First tool type: {type(first_tool)}")
            
            if hasattr(first_tool, '__dict__'):
                print(f"First tool attributes: {first_tool.__dict__}")
            
            print(f"First tool dir: {dir(first_tool)}")
            
        # Also try the _mcp_list_tools method
        print("\nTrying _mcp_list_tools...")
        list_result = await mcp_server._mcp_list_tools()
        print(f"List result: {list_result}")
        
        # Test tool calling format
        print("\nTesting tool call format...")
        try:
            # Try the format that failed
            result1 = await mcp_server._mcp_call_tool("get_confluence_page", {"page_id": "123456"})
            print(f"Direct format result: {result1}")
        except Exception as e:
            print(f"Direct format error: {e}")
            
        try:
            # Try with inputs wrapper
            result2 = await mcp_server._mcp_call_tool("get_confluence_page", {"inputs": {"page_id": "123456"}})
            print(f"Inputs wrapper result: {result2}")
        except Exception as e:
            print(f"Inputs wrapper error: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_tools()) 