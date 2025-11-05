"""
MCP Client
Client for calling MCP Server tools via HTTP/JSON-RPC protocol.
"""

import os
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP Client for calling tools hosted in the MCP Server.
    
    This client implements the MCP protocol for tool invocation:
    - HTTP transport
    - JSON-RPC style requests
    - Automatic retry with exponential backoff
    - Connection pooling
    """
    
    def __init__(self, server_url: str = None, timeout: float = 30.0):
        """
        Initialize MCP client.
        
        Args:
            server_url: MCP server URL (default: from environment)
            timeout: Request timeout in seconds
        """
        self.server_url = server_url or os.getenv(
            "MCP_SERVER_URL",
            "http://mcp_server:8001"
        )
        self.timeout = timeout
        
        # Create HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.server_url,
            timeout=timeout,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )
        
        logger.info(f"MCP Client initialized: {self.server_url}")
    
    async def list_tools(self) -> Dict[str, Any]:
        """
        List all available tools in the MCP server.
        
        Returns:
            Dictionary with 'tools' key containing list of tool info
        """
        try:
            response = await self.client.get("/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            raise
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information including schemas
        """
        try:
            response = await self.client.get(f"/tools/{tool_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get tool info for '{tool_name}': {e}")
            raise
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            retry_count: Number of retry attempts
            
        Returns:
            Tool execution result
            
        Raises:
            MCPToolError: If tool execution fails
        """
        last_error = None
        
        for attempt in range(retry_count):
            try:
                response = await self.client.post(
                    "/tools/call",
                    json={
                        "tool": tool_name,
                        "parameters": parameters
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("success", False):
                    error_msg = result.get("error", "Unknown error")
                    raise MCPToolError(
                        f"Tool '{tool_name}' failed: {error_msg}",
                        tool_name=tool_name,
                        parameters=parameters,
                        error=error_msg
                    )
                
                logger.info(f"MCP tool '{tool_name}' executed successfully")
                return result.get("result", {})
            
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 404:
                    raise MCPToolError(
                        f"Tool '{tool_name}' not found",
                        tool_name=tool_name,
                        parameters=parameters,
                        error=str(e)
                    )
                logger.warning(
                    f"MCP tool call failed (attempt {attempt + 1}/{retry_count}): {e}"
                )
            
            except Exception as e:
                last_error = e
                logger.warning(
                    f"MCP tool call failed (attempt {attempt + 1}/{retry_count}): {e}"
                )
        
        # All retries failed
        raise MCPToolError(
            f"Tool '{tool_name}' failed after {retry_count} attempts",
            tool_name=tool_name,
            parameters=parameters,
            error=str(last_error)
        )
    
    async def fetch_evidence(
        self,
        sources: list,
        project_id: int,
        created_by: int
    ) -> Dict[str, Any]:
        """
        Convenience method to call fetch_evidence tool.
        
        Args:
            sources: List of evidence sources
            project_id: Project ID
            created_by: User ID
            
        Returns:
            Evidence fetcher result
        """
        return await self.call_tool(
            "fetch_evidence",
            {
                "sources": sources,
                "project_id": project_id,
                "created_by": created_by
            }
        )
    
    async def analyze_compliance(
        self,
        project_id: int,
        framework: str = "IM8",
        include_evidence: bool = True,
        generate_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Convenience method to call analyze_compliance tool.
        
        Args:
            project_id: Project ID to analyze
            framework: Framework (IM8, ISO27001, NIST)
            include_evidence: Include evidence analysis
            generate_recommendations: Generate AI recommendations
            
        Returns:
            Compliance analysis result
        """
        return await self.call_tool(
            "analyze_compliance",
            {
                "project_id": project_id,
                "framework": framework,
                "include_evidence": include_evidence,
                "generate_recommendations": generate_recommendations
            }
        )
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class MCPToolError(Exception):
    """Exception raised when an MCP tool execution fails"""
    
    def __init__(
        self,
        message: str,
        tool_name: str = None,
        parameters: Dict[str, Any] = None,
        error: str = None
    ):
        super().__init__(message)
        self.tool_name = tool_name
        self.parameters = parameters
        self.error = error


# Singleton instance
mcp_client = MCPClient()
