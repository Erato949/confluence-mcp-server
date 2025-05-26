#!/usr/bin/env python3
"""
Decode Smithery configuration to extract the actual API token
This script decodes the base64 configuration from the server logs
"""

import base64
import json

def decode_smithery_config():
    """Decode the actual Smithery config from the logs."""
    
    # This is the actual config from your server logs
    smithery_config_b64 = "eyJjb25mbHVlbmNlVXJsIjogImh0dHBzOi8vZmVlZGJhY2tsb29wYWkuYXRsYXNzaWFuLm5ldC93aWtpLyIsICJ1c2VybmFtZSI6"
    
    # The log shows it was truncated, so let's try to get the full config
    # From the logs, we can see it's length 176, let's reconstruct what we can
    
    print("Attempting to decode Smithery configuration...")
    print(f"Base64 string length: {len(smithery_config_b64)}")
    
    try:
        # Try with padding
        for padding in ["", "=", "==", "==="]:
            try:
                decoded_bytes = base64.b64decode(smithery_config_b64 + padding)
                config_json = decoded_bytes.decode('utf-8')
                print(f"✅ Successfully decoded with padding '{padding}':")
                print(f"Decoded JSON: {config_json}")
                
                try:
                    config = json.loads(config_json)
                    print("✅ Successfully parsed JSON:")
                    for key, value in config.items():
                        if key.lower() in ['apitoken', 'api_token', 'token']:
                            print(f"  {key}: {'*' * min(len(str(value)), 20)} (masked)")
                        else:
                            print(f"  {key}: {value}")
                    return config
                except json.JSONDecodeError as je:
                    print(f"  ⚠️ JSON decode error: {je}")
                    print(f"  Raw content: {config_json}")
                    
            except Exception as e:
                continue
                
        print("❌ Could not decode the base64 string with any padding")
        return None
        
    except Exception as e:
        print(f"❌ Error decoding: {e}")
        return None

def get_token_from_smithery():
    """Instructions for getting the token from Smithery."""
    print("\n" + "="*60)
    print("OPTION 1: Get token from Smithery directly")
    print("="*60)
    print("1. Go to your Smithery deployment dashboard")
    print("2. Look for environment variables or configuration")
    print("3. Find the CONFLUENCE_API_TOKEN value")
    print("4. Copy it to your .env file")
    
def get_token_from_atlassian():
    """Instructions for creating a new token."""
    print("\n" + "="*60)
    print("OPTION 2: Create a new API token")
    print("="*60)
    print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Log in with your Atlassian account (chughes@feedbackloopai.ai)")
    print("3. Click 'Create API token'")
    print("4. Give it a name like 'Claude MCP Server'")
    print("5. Copy the generated token")
    print("6. Paste it in your .env file")

def update_env_file_instructions():
    """Show how to update the .env file."""
    print("\n" + "="*60)
    print("FINAL STEP: Update your .env file")
    print("="*60)
    print("1. Open the .env file in this directory")
    print("2. Replace 'YOUR_ACTUAL_API_TOKEN_HERE' with your actual token")
    print("3. Save the file")
    print("4. Restart Claude Desktop")
    print("5. Test the connection")

def main():
    """Main function."""
    print("🔓 Smithery Configuration Decoder")
    print("=" * 50)
    
    # Try to decode the config
    config = decode_smithery_config()
    
    # Show alternative options
    get_token_from_smithery()
    get_token_from_atlassian()
    update_env_file_instructions()
    
    print("\n✅ Once you've updated the .env file, restart Claude Desktop and try using the Confluence tools!")

if __name__ == "__main__":
    main() 