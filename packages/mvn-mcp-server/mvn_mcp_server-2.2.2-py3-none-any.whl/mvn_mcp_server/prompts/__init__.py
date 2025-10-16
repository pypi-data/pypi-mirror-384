# Maven MCP Server Prompts
"""
Interactive conversation starters and guided workflows for Maven dependency management.

This module provides structured prompts that help AI assistants guide users through
complex Maven dependency management workflows, following enterprise patterns.
"""

from .list_mcp_assets import list_mcp_assets
from .triage import dependency_triage
from .plan import update_plan

__all__ = ["list_mcp_assets", "dependency_triage", "update_plan"]
