#!/usr/bin/env python3
"""
Debug script to decode the exact Smithery configuration from the logs
This will help us understand why the username is showing as 'your-email@domain.com'
"""

import base64
import json

def debug_smithery_config():
    """Debug the exact config string from the logs."""
    
    # This is the EXACT base64 string from your logs (truncated)
    base64_config = "eyJjb25mbHVlbmNlVXJsIjogImh0dHBzOi8vZmVlZGJhY2tsb29wYWkuYXRsYXNzaWFuLm5ldC93aWtpLyIsICJ1c2VybmFtZSI6"
    
    print("🔍 Debugging Smithery Configuration")
    print("=" * 50)
    print(f"Base64 string from logs: {base64_config}")
    print(f"Length: {len(base64_config)}")
    print()
    
    # Try to decode what we have
    try:
        # The string appears to be truncated, but let's see what we can decode
        for padding in ["", "=", "==", "==="]:
            try:
                padded_string = base64_config + padding
                decoded_bytes = base64.b64decode(padded_string)
                decoded_str = decoded_bytes.decode('utf-8')
                print(f"✅ Decoded with padding '{padding}':")
                print(f"Raw: {decoded_str}")
                print()
                
                # Try to parse as JSON (might be incomplete)
                try:
                    config = json.loads(decoded_str)
                    print("✅ Valid JSON found:")
                    for key, value in config.items():
                        if 'token' in key.lower():
                            print(f"  {key}: [MASKED]")
                        else:
                            print(f"  {key}: {value}")
                    return config
                except json.JSONDecodeError:
                    print("⚠️  Not valid JSON (string is truncated)")
                    print()
                    
            except Exception as e:
                continue
                
        print("❌ Could not decode - string appears to be truncated")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return None

def analyze_truncation():
    """Analyze why the config might be truncated."""
    print("\n🔍 Analyzing truncation issue...")
    print("=" * 50)
    
    # The logs show the config has length 176, but we only see the first ~100 chars
    # This suggests the logging is truncating the output
    
    print("HYPOTHESIS: The base64 config is being truncated in the logs")
    print("- Server receives full config (length 176)")
    print("- Logs truncate the display for readability") 
    print("- The actual issue is elsewhere")
    print()
    
    print("POSSIBLE ROOT CAUSES:")
    print("1. Server correctly receives config but has a bug in parsing")
    print("2. Smithery is sending placeholder values despite UI showing real ones")
    print("3. There's a caching issue where old config is being used")
    print("4. Environment variable override is happening somewhere")
    print()

def create_test_config():
    """Create a test config to see what should be sent."""
    print("\n🧪 Creating test configuration...")
    print("=" * 50)
    
    test_config = {
        "confluenceUrl": "https://feedbackloopai.atlassian.net/wiki/",
        "username": "chughes@feedbackloopai.ai",
        "apiToken": "ATATT3xFfGF0T3JlWWNaJQo5cjBxYWs1N1BLUExample"
    }
    
    # Encode to base64
    json_str = json.dumps(test_config)
    base64_encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    print(f"Test JSON: {json_str}")
    print(f"Test JSON length: {len(json_str)}")
    print(f"Test base64: {base64_encoded}")
    print(f"Test base64 length: {len(base64_encoded)}")
    print()
    
    print("COMPARISON:")
    print(f"Your config length: 176 chars (from logs)")
    print(f"Test config length: {len(base64_encoded)} chars") 
    print()
    
    if len(base64_encoded) > 176:
        print("⚠️  Your config is shorter than expected - might be missing the API token")
    elif len(base64_encoded) < 176:
        print("⚠️  Your config is longer than expected - might have extra fields")
    else:
        print("✅ Length matches - config structure looks correct")

def main():
    """Main debug function."""
    debug_smithery_config()
    analyze_truncation()
    create_test_config()
    
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    print("1. The issue is likely NOT in the base64 decoding")
    print("2. Check if Smithery is actually sending placeholder values")
    print("3. Add more detailed logging to see the full decoded config")
    print("4. Verify no environment variable overrides are happening")
    print("5. Check for config caching issues in Smithery")

if __name__ == "__main__":
    main() 