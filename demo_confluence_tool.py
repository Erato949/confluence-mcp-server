#!/usr/bin/env python3

import asyncio
import httpx
import json
import base64
import os

async def demo_confluence_tool():
    """Demo the working Confluence MCP tool"""
    
    print("🔧 Confluence MCP Tool Demo")
    print("=" * 40)
    
    # First, let's set up a proper Smithery config with your actual Confluence URL
    config_data = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": os.getenv("CONFLUENCE_USERNAME", "your-email@domain.com"),  
        "apiToken": os.getenv("CONFLUENCE_API_TOKEN", "your-api-token")
    }
    
    config_json = json.dumps(config_data)
    config_encoded = base64.b64encode(config_json.encode()).decode()
    
    print(f"📋 Config URL: {config_data['confluenceUrl']}")
    print(f"👤 Username: {config_data['username']}")
    print(f"🔑 Token: {'SET' if config_data['apiToken'] != 'your-api-token' else 'NOT_SET'}")
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n🌐 Testing connection to {base_url}")
        
        # Test 1: List available tools
        print("\n📋 Step 1: Getting available tools...")
        try:
            response = await client.get(f"{base_url}/mcp", params={"config": config_encoded})
            if response.status_code == 200:
                tools = response.json().get("tools", [])
                print(f"✅ Found {len(tools)} available tools:")
                for i, tool in enumerate(tools[:3], 1):  # Show first 3
                    print(f"   {i}. {tool['name']}: {tool['description']}")
                if len(tools) > 3:
                    print(f"   ... and {len(tools) - 3} more")
            else:
                print(f"❌ Failed to get tools: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return
        
        # Test 2: Try to list Confluence spaces
        print("\n🏢 Step 2: Listing Confluence spaces...")
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_confluence_spaces",
                "arguments": {"limit": 10}
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/mcp", 
                json=mcp_request,
                params={"config": config_encoded}
            )
            
            print(f"📡 Response status: {response.status_code}")
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"]["message"]
                print(f"⚠️  Error: {error_msg}")
                
                # Diagnose the error type
                if "protocol" in error_msg.lower():
                    print("❌ URL protocol error - this should be fixed now!")
                elif "404" in error_msg or "not found" in error_msg.lower():
                    print("🔍 404 error - check the API endpoint URL")
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    print("🔐 Authentication error - check your credentials")
                elif "403" in error_msg or "forbidden" in error_msg.lower():
                    print("🚫 Permission error - check your API token permissions")
                else:
                    print(f"🤔 Unknown error type: {error_msg}")
            else:
                # Success!
                content = result.get("result", {}).get("content", [])
                if content and content[0].get("type") == "text":
                    spaces_data = json.loads(content[0]["text"])
                    if "spaces" in spaces_data:
                        spaces = spaces_data["spaces"]
                        print(f"🎉 SUCCESS! Found {len(spaces)} spaces:")
                        for space in spaces:
                            print(f"   • {space.get('name', 'Unknown')} ({space.get('key', 'N/A')})")
                    else:
                        print(f"✅ Tool executed successfully: {spaces_data}")
                else:
                    print(f"✅ Success but unexpected format: {result}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n{'='*40}")
    print("🏁 Demo complete!")
    
    if config_data['apiToken'] == 'your-api-token':
        print("\n💡 To test with real data:")
        print("   1. Set CONFLUENCE_USERNAME environment variable")
        print("   2. Set CONFLUENCE_API_TOKEN environment variable") 
        print("   3. Re-run this demo")

if __name__ == "__main__":
    asyncio.run(demo_confluence_tool()) 