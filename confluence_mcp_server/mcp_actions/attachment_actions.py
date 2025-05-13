# This file will contain the logic for attachment-related MCP actions.

from typing import List, Optional

from atlassian import Confluence
from atlassian.errors import ApiError
from fastapi import HTTPException

from .schemas import (
    GetAttachmentsInput, AttachmentOutputItem, GetAttachmentsOutput
)

async def get_attachments_logic(
    client: Confluence,
    inputs: GetAttachmentsInput
) -> GetAttachmentsOutput:
    """
    Logic to retrieve attachments for a Confluence page.
    """
    try:
        # The atlassian-python-api's get_attachments_from_content returns a dictionary similar to other paginated list endpoints.
        # Example structure (simplified from typical Confluence REST API responses):
        # {
        #     'results': [
        #         {
        #             'id': 'att12345',
        #             'type': 'attachment',
        #             'status': 'current',
        #             'title': 'example.pdf',
        #             'metadata': {
        #                 'mediaType': 'application/pdf',
        #                 'comment': 'This is a test attachment.'
        #             },
        #             'version': {'number': 1, 'when': '2023-10-26T10:00:00.000Z'},
        #             'extensions': {'fileSize': 102400},
        #             '_links': {
        #                 'webui': '/display/SPACEKEY/PageTitle?preview=%2Fatt12345%2Fexample.pdf',
        #                 'download': '/download/attachments/PAGEID/example.pdf?version=1&modificationDate=1698314400000&api=v2',
        #                 'self': 'https://your-domain.atlassian.net/wiki/rest/api/content/PAGEID/child/attachment/att12345'
        #             }
        #         }, ...
        #     ],
        #     'start': 0,
        #     'limit': 25,
        #     'size': actual_number_returned,
        #     '_links': {'next': '/rest/api/content/PAGEID/child/attachment?limit=25&start=25'}
        # }

        api_response = client.get_attachments_from_content(
            page_id=inputs.page_id,
            filename=inputs.filename,
            media_type=inputs.media_type,
            limit=inputs.limit, # Defaults are handled by the library or API if None
            start=inputs.start  # Defaults are handled by the library or API if None
        )

        attachments_data = api_response.get('results', [])
        processed_attachments: List[AttachmentOutputItem] = []

        for item_data in attachments_data:
            attachment_id_str = str(item_data.get('id'))
            title = item_data.get('title', 'N/A')
            status = item_data.get('status', 'unknown')
            
            media_type = item_data.get('metadata', {}).get('mediaType')
            comment = item_data.get('metadata', {}).get('comment')
            
            file_size = item_data.get('extensions', {}).get('fileSize')
            
            version_info = item_data.get('version', {})
            version_number = version_info.get('number')
            created_date = version_info.get('when') # This is often the version creation date

            links = item_data.get('_links', {})
            download_link = links.get('download')
            web_ui_link = links.get('webui')

            processed_attachments.append(
                AttachmentOutputItem(
                    attachment_id=attachment_id_str,
                    title=title,
                    status=status,
                    media_type=media_type,
                    file_size=file_size,
                    created_date=created_date,
                    version_number=version_number,
                    download_link=download_link,
                    web_ui_link=web_ui_link,
                    comment=comment
                )
            )
        
        retrieved_count = api_response.get('size', len(processed_attachments))
        # The 'totalSize' or equivalent for total attachments on page might not be directly available
        # or might require a different call/interpretation. For now, we pass None if not in this response.
        total_available_from_api = api_response.get('totalSize') 

        next_start = None
        if '_links' in api_response and 'next' in api_response['_links']:
            # A 'next' link implies more results are available.
            # Simple calculation for next_start_offset:
            if retrieved_count == inputs.limit:
                 next_start = inputs.start + retrieved_count

        return GetAttachmentsOutput(
            attachments=processed_attachments,
            retrieved_count=retrieved_count,
            total_available=total_available_from_api, # May be None
            limit_used=inputs.limit,
            start_used=inputs.start,
            next_start_offset=next_start
        )

    except ApiError as e:
        # Correctly access status_code, reason, and url from e.response
        api_response_obj = e.response
        
        _status_code = 500 # Default
        _reason = "Not specified by API" # Default
        _url = "N/A" # Default

        if api_response_obj is not None:
            _status_code = api_response_obj.status_code if isinstance(api_response_obj.status_code, int) else _status_code
            _reason = api_response_obj.reason if api_response_obj.reason is not None else _reason
            if hasattr(api_response_obj, 'request') and api_response_obj.request is not None:
                _url = api_response_obj.request.url if api_response_obj.request.url is not None else _url
            elif hasattr(api_response_obj, 'url') and api_response_obj.url is not None: # Fallback if request object not present but url is
                _url = api_response_obj.url

        # Ensure status_code is an int for the HTTPException
        if not isinstance(_status_code, int):
            _status_code = 500
        
        if _status_code == 404:
            # Specific handling for 404 errors, ensuring the detail message is informative
            # and compatible with test assertions.
            final_detail = (f"Page with ID '{inputs.page_id}' not found, or attachments endpoint not available for it. "
                            f"[Confluence API: Status {_status_code}, Reason: '{_reason}', URL: '{_url}']")
            raise HTTPException(status_code=404, detail=final_detail)
        else:
            # General ApiError handling for other status codes
            detail_message = f"Error getting attachments from Confluence: Status {_status_code}."
            if _reason and _reason != "Not specified by API": # Check _reason is not None or empty
                detail_message += f" Reason: '{_reason}'_"
            if _url and _url != "N/A": # Check _url is not None or empty
                detail_message += f" URL: '{_url}'_"
            # It's good practice to include the relevant input identifier if possible
            detail_message += f" (Attempted for Page ID: '{inputs.page_id}')"
            
            raise HTTPException(status_code=_status_code, detail=detail_message)
    
    except Exception as e:
        # Catch-all for other unexpected errors, e.g., issues with response parsing or unexpected structure
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing attachments: {str(e)}")

# Placeholder for add_attachment_logic
# async def add_attachment_logic():
#     pass
