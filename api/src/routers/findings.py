"""
Finding Management API
Endpoints for creating, managing, and tracking security findings through their lifecycle
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta
from api.src.utils.datetime_utils import now_sgt

from api.src.database import get_db
from api.src.auth import get_current_user, require_admin
from api.src.models import User, Finding, FindingComment, Assessment, Control
from api.src.schemas import (
    FindingCreate,
    FindingUpdate,
    FindingResponse,
    FindingListResponse,
    FindingAssignment,
    FindingResolution,
    FindingCommentCreate,
    FindingCommentResponse,
    FindingValidation
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/findings", tags=["findings"])


@router.post("/", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def create_finding(
    finding_data: FindingCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new comprehensive security finding
    
    Permissions: Analysts, Auditors, Admins
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if user.role_id not in [7, 8, 1]:  # analyst=7, auditor=8, super_admin=1
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create findings"
        )
    
    # Verify assessment exists and belongs to user's agency
    assessment = db.query(Assessment).filter(
        Assessment.id == finding_data.assessment_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Verify control if provided
    if finding_data.control_id:
        control = db.query(Control).filter(
            Control.id == finding_data.control_id,
            Control.agency_id == user.agency_id
        ).first()
        if not control:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Control not found"
            )
    
    # Create comprehensive finding
    finding = Finding(
        assessment_id=finding_data.assessment_id,
        project_id=finding_data.project_id,
        agency_id=user.agency_id,
        control_id=finding_data.control_id,
        title=finding_data.title,
        description=finding_data.description,
        severity=finding_data.severity,
        cvss_score=finding_data.cvss_score,
        category=finding_data.category,
        affected_asset=finding_data.affected_asset,
        affected_url=finding_data.affected_url,
        affected_component=finding_data.affected_component,
        reproduction_steps=finding_data.reproduction_steps,
        proof_of_concept=finding_data.proof_of_concept,
        evidence_file_paths=finding_data.evidence_file_paths or [],
        business_impact=finding_data.business_impact,
        likelihood=finding_data.likelihood,
        remediation_recommendation=finding_data.remediation_recommendation,
        remediation_complexity=finding_data.remediation_complexity,
        remediation_priority=finding_data.remediation_priority,
        estimated_effort_hours=finding_data.estimated_effort_hours,
        status=finding_data.status,
        assigned_to_user_id=finding_data.assigned_to_user_id,
        due_date=finding_data.due_date or (now_sgt() + timedelta(days=30)).date(),
        resolution_description=finding_data.resolution_description,
        resolution_verification_evidence=finding_data.resolution_verification_evidence,
        created_by_user_id=current_user["id"]
    )
    
    db.add(finding)
    db.commit()
    db.refresh(finding)
    
    # Update assessment findings count by severity
    assessment.findings_count_critical = db.query(Finding).filter(
        Finding.assessment_id == assessment.id,
        Finding.severity == "critical"
    ).count()
    assessment.findings_count_high = db.query(Finding).filter(
        Finding.assessment_id == assessment.id,
        Finding.severity == "high"
    ).count()
    assessment.findings_count_medium = db.query(Finding).filter(
        Finding.assessment_id == assessment.id,
        Finding.severity == "medium"
    ).count()
    assessment.findings_count_low = db.query(Finding).filter(
        Finding.assessment_id == assessment.id,
        Finding.severity == "low"
    ).count()
    db.commit()
    
    logger.info(f"Finding created: {finding.id} by user {current_user['id']}")
    
    return finding


@router.get("/", response_model=List[FindingListResponse])
async def list_findings(
    assessment_id: Optional[int] = Query(None, description="Filter by assessment"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to_me: bool = Query(False, description="Show only my assignments"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all findings for the user's agency
    
    Filters:
    - assessment_id: Filter by assessment
    - severity: critical, high, medium, low, info
    - status: open, in_progress, resolved, validated, closed
    - assigned_to_me: show only findings assigned to current user
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Base query: join with assessment to filter by agency
    query = db.query(Finding).join(Assessment).filter(
        Assessment.agency_id == user.agency_id
    )
    
    # Apply filters
    if assessment_id:
        query = query.filter(Finding.assessment_id == assessment_id)
    
    if severity:
        query = query.filter(Finding.severity == severity)
    
    if status:
        query = query.filter(Finding.status == status)
    
    if assigned_to_me:
        query = query.filter(Finding.assigned_to_user_id == current_user["id"])
    
    # Load relationships
    query = query.options(
        joinedload(Finding.assigned_to),
        joinedload(Finding.assessment)
    )
    
    findings = query.order_by(
        Finding.severity.desc(),
        Finding.created_at.desc()
    ).all()
    
    result = []
    for finding in findings:
        result.append({
            "id": finding.id,
            "title": finding.title,
            "severity": finding.severity,
            "priority": finding.remediation_priority or "planned",
            "resolution_status": finding.status,
            "assigned_to": finding.assigned_to.username if finding.assigned_to else None,
            "due_date": finding.target_remediation_date,
            "assessment_title": finding.assessment.name,
            "created_at": finding.created_at,
            "false_positive": finding.status == "false_positive"
        })
    
    return result


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific finding"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    finding = db.query(Finding).join(Assessment).options(
        joinedload(Finding.assigned_to),
        joinedload(Finding.resolver),
        joinedload(Finding.validator),
        joinedload(Finding.assessment),
        joinedload(Finding.control)
    ).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    # Get comments count
    comments_count = db.query(FindingComment).filter(
        FindingComment.finding_id == finding_id
    ).count()
    
    return {
        **finding.__dict__,
        "assigned_to_username": finding.assigned_to.username if finding.assigned_to else None,
        "resolved_by_username": finding.resolver.username if finding.resolver else None,
        "validated_by_username": finding.validator.username if finding.validator else None,
        "assessment_title": finding.assessment.title,
        "control_name": finding.control.name if finding.control else None,
        "comments_count": comments_count
    }


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: int,
    update_data: FindingUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update finding details"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    # Check permissions (only assigned analyst, auditors, or admins can update)
    if user.role.name not in ["admin", "super_admin", "auditor"]:
        if finding.assigned_to_user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update findings assigned to you"
            )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(finding, key, value)
    
    db.commit()
    db.refresh(finding)
    
    logger.info(f"Finding {finding_id} updated by user {current_user['id']}")
    
    return finding


@router.post("/{finding_id}/assign")
async def assign_finding(
    finding_id: int,
    assignment: FindingAssignment,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign finding to an analyst for remediation"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Only auditors and admins can assign
    if user.role.name not in ["auditor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign findings"
        )
    
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
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
    
    finding.assigned_to_user_id = assignment.assigned_to
    finding.status = "in_progress"
    
    db.commit()
    
    logger.info(f"Finding {finding_id} assigned to user {assignment.assigned_to}")
    
    return {
        "message": "Finding assigned successfully",
        "finding_id": finding_id,
        "assigned_to": assigned_user.username
    }


@router.post("/{finding_id}/resolve")
async def resolve_finding(
    finding_id: int,
    resolution: FindingResolution,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark finding as resolved with remediation notes"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    # Only assigned analyst can resolve
    if finding.assigned_to_user_id != current_user["id"] and user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned analyst can resolve this finding"
        )
    
    finding.status = "resolved"
    finding.resolved_by = current_user["id"]
    finding.resolved_at = now_sgt()
    finding.remediation_notes = resolution.remediation_notes
    
    # Add resolution comment
    comment = FindingComment(
        finding_id=finding_id,
        user_id=current_user["id"],
        comment_type="resolution",
        comment_text=f"Finding resolved: {resolution.remediation_notes}"
    )
    db.add(comment)
    
    db.commit()
    
    logger.info(f"Finding {finding_id} resolved by user {current_user['id']}")
    
    return {
        "message": "Finding marked as resolved",
        "finding_id": finding_id,
        "resolved_at": finding.resolved_at
    }


@router.post("/{finding_id}/validate")
async def validate_finding(
    finding_id: int,
    validation: FindingValidation,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a resolved finding (QA process)"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Only auditors can validate
    if user.role.name not in ["auditor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to validate findings"
        )
    
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    if finding.status != "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding must be in 'resolved' status to validate"
        )
    
    if validation.approved:
        finding.status = "validated"
        finding.validated_by = current_user["id"]
        finding.validated_at = now_sgt()
        comment_text = f"Finding validated: {validation.validation_notes or 'Approved'}"
    else:
        # Reject validation, send back to in_progress
        finding.status = "in_progress"
        comment_text = f"Validation rejected: {validation.validation_notes}"
    
    # Add validation comment
    comment = FindingComment(
        finding_id=finding_id,
        user_id=current_user["id"],
        comment_type="validation",
        comment_text=comment_text
    )
    db.add(comment)
    
    db.commit()
    
    logger.info(f"Finding {finding_id} validation by user {current_user['id']}: {validation.approved}")
    
    return {
        "message": "Validation complete",
        "finding_id": finding_id,
        "approved": validation.approved,
        "status": finding.status
    }


@router.post("/{finding_id}/mark-false-positive")
async def mark_false_positive(
    finding_id: int,
    justification: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark finding as false positive"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Only auditors can mark false positives
    if user.role.name not in ["auditor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to mark false positives"
        )
    
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    finding.false_positive = True
    finding.status = "closed"
    finding.validated_by = current_user["id"]
    finding.validated_at = now_sgt()
    
    # Add comment
    comment = FindingComment(
        finding_id=finding_id,
        user_id=current_user["id"],
        comment_type="false_positive",
        comment_text=f"Marked as false positive: {justification}"
    )
    db.add(comment)
    
    db.commit()
    
    logger.info(f"Finding {finding_id} marked as false positive by user {current_user['id']}")
    
    return {
        "message": "Finding marked as false positive",
        "finding_id": finding_id
    }


@router.get("/{finding_id}/comments", response_model=List[FindingCommentResponse])
async def get_finding_comments(
    finding_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all comments for a finding"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Verify finding exists and user has access
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    comments = db.query(FindingComment).options(
        joinedload(FindingComment.user)
    ).filter(
        FindingComment.finding_id == finding_id
    ).order_by(FindingComment.created_at.desc()).all()
    
    return [
        {
            "id": comment.id,
            "finding_id": comment.finding_id,
            "user_id": comment.user_id,
            "username": comment.user.username,
            "comment_type": comment.comment_type,
            "comment_text": comment.comment_text,
            "created_at": comment.created_at
        }
        for comment in comments
    ]


@router.post("/{finding_id}/comments", response_model=FindingCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_finding_comment(
    finding_id: int,
    comment_data: FindingCommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a finding"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Verify finding exists and user has access
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    comment = FindingComment(
        finding_id=finding_id,
        user_id=current_user["id"],
        comment_type=comment_data.comment_type,
        comment_text=comment_data.comment_text
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return {
        "id": comment.id,
        "finding_id": comment.finding_id,
        "user_id": comment.user_id,
        "username": user.username,
        "comment_type": comment.comment_type,
        "comment_text": comment.comment_text,
        "created_at": comment.created_at
    }


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(
    finding_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a finding (Admin only)"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    finding = db.query(Finding).join(Assessment).filter(
        Finding.id == finding_id,
        Assessment.agency_id == user.agency_id
    ).first()
    
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )
    
    db.delete(finding)
    db.commit()
    
    logger.info(f"Finding {finding_id} deleted by admin {current_user['id']}")
    
    return None
