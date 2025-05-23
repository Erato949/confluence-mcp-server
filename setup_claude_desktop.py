#!/usr/bin/env python3
"""
Confluence MCP Server v1.0.0 - Production Ready
Claude Desktop Configuration Setup Script
"""

import json
import os
import platform
import shutil
from pathlib import Path


def get_claude_config_path():
    """Get the Claude Desktop configuration file path based on the operating system."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    else:
        raise OSError(f"Unsupported operating system: {system}")


def get_project_root():
    """Get the absolute path to the project root directory."""
    return Path(__file__).parent.absolute()


def create_claude_config():
    """Create or update Claude Desktop configuration."""
    config_path = get_claude_config_path()
    project_root = get_project_root()
    main_py_path = project_root / "confluence_mcp_server" / "main.py"
    
    # Ensure the Claude config directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Ensure mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add or update Confluence MCP server configuration
    # 🔒 SECURITY: Using placeholder values - NEVER commit real credentials
    config["mcpServers"]["confluence-mcp"] = {
        "command": "python",
        "args": [str(main_py_path)],
        "env": {
            "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki/",
            "CONFLUENCE_USERNAME": "your-email@example.com", 
            "CONFLUENCE_API_TOKEN": "YOUR_API_TOKEN_HERE"
        }
    }
    
    # Write updated configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path, main_py_path


def main():
    """Main setup function."""
    print("🔧 Confluence MCP Server - Claude Desktop Setup")
    print("=" * 50)
    
    try:
        config_path, main_py_path = create_claude_config()
        
        print(f"✅ Configuration file updated: {config_path}")
        print(f"📁 MCP Server path: {main_py_path}")
        print()
        print("🚨 IMPORTANT: You must update the environment variables in the config:")
        print(f"   - Edit: {config_path}")
        print("   - Update CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN")
        print()
        print("📋 Next steps:")
        print("1. Open the configuration file above")
        print("2. Replace placeholder values with your actual Confluence credentials")
        print("3. Restart Claude Desktop")
        print("4. Look for the 🔨 hammer icon in Claude Desktop to access MCP tools")
        print()
        print("🔧 Available tools after setup:")
        print("   - get_confluence_page")
        print("   - create_confluence_page") 
        print("   - update_confluence_page")
        print("   - delete_confluence_page")
        print("   - search_confluence_pages")
        print("   - get_confluence_spaces")
        print("   - get_page_attachments")
        print("   - add_page_attachment")
        print("   - delete_page_attachment")
        print("   - get_page_comments")
        
    except OSError as e:
        print(f"❌ Error: {e}")
        print("This script only supports macOS and Windows.")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 