"""
Analytics API
Real-time metrics and dashboards for compliance tracking
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, timedelta
from api.src.utils.datetime_utils import now_sgt

from api.src.database import get_db
from api.src.auth import get_current_user, require_admin
from api.src.models import (
    User, Assessment, Finding, Control, Evidence,
    AssessmentControl, Agency
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard metrics for the user's agency
    
    Returns:
    - Assessment statistics
    - Finding statistics by severity and status
    - Control testing statistics
    - Recent activity summary
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    agency_id = user.agency_id
    
    # Assessment Metrics
    total_assessments = db.query(Assessment).filter(
        Assessment.agency_id == agency_id
    ).count()
    
    active_assessments = db.query(Assessment).filter(
        Assessment.agency_id == agency_id,
        Assessment.status.in_(["planning", "in_progress"])
    ).count()
    
    completed_assessments = db.query(Assessment).filter(
        Assessment.agency_id == agency_id,
        Assessment.status == "completed"
    ).count()
    
    # Finding Metrics
    findings_query = db.query(Finding).join(Assessment).filter(
        Assessment.agency_id == agency_id
    )
    
    total_findings = findings_query.count()
    
    open_findings = findings_query.filter(
        Finding.status == "open"
    ).count()
    
    resolved_findings = findings_query.filter(
        Finding.status.in_(["resolved", "validated", "closed"])
    ).count()
    
    # Findings by Severity
    critical_findings = findings_query.filter(
        Finding.severity == "critical",
        Finding.status.notin_(["resolved", "validated", "closed"])
    ).count()
    
    high_findings = findings_query.filter(
        Finding.severity == "high",
        Finding.status.notin_(["resolved", "validated", "closed"])
    ).count()
    
    medium_findings = findings_query.filter(
        Finding.severity == "medium",
        Finding.status.notin_(["resolved", "validated", "closed"])
    ).count()
    
    low_findings = findings_query.filter(
        Finding.severity == "low",
        Finding.status.notin_(["resolved", "validated", "closed"])
    ).count()
    
    # Overdue Findings
    overdue_findings = findings_query.filter(
        Finding.due_date < now_sgt(),
        Finding.status.notin_(["resolved", "validated", "closed"])
    ).count()
    
    # Control Metrics
    total_controls = db.query(Control).filter(
        Control.agency_id == agency_id
    ).count()
    
    tested_controls = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.last_tested_at.isnot(None)
    ).count()
    
    passed_controls = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.review_status == "passed"
    ).count()
    
    failed_controls = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.review_status == "failed"
    ).count()
    
    # Evidence Metrics
    total_evidence = db.query(Evidence).join(Control).filter(
        Control.agency_id == agency_id
    ).count()
    
    # Recent Activity (last 30 days)
    thirty_days_ago = now_sgt() - timedelta(days=30)
    
    recent_assessments = db.query(Assessment).filter(
        Assessment.agency_id == agency_id,
        Assessment.created_at >= thirty_days_ago
    ).count()
    
    recent_findings = findings_query.filter(
        Finding.created_at >= thirty_days_ago
    ).count()
    
    recent_resolved = findings_query.filter(
        Finding.resolved_at >= thirty_days_ago
    ).count()
    
    # Compliance Score (percentage of controls passing)
    compliance_score = 0
    if total_controls > 0:
        compliance_score = round((passed_controls / total_controls) * 100, 2)
    
    # Risk Score (weighted by severity)
    risk_score = (
        (critical_findings * 10) +
        (high_findings * 5) +
        (medium_findings * 2) +
        (low_findings * 1)
    )
    
    return {
        "assessments": {
            "total": total_assessments,
            "active": active_assessments,
            "completed": completed_assessments
        },
        "findings": {
            "total": total_findings,
            "open": open_findings,
            "resolved": resolved_findings,
            "overdue": overdue_findings,
            "by_severity": {
                "critical": critical_findings,
                "high": high_findings,
                "medium": medium_findings,
                "low": low_findings
            }
        },
        "controls": {
            "total": total_controls,
            "tested": tested_controls,
            "passed": passed_controls,
            "failed": failed_controls,
            "compliance_score": compliance_score
        },
        "evidence": {
            "total": total_evidence
        },
        "recent_activity": {
            "new_assessments": recent_assessments,
            "new_findings": recent_findings,
            "resolved_findings": recent_resolved
        },
        "risk_score": risk_score,
        "agency_id": agency_id
    }


@router.get("/assessments/trends")
async def get_assessment_trends(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assessment creation and completion trends"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    agency_id = user.agency_id
    
    start_date = now_sgt() - timedelta(days=days)
    
    # Assessments created per day
    created_trends = db.query(
        func.date(Assessment.created_at).label("date"),
        func.count(Assessment.id).label("count")
    ).filter(
        Assessment.agency_id == agency_id,
        Assessment.created_at >= start_date
    ).group_by(func.date(Assessment.created_at)).all()
    
    # Assessments completed per day
    completed_trends = db.query(
        func.date(Assessment.completed_at).label("date"),
        func.count(Assessment.id).label("count")
    ).filter(
        Assessment.agency_id == agency_id,
        Assessment.completed_at >= start_date,
        Assessment.completed_at.isnot(None)
    ).group_by(func.date(Assessment.completed_at)).all()
    
    return {
        "created": [{"date": str(t.date), "count": t.count} for t in created_trends],
        "completed": [{"date": str(t.date), "count": t.count} for t in completed_trends]
    }


@router.get("/findings/trends")
async def get_finding_trends(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get finding creation and resolution trends"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    agency_id = user.agency_id
    
    start_date = now_sgt() - timedelta(days=days)
    
    # Findings created per day
    created_trends = db.query(
        func.date(Finding.created_at).label("date"),
        func.count(Finding.id).label("count")
    ).join(Assessment).filter(
        Assessment.agency_id == agency_id,
        Finding.created_at >= start_date
    ).group_by(func.date(Finding.created_at)).all()
    
    # Findings resolved per day
    resolved_trends = db.query(
        func.date(Finding.resolved_at).label("date"),
        func.count(Finding.id).label("count")
    ).join(Assessment).filter(
        Assessment.agency_id == agency_id,
        Finding.resolved_at >= start_date,
        Finding.resolved_at.isnot(None)
    ).group_by(func.date(Finding.resolved_at)).all()
    
    return {
        "created": [{"date": str(t.date), "count": t.count} for t in created_trends],
        "resolved": [{"date": str(t.date), "count": t.count} for t in resolved_trends]
    }


@router.get("/findings/severity-breakdown")
async def get_findings_severity_breakdown(
    assessment_id: Optional[int] = Query(None, description="Filter by assessment"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get breakdown of findings by severity and status"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    agency_id = user.agency_id
    
    query = db.query(Finding).join(Assessment).filter(
        Assessment.agency_id == agency_id
    )
    
    if assessment_id:
        query = query.filter(Finding.assessment_id == assessment_id)
    
    # Group by severity and resolution status
    results = db.query(
        Finding.severity,
        Finding.status,
        func.count(Finding.id).label("count")
    ).join(Assessment).filter(
        Assessment.agency_id == agency_id
    )
    
    if assessment_id:
        results = results.filter(Finding.assessment_id == assessment_id)
    
    results = results.group_by(Finding.severity, Finding.status).all()
    
    breakdown = {}
    for severity in ["critical", "high", "medium", "low", "info"]:
        breakdown[severity] = {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
            "validated": 0,
            "closed": 0
        }
    
    for result in results:
        if result.severity in breakdown and result.status in breakdown[result.severity]:
            breakdown[result.severity][result.status] = result.count
    
    return breakdown


@router.get("/controls/testing-stats")
async def get_control_testing_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get control testing statistics"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    agency_id = user.agency_id
    
    total = db.query(Control).filter(Control.agency_id == agency_id).count()
    
    # Never tested
    never_tested = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.last_tested_at.is_(None)
    ).count()
    
    # Tested in last 30 days
    thirty_days_ago = now_sgt() - timedelta(days=30)
    recently_tested = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.last_tested_at >= thirty_days_ago
    ).count()
    
    # Tested in last 90 days
    ninety_days_ago = now_sgt() - timedelta(days=90)
    tested_90_days = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.last_tested_at >= ninety_days_ago
    ).count()
    
    # By review status
    passed = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.review_status == "passed"
    ).count()
    
    failed = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.review_status == "failed"
    ).count()
    
    needs_review = db.query(Control).filter(
        Control.agency_id == agency_id,
        Control.review_status == "needs_improvement"
    ).count()
    
    return {
        "total_controls": total,
        "never_tested": never_tested,
        "recently_tested": recently_tested,
        "tested_90_days": tested_90_days,
        "by_status": {
            "passed": passed,
            "failed": failed,
            "needs_improvement": needs_review,
            "pending": total - passed - failed - needs_review
        },
        "testing_coverage": round((tested_90_days / total * 100), 2) if total > 0 else 0
    }


@router.get("/my-workload")
async def get_my_workload(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's assigned workload"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Assigned assessments
    my_assessments = db.query(Assessment).filter(
        Assessment.assigned_to == current_user["id"],
        Assessment.status.in_(["planning", "in_progress"])
    ).count()
    
    # Assigned findings
    my_findings = db.query(Finding).join(Assessment).filter(
        Finding.assigned_to == current_user["id"],
        Finding.status.in_(["open", "in_progress"])
    ).count()
    
    # Overdue findings
    my_overdue = db.query(Finding).join(Assessment).filter(
        Finding.assigned_to == current_user["id"],
        Finding.due_date < now_sgt(),
        Finding.status.in_(["open", "in_progress"])
    ).count()
    
    # Findings due soon (next 7 days)
    seven_days = now_sgt() + timedelta(days=7)
    due_soon = db.query(Finding).join(Assessment).filter(
        Finding.assigned_to == current_user["id"],
        Finding.due_date <= seven_days,
        Finding.due_date >= now_sgt(),
        Finding.status.in_(["open", "in_progress"])
    ).count()
    
    return {
        "user_id": current_user["id"],
        "username": user.username,
        "assigned_assessments": my_assessments,
        "assigned_findings": my_findings,
        "overdue_findings": my_overdue,
        "due_soon_findings": due_soon
    }


@router.get("/agency-comparison")
async def get_agency_comparison(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comparison metrics across all agencies (Admin only)"""
    
    agencies = db.query(Agency).filter(Agency.active == True).all()
    
    comparison = []
    for agency in agencies:
        total_assessments = db.query(Assessment).filter(
            Assessment.agency_id == agency.id
        ).count()
        
        total_findings = db.query(Finding).join(Assessment).filter(
            Assessment.agency_id == agency.id
        ).count()
        
        open_findings = db.query(Finding).join(Assessment).filter(
            Assessment.agency_id == agency.id,
            Finding.status == "open"
        ).count()
        
        total_controls = db.query(Control).filter(
            Control.agency_id == agency.id
        ).count()
        
        comparison.append({
            "agency_id": agency.id,
            "agency_name": agency.name,
            "assessments": total_assessments,
            "findings": total_findings,
            "open_findings": open_findings,
            "controls": total_controls
        })
    
    return comparison
