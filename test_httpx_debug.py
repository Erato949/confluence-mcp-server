#!/usr/bin/env python3

import asyncio
import httpx
import os

async def test_httpx_client():
    """Test httpx client creation and request to debug URL protocol issue"""
    
    # Simulate the exact URL processing from server_http_optimized.py
    confluence_url = 'https://feedbackloopai.atlassian.net/wiki/'
    print(f"Original URL: {confluence_url}")
    
    # Step 1: Remove /wiki/ path
    base_url = confluence_url.rstrip('/wiki/')
    print(f"After rstrip('/wiki/'): {base_url}")
    
    # Step 2: Remove trailing slashes
    base_url = base_url.rstrip('/')
    print(f"After rstrip('/'): {base_url}")
    
    # Step 3: Add protocol if missing
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'https://{base_url}'
    print(f"Final base_url: {base_url}")
    
    # Test httpx client creation
    try:
        async with httpx.AsyncClient(
            base_url=base_url,
            auth=('test_username', 'test_token'),
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        ) as client:
            print(f"Client created successfully with base_url: {client.base_url}")
            
            # Test making a request (this should fail with auth error, but not URL error)
            try:
                response = await client.get('/rest/api/space', params={'limit': 10})
                print(f"Request successful: {response.status_code}")
            except Exception as e:
                print(f"Request failed (expected): {type(e).__name__}: {e}")
                
    except Exception as e:
        print(f"Client creation failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_httpx_client()) 