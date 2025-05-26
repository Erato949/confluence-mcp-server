#!/usr/bin/env python3
"""
Setup script for local Confluence MCP Server configuration
This script helps configure the server for local Claude Desktop use
"""

import os
import json
import base64
from pathlib import Path

def decode_smithery_config():
    """Decode the Smithery config to extract actual credentials."""
    # This is the config from the logs
    smithery_config_b64 = "eyJjb25mbHVlbmNlVXJsIjogImh0dHBzOi8vZmVlZGJhY2tsb29wYWkuYXRsYXNzaWFuLm5ldC93aWtpLyIsICJ1c2VybmFtZSI6..."
    
    try:
        # Try to decode the base64 config
        decoded_bytes = base64.b64decode(smithery_config_b64 + "==")  # Add padding if needed
        config_json = decoded_bytes.decode('utf-8')
        config = json.loads(config_json)
        return config
    except Exception as e:
        print(f"Could not decode Smithery config: {e}")
        return None

def create_env_file():
    """Create .env file with actual credentials."""
    env_content = """# Confluence MCP Server - Local Environment Configuration
# Extracted from Smithery deployment

CONFLUENCE_URL="https://feedbackloopai.atlassian.net/wiki/"
CONFLUENCE_USERNAME="chughes@feedbackloopai.ai"
CONFLUENCE_API_TOKEN="YOUR_ACTUAL_API_TOKEN_HERE"

# Note: Replace YOUR_ACTUAL_API_TOKEN_HERE with your actual Confluence API token
# Get it from: https://id.atlassian.com/manage-profile/security/api-tokens
"""
    
    env_path = Path(".env")
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_path}")
        print("⚠️  Remember to replace YOUR_ACTUAL_API_TOKEN_HERE with your actual token")
    except Exception as e:
        print(f"❌ Could not create .env file: {e}")

def update_claude_desktop_config():
    """Update Claude Desktop config to use the correct server."""
    config_path = Path("claude_desktop_config.json")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update to use the optimized server
        if "confluence-mcp" in config.get("mcpServers", {}):
            # Option 1: Use the optimized HTTP server
            config["mcpServers"]["confluence-mcp"]["args"] = [
                "C:\\Users\\chris\\Documents\\Confluence-MCP-Server_Claude\\confluence_mcp_server\\server_http_optimized.py"
            ]
            
            # Remove the placeholder token - it will be loaded from .env
            if "env" in config["mcpServers"]["confluence-mcp"]:
                env_config = config["mcpServers"]["confluence-mcp"]["env"]
                if "CONFLUENCE_API_TOKEN" in env_config:
                    del env_config["CONFLUENCE_API_TOKEN"]  # Will be loaded from .env
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated {config_path} to use optimized server")
        
    except Exception as e:
        print(f"❌ Could not update Claude Desktop config: {e}")

def main():
    """Main setup function."""
    print("🔧 Setting up local Confluence MCP Server configuration...")
    print()
    
    # Step 1: Create .env file
    print("Step 1: Creating .env file...")
    create_env_file()
    print()
    
    # Step 2: Update Claude Desktop config
    print("Step 2: Updating Claude Desktop configuration...")
    update_claude_desktop_config()
    print()
    
    print("📋 Next steps:")
    print("1. Edit .env file and replace YOUR_ACTUAL_API_TOKEN_HERE with your actual API token")
    print("2. Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens")
    print("3. Restart Claude Desktop")
    print("4. Test the MCP server connection")
    print()
    print("🔍 To test locally, you can also run:")
    print("   python test_smithery_config.py")

if __name__ == "__main__":
    main() 