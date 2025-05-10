# confluence_mcp_server/mcp_actions/space_actions.py

from typing import List, Optional
from atlassian import Confluence
from atlassian.errors import ApiError
from .schemas import GetSpacesInput, GetSpacesOutput, SpaceSchema

def get_spaces_logic(
    client: Confluence,
    inputs: GetSpacesInput
) -> GetSpacesOutput:
    """
    Logic for the get_spaces tool.
    Fetches spaces from Confluence.
    Prioritizes fetching by space_ids, then space_keys, then all spaces with filters.
    """
    processed_spaces: List[SpaceSchema] = []
    
    try:
        # Scenario 1: Fetch by specific space IDs
        if inputs.space_ids:
            for space_id_input in inputs.space_ids:
                try:
                    # The API client expects space_id as string, Pydantic model might have it as int
                    space_data_item = client.get_space(space_id=str(space_id_input)) 
                    if space_data_item:
                        processed_spaces.append(
                            SpaceSchema(
                                id=int(space_data_item['id']), # Ensure ID is int for schema
                                key=space_data_item['key'],
                                name=space_data_item['name'],
                                type=space_data_item['type'],
                                status=space_data_item.get('status', 'CURRENT')
                            )
                        )
                except ApiError as e:
                    if e.response and e.response.status_code == 404:
                        print(f"Warning: Space with ID '{space_id_input}' not found. Skipping.")
                    else:
                        print(f"Warning: API error fetching space ID '{space_id_input}': {e}. Skipping.")
                except Exception as e: # Catch other potential errors during individual fetch
                    print(f"Warning: Unexpected error fetching space ID '{space_id_input}': {e}. Skipping.")
            
            return GetSpacesOutput(
                spaces=processed_spaces,
                count=len(processed_spaces),
                total_available=len(processed_spaces) # For ID/key fetches, total_available is just what we found
            )

        # Scenario 2: Fetch by specific space keys
        elif inputs.space_keys:
            for space_key_input in inputs.space_keys:
                try:
                    space_data_item = client.get_space(space_key=space_key_input)
                    if space_data_item:
                        processed_spaces.append(
                            SpaceSchema(
                                id=int(space_data_item['id']), # Ensure ID is int
                                key=space_data_item['key'],
                                name=space_data_item['name'],
                                type=space_data_item['type'],
                                status=space_data_item.get('status', 'CURRENT')
                            )
                        )
                except ApiError as e:
                    if e.response and e.response.status_code == 404:
                        print(f"Warning: Space with key '{space_key_input}' not found. Skipping.")
                    else:
                        print(f"Warning: API error fetching space key '{space_key_input}': {e}. Skipping.")
                except Exception as e: # Catch other potential errors
                    print(f"Warning: Unexpected error fetching space key '{space_key_input}': {e}. Skipping.")
            
            return GetSpacesOutput(
                spaces=processed_spaces,
                count=len(processed_spaces),
                total_available=len(processed_spaces)
            )

        # Scenario 3: Fetch all spaces with optional filters (default behavior)
        api_params_for_fetch = {}
        if inputs.start is not None:
            api_params_for_fetch['start'] = inputs.start
        if inputs.limit is not None:
            api_params_for_fetch['limit'] = inputs.limit
        
        # Parameters for the Confluence API client
        if inputs.status:
            api_params_for_fetch['status'] = inputs.status
        if inputs.space_type: # Note: API client uses 'space_type' not 'type'
            api_params_for_fetch['space_type'] = inputs.space_type
        if inputs.label:
            api_params_for_fetch['label'] = inputs.label
        if inputs.favourite is not None: # Pass boolean directly
            api_params_for_fetch['favourite'] = inputs.favourite
        if inputs.expand:
            # Ensure expand is a comma-separated string if it's a list
            api_params_for_fetch['expand'] = ",".join(inputs.expand) if isinstance(inputs.expand, list) else inputs.expand

        print(f"Calling Confluence API get_all_spaces with params: {api_params_for_fetch}")
        raw_spaces_data = client.get_all_spaces(**api_params_for_fetch)

        if raw_spaces_data and 'results' in raw_spaces_data:
            for space_data_item in raw_spaces_data['results']:
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
                        id=int(space_data_item['id']), # Ensure ID is int
                        key=space_data_item['key'],
                        name=space_data_item['name'],
                        type=space_data_item['type'], 
                        status=space_data_item.get('status', 'CURRENT') 
                    )
                )
        
        # 'size' in the API response indicates the number of items in the current page/batch
        num_retrieved_this_call = raw_spaces_data.get('size', len(processed_spaces)) if raw_spaces_data else len(processed_spaces)

        return GetSpacesOutput(
            spaces=processed_spaces,
            count=len(processed_spaces),
            total_available=num_retrieved_this_call 
        )

    except Exception as e:
        print(f"Error encountered in get_spaces_logic: {type(e).__name__} - {e}")
        raise
