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


async def handle_create_controls_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Generate and create security controls using LLM
    
    Payload:
        framework: str - Security framework (e.g., "IM8")
        count: int - Number of controls to generate
        domain_areas: List[str] - Domain areas to cover
        project_id: int - Project to link controls to
        agency_id: int - Agency ID
    """
    from api.src.services.llm_service import get_llm_service
    from api.src.models import Control
    
    logger.info(f"Create controls task {task_id} started")
    await update_progress(task_id, 10, "Initializing LLM service...")
    
    try:
        llm_service = get_llm_service()
        if not llm_service.is_available():
            return {
                "status": "error",
                "message": "LLM service not configured. Set AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY environment variables."
            }
        
        framework = payload.get("framework", "IM8")
        count = payload.get("count", 30)
        domain_areas = payload.get("domain_areas", [
            "IM8-01", "IM8-02", "IM8-03", "IM8-04", "IM8-05",
            "IM8-06", "IM8-07", "IM8-08", "IM8-09", "IM8-10"
        ])
        project_id = payload.get("project_id")
        agency_id = payload.get("agency_id")
        
        await update_progress(task_id, 20, f"Generating {count} controls for {framework}...")
        
        # Generate controls using LLM
        controls_data = llm_service.generate_controls(framework, domain_areas, count)
        
        await update_progress(task_id, 60, f"Generated {len(controls_data)} controls, saving to database...")
        
        # Create control records in database
        created_controls = []
        for idx, control_data in enumerate(controls_data):
            control = Control(
                agency_id=agency_id,
                project_id=project_id,
                name=control_data.get("name"),
                description=control_data.get("description"),
                control_type=control_data.get("control_type"),
                status="pending",
                framework=framework,
                control_id=control_data.get("control_id"),
                category=control_data.get("category"),
                requirement_level=control_data.get("requirement_level", "Mandatory"),
                implementation_guidance=control_data.get("implementation_guidance"),
                evidence_requirements=control_data.get("evidence_requirements", []),
                testing_frequency=control_data.get("testing_frequency", "Annual")
            )
            db.add(control)
            created_controls.append(control_data.get("name"))
            
            # Update progress
            progress = 60 + int((idx + 1) / len(controls_data) * 30)
            await update_progress(task_id, progress, f"Saved {idx + 1}/{len(controls_data)} controls...")
        
        db.commit()
        
        await update_progress(task_id, 100, f"Successfully created {len(created_controls)} controls")
        
        return {
            "status": "success",
            "message": f"Successfully created {len(created_controls)} {framework} controls",
            "controls_created": len(created_controls),
            "control_names": created_controls[:10],  # First 10 names
            "framework": framework,
            "domains_covered": domain_areas
        }
    
    except Exception as e:
        logger.error(f"Create controls task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to create controls: {str(e)}"
        }


async def handle_create_findings_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Generate and create security findings using LLM
    
    Payload:
        findings_description: str - Natural language description of findings
        assessment_id: int - Assessment to link findings to
        framework: str - Framework for control mapping (default: "IM8")
        assigned_to: int - User ID to assign findings to
        agency_id: int - Agency ID
    """
    from api.src.services.llm_service import get_llm_service
    from api.src.models import Finding
    from datetime import datetime, timedelta
    
    logger.info(f"Create findings task {task_id} started")
    await update_progress(task_id, 10, "Initializing LLM service...")
    
    try:
        llm_service = get_llm_service()
        if not llm_service.is_available():
            return {
                "status": "error",
                "message": "LLM service not configured."
            }
        
        findings_description = payload.get("findings_description", "")
        assessment_id = payload.get("assessment_id")
        framework = payload.get("framework", "IM8")
        assigned_to = payload.get("assigned_to")
        
        await update_progress(task_id, 20, "Parsing findings description...")
        
        # Generate findings using LLM
        findings_data = llm_service.generate_findings(findings_description, assessment_id, framework)
        
        await update_progress(task_id, 60, f"Generated {len(findings_data)} findings, saving to database...")
        
        # Create finding records
        created_findings = []
        for idx, finding_data in enumerate(findings_data):
            # Calculate due date based on severity
            severity = finding_data.get("severity", "medium")
            if severity == "critical":
                due_days = 30
            elif severity == "high":
                due_days = 60
            elif severity == "medium":
                due_days = 90
            else:
                due_days = 120
            
            finding = Finding(
                assessment_id=assessment_id,
                title=finding_data.get("title"),
                description=finding_data.get("description"),
                severity=severity,
                cvss=finding_data.get("cvss"),
                cve=finding_data.get("cve"),
                remediation=finding_data.get("remediation"),
                priority=finding_data.get("priority", severity),
                assigned_to=assigned_to,
                due_date=datetime.utcnow() + timedelta(days=due_days),
                resolution_status="open",
                created_at=datetime.utcnow()
            )
            db.add(finding)
            created_findings.append(finding_data.get("title"))
            
            progress = 60 + int((idx + 1) / len(findings_data) * 30)
            await update_progress(task_id, progress, f"Saved {idx + 1}/{len(findings_data)} findings...")
        
        db.commit()
        
        await update_progress(task_id, 100, f"Successfully created {len(created_findings)} findings")
        
        return {
            "status": "success",
            "message": f"Successfully created {len(created_findings)} findings",
            "findings_created": len(created_findings),
            "finding_titles": created_findings,
            "assessment_id": assessment_id
        }
    
    except Exception as e:
        logger.error(f"Create findings task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to create findings: {str(e)}"
        }


async def handle_analyze_evidence_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Analyze evidence documents using LLM
    
    Payload:
        evidence_ids: List[int] - Evidence IDs to analyze
        control_id: int - Control ID to validate against
    """
    from api.src.services.llm_service import get_llm_service
    from api.src.models import Evidence, Control
    
    logger.info(f"Analyze evidence task {task_id} started")
    await update_progress(task_id, 10, "Initializing LLM service...")
    
    try:
        llm_service = get_llm_service()
        if not llm_service.is_available():
            return {
                "status": "error",
                "message": "LLM service not configured."
            }
        
        evidence_ids = payload.get("evidence_ids", [])
        control_id = payload.get("control_id")
        
        # Get control requirements
        control = db.query(Control).filter(Control.id == control_id).first()
        if not control:
            return {
                "status": "error",
                "message": f"Control {control_id} not found"
            }
        
        requirements = control.evidence_requirements or []
        
        await update_progress(task_id, 20, f"Analyzing {len(evidence_ids)} evidence items...")
        
        analysis_results = []
        for idx, evidence_id in enumerate(evidence_ids):
            evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
            if not evidence:
                continue
            
            # For now, analyze based on file name and type
            # In production, you'd read the actual file content from Azure Blob Storage
            evidence_content = f"File: {evidence.file_name}\nType: {evidence.type}\nDescription: {evidence.description or 'N/A'}"
            
            analysis = llm_service.analyze_evidence(evidence_content, requirements)
            
            # Update evidence with analysis results
            evidence.review_comments = f"AI Analysis - Completeness: {analysis.get('completeness_score', 0)}%\n" + \
                                      f"Gaps: {', '.join(analysis.get('gaps', []))}"
            
            analysis_results.append({
                "evidence_id": evidence_id,
                "file_name": evidence.file_name,
                "completeness_score": analysis.get("completeness_score", 0),
                "gaps": analysis.get("gaps", [])
            })
            
            progress = 20 + int((idx + 1) / len(evidence_ids) * 70)
            await update_progress(task_id, progress, f"Analyzed {idx + 1}/{len(evidence_ids)} items...")
        
        db.commit()
        
        await update_progress(task_id, 100, "Analysis complete")
        
        avg_score = sum(r["completeness_score"] for r in analysis_results) / len(analysis_results) if analysis_results else 0
        
        return {
            "status": "success",
            "message": f"Analyzed {len(analysis_results)} evidence items",
            "average_completeness": round(avg_score, 2),
            "analysis_results": analysis_results
        }
    
    except Exception as e:
        logger.error(f"Analyze evidence task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze evidence: {str(e)}"
        }


async def handle_generate_compliance_report_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Generate compliance report using LLM
    
    Payload:
        assessment_id: int - Assessment ID
        report_type: str - "executive" or "technical"
    """
    from api.src.services.llm_service import get_llm_service
    from api.src.models import Assessment, Finding, Control
    from sqlalchemy import func
    
    logger.info(f"Generate compliance report task {task_id} started")
    await update_progress(task_id, 10, "Gathering assessment data...")
    
    try:
        llm_service = get_llm_service()
        if not llm_service.is_available():
            return {
                "status": "error",
                "message": "LLM service not configured."
            }
        
        assessment_id = payload.get("assessment_id")
        report_type = payload.get("report_type", "executive")
        
        # Get assessment
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            return {
                "status": "error",
                "message": f"Assessment {assessment_id} not found"
            }
        
        await update_progress(task_id, 30, "Collecting findings and metrics...")
        
        # Gather data for report
        findings = db.query(Finding).filter(Finding.assessment_id == assessment_id).all()
        
        findings_by_severity = db.query(
            Finding.severity,
            func.count(Finding.id)
        ).filter(Finding.assessment_id == assessment_id).group_by(Finding.severity).all()
        
        findings_by_status = db.query(
            Finding.resolution_status,
            func.count(Finding.id)
        ).filter(Finding.assessment_id == assessment_id).group_by(Finding.resolution_status).all()
        
        report_data = {
            "assessment": {
                "title": assessment.title,
                "framework": assessment.framework,
                "scope": assessment.scope,
                "status": assessment.status,
                "period_start": str(assessment.assessment_period_start) if assessment.assessment_period_start else None,
                "period_end": str(assessment.assessment_period_end) if assessment.assessment_period_end else None
            },
            "findings": {
                "total": len(findings),
                "by_severity": {sev: count for sev, count in findings_by_severity},
                "by_status": {status: count for status, count in findings_by_status}
            },
            "compliance_score": assessment.progress_percentage or 0
        }
        
        await update_progress(task_id, 60, f"Generating {report_type} report...")
        
        # Generate report using LLM
        report_content = llm_service.generate_report(report_type, report_data)
        
        await update_progress(task_id, 100, "Report generated successfully")
        
        return {
            "status": "success",
            "message": f"Generated {report_type} compliance report",
            "report_type": report_type,
            "report_content": report_content,
            "assessment_id": assessment_id,
            "assessment_title": assessment.title
        }
    
    except Exception as e:
        logger.error(f"Generate compliance report task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to generate report: {str(e)}"
        }


# Map of task types to their handlers
TASK_HANDLERS = {
    "test": handle_test_task,
    "fetch_evidence": handle_fetch_evidence_task,
    "generate_report": handle_generate_report_task,
    "analyze_compliance": handle_analyze_compliance_task,
    "create_controls": handle_create_controls_task,
    "create_findings": handle_create_findings_task,
    "analyze_evidence": handle_analyze_evidence_task,
    "generate_compliance_report": handle_generate_compliance_report_task,
}
