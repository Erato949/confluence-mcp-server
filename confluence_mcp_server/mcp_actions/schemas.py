# Pydantic models for tool inputs and outputs
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator, field_validator

# Common Base Models (if any common fields emerge, consider a base)

# --- Get_Page Schemas ---
class GetPageInput(BaseModel):
    page_id: Optional[str] = Field(default=None, description="The ID of the page to retrieve.")
    space_key: Optional[str] = Field(default=None, description="The key of the space where the page resides (used with title).")
    title: Optional[str] = Field(default=None, description="The title of the page to retrieve (used with space_key).")
    expand: Optional[str] = Field(default=None, description="A comma-separated list of properties to expand (e.g., 'body.view,version,space').")

    @model_validator(mode='after')
    def check_page_id_or_space_key_and_title(cls, values):
        page_id = values.page_id
        space_key = values.space_key
        title = values.title
        if page_id is None and not (space_key and title):
            raise ValueError("Either 'page_id' or both 'space_key' and 'title' must be provided.")
        if page_id and (space_key or title):
            raise ValueError("'page_id' cannot be provided together with 'space_key' or 'title'.")
        return values

class PageOutput(BaseModel):
    page_id: str = Field(..., description="The ID of the page.")
    space_key: Optional[str] = Field(default=None, description="The key of the space the page belongs to.")
    title: str = Field(..., description="The title of the page.")
    author_id: Optional[str] = Field(default=None, description="The account ID of the user who created the page.")
    created_date: Optional[str] = Field(default=None, description="The date and time the page was created.")
    last_modified_date: Optional[str] = Field(default=None, description="The date and time the page was last modified.")
    version: Optional[int] = Field(default=None, description="The version number of the page.")
    url: Optional[HttpUrl] = Field(default=None, description="The URL of the page on Confluence.")
    content: Optional[str] = Field(default=None, description="The content of the page (if requested via expand).")
    parent_page_id: Optional[str] = Field(default=None, description="The ID of the parent page, if any.")


# --- Search_Pages Schemas ---
class SearchPagesInput(BaseModel):
    query: Optional[str] = Field(default=None, description="The search query string (e.g., free text).")
    cql: Optional[str] = Field(default=None, description="A CQL (Confluence Query Language) string for advanced searching.")
    space_key: Optional[str] = Field(default=None, description="The key of the space to limit the search to.")
    limit: int = Field(default=25, ge=1, le=100, description="Maximum number of pages to return.")
    start: int = Field(default=0, ge=0, description="Starting offset for pagination.")
    expand: Optional[str] = Field(default=None, description="A comma-separated list of properties to expand for each result (e.g., 'body.view,version').")
    excerpt: Optional[str] = Field(default=None, pattern=r"^(none|highlight|indexed)$", description="Type of excerpt to include (none, highlight, indexed).")

    @model_validator(mode='after')
    def check_query_or_cql_provided(cls, values):
        if not values.query and not values.cql:
            raise ValueError("Either 'query' or 'cql' must be provided for searching.")
        if values.query and values.cql:
            raise ValueError("'query' and 'cql' cannot be provided simultaneously. Use one or the other.")
        return values

class SearchPagesOutputItem(BaseModel):
    page_id: str = Field(..., description="ID of the found page.")
    title: str = Field(..., description="Title of the found page.")
    space_key: Optional[str] = Field(default=None, description="Space key of the page.")
    last_modified_date: Optional[str] = Field(default=None, description="Last modified date of the page.")
    url: Optional[HttpUrl] = Field(default=None, description="URL of the page.")
    excerpt_highlight: Optional[str] = Field(default=None, description="Highlighted excerpt of the page content, if requested.")
    content_preview: Optional[str] = Field(default=None, description="Preview of the page content (e.g., if 'body.view' in expand).")
    # Add other relevant fields that Confluence search might return and are useful

class SearchPagesOutput(BaseModel):
    results: List[SearchPagesOutputItem] = Field(default_factory=list, description="List of pages found.")
    total_available: int = Field(..., description="Total number of pages available for the search criteria.")
    next_start_offset: Optional[int] = Field(default=None, description="Offset for the next page of results, if more are available.")


# --- Get_Spaces Schemas ---
class GetSpacesInput(BaseModel):
    limit: int = Field(default=25, ge=1, le=100, description="Maximum number of spaces to return.")
    start: int = Field(default=0, ge=0, description="Starting offset for pagination.")
    # Add other potential filters like space_type, status, label if needed by API

class SpaceOutputItem(BaseModel):
    space_id: int = Field(..., description="ID of the space.")
    key: str = Field(..., description="Key of the space.")
    name: str = Field(..., description="Name of the space.")
    type: Optional[str] = Field(default=None, description="Type of the space (e.g., 'global', 'personal').")
    status: Optional[str] = Field(default=None, description="Status of the space.")
    url: Optional[HttpUrl] = Field(default=None, description="URL to the space homepage.")

class GetSpacesOutput(BaseModel):
    spaces: List[SpaceOutputItem] = Field(default_factory=list, description="List of spaces retrieved.")
    total_available: int = Field(..., description="Total number of spaces available.")
    next_start_offset: Optional[int] = Field(default=None, description="Offset for the next page of results, if more are available.")


# --- Create_Page Schemas ---
class CreatePageInput(BaseModel):
    space_key: str = Field(..., description="The key of the space where the page will be created.")
    title: str = Field(..., min_length=1, description="The title of the new page.")
    content: str = Field(..., description="The content of the new page (usually in Confluence Storage Format - XML).")
    parent_page_id: Optional[str] = Field(default=None, description="The ID of the parent page, if this is a child page.")
    # Consider adding content_type (e.g., 'storage', 'wiki') if API supports/requires

class CreatePageOutput(BaseModel):
    page_id: str = Field(..., description="The ID of the newly created page.")
    title: str = Field(..., description="The title of the newly created page.")
    space_key: str = Field(..., description="The key of the space where the page was created.")
    version: int = Field(..., description="The version number of the newly created page (usually 1).")
    url: HttpUrl = Field(..., description="The URL of the newly created page.")
    status: Optional[str] = Field(default="current", description="Status of the page, e.g., 'current'.")


# --- Update_Page Schemas ---
class UpdatePageInput(BaseModel):
    page_id: str = Field(..., description="The ID of the page to update.")
    new_version_number: int = Field(..., gt=0, description="The new version number for the page (must be current version + 1).")
    title: Optional[str] = Field(default=None, min_length=1, description="The new title for the page. If None, title remains unchanged.")
    content: Optional[str] = Field(default=None, description="The new content for the page (usually Confluence Storage Format). If None, content remains unchanged.")
    # space_key: Optional[str] = Field(default=None, description="If provided, attempts to move the page to this space. Requires appropriate permissions.") # Moving might be a separate tool
    parent_page_id: Optional[str] = Field(default=None, description="The ID of the new parent page. If None, parent remains unchanged. Use empty string or special value if API needs it to make it top-level.")
    # status: Optional[str] = Field(default=None, description="New status for the page (e.g., 'archived').") # Status update might be part of this or separate

    @model_validator(mode='after')
    def check_at_least_one_updatable_field(cls, values):
        if values.title is None and values.content is None and values.parent_page_id is None: # and values.space_key is None and values.status is None:
            raise ValueError("At least one field (title, content, parent_page_id) must be provided to update the page.")
        return values

class UpdatePageOutput(BaseModel):
    page_id: str = Field(..., description="The ID of the updated page.")
    title: str = Field(..., description="The title of the updated page.")
    space_key: str = Field(..., description="The key of the space where the page resides.")
    version: int = Field(..., description="The new version number of the page.")
    url: HttpUrl = Field(..., description="The URL of the updated page.")
    last_modified_date: str = Field(..., description="Timestamp of the last modification.")


# --- Delete_Page Schemas ---
class DeletePageInput(BaseModel):
    page_id: str = Field(..., description="The ID of the Confluence page to be deleted (moved to trash).")

class DeletePageOutput(BaseModel):
    page_id: str = Field(..., description="The ID of the page that was moved to trash.")
    message: str = Field(..., description="Confirmation message for the delete operation.")
    status: str = Field(default="success", description="Status of the delete operation.")


# --- Get_Comments Schemas ---
class GetCommentsInput(BaseModel):
    page_id: str = Field(..., description="The ID of the page from which to retrieve comments.")
    limit: int = Field(default=25, ge=1, le=100, description="Maximum number of comments to return.")
    start: int = Field(default=0, ge=0, description="Starting offset for pagination.")
    expand: Optional[str] = Field(default=None, description="Comma-separated list of properties to expand for each comment (e.g., 'history', 'restrictions.read.restrictions.user').")
    # Note: Confluence API for comments might have different expand options than pages.

class CommentOutputItem(BaseModel):
    comment_id: str = Field(..., description="ID of the comment.")
    author_display_name: Optional[str] = Field(default=None, description="Display name of the comment author.")
    # author_id: Optional[str] = Field(default=None, description="Account ID of the comment author.") # May not be directly available or consistently
    created_date: str = Field(..., description="Timestamp when the comment was created.")
    last_updated_date: Optional[str] = Field(default=None, description="Timestamp when the comment was last updated.")
    body: str = Field(..., description="Content of the comment (typically in Confluence storage format or view format depending on expand).")
    parent_comment_id: Optional[str] = Field(default=None, description="ID of the parent comment, if this is a reply.")
    url: Optional[HttpUrl] = Field(default=None, description="URL to view the comment directly if available.")

class GetCommentsOutput(BaseModel):
    comments: List[CommentOutputItem] = Field(default_factory=list, description="List of comments retrieved.")
    total_returned: int = Field(..., description="Number of comments returned in this response.")
    total_available: int = Field(..., description="Total number of comments available for the page.")
    next_start_offset: Optional[int] = Field(default=None, description="Offset for the next page of results, if more comments are available.")


# --- Add_Comment Schemas ---
class AddCommentInput(BaseModel):
    page_id: str = Field(..., description="The ID of the page to add the comment to.")
    content: str = Field(..., min_length=1, description="The content of the comment (Confluence Storage Format XML).")
    parent_comment_id: Optional[str] = Field(default=None, description="ID of the parent comment if this is a reply.")

class AddCommentOutput(BaseModel):
    comment_id: str = Field(..., description="ID of the newly created comment.")
    page_id: str = Field(..., description="ID of the page the comment was added to.")
    url: Optional[HttpUrl] = Field(default=None, description="URL to the newly created comment.")
    status: str = Field(default="success", description="Status of the add comment operation.")


# --- Delete_Page Schemas ---
class DeletePageInput(BaseModel):
    page_id: str = Field(..., description="The ID of the page to be moved to trash.")
    # Future consideration: Add 'purge: bool = False' if permanent delete logic (beyond trash) is implemented.
    # Current Confluence API for DELETE /content/{id} typically moves to trash, not permanent deletion.

class DeletePageOutput(BaseModel):
    page_id: str = Field(..., description="The ID of the page that was moved to trash.")
    message: str = Field(..., description="Confirmation message for the delete operation.")
    status: str = Field(default="success", description="Status of the delete operation.")


# --- Get_Attachments Schemas ---
class GetAttachmentsInput(BaseModel):
    page_id: str = Field(..., description="The ID of the page from which to retrieve attachments.")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of attachments to return.") # Check Confluence API for actual max limit
    start: int = Field(default=0, ge=0, description="Starting offset for pagination.")
    filename: Optional[str] = Field(default=None, description="Filter attachments by filename.")
    media_type: Optional[str] = Field(default=None, description="Filter attachments by media type (e.g., 'image/png', 'application/pdf').")

class AttachmentOutputItem(BaseModel):
    attachment_id: str = Field(..., description="ID of the attachment.")
    title: str = Field(..., description="Title (filename) of the attachment.")
    media_type: Optional[str] = Field(default=None, description="Media type of the attachment.")
    file_size: Optional[int] = Field(default=None, description="Size of the attachment in bytes.")
    created_date: Optional[str] = Field(default=None, description="Timestamp when the attachment was created.")
    author_display_name: Optional[str] = Field(default=None, description="Display name of the user who uploaded the attachment.")
    version: Optional[int] = Field(default=None, description="Version number of the attachment.")
    download_link: Optional[str] = Field(default=None, description="Relative download link for the attachment.") # Often needs base URL prepended
    webui_link: Optional[str] = Field(default=None, description="Relative link to view the attachment in Confluence UI.")
    comment: Optional[str] = Field(default=None, description="Comment associated with the attachment version.")

class GetAttachmentsOutput(BaseModel):
    attachments: List[AttachmentOutputItem] = Field(default_factory=list, description="List of attachments retrieved.")
    total_returned: int = Field(..., description="Number of attachments returned in this response.")
    total_available: int = Field(..., description="Total number of attachments available for the page and filters.")
    next_start_offset: Optional[int] = Field(default=None, description="Offset for the next page of results, if more attachments are available.")


# --- Add_Attachment Schemas ---
class AddAttachmentInput(BaseModel):
    page_id: str = Field(..., description="The ID of the page to add the attachment to.")
    file_path: str = Field(..., description="The local path to the file to be uploaded.") # This implies the server has access to this path
    # Alternatively, file_content: bytes and filename: str might be better for MCP
    # For now, assuming file_path is resolvable by the server process.
    filename_on_confluence: Optional[str] = Field(default=None, description="Optional name for the file on Confluence. If None, uses the local filename.")
    comment: Optional[str] = Field(default=None, description="Optional comment for the attachment version.")
    # content_type: Optional[str] = Field(default=None, description="MIME type of the file. If None, will be inferred if possible.")

class AddAttachmentOutput(BaseModel):
    attachment_id: str = Field(..., description="ID of the newly uploaded attachment (or a new version).")
    title: str = Field(..., description="Filename of the attachment on Confluence.")
    page_id: str = Field(..., description="ID of the page the attachment was added to.")
    version: int = Field(..., description="Version number of the attachment.")
    download_link: Optional[str] = Field(default=None, description="Relative download link.")
    status: str = Field(default="success", description="Status of the add attachment operation.")


# --- Delete_Attachment Schemas ---
class DeleteAttachmentInput(BaseModel):
    attachment_id: str = Field(..., description="The ID of the attachment to be permanently deleted.")

class DeleteAttachmentOutput(BaseModel):
    attachment_id: str = Field(..., description="The ID of the attachment that was deleted.")
    message: str = Field(..., description="Confirmation message for the delete operation.")
    status: str = Field(default="success", description="Status of the delete operation.")
