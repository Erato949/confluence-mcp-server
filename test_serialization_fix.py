#!/usr/bin/env python3
"""
Test script to validate the JSON serialization fix for HttpUrl objects.
"""

import json
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic import BaseModel, HttpUrl
from confluence_mcp_server.mcp_actions.schemas import SpaceOutputItem, GetSpacesOutput

def test_json_serialization():
    """Test that HttpUrl objects are properly serialized to JSON."""
    
    # Create a test space item with HttpUrl
    space_item = SpaceOutputItem(
        space_id=123,
        key="TEST",
        name="Test Space",
        type="global",
        status="current",
        url="https://example.atlassian.net/wiki/spaces/TEST"
    )
    
    print("Testing individual SpaceOutputItem serialization...")
    
    # Test model_dump() without mode (original problematic method)
    try:
        result_dict_old = space_item.model_dump()
        json_str_old = json.dumps(result_dict_old, indent=2)
        print("❌ OLD METHOD: model_dump() without mode - This should fail!")
        print(f"JSON: {json_str_old}")
    except Exception as e:
        print(f"✅ OLD METHOD FAILED (as expected): {type(e).__name__}: {str(e)}")
    
    # Test model_dump(mode='json') (fixed method)
    try:
        result_dict_new = space_item.model_dump(mode='json')
        json_str_new = json.dumps(result_dict_new, indent=2)
        print("✅ NEW METHOD: model_dump(mode='json') - This should work!")
        print(f"JSON: {json_str_new}")
    except Exception as e:
        print(f"❌ NEW METHOD FAILED: {type(e).__name__}: {str(e)}")
    
    print("\nTesting GetSpacesOutput with multiple spaces...")
    
    # Create a more complex object with multiple spaces
    spaces_output = GetSpacesOutput(
        spaces=[
            SpaceOutputItem(
                space_id=123,
                key="TEST1",
                name="Test Space 1",
                type="global",
                status="current",
                url="https://example.atlassian.net/wiki/spaces/TEST1"
            ),
            SpaceOutputItem(
                space_id=456,
                key="TEST2",
                name="Test Space 2",
                type="personal",
                status="current",
                url="https://example.atlassian.net/wiki/spaces/TEST2"
            )
        ],
        total_available=2,
        next_start_offset=None
    )
    
    # Test the fixed method on complex object
    try:
        result_dict = spaces_output.model_dump(mode='json')
        json_str = json.dumps(result_dict, indent=2)
        print("✅ COMPLEX OBJECT: GetSpacesOutput serialization works!")
        print(f"JSON (first 200 chars): {json_str[:200]}...")
        
        # Verify that URLs are strings in the result
        first_space_url = result_dict['spaces'][0]['url']
        print(f"✅ URL type in result: {type(first_space_url)} (should be str)")
        print(f"✅ URL value: {first_space_url}")
        
    except Exception as e:
        print(f"❌ COMPLEX OBJECT FAILED: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING JSON SERIALIZATION FIX FOR HttpUrl OBJECTS")
    print("=" * 60)
    test_json_serialization()
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60) 