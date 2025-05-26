#!/usr/bin/env python3
"""
Comprehensive Confluence MCP Server Issue Resolver
This script helps diagnose and fix both local config and Confluence permission issues
"""

import os
import json
import asyncio
import httpx
from pathlib import Path

async def test_confluence_connection(url, username, token):
    """Test Confluence connection with given credentials."""
    print(f"\n🔍 Testing Confluence connection...")
    print(f"URL: {url}")
    print(f"Username: {username}")
    print(f"Token: {'*' * min(len(token), 10)}...")
    
    # Clean up URL for API calls
    base_url = url.rstrip('/wiki/').rstrip('/')
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'https://{base_url}'
    
    print(f"Base URL for API: {base_url}")
    
    try:
        async with httpx.AsyncClient(
            base_url=base_url,
            auth=(username, token),
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        ) as client:
            
            # Test 1: Basic API connectivity
            print("\n📡 Test 1: Basic API connectivity...")
            try:
                response = await client.get('/wiki/rest/api/user/current')
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ Authentication successful!")
                    print(f"   User: {user_data.get('displayName', 'Unknown')}")
                    print(f"   Account ID: {user_data.get('accountId', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Client setup failed: {e}")
        return False

async def test_confluence_permissions(url, username, token):
    """Test specific Confluence permissions."""
    print(f"\n🔐 Testing Confluence permissions...")
    
    base_url = url.rstrip('/wiki/').rstrip('/')
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'https://{base_url}'
    
    try:
        async with httpx.AsyncClient(
            base_url=base_url,
            auth=(username, token),
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        ) as client:
            
            # Test 2: Space access
            print("\n📂 Test 2: Space access...")
            try:
                response = await client.get('/wiki/rest/api/space?limit=1')
                if response.status_code == 200:
                    spaces = response.json()
                    print(f"✅ Can access spaces! Found {spaces.get('size', 0)} spaces")
                    if spaces.get('results'):
                        space = spaces['results'][0]
                        print(f"   Sample space: {space.get('name', 'Unknown')}")
                elif response.status_code == 403:
                    print(f"❌ No permission to access spaces")
                    print(f"   This is the root cause of your issue!")
                    return False
                else:
                    print(f"⚠️  Unexpected response: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
            except Exception as e:
                print(f"❌ Space test failed: {e}")
                return False
            
            # Test 3: Page search
            print("\n📄 Test 3: Page search permissions...")
            try:
                response = await client.get('/wiki/rest/api/content?limit=1')
                if response.status_code == 200:
                    content = response.json()
                    print(f"✅ Can search pages! Found {content.get('size', 0)} pages")
                elif response.status_code == 403:
                    print(f"❌ No permission to search pages")
                    return False
                else:
                    print(f"⚠️  Unexpected response: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Page search test failed: {e}")
                return False
                
            return True
            
    except Exception as e:
        print(f"❌ Permission tests failed: {e}")
        return False

def check_local_config():
    """Check local configuration files."""
    print("\n📋 Checking local configuration...")
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file exists")
        with open(env_path, 'r') as f:
            content = f.read()
            if "YOUR_ACTUAL_API_TOKEN_HERE" in content:
                print("❌ .env file still has placeholder token!")
                return False
            else:
                print("✅ .env file appears to have real token")
    else:
        print("❌ .env file missing")
        return False
    
    # Check Claude Desktop config
    config_path = Path("claude_desktop_config.json")
    if config_path.exists():
        print("✅ Claude Desktop config exists")
        with open(config_path, 'r') as f:
            config = json.load(f)
            if "server_http_optimized.py" in str(config):
                print("✅ Using optimized server")
            else:
                print("⚠️  Not using optimized server")
    else:
        print("❌ Claude Desktop config missing")
        return False
    
    return True

def show_permission_fix_instructions():
    """Show instructions for fixing Confluence permissions."""
    print("\n" + "="*70)
    print("🔧 CONFLUENCE PERMISSION ISSUE - HOW TO FIX")
    print("="*70)
    print("""
The 403 "Current user not permitted to use Confluence" error means your 
account doesn't have the right permissions. Here's how to fix it:

1. CHECK YOUR CONFLUENCE ACCESS:
   - Go to https://feedbackloopai.atlassian.net/wiki/
   - Log in with chughes@feedbackloopai.ai
   - Verify you can see and access Confluence pages

2. CHECK YOUR API TOKEN:
   - The token must be for the SAME account that has Confluence access
   - If you created the token with a different account, that's the problem
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Make sure you're logged in as chughes@feedbackloopai.ai
   - Create a new token if needed

3. CHECK CONFLUENCE PERMISSIONS:
   - Ask your Confluence admin to verify your account has:
     - "Can use" permission for Confluence
     - Access to at least one space
     - "View" permissions on spaces you want to access

4. ALTERNATIVE - USE A SERVICE ACCOUNT:
   - Ask your admin to create a service account for API access
   - Use that account's credentials instead

5. VERIFY IN SMITHERY:
   - Make sure Smithery is using the correct credentials
   - The username in the logs shows 'your-email@domain.com' which looks like a placeholder
   - This might be why it's failing!
""")

def show_local_fix_instructions():
    """Show instructions for fixing local configuration."""
    print("\n" + "="*70)
    print("🔧 LOCAL CONFIGURATION - HOW TO FIX")
    print("="*70)
    print("""
To fix the local "Request URL is missing protocol" error:

1. GET YOUR API TOKEN:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Log in as chughes@feedbackloopai.ai (make sure it's the right account!)
   - Create a new API token named "Claude MCP Server"
   - Copy the token value

2. UPDATE YOUR .env FILE:
   - Open the .env file in this directory
   - Replace YOUR_ACTUAL_API_TOKEN_HERE with your real token
   - Save the file

3. RESTART CLAUDE DESKTOP:
   - Completely quit Claude Desktop
   - Restart it
   - The MCP server should now work

4. TEST THE CONNECTION:
   - Try using a Confluence tool in Claude
   - If it still fails, run this script again to diagnose
""")

async def main():
    """Main diagnostic function."""
    print("🩺 Confluence MCP Server Issue Resolver")
    print("="*50)
    
    # Check local config first
    local_ok = check_local_config()
    
    # Try to load credentials
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        url = os.getenv("CONFLUENCE_URL")
        username = os.getenv("CONFLUENCE_USERNAME") 
        token = os.getenv("CONFLUENCE_API_TOKEN")
        
        if not all([url, username, token]) or token == "YOUR_ACTUAL_API_TOKEN_HERE":
            print("❌ Configuration incomplete or has placeholder values")
            show_local_fix_instructions()
            return
        
        # Test the connection
        auth_ok = await test_confluence_connection(url, username, token)
        if auth_ok:
            perm_ok = await test_confluence_permissions(url, username, token)
            if perm_ok:
                print("\n✅ ALL TESTS PASSED! Your Confluence MCP Server should work now.")
            else:
                show_permission_fix_instructions()
        else:
            print("\n❌ Authentication failed. Check your credentials.")
            show_local_fix_instructions()
            show_permission_fix_instructions()
            
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        show_local_fix_instructions()

if __name__ == "__main__":
    asyncio.run(main()) 