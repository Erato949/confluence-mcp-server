from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator

class MCPToolSchema(BaseModel):
    """
    Schema representing a single tool available through the MCP server.
    Based on general MCP principles.
    """
    name: str = Field(..., description="The unique name of the tool.")
    description: str = Field(..., description="A human-readable description of what the tool does.")
    input_schema: Dict[str, Any] = Field(..., description="A JSON schema describing the expected input parameters for the tool.")
    output_schema: Dict[str, Any] = Field(..., description="A JSON schema describing the expected output of the tool.")

class MCPListToolsResponse(BaseModel):
    """
    Schema for the response when listing available tools.
    """
    tools: List[MCPToolSchema]

class MCPExecuteRequest(BaseModel):
    """
    Schema for a request to execute a tool.
    """
    tool_name: str = Field(..., description="The name of the tool to execute.")
    inputs: Dict[str, Any] = Field(..., description="A dictionary of input parameters for the tool, conforming to its input_schema.")

class MCPExecuteResponse(BaseModel):
    """
    Schema for the response after executing a tool.
    """
    tool_name: str = Field(..., description="The name of the tool that was executed.")
    status: str = Field(..., description="Execution status (e.g., 'success', 'error').")
    outputs: Optional[Dict[str, Any]] = Field(None, description="A dictionary of output data from the tool, conforming to its output_schema. Present on success.")
    error_message: Optional[str] = Field(None, description="An error message if the execution failed. Present on error.")
    error_type: Optional[str] = Field(None, description="A more specific error type if applicable. Present on error.")


# --- Specific Tool Schemas (to be added as we implement tools) ---

# --- Schemas for 'get_spaces' tool ---

class GetSpacesInput(BaseModel):
    """
    Input schema for the get_spaces tool.
    Allows for optional filtering and pagination.
    """
    space_ids: Optional[List[int]] = Field(None, description="List of space IDs to retrieve. If provided, other filters (except limit/start for potential future individual call limits) are ignored.", examples=[[123, 456]])
    space_keys: Optional[List[str]] = Field(None, description="List of space keys to retrieve. If provided, other filters (except limit/start) are ignored.", examples=[["KEY1", "KEY2"]])
    
    space_type: Optional[str] = Field(None, description="Filter by space type (e.g., 'global', 'personal').", examples=["global"])
    status: Optional[str] = Field(None, description="Filter by space status (e.g., 'current', 'archived').", examples=["current"])
    label: Optional[str] = Field(None, description="Filter spaces by a specific label.", examples=["team-space"])
    favourite: Optional[bool] = Field(None, description="Filter spaces by whether they are marked as favourite.")
    expand: Optional[List[str]] = Field(None, description="List of properties to expand in the results (e.g., 'description.plain', 'metadata.labels').", examples=[["description.plain"]])
    
    limit: Optional[int] = Field(None, description="Maximum number of spaces to return.", gt=0, examples=[10])
    start: Optional[int] = Field(None, description="Starting index for pagination (0-based).", ge=0, examples=[0])

    @model_validator(mode='before')
    @classmethod
    def check_exclusive_filters(cls, values: Any) -> Any:
        if not isinstance(values, dict):
             return values

        id_filters_present = values.get('space_ids') is not None or values.get('space_keys') is not None
        
        general_filter_keys = ['space_type', 'status', 'label', 'favourite']
        general_filters_present = any(values.get(k) is not None for k in general_filter_keys)

        if id_filters_present and general_filters_present:
            raise ValueError("Cannot use 'space_ids' or 'space_keys' with other general filters like 'space_type', 'status', 'label', or 'favourite'.")
        return values


class SpaceSchema(BaseModel):
    """
    Represents a Confluence space.
    """
    id: int = Field(..., description="The ID of the space.")
    key: str = Field(..., description="The key of the space.")
    name: str = Field(..., description="The name of the space.")
    type: str = Field(..., description="The type of the space (e.g., 'global', 'personal').")
    status: str = Field(..., description="The status of the space (e.g., 'CURRENT').")
    # _links: Dict[str, str] = Field(..., description="Links related to the space, e.g., web UI.") # Often contains a 'webui' link

class GetSpacesOutput(BaseModel):
    """
    Output schema for the get_spaces tool.
    Returns a list of spaces.
    """
    spaces: List[SpaceSchema] = Field(..., description="A list of Confluence spaces.")
    count: int = Field(..., description="The number of spaces returned in this response.")
    total_available: Optional[int] = Field(None, description="The total number of spaces available on the server matching the query (if known).")


# --- Schemas for 'Get_Page' tool ---

class GetPageInput(BaseModel):
    """
    Input schema for the Get_Page tool.
    Requires page_id and allows optional expansion of page details.
    """
    page_id: int = Field(..., description="The ID of the Confluence page to retrieve.")
    expand: Optional[str] = Field(None, description="A comma-separated list of properties to expand on the page object (e.g., 'body.storage,version,space').", examples=["body.storage,version"])

class GetPageOutput(BaseModel):
    """
    Output schema for the Get_Page tool.
    Returns detailed information about a Confluence page.
    """
    page_id: int = Field(..., description="The ID of the page.")
    title: str = Field(..., description="The title of the page.")
    space_key: str = Field(..., description="The key of the space this page belongs to.")
    status: str = Field(..., description="The status of the page (e.g., 'current', 'draft').")
    content: Optional[str] = Field(None, description="The content of the page, typically in storage format. Requires 'body.storage' in expand input.")
    version: Optional[int] = Field(None, description="The version number of the page. Requires 'version' in expand input.")
    web_url: str = Field(..., description="The web URL to view the page.")
    # Add other relevant fields as needed based on common use cases or API response
    # e.g., author, last_modified_date, etc. if 'history' or other elements are expanded.
