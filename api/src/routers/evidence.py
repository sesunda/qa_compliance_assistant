from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.src import models, schemas
from api.src.auth import require_auditor, require_viewer, require_analyst, check_agency_access
from api.src.database import get_db
from api.src.services.evidence_storage import evidence_storage_service
from api.src.services.excel_processor import get_excel_processor
from api.src.services.im8_validator import get_im8_validator
from api.src.utils.datetime_utils import now_sgt


router = APIRouter(prefix="/evidence", tags=["evidence"])


# Maker-Checker workflow schemas
class SubmitForReviewRequest(BaseModel):
    comments: Optional[str] = None


class ApproveEvidenceRequest(BaseModel):
    comments: Optional[str] = None


class RejectEvidenceRequest(BaseModel):
    comments: str  # Required for rejection


def _get_control(db: Session, control_id: int) -> models.Control:
    control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    return control


def _get_evidence(db: Session, evidence_id: int) -> models.Evidence:
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


@router.post("/upload", response_model=schemas.Evidence, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    control_id: int = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)
):
    """Upload a new evidence file and persist metadata. Only analysts can upload evidence."""

    control = _get_control(db, control_id)

    if not check_agency_access(current_user, control.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    storage_meta = await evidence_storage_service.save_file(
        upload_file=file,
        agency_id=control.agency_id,
        control_id=control.id
    )

    # Initialize metadata_json and verification status
    metadata_json = None
    verification_status = "pending"
    
    # IM8 Assessment Document processing
    if evidence_type == "im8_assessment_document":
        try:
            # Read file content for parsing
            file_path = evidence_storage_service.resolve_file_path(storage_meta["relative_path"])
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Parse IM8 Excel document
            excel_processor = get_excel_processor()
            parsed_data = excel_processor.parse_im8_document(file_content, file.filename)
            
            # Validate IM8 structure
            validator = get_im8_validator()
            is_valid, validation_errors = validator.validate_im8_document(parsed_data, strict_mode=False)
            
            # Calculate completion stats
            completion_stats = excel_processor.calculate_completion_stats(parsed_data)
            parsed_data["completion_stats"] = completion_stats
            
            # Store validation results
            parsed_data["validation"] = {
                "is_valid": is_valid,
                "errors": validation_errors,
                "validated_at": now_sgt().isoformat()
            }
            
            # Store parsed data in metadata_json
            metadata_json = parsed_data
            
            # Auto-submit to "under_review" for valid IM8 documents
            if is_valid:
                verification_status = "under_review"
            else:
                # If validation errors, keep in pending with error details
                verification_status = "pending"
                
        except Exception as e:
            # If parsing/validation fails, store error in metadata
            metadata_json = {
                "evidence_type": "im8_assessment_document",
                "processing_error": str(e),
                "processed_at": now_sgt().isoformat()
            }

    db_evidence = models.Evidence(
        control_id=control.id,
        agency_id=control.agency_id,
        title=title or (file.filename or "Uploaded Evidence"),
        description=description,
        evidence_type=evidence_type,
        file_path=storage_meta["relative_path"],
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size=storage_meta["file_size"],
        checksum=storage_meta["checksum"],
        storage_backend=storage_meta["storage_backend"],
        uploaded_by=current_user["id"],
        submitted_by=current_user["id"],  # Maker-checker: Set submitter
        verification_status=verification_status,
        metadata_json=metadata_json,  # Store parsed IM8 data
    )

    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.post("/", response_model=schemas.Evidence)
def create_evidence(
    evidence: schemas.EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)
):
    """Create an evidence record without uploading a file. Only analysts can create evidence."""

    control = _get_control(db, evidence.control_id)
    if not check_agency_access(current_user, control.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db_evidence = models.Evidence(
        control_id=control.id,
        agency_id=control.agency_id,
        title=evidence.title,
        description=evidence.description,
        evidence_type=evidence.evidence_type,
        verified=evidence.verified,
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.get("/", response_model=List[schemas.Evidence])
def list_evidence(
    control_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    query = db.query(models.Evidence)

    if current_user["role"] != "super_admin":
        query = query.filter(models.Evidence.agency_id == current_user["agency_id"])

    if control_id is not None:
        query = query.filter(models.Evidence.control_id == control_id)

    evidence_items = query.order_by(models.Evidence.created_at.desc()).offset(skip).limit(limit).all()
    return evidence_items


@router.get("/{evidence_id}", response_model=schemas.Evidence)
def get_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return evidence


@router.get("/{evidence_id}/download")
def download_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    evidence = _get_evidence(db, evidence_id)

    if not evidence.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found")

    if not check_agency_access(current_user, evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        file_path = evidence_storage_service.resolve_file_path(evidence.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found") from None

    filename = evidence.original_filename or Path(file_path).name
    media_type = evidence.mime_type or "application/octet-stream"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)


@router.put("/{evidence_id}", response_model=schemas.Evidence)
def update_evidence(
    evidence_id: int,
    evidence: schemas.EvidenceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    db_evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, db_evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    for key, value in evidence.model_dump(exclude_unset=True).items():
        setattr(db_evidence, key, value)

    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.delete("/{evidence_id}")
def delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    db_evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, db_evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if db_evidence.file_path:
        evidence_storage_service.delete_file(db_evidence.file_path)

    db.delete(db_evidence)
    db.commit()
    return {"message": "Evidence deleted successfully"}


# ============================================================================
# MAKER-CHECKER WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/{evidence_id}/submit-for-review", response_model=schemas.Evidence)
def submit_evidence_for_review(
    evidence_id: int,
    request: SubmitForReviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)
):
    """
    Submit evidence for review (Maker action).
    Analysts can submit their own evidence for auditor review.
    """
    db_evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, db_evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check current status
    if db_evidence.verification_status not in ['pending', 'rejected']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evidence cannot be submitted from {db_evidence.verification_status} status"
        )

    # Update status
    db_evidence.verification_status = 'under_review'
    db_evidence.submitted_by = current_user["id"]
    if request.comments:
        db_evidence.review_comments = request.comments

    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.post("/{evidence_id}/approve", response_model=schemas.Evidence)
def approve_evidence(
    evidence_id: int,
    request: ApproveEvidenceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """
    Approve evidence (Checker action).
    Auditors can approve evidence submitted for review.
    Segregation of duties: Cannot approve own submissions.
    """
    db_evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, db_evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check current status
    if db_evidence.verification_status != 'under_review':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evidence must be 'under_review' to approve. Current status: {db_evidence.verification_status}"
        )

    # Segregation of duties: Cannot approve own submission
    if db_evidence.submitted_by == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve evidence you submitted (segregation of duties)"
        )

    # Approve evidence
    db_evidence.verification_status = 'approved'
    db_evidence.verified = True
    db_evidence.reviewed_by = current_user["id"]
    db_evidence.reviewed_at = now_sgt()
    if request.comments:
        db_evidence.review_comments = request.comments

    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.post("/{evidence_id}/reject", response_model=schemas.Evidence)
def reject_evidence(
    evidence_id: int,
    request: RejectEvidenceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """
    Reject evidence (Checker action).
    Auditors can reject evidence with mandatory comments.
    """
    db_evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, db_evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check current status
    if db_evidence.verification_status != 'under_review':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evidence must be 'under_review' to reject. Current status: {db_evidence.verification_status}"
        )

    # Reject evidence
    db_evidence.verification_status = 'rejected'
    db_evidence.verified = False
    db_evidence.reviewed_by = current_user["id"]
    db_evidence.reviewed_at = now_sgt()
    db_evidence.review_comments = request.comments

    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.get("/{evidence_id}/review-history")
def get_evidence_review_history(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    """
    Get review history for evidence including submitter and reviewer details.
    """
    db_evidence = _get_evidence(db, evidence_id)

    if not check_agency_access(current_user, db_evidence.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Get user details
    submitter = None
    if db_evidence.submitted_by:
        submitter_user = db.query(models.User).filter(models.User.id == db_evidence.submitted_by).first()
        if submitter_user:
            submitter = {
                "id": submitter_user.id,
                "username": submitter_user.username,
                "full_name": submitter_user.full_name
            }

    reviewer = None
    if db_evidence.reviewed_by:
        reviewer_user = db.query(models.User).filter(models.User.id == db_evidence.reviewed_by).first()
        if reviewer_user:
            reviewer = {
                "id": reviewer_user.id,
                "username": reviewer_user.username,
                "full_name": reviewer_user.full_name
            }

    uploader = None
    if db_evidence.uploaded_by:
        uploader_user = db.query(models.User).filter(models.User.id == db_evidence.uploaded_by).first()
        if uploader_user:
            uploader = {
                "id": uploader_user.id,
                "username": uploader_user.username,
                "full_name": uploader_user.full_name
            }

    return {
        "evidence_id": db_evidence.id,
        "verification_status": db_evidence.verification_status,
        "verified": db_evidence.verified,
        "review_comments": db_evidence.review_comments,
        "uploader": uploader,
        "uploaded_at": db_evidence.uploaded_at,
        "submitter": submitter,
        "reviewer": reviewer,
        "reviewed_at": db_evidence.reviewed_at,
        "created_at": db_evidence.created_at,
        "updated_at": db_evidence.updated_at
    }
