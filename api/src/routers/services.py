"""
Services Router - Endpoints for Phase 4 & 5 business logic and AI services
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from api.src.database import get_db
from api.src.models import Assessment, Finding, Control, User
from api.src.auth import get_current_user

# Import services
from api.src.services.assessment_service import AssessmentService
from api.src.services.finding_service import FindingService
from api.src.services.compliance_service import ComplianceService
from api.src.services.ai_finding_analyzer import ai_analyzer
from api.src.services.report_generator import report_generator
from api.src.services.notification_service import notification_service

router = APIRouter(prefix="/services", tags=["services"])


# ============================================================================
# Phase 4: Business Logic Services
# ============================================================================

@router.post("/assessment/{assessment_id}/update-progress")
def update_assessment_progress(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate and update assessment progress automatically
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Calculate progress
    progress = AssessmentService.calculate_progress(assessment, db)
    assessment.progress_percentage = progress
    
    # Update counts
    AssessmentService.update_assessment_counts(assessment, db)
    
    # Auto-update status
    AssessmentService.auto_update_status(assessment, db)
    
    db.commit()
    
    return {
        "assessment_id": assessment_id,
        "progress_percentage": progress,
        "status": assessment.status,
        "controls_tested": assessment.controls_tested_count,
        "findings_count": assessment.findings_count
    }


@router.get("/assessment/{assessment_id}/metrics")
def get_assessment_metrics(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive metrics for an assessment
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    metrics = AssessmentService.get_assessment_metrics(assessment, db)
    return metrics


@router.get("/assessment/{assessment_id}/compliance-score")
def get_compliance_score(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate compliance score for assessment
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    score = ComplianceService.calculate_compliance_score(assessment, db)
    return score


@router.get("/assessment/{assessment_id}/gap-analysis")
def perform_gap_analysis(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform gap analysis for assessment
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    gaps = ComplianceService.perform_gap_analysis(assessment, db)
    return gaps


@router.post("/finding/{finding_id}/calculate-risk")
def calculate_finding_risk(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate risk score for a finding
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    risk_score = FindingService.calculate_risk_score(finding)
    priority = FindingService.auto_assign_priority(finding)
    sla_status = FindingService.check_sla_breach(finding)
    
    # Update finding priority if not set
    if not finding.priority:
        finding.priority = priority
        db.commit()
    
    return {
        "finding_id": finding_id,
        "risk_score": risk_score,
        "recommended_priority": priority,
        "current_priority": finding.priority,
        "sla_status": sla_status
    }


@router.get("/findings/needing-escalation")
def get_findings_needing_escalation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get findings that need escalation (overdue critical/high)
    """
    findings = FindingService.get_findings_needing_escalation(db)
    
    return {
        "count": len(findings),
        "findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "due_date": f.due_date,
                "assigned_to": f.assignee.full_name if f.assignee else None,
                "days_overdue": (f.due_date - f.created_at).days if f.due_date else 0
            }
            for f in findings
        ]
    }


@router.get("/findings/metrics")
def get_finding_metrics(
    assessment_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive finding metrics
    """
    metrics = FindingService.get_finding_metrics(db, assessment_id)
    return metrics


# ============================================================================
# Phase 5: AI Integration Services
# ============================================================================

@router.post("/ai/analyze-finding/{finding_id}")
def ai_analyze_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Use AI to analyze a finding and provide insights
    Requires GITHUB_TOKEN environment variable
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Get related control if exists
    control = None
    if finding.control_id:
        control = db.query(Control).filter(Control.id == finding.control_id).first()
    
    # Analyze with AI
    analysis = ai_analyzer.analyze_finding(finding, control)
    
    return analysis


@router.post("/ai/analyze-findings-batch")
def ai_analyze_findings_batch(
    finding_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch analyze multiple findings with AI
    Runs in background
    """
    findings = db.query(Finding).filter(Finding.id.in_(finding_ids)).all()
    
    if not findings:
        raise HTTPException(status_code=404, detail="No findings found")
    
    # Run analysis in background
    def analyze_batch():
        results = ai_analyzer.batch_analyze_findings(findings)
        # Could store results in database or send notification
        return results
    
    background_tasks.add_task(analyze_batch)
    
    return {
        "status": "processing",
        "finding_count": len(findings),
        "message": "AI analysis started in background"
    }


@router.post("/ai/suggest-priority")
def ai_suggest_remediation_priority(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Use AI to suggest remediation priority order
    """
    findings = db.query(Finding).filter(
        Finding.assessment_id == assessment_id,
        Finding.resolution_status.in_(['open', 'in_progress'])
    ).all()
    
    if not findings:
        return {"message": "No open findings to prioritize"}
    
    priority_suggestion = ai_analyzer.suggest_remediation_priority(findings)
    
    return {
        "assessment_id": assessment_id,
        "findings_count": len(findings),
        "suggested_priority": priority_suggestion
    }


@router.post("/reports/generate/{assessment_id}")
def generate_assessment_report(
    assessment_id: int,
    include_findings: bool = True,
    include_controls: bool = True,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF report for assessment
    Requires reportlab library
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Generate report in background
    def generate_report():
        result = report_generator.generate_assessment_report(
            assessment,
            db,
            include_findings=include_findings,
            include_controls=include_controls
        )
        
        # Could send email notification when done
        if result["status"] == "success" and assessment.assigned_to:
            analyst = db.query(User).filter(User.id == assessment.assigned_to).first()
            if analyst:
                notification_service.send_email(
                    analyst.email,
                    f"Report Ready: {assessment.title}",
                    f"<p>Your assessment report is ready: <a href='/storage/reports/{result['filename']}'>Download Report</a></p>"
                )
        
        return result
    
    background_tasks.add_task(generate_report)
    
    return {
        "status": "generating",
        "assessment_id": assessment_id,
        "message": "Report generation started in background"
    }


@router.post("/notifications/finding-assigned")
def notify_finding_assigned(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send notification about finding assignment
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding or not finding.assigned_to:
        raise HTTPException(status_code=404, detail="Finding or assignee not found")
    
    assignee = db.query(User).filter(User.id == finding.assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    result = notification_service.notify_finding_assigned(finding, assignee)
    return result


@router.post("/notifications/sla-breach")
def notify_sla_breach(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send SLA breach notification
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding or not finding.assigned_to:
        raise HTTPException(status_code=404, detail="Finding or assignee not found")
    
    assignee = db.query(User).filter(User.id == finding.assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    result = notification_service.notify_sla_breach(finding, assignee)
    return result


@router.get("/health/services")
def check_services_health():
    """
    Check health status of all Phase 4 & 5 services
    """
    return {
        "business_logic": {
            "assessment_service": "operational",
            "finding_service": "operational",
            "compliance_service": "operational"
        },
        "ai_services": {
            "ai_analyzer": "operational" if ai_analyzer.enabled else "disabled",
            "model": ai_analyzer.model if ai_analyzer.enabled else None,
            "note": "Requires GITHUB_TOKEN environment variable"
        },
        "reporting": {
            "pdf_generator": "operational" if report_generator.enabled else "disabled",
            "note": "Requires reportlab library"
        },
        "notifications": {
            "email_service": "operational" if (notification_service.smtp_enabled or notification_service.sendgrid_enabled) else "disabled",
            "smtp": "enabled" if notification_service.smtp_enabled else "disabled",
            "sendgrid": "enabled" if notification_service.sendgrid_enabled else "disabled"
        }
    }
