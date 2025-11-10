from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from api.src.database import get_db
from api.src import models, schemas
from api.src.auth import get_current_user, require_auditor, require_viewer, check_agency_access

router = APIRouter(prefix="/controls", tags=["controls"])


@router.post("/", response_model=schemas.Control, status_code=status.HTTP_201_CREATED)
def create_control(
    control: schemas.ControlCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Create a new control. Only auditors can create controls."""
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == control.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check agency access
    if not check_agency_access(current_user, project.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Automatically set agency_id from current user
    control_data = control.model_dump()
    control_data["agency_id"] = current_user["agency_id"]
    
    db_control = models.Control(**control_data)
    db.add(db_control)
    db.commit()
    db.refresh(db_control)
    return db_control


@router.get("/", response_model=List[schemas.Control])
def list_controls(
    project_id: int = None,
    agency_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    """List controls. Users see only their agency's controls (except super_admin)."""
    query = db.query(models.Control)
    
    # Filter by agency unless super_admin
    if current_user.get("role") != "super_admin":
        query = query.filter(models.Control.agency_id == current_user["agency_id"])
    elif agency_id:
        # Super admin can filter by specific agency
        query = query.filter(models.Control.agency_id == agency_id)
    
    if project_id:
        query = query.filter(models.Control.project_id == project_id)
    
    controls = query.offset(skip).limit(limit).all()
    return controls


@router.get("/{control_id}", response_model=schemas.Control)
def get_control(
    control_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    """Get a specific control. Must belong to user's agency."""
    control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Check agency access
    if not check_agency_access(current_user, control.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return control


@router.put("/{control_id}", response_model=schemas.Control)
def update_control(
    control_id: int,
    control: schemas.ControlUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Update a control. Only auditors can update controls from their agency."""
    db_control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not db_control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Check agency access
    if not check_agency_access(current_user, db_control.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    for key, value in control.model_dump(exclude_unset=True).items():
        setattr(db_control, key, value)
    
    db.commit()
    db.refresh(db_control)
    return db_control


@router.delete("/{control_id}")
def delete_control(
    control_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Delete a control. Only auditors can delete controls from their agency."""
    db_control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not db_control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Check agency access
    if not check_agency_access(current_user, db_control.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    db.delete(db_control)
    db.commit()
    return {"message": "Control deleted successfully"}


# New Control Testing Workflow Endpoints

@router.post("/{control_id}/test")
async def test_control(
    control_id: int,
    test_data: schemas.ControlTestCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a control test execution"""
    user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
    
    control = db.query(models.Control).filter(
        models.Control.id == control_id,
        models.Control.agency_id == user.agency_id
    ).first()
    
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )
    
    # Update control testing information
    control.last_tested_at = datetime.utcnow()
    control.review_status = test_data.test_result  # passed, failed, not_applicable
    control.reviewed_by = current_user["id"]
    
    if test_data.assessment_score is not None:
        control.assessment_score = test_data.assessment_score
    
    if test_data.test_notes:
        # Store test notes in metadata
        if not control.metadata_json:
            control.metadata_json = {}
        control.metadata_json["last_test_notes"] = test_data.test_notes
    
    db.commit()
    
    return {
        "message": "Control test recorded",
        "control_id": control_id,
        "test_result": test_data.test_result,
        "tested_at": control.last_tested_at
    }


@router.post("/{control_id}/review")
async def review_control(
    control_id: int,
    review_data: schemas.ControlReviewCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a control design review"""
    user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
    
    # Only auditors can review controls
    if user.role.name not in ["auditor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to review controls"
        )
    
    control = db.query(models.Control).filter(
        models.Control.id == control_id,
        models.Control.agency_id == user.agency_id
    ).first()
    
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )
    
    control.review_status = review_data.review_status  # approved, needs_improvement, rejected
    control.reviewed_by = current_user["id"]
    
    if review_data.review_notes:
        if not control.metadata_json:
            control.metadata_json = {}
        control.metadata_json["review_notes"] = review_data.review_notes
        control.metadata_json["reviewed_at"] = datetime.utcnow().isoformat()
    
    db.commit()
    
    return {
        "message": "Control review submitted",
        "control_id": control_id,
        "review_status": control.review_status
    }


@router.patch("/{control_id}/test-procedure")
async def update_test_procedure(
    control_id: int,
    procedure_data: schemas.ControlTestProcedureUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update control test procedure and frequency"""
    user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
    
    control = db.query(models.Control).filter(
        models.Control.id == control_id,
        models.Control.agency_id == user.agency_id
    ).first()
    
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )
    
    if procedure_data.test_procedure is not None:
        control.test_procedure = procedure_data.test_procedure
    
    if procedure_data.testing_frequency is not None:
        control.testing_frequency = procedure_data.testing_frequency
    
    db.commit()
    
    return {
        "message": "Test procedure updated",
        "control_id": control_id
    }


@router.get("/{control_id}/testing-history")
async def get_testing_history(
    control_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get testing history for a control"""
    user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
    
    control = db.query(models.Control).options(
        joinedload(models.Control.reviewed_by_user)
    ).filter(
        models.Control.id == control_id,
        models.Control.agency_id == user.agency_id
    ).first()
    
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )
    
    return {
        "control_id": control_id,
        "control_name": control.name,
        "last_tested_at": control.last_tested_at,
        "review_status": control.review_status,
        "assessment_score": control.assessment_score,
        "testing_frequency": control.testing_frequency,
        "reviewed_by": control.reviewed_by_user.username if control.reviewed_by_user else None,
        "test_notes": control.metadata_json.get("last_test_notes") if control.metadata_json else None,
        "review_notes": control.metadata_json.get("review_notes") if control.metadata_json else None
    }
