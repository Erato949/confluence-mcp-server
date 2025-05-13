import os
from fastapi import FastAPI, HTTPException, Body, APIRouter
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Union
from atlassian import Confluence
from pydantic import ValidationError
from pydantic_core import ErrorDetails
import json
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Import schemas from the mcp_actions package
from .mcp_actions.schemas import (
    MCPToolSchema,
    MCPListToolsResponse,
    MCPExecuteRequest,
    MCPExecuteResponse,
    GetSpacesInput,
    GetSpacesOutput,
    GetPageInput, 
    GetPageOutput,
    SearchPagesInput,
    SearchPagesOutput,
    CreatePageInput,
    CreatePageOutput,
    UpdatePageInput, 
    UpdatePageOutput, 
)
# Import tool logic
from .mcp_actions.space_actions import get_spaces_logic
from .mcp_actions.page_actions import get_page_logic, search_pages_logic, create_page_logic, update_page_logic

# Load environment variables from .env file
load_dotenv()

# --- Confluence Client Initialization ---
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_KEY = os.getenv("CONFLUENCE_API_KEY")

confluence_client: Optional[Confluence] = None

if CONFLUENCE_URL and CONFLUENCE_USERNAME and CONFLUENCE_API_KEY:
    try:
        confluence_client = Confluence(
            url=CONFLUENCE_URL,
            username=CONFLUENCE_USERNAME,
            password=CONFLUENCE_API_KEY, 
            cloud=True 
        )
        print("Successfully initialized Confluence client.")

        # --- Test Confluence Connection ---
        try:
            print(f"Attempting a basic API call to Confluence (listing 1 space)...")
            # Use get_all_spaces(limit=1) as a basic connectivity test
            spaces = confluence_client.get_all_spaces(limit=1)
            
            if spaces is not None: # Check if the call returned something (even an empty list for 'results' is a success)
                # The structure of `spaces` is typically a dict with a 'results' list.
                # We are just checking if the API call itself succeeded without an auth error.
                print(f"Successfully connected to Confluence and performed a basic API call.")
                # You can inspect `spaces` if needed: print(f"Spaces data: {spaces}")
            else:
                # This case might indicate an issue if get_all_spaces returns None on error,
                # though it usually raises an exception for auth/connection errors.
                print(f"Basic Confluence API call (get_all_spaces) returned None. Check permissions or instance status.")

        except Exception as conn_test_e:
            print(f"Confluence client initialized, but basic connection test (get_all_spaces) failed: {conn_test_e}")
            # This is where we'd likely catch authentication or network errors.
            print("Please check your Confluence URL, credentials, API key permissions (e.g., view spaces), and network connectivity.")
            # Depending on desired behavior, you might set confluence_client to None here if a successful test is mandatory.
            # confluence_client = None 
            
    except Exception as e:
        print(f"Error initializing Confluence client: {e}")
        confluence_client = None
else:
    print("Confluence credentials not found in environment variables. Confluence client not initialized.")

def get_confluence_client() -> Confluence:
    """
    Returns the initialized Confluence client.
    Raises an HTTPException if the client is not available.
    """
    if confluence_client is None:
        raise HTTPException(
            status_code=503, 
            detail="Confluence client is not initialized. Check server configuration and .env file."
        )
    return confluence_client

# Initialize FastAPI app
app = FastAPI(
    title="Confluence MCP Server",
    description="A local MCP server for interacting with Confluence.",
    version="0.1.0"
)

# --- In-memory store for tool definitions ---
AVAILABLE_TOOLS: Dict[str, Dict[str, Any]] = {}

# --- Helper function to load tool definitions ---
def load_tools():
    """
    Loads and registers tool definitions.
    """
    # Define and register the get_spaces tool
    AVAILABLE_TOOLS['get_spaces'] = {
        "description": "Retrieves a list of spaces from Confluence. Allows optional filtering by space type, and pagination using limit and start.",
        "input_schema": GetSpacesInput,
        "output_schema": GetSpacesOutput,
        "logic": get_spaces_logic
    }

    # Get Page Tool Definition
    AVAILABLE_TOOLS['Get_Page'] = {
        "description": "Fetches a specific page by ID or by space key and title.",
        "input_schema": GetPageInput,
        "output_schema": GetPageOutput,
        "logic": get_page_logic  # Reference the logic function
    }

    # Search Pages Tool Definition
    AVAILABLE_TOOLS['search_pages'] = {
        "description": "Searches for pages using Confluence Query Language (CQL) or basic filters.",
        "input_schema": SearchPagesInput,
        "output_schema": SearchPagesOutput,
        "logic": search_pages_logic
    }
    
    # Create Page Tool Definition
    AVAILABLE_TOOLS['create_page'] = {
        "description": "Creates a new page in a Confluence space.",
        "input_schema": CreatePageInput,
        "output_schema": CreatePageOutput,
        "logic": create_page_logic
    }

    # Update Page Tool Definition
    AVAILABLE_TOOLS['update_page'] = {
        "description": "Updates an existing page's title, content, or parent.",
        "input_schema": UpdatePageInput,
        "output_schema": UpdatePageOutput,
        "logic": update_page_logic
    }

    print(f"Registered tools: {list(AVAILABLE_TOOLS.keys())}")

# Call load_tools at startup to populate AVAILABLE_TOOLS
load_tools()


# --- API Endpoints ---
router = APIRouter()

@app.get("/health", status_code=200)
async def health_check():
    client_status = "initialized" if confluence_client else "not_initialized"
    return {"status": "ok", "message": "Confluence MCP Server is running", "confluence_client_status": client_status}

def make_errors_json_serializable(errors: list[ErrorDetails]) -> list[dict]:
    """Converts Pydantic's ErrorDetails list into a JSON-serializable format.

    Handles non-serializable types often found in validation contexts,
    like exception objects or complex inputs, by converting them to strings.
    """
    serializable_list = []
    if not isinstance(errors, list):
        # Handle cases where errors might not be a list as expected
        return [{'msg': 'Invalid error format received.'}]
        
    for error in errors:
        # Ensure error is a dictionary before processing
        if not isinstance(error, dict):
            serializable_list.append({'msg': f'Non-dict error item encountered: {type(error)}'})
            continue
            
        serializable_error = {} 
        for key, value in error.items():
            try:
                # Attempt a simple JSON check - this is basic but covers common cases
                json.dumps({key: value})
                serializable_error[key] = value
            except (TypeError, OverflowError):
                # If standard serialization fails, convert to string
                # Special handling for 'loc' which should be a tuple of strings/ints
                if key == 'loc' and isinstance(value, (list, tuple)):
                     serializable_error[key] = tuple(str(loc_item) for loc_item in value)
                # Convert anything else problematic to its string representation
                else:
                    serializable_error[key] = str(value)
                    
        serializable_list.append(serializable_error)
    return serializable_list

@router.post("/execute", response_model=MCPExecuteResponse, response_model_exclude_none=True)
async def execute_tool_endpoint(request: MCPExecuteRequest = Body(...)):
    tool_name = request.tool_name
    inputs = request.inputs or {}
    tool_info = AVAILABLE_TOOLS.get(tool_name)

    if not tool_info:
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message=f"Tool '{tool_name}' is not recognized or not available.",
            error_type="ToolNotFoundError"
        ).model_dump(exclude_none=False)
        return JSONResponse(content=error_payload, status_code=404)

    logic_function = tool_info.get('logic')
    input_schema_class = tool_info.get('input_schema')

    if not logic_function or not input_schema_class:
        # This case indicates an internal configuration error
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message=f"Internal configuration error for tool '{tool_name}': Missing logic or input schema.",
            error_type="ConfigurationError"
        ).model_dump(exclude_none=False)
        return JSONResponse(content=error_payload, status_code=500)

    try:
        parsed_inputs = input_schema_class.model_validate(inputs)
    except ValidationError as e:
        serializable_errors = make_errors_json_serializable(e.errors())
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message="Input validation failed.",
            error_type="InputValidationError",
            validation_details=serializable_errors # Use the sanitized errors
        ).model_dump(exclude_none=False)
        return JSONResponse(content=error_payload, status_code=422)

    try:
        client = get_confluence_client()
        tool_output_model = await logic_function(client=client, inputs=parsed_inputs)
        logger.debug(f"Logic function {logic_function.__name__} returned: {tool_output_model}")

        # Handle case where logic function returns None (e.g., resource not found)
        if tool_output_model is None:
            logger.warning(f"{logic_function.__name__} returned None, raising 404.")
            raise HTTPException(status_code=404, detail=f"{tool_name} resource not found.")

        # Prepare success response
        response = MCPExecuteResponse(
            tool_name=tool_name,
            status="success",
            outputs=tool_output_model.model_dump(exclude_none=False) 
        )
        return response

    except HTTPException as http_exc: 
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message=http_exc.detail, # Use detail directly
            error_type=type(http_exc).__name__ 
        ).model_dump(exclude_none=False)
        return JSONResponse(content=error_payload, status_code=http_exc.status_code)
    except Exception as e: 
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message=f"An unexpected error occurred in tool '{tool_name}': {str(e)}",
            error_type="ToolLogicError"
        ).model_dump(exclude_none=False)
        return JSONResponse(content=error_payload, status_code=500)

app.include_router(router)

# --- Main entry point for Uvicorn (if running directly) ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 
