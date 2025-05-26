#!/usr/bin/env python3
import requests
import base64
import json

# Test configuration
config = {
    "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
    "username": "chughes@feedbackloopai.ai", 
    "apiToken": "test-token-value"
}

# Encode as base64
config_json = json.dumps(config)
encoded_config = base64.b64encode(config_json.encode()).decode()

print(f"Testing configuration mechanism...")
print(f"Config: {config_json}")
print(f"Encoded: {encoded_config}")

# Test the /mcp endpoint with config
url = f"http://localhost:8000/mcp?config={encoded_config}"
print(f"URL: {url}")

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")

# Now test a tool call to see if config was applied
print("\nTesting tool call...")
tool_call = {
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/call",
    "params": {
        "name": "get_confluence_spaces",
        "arguments": {"limit": 10}
    }
}

try:
    # Include config in POST request as well (Smithery.ai pattern)
    response = requests.post(f"http://localhost:8000/mcp?config={encoded_config}", json=tool_call)
    print(f"Tool call status: {response.status_code}")
    print(f"Tool call response: {response.text}")
except Exception as e:
    print(f"Tool call error: {e}") 