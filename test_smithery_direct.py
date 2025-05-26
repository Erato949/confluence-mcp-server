#!/usr/bin/env python3
"""
Test direct Smithery configuration bypassing the template
This will help verify if Smithery UI config is actually being sent
"""

import os
import base64
import json

def create_manual_config():
    """Create a manual configuration for testing."""
    
    print("🧪 Manual Configuration Test")
    print("=" * 50)
    
    # Create a test config with your real values
    # You'll need to fill these in with your actual credentials
    test_config = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": "chughes@feedbackloopai.ai",  # Replace with your real email
        "apiToken": "YOUR_REAL_API_TOKEN_HERE"    # Replace with your real token
    }
    
    # Encode it
    config_json = json.dumps(test_config)
    config_b64 = base64.b64encode(config_json.encode('utf-8')).decode('utf-8')
    
    print(f"Manual config JSON: {config_json}")
    print(f"Manual config base64: {config_b64}")
    print(f"Manual config length: {len(config_b64)}")
    print()
    
    print("🎯 Testing Manual Configuration:")
    print("1. Replace YOUR_REAL_API_TOKEN_HERE with your actual token")
    print("2. Test this config directly in the server")
    print("3. Compare with what Smithery sends")
    
    return config_b64

def compare_configs():
    """Compare different configuration sources."""
    
    print("🔍 Configuration Source Comparison")
    print("=" * 50)
    
    # Template config (what we think Smithery is sending)
    template = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": "your-email@domain.com",
        "apiToken": "your-api-token-here"
    }
    
    # Expected real config
    real = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": "chughes@feedbackloopai.ai",
        "apiToken": "ATATT3xFfGF0T3J... (real token)"
    }
    
    template_b64 = base64.b64encode(json.dumps(template).encode()).decode()
    real_b64 = base64.b64encode(json.dumps(real).encode()).decode()
    
    print("TEMPLATE CONFIG:")
    print(f"  JSON: {json.dumps(template)}")
    print(f"  Base64: {template_b64[:50]}...")
    print(f"  Length: {len(template_b64)}")
    print()
    
    print("EXPECTED REAL CONFIG:")
    print(f"  JSON: {json.dumps(real)}")
    print(f"  Base64: {real_b64[:50]}...")
    print(f"  Length: {len(real_b64)}")
    print()
    
    print("FROM LOGS (length 176):")
    log_prefix = "eyJjb25mbHVlbmNlVXJsIjogImh0dHBzOi8vZmVlZGJhY2tsb29wYWkuYXRsYXNzaWFuLm5ldC93aWtpLyIsICJ1c2VybmFtZSI6"
    print(f"  Base64: {log_prefix}...")
    print(f"  Length: 176")
    print()
    
    # Check if log prefix matches template
    if template_b64.startswith(log_prefix[:50]):
        print("🚨 MATCH: Logs show template config is being used!")
    else:
        print("✅ NO MATCH: Logs show different config (possibly real)")

if __name__ == "__main__":
    create_manual_config()
    print()
    compare_configs() 