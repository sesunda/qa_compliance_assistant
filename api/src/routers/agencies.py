from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from api.src import models, schemas
from api.src.database import get_db
from api.src.auth import get_current_user

router = APIRouter(prefix="/agencies", tags=["agencies"])


@router.post("/", response_model=schemas.Agency, status_code=status.HTTP_201_CREATED)
def create_agency(
    agency: schemas.AgencyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new agency (admin/super_admin only)"""
    # Check if user has permission to create agencies
    user_role = current_user.get("role")
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create agencies"
        )
    
    # Check if agency with same name or code already exists
    existing = db.query(models.Agency).filter(
        (models.Agency.name == agency.name) | 
        (models.Agency.code == agency.code)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agency with this name or code already exists"
        )
    
    db_agency = models.Agency(**agency.dict())
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    return db_agency


@router.get("/", response_model=list[schemas.Agency])
def list_agencies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all agencies"""
    query = db.query(models.Agency)
    
    if active_only:
        query = query.filter(models.Agency.active == True)
    
    if search:
        query = query.filter(
            (models.Agency.name.ilike(f"%{search}%")) |
            (models.Agency.code.ilike(f"%{search}%")) |
            (models.Agency.description.ilike(f"%{search}%"))
        )
    
    agencies = query.order_by(models.Agency.name.asc()).offset(skip).limit(limit).all()
    return agencies


@router.get("/{agency_id}", response_model=schemas.Agency)
def get_agency(
    agency_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get agency by ID"""
    agency = db.query(models.Agency).filter(models.Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found"
        )
    return agency


@router.put("/{agency_id}", response_model=schemas.Agency)
def update_agency(
    agency_id: int,
    agency_update: schemas.AgencyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an agency (admin/super_admin only)"""
    # Check if user has permission to update agencies
    user_role = current_user.get("role")
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update agencies"
        )
    
    db_agency = db.query(models.Agency).filter(models.Agency.id == agency_id).first()
    if not db_agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found"
        )
    
    # Check for duplicate name/code if being updated
    if agency_update.name or agency_update.code:
        existing = db.query(models.Agency).filter(
            models.Agency.id != agency_id,
            (models.Agency.name == agency_update.name) | 
            (models.Agency.code == agency_update.code)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agency with this name or code already exists"
            )
    
    # Update fields
    update_data = agency_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_agency, field, value)
    
    db.commit()
    db.refresh(db_agency)
    return db_agency


@router.delete("/{agency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agency(
    agency_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an agency (super_admin only)"""
    # Only super_admin can delete agencies
    user_role = current_user.get("role")
    if user_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can delete agencies"
        )
    
    db_agency = db.query(models.Agency).filter(models.Agency.id == agency_id).first()
    if not db_agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found"
        )
    
    # Check if agency has users or projects
    user_count = db.query(models.User).filter(models.User.agency_id == agency_id).count()
    project_count = db.query(models.Project).filter(models.Project.agency_id == agency_id).count()
    
    if user_count > 0 or project_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete agency with {user_count} users and {project_count} projects. Deactivate instead."
        )
    
    db.delete(db_agency)
    db.commit()
    return None


@router.get("/{agency_id}/stats")
def get_agency_stats(
    agency_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics for an agency"""
    agency = db.query(models.Agency).filter(models.Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found"
        )
    
    user_count = db.query(models.User).filter(models.User.agency_id == agency_id).count()
    active_user_count = db.query(models.User).filter(
        models.User.agency_id == agency_id,
        models.User.is_active == True
    ).count()
    
    project_count = db.query(models.Project).filter(models.Project.agency_id == agency_id).count()
    
    return {
        "agency_id": agency_id,
        "agency_name": agency.name,
        "total_users": user_count,
        "active_users": active_user_count,
        "total_projects": project_count
    }
