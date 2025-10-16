"""Logging configuration for MCP server.

Provides structured logging with JSON output for enterprise observability.
"""

import logging
import sys
from typing import Any, Dict, Optional
import json
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              If not provided, uses LOG_LEVEL env var or defaults to INFO

    Returns:
        Configured logger instance
    """
    import os

    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Determine log level
        log_level_str = level or os.getenv("LOG_LEVEL", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logger.setLevel(log_level)

        # Create console handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(log_level)

        # Use JSON formatter for structured logging
        # Can be switched to simple format with env var
        if os.getenv("LOG_FORMAT", "json").lower() == "json":
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )

        logger.addHandler(handler)

    return logger


def log_tool_invocation(
    logger: logging.Logger,
    tool_name: str,
    parameters: Dict[str, Any],
    user_id: Optional[str] = None,
) -> None:
    """Log MCP tool invocation for audit trail.

    Args:
        logger: Logger instance
        tool_name: Name of the tool being invoked
        parameters: Tool parameters (sanitized)
        user_id: Optional user identifier
    """
    extra_fields = {
        "tool_name": tool_name,
        "parameters": parameters,
        "event_type": "tool_invocation",
    }
    if user_id:
        extra_fields["user_id"] = user_id

    logger.info(
        f"Tool invocation: {tool_name}",
        extra={"extra_fields": extra_fields},
    )
