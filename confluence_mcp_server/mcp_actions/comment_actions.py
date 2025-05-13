from typing import List, Optional

from atlassian import Confluence
from atlassian.errors import ApiError
from fastapi import HTTPException

from .schemas import GetCommentsInput, CommentOutputItem, GetCommentsOutput

async def get_comments_logic(
    client: Confluence, 
    inputs: GetCommentsInput
) -> GetCommentsOutput:
    """
    Logic to retrieve comments for a Confluence page.
    """
    try:
        # Placeholder: Actual API call and response processing will be implemented next.
        # For now, simulating a call and returning a basic structure.
        
        # The atlassian-python-api's get_page_comments method returns a dictionary.
        # Example structure (simplified):
        # {
        #     'results': [
        #         {'id': '123', 'title': None, 'status': None, 'extensions': {'author': {...}, 'resolutionDate': '...'}, 'body': {'storage': {'value': '...'}} }, ...
        #     ],
        #     'start': 0,
        #     'limit': 25,
        #     'size': actual_number_returned,
        #     '_links': {'next': '/rest/api/content/PAGE_ID/child/comment?limit=25&start=25'}
        # }
        # Note: The actual comment fields will differ. We need to map these to CommentOutputItem.

        api_response = client.get_page_comments(
            page_id=inputs.page_id,
            limit=inputs.limit if inputs.limit is not None else 25, # API might have its own defaults
            start=inputs.start if inputs.start is not None else 0, # API might have its own defaults
            expand=inputs.expand # Pass expand string directly
        )

        comments_data = api_response.get('results', [])
        processed_comments: List[CommentOutputItem] = []

        for item_data in comments_data:
            # Ensure id is string as per our schema and Confluence API typical behavior
            comment_id_str = str(item_data.get('id')) 

            # Extract author details (these might be nested or require specific expand)
            author_details = item_data.get('extensions', {}).get('author', {})
            author_id = author_details.get('accountId') # Example path, adjust based on actual API response
            author_display_name = author_details.get('displayName') # Example path

            # Extract body formats (these might be nested or require specific expand)
            body_info = item_data.get('body', {})
            body_storage = body_info.get('storage', {}).get('value') if body_info.get('storage') else None
            body_view = body_info.get('view', {}).get('value') if body_info.get('view') else None
            
            # Extract parent comment ID if it's a reply
            # This might be in _links or a specific field like 'parent_id' in extensions, depending on API version and expand
            # For simplicity, assuming a direct field or that it's handled by 'expand' if needed
            parent_id = item_data.get('extensions', {}).get('parentComment', {}).get('id')
            parent_comment_id_str = str(parent_id) if parent_id else None

            processed_comments.append(
                CommentOutputItem(
                    comment_id=comment_id_str,
                    author_id=author_id,
                    author_display_name=author_display_name,
                    created_date=item_data.get('extensions', {}).get('when'), # Example path for creation date
                    last_updated_date=item_data.get('extensions', {}).get('lastModifiedDate'), # Example path
                    body_storage=body_storage,
                    body_view=body_view,
                    parent_comment_id=parent_comment_id_str
                    # url: This might need to be constructed or found in _links
                )
            )
        
        retrieved_count = api_response.get('size', len(processed_comments))
        total_available_from_api = api_response.get('totalSize') # This field might exist in some API versions for total comments on page
        
        next_start = None
        if '_links' in api_response and 'next' in api_response['_links']:
            # Parse 'next' link to get the next start offset if available
            # Example: /rest/api/content/123/child/comment?limit=25&start=25
            # This parsing can be complex; for now, let's assume we can extract it or it matches limit+start
            if retrieved_count == (inputs.limit if inputs.limit is not None else 25):
                 next_start = (inputs.start if inputs.start is not None else 0) + retrieved_count

        return GetCommentsOutput(
            comments=processed_comments,
            retrieved_count=retrieved_count,
            total_available=total_available_from_api, # Or None if not provided by API
            next_start_offset=next_start,
            limit_used=inputs.limit if inputs.limit is not None else 25,
            start_used=inputs.start if inputs.start is not None else 0
        )

    except ApiError as e:
        api_status_code = getattr(e, 'status_code', 500)
        if api_status_code == 404:
            # If the page itself wasn't found, raise a 404 HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"Page with ID '{inputs.page_id}' not found or user lacks permission."
            )
        else:
            # For other API errors, construct a detailed message and raise HTTPException
            # Safely construct the detail message WITHOUT relying on e.text
            error_reason = getattr(e, 'reason', 'Unknown Reason')
            error_url = getattr(e, 'url', 'N/A')
            detail_message = f"Error getting comments from Confluence: Details: Received {api_status_code} {error_reason} for url: {error_url}"
            raise HTTPException(
                # Use the API status code if it's a standard client/server error, else 500
                status_code=api_status_code if 400 <= api_status_code < 600 else 500,
                detail=detail_message
            )
    
    except Exception as e:
        # Catch-all for other unexpected errors, e.g., issues with response parsing
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing comments: {str(e)}")
