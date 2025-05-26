#!/usr/bin/env python3

import asyncio
import httpx
import json
import base64

async def test_server():
    """Simple test of the server with config"""
    
    # Create test config
    config_data = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": "test@example.com",
        "apiToken": "fake-token-for-testing"
    }
    
    config_json = json.dumps(config_data)
    config_encoded = base64.b64encode(config_json.encode()).decode()
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test tool execution with config
        print("Testing tool execution with config...")
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_confluence_spaces",
                "arguments": {"limit": 5}
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/mcp", 
                json=mcp_request,
                params={"config": config_encoded}
            )
            
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"]["message"]
                print(f"Error: {error_msg}")
                
                # Check the type of error
                if "protocol" in error_msg.lower():
                    print("❌ STILL GETTING URL PROTOCOL ERROR!")
                    return False
                elif "401" in error_msg or "auth" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    print("✅ Got auth error instead of URL error - FIX WORKS!")
                    return True
                else:
                    print(f"ℹ️  Different error: {error_msg}")
                    return True  # Any error other than protocol is progress
            else:
                print("✅ Unexpected success!")
                return True
                
        except Exception as e:
            print(f"Request failed: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_server())
    if result:
        print("\n🎉 Configuration fix successful!")
    else:
        print("\n❌ Configuration fix failed!") 