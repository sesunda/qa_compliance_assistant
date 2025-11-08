"""
Assessment Management API
Endpoints for creating, managing, and tracking security assessments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from api.src.database import get_db
from api.src.auth import get_current_user, require_admin
from api.src.models import User, Assessment, Finding, Control, AssessmentControl, Agency
from api.src.schemas import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentListResponse,
    AssessmentSummary,
    AssessmentAssignment,
    AssessmentProgressUpdate
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment_data: AssessmentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new security assessment
    
    Permissions: Analysts, Auditors, Admins
    """
    # Verify user has permission
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if user.role.name not in ["analyst", "auditor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create assessments"
        )
    
    # Create assessment
    assessment = Assessment(
        agency_id=user.agency_id,
        title=assessment_data.title,
        assessment_type=assessment_data.assessment_type,
        framework=assessment_data.framework,
        scope=assessment_data.scope,
        status="planning",
        progress_percentage=0,
        target_completion_date=assessment_data.target_completion_date,
        assessment_period_start=assessment_data.period_start,
        assessment_period_end=assessment_data.period_end,
        metadata_json=assessment_data.metadata or {}
    )
    
    # Assign analyst if specified
    if assessment_data.assigned_to:
        assigned_user = db.query(User).filter(
            User.id == assessment_data.assigned_to,
            User.agency_id == user.agency_id
        ).first()
        if assigned_user:
            assessment.assigned_to = assessment_data.assigned_to
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    logger.info(f"Assessment created: {assessment.id} by user {current_user['id']}")
    
    return assessment


@router.get("/", response_model=List[AssessmentListResponse])
async def list_assessments(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    assessment_type: Optional[str] = Query(None, description="Filter by type"),
    assigned_to_me: bool = Query(False, description="Show only my assignments"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all assessments for the user's agency
    
    Filters:
    - status: open, in_progress, completed, closed
    - assessment_type: vapt, infra_pt, compliance_audit
    - assigned_to_me: show only assessments assigned to current user
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    query = db.query(Assessment).filter(Assessment.agency_id == user.agency_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Assessment.status == status_filter)
    
    if assessment_type:
        query = query.filter(Assessment.assessment_type == assessment_type)
    
    if assigned_to_me:
        query = query.filter(Assessment.assigned_to == current_user["id"])
    
    # Load relationships
    query = query.options(
        joinedload(Assessment.analyst)
    )
    
    assessments = query.order_by(Assessment.created_at.desc()).all()
    
    # Calculate statistics for each assessment
    result = []
    for assessment in assessments:
        findings_count = db.query(Finding).filter(
            Finding.assessment_id == assessment.id
        ).count()
        
        controls_count = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id
        ).count()
        
        result.append({
            "id": assessment.id,
            "title": assessment.title,
            "assessment_type": assessment.assessment_type,
            "framework": assessment.framework,
            "status": assessment.status,
            "progress_percentage": assessment.progress_percentage,
            "assigned_to": assessment.analyst.username if assessment.analyst else None,
            "findings_count": findings_count,
            "controls_tested_count": controls_count,
            "target_completion_date": assessment.target_completion_date,
            "created_at": assessment.created_at
        })
    
    return result


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific assessment"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).options(
        joinedload(Assessment.analyst),
        joinedload(Assessment.agency)
    ).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Get related statistics
    findings = db.query(Finding).filter(Finding.assessment_id == assessment_id).all()
    controls = db.query(AssessmentControl).filter(
        AssessmentControl.assessment_id == assessment_id
    ).all()
    
    # Calculate findings by severity
    findings_by_severity = {
        "critical": len([f for f in findings if f.severity == "critical"]),
        "high": len([f for f in findings if f.severity == "high"]),
        "medium": len([f for f in findings if f.severity == "medium"]),
        "low": len([f for f in findings if f.severity == "low"]),
        "info": len([f for f in findings if f.severity == "info"])
    }
    
    # Calculate resolution status
    resolved_findings = len([f for f in findings if f.resolution_status == "resolved"])
    
    return {
        **assessment.__dict__,
        "findings_count": len(findings),
        "findings_resolved": resolved_findings,
        "findings_by_severity": findings_by_severity,
        "controls_tested_count": len(controls),
        "assigned_to_username": assessment.analyst.username if assessment.analyst else None
    }


@router.patch("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int,
    update_data: AssessmentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assessment details"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check permissions (only assigned analyst, auditors, or admins can update)
    if user.role.name not in ["admin", "super_admin", "auditor"]:
        if assessment.assigned_to != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update assessments assigned to you"
            )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(assessment, key, value)
    
    db.commit()
    db.refresh(assessment)
    
    logger.info(f"Assessment {assessment_id} updated by user {current_user['id']}")
    
    return assessment


@router.post("/{assessment_id}/assign")
async def assign_assessment(
    assessment_id: int,
    assignment: AssessmentAssignment,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign assessment to an analyst"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Only auditors and admins can assign
    if user.role.name not in ["auditor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign assessments"
        )
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Verify assigned user exists and is in same agency
    assigned_user = db.query(User).filter(
        User.id == assignment.assigned_to,
        User.agency_id == user.agency_id
    ).first()
    
    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found or not in same agency"
        )
    
    assessment.assigned_to = assignment.assigned_to
    assessment.status = "in_progress"
    
    db.commit()
    
    logger.info(f"Assessment {assessment_id} assigned to user {assignment.assigned_to}")
    
    return {
        "message": "Assessment assigned successfully",
        "assessment_id": assessment_id,
        "assigned_to": assigned_user.username
    }


@router.patch("/{assessment_id}/progress")
async def update_progress(
    assessment_id: int,
    progress_update: AssessmentProgressUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assessment progress"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Only assigned analyst can update progress
    if assessment.assigned_to != current_user["id"] and user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned analyst can update progress"
        )
    
    assessment.progress_percentage = progress_update.progress_percentage
    
    # Auto-update status based on progress
    if progress_update.progress_percentage == 0:
        assessment.status = "planning"
    elif progress_update.progress_percentage < 100:
        assessment.status = "in_progress"
    else:
        assessment.status = "completed"
        assessment.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Progress updated",
        "progress_percentage": assessment.progress_percentage,
        "status": assessment.status
    }


@router.get("/{assessment_id}/controls", response_model=List[dict])
async def get_assessment_controls(
    assessment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all controls associated with this assessment"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Get assessment controls with control details
    assessment_controls = db.query(AssessmentControl).join(Control).filter(
        AssessmentControl.assessment_id == assessment_id
    ).all()
    
    result = []
    for ac in assessment_controls:
        control = ac.control
        result.append({
            "id": ac.id,
            "control_id": control.id,
            "control_name": control.name,
            "control_type": control.control_type,
            "testing_status": ac.testing_status,
            "testing_priority": ac.testing_priority,
            "review_status": control.review_status,
            "last_tested_at": control.last_tested_at
        })
    
    return result


@router.post("/{assessment_id}/controls")
async def add_controls_to_assessment(
    assessment_id: int,
    control_ids: List[int],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add controls to assessment for testing"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    added = 0
    for control_id in control_ids:
        # Check if control exists and belongs to same agency
        control = db.query(Control).filter(
            Control.id == control_id,
            Control.agency_id == user.agency_id
        ).first()
        
        if not control:
            continue
        
        # Check if already added
        existing = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment_id,
            AssessmentControl.control_id == control_id
        ).first()
        
        if existing:
            continue
        
        # Add control to assessment
        ac = AssessmentControl(
            assessment_id=assessment_id,
            control_id=control_id,
            selected_for_testing=True,
            testing_status="pending",
            testing_priority=999  # Default low priority
        )
        db.add(ac)
        added += 1
    
    db.commit()
    
    return {
        "message": f"{added} controls added to assessment",
        "assessment_id": assessment_id,
        "controls_added": added
    }


@router.get("/{assessment_id}/findings", response_model=List[dict])
async def get_assessment_findings(
    assessment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all findings for this assessment"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    findings = db.query(Finding).filter(
        Finding.assessment_id == assessment_id
    ).all()
    
    result = []
    for finding in findings:
        result.append({
            "id": finding.id,
            "title": finding.title,
            "severity": finding.severity,
            "resolution_status": finding.resolution_status,
            "assigned_to": finding.assigned_to,
            "due_date": finding.due_date,
            "created_at": finding.created_at
        })
    
    return result


@router.post("/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark assessment as complete and generate report"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Only assigned analyst or admin can complete
    if assessment.assigned_to != current_user["id"] and user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned analyst can complete assessment"
        )
    
    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()
    assessment.progress_percentage = 100
    
    db.commit()
    
    # TODO: Trigger report generation
    
    logger.info(f"Assessment {assessment_id} marked as complete")
    
    return {
        "message": "Assessment completed successfully",
        "assessment_id": assessment_id,
        "completed_at": assessment.completed_at
    }


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an assessment (Admin only)"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    db.delete(assessment)
    db.commit()
    
    logger.info(f"Assessment {assessment_id} deleted by admin {current_user['id']}")
    
    return None
