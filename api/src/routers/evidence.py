from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.src import models, schemas
from api.src.auth import require_auditor, require_viewer, check_agency_access
from api.src.database import get_db
from api.src.services.evidence_storage import evidence_storage_service


router = APIRouter(prefix="/evidence", tags=["evidence"])


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
    current_user: dict = Depends(require_auditor)
):
    """Upload a new evidence file and persist metadata."""

    control = _get_control(db, control_id)

    if not check_agency_access(current_user, control.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    storage_meta = await evidence_storage_service.save_file(
        upload_file=file,
        agency_id=control.agency_id,
        control_id=control.id
    )

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
    )

    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.post("/", response_model=schemas.Evidence)
def create_evidence(
    evidence: schemas.EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Create an evidence record without uploading a file."""

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
