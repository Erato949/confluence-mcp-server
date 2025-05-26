import logging
import os  # Added
from typing import List, Optional

import httpx
from fastapi import HTTPException

# Assuming schemas.py is in the same directory or accessible via Python path
from .schemas import (
    AttachmentOutputItem,
    GetAttachmentsInput,
    GetAttachmentsOutput,
    AddAttachmentInput,
    AddAttachmentOutput,
    DeleteAttachmentInput,
    DeleteAttachmentOutput
)

logger = logging.getLogger(__name__)

async def get_attachments_logic(client: httpx.AsyncClient, inputs: GetAttachmentsInput) -> GetAttachmentsOutput:
    """
    Retrieves a list of attachments for a given Confluence page.
    """
    page_id = inputs.page_id
    confluence_base_url = str(client.base_url).rstrip('/')
    
    logger.info(f"Attempting to retrieve attachments for page ID '{page_id}' with inputs: {inputs.model_dump_json(exclude_none=True)}")

    api_params = {
        "start": inputs.start,
        "limit": inputs.limit,
    }
    if inputs.filename:
        api_params["filename"] = inputs.filename
    if inputs.media_type:
        api_params["mediaType"] = inputs.media_type # Note: API uses 'mediaType'

    try:
        response = await client.get(
            f"/rest/api/content/{page_id}/child/attachment",
            params=api_params
        )
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        
        response_data = response.json()
        
        attachments_output_list: List[AttachmentOutputItem] = []
        results = response_data.get("results", [])
        
        for item in results:
            attachment_id = item.get("id")
            title = item.get("title")
            media_type = item.get("extensions", {}).get("mediaType") # API often has it here
            if not media_type and "mediaType" in item: # Fallback if it's at the top level
                 media_type = item.get("mediaType")

            file_size = item.get("extensions", {}).get("fileSize")
            
            version_info = item.get("version", {})
            created_date = version_info.get("when")
            author_display_name = version_info.get("by", {}).get("displayName")
            version_number = version_info.get("number")
            comment = version_info.get("message")

            links = item.get("_links", {})
            download_path = links.get("download")
            webui_path = links.get("webui")
            
            download_link_full = f"{confluence_base_url}{download_path}" if download_path else None
            webui_link_full = f"{confluence_base_url}{webui_path}" if webui_path else None

            attachments_output_list.append(
                AttachmentOutputItem(
                    attachment_id=attachment_id,
                    title=title,
                    media_type=media_type,
                    file_size=file_size,
                    created_date=created_date,
                    author_display_name=author_display_name,
                    version=version_number,
                    download_link=download_link_full,
                    webui_link=webui_link_full,
                    comment=comment,
                )
            )

        total_returned = len(attachments_output_list)
        total_available = response_data.get("size", total_returned) 

        next_start_offset = None
        if response_data.get("_links", {}).get("next"):
            next_start_offset = inputs.start + total_returned
            
        return GetAttachmentsOutput(
            attachments=attachments_output_list,
            total_returned=total_returned,
            total_available=total_available,
            next_start_offset=next_start_offset
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error retrieving attachments for page ID '{page_id}': {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            response_content = e.response.json()
            if isinstance(response_content, dict):
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
                api_msg = msg1 or msg2 or msg3
                if api_msg: error_detail = f"Confluence API Error: {api_msg}"
        except Exception: pass

        if e.response.status_code == 404:
            error_detail = f"Page with ID '{page_id}' not found, or attachments endpoint not available for this content type."
        elif e.response.status_code == 403:
             error_detail = f"Permission denied to access attachments for page ID '{page_id}'. Details: {error_detail}"
        raise HTTPException(status_code=e.response.status_code, detail=f"Error retrieving attachments: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Request error retrieving attachments for page ID '{page_id}': {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error retrieving attachments for page ID '{page_id}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while retrieving attachments: {str(e)}")

async def add_attachment_logic(client: httpx.AsyncClient, inputs: AddAttachmentInput) -> AddAttachmentOutput:
    """
    Adds an attachment to a given Confluence page.
    """
    page_id = inputs.page_id
    file_path = inputs.file_path
    confluence_base_url = str(client.base_url).rstrip('/')

    logger.info(f"Attempting to add attachment from path '{file_path}' to page ID '{page_id}' with inputs: {inputs.model_dump_json(exclude_none=True)}")

    if not os.path.exists(file_path):
        logger.error(f"File not found at path: {file_path}")
        raise HTTPException(status_code=400, detail=f"File not found at path: {file_path}")

    filename_on_confluence = inputs.filename_on_confluence or os.path.basename(file_path)
    
    form_data = {}
    if inputs.comment:
        form_data["comment"] = inputs.comment
    form_data["minorEdit"] = "false" 

    try:
        with open(file_path, "rb") as f:
            files_payload = {"file": (filename_on_confluence, f)}
            headers = {"X-Atlassian-Token": "nocheck"}

            response = await client.post(
                f"/rest/api/content/{page_id}/child/attachment",
                files=files_payload,
                data=form_data,
                headers=headers
            )
            response.raise_for_status()
        
        response_data = response.json()
        
        if not response_data.get("results") or not isinstance(response_data["results"], list) or len(response_data["results"]) == 0:
            logger.error(f"Unexpected response structure after adding attachment to page '{page_id}': {response_data}")
            raise HTTPException(status_code=500, detail="Failed to add attachment due to unexpected API response format.")

        attachment_data = response_data["results"][0]
        
        attachment_id = attachment_data.get("id")
        title = attachment_data.get("title")
        version_info = attachment_data.get("version", {})
        version_number = version_info.get("number")
        
        links = attachment_data.get("_links", {})
        download_path = links.get("download")
        download_link_full = f"{confluence_base_url}{download_path}" if download_path else None

        return AddAttachmentOutput(
            attachment_id=attachment_id,
            title=title,
            page_id=page_id,
            version=version_number,
            download_link=download_link_full,
            status="success"
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error adding attachment to page ID '{page_id}': {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            response_content = e.response.json()
            if isinstance(response_content, dict):
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
                api_msg = msg1 or msg2 or msg3
                if api_msg: error_detail = f"Confluence API Error: {api_msg}"
        except Exception: pass
        
        if e.response.status_code == 404:
            error_detail = f"Page with ID '{page_id}' not found."
        elif e.response.status_code == 403:
             error_detail = f"Permission denied to add attachment to page ID '{page_id}'. Details: {error_detail}"
        elif e.response.status_code == 400:
             error_detail = f"Bad request adding attachment to page ID '{page_id}'. May be due to file size, type, or name. Details: {error_detail}"

        raise HTTPException(status_code=e.response.status_code, detail=f"Error adding attachment: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Request error adding attachment to page ID '{page_id}': {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except IOError as e: 
        logger.error(f"File I/O error for '{file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading file for attachment: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error adding attachment to page ID '{page_id}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while adding attachment: {str(e)}")

async def delete_attachment_logic(client: httpx.AsyncClient, inputs: DeleteAttachmentInput) -> DeleteAttachmentOutput:
    """
    Permanently deletes an attachment from Confluence.
    """
    attachment_id = inputs.attachment_id
    logger.info(f"Attempting to permanently delete attachment ID '{attachment_id}'")

    headers = {"X-Atlassian-Token": "nocheck"}

    try:
        response = await client.delete(
            f"/rest/api/content/{attachment_id}",
            headers=headers
        )
        response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
                                    # For DELETE, a 204 No Content is typical for success.
        
        logger.info(f"Attachment ID '{attachment_id}' successfully deleted (status {response.status_code}).")
        return DeleteAttachmentOutput(
            attachment_id=attachment_id,
            message=f"Attachment with ID '{attachment_id}' has been permanently deleted.",
            status="success"
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error deleting attachment ID '{attachment_id}': {e.request.method} {e.request.url} - Status {e.response.status_code}", exc_info=True)
        error_detail = f"Confluence API Error: Status {e.response.status_code}"
        try:
            response_content = e.response.json() # May not always be JSON for errors like 404
            if isinstance(response_content, dict):
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
                api_msg = msg1 or msg2 or msg3
                if api_msg: error_detail = f"Confluence API Error: {api_msg}"
        except Exception: 
            # If response is not JSON or parsing fails, use the raw text if available
            if e.response and hasattr(e.response, 'text') and e.response.text:
                error_detail = f"Confluence API Error: Status {e.response.status_code}, Response: {e.response.text[:200]}" # Truncate long non-JSON responses
            pass # Keep generic error_detail if nothing better found
        
        if e.response.status_code == 404:
            error_detail = f"Attachment with ID '{attachment_id}' not found or already deleted."
        elif e.response.status_code == 403:
             error_detail = f"Permission denied to delete attachment ID '{attachment_id}'. Details: {error_detail}"
        
        raise HTTPException(status_code=e.response.status_code, detail=f"Error deleting attachment: {error_detail}")
    except httpx.RequestError as e:
        logger.error(f"Request error deleting attachment ID '{attachment_id}': {e.request.method} {e.request.url}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Error connecting to Confluence: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error deleting attachment ID '{attachment_id}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while deleting attachment: {str(e)}")
