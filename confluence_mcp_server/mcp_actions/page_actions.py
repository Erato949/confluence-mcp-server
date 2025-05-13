# confluence_mcp_server/mcp_actions/page_actions.py

from atlassian import Confluence
from atlassian.errors import ApiError 
from fastapi import HTTPException
from pydantic import ValidationError 
from typing import List, Optional
from urllib.parse import urljoin 
import asyncio
import logging

logger = logging.getLogger(__name__)

from .schemas import (
    GetPageInput, GetPageOutput,
    SearchPagesInput, SearchPagesOutput, SearchedPageSchema,
    CreatePageInput, CreatePageOutput,
    UpdatePageInput, UpdatePageOutput,
    DeletePageInput, DeletePageOutput
)

# --- Helper Functions ---

def get_confluence_page_url(webui_link: Optional[str], instance_base_url: str) -> str:
    """Constructs the full web URL for a Confluence page using urljoin."""
    if not webui_link:
        logger.debug("webui_link not provided, returning URL_NOT_AVAILABLE")
        return "URL_NOT_AVAILABLE"

    # Ensure base URL ends with a slash for urljoin to work correctly with relative paths
    if not instance_base_url.endswith('/'):
        instance_base_url += '/'

    # webui_link might be like '/wiki/display/...' or just '/display/...' or even relative
    # urljoin handles combining these intelligently.
    full_url = urljoin(instance_base_url, webui_link)

    logger.debug(f"Constructed URL: base='{instance_base_url}', webui='{webui_link}', result='{full_url}'")
    return full_url

# --- Get Page ---
async def get_page_logic(
    client: Confluence,
    inputs: GetPageInput
) -> GetPageOutput | None:
    """
    Logic for the Get_Page tool.
    Fetches a specific page from Confluence by its ID, or by its space key and title.
    """
    # Forcing a re-evaluation of this file's bytecode
    page_data = None
    error_detail_prefix = ""
    try:
        logger.debug(f"get_page_logic called with inputs: page_id={inputs.page_id}, space_key={inputs.space_key}, title={inputs.title}, expand={inputs.expand}") # Debug line
        if inputs.page_id is not None:
            logger.debug(f"Calling Confluence API get_page_by_id with page_id: {inputs.page_id}, expand: {inputs.expand}")
            page_data = client.get_page_by_id(page_id=inputs.page_id, expand=inputs.expand)
            error_detail_prefix = f"Page with ID {inputs.page_id}"
        elif inputs.space_key and inputs.title:
            logger.debug(f"Calling Confluence API get_page_by_title with space_key: {inputs.space_key}, title: {inputs.title}, expand: {inputs.expand}")
            # Note: get_page_by_title does not directly support 'expand' in atlassian-python-api as of 4.0.3
            # We would typically fetch by title, get the ID, then fetch by ID with expand if needed.
            # For simplicity here, we'll assume get_page_by_title returns enough, or we handle expansion post-fetch if necessary.
            # However, the library's get_page_by_title *does* pass through expand kwargs to the underlying get_page_by_id it uses after finding the page list by title.
            page_data = client.get_page_by_title(space=inputs.space_key, title=inputs.title, expand=inputs.expand)
            error_detail_prefix = f"Page with title '{inputs.title}' in space '{inputs.space_key}'"
        # The GetPageInput model validator should prevent a state where neither condition is met.

        if not page_data:
            logger.debug(f"page_data is None or empty after API call.") # Debug line
            raise HTTPException(status_code=404, detail=f"{error_detail_prefix} not found.")

        logger.debug(f"page_data received from API mock: {page_data}") # Debug line

        # Extract space key - it might be directly available or nested if 'space' is expanded
        space_key_val = "UNKNOWN"
        if 'space' in page_data and isinstance(page_data['space'], dict) and 'key' in page_data['space']:
            space_key_val = page_data['space']['key']
        elif 'spaceKey' in page_data: # Fallback if spaceKey is a top-level attribute (less common for get_page_by_id)
             space_key_val = page_data['spaceKey']
        
        # Extract content if available (depends on expand='body.storage')
        content_val = None
        logger.debug(f"DEBUG: Attempting to extract content. page_data.get('body'): {page_data.get('body')}") # Debug line
        if 'body' in page_data and isinstance(page_data['body'], dict) and 'storage' in page_data['body'] and isinstance(page_data['body']['storage'], dict) and 'value' in page_data['body']['storage']:
            content_val = page_data['body']['storage']['value']
        logger.debug(f"DEBUG: content_val after extraction: {content_val}") # Debug line
        
        # Extract version if available (depends on expand='version')
        version_val = None
        logger.debug(f"DEBUG: Attempting to extract version. page_data.get('version'): {page_data.get('version')}") # Debug line
        if 'version' in page_data and isinstance(page_data['version'], dict) and 'number' in page_data['version']:
            version_val = page_data['version']['number']
        logger.debug(f"DEBUG: version_val after extraction: {version_val}") # Debug line

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

        logger.debug(f"PRE-RETURN: page_id raw from page_data: {page_data.get('id')}, type: {type(page_data.get('id'))}") # Debug line
        logger.debug(f"PRE-RETURN: title: {page_data.get('title')}, space_key: {space_key_val}, status: {page_data.get('status', 'unknown')}, content: {content_val}, version: {version_val}, web_url: {web_url_val}") # Debug line
        
        output_object = GetPageOutput(
            page_id=page_data['id'],
            title=page_data['title'],
            space_key=space_key_val, 
            status=page_data.get('status', 'unknown'),
            content=content_val,
            version=version_val,
            web_url=web_url_val
        )
        logger.debug(f"POST-INSTANTIATION of GetPageOutput: {output_object.model_dump_json(indent=2)}") # Debug line
        return output_object

    except HTTPException: # Re-raise HTTPException to be caught by the endpoint handler
        raise
    except Exception as e:
        logger.error(f"!!!!!!!!!! FATAL ERROR IN get_page_logic !!!!!!!!!=") # Enhanced Debug line
        logger.error(f"!!!!!!!!!! TYPE: {type(e).__name__} !!!!!!!!!=") # Enhanced Debug line
        logger.error(f"!!!!!!!!!! ARGS: {e.args} !!!!!!!!!=") # Enhanced Debug line
        import traceback
        logger.error(traceback.format_exc()) # Print full traceback
        logger.error(f"Error encountered in get_page_logic: {type(e).__name__} - {e}")
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


async def search_pages_logic(
    client: Confluence,
    inputs: SearchPagesInput
) -> SearchPagesOutput:
    """
    Logic to search for Confluence pages using CQL.
    """
    try:
        logger.debug(f"DEBUG: search_pages_logic called with CQL: {inputs.cql}, limit: {inputs.limit}, start: {inputs.start}, expand: {inputs.expand}, excerpt: {inputs.excerpt}")

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
            logger.debug(f"DEBUG: CQL search for '{inputs.cql}' returned no results or unexpected response format.")
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

        logger.debug(f"DEBUG: api_response from Confluence: {api_response}")

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
                logger.debug(f"DEBUG: Skipping result due to missing page ID. Raw data: {page_data}")
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
        logger.error(f"An unexpected error occurred in search_pages_logic: {error_type} - {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{error_type}: {error_msg}")

async def create_page_logic(
    client: Confluence,
    inputs: CreatePageInput
) -> CreatePageOutput | None:
    """
    Logic for the create_page tool.
    Creates a new page in Confluence.
    """
    try:
        logger.debug(f"DEBUG: create_page_logic called with inputs: space_key={inputs.space_key}, title={inputs.title}, parent_page_id={inputs.parent_page_id}") # Debug start

        # Prepare parameters for the API call
        params = {
            "space": inputs.space_key,
            "title": inputs.title,
            "body": inputs.content, # Map schema 'content' to API 'body'
            "representation": "storage", # Specify content format
            "type": "page"
        }
        if inputs.parent_page_id is not None:
            params["parent_id"] = str(inputs.parent_page_id) # API expects string ID for parent

        logger.debug(f"DEBUG: Calling client.create_page with params: {params}")
        created_page_response = client.create_page(**params)
        logger.debug(f"DEBUG: client.create_page response: {created_page_response}")

        if not created_page_response:
             logger.error(f"ERROR: client.create_page returned unexpected response: {created_page_response}")
             raise HTTPException(status_code=500, detail="Failed to create page, unexpected empty response from Confluence API.")

        # Construct the output using the response data
        page_id = int(created_page_response.get("id", 0)) # API returns string ID
        if not page_id:
             logger.error(f"ERROR: 'id' not found or invalid in create_page response: {created_page_response}")
             raise HTTPException(status_code=500, detail="Failed to create page, missing 'id' in Confluence API response.")

        webui_link = created_page_response.get('_links', {}).get('webui')
        page_url = get_confluence_page_url(webui_link, client.url) # Use helper function

        # Ensure version is extracted correctly
        version_info = created_page_response.get('version', {})
        version_number = version_info.get('number', 1) # Default to 1 if not present

        response_data = {
            "page_id": page_id,
            "title": created_page_response.get("title", inputs.title), # Use input title as fallback
            "space_key": inputs.space_key, # Space key comes from input
            "version": version_number,
            "status": created_page_response.get("status", "current"), # Default if not present
            "url": page_url
        }

        logger.debug(f"DEBUG: Returning CreatePageOutput: {response_data}")
        return CreatePageOutput(**response_data)

    except ApiError as e:
        # Log the specific API error
        api_status_code = 500 # Default

        # Try getting status from response first
        if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'status_code') and e.response.status_code is not None:
            api_status_code = e.response.status_code
        # Fallback to checking status directly on the error object (for test mocks)
        elif hasattr(e, 'status_code') and e.status_code is not None:
            api_status_code = e.status_code

        api_reason = str(e) # Keep using str(e) for the main reason
        logger.error(f"ERROR: API error during page creation: {api_status_code} - {api_reason}")

        # Determine HTTP status code for the response based on extracted api_status_code
        http_status_code = 500 # Default HTTPException status to 500 for unexpected API errors
        if isinstance(api_status_code, int) and 400 <= api_status_code < 500:
             # If it's a 4xx error from the API, use that status for the HTTPException
            http_status_code = api_status_code
        # Add specific mappings if needed, e.g., map 409 to 409
        elif api_status_code == 409:
             http_status_code = 409
        # Add other mappings as necessary...
        # Note: The previous logic defaulted to 400 here, but 500 might be safer default for uncategorized API errors

        # Construct the detailed message for the HTTPException (using original logic)
        status_code_val = getattr(e, 'status_code', api_status_code) # Use extracted code if direct attribute missing
        reason_val = getattr(e, 'reason', 'N/A')
        url_val = getattr(e, 'url', 'N/A')
        text_val = getattr(e, 'text', 'N/A')

        if hasattr(e, 'reason') and e.reason:
            simple_reason = e.reason
        else:
            simple_reason = str(e).split('\n')[0]

        detail_str = f"Error creating page in Confluence: Details: Received {status_code_val} {simple_reason} for url: {url_val}\nResponse: {text_val}"

        # Re-raise as HTTPException for FastAPI to handle
        raise HTTPException(
            status_code=http_status_code, # Use the determined http_status_code
            detail=detail_str
        )
    except Exception as e:
        # Catch any other unexpected errors
        detailed_error_msg = f"Unexpected error during page creation: {type(e).__name__} - {str(e)}"
        logger.error(f"ERROR: {detailed_error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating page in Confluence: Details: {str(e)}"
        ) from e

async def update_page_logic(
    client: Confluence,
    inputs: UpdatePageInput
) -> UpdatePageOutput:
    """
    Logic to update an existing page in Confluence.
    Requires the current version number for optimistic concurrency control.
    At least one of title, content, or parent_page_id must be provided.
    """
    logger.debug(f"DEBUG: update_page_logic called with page_id: {inputs.page_id}, title: {inputs.title is not None}, has_content: {inputs.content is not None}, parent_id: {inputs.parent_page_id}, version: {inputs.current_version_number}")

    try:
        # Initialize with input values or None
        current_title = inputs.title
        current_body = inputs.content
        fetched_space_key = None # Store space key if we fetch the page

        # Fetch current page details if title or content is missing for the update.
        # Always expand 'space' to potentially get the space_key needed later.
        expand_needed = "body.storage,version,space"

        if inputs.title is None or inputs.content is None:
            logger.debug(f"DEBUG: Fetching current page {inputs.page_id} with expand='{expand_needed}' for update.")
            try:
                # Wrap synchronous call
                current_page_data = await asyncio.to_thread(
                    client.get_page_by_id, page_id=inputs.page_id, expand=expand_needed
                )
                logger.debug(f"DEBUG: Fetched current page data: {current_page_data}")
                if inputs.title is None:
                    current_title = current_page_data.get('title')
                if inputs.content is None:
                    current_body = current_page_data.get('body', {}).get('storage', {}).get('value', '')
                    if not current_body:
                         logger.warning(f"Could not fetch existing body for page {inputs.page_id}, or body was empty. Proceeding with empty/provided content.")

                # Store fetched space key if available
                if 'space' in current_page_data and isinstance(current_page_data['space'], dict):
                    fetched_space_key = current_page_data['space'].get('key')
                    logger.debug(f"DEBUG: Fetched space_key='{fetched_space_key}' during initial get_page_by_id.")

            except ApiError as e:
                 # Correctly extract status code from e.response
                 api_status_code = 500 # Default
                 if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'status_code'):
                     api_status_code = e.response.status_code

                 api_reason = str(e)
                 logger.error(f"ERROR: API error fetching page {inputs.page_id} for update: {api_status_code} - {api_reason}")
                 if api_status_code == 404:
                      raise HTTPException(status_code=404, detail=f"Page with ID {inputs.page_id} not found.") from e
                 else:
                      # Use api_reason for detail
                      raise HTTPException(status_code=api_status_code, detail=f"Failed to fetch page {inputs.page_id} for update: {api_reason}") from e
            except Exception as e:
                logger.error(f"ERROR: Unexpected error fetching page {inputs.page_id} for update: {e}")
                raise HTTPException(status_code=500, detail=f"Unexpected error fetching page {inputs.page_id} for update: {str(e)}") from e

        # Ensure we have a title before proceeding (check after potential fetch)
        if current_title is None:
             # This should only happen if fetch failed AND title wasn't provided.
             raise HTTPException(status_code=400, detail="Title is required for update and could not be fetched or wasn't provided.")
        # Body can be None or empty string if not provided and fetch failed/returned no body.
        # client.update_page might require it, ensure representation is set if body is string.

        # Prepare parameters for the API call
        next_version_number = inputs.current_version_number + 1
        update_params = {
            "page_id": inputs.page_id,
            "title": current_title, # Use fetched or provided title
            "body": current_body,   # Use fetched or provided content (can be None or str)
            "version": next_version_number,
            # "representation": "storage" # Add this ONLY if body is a string
        }

        # Conditionally add representation if body is a string (even empty)
        if isinstance(update_params.get("body"), str):
            update_params["representation"] = "storage"
        else:
            # If body is None (wasn't provided, couldn't be fetched), remove it from params
            # as sending 'body: null' might be invalid depending on the API client library.
            update_params.pop("body", None)
            logger.debug(f"DEBUG: 'body' is None, removing from update_params.")

        # OMIT parent_id from update_params - changing parent requires move_page.
        logger.debug(f"DEBUG: Calling client.update_page via asyncio.to_thread with params: page_id={update_params.get('page_id')}, title='{update_params.get('title')}', body_present={update_params.get('body') is not None}, version={update_params.get('version')}, representation={update_params.get('representation')}")
        # Wrap synchronous call
        updated_page_response = await asyncio.to_thread(
            client.update_page, **update_params
        )
        logger.debug(f"DEBUG: client.update_page response: {updated_page_response}")

        # Construct the output
        try:
            # Ensure base URL ends with '/' and webui path doesn't start with '/'
            base_url = str(client.url).rstrip('/') + '/' # Ensure base ends with /
            webui_path = updated_page_response.get('_links', {}).get('webui', '').lstrip('/') # Ensure path doesn't start with /
            full_url = urljoin(base_url, webui_path)
            logger.debug(f"Constructed URL: base='{base_url}', webui='{webui_path}', result='{full_url}'") # Log adjusted parts

            # Get space_key (prefer from update_result, fallback to initial fetch if needed)
            space_key = updated_page_response.get('space', {}).get('key')
            if not space_key:
                space_key = fetched_space_key
                logger.debug(f"DEBUG: Using space_key='{space_key}' fetched earlier.")

            if not space_key:
                logger.error(f"ERROR: Could not determine space_key for updated page {inputs.page_id}. Response: {updated_page_response}")
                raise HTTPException(status_code=500, detail=f"Internal error: Could not determine space key for page {inputs.page_id} after update.")

            response_data = {
                "page_id": str(updated_page_response.get("id", inputs.page_id)), # Schema wants str
                "title": updated_page_response.get("title", current_title), # Use input title as fallback
                "space_key": space_key,
                "version": updated_page_response.get("version", {}).get("number", next_version_number),
                "status": updated_page_response.get("status", "current"),
                "url": full_url
            }

            # Validate final output structure before returning
            try:
                 output = UpdatePageOutput(**response_data)
                 logger.debug(f"DEBUG: Successfully created UpdatePageOutput: {output.model_dump()}")
                 return output
            except ValidationError as val_err:
                 error_details = val_err.errors()
                 logger.error(f"ERROR: ValidationError creating UpdatePageOutput. Data: {response_data}. Details: {error_details}")
                 # Provide more detail in the HTTPException if possible
                 detail_msg = f"Internal Server Error: Failed to structure update page response. First error: {error_details[0]['msg']} at loc {error_details[0]['loc']}"
                 raise HTTPException(status_code=500, detail=detail_msg) from val_err

        except ApiError as e:
            # Correctly extract status code from e.response
            api_status_code = 500 # Default
            if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'status_code'):
                api_status_code = e.response.status_code

            api_reason = str(e)
            logger.error(f"API error during page update for page_id {inputs.page_id}: Status {api_status_code}, Reason: {api_reason}")
            raise HTTPException(status_code=api_status_code, detail=f"Error interacting with Confluence API: {api_reason}")
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error during page update for page_id {inputs.page_id}: {type(e).__name__} - {str(e)}", exc_info=True)
            # Match the error message format expected in the passed test test_update_page_unexpected_error
            raise HTTPException(status_code=500, detail=f"Unexpected error updating page. Details: {str(e)}")

    except ApiError as e:
        # Correctly extract status code from e.response
        api_status_code = 500 # Default
        if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'status_code'):
            api_status_code = e.response.status_code

        api_reason = str(e)
        # Determine the appropriate status code for the HTTPException
        # Use the extracted API status code if it's a client error (4xx) or specific server errors we handle (like 409 conflict)
        # Otherwise, default to 503 Service Unavailable for general API issues
        http_status_code = 503 # Default to Service Unavailable for API errors
        if 400 <= api_status_code < 500:
            http_status_code = api_status_code
        elif api_status_code == 503:
             http_status_code = 503 # Explicitly keep 503 if API returned it

        logger.error(f"ERROR: Confluence API error during page update: {api_status_code} - {api_reason}. Raising HTTPException with status {http_status_code}")
        # Construct detail message
        detail_message = f"Error updating page {inputs.page_id} in Confluence: Details: {api_reason}"
        # Optionally add more context if needed, e.g. API status code
        # detail_message += f" (API Status: {api_status_code})"

        raise HTTPException(status_code=http_status_code, detail=detail_message) from e

    except HTTPException as http_exc: # Re-raise HTTPExceptions raised internally
         logger.debug(f"DEBUG: Re-raising HTTPException from update_page_logic: {http_exc.status_code} - {http_exc.detail}")
         raise http_exc

    except Exception as e:
        # Catch any other unexpected errors
        detailed_error_msg = f"Unexpected error during page update for page_id {inputs.page_id}: {type(e).__name__} - {str(e)}"
        logger.error(f"ERROR: {detailed_error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: Unexpected error updating page. Details: {str(e)}"
        ) from e

# --- Delete Page ---
async def delete_page_logic(
    client: Confluence,
    inputs: DeletePageInput
) -> DeletePageOutput:
    """
    Logic for the delete_page tool.
    Deletes a specific page from Confluence by its ID.
    """
    page_id = inputs.page_id
    logger.debug(f"Attempting to delete page with ID: {page_id}")

    try:
        # The atlassian-python-api's delete_page method typically returns True on success
        # or raises ApiError on failure.
        success = await client.delete_page(page_id=page_id, status=None, recursive=False) # Assuming we don't need recursive delete for now

        if success: # Explicitly check return value if needed, though ApiError is the main indicator
             logger.info(f"Successfully deleted page with ID: {page_id}")
             return DeletePageOutput(message=f"Successfully deleted page with ID {page_id}.")
        else:
             # This path might be unlikely if ApiError is always raised on failure
             logger.warning(f"delete_page call for ID {page_id} returned False/None but did not raise ApiError.")
             raise HTTPException(status_code=500, detail=f"Failed to delete page ID {page_id}. API did not confirm success.")

    except ApiError as e:
        status_code = getattr(e, 'response', None) and getattr(e.response, 'status_code', 500)
        error_message = str(e)
        logger.error(f"Confluence API error deleting page ID {page_id}: Status {status_code} - {error_message}")
        if status_code == 404:
            raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found.")
        elif status_code == 403:
             raise HTTPException(status_code=403, detail=f"Permission denied when attempting to delete page ID {page_id}.")
        else:
            raise HTTPException(status_code=status_code, detail=f"Confluence API error deleting page ID {page_id}: {error_message}")
            
    except HTTPException: # Re-raise HTTPException if it was raised above
        raise
    except Exception as e:
        logger.exception(f"Unexpected error deleting page ID {page_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while deleting page ID {page_id}: {str(e)}")
