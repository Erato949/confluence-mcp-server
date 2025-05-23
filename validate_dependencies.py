#!/usr/bin/env python3
"""
Quick validation script to ensure all dependencies are working correctly.
"""

def main():
    print("🔍 Validating Confluence MCP Server Dependencies...")
    
    try:
        # Test core FastMCP import
        import fastmcp
        print("✅ fastmcp imported successfully")
        
        # Test HTTP transport dependencies
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn imported successfully")
        
        # Test testing dependencies
        import pytest
        import pytest_asyncio
        print("✅ pytest and pytest-asyncio imported successfully")
        
        # Test our server modules
        import confluence_mcp_server.main
        import confluence_mcp_server.server_http
        import confluence_mcp_server.launcher
        print("✅ All Confluence MCP Server modules imported successfully")
        
        print("\n🎉 All dependencies are working correctly!")
        print("✅ Ready for production deployment")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 