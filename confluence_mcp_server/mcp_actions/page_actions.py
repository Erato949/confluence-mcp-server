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
    Fetches a specific page from Confluence by its ID.
    """
    try:
        print(f"Calling Confluence API get_page_by_id with page_id: {inputs.page_id}, expand: {inputs.expand}")
        page_data = client.get_page_by_id(page_id=inputs.page_id, expand=inputs.expand)

        if not page_data:
            raise HTTPException(status_code=404, detail=f"Page with ID {inputs.page_id} not found.")

        # Extract space key - it might be directly available or nested if 'space' is expanded
        space_key_val = "UNKNOWN"
        if 'space' in page_data and isinstance(page_data['space'], dict) and 'key' in page_data['space']:
            space_key_val = page_data['space']['key']
        elif 'spaceKey' in page_data: # Fallback if spaceKey is a top-level attribute (less common for get_page_by_id)
             space_key_val = page_data['spaceKey']
        
        # Extract content if available (depends on expand='body.storage')
        content_val = None
        if 'body' in page_data and isinstance(page_data['body'], dict) and 'storage' in page_data['body'] and isinstance(page_data['body']['storage'], dict) and 'value' in page_data['body']['storage']:
            content_val = page_data['body']['storage']['value']
        
        # Extract version if available (depends on expand='version')
        version_val = None
        if 'version' in page_data and isinstance(page_data['version'], dict) and 'number' in page_data['version']:
            version_val = page_data['version']['number']

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

        return GetPageOutput(
            page_id=page_data['id'],
            title=page_data['title'],
            space_key=space_key_val, # Placeholder, needs proper extraction if 'space' is not expanded
            status=page_data.get('status', 'unknown'),
            content=content_val,
            version=version_val,
            web_url=web_url_val
        )

    except HTTPException: # Re-raise HTTPException to be caught by the endpoint handler
        raise
    except Exception as e:
        print(f"Error encountered in get_page_logic: {type(e).__name__} - {e}")
        # Convert other exceptions to a generic 500 error for the tool execution
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching page {inputs.page_id}: {str(e)}")

