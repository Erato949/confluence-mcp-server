import os
from fastapi import FastAPI, HTTPException, Body, APIRouter
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from atlassian import Confluence
from pydantic import ValidationError

# Import schemas from the mcp_actions package
from .mcp_actions.schemas import (
    MCPToolSchema,
    MCPListToolsResponse,
    MCPExecuteRequest,
    MCPExecuteResponse,
    GetSpacesInput,
    GetSpacesOutput,
    GetPageInput, 
    GetPageOutput 
)
# Import tool logic
from .mcp_actions.space_actions import get_spaces_logic
from .mcp_actions.page_actions import get_page_logic 

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
AVAILABLE_TOOLS: Dict[str, MCPToolSchema] = {}

# --- Helper function to load tool definitions ---
def load_tools():
    """
    Loads and registers tool definitions.
    """
    # Define and register the get_spaces tool
    get_spaces_tool_definition = MCPToolSchema(
        name="get_spaces",
        description="Retrieves a list of spaces from Confluence. Allows optional filtering by space type, and pagination using limit and start.",
        input_schema=GetSpacesInput.model_json_schema(),  
        output_schema=GetSpacesOutput.model_json_schema() 
    )
    AVAILABLE_TOOLS[get_spaces_tool_definition.name] = get_spaces_tool_definition

    # Define and register the Get_Page tool
    get_page_tool_definition = MCPToolSchema(
        name="Get_Page", 
        description="Retrieves a specific page from Confluence by its ID. Allows optional expansion of page details like content and version.",
        input_schema=GetPageInput.model_json_schema(),
        output_schema=GetPageOutput.model_json_schema()
    )
    AVAILABLE_TOOLS[get_page_tool_definition.name] = get_page_tool_definition

# Call load_tools at startup to populate AVAILABLE_TOOLS
load_tools()


# --- API Endpoints ---
router = APIRouter()

@app.get("/health", status_code=200)
async def health_check():
    client_status = "initialized" if confluence_client else "not_initialized"
    return {"status": "ok", "message": "Confluence MCP Server is running", "confluence_client_status": client_status}

@router.post("/execute", response_model=MCPExecuteResponse, response_model_exclude_none=True)
async def execute_tool_endpoint(request: MCPExecuteRequest = Body(...)):
    client: Confluence
    tool_name = request.tool_name
    inputs = request.inputs or {}

    if tool_name not in AVAILABLE_TOOLS:
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message=f"Tool '{tool_name}' is not recognized or not available.",
            error_type="ToolNotFoundError"
        ).model_dump(exclude_none=True)
        return JSONResponse(content=error_payload, status_code=404)

    try:
        client = get_confluence_client()

        if tool_name == "get_spaces":
            try:
                parsed_inputs = GetSpacesInput(**inputs)
            except ValidationError as e:
                error_payload = MCPExecuteResponse(
                    tool_name=tool_name,
                    status="error",
                    error_message=f"Input validation failed for tool '{tool_name}': {str(e)}",
                    error_type="InputValidationError"
                ).model_dump(exclude_none=True)
                return JSONResponse(content=error_payload, status_code=422)

            tool_output_model = get_spaces_logic(client=client, inputs=parsed_inputs)
            response_object = MCPExecuteResponse(
                tool_name=tool_name,
                status="success",
                outputs=tool_output_model.model_dump(exclude_none=True) # Ensure dict and exclude Nones
            )
            print(f"DEBUG MAIN: Returning MCPExecuteResponse object directly for get_spaces. Model before FastAPI processing: {response_object.model_dump_json(indent=2, exclude_none=False)}")
            return response_object
        
        elif tool_name == "Get_Page": 
            try:
                parsed_inputs = GetPageInput(**inputs)
            except ValidationError as e:
                error_payload = MCPExecuteResponse(
                    tool_name=tool_name,
                    status="error",
                    error_message=f"Input validation failed for tool '{tool_name}': {str(e)}",
                    error_type="InputValidationError"
                ).model_dump(exclude_none=True)
                return JSONResponse(content=error_payload, status_code=422)
            
            try:
                tool_output_model = get_page_logic(client=client, inputs=parsed_inputs)
                response_object = MCPExecuteResponse(
                    tool_name=tool_name,
                    status="success",
                    outputs=tool_output_model.model_dump(exclude_none=False) # Keep exclude_none=False as per original intent for Get_Page
                )
                print(f"DEBUG MAIN: Returning MCPExecuteResponse object directly for Get_Page. Model before FastAPI processing: {response_object.model_dump_json(indent=2, exclude_none=False)}")
                return response_object
            except HTTPException as http_exc: 
                print(f"DEBUG MAIN: HTTPException caught for Get_Page: {http_exc.status_code} - {http_exc.detail}")
                error_payload = MCPExecuteResponse(
                    tool_name=tool_name,
                    status="error",
                    error_message=str(http_exc.detail),
                    error_type=type(http_exc).__name__ 
                ).model_dump(exclude_none=True)
                return JSONResponse(content=error_payload, status_code=http_exc.status_code)
            except Exception as e: 
                print(f"DEBUG MAIN: Generic Exception caught for Get_Page: {type(e).__name__} - {str(e)}")
                import traceback
                print(traceback.format_exc())
                error_payload = MCPExecuteResponse(
                    tool_name=tool_name,
                    status="error",
                    error_message=f"An unexpected error occurred in tool '{tool_name}': {str(e)}",
                    error_type="ToolLogicError"
                ).model_dump(exclude_none=True)
                return JSONResponse(content=error_payload, status_code=500)

        else:
            # This case handles tools that are in AVAILABLE_TOOLS but not explicitly in the if/elif chain.
            # For robust error handling, this path should also return a JSONResponse with a proper status code.
            error_payload = MCPExecuteResponse(
                tool_name=tool_name,
                status="error",
                error_message=f"Execution logic for tool '{tool_name}' is not implemented in the /execute endpoint.",
                error_type="NotImplementedError"
            ).model_dump(exclude_none=True)
            return JSONResponse(content=error_payload, status_code=501) # 501 Not Implemented

    except HTTPException as http_exc:
        # Handles errors from get_confluence_client() or other top-level HTTPExceptions before tool logic
        print(f"DEBUG MAIN: Outer HTTPException caught: {http_exc.status_code} - {http_exc.detail}")
        error_payload = MCPExecuteResponse(
            tool_name=tool_name, 
            status="error",
            error_message=str(http_exc.detail), 
            # Attempt to classify error based on status code, or use a generic type
            error_type="ServiceConfigurationError" if http_exc.status_code == 503 else type(http_exc).__name__
        ).model_dump(exclude_none=True)
        return JSONResponse(content=error_payload, status_code=http_exc.status_code)
    except Exception as e:
        # Catch-all for other unexpected errors during tool dispatch or pre-tool-logic phase
        print(f"DEBUG MAIN: Outer Generic Exception caught: {type(e).__name__} - {str(e)}")
        import traceback
        print(traceback.format_exc())
        error_payload = MCPExecuteResponse(
            tool_name=tool_name,
            status="error",
            error_message=f"An unexpected server error occurred while preparing to execute tool '{tool_name}'.",
            error_type="ServerError"
        ).model_dump(exclude_none=True)
        return JSONResponse(content=error_payload, status_code=500)

app.include_router(router)

# --- Main entry point for Uvicorn (if running directly) ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 
