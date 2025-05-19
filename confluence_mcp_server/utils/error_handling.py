# confluence_mcp_server/utils/error_handling.py
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Standard MCP Error Codes (subset for example)
# See MCP specification for a more complete list if needed.
MCP_ERROR_CODE_INTERNAL = -32603
MCP_ERROR_CODE_INVALID_PARAMS = -32602
MCP_ERROR_CODE_METHOD_NOT_FOUND = -32601
MCP_ERROR_CODE_SERVER_ERROR_START = -32000
MCP_ERROR_CODE_SERVER_ERROR_END = -32099 # Not official, but a common range

# Custom error codes for tool-specific issues (within server error range)
TOOL_ERROR_UPSTREAM_API = -32001
TOOL_ERROR_VALIDATION = -32002
TOOL_ERROR_NOT_FOUND = -32003 # Example for resource not found
TOOL_ERROR_EXECUTION = -32004 # Generic tool execution error


class MCPError(Exception):
    """Base class for all MCP-related errors."""
    def __init__(self, message: str, code: int, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data if data is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        error_dict = {
            "message": self.message,
            "code": self.code,
        }
        if self.data:
            error_dict["data"] = self.data
        return error_dict

    def __str__(self) -> str:
        return f"MCPError(code={self.code}, message='{self.message}', data={self.data})"


class MCPToolError(MCPError):
    """Base class for errors specific to tool execution within the MCP server."""
    def __init__(self, message: str, code: int = TOOL_ERROR_EXECUTION, data: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, data)


class MCPInputValidationError(MCPToolError):
    """Error for invalid input parameters provided to a tool."""
    def __init__(self, message: str = "Invalid input parameters.", validation_details: Optional[List[Dict[str, Any]]] = None):
        data = {}
        if validation_details:
            data["validation_details"] = validation_details
        # FastMCP expects code -32602 for invalid params generally
        # but for more detailed validation, a tool-specific code might be used
        # For now, let's use a generic tool validation error.
        super().__init__(message, code=TOOL_ERROR_VALIDATION, data=data)


class MCPUpstreamAPIError(MCPToolError):
    """Error for issues encountered when interacting with an upstream API (e.g., Confluence)."""
    def __init__(self, message: str = "Error interacting with upstream API.", upstream_status_code: Optional[int] = None, upstream_message: Optional[str] = None):
        data = {}
        if upstream_status_code is not None:
            data["upstream_status_code"] = upstream_status_code
        if upstream_message:
            data["upstream_message"] = upstream_message
        super().__init__(message, code=TOOL_ERROR_UPSTREAM_API, data=data)


class MCPNotFoundError(MCPToolError):
    """Error for when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, code=TOOL_ERROR_NOT_FOUND)


# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        raise MCPInputValidationError(validation_details=[{"loc": ["field"], "msg": "is required", "type": "missing"}])
    except MCPError as e:
        logger.error(f"Caught MCPError: {e.to_dict()}")

    try:
        raise MCPUpstreamAPIError(upstream_status_code=503, upstream_message="Service unavailable")
    except MCPError as e:
        logger.error(f"Caught MCPError: {e.to_dict()}")

    try:
        raise MCPNotFoundError(message="The specific page you requested could not be found.")
    except MCPError as e:
        logger.error(f"Caught MCPError: {e.to_dict()}")
        
    try:
        raise MCPToolError(message="A generic tool failure occurred.")
    except MCPError as e:
        logger.error(f"Caught MCPError: {e.to_dict()}")

