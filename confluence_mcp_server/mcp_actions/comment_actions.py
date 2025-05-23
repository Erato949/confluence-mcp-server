# Logic for comment-related Confluence tools

import logging
from typing import Optional
import httpx
from fastapi import HTTPException
from .schemas import GetCommentsInput, GetCommentsOutput

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
        # Build query parameters
        params = {
            'limit': inputs.limit,
            'start': inputs.start,
            'expand': 'body.storage,version,space'
        }
        
        if inputs.depth:
            params['depth'] = inputs.depth
            
        # Make API request to get page comments
        response = await client.get(f'rest/api/content/{inputs.page_id}/child/comment', params=params)
        
        if response.status_code == 200:
            data = response.json()
            return GetCommentsOutput(
                comments=data.get('results', []),
                size=data.get('size', 0),
                start=data.get('start', 0),
                limit=data.get('limit', 0),
                is_last_page=data.get('size', 0) < inputs.limit
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
