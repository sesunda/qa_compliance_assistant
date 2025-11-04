"""
MCP Client Package
Client library for calling MCP Server tools from the FastAPI backend.
"""

from .client import MCPClient, mcp_client

__all__ = ["MCPClient", "mcp_client"]
