from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from api.src.database import get_db
from api.src import models, schemas

router: APIRouter = APIRouter(prefix="/control-catalog", tags=["control_catalog"])


@router.post("/propose", response_model=schemas.ControlCatalog)
def propose_control_catalog(entry: schemas.ControlCatalogCreate, db: Session = Depends(get_db)):
    # Try to resolve proposed domain code to an id
    proposed_domain_id = None
    if entry.proposed_domain_code:
        domain = db.query(models.IM8DomainArea).filter(models.IM8DomainArea.code == entry.proposed_domain_code).first()
        if domain:
            proposed_domain_id = domain.id

    # If external_id is provided, try to find existing catalog entry and update it
    db_entry = None
    if entry.external_id:
        db_entry = db.query(models.ControlCatalog).filter(models.ControlCatalog.external_id == entry.external_id).first()

    if db_entry is None:
        db_entry = models.ControlCatalog(
            external_id=entry.external_id,
            title=entry.title,
            description=entry.description,
            family=entry.family,
            raw_json=entry.raw_json,
            proposed_domain_id=proposed_domain_id,
            proposed_confidence=str(entry.proposed_confidence) if entry.proposed_confidence is not None else None,
            mapping_rationale=entry.mapping_rationale,
        )
        db.add(db_entry)
    else:
        # update fields
        db_entry.title = entry.title
        db_entry.description = entry.description
        db_entry.family = entry.family
        db_entry.raw_json = entry.raw_json
        db_entry.proposed_domain_id = proposed_domain_id
        db_entry.proposed_confidence = str(entry.proposed_confidence) if entry.proposed_confidence is not None else None
        db_entry.mapping_rationale = entry.mapping_rationale

    db.commit()
    db.refresh(db_entry)
    return db_entry


@router.get("/", response_model=List[schemas.ControlCatalog])
def list_control_catalog(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(models.ControlCatalog).offset(skip).limit(limit).all()
    return items


@router.post("/{catalog_id}/approve", response_model=schemas.ControlCatalog)
def approve_catalog(catalog_id: int, approved_domain_code: str = Body(...), approved_by: Optional[str] = Body(None), db: Session = Depends(get_db)):
    item = db.query(models.ControlCatalog).filter(models.ControlCatalog.id == catalog_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Catalog entry not found")

    domain = db.query(models.IM8DomainArea).filter(models.IM8DomainArea.code == approved_domain_code).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain code not found")

    item.approved_domain_id = domain.id
    item.approved_by = approved_by
    from datetime import datetime
    item.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item
