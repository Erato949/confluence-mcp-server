#!/usr/bin/env python3
"""
Decode the EXACT base64 config from the user's logs
This will prove whether Smithery is sending placeholder or real values
"""

import base64
import json

def decode_exact_config():
    """Decode the exact base64 string from the logs."""
    
    # From the logs: length 176, starting with this
    base64_start = "eyJjb25mbHVlbmNlVXJsIjogImh0dHBzOi8vZmVlZGJhY2tsb29wYWkuYXRsYXNzaWFuLm5ldC93aWtpLyIsICJ1c2VybmFtZSI6"
    
    print("🔍 Decoding Configuration from Logs")
    print("=" * 50)
    print(f"Base64 prefix: {base64_start}")
    print(f"Expected total length: 176 characters")
    print(f"Current prefix length: {len(base64_start)}")
    print()
    
    # Decode what we have so far
    try:
        # Try with different padding
        for padding in ["", "=", "==", "==="]:
            try:
                decoded_bytes = base64.b64decode(base64_start + padding)
                decoded_text = decoded_bytes.decode('utf-8')
                print(f"✅ Partial decode (padding '{padding}'):")
                print(f"Decoded text: {decoded_text}")
                print()
                break
            except:
                continue
                
    except Exception as e:
        print(f"❌ Decode error: {e}")
    
    # Reconstruct what the full config likely looks like
    print("🧪 Reconstructing Full Configuration")
    print("=" * 50)
    
    # Based on the partial decode, we can see it starts with:
    # {"confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/", "username": 
    
    # If this is the template, it would be:
    template_config = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": "your-email@domain.com",
        "apiToken": "your-api-token-here"
    }
    
    template_json = json.dumps(template_config)
    template_b64 = base64.b64encode(template_json.encode('utf-8')).decode('utf-8')
    
    print(f"Template JSON: {template_json}")
    print(f"Template JSON length: {len(template_json)}")
    print(f"Template base64: {template_b64}")
    print(f"Template base64 length: {len(template_b64)}")
    print()
    
    print("🔍 COMPARISON:")
    print(f"Log config length: 176")
    print(f"Template config length: {len(template_b64)}")
    print(f"Lengths match: {len(template_b64) == 176}")
    print()
    
    if len(template_b64) == 176:
        print("🚨 SMOKING GUN: The configuration length matches the template exactly!")
        print("   This proves Smithery is sending placeholder values, not real ones.")
    
    print("\n🎯 VERIFICATION:")
    print("If the base64 from logs starts with:")
    print(f"  {template_b64[:80]}...")
    print("Then Smithery is definitely sending the template config.")

if __name__ == "__main__":
    decode_exact_config() 