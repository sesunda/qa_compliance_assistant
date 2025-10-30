from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.src.database import get_db
from api.src import models, schemas

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/", response_model=schemas.Evidence)
def create_evidence(evidence: schemas.EvidenceCreate, db: Session = Depends(get_db)):
    # Verify control exists
    control = db.query(models.Control).filter(models.Control.id == evidence.control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    db_evidence = models.Evidence(**evidence.model_dump())
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.get("/", response_model=List[schemas.Evidence])
def list_evidence(control_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Evidence)
    if control_id:
        query = query.filter(models.Evidence.control_id == control_id)
    evidence = query.offset(skip).limit(limit).all()
    return evidence


@router.get("/{evidence_id}", response_model=schemas.Evidence)
def get_evidence(evidence_id: int, db: Session = Depends(get_db)):
    evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.put("/{evidence_id}", response_model=schemas.Evidence)
def update_evidence(evidence_id: int, evidence: schemas.EvidenceUpdate, db: Session = Depends(get_db)):
    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    for key, value in evidence.model_dump(exclude_unset=True).items():
        setattr(db_evidence, key, value)
    
    db.commit()
    db.refresh(db_evidence)
    return db_evidence


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)):
    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    db.delete(db_evidence)
    db.commit()
    return {"message": "Evidence deleted successfully"}
