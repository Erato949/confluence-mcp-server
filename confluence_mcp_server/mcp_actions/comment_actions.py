# Logic for comment-related Confluence tools

import logging
from typing import Optional
import httpx
from fastapi import HTTPException
from .schemas import GetCommentsInput, GetCommentsOutput, CommentOutputItem

logger = logging.getLogger(__name__)

async def get_comments_logic(client: httpx.AsyncClient, inputs: GetCommentsInput) -> GetCommentsOutput:
    """
    Retrieves comments for a specific Confluence page.
    
    Args:
        client: Configured httpx.AsyncClient for Confluence API
        inputs: GetCommentsInput containing page_id and query parameters
        
    Returns:
        GetCommentsOutput containing list of comments and metadata
    """
    try:
        # Build query parameters - only use fields that exist in GetCommentsInput
        params = {
            'limit': inputs.limit,
            'start': inputs.start
        }
        
        # Use expand parameter if provided, otherwise use default expand for useful comment data
        if inputs.expand:
            params['expand'] = inputs.expand
        else:
            params['expand'] = 'body.storage,version,ancestors'
            
        # Make API request to get page comments
        response = await client.get(f'/wiki/rest/api/content/{inputs.page_id}/child/comment', params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Convert API response to our output format
            comments = []
            confluence_base = str(client.base_url)
            
            for comment_data in data.get('results', []):
                # Get comment URL
                webui_link = comment_data.get('_links', {}).get('webui')
                comment_url = None
                if webui_link:
                    comment_url = f"{confluence_base}{webui_link}"
                
                # Get author information
                version_info = comment_data.get('version', {})
                author_info = version_info.get('by', {})
                author_display_name = author_info.get('displayName')
                
                # Get comment content
                body_storage = comment_data.get('body', {}).get('storage', {})
                comment_body = body_storage.get('value', '') if body_storage else ''
                
                # Get parent comment ID (from ancestors)
                parent_comment_id = None
                ancestors = comment_data.get('ancestors', [])
                if ancestors:
                    # The immediate parent would be the last ancestor
                    parent_comment_id = ancestors[-1].get('id')
                
                comment_item = CommentOutputItem(
                    comment_id=comment_data.get('id', ''),
                    author_display_name=author_display_name,
                    created_date=comment_data.get('history', {}).get('createdDate', ''),
                    last_updated_date=version_info.get('when'),
                    body=comment_body,
                    parent_comment_id=parent_comment_id,
                    url=comment_url
                )
                comments.append(comment_item)
            
            # Calculate next start offset
            current_size = data.get('size', 0)
            next_start = None
            if current_size >= inputs.limit:
                next_start = inputs.start + current_size
                
            return GetCommentsOutput(
                comments=comments,
                total_returned=len(comments),
                total_available=data.get('totalSize', len(comments)),
                next_start_offset=next_start
            )
        elif response.status_code == 404:
            logger.error(f"Page not found: {inputs.page_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Page with ID {inputs.page_id} not found"
            )
        else:
            logger.error(f"Failed to retrieve comments for page {inputs.page_id}: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to retrieve comments: {response.text}"
            )
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error retrieving comments: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error retrieving comments: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
