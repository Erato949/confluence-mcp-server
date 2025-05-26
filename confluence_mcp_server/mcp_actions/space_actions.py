# Logic for space-related Confluence tools

import logging
from typing import Optional
import httpx
from fastapi import HTTPException
from .schemas import GetSpacesInput, GetSpacesOutput, SpaceOutputItem

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
        # Build query parameters - only use fields that exist in GetSpacesInput
        params = {
            'limit': inputs.limit,
            'start': inputs.start
        }
            
        # Make API request to get spaces (Confluence Cloud uses /wiki/rest/api/ prefix)
        response = await client.get('/wiki/rest/api/space', params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Convert API response to our output format
            spaces = []
            for space_data in data.get('results', []):
                # Get the relative URL and convert to full URL if available
                webui_link = space_data.get('_links', {}).get('webui')
                full_url = None
                if webui_link:
                    # Construct full URL by combining base URL with relative path
                    confluence_base = str(client.base_url)
                    full_url = f"{confluence_base}{webui_link}"
                
                space_item = SpaceOutputItem(
                    space_id=space_data.get('id', 0),
                    key=space_data.get('key', ''),
                    name=space_data.get('name', ''),
                    type=space_data.get('type'),
                    status=space_data.get('status'),
                    url=full_url  # This will be None if no webui link, which is fine since field is Optional
                )
                spaces.append(space_item)
            
            # Calculate next start offset
            current_size = data.get('size', 0)
            next_start = None
            if current_size >= inputs.limit:
                next_start = inputs.start + current_size
                
            return GetSpacesOutput(
                spaces=spaces,
                total_available=data.get('totalSize', len(spaces)),
                next_start_offset=next_start
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
