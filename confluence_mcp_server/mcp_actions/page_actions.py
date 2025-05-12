# confluence_mcp_server/mcp_actions/page_actions.py

from atlassian import Confluence
from .schemas import GetPageInput, GetPageOutput, SearchPagesInput, SearchedPageSchema, SearchPagesOutput, CreatePageInput, CreatePageOutput
from fastapi import HTTPException
from typing import List, Dict, Any, Optional

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


def search_pages_logic(
    client: Confluence,
    inputs: SearchPagesInput
) -> SearchPagesOutput:
    """
    Logic for the search_pages tool.
    Searches Confluence pages using CQL.
    """
    try:
        print(f"DEBUG: search_pages_logic called with CQL: {inputs.cql}, limit: {inputs.limit}, start: {inputs.start}, expand: {inputs.expand}, excerpt: {inputs.excerpt}")

        # The atlassian-python-api's cql method returns a dictionary that usually includes:
        # 'results': list of page objects
        # 'start': the start point of the result set
        # 'limit': the page size
        # 'size': the number of results in the current page
        # 'totalSize': (optional, sometimes not present or accurate) total number of results available
        # '_links': contains links for pagination (e.g., 'next', 'prev')
        
        api_response = client.cql(
            cql=inputs.cql,
            limit=inputs.limit,
            start=inputs.start,
            expand=inputs.expand,
            excerpt=inputs.excerpt
            # include_archived_spaces is not a direct param for client.cql; it's part of CQL itself if needed.
        )

        if not api_response or 'results' not in api_response:
            print(f"DEBUG: CQL search for '{inputs.cql}' returned no results or unexpected response format.")
            return SearchPagesOutput(
                results=[],
                count=0,
                total_available=0,
                cql_query_used=inputs.cql,
                limit_used=inputs.limit,
                start_used=inputs.start,
                expand_used=inputs.expand,
                excerpt_used=inputs.excerpt
            )

        print(f"DEBUG: api_response from Confluence: {api_response}")

        processed_results: List[SearchedPageSchema] = []
        base_url = client.url.split('/rest/api')[0]
        if not base_url.endswith('/wiki'):
            if not base_url.endswith('/'):
                base_url += '/'
            base_url += 'wiki'

        for page_data in api_response.get('results', []):
            space_key_val = None
            if 'space' in page_data and isinstance(page_data['space'], dict) and 'key' in page_data['space']:
                space_key_val = page_data['space']['key']
            elif 'content' in page_data and isinstance(page_data['content'], dict) and \
                 'space' in page_data['content'] and isinstance(page_data['content']['space'], dict) and \
                 'key' in page_data['content']['space']:
                 space_key_val = page_data['content']['space']['key']

            content_val = None
            if 'body' in page_data and isinstance(page_data['body'], dict):
                if 'storage' in page_data['body'] and isinstance(page_data['body']['storage'], dict) and 'value' in page_data['body']['storage']:
                    content_val = page_data['body']['storage']['value']
                elif 'view' in page_data['body'] and isinstance(page_data['body']['view'], dict) and 'value' in page_data['body']['view']:
                    content_val = page_data['body']['view']['value']

            version_val = None
            if 'version' in page_data and isinstance(page_data['version'], dict) and 'number' in page_data['version']:
                version_val = page_data['version']['number']

            web_ui_link_path = ""
            if '_links' in page_data and 'webui' in page_data['_links']:
                web_ui_link_path = page_data['_links']['webui']
            elif 'content' in page_data and '_links' in page_data['content'] and 'webui' in page_data['content']['_links']:
                web_ui_link_path = page_data['content']['_links']['webui']
            
            web_url_val = f"{base_url}{web_ui_link_path}" if web_ui_link_path else "URL_NOT_FOUND"

            excerpt_highlight_val = None
            if inputs.excerpt == 'highlight': # Check if highlight was requested
                # The API might return it as 'excerpt' (common) or 'highlight' (less common but possible)
                # We prioritize 'excerpt' if present, then 'highlight'.
                if 'excerpt' in page_data:
                    excerpt_highlight_val = page_data.get('excerpt')
                elif 'highlight' in page_data:
                    excerpt_highlight_val = page_data.get('highlight')

            # Page ID and Title can be in 'content' or directly on the result object
            page_id_val = None
            title_val = "Untitled"
            status_val = "unknown"
            last_modified_val = None # Initialize

            content_obj = page_data.get('content', page_data) # Fallback to page_data if 'content' isn't there
            if isinstance(content_obj, dict):
                page_id_val = int(content_obj.get('id', 0))
                title_val = content_obj.get('title', 'Untitled')
                status_val = content_obj.get('status', 'unknown')
                # history.lastUpdated.when or similar for last_modified_date. Requires 'history.lastUpdated' in expand.
                if 'history' in content_obj and isinstance(content_obj['history'], dict) and \
                   'lastUpdated' in content_obj['history'] and isinstance(content_obj['history']['lastUpdated'], dict) and \
                   'when' in content_obj['history']['lastUpdated']:
                    last_modified_val = content_obj['history']['lastUpdated']['when']
            
            if page_id_val is None:
                # If still no page ID, skip this result as it's unusable for SearchedPageSchema
                print(f"DEBUG: Skipping result due to missing page ID. Raw data: {page_data}")
                continue

            processed_results.append(
                SearchedPageSchema(
                    page_id=page_id_val,
                    title=title_val,
                    space_key=space_key_val,
                    status=status_val,
                    excerpt_highlight=excerpt_highlight_val,
                    content=content_val,
                    version=version_val,
                    web_url=web_url_val,
                    last_modified_date=last_modified_val
                    # raw_result=page_data # If we decide to include raw results
                )
            )

        return SearchPagesOutput(
            results=processed_results,
            count=len(processed_results), # This is the number of items we successfully processed
            total_available=api_response.get('size'), # Use size from API (actual key)
            cql_query_used=inputs.cql,
            limit_used=inputs.limit,
            start_used=inputs.start,
            expand_used=inputs.expand,
            excerpt_used=inputs.excerpt
        )

    except HTTPException: # Re-raise HTTPException
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"Error during CQL search: {str(e)}"
        print(f"An unexpected error occurred in search_pages_logic: {error_type} - {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{error_type}: {error_msg}")

def create_page_logic(
    client: Confluence,
    inputs: CreatePageInput,
    base_url: str  # Base URL of the Confluence instance
) -> CreatePageOutput:
    """
    Logic for the create_page tool.
    Creates a new page in Confluence.
    """
    try:
        print(f"DEBUG: create_page_logic called with inputs: space_key='{inputs.space_key}', title='{inputs.title}', parent_page_id={inputs.parent_page_id}, content_length={len(inputs.content)}")

        # The atlassian-python-api's create_page expects parent_id as a string if provided.
        parent_id_str = str(inputs.parent_page_id) if inputs.parent_page_id is not None else None

        created_page_data = client.create_page(
            space=inputs.space_key,
            title=inputs.title,
            body=inputs.content,
            parent_id=parent_id_str,
            type='page',
            representation='storage',
            editor='v2' # Optional: specify editor version, v2 is common for storage format
        )

        if not created_page_data or 'id' not in created_page_data:
            print(f"DEBUG: create_page API call did not return expected data or ID. Response: {created_page_data}")
            raise HTTPException(status_code=500, detail="Confluence API did not return expected data after page creation.")

        print(f"DEBUG: Page created successfully. API response: {created_page_data}")

        page_id = int(created_page_data['id'])
        title = created_page_data.get('title', inputs.title) # API should return title
        version_info = created_page_data.get('version', {})
        version_number = version_info.get('number', 1) # Default to 1 if not present
        status = created_page_data.get('status', 'current')

        # Construct the web URL
        # Example _links structure: {'webui': '/display/SPACEKEY/Page+Title', ...}
        # or sometimes {'tinyui': '/x/shortlink', 'self': '...rest/api/content/id'}
        web_ui_link_path = ""
        if '_links' in created_page_data and 'webui' in created_page_data['_links']:
            web_ui_link_path = created_page_data['_links']['webui']
        
        # Ensure base_url doesn't have a trailing slash if web_ui_link_path starts with one
        if base_url.endswith('/') and web_ui_link_path.startswith('/'):
            effective_base_url = base_url.rstrip('/')
        else:
            effective_base_url = base_url
            
        full_web_url = f"{effective_base_url}{web_ui_link_path}" if web_ui_link_path else f"{effective_base_url}/pages/viewpage.action?pageId={page_id}"


        return CreatePageOutput(
            page_id=page_id,
            title=title,
            space_key=inputs.space_key, # The space key is from input, not typically in create_page response directly
            version=version_number,
            status=status,
            url=full_web_url
        )

    except HTTPException: # Re-raise HTTPException
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"Error during page creation: {str(e)}"
        print(f"An unexpected error occurred in create_page_logic: {error_type} - {error_msg}")
        import traceback
        traceback.print_exc() # For server-side logging of the full error
        # Provide a more user-friendly message if possible, or specific Confluence error details
        # For example, check if 'e' has attributes like 'response' for REST API errors
        if hasattr(e, 'response') and e.response is not None:
            try:
                confluence_error = e.response.json()
                error_detail = confluence_error.get('message', str(e))
                status_code = e.response.status_code
                # Check for common Confluence errors
                if "A page with this title already exists" in error_detail:
                    status_code = 409 # Conflict
                
                print(f"Confluence API Error ({status_code}): {error_detail}")
                raise HTTPException(status_code=status_code, detail=f"Confluence API Error: {error_detail}")
            except ValueError: # If response is not JSON
                pass # Fall through to generic error

        raise HTTPException(status_code=500, detail=f"Server Error ({error_type}): {error_msg}")
