# confluence_mcp_server/mcp_actions/page_actions.py

from atlassian import Confluence
from .schemas import GetPageInput, GetPageOutput
from fastapi import HTTPException

def get_page_logic(
    client: Confluence,
    inputs: GetPageInput
) -> GetPageOutput:
    """
    Logic for the Get_Page tool.
    Fetches a specific page from Confluence by its ID, or by its space key and title.
    """
    # Forcing a re-evaluation of this file's bytecode
    page_data = None
    error_detail_prefix = ""
    try:
        print(f"DEBUG: get_page_logic called with inputs: page_id={inputs.page_id}, space_key={inputs.space_key}, title={inputs.title}, expand={inputs.expand}") # Debug line
        if inputs.page_id is not None:
            print(f"Calling Confluence API get_page_by_id with page_id: {inputs.page_id}, expand: {inputs.expand}")
            page_data = client.get_page_by_id(page_id=inputs.page_id, expand=inputs.expand)
            error_detail_prefix = f"Page with ID {inputs.page_id}"
        elif inputs.space_key and inputs.title:
            print(f"Calling Confluence API get_page_by_title with space_key: {inputs.space_key}, title: {inputs.title}, expand: {inputs.expand}")
            # Note: get_page_by_title does not directly support 'expand' in atlassian-python-api as of 4.0.3
            # We would typically fetch by title, get the ID, then fetch by ID with expand if needed.
            # For simplicity here, we'll assume get_page_by_title returns enough, or we handle expansion post-fetch if necessary.
            # However, the library's get_page_by_title *does* pass through expand kwargs to the underlying get_page_by_id it uses after finding the page list by title.
            page_data = client.get_page_by_title(space=inputs.space_key, title=inputs.title, expand=inputs.expand)
            error_detail_prefix = f"Page with title '{inputs.title}' in space '{inputs.space_key}'"
        # The GetPageInput model validator should prevent a state where neither condition is met.

        if not page_data:
            print(f"DEBUG: page_data is None or empty after API call.") # Debug line
            raise HTTPException(status_code=404, detail=f"{error_detail_prefix} not found.")

        print(f"DEBUG: page_data received from API mock: {page_data}") # Debug line

        # Extract space key - it might be directly available or nested if 'space' is expanded
        space_key_val = "UNKNOWN"
        if 'space' in page_data and isinstance(page_data['space'], dict) and 'key' in page_data['space']:
            space_key_val = page_data['space']['key']
        elif 'spaceKey' in page_data: # Fallback if spaceKey is a top-level attribute (less common for get_page_by_id)
             space_key_val = page_data['spaceKey']
        
        # Extract content if available (depends on expand='body.storage')
        content_val = None
        print(f"DEBUG: Attempting to extract content. page_data.get('body'): {page_data.get('body')}") # Debug line
        if 'body' in page_data and isinstance(page_data['body'], dict) and 'storage' in page_data['body'] and isinstance(page_data['body']['storage'], dict) and 'value' in page_data['body']['storage']:
            content_val = page_data['body']['storage']['value']
        print(f"DEBUG: content_val after extraction: {content_val}") # Debug line
        
        # Extract version if available (depends on expand='version')
        version_val = None
        print(f"DEBUG: Attempting to extract version. page_data.get('version'): {page_data.get('version')}") # Debug line
        if 'version' in page_data and isinstance(page_data['version'], dict) and 'number' in page_data['version']:
            version_val = page_data['version']['number']
        print(f"DEBUG: version_val after extraction: {version_val}") # Debug line

        # Construct web_url
        # The base URL needs to be from the client or config, as page_data._links.webui might be relative or absolute depending on API.
        # For simplicity, assuming CONFLUENCE_URL from env is the base for web UI.
        # A more robust way is to parse page_data['_links']['webui'] or page_data['_links']['self'] and combine.
        # For cloud, it's typically f"{CONFLUENCE_URL}/wiki{page_data['_links']['webui']}"
        web_ui_link = ""
        if '_links' in page_data and 'webui' in page_data['_links']:
            web_ui_link = page_data['_links']['webui'] # This is usually like "/spaces/KEY/pages/ID"
            # To make it absolute, we need the base URL.
            # We will construct it using the client's url attribute, assuming it's the base.
            # The client.url might end with /rest/api, so we need to strip that.
            base_url = client.url.split('/rest/api')[0]
            if not base_url.endswith('/wiki'): # Ensure /wiki is present for cloud URLs
                if not base_url.endswith('/'):
                    base_url += '/'
                base_url += 'wiki'
            web_url_val = f"{base_url}{web_ui_link}"
        elif 'url' in page_data: # some older API versions might have a direct URL
            web_url_val = page_data['url']
        else:
            web_url_val = "URL_NOT_FOUND"

        print(f"DEBUG: PRE-RETURN: page_id raw from page_data: {page_data.get('id')}, type: {type(page_data.get('id'))}") # Debug line
        print(f"DEBUG: PRE-RETURN: title: {page_data.get('title')}, space_key: {space_key_val}, status: {page_data.get('status', 'unknown')}, content: {content_val}, version: {version_val}, web_url: {web_url_val}") # Debug line
        
        output_object = GetPageOutput(
            page_id=page_data['id'],
            title=page_data['title'],
            space_key=space_key_val, 
            status=page_data.get('status', 'unknown'),
            content=content_val,
            version=version_val,
            web_url=web_url_val
        )
        print(f"DEBUG: POST-INSTANTIATION of GetPageOutput: {output_object.model_dump_json(indent=2)}") # Debug line
        return output_object

    except HTTPException: # Re-raise HTTPException to be caught by the endpoint handler
        raise
    except Exception as e:
        print(f"!!!!!!!!!! FATAL ERROR IN get_page_logic !!!!!!!!!=") # Enhanced Debug line
        print(f"!!!!!!!!!! TYPE: {type(e).__name__} !!!!!!!!!=") # Enhanced Debug line
        print(f"!!!!!!!!!! ARGS: {e.args} !!!!!!!!!=") # Enhanced Debug line
        import traceback
        print(traceback.format_exc()) # Print full traceback
        print(f"Error encountered in get_page_logic: {type(e).__name__} - {e}")
        # Determine lookup method for error message
        lookup_method_desc = ""
        if inputs.page_id is not None:
            lookup_method_desc = f"page ID {inputs.page_id}"
        elif inputs.space_key and inputs.title:
            lookup_method_desc = f"page title '{inputs.title}' in space '{inputs.space_key}'"
        else:
            lookup_method_desc = "the specified parameters"

        # Convert other exceptions to a generic 500 error for the tool execution
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching page using {lookup_method_desc}: {str(e)}")
