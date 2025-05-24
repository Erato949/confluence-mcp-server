#!/usr/bin/env python3
"""
Script to fix the indentation issue in main.py
"""

def fix_setup_environment_function():
    """Fix the indentation in the setup_environment function."""
    
    # Read the current file
    with open('confluence_mcp_server/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic function
    old_function = '''async def setup_environment():
        """Setup environment variables and logging for the server."""
    # Load environment variables from .env file with explicit path'''
    
    new_function = '''async def setup_environment():
    """Setup environment variables and logging for the server."""
    # Load environment variables from .env file with explicit path'''
    
    # Replace the function
    if old_function in content:
        content = content.replace(old_function, new_function)
        print("Found and fixed the function header")
    else:
        print("Could not find the exact function header to fix")
        return False
    
    # Write the fixed content back
    with open('confluence_mcp_server/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("File has been fixed")
    return True

if __name__ == "__main__":
    fix_setup_environment_function() 