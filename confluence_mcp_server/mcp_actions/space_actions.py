# confluence_mcp_server/mcp_actions/space_actions.py

from typing import List
from atlassian import Confluence
from .schemas import GetSpacesInput, GetSpacesOutput, SpaceSchema

def get_spaces_logic(
    client: Confluence,
    inputs: GetSpacesInput
) -> GetSpacesOutput:
    """
    Logic for the get_spaces tool.
    Fetches spaces from Confluence and applies client-side filtering if needed.
    """
    try:
        api_params_for_fetch = {}
        # Parameters that get_all_spaces in v4.0.3 definitely supports
        if inputs.start is not None:
            api_params_for_fetch['start'] = inputs.start
        
        # For client-side filtering, we might need to fetch more initially if a type filter is applied
        # However, if a limit is also applied, we respect the limit on the *final filtered* list.
        # This can get complex. A simpler client-side filter approach:
        # Fetch with limit if provided (or a reasonable default), then filter.
        # The Confluence API itself usually limits to 25 or 50 by default if no limit is sent.
        
        effective_limit_for_fetch = inputs.limit
        if inputs.space_type and inputs.limit:
            # If filtering by type AND a limit is set, we might need to fetch more to find enough matches.
            # For simplicity now, we'll fetch up to a slightly larger number if a type filter is active,
            # or just rely on multiple paged fetches if this were a full implementation.
            # Let's set a practical cap for initial fetch if type filtering is active.
            # A more robust solution would involve pagination until enough filtered results are found or all spaces are checked.
            # For now, let's fetch up to 100 if a type is specified and limit is also specified,
            # as a heuristic to get enough items to filter from.
            # This is a simplification; true pagination to meet a limit post-filter is more involved.
             if inputs.limit < 50: # If desired limit is small, fetch a bit more for filtering
                 effective_limit_for_fetch = 100 # Fetch more to have a chance to find typed spaces
             else: # If desired limit is already large, use that
                 effective_limit_for_fetch = inputs.limit

        if effective_limit_for_fetch is not None:
             api_params_for_fetch['limit'] = effective_limit_for_fetch
        # else, rely on API's default limit (often 25 or 50)

        # We do NOT pass inputs.space_type to the API call directly as it's not supported for this library version's method.
        # if inputs.space_type:
            # The Confluence API uses 'type' for space type filtering.
            # api_params_for_fetch['type'] = inputs.space_type # This caused TypeError
        
        print(f"Calling Confluence API get_all_spaces with params: {api_params_for_fetch}")
        raw_spaces_data = client.get_all_spaces(**api_params_for_fetch)

        processed_spaces: List[SpaceSchema] = []
        if raw_spaces_data and 'results' in raw_spaces_data:
            for space_data_item in raw_spaces_data['results']:
                # Client-side type filtering
                if inputs.space_type and space_data_item.get('type') != inputs.space_type:
                    continue  # Skip if type doesn't match

                # Robustness: Check for essential keys before creating SpaceSchema
                required_keys = ['id', 'key', 'name', 'type']
                missing_keys = [key for key in required_keys if key not in space_data_item]
                if missing_keys:
                    space_id_for_log = space_data_item.get('id', 'UNKNOWN_ID')
                    space_key_for_log = space_data_item.get('key', 'UNKNOWN_KEY')
                    print(f"Warning: Skipping space (ID: {space_id_for_log}, Key: {space_key_for_log}) due to missing keys: {missing_keys}")
                    continue

                processed_spaces.append(
                    SpaceSchema(
                        id=space_data_item['id'],
                        key=space_data_item['key'],
                        name=space_data_item['name'],
                        type=space_data_item['type'], 
                        status=space_data_item.get('status', 'CURRENT') 
                    )
                )
                
                # If a limit was specified for the *output*, respect it after filtering
                if inputs.limit is not None and len(processed_spaces) >= inputs.limit:
                    break 
        
        total_count_on_server = raw_spaces_data.get('totalSize') # Total before client-side filtering and limiting

        return GetSpacesOutput(
            spaces=processed_spaces,
            count=len(processed_spaces),
            total_available=total_count_on_server # This is total available from the API call, not post-filter total.
                                                 # Accurately getting total_available post-filter would require fetching all.
        )

    except Exception as e:
        print(f"Error encountered in get_spaces_logic: {type(e).__name__} - {e}")
        raise
