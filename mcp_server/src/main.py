"""
MCP Server - Model Context Protocol Server
Hosts tools for the QCA compliance assistant.
"""

import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Import sample data for legacy endpoints
from mcp_server.src.sample_data import SampleEvidence, SAMPLE_EVIDENCE

# Import MCP tools
from mcp_server.src.mcp_tools import EvidenceFetcherTool, ComplianceAnalyzerTool

# Get database connection from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://qca_user:qca_password@db:5432/qca_db"
)

EVIDENCE_STORAGE_PATH = os.getenv(
    "EVIDENCE_STORAGE_PATH",
    "/app/evidence_storage"
)

app = FastAPI(
    title="MCP Server",
    description="Model Context Protocol Server for QCA Tools",
    version="2.0.0"
)


# ==================== MCP Tool Registry ====================

class MCPTool:
    """MCP Tool wrapper"""
    def __init__(self, tool_instance):
        self.instance = tool_instance
        self.name = tool_instance.name
        self.description = tool_instance.description
        self.input_schema = tool_instance.input_schema
        self.output_schema = tool_instance.output_schema


class ToolRegistry:
    """Registry for MCP tools"""
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
    
    def register(self, tool_instance):
        """Register a tool"""
        tool = MCPTool(tool_instance)
        self.tools[tool.name] = tool
        return tool
    
    def get(self, name: str) -> MCPTool:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        return self.tools[name]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema
            }
            for tool in self.tools.values()
        ]


# Initialize tool registry
registry = ToolRegistry()

# Register tools
registry.register(EvidenceFetcherTool(
    db_connection_string=DATABASE_URL,
    storage_path=EVIDENCE_STORAGE_PATH
))
registry.register(ComplianceAnalyzerTool(
    db_connection_string=DATABASE_URL
))


# ==================== MCP Protocol Endpoints ====================

class ToolCallRequest(BaseModel):
    """MCP tool call request"""
    tool: str = Field(..., description="Tool name")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")


class ToolCallResponse(BaseModel):
    """MCP tool call response"""
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error: str = None


@app.get("/")
def root():
    """MCP Server status"""
    return {
        "message": "MCP Server - Model Context Protocol",
        "version": "2.0.0",
        "status": "running",
        "tools_registered": len(registry.tools)
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tools": len(registry.tools)
    }


@app.get("/tools")
def list_tools():
    """
    List all registered MCP tools.
    Returns tool names, descriptions, and schemas.
    """
    return {
        "tools": registry.list_tools()
    }


@app.get("/tools/{tool_name}")
def get_tool_info(tool_name: str):
    """
    Get information about a specific tool.
    
    Args:
        tool_name: Name of the tool
    """
    try:
        tool = registry.get(tool_name)
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """
    Call an MCP tool.
    
    This is the main MCP protocol endpoint. Agents call this to execute tools.
    
    Args:
        request: Tool call request with tool name and parameters
        
    Returns:
        Tool execution result
    """
    import logging
    from pydantic import ValidationError
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Tool call request: tool='{request.tool}', available_tools={list(registry.tools.keys())}")
        
        # Get tool from registry
        tool = registry.get(request.tool)
        
        # Execute tool
        result = await tool.instance.execute(request.parameters)
        
        return ToolCallResponse(
            success=True,
            result=result
        )
    
    except ValueError as e:
        # Tool not found in registry
        if "Tool not found" in str(e):
            logger.error(f"Tool not found: {request.tool}, available: {list(registry.tools.keys())}")
            raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool}")
        # Other ValueError
        logger.error(f"ValueError in tool execution: {e}")
        return ToolCallResponse(
            success=False,
            error=f"Invalid parameters: {str(e)}"
        )
    
    except ValidationError as e:
        # Pydantic validation error for tool parameters
        logger.error(f"Parameter validation error for tool '{request.tool}': {e}")
        return ToolCallResponse(
            success=False,
            error=f"Parameter validation failed: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return ToolCallResponse(
            success=False,
            error=str(e)
        )


# ==================== Legacy Endpoints (for backward compatibility) ====================

@app.get("/sample-evidence", response_model=List[SampleEvidence])
def get_sample_evidence():
    """Get all sample evidence items (legacy)"""
    return SAMPLE_EVIDENCE


@app.get("/sample-evidence/{evidence_id}", response_model=SampleEvidence)
def get_sample_evidence_by_id(evidence_id: int):
    """Get a specific sample evidence item by ID (legacy)"""
    for evidence in SAMPLE_EVIDENCE:
        if evidence["id"] == evidence_id:
            return evidence
    raise HTTPException(status_code=404, detail="Evidence not found")


@app.get("/sample-evidence/type/{evidence_type}", response_model=List[SampleEvidence])
def get_sample_evidence_by_type(evidence_type: str):
    """Get sample evidence items by type (legacy)"""
    filtered = [e for e in SAMPLE_EVIDENCE if e["evidence_type"] == evidence_type]
    return filtered

