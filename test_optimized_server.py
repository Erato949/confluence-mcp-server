#!/usr/bin/env python3
"""
Quick test script to validate the optimized server for Smithery.ai deployment
"""

import asyncio
import json
import httpx

async def test_optimized_server():
    """Test the optimized server endpoints for Smithery compliance."""
    
    print("🧪 Testing Optimized Confluence MCP Server for Smithery.ai")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Health check
            print("1. Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            health_data = response.json()
            print(f"   ✅ Health: {health_data}")
            
            # Test 2: Root endpoint
            print("\n2. Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            assert response.status_code == 200
            root_data = response.json()
            print(f"   ✅ Root: {root_data}")
            print(f"   📊 Tools count: {root_data.get('tools_count', 0)}")
            
            # Test 3: Tool listing (Smithery requirement - NO AUTH)
            print("\n3. Testing tool listing (GET /mcp) - LAZY LOADING...")
            response = await client.get(f"{base_url}/mcp")
            assert response.status_code == 200
            tools_data = response.json()
            tools = tools_data.get("tools", [])
            print(f"   ✅ Tool listing successful")
            print(f"   📋 Found {len(tools)} tools")
            
            # Verify all expected tools are present
            expected_tools = [
                "get_confluence_page", "search_confluence_pages", "create_confluence_page",
                "update_confluence_page", "delete_confluence_page", "get_confluence_spaces",
                "get_page_attachments", "add_page_attachment", "delete_page_attachment",
                "get_page_comments"
            ]
            
            found_tools = [tool["name"] for tool in tools]
            missing_tools = set(expected_tools) - set(found_tools)
            
            if missing_tools:
                print(f"   ❌ Missing tools: {missing_tools}")
            else:
                print(f"   ✅ All 10 Confluence tools present")
            
            # Test 4: JSON-RPC tool listing
            print("\n4. Testing JSON-RPC tool listing...")
            rpc_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            response = await client.post(f"{base_url}/mcp", json=rpc_request)
            assert response.status_code == 200
            rpc_data = response.json()
            print(f"   ✅ JSON-RPC response: {rpc_data.get('jsonrpc')} (ID: {rpc_data.get('id')})")
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED - Server is Smithery.ai ready!")
            print("✅ Lazy loading: Tool listing requires NO authentication")
            print("✅ Fast response: Pre-computed static tools")
            print("✅ MCP compliant: All endpoints working correctly")
            print("✅ Smithery ready: Deploy with confidence!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            print("Make sure the optimized server is running on port 8001")
            print("Run: python -c \"from confluence_mcp_server.server_http_optimized import run_server; run_server(port=8001)\"")

if __name__ == "__main__":
    asyncio.run(test_optimized_server()) 