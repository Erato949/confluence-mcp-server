# Logic for space-related Confluence tools

import logging
from typing import Optional
import httpx
from fastapi import HTTPException
from .schemas import GetSpacesInput, GetSpacesOutput

logger = logging.getLogger(__name__)

async def get_spaces_logic(client: httpx.AsyncClient, inputs: GetSpacesInput) -> GetSpacesOutput:
    """
    Retrieves a list of spaces from Confluence.
    
    Args:
        client: Configured httpx.AsyncClient for Confluence API
        inputs: GetSpacesInput containing query parameters
        
    Returns:
        GetSpacesOutput containing list of spaces and metadata
    """
    try:
        # Build query parameters
        params = {
            'limit': inputs.limit,
            'start': inputs.start
        }
        
        if inputs.space_key:
            params['spaceKey'] = inputs.space_key
        if inputs.space_type:
            params['type'] = inputs.space_type
        if inputs.status:
            params['status'] = inputs.status
            
        # Make API request to get spaces
        response = await client.get('rest/api/space', params=params)
        
        if response.status_code == 200:
            data = response.json()
            return GetSpacesOutput(
                spaces=data.get('results', []),
                size=data.get('size', 0),
                start=data.get('start', 0),
                limit=data.get('limit', 0),
                is_last_page=data.get('size', 0) < inputs.limit
            )
        else:
            logger.error(f"Failed to retrieve spaces: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to retrieve spaces: {response.text}"
            )
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error retrieving spaces: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error retrieving spaces: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
