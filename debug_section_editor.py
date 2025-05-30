#!/usr/bin/env python3
"""
Debug script for SectionEditor
"""

from confluence_mcp_server.selective_editing.section_editor import SectionEditor

def test_basic_functionality():
    print("Creating SectionEditor...")
    editor = SectionEditor()
    print("✅ SectionEditor created successfully")
    
    print(f"XML parser type: {type(editor.xml_parser)}")
    print(f"Content analyzer type: {type(editor.content_analyzer)}")
    
    # Test simple content
    simple_content = """
    <div>
        <h1>Section One</h1>
        <p>Content of section one.</p>
        
        <h1>Section Two</h1>
        <p>Content of section two.</p>
    </div>
    """
    
    print("\nTesting replace_section...")
    try:
        result = editor.replace_section(
            content=simple_content,
            heading="Section One",
            new_content="<p>This is the new content for section one.</p>"
        )
        print(f"Result success: {result.success}")
        if not result.success:
            print(f"Error: {result.error_message}")
        else:
            print("✅ replace_section worked!")
            print(f"Modified content length: {len(result.modified_content) if result.modified_content else 0}")
    except Exception as e:
        print(f"❌ Exception in replace_section: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality() 