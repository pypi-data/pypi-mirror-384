"""Response formatting service for mvn MCP Server.

This module provides standardized functions for formatting tool responses
and error messages to ensure consistent API behavior.
"""

import logging
from typing import Dict, Any, Optional

from mvn_mcp_server.shared.data_types import ErrorCode

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


def format_success_response(tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Format a standardized success response.

    Args:
        tool_name: The name of the tool generating the response
        data: The response data to include

    Returns:
        A standardized response dictionary
    """
    response = {"tool_name": tool_name, "status": "success", "result": data}

    logger.debug(f"Formatted success response for {tool_name}: {data}")
    return response


def format_error_response(
    tool_name: str,
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Format a standardized error response.

    Args:
        tool_name: The name of the tool generating the error
        error_code: The error code enum value
        message: Human-readable error message
        details: Optional additional details about the error

    Returns:
        A standardized error response dictionary
    """
    response = {
        "tool_name": tool_name,
        "status": "error",
        "error": {
            "code": error_code.value if hasattr(error_code, "value") else error_code,
            "message": message,
        },
    }

    if details:
        response["error"]["details"] = details

    logger.debug(f"Formatted error response for {tool_name}: {error_code} - {message}")
    return response
