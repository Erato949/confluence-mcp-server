#!/usr/bin/env python3
"""
Test script for Smithery.ai configuration support
Tests the dual configuration system (env vars + Smithery config)
"""

import os
import sys
import json
import base64
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch

# Add project root to path so we can import the main module
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the functions we want to test
from confluence_mcp_server.main import (
    detect_and_apply_smithery_config,
    _parse_config_parameter,
    _apply_smithery_config_to_env
)

# Setup test logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_parse_config_parameter():
    """Test parsing of various config parameter formats."""
    print("\n=== Testing _parse_config_parameter ===")
    
    # Test 1: Direct JSON string
    json_config = '{"confluenceUrl": "https://test.atlassian.net", "username": "test@example.com", "apiToken": "test-token"}'
    result = _parse_config_parameter(json_config)
    assert result is not None, "Should parse direct JSON"
    assert result["confluenceUrl"] == "https://test.atlassian.net"
    print("✅ Direct JSON parsing works")
    
    # Test 2: Base64 encoded JSON
    encoded_config = base64.b64encode(json_config.encode()).decode()
    result = _parse_config_parameter(encoded_config)
    assert result is not None, "Should parse base64 encoded JSON"
    assert result["username"] == "test@example.com"
    print("✅ Base64 encoded JSON parsing works")
    
    # Test 3: Invalid format
    result = _parse_config_parameter("invalid-config")
    assert result is None, "Should return None for invalid config"
    print("✅ Invalid config handling works")
    
    print("✅ All _parse_config_parameter tests passed!")

def test_apply_smithery_config_to_env():
    """Test applying Smithery config to environment variables."""
    print("\n=== Testing _apply_smithery_config_to_env ===")
    
    # Clear any existing env vars for clean test
    original_env = {}
    for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN"]:
        original_env[var] = os.getenv(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        # Test config data
        config_data = {
            "confluenceUrl": "https://smithery-test.atlassian.net",
            "username": "smithery@example.com", 
            "apiToken": "smithery-test-token"
        }
        
        # Apply config
        applied = _apply_smithery_config_to_env(config_data)
        
        # Verify environment variables were set
        assert os.getenv("CONFLUENCE_URL") == "https://smithery-test.atlassian.net"
        assert os.getenv("CONFLUENCE_USERNAME") == "smithery@example.com"
        assert os.getenv("CONFLUENCE_API_TOKEN") == "smithery-test-token"
        
        assert len(applied) == 3, "Should have applied 3 config values"
        print("✅ Config applied to environment variables correctly")
        
        # Test that existing env vars are preserved
        os.environ["CONFLUENCE_URL"] = "existing-url"
        config_data_2 = {"confluenceUrl": "new-url"}
        
        applied_2 = _apply_smithery_config_to_env(config_data_2)
        
        # Should preserve existing value
        assert os.getenv("CONFLUENCE_URL") == "existing-url"
        assert "CONFLUENCE_URL" not in applied_2
        print("✅ Existing environment variables are preserved")
        
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    print("✅ All _apply_smithery_config_to_env tests passed!")

def test_detect_and_apply_smithery_config():
    """Test the main Smithery config detection function."""
    print("\n=== Testing detect_and_apply_smithery_config ===")
    
    # Clear environment for clean test
    original_env = {}
    for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN", 
                "SMITHERY_CONFIG", "MCP_CONFIG", "SMITHERY_CONFLUENCE_URL", 
                "SMITHERY_USERNAME", "SMITHERY_API_TOKEN"]:
        original_env[var] = os.getenv(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        # Test 1: Command line argument detection
        test_config = {
            "confluenceUrl": "https://cmd-test.atlassian.net",
            "username": "cmd@example.com",
            "apiToken": "cmd-token"
        }
        config_json = json.dumps(test_config)
        
        with patch.object(sys, 'argv', ['main.py', '--config', config_json]):
            result = detect_and_apply_smithery_config()
            assert result is not None, "Should detect command line config"
            assert os.getenv("CONFLUENCE_URL") == "https://cmd-test.atlassian.net"
            print("✅ Command line config detection works")
        
        # Clean up
        for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN"]:
            if var in os.environ:
                del os.environ[var]
        
        # Test 2: Environment variable detection (SMITHERY_CONFIG)
        encoded_config = base64.b64encode(config_json.encode()).decode()
        os.environ["SMITHERY_CONFIG"] = encoded_config
        
        result = detect_and_apply_smithery_config()
        assert result is not None, "Should detect SMITHERY_CONFIG"
        assert os.getenv("CONFLUENCE_USERNAME") == "cmd@example.com"
        print("✅ SMITHERY_CONFIG environment variable detection works")
        
        # Clean up
        del os.environ["SMITHERY_CONFIG"]
        for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN"]:
            if var in os.environ:
                del os.environ[var]
        
        # Test 3: Individual Smithery environment variables
        os.environ["SMITHERY_CONFLUENCE_URL"] = "https://individual-test.atlassian.net"
        os.environ["SMITHERY_USERNAME"] = "individual@example.com"
        os.environ["SMITHERY_API_TOKEN"] = "individual-token"
        
        result = detect_and_apply_smithery_config()
        assert result is not None, "Should detect individual Smithery env vars"
        assert os.getenv("CONFLUENCE_URL") == "https://individual-test.atlassian.net"
        print("✅ Individual Smithery environment variable detection works")
        
        # Test 4: No config present
        for var in ["SMITHERY_CONFLUENCE_URL", "SMITHERY_USERNAME", "SMITHERY_API_TOKEN"]:
            del os.environ[var]
        for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN"]:
            if var in os.environ:
                del os.environ[var]
        
        result = detect_and_apply_smithery_config()
        assert result is None, "Should return None when no config is present"
        print("✅ No config handling works")
        
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    print("✅ All detect_and_apply_smithery_config tests passed!")

def test_integration_scenario():
    """Test a realistic integration scenario."""
    print("\n=== Testing Integration Scenario ===")
    
    # Simulate Smithery.ai deployment scenario
    smithery_config = {
        "confluenceUrl": "https://mycompany.atlassian.net",
        "username": "api-user@mycompany.com",
        "apiToken": "ATATT3xFfGF0-sample-token-here"
    }
    
    # Encode as Smithery would
    config_json = json.dumps(smithery_config)
    encoded_config = base64.b64encode(config_json.encode()).decode()
    
    # Clear environment
    original_env = {}
    for var in ["CONFLUENCE_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN", "SMITHERY_CONFIG"]:
        original_env[var] = os.getenv(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        # Simulate Smithery setting the config
        os.environ["SMITHERY_CONFIG"] = encoded_config
        
        # Test detection and application
        result = detect_and_apply_smithery_config()
        
        # Verify the configuration was applied correctly
        assert result is not None, "Config should be detected"
        assert len(result) == 3, "Should apply all 3 config values"
        
        # Verify environment variables are set correctly
        assert os.getenv("CONFLUENCE_URL") == "https://mycompany.atlassian.net"
        assert os.getenv("CONFLUENCE_USERNAME") == "api-user@mycompany.com"
        assert os.getenv("CONFLUENCE_API_TOKEN") == "ATATT3xFfGF0-sample-token-here"
        
        print("✅ Integration scenario works perfectly!")
        print(f"   - Config detected: {list(result.keys())}")
        print(f"   - URL: {os.getenv('CONFLUENCE_URL')}")
        print(f"   - Username: {os.getenv('CONFLUENCE_USERNAME')}")
        print(f"   - Token: {os.getenv('CONFLUENCE_API_TOKEN')[:10]}...")
        
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

def main():
    """Run all tests."""
    print("🧪 Testing Smithery.ai Configuration Support")
    print("=" * 50)
    
    try:
        test_parse_config_parameter()
        test_apply_smithery_config_to_env()
        test_detect_and_apply_smithery_config()
        test_integration_scenario()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Smithery.ai configuration support is working correctly")
        print("✅ Ready for deployment to Smithery.ai")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    main() 