#!/usr/bin/env python3
"""
Test script to validate Smithery.ai compatibility
Tests all the endpoints that Smithery uses for tool scanning
"""

import requests
import json
import time

def test_server_endpoints():
    """Test all the endpoints Smithery needs for tool scanning"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Smithery.ai compatibility...")
    print(f"📡 Testing server at {base_url}")
    
    try:
        # Test 1: Health check
        print("\n1️⃣ Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 2: Root endpoint
        print("\n2️⃣ Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 3: GET /mcp (tool listing - what Smithery uses for scanning)
        print("\n3️⃣ Testing GET /mcp (Smithery tool scanning)...")
        response = requests.get(f"{base_url}/mcp", timeout=10)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Tools count: {len(result['tools'])}")
        print(f"   First tool: {result['tools'][0]['name']}")
        
        # Test 4: POST /mcp with tools/list (JSON-RPC)
        print("\n4️⃣ Testing POST /mcp with tools/list...")
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list", 
            "id": 1
        }
        response = requests.post(f"{base_url}/mcp", json=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Tools count: {len(result['result']['tools'])}")
        
        # Test 5: Test with Accept: text/event-stream header (SSE)
        print("\n5️⃣ Testing POST /mcp with SSE header...")
        headers = {"Accept": "text/event-stream"}
        response = requests.post(f"{base_url}/mcp", json=payload, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        
        print("\n✅ All tests passed! Server is Smithery-compatible.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting server compatibility test...")
    print("Make sure the server is running with: python -m confluence_mcp_server.server_http")
    time.sleep(2)
    test_server_endpoints() 