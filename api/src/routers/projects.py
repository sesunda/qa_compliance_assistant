from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api.src.database import get_db
from api.src import models, schemas
from api.src.auth import require_auditor, require_viewer, check_agency_access

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Create a new project. Only auditors can create projects."""
    # Automatically set agency_id from current user's JWT token
    project_data = project.model_dump()
    project_data["agency_id"] = current_user["agency_id"]
    
    db_project = models.Project(**project_data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[schemas.Project])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    """List projects. Users see only their agency's projects (except super_admin)."""
    query = db.query(models.Project)
    
    # Filter by agency unless super_admin
    if current_user.get("role") != "super_admin":
        query = query.filter(models.Project.agency_id == current_user["agency_id"])
    
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=schemas.Project)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_viewer)
):
    """Get a specific project. Must belong to user's agency."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check agency access
    if not check_agency_access(current_user, project.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    project: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Update a project. Only auditors can update projects from their agency."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check agency access
    if not check_agency_access(current_user, db_project.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    for key, value in project.model_dump(exclude_unset=True).items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)
):
    """Delete a project. Only auditors can delete projects from their agency."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check agency access
    if not check_agency_access(current_user, db_project.agency_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted successfully"}
