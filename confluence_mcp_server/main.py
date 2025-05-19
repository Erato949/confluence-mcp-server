import os
import logging
from dotenv import load_dotenv
import types

# FastAPI imports
from fastapi import FastAPI, Request # Added Request for app.state access (though not strictly needed for app.state)
from starlette.applications import Starlette 

# MCP and FastMCP imports
from mcp.server.fastmcp import FastMCP, Context # Reverted to use FastMCP from package __init__
from mcp.types import Tool # Changed from ToolSpec, Source, MessagesInput, MessagesOutput

from contextlib import asynccontextmanager
from functools import partial
# from starlette.applications import Starlette # Redundant import
from typing import AsyncGenerator, Optional

# Local project imports
from confluence_mcp_server.utils.logging_config import setup_logging

# Load environment variables FIRST
load_dotenv()

# Configure logging
setup_logging(logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Confluence MCP Server starting up...")

@asynccontextmanager
async def actual_root_app_lifespan(app: FastAPI): # app is root_app
    print("--- DEBUG PRINT: Entering actual_root_app_lifespan (startup) ---", flush=True)
    logger.info("Actual Root App Lifespan: Startup sequence initiated.")
    
    global tool_manager # Ensure tool_manager is accessible
    # tool_manager should have been initialized and populated by lines ~120-148
    if tool_manager is None:
        print("--- DEBUG PRINT: CRITICAL - tool_manager is None in lifespan. This indicates an initialization order problem. ---", flush=True)
        logger.critical("tool_manager is None within actual_root_app_lifespan. Aborting lifespan setup for MCP.")
        # If tool_manager is critical and not set, we might not want to proceed with MCP part
        yield # Allow root_app to proceed without MCP if tool_manager is missing
        print("--- DEBUG PRINT: Exiting actual_root_app_lifespan (shutdown) due to missing tool_manager. ---", flush=True)
        return

    print(f"--- DEBUG PRINT: Using tool_manager: {type(tool_manager)} in lifespan. Tools: {len(tool_manager._tools) if hasattr(tool_manager, '_tools') and tool_manager._tools else 'None'}", flush=True)

    local_mcp_server_instance = FastMCP(
        title="Confluence MCP Server - via FastMCP",
        description="MCP server using FastMCP and its streamable_http_app transport.",
        version="0.1.0",
        tool_manager=tool_manager, 
        context_model=Context,
        logger=logger, # Pass the main logger
    )
    
    global mcp_server_instance # Allows mcp_server_instance to be potentially inspected, though its primary role is reduced
    mcp_server_instance = local_mcp_server_instance
    print(f"--- DEBUG PRINT: local_mcp_server_instance ({type(local_mcp_server_instance)}) created in lifespan and assigned to global mcp_server_instance. ---", flush=True)
    
    # Get the transport app from FastMCP
    # The streamable_http_app() method seems to return a Starlette app directly in this version.
    # It might be an async method or a regular method.
    
    returned_item = local_mcp_server_instance.streamable_http_app()
    print(f"--- DEBUG PRINT: local_mcp_server_instance.streamable_http_app() returned: {type(returned_item)} ---", flush=True)

    transport_app_for_state = None
    if hasattr(returned_item, '__await__'): # Check if it's a coroutine
        print("--- DEBUG PRINT: streamable_http_app() result is awaitable. Awaiting it. ---", flush=True)
        transport_app_for_state = await returned_item
    else: # If not awaitable, assume it's the app instance directly
        print("--- DEBUG PRINT: streamable_http_app() result is NOT awaitable. Using as is. ---", flush=True)
        transport_app_for_state = returned_item

    print(f"--- DEBUG PRINT: Final transport app to assign to state is: {type(transport_app_for_state)} ---", flush=True)
    
    # Check if we actually got a Starlette app before trying to use it.
    if transport_app_for_state.__class__.__name__ == 'Starlette':
        app.state.mcp_app_to_mount = transport_app_for_state
        logger.info(f"MCP transport app ({type(app.state.mcp_app_to_mount)}) obtained and set to app.state.mcp_app_to_mount.")
    else:
        logger.error(f"FastMCP.streamable_http_app() did not return a Starlette app. Got: {type(transport_app_for_state)}. MCP server cannot be mounted.")
        app.state.mcp_app_to_mount = None # Ensure it's None if not a Starlette app

    # --- MOUNTING LOGIC MOVED FROM STARTUP EVENT HANDLER ---
    print("--- DEBUG PRINT: Lifespan: Attempting to mount MCP app. ---", flush=True)
    logger.info("Lifespan: Attempting to mount MCP app.")
    # Check if mcp_app_to_mount was set by the lifespan function
    if hasattr(app.state, 'mcp_app_to_mount') and app.state.mcp_app_to_mount is not None:
        mcp_app_resolved = app.state.mcp_app_to_mount
        print(f"--- DEBUG PRINT: Lifespan: Mounting mcp_app ({type(mcp_app_resolved)}) to app at /mcp_server. ---", flush=True)
        # The name argument for mount is important if you ever need to refer to this mount, e.g., for unmounting or routing.
        app.mount("/mcp_server", mcp_app_resolved, name="mcp_server_transport") # Using 'app' here
        logger.info(f"Lifespan: MCP app ({type(mcp_app_resolved).__name__}) mounted at /mcp_server.")
        
        # Diagnostic print of routes after mount
        route_info = []
        print("--------------------------------------------------")
        print("DIAGNOSTIC: Routes in app (after MCP app mount in lifespan)")
        for route in app.routes: # Using 'app' here
            if hasattr(route, "path"):
                path = route.path
                name = route.name if hasattr(route, "name") else "N/A"
                methods = route.methods if hasattr(route, "methods") else "N/A"
                route_info.append(f"  Path: {path}, Name: {name}, Methods: {methods}")
            elif isinstance(route, Mount):
                mount_path = route.path
                mounted_app_type = type(route.app).__name__
                route_info.append(f"  Mount Path: {mount_path}, App: {mounted_app_type}")
        print("\n".join(route_info))
        print("--------------------------------------------------", flush=True)
    else:
        print("--- DEBUG PRINT: Lifespan: No mcp_app_to_mount available in app.state. MCP server not mounted. ---", flush=True)
        logger.error("Lifespan: No app found in app.state.mcp_app_to_mount. MCP server not mounted.")
    # --- END OF MOVED MOUNTING LOGIC ---

    if mcp_server_instance and mcp_server_instance._session_manager:
        logger.info("--- DEBUG PRINT: Entering session_manager.run() context to make application operational ---")
        async with mcp_server_instance._session_manager.run():
            # The MCP app (if any) should have already been mounted from app.state before this block.
            # No need to check a local mcp_app_to_mount or re-mount here.
            logger.info("--- DEBUG PRINT: About to yield in actual_root_app_lifespan (operational phase) INSIDE session_manager.run() ---")
            yield  # Application is operational
            logger.info("--- DEBUG PRINT: Returned from yield in actual_root_app_lifespan (shutdown phase) INSIDE session_manager.run() ---")
            # Shutdown logic related to session_manager is handled by its own context exit
    else:
        # Fallback if session_manager isn't available or mcp_server_instance is None
        logger.warning("Lifespan: MCP server instance or its session manager not available for session_manager.run() context. Proceeding without it.")
        logger.info("--- DEBUG PRINT: About to yield in actual_root_app_lifespan (operational phase) - FALLBACK PATH (no session_manager context) ---")
        yield # Application is operational (potentially with issues if session_manager was critical for the mounted app)
        logger.info("--- DEBUG PRINT: Returned from yield in actual_root_app_lifespan (shutdown phase) - FALLBACK PATH (no session_manager context) ---")

    # General shutdown logic here (outside session_manager.run if it was used)
    logger.info("Lifespan: Shutdown sequence initiated.")
    if mcp_server_instance and hasattr(mcp_server_instance, 'close') and callable(mcp_server_instance.close):
        # Assuming close is an async method if it exists; typical for server resources
        # Check if it's an async function if unsure
        # For now, let's assume it could be sync or async, or may not exist for FastMCP
        # FastMCP itself doesn't define a close(), but its underlying MCPServer might, or transports.
        # The session_manager.run() handles its own cleanup.
        logger.info("Lifespan: mcp_server_instance specific close() if any, would be called here if needed.") 
    if hasattr(app.state, 'mcp_app_to_mount') and app.state.mcp_app_to_mount is not None:
        logger.info(f"Root app has resumed from yield. MCP transport app ({type(app.state.mcp_app_to_mount)}) was active.")
    else:
        logger.info("Root app has resumed from yield. No MCP transport app was active or set in app.state.")

    app.state.mcp_app_to_mount = None # Clear the reference after the context has exited
    mcp_server_instance = None # Clear the global instance as well
    logger.info("Actual Root App Lifespan: Shutdown sequence completed.")
    print("--- DEBUG PRINT: Exiting actual_root_app_lifespan (shutdown) ---", flush=True)

# Create the main FastAPI app (root app)
root_app = FastAPI(
    title="Confluence MCP Server - Root",
    description="Main FastAPI application hosting health checks and MCP server.",
    version="0.1.0",
    lifespan=actual_root_app_lifespan
)



# Initialize mcp_app_to_mount on app.state so it's available when lifespan runs
root_app.state.mcp_app_to_mount = None 
print("--- DEBUG PRINT: root_app created, root_app.state.mcp_app_to_mount initialized to None. ---", flush=True)

# --- Health Check Endpoint on Root App ---
@root_app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# --- Tool Definitions (Example) ---
# mcp.types should provide ToolSpec, Source, MessagesInput, MessagesOutput
from pydantic import BaseModel, Field

class AddInput(BaseModel):
    x: int = Field(..., description="First number")
    y: int = Field(..., description="Second number")

class AddOutput(BaseModel):
    result: int = Field(..., description="Sum of x and y")

async def add_logic(context: Context, inputs: AddInput) -> AddOutput:
    print(f"--- DEBUG PRINT: add_logic called with inputs: {inputs} ---", flush=True)
    logger.info(f"Executing 'add_logic' with x={inputs.x}, y={inputs.y}")
    result = inputs.x + inputs.y
    return AddOutput(result=result)

AVAILABLE_TOOLS = {
    "Add": {
        "tool_spec": Tool(
            name="Add",
            description="Adds two numbers.",
            # source=Source(module=__name__, function_name="add_logic"), # 'source' not in mcp.types.Tool
            inputSchema=AddInput.model_json_schema(), # Using model_json_schema()
            responseSchema=AddOutput.model_json_schema(), # Using model_json_schema()
        ),
        "logic": add_logic,
    },
}

class ToolManager:
    def __init__(self, available_tools):
        self._tools = available_tools
        print(f"--- DEBUG PRINT: ToolManager initialized with tools: {list(self._tools.keys())} ---", flush=True)
        logger.info(f"ToolManager initialized with tools: {list(self._tools.keys())}")

    def get_tool_spec(self, tool_name: str) -> Tool: # Changed return type to Tool
        print(f"--- DEBUG PRINT: ToolManager.get_tool_spec called for: {tool_name} ---", flush=True)
        if tool_name not in self._tools:
            logger.error(f"Tool '{tool_name}' not found in ToolManager.")
            raise ValueError(f"Tool '{tool_name}' not found")
        spec = self._tools[tool_name]["tool_spec"]
        logger.debug(f"Retrieved spec for tool '{tool_name}': {spec.name}")
        return spec

    def get_tool_logic(self, tool_name: str):
        print(f"--- DEBUG PRINT: ToolManager.get_tool_logic called for: {tool_name} ---", flush=True)
        if tool_name not in self._tools:
            logger.error(f"Tool logic for '{tool_name}' not found in ToolManager.")
            raise ValueError(f"Tool logic for '{tool_name}' not found")
        logic = self._tools[tool_name]["logic"]
        logger.debug(f"Retrieved logic for tool '{tool_name}': {getattr(logic, '__name__', type(logic).__name__)}")
        return logic

    def list_tools(self) -> list[Tool]: # Changed return type to list[Tool]
        print("--- DEBUG PRINT: ToolManager.list_tools called ---", flush=True)
        specs = [data["tool_spec"] for data in self._tools.values()]
        logger.info(f"Listing available tools: {len(specs)} found.")
        return specs

tool_manager = ToolManager(AVAILABLE_TOOLS)

# --- FastMCP Server Instance Creation ---
fastapi_for_mcp = FastAPI(
    title="Confluence MCP Server - Tools Sub-App",
    description="FastAPI app for MCP tools, managed by FastMCP.",
    # Lifespan for this app (if any) should be set up by FastMCP internally if it needs one
    # for managing its own tool routes or other internal state. We are not setting it here.
)
print(f"--- DEBUG PRINT: fastapi_for_mcp instance created: {type(fastapi_for_mcp)} ---", flush=True)

# json_rpc_transport_factory and StreamableHttpTransport are no longer needed as
# FastMCP.from_fastapi will use its default streamable_http_app transport.

mcp_server_instance: Optional[FastMCP] = None # Reverted to FastMCP type hint
# app_to_mount is now handled via root_app.state


# Diagnostic print: Inspect routes
print("-" * 50)
print("DIAGNOSTIC: Routes in root_app (after potential mount)")
for route in root_app.routes:
    route_path = getattr(route, 'path', 'N/A')
    route_name = getattr(route, 'name', 'N/A')
    route_methods = getattr(route, 'methods', 'N/A') if hasattr(route, 'methods') else 'N/A (Mount)'
    print(f"  Path: {route_path}, Name: {route_name}, Methods: {route_methods}")
    if hasattr(route, 'app') and hasattr(route.app, 'routes') and route_path == '/mcp_server':
        print(f"    Inspecting routes for Mount at {route_path}:")
        for sub_route in route.app.routes:
             sub_route_path = getattr(sub_route, 'path', 'N/A')
             sub_route_name = getattr(sub_route, 'name', 'N/A')
             sub_route_methods = getattr(sub_route, 'methods', 'N/A') if hasattr(sub_route, 'methods') else 'N/A (Sub-Mount)'
             print(f"      Sub-Path: {sub_route_path}, Sub-Name: {sub_route_name}, Sub-Methods: {sub_route_methods}")
print("-" * 50)

app = root_app

if __name__ == "__main__":
    import uvicorn
    APP_PORT = int(os.getenv("PORT", "8000"))
    APP_HOST = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting Uvicorn to serve 'root_app' on {APP_HOST}:{APP_PORT}")
    logger.info("MCP server with tools and JSON-RPC transport should be at /mcp_server")
    uvicorn.run("confluence_mcp_server.main:app", host=APP_HOST, port=APP_PORT, reload=True) # Ensure Uvicorn runs the 'app' from this module
