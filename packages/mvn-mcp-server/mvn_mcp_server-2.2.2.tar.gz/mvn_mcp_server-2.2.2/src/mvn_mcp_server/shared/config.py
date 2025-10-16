"""Configuration management for MCP server.

Centralized configuration with environment variable support.
"""

import os
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration settings."""

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    log_format: str = Field(default="json", description="Log format (json or simple)")

    cache_ttl_metadata: int = Field(
        default=3600, description="Cache TTL for metadata in seconds"
    )

    cache_ttl_search: int = Field(
        default=900, description="Cache TTL for search results in seconds"
    )

    maven_api_timeout: int = Field(
        default=30, description="Timeout for Maven API requests in seconds"
    )

    max_retries: int = Field(
        default=3, description="Maximum retry attempts for failed requests"
    )

    enable_telemetry: bool = Field(
        default=False, description="Enable telemetry collection (future use)"
    )

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables.

        Environment variables:
            MVN_MCP_LOG_LEVEL: Logging level
            MVN_MCP_LOG_FORMAT: Log format (json or simple)
            MVN_MCP_CACHE_TTL_METADATA: Cache TTL for metadata
            MVN_MCP_CACHE_TTL_SEARCH: Cache TTL for search results
            MVN_MCP_API_TIMEOUT: Maven API timeout
            MVN_MCP_MAX_RETRIES: Maximum retry attempts
            MVN_MCP_ENABLE_TELEMETRY: Enable telemetry

        Returns:
            ServerConfig instance with values from environment
        """
        return cls(
            log_level=os.getenv("MVN_MCP_LOG_LEVEL", "INFO"),
            log_format=os.getenv("MVN_MCP_LOG_FORMAT", "json"),
            cache_ttl_metadata=int(os.getenv("MVN_MCP_CACHE_TTL_METADATA", "3600")),
            cache_ttl_search=int(os.getenv("MVN_MCP_CACHE_TTL_SEARCH", "900")),
            maven_api_timeout=int(os.getenv("MVN_MCP_API_TIMEOUT", "30")),
            max_retries=int(os.getenv("MVN_MCP_MAX_RETRIES", "3")),
            enable_telemetry=os.getenv("MVN_MCP_ENABLE_TELEMETRY", "false").lower()
            == "true",
        )


# Global configuration instance
config = ServerConfig.from_env()
