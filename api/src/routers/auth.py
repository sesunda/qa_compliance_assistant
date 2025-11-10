"""Authentication and user management routes"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from api.src.database import get_db
from api.src import models
from api.src.auth_schemas import (
    LoginRequest, Token, User, UserCreate, UserUpdate, CurrentUser, AgencySummary,
    PasswordChange, UserRole, UserRoleCreate
)
from api.src.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_admin, require_auditor, require_analyst,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    # Find user by username or email
    user = db.query(models.User).filter(
        (models.User.username == login_data.username) | 
        (models.User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Get user with role information
    user_with_role = db.query(models.User).filter(models.User.id == user.id).first()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "agency_id": user.agency_id,
            "role_id": user.role_id,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role": {
                "id": user_with_role.role.id,
                "name": user_with_role.role.name,
                "description": user_with_role.role.description,
                "permissions": user_with_role.role.permissions,
                "created_at": user_with_role.role.created_at
            } if user_with_role.role else None,
            "agency": {
                "id": user_with_role.agency.id,
                "name": user_with_role.agency.name,
                "code": user_with_role.agency.code,
                "description": user_with_role.agency.description,
                "contact_email": user_with_role.agency.contact_email
            } if user_with_role.agency else None
        }
    }


@router.get("/me", response_model=CurrentUser)
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    from sqlalchemy.orm import joinedload
    
    user_record = db.query(models.User).options(
        joinedload(models.User.role),
        joinedload(models.User.agency)
    ).filter(models.User.id == current_user["id"]).first()

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    permissions = user_record.role.permissions if user_record.role else None

    return {
        **User.model_validate(user_record).model_dump(),
        "permissions": permissions
    }


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
    
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


# User management routes (Admin only)
@router.post("/users", response_model=User)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new user (Admin only)"""
    # Check if username or email already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) |
        (models.User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Verify agency exists
    agency = db.query(models.Agency).filter(models.Agency.id == user_data.agency_id).first()
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found"
        )
    
    # Verify role exists
    role = db.query(models.UserRole).filter(models.UserRole.id == user_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        agency_id=user_data.agency_id,
        role_id=user_data.role_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/users", response_model=list[User])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)
):
    """List all users (Analyst+ access - analysts, auditors, admins can view users)"""
    query = db.query(models.User)
    
    # Non-super-admin users can only see users from their agency
    if current_user["role"] != "super_admin":
        query = query.filter(models.User.agency_id == current_user["agency_id"])
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)
):
    """Get specific user (Analyst+ access)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check agency access
    if current_user["role"] != "super_admin" and user.agency_id != current_user["agency_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return user


@router.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update user (Admin only)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check agency access
    if current_user["role"] != "super_admin" and user.agency_id != current_user["agency_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/agencies", response_model=list[AgencySummary])
def list_agencies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)
):
    """List agencies (Analyst+ access - users can see their own agency, super_admin sees all)"""
    query = db.query(models.Agency)

    if current_user["role"] != "super_admin":
        query = query.filter(models.Agency.id == current_user["agency_id"])

    agencies = query.order_by(models.Agency.name.asc()).all()
    return agencies


# Role management routes
@router.post("/roles", response_model=UserRole)
def create_role(
    role_data: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new user role (Admin only)"""
    # Check if role name already exists
    existing_role = db.query(models.UserRole).filter(models.UserRole.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )
    
    db_role = models.UserRole(**role_data.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    return db_role


@router.get("/roles", response_model=list[UserRole])
def list_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all user roles"""
    roles = db.query(models.UserRole).all()
    return roles