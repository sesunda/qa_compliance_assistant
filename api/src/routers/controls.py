from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.src.database import get_db
from api.src import models, schemas

router = APIRouter(prefix="/controls", tags=["controls"])


@router.post("/", response_model=schemas.Control)
def create_control(control: schemas.ControlCreate, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == control.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_control = models.Control(**control.model_dump())
    db.add(db_control)
    db.commit()
    db.refresh(db_control)
    return db_control


@router.get("/", response_model=List[schemas.Control])
def list_controls(project_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Control)
    if project_id:
        query = query.filter(models.Control.project_id == project_id)
    controls = query.offset(skip).limit(limit).all()
    return controls


@router.get("/{control_id}", response_model=schemas.Control)
def get_control(control_id: int, db: Session = Depends(get_db)):
    control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.put("/{control_id}", response_model=schemas.Control)
def update_control(control_id: int, control: schemas.ControlUpdate, db: Session = Depends(get_db)):
    db_control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not db_control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    for key, value in control.model_dump(exclude_unset=True).items():
        setattr(db_control, key, value)
    
    db.commit()
    db.refresh(db_control)
    return db_control


@router.delete("/{control_id}")
def delete_control(control_id: int, db: Session = Depends(get_db)):
    db_control = db.query(models.Control).filter(models.Control.id == control_id).first()
    if not db_control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    db.delete(db_control)
    db.commit()
    return {"message": "Control deleted successfully"}
