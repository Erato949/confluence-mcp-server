#!/usr/bin/env python3

import asyncio
import httpx

async def test_empty_url():
    """Test what happens with empty or None URLs"""
    
    test_cases = [
        "",
        None,
        " ",
        "   ",
        "http://",
        "https://",
        "feedbackloopai.atlassian.net"  # Missing protocol
    ]
    
    for i, url in enumerate(test_cases):
        print(f"\nTest {i+1}: URL = {repr(url)}")
        try:
            async with httpx.AsyncClient(base_url=url) as client:
                print(f"  Client created with base_url: {client.base_url}")
                try:
                    response = await client.get('/rest/api/space')
                    print(f"  Request successful: {response.status_code}")
                except Exception as e:
                    print(f"  Request failed: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"  Client creation failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_empty_url()) 