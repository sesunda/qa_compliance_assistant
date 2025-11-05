"""
Task handler implementations for different agent task types.

Each handler orchestrates tasks by calling MCP tools.
"""
import asyncio
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from api.src.workers.task_worker import update_progress
from api.src.mcp.client import mcp_client, MCPToolError

logger = logging.getLogger(__name__)


async def handle_test_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Test task handler for demonstration purposes.
    
    Args:
        task_id: ID of the task
        payload: Task parameters
        db: Database session
        
    Returns:
        Task result data
    """
    logger.info(f"Test task {task_id} started with payload: {payload}")
    
    # Simulate some work with progress updates
    steps = payload.get("steps", 5)
    for i in range(steps):
        await asyncio.sleep(1)
        progress = int(((i + 1) / steps) * 100)
        await update_progress(task_id, progress, f"Completed step {i+1}/{steps}")
        logger.info(f"Test task {task_id} - step {i+1}/{steps} ({progress}%)")
    
    result = {
        "status": "success",
        "message": "Test task completed successfully",
        "payload_received": payload,
        "steps_executed": steps,
        "execution_time_seconds": steps
    }
    
    logger.info(f"Test task {task_id} completed")
    return result


async def handle_fetch_evidence_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handler for fetching evidence using MCP tool.
    
    This handler orchestrates the evidence fetching by calling the
    MCP-hosted evidence_fetcher tool.
    
    Args:
        task_id: ID of the task
        payload: Should contain:
            - sources: List of evidence sources
            - project_id: Project ID
            - created_by: User ID
        db: Database session
        
    Returns:
        Result from MCP evidence fetcher tool
    """
    logger.info(f"Evidence fetch task {task_id} started - calling MCP tool")
    
    await update_progress(task_id, 10, "Preparing evidence sources...")
    
    try:
        # Extract parameters
        sources = payload.get("sources", [])
        file_path = payload.get("file_path")
        control_id = payload.get("control_id", 1)
        project_id = payload.get("project_id", 1)
        created_by = payload.get("created_by") or payload.get("current_user_id", 1)
        
        # If file_path is provided (from AI agent upload), create a source entry
        if file_path and not sources:
            sources = [{
                "type": "file",
                "location": file_path,
                "control_id": control_id or 1,
                "description": payload.get("description", "Evidence document uploaded via AI Assistant")
            }]
            logger.info(f"Created source from file_path: {file_path}")
        
        if not sources:
            return {
                "status": "error",
                "message": "No evidence sources provided",
                "evidence_ids": [],
                "total_fetched": 0
            }
        
        await update_progress(task_id, 20, f"Calling MCP tool to fetch {len(sources)} sources...")
        
        # Call MCP tool
        result = await mcp_client.fetch_evidence(
            sources=sources,
            project_id=project_id,
            created_by=created_by
        )
        
        await update_progress(
            task_id,
            90,
            f"Fetched {result.get('total_fetched', 0)} evidence items"
        )
        
        logger.info(
            f"Evidence fetch task {task_id} completed: "
            f"{result.get('total_fetched', 0)} fetched, "
            f"{result.get('total_failed', 0)} failed"
        )
        
        return {
            "status": "success" if result.get("success") else "partial",
            "message": "Evidence fetching completed via MCP",
            **result
        }
    
    except MCPToolError as e:
        logger.error(f"Evidence fetch task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"MCP tool error: {e.error}",
            "evidence_ids": [],
            "total_fetched": 0,
            "total_failed": len(payload.get("sources", []))
        }
    
    except Exception as e:
        logger.error(f"Evidence fetch task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "evidence_ids": [],
            "total_fetched": 0
        }


async def handle_generate_report_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handler for auto-generating compliance reports.
    
    Args:
        task_id: ID of the task
        payload: Should contain: project_id, report_type, template, etc.
        db: Database session
        
    Returns:
        Result containing generated report details
    """
    logger.info(f"Report generation task {task_id} started")
    
    # TODO: Implement as MCP tool
    # For now, return placeholder
    result = {
        "status": "not_implemented",
        "message": "Report generation will be implemented as MCP tool in next phase",
        "planned_formats": ["pdf", "docx", "html"],
        "payload": payload
    }
    
    await asyncio.sleep(2)  # Simulate work
    return result


async def handle_analyze_compliance_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handler for analyzing compliance using MCP tool.
    
    This handler orchestrates compliance analysis by calling the
    MCP-hosted compliance_analyzer tool.
    
    Args:
        task_id: ID of the task
        payload: Should contain:
            - project_id: Project ID to analyze
            - framework: Framework (IM8, ISO27001, NIST)
            - include_evidence: Whether to analyze evidence
            - generate_recommendations: Whether to generate AI recommendations
        db: Database session
        
    Returns:
        Analysis results with gaps and recommendations
    """
    logger.info(f"Compliance analysis task {task_id} started - calling MCP tool")
    
    await update_progress(task_id, 10, "Initializing compliance analysis...")
    
    try:
        # Extract parameters
        project_id = payload.get("project_id")
        framework = payload.get("framework", "IM8")
        include_evidence = payload.get("include_evidence", True)
        generate_recommendations = payload.get("generate_recommendations", True)
        
        await update_progress(
            task_id,
            20,
            f"Analyzing {framework} compliance for project {project_id}..."
        )
        
        # Call MCP tool
        result = await mcp_client.analyze_compliance(
            project_id=project_id,
            framework=framework,
            include_evidence=include_evidence,
            generate_recommendations=generate_recommendations
        )
        
        await update_progress(
            task_id,
            80,
            f"Analysis complete: {result.get('overall_score', 0):.1f}% compliance"
        )
        
        logger.info(
            f"Compliance analysis task {task_id} completed: "
            f"{result.get('overall_score', 0):.1f}% compliance, "
            f"{result.get('total_controls', 0)} controls assessed"
        )
        
        return {
            "status": "success",
            "message": f"Compliance analysis completed via MCP: {result.get('overall_score', 0):.1f}%",
            **result
        }
    
    except MCPToolError as e:
        logger.error(f"Compliance analysis task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"MCP tool error: {e.error}",
            "overall_score": 0,
            "total_controls": 0
        }
    
    except Exception as e:
        logger.error(f"Compliance analysis task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "overall_score": 0
        }


# Map of task types to their handlers
TASK_HANDLERS = {
    "test": handle_test_task,
    "fetch_evidence": handle_fetch_evidence_task,
    "generate_report": handle_generate_report_task,
    "analyze_compliance": handle_analyze_compliance_task,
}
