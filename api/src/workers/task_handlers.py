"""
Task handler implementations for different agent task types.

Each handler orchestrates tasks by calling MCP tools.
"""
import asyncio
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from api.src.workers.task_worker import update_progress
from api.src.mcp.client import mcp_client, MCPToolError

logger = logging.getLogger(__name__)


# ============================================================================
# CONTROL REQUIREMENTS DATABASE (RAG Knowledge Base)
# ============================================================================
# Mapping of control_id to acceptance criteria for evidence validation
CONTROL_REQUIREMENTS = {
    1: {
        "title": "Access Control Policy",
        "domain": "IM8-01",
        "requirements": [
            "Document must define user access control procedures",
            "Must include authentication and authorization policies",
            "Should specify role-based access control (RBAC) implementation",
            "Must include password complexity requirements",
            "Should define periodic access review procedures"
        ],
        "evidence_types": ["document", "screenshot", "configuration"],
        "keywords": ["access control", "authentication", "authorization", "RBAC", "password policy"]
    },
    3: {
        "title": "Incident Response Plan",
        "domain": "IM8-06",
        "requirements": [
            "Must define incident classification levels",
            "Should include response team contact information",
            "Must specify escalation procedures",
            "Should include incident logging procedures",
            "Must define post-incident review process"
        ],
        "evidence_types": ["document", "report"],
        "keywords": ["incident", "response", "escalation", "notification", "remediation"]
    },
    4: {
        "title": "Data Backup Procedure",
        "domain": "IM8-07",
        "requirements": [
            "Must specify backup frequency and schedule",
            "Should define backup retention periods",
            "Must include restore testing procedures",
            "Should specify offsite storage requirements",
            "Must define backup encryption standards"
        ],
        "evidence_types": ["document", "configuration", "log"],
        "keywords": ["backup", "restore", "retention", "recovery", "encryption"]
    },
    5: {
        "title": "Security Awareness Training",
        "domain": "IM8-02",
        "requirements": [
            "Must include training completion records",
            "Should show training content and curriculum",
            "Must demonstrate employee acknowledgment",
            "Should include phishing awareness training",
            "Must specify training frequency (annual minimum)"
        ],
        "evidence_types": ["document", "screenshot", "report"],
        "keywords": ["training", "awareness", "phishing", "security", "education"]
    }
}

# ============================================================================
# CONTROL RELATIONSHIP GRAPH (Graph RAG Knowledge)
# ============================================================================
# Maps control_id to related controls in the same domain or with similar objectives
CONTROL_GRAPH = {
    1: {  # Access Control Policy
        "same_domain": [],  # IM8-01 domain
        "related": [3, 5],  # Incident Response (auth failures), Security Training
        "upstream": [],  # Controls this depends on
        "downstream": [3]  # Controls that depend on this
    },
    3: {  # Incident Response Plan
        "same_domain": [],  # IM8-06 domain
        "related": [1, 4],  # Access Control (breach), Backup (recovery)
        "upstream": [1],  # Depends on Access Control
        "downstream": []
    },
    4: {  # Data Backup Procedure
        "same_domain": [],  # IM8-07 domain
        "related": [3],  # Incident Response (disaster recovery)
        "upstream": [],
        "downstream": [3]  # Supports Incident Response
    },
    5: {  # Security Awareness Training
        "same_domain": [],  # IM8-02 domain
        "related": [1, 3],  # Access Control (training), Incident Response (reporting)
        "upstream": [],
        "downstream": [1, 3]  # Supports both
    }
}


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


async def handle_upload_evidence_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handler for direct evidence upload from chat (file already saved by API).
    
    This bypasses MCP and directly creates evidence record since file is already
    stored in API container's storage.
    
    Args:
        task_id: ID of the task
        payload: Should contain:
            - file_path: Path to uploaded file (already saved)
            - control_id: Control ID
            - title: Evidence title
            - description: Evidence description
            - current_user_id: User who uploaded
            - agency_id: Agency ID
        db: Database session
        
    Returns:
        Evidence ID and success status
    """
    from api.src import models
    
    logger.info(f"Direct evidence upload task {task_id} started")
    
    await update_progress(task_id, 10, "Processing uploaded file...")
    
    try:
        # Extract parameters
        file_path = payload.get("file_path")
        control_id = payload.get("control_id")
        title = payload.get("title")
        description = payload.get("description")
        evidence_type = payload.get("evidence_type", "policy_document")
        current_user_id = payload.get("current_user_id")
        agency_id = payload.get("agency_id")
        
        if not file_path or not control_id or not current_user_id:
            return {
                "status": "error",
                "message": "Missing required parameters",
                "evidence_ids": []
            }
        
        await update_progress(task_id, 30, "Creating evidence record...")
        
        # Get control to verify it exists
        control = db.query(models.Control).filter(models.Control.id == control_id).first()
        if not control:
            return {
                "status": "error",
                "message": f"Control {control_id} not found",
                "evidence_ids": []
            }
        
        # Check if evidence record already exists for this file
        existing = db.query(models.Evidence).filter(
            models.Evidence.file_path == file_path
        ).first()
        
        if existing:
            logger.info(f"Evidence already exists with ID {existing.id}")
            return {
                "status": "success",
                "message": f"Evidence record already exists",
                "evidence_ids": [existing.id],
                "total_fetched": 1
            }
        
        # Create new evidence record
        evidence = models.Evidence(
            control_id=control.id,
            agency_id=agency_id or control.agency_id,
            title=title or "Evidence document",
            description=description,
            evidence_type=evidence_type,
            file_path=file_path,
            uploaded_by=current_user_id,
            verification_status="pending"
        )
        
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        
        await update_progress(task_id, 100, f"Evidence {evidence.id} created successfully")
        
        logger.info(f"Direct upload task {task_id} completed: Evidence {evidence.id} created")
        
        return {
            "status": "success",
            "message": f"Evidence {evidence.id} uploaded successfully",
            "evidence_ids": [evidence.id],
            "total_fetched": 1,
            "total_failed": 0
        }
    
    except Exception as e:
        logger.error(f"Direct upload task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Upload failed: {str(e)}",
            "evidence_ids": [],
            "total_fetched": 0
        }


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
            # Map LLM-generated data to actual Control model fields
            # Store framework info in control_type field (e.g., "IM8-AC-01")
            control_type = control_data.get("control_id", f"{framework}-{idx+1:03d}")
            
            # Combine implementation guidance and evidence requirements into description
            description = control_data.get("description", "")
            implementation = control_data.get("implementation_guidance")
            if implementation:
                description += f"\n\nImplementation Guidance:\n{implementation}"
            evidence_reqs = control_data.get("evidence_requirements", [])
            if evidence_reqs:
                description += f"\n\nEvidence Requirements:\n" + "\n".join(f"- {req}" for req in evidence_reqs)
            
            control = Control(
                agency_id=agency_id,
                project_id=project_id,
                name=control_data.get("name"),
                description=description,
                control_type=control_type,
                status="pending",
                test_procedure=control_data.get("implementation_guidance", "To be defined"),
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


async def handle_create_project_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Create a new project
    
    Payload:
        name: str - Project name (required)
        description: str - Project description
        project_type: str - Type of project (default: "compliance_assessment")
        agency_id: int - Agency ID (from current user, required)
        start_date: str - Start date (YYYY-MM-DD format, optional)
        created_by: int - User ID who created it
    """
    logger.info(f"Create project task {task_id} started")
    await update_progress(task_id, 20, "Creating project...")
    
    try:
        from api.src.models import Project
        from datetime import datetime
        
        # Validate required fields
        if not payload.get("name"):
            return {
                "status": "error",
                "message": "Project name is required"
            }
        
        if not payload.get("agency_id"):
            return {
                "status": "error",
                "message": "Agency ID is required"
            }
        
        # Parse start_date if provided
        start_date = None
        if payload.get("start_date"):
            try:
                start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d").date()
            except ValueError:
                start_date = None
        
        project = Project(
            name=payload["name"],
            description=payload.get("description", ""),
            project_type=payload.get("project_type", "compliance_assessment"),
            status="pending",
            agency_id=payload["agency_id"],
            start_date=start_date
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        await update_progress(task_id, 100, f"Project '{project.name}' created successfully")
        
        logger.info(f"Create project task {task_id} completed: Project {project.id} - {project.name}")
        
        return {
            "status": "success",
            "message": f"Project '{project.name}' created successfully",
            "project_id": project.id,
            "project_name": project.name,
            "project_type": project.project_type,
            "agency_id": project.agency_id
        }
    
    except Exception as e:
        logger.error(f"Create project task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to create project: {str(e)}"
        }


async def handle_request_evidence_upload_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handle evidence upload request - creates pending evidence record for analyst to upload file
    
    Payload:
        control_id: int - Control ID (required)
        title: str - Evidence title (required)
        description: str - Evidence description
        evidence_type: str - Type (document/screenshot/configuration/log/report/other)
        current_user_id: int - User ID (required)
    """
    logger.info(f"Request evidence upload task {task_id} started")
    await update_progress(task_id, 20, "Creating evidence upload request...")
    
    try:
        from api.src.models import Evidence, Control
        import uuid
        
        control_id = payload.get("control_id")
        title = payload.get("title")
        current_user_id = payload.get("current_user_id") or payload.get("created_by")
        
        if not control_id or not title or not current_user_id:
            return {
                "status": "error",
                "message": "control_id, title, and current_user_id are required"
            }
        
        # Lookup control to get agency_id (required for Evidence record)
        control = db.query(Control).filter(Control.id == control_id).first()
        if not control:
            return {
                "status": "error",
                "message": f"Control {control_id} not found"
            }
        
        # Generate upload ID for frontend
        upload_id = str(uuid.uuid4())
        
        # Create pending evidence record with agency_id from control
        evidence = Evidence(
            control_id=control_id,
            agency_id=control.agency_id,  # FIX: Set agency_id from control
            title=title,
            description=payload.get("description", ""),
            evidence_type=payload.get("evidence_type", "document"),
            verification_status="pending",
            uploaded_by=current_user_id,
            file_path=f"/pending/{upload_id}",  # Placeholder path
            original_filename="pending_upload"
        )
        
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        
        await update_progress(task_id, 100, "Evidence upload request created")
        
        logger.info(f"Request evidence upload task {task_id} completed: Evidence {evidence.id}")
        
        # Get control info
        control_info = CONTROL_REQUIREMENTS.get(control_id, {})
        
        return {
            "status": "success",
            "message": f"Evidence upload requested for control {control_id}",
            "evidence_id": evidence.id,
            "upload_id": upload_id,
            "control_id": control_id,
            "control_title": control_info.get("title", f"Control {control_id}"),
            "accepted_types": control_info.get("evidence_types", ["document", "screenshot"]),
            "instructions": f"Please upload evidence for: {title}. Accepted file types: PDF, DOCX, XLSX, PNG, JPG (max 10MB)"
        }
    
    except Exception as e:
        logger.error(f"Request evidence upload task {task_id} failed: {e}")
        db.rollback()
        return {
            "status": "error",
            "message": f"Failed to create evidence upload request: {str(e)}"
        }


async def handle_analyze_evidence_rag_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Analyze evidence against control requirements using RAG
    
    Payload:
        evidence_id: int - Evidence ID (required)
        control_id: int - Control ID (optional, can be inferred)
    """
    logger.info(f"Analyze evidence RAG task {task_id} started")
    await update_progress(task_id, 20, "Loading evidence and control requirements...")
    
    try:
        from api.src.models import Evidence
        
        evidence_id = payload.get("evidence_id")
        if not evidence_id:
            return {
                "status": "error",
                "message": "evidence_id is required"
            }
        
        # Fetch evidence
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {
                "status": "error",
                "message": f"Evidence {evidence_id} not found"
            }
        
        control_id = payload.get("control_id") or evidence.control_id
        control_reqs = CONTROL_REQUIREMENTS.get(control_id)
        
        if not control_reqs:
            return {
                "status": "error",
                "message": f"Control {control_id} requirements not found in knowledge base"
            }
        
        await update_progress(task_id, 50, "Validating evidence against requirements...")
        
        # RAG Analysis: Check evidence metadata against requirements
        analysis = {
            "evidence_id": evidence_id,
            "control_id": control_id,
            "control_title": control_reqs["title"],
            "validation_results": []
        }
        
        # Check evidence type matches accepted types
        type_valid = evidence.evidence_type in control_reqs["evidence_types"]
        analysis["validation_results"].append({
            "criterion": "Evidence Type",
            "expected": control_reqs["evidence_types"],
            "actual": evidence.evidence_type,
            "passed": type_valid
        })
        
        # Check keywords in title/description (simple RAG)
        keywords_found = []
        text_to_check = f"{evidence.title} {evidence.description}".lower()
        for keyword in control_reqs["keywords"]:
            if keyword.lower() in text_to_check:
                keywords_found.append(keyword)
        
        keyword_coverage = len(keywords_found) / len(control_reqs["keywords"]) * 100
        analysis["validation_results"].append({
            "criterion": "Keyword Coverage",
            "expected": control_reqs["keywords"],
            "actual": keywords_found,
            "passed": keyword_coverage >= 40,  # 40% threshold
            "coverage_percent": round(keyword_coverage, 1)
        })
        
        # Overall assessment
        passed_count = sum(1 for v in analysis["validation_results"] if v["passed"])
        total_count = len(analysis["validation_results"])
        overall_score = (passed_count / total_count) * 100
        
        analysis["overall_score"] = round(overall_score, 1)
        analysis["passed"] = overall_score >= 60  # 60% threshold
        analysis["recommendations"] = []
        
        if not type_valid:
            analysis["recommendations"].append(
                f"Consider providing evidence type: {', '.join(control_reqs['evidence_types'])}"
            )
        
        if keyword_coverage < 60:
            missing_keywords = [k for k in control_reqs["keywords"] if k not in keywords_found]
            analysis["recommendations"].append(
                f"Include more relevant keywords: {', '.join(missing_keywords[:3])}"
            )
        
        await update_progress(task_id, 100, "Evidence analysis completed")
        
        logger.info(f"Analyze evidence RAG task {task_id} completed: Score {overall_score}%")
        
        return {
            "status": "success",
            "message": f"Evidence analysis completed (Score: {overall_score}%)",
            "analysis": analysis
        }
    
    except Exception as e:
        logger.error(f"Analyze evidence RAG task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to analyze evidence: {str(e)}"
        }


async def handle_suggest_related_controls_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Suggest related controls using Graph RAG
    
    Payload:
        evidence_id: int - Evidence ID (required)
        control_id: int - Primary control ID (required)
        max_suggestions: int - Max suggestions to return (default 5)
    """
    logger.info(f"Suggest related controls task {task_id} started")
    await update_progress(task_id, 30, "Analyzing control relationships...")
    
    try:
        from api.src.models import Evidence, Control
        
        evidence_id = payload.get("evidence_id")
        control_id = payload.get("control_id")
        max_suggestions = payload.get("max_suggestions", 5)
        
        if not evidence_id or not control_id:
            return {
                "status": "error",
                "message": "evidence_id and control_id are required"
            }
        
        # Fetch evidence
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {
                "status": "error",
                "message": f"Evidence {evidence_id} not found"
            }
        
        # Graph RAG: Get related controls from graph
        control_relationships = CONTROL_GRAPH.get(control_id, {})
        related_ids = (
            control_relationships.get("same_domain", []) +
            control_relationships.get("related", []) +
            control_relationships.get("downstream", [])
        )
        
        # Remove duplicates and limit
        related_ids = list(set(related_ids))[:max_suggestions]
        
        await update_progress(task_id, 70, f"Found {len(related_ids)} related controls...")
        
        suggestions = []
        for rel_id in related_ids:
            control_info = CONTROL_REQUIREMENTS.get(rel_id)
            if not control_info:
                continue
            
            # Fetch control from DB
            control = db.query(Control).filter(Control.id == rel_id).first()
            
            # Calculate relevance score based on evidence type and keywords
            relevance_score = 50  # Base score
            
            # Boost if evidence type matches
            if evidence.evidence_type in control_info.get("evidence_types", []):
                relevance_score += 30
            
            # Boost for keyword overlap
            text_to_check = f"{evidence.title} {evidence.description}".lower()
            keyword_matches = sum(1 for kw in control_info["keywords"] if kw.lower() in text_to_check)
            relevance_score += min(keyword_matches * 5, 20)
            
            suggestions.append({
                "control_id": rel_id,
                "control_title": control_info["title"],
                "domain": control_info["domain"],
                "relevance_score": min(relevance_score, 100),
                "reason": f"Related through {control_relationships.get('related', []).__contains__(rel_id) and 'similar objectives' or 'domain relationship'}",
                "status": control.status if control else "unknown"
            })
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        await update_progress(task_id, 100, f"Generated {len(suggestions)} suggestions")
        
        logger.info(f"Suggest related controls task {task_id} completed: {len(suggestions)} suggestions")
        
        return {
            "status": "success",
            "message": f"Found {len(suggestions)} related controls",
            "primary_control_id": control_id,
            "evidence_id": evidence_id,
            "suggestions": suggestions
        }
    
    except Exception as e:
        logger.error(f"Suggest related controls task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to suggest related controls: {str(e)}"
        }


async def handle_submit_evidence_for_review_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Submit evidence for auditor review (maker-checker workflow)
    
    Payload:
        evidence_id: int - Evidence ID (required)
        comments: str - Submission comments (optional)
        current_user_id: int - User ID (required)
    """
    logger.info(f"Submit evidence for review task {task_id} started")
    await update_progress(task_id, 30, "Submitting evidence for review...")
    
    try:
        from api.src.models import Evidence
        from datetime import datetime
        
        evidence_id = payload.get("evidence_id")
        current_user_id = payload.get("current_user_id") or payload.get("created_by")
        
        if not evidence_id or not current_user_id:
            return {
                "status": "error",
                "message": "evidence_id and current_user_id are required"
            }
        
        # Fetch evidence
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {
                "status": "error",
                "message": f"Evidence {evidence_id} not found"
            }
        
        # Validate current status
        if evidence.verification_status not in ["pending", "rejected"]:
            return {
                "status": "error",
                "message": f"Evidence cannot be submitted - current status: {evidence.verification_status}"
            }
        
        # Update evidence status
        evidence.verification_status = "under_review"
        evidence.submitted_by = current_user_id
        evidence.review_comments = payload.get("comments", "")
        
        db.commit()
        db.refresh(evidence)
        
        await update_progress(task_id, 100, "Evidence submitted for review")
        
        logger.info(f"Submit evidence for review task {task_id} completed: Evidence {evidence_id}")
        
        return {
            "status": "success",
            "message": f"Evidence '{evidence.title}' submitted for auditor review",
            "evidence_id": evidence_id,
            "verification_status": evidence.verification_status,
            "submitted_by": current_user_id
        }
    
    except Exception as e:
        logger.error(f"Submit evidence for review task {task_id} failed: {e}")
        db.rollback()
        return {
            "status": "error",
            "message": f"Failed to submit evidence: {str(e)}"
        }


# Map of task types to their handlers
TASK_HANDLERS = {
    "test": handle_test_task,
    "upload_evidence": handle_upload_evidence_task,  # Direct upload (no MCP)
    "fetch_evidence": handle_fetch_evidence_task,
    "generate_report": handle_generate_report_task,
    "analyze_compliance": handle_analyze_compliance_task,
    "create_controls": handle_create_controls_task,
    "create_project": handle_create_project_task,
    "create_findings": handle_create_findings_task,
    "analyze_evidence": handle_analyze_evidence_task,  # Original MCP version
    "analyze_evidence_rag": handle_analyze_evidence_rag_task,  # New RAG version
    "generate_compliance_report": handle_generate_compliance_report_task,
    "request_evidence_upload": handle_request_evidence_upload_task,
    "suggest_related_controls": handle_suggest_related_controls_task,
    "submit_evidence_for_review": handle_submit_evidence_for_review_task,
}