"""
Confluence MCP Server v1.0.0 - Production Ready
Page Actions Module - Complete page management functionality
"""

# Logic for page-related Confluence tools
import logging
from typing import List, Optional, Union, Dict, Any

import httpx # For making async HTTP requests
from fastapi import HTTPException
# ApiError from atlassian.errors is no longer used directly, httpx.HTTPStatusError will be handled

from .schemas import (
    GetPageInput, PageOutput,
    SearchPagesInput, SearchPagesOutput, SearchPagesOutputItem,
    CreatePageInput, CreatePageOutput,
    UpdatePageInput, UpdatePageOutput,
    DeletePageInput, DeletePageOutput
)
# Assuming a utility for base URL or other common Confluence tasks
# from ..utils.confluence_utils import get_page_url_from_api_response

# Placeholder for the utility function if not created yet
# In a real scenario, this would be in confluence_mcp_server/utils/confluence_utils.py
def get_page_url_from_api_response(page_data: Dict[str, Any], base_confluence_url: Optional[str]) -> Optional[str]:
    if not base_confluence_url:
        return None
    api_links = page_data.get('_links', {})
    webui_link = api_links.get('webui') # typically like '/display/SPACEKEY/Page+Title' or '/pages/12345'
    base_link = api_links.get('base') # typically the Confluence base URL

    if webui_link and base_link:
        # Ensure no double slashes if webui_link is absolute or base_link already has context path
        # This logic might need refinement based on actual link formats
        if webui_link.startswith('http'): # if webui_link is already absolute
            return webui_link
        return str(base_link).rstrip('/') + str(webui_link)
    
    # Fallback if _links.webui is not present but page_id is
    page_id = page_data.get('id')
    if page_id:
        return f"{str(base_confluence_url).rstrip('/')}/pages/viewpage.action?pageId={page_id}"
    return None

logger = logging.getLogger(__name__)

async def get_page_logic(client: httpx.AsyncClient, inputs: GetPageInput) -> PageOutput:
    page_data: Optional[Dict[str, Any]] = None
    params = {}
    if inputs.expand:
        params['expand'] = inputs.expand

    try:
        if inputs.page_id:
            logger.info(f"Fetching page by ID: {inputs.page_id} with params: {params}")
            response = await client.get(f"/rest/api/content/{inputs.page_id}", params=params)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            page_data = response.json()
        elif inputs.space_key and inputs.title:
            logger.info(f"Fetching page by title: '{inputs.title}' in space: '{inputs.space_key}' with params: {params}")
            search_params = {
                "spaceKey": inputs.space_key,
                "title": inputs.title,
                "limit": 1 # Fetch by title might return multiple, ensure we only get the exact match or first one
            }
            if inputs.expand:
                search_params['expand'] = inputs.expand
            
            response = await client.get("/rest/api/content", params=search_params)
            response.raise_for_status()
            results = response.json()
            if results and results.get('results'):
                page_data = results['results'][0]
            else:
                # If no results, treat as not found
                raise HTTPException(status_code=404, detail=f"Page not found with title '{inputs.title}' in space '{inputs.space_key}'.")

        if not page_data:
            # This case should ideally be caught by raise_for_status or the logic above
            raise HTTPException(status_code=404, detail="Page not found with provided identifiers.")

        space_info = page_data.get('space', {})
        space_key_from_data = space_info.get('key') if isinstance(space_info, dict) else None
        page_content = None
        if inputs.expand and 'body.view' in inputs.expand:
            body_view = page_data.get('body', {}).get('view', {})
            if isinstance(body_view, dict):
                 page_content = body_view.get('value')
        
        # Construct page URL using the base_url from the httpx client
        page_url = get_page_url_from_api_response(page_data, str(client.base_url))

        return PageOutput(
            page_id=page_data['id'],
            space_key=space_key_from_data,
            title=page_data['title'],
            author_id=page_data.get('history', {}).get('createdBy', {}).get('accountId'),
            created_date=page_data.get('history', {}).get('createdDate'),
            last_modified_date=page_data.get('version', {}).get('when'),
            version=page_data.get('version', {}).get('number'),
            url=page_url,
            content=page_content,
            parent_page_id=page_data.get('ancestors', [{}])[-1].get('id') if page_data.get('ancestors') else None # Updated parent ID logic
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while getting page: {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            # Try to get more specific error from Confluence response
            response_json = e.response.json()
            if isinstance(response_json, dict) and 'message' in response_json:
                error_detail = f"Confluence API Error: {response_json['message']}"
            elif isinstance(response_json, dict) and 'errorMessages' in response_json and response_json['errorMessages']:
                 error_detail = f"Confluence API Error: {', '.join(response_json['errorMessages'])}"
        except Exception:
            pass # Keep generic error_detail if parsing fails
        
        if e.response.status_code == 404:
            error_detail = "Page not found."
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except httpx.RequestError as e:
        logger.error(f"Request error while getting page: {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}") # Service unavailable type error
    except HTTPException:
        # Re-raise HTTPException as-is to avoid double wrapping
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_page_logic: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

async def search_pages_logic(client: httpx.AsyncClient, inputs: SearchPagesInput) -> SearchPagesOutput:
    cql_parts = []
    if inputs.cql:
        cql_parts.append(f"({inputs.cql})")
    else:
        # Basic query building if direct CQL is not provided
        escaped_query = inputs.query.replace('"', '\\"') # Escape double quotes for CQL
        cql_parts.append(f'text ~ "{escaped_query}" OR title ~ "{escaped_query}"')

    if inputs.space_key:
        cql_parts.append(f"space = \"{inputs.space_key}\"")
    
    final_cql = " AND ".join(cql_parts)
    
    api_params = {
        "cql": final_cql,
        "limit": inputs.limit,
        "start": inputs.start
    }
    if inputs.expand:
        api_params["expand"] = inputs.expand
    if inputs.excerpt:
        api_params["excerpt"] = inputs.excerpt

    logger.info(f"Executing Confluence search with params: {api_params}")

    try:
        response = await client.get("/rest/api/content/search", params=api_params)
        response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
        response_json = response.json()

        results_output_items = []
        expand_list_for_content_preview = inputs.expand.split(',') if inputs.expand else []

        for item_data in response_json.get('results', []):
            page_url = get_page_url_from_api_response(item_data, str(client.base_url))
            content_prev = None
            # Check if 'body.view' was requested and is present for content preview
            if 'body.view' in expand_list_for_content_preview:
                body_data = item_data.get('body', {})
                view_data = body_data.get('view', {})
                if isinstance(view_data, dict):
                    content_prev = view_data.get('value')
            
            space_key_val = item_data.get('space', {}).get('key') if isinstance(item_data.get('space'), dict) else None

            results_output_items.append(SearchPagesOutputItem(
                page_id=item_data['id'],
                title=item_data['title'],
                space_key=space_key_val,
                last_modified_date=item_data.get('version', {}).get('when'), # version.when is last modified
                url=page_url,
                excerpt_highlight=item_data.get('excerpt'), # Excerpt from search result directly
                content_preview=content_prev
            ))
        
        current_start = response_json.get('start', 0)
        current_size = response_json.get('size', 0) # Number of items in this response
        total_available = response_json.get('totalSize', 0)

        next_offset = None
        if (current_start + current_size) < total_available:
            next_offset = current_start + current_size

        return SearchPagesOutput(
            results=results_output_items,
            total_available=total_available,
            next_start_offset=next_offset
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during Confluence search: {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            response_content = e.response.json()
            if isinstance(response_content, dict):
                if 'message' in response_content:
                    error_detail = f"Confluence API Error: {response_content['message']}"
                elif 'errorMessages' in response_content and response_content['errorMessages']:
                    error_detail = f"Confluence API Error: {', '.join(response_content['errorMessages'])}"
        except Exception:
            pass # Keep generic error_detail

        if e.response.status_code == 400 and ("CQL" in error_detail or "parse" in error_detail.lower() or "cql" in error_detail.lower()):
             error_detail = f"Invalid CQL syntax or query parameter. Details: {error_detail}"
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except httpx.RequestError as e:
        logger.error(f"Request error during Confluence search: {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error in search_pages_logic: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

async def create_page_logic(client: httpx.AsyncClient, inputs: CreatePageInput) -> CreatePageOutput:
    logger.info(f"Attempting to create page titled '{inputs.title}' in space '{inputs.space_key}'")

    payload = {
        "type": "page",
        "title": inputs.title,
        "space": {"key": inputs.space_key},
        "body": {
            "storage": {
                "value": inputs.content,
                "representation": "storage"
            }
        }
    }
    if inputs.parent_page_id:
        payload["ancestors"] = [{"id": inputs.parent_page_id}]

    try:
        response = await client.post("/rest/api/content", json=payload)
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        created_page_data = response.json()

        if not created_page_data:
            # This case should ideally be caught by raise_for_status if API returns non-2xx on failure
            logger.error(f"Failed to create page '{inputs.title}', no data returned from Confluence despite a success status: {response.status_code}")
            raise HTTPException(status_code=500, detail="Failed to create page, no data returned from Confluence but status was OK.")

        page_url = get_page_url_from_api_response(created_page_data, str(client.base_url))
        
        # The actual space key should be in the response if successful
        space_info = created_page_data.get('space', {})
        space_key_from_data = space_info.get('key') if isinstance(space_info, dict) else inputs.space_key

        return CreatePageOutput(
            page_id=created_page_data['id'],
            title=created_page_data['title'],
            space_key=space_key_from_data, # Prefer space key from response
            version=created_page_data.get('version', {}).get('number', 1),
            url=page_url,
            status=created_page_data.get('status', 'current')
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during page creation: {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            response_content = e.response.json()
            if isinstance(response_content, dict):
                if 'message' in response_content:
                    error_detail = f"Confluence API Error: {response_content['message']}"
                elif 'data' in response_content and 'errors' in response_content['data'] and response_content['data']['errors']:
                    # Handle cases like title already exists in space
                    first_error = response_content['data']['errors'][0]
                    error_detail = f"Confluence API Error: {first_error.get('message', {}).get('translation', 'Unknown error')}"
                elif 'errorMessages' in response_content and response_content['errorMessages']:
                     error_detail = f"Confluence API Error: {', '.join(response_content['errorMessages'])}"
        except Exception:
            pass # Keep generic error_detail if parsing fails

        # Customize error for specific known issues if possible
        if e.response.status_code == 400 and "A page with this title already exists" in error_detail:
            error_detail = f"A page titled '{inputs.title}' already exists in space '{inputs.space_key}'."
        
        raise HTTPException(status_code=e.response.status_code, detail=f"Error creating page: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Request error during page creation: {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error in create_page_logic: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during page creation: {str(e)}")

async def update_page_logic(client: httpx.AsyncClient, inputs: UpdatePageInput) -> UpdatePageOutput:
    logger.info(f"Attempting to update page ID '{inputs.page_id}' to version '{inputs.new_version_number}'")
    
    current_page_data = None
    try:
        # Step 1: Fetch current page data to get current version and other details
        get_params = {"expand": "body.storage,version,space"}
        current_page_response = await client.get(f"/rest/api/content/{inputs.page_id}", params=get_params)
        if current_page_response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Page with ID '{inputs.page_id}' not found.")
        current_page_response.raise_for_status() # For other non-404 errors
        current_page_data = current_page_response.json()

        # Step 2: Validate version
        current_version_number = current_page_data.get('version', {}).get('number')
        if inputs.new_version_number != current_version_number + 1:
            logger.error(f"Version conflict for page {inputs.page_id}. Current: {current_version_number}, Input new: {inputs.new_version_number}, Expected next: {current_version_number + 1}")
            raise HTTPException(
                status_code=409, 
                detail=f"Version conflict. Current page version is {current_version_number}, supplied next version is {inputs.new_version_number}. Expected next version to be {current_version_number + 1}."
            )

        # Step 3: Construct the update payload
        payload = {
            "version": {"number": inputs.new_version_number},
            "type": "page",
            "title": inputs.title if inputs.title is not None else current_page_data['title'] # Title is mandatory
        }

        if inputs.content is not None:
            payload["body"] = {"storage": {"value": inputs.content, "representation": "storage"}}
        
        if inputs.parent_page_id is not None:
            if inputs.parent_page_id == "": # Empty string indicates making it a top-level page
                payload["ancestors"] = []
            else:
                payload["ancestors"] = [{"id": inputs.parent_page_id}]
        
        # Step 4: Make the PUT request to update the page
        logger.debug(f"Updating page {inputs.page_id} with payload: {payload}")
        update_response = await client.put(f"/rest/api/content/{inputs.page_id}", json=payload)
        update_response.raise_for_status()
        updated_page_data = update_response.json()

        # Step 5: Map to output schema
        page_url = get_page_url_from_api_response(updated_page_data, str(client.base_url))
        
        # Space key from the response, or fallback to current if somehow missing (should not happen)
        space_key_from_data = updated_page_data.get('space', {}).get('key') \
                              if isinstance(updated_page_data.get('space'), dict) \
                              else current_page_data.get('space',{}).get('key')

        return UpdatePageOutput(
            page_id=updated_page_data['id'],
            title=updated_page_data['title'],
            space_key=space_key_from_data,
            version=updated_page_data.get('version', {}).get('number'),
            url=page_url,
            last_modified_date=updated_page_data.get('version', {}).get('when')
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during page update for {inputs.page_id}: {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            response_content = e.response.json()
            if isinstance(response_content, dict):
                # Attempt to extract a more specific error message from various possible locations
                msg1 = response_content.get('message', '')
                
                msg2 = ''
                data_field = response_content.get('data')
                if isinstance(data_field, dict):
                    errors_field = data_field.get('errors')
                    if isinstance(errors_field, list) and errors_field:
                        first_error = errors_field[0]
                        if isinstance(first_error, dict):
                            message_field = first_error.get('message')
                            if isinstance(message_field, dict):
                                msg2 = message_field.get('translation', '')
                
                msg3 = ''
                error_messages_field = response_content.get('errorMessages')
                if isinstance(error_messages_field, list) and error_messages_field:
                    msg3 = ', '.join(str(em) for em in error_messages_field if em)

                error_message_from_api = msg1 or msg2 or msg3
                if error_message_from_api:
                    error_detail = f"Confluence API Error: {error_message_from_api}"
        except Exception:
            pass # Keep generic error_detail

        if e.response.status_code == 404:
            error_detail = f"Page with ID '{inputs.page_id}' not found for update."
        elif e.response.status_code == 409: # Version conflict or other conflicts
             # The previous specific version conflict message is good, but API might return other 409s
            if "Version conflict" not in error_detail and current_page_data: # Check if we already raised a more specific one
                 error_detail = f"Conflict updating page '{inputs.page_id}'. This could be a version mismatch or another issue. Details: {error_detail}"

        raise HTTPException(status_code=e.response.status_code, detail=f"Error updating page: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Request error during page update: {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except HTTPException:
        # Re-raise HTTPException as-is to avoid double wrapping
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in update_page_logic for page {inputs.page_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during page update: {str(e)}")

async def delete_page_logic(client: httpx.AsyncClient, inputs: DeletePageInput) -> DeletePageOutput:
    """
    Moves a Confluence page to the trash.
    Note: This typically moves the page to trash, not permanent deletion directly.
    Permanent deletion usually requires further steps (e.g., via UI or specific API if available).
    """
    page_id = inputs.page_id
    logger.info(f"Attempting to delete page with ID '{page_id}'.")
    
    delete_url = f"/wiki/rest/api/content/{page_id}"
    
    try:
        response = await client.delete(delete_url)
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        
        logger.info(f"Successfully deleted page with ID '{page_id}'. Response: {response.status_code}")
        return DeletePageOutput(
            page_id=page_id,
            message=f"Page with ID '{page_id}' has been successfully moved to trash.",
            status="success"
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during page deletion for ID '{page_id}': {e.response.status_code} - {e.response.text}", exc_info=True)
        error_detail = f"API responded with status {e.response.status_code}. "
        try:
            response_content = e.response.json()
            # Try to extract a more specific error message from Confluence
            if isinstance(response_content, dict):
                msg1 = response_content.get('message', '') # Common for some direct errors
                
                msg2 = ''
                data_field = response_content.get('data')
                if isinstance(data_field, dict):
                    errors_field = data_field.get('errors')
                    if isinstance(errors_field, list) and errors_field:
                        first_error = errors_field[0]
                        if isinstance(first_error, dict):
                            message_field = first_error.get('message')
                            if isinstance(message_field, dict):
                                msg2 = message_field.get('translation', '')
                
                msg3 = ''
                error_messages_field = response_content.get('errorMessages')
                if isinstance(error_messages_field, list) and error_messages_field:
                    msg3 = ', '.join(str(em) for em in error_messages_field if em)

                error_message_from_api = msg1 or msg2 or msg3
                if error_message_from_api:
                    error_detail = f"Confluence API Error: {error_message_from_api}"
        except Exception:
            # If response is not JSON or parsing fails, keep the generic error_detail
            pass 

        if e.response.status_code == 404:
            error_detail = f"Page with ID '{page_id}' not found or already deleted."
        elif e.response.status_code == 403:
            error_detail = f"Permission denied to delete page ID '{page_id}'. Details: {error_detail}"
        
        raise HTTPException(status_code=e.response.status_code, detail=f"Error deleting page: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Request error during page deletion for ID '{page_id}': {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error in delete_page_logic for ID '{page_id}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during page deletion: {str(e)}")