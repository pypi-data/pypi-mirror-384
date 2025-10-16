"""mvn MCP Server main entry point.

This module serves as the primary entry point for the mvn MCP Server.
"""

import sys
import os
from mvn_mcp_server.server import mcp
from mvn_mcp_server.shared.logging import get_logger
from mvn_mcp_server import __version__

# Initialize logger
logger = get_logger(__name__)


def main():
    """Start the mvn MCP Server."""
    # Handle version flag
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(f"Maven MCP Server version {__version__}")
        return 0

    # Log startup
    logger.info(
        "Starting Maven MCP Server",
        extra={
            "extra_fields": {
                "version": __version__,
                "python_version": sys.version.split()[0],
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
            }
        },
    )

    try:
        # Run the FastMCP server
        mcp.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        return 0
    except Exception as e:
        logger.exception(
            "Fatal error during server operation",
            extra={"extra_fields": {"error": str(e)}},
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
