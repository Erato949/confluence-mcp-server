from pydantic import BaseModel, Field
from mcp import Tool # Assuming Tool class might be needed, or for type hints
from mcp.server.fastmcp import Context # For type hinting context provided by FastMCP

# To use the @mcp_server_instance.tool() decorator, we need access to mcp_server_instance.
# This typically means mcp_server_instance should be defined in a way that's importable,
# e.g., in main.py or an app initialization file.
# For now, let's assume we can import it from main.
# If main.py isn't structured to allow mcp_server_instance to be imported without side effects
# (like starting a server if __name__ == "__main__"), this might need adjustment.
from confluence_mcp_server.main import mcp_server_instance 

# --- Echo Tool Schemas ---
class EchoInput(BaseModel):
    message: str = Field(..., description="The message to echo back.")

class EchoOutput(BaseModel):
    reply: str = Field(..., description="The echoed message.")

# --- Echo Tool Implementation ---
@mcp_server_instance.tool(
    name="echo_message",
    description="A simple tool that echoes back the provided message."
    # input_schema and output_schema will be inferred from type hints
)
async def echo_message_tool(context: Context, inputs: EchoInput) -> EchoOutput:
    """
    Echoes back the message provided in the input.
    """
    # 'context' can be used to access server-wide resources or settings if needed.
    # For this simple tool, we don't use it.
    return EchoOutput(reply=f"Echo: {inputs.message}")

# To make sure FastMCP scans this module, it needs to be imported somewhere,
# or FastMCP needs to be configured to scan the 'confluence_mcp_server.mcp_actions' package.
# Often, just having the @tool decorator is enough if FastMCP's package scanning is active.
