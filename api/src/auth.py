"""Authentication and authorization utilities"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from api.src.utils.datetime_utils import now_sgt
import hashlib
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from api.src.config import settings
from api.src.database import get_db
from api.src.models import User, UserRole


# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security scheme
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password using SHA256 (temporary - will upgrade to bcrypt later)"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = now_sgt() + expires_delta
    else:
        expire = now_sgt() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Get the current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.name.lower() if user.role else "user",  # Normalize to lowercase
        "agency_id": user.agency_id,
        "is_active": user.is_active
    }


class RoleChecker:
    """Dependency class for role-based access control"""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user (convenience function)"""
    return current_user


# Role-based access control decorators
require_admin = RoleChecker(["admin", "super_admin"])
require_auditor = RoleChecker(["admin", "super_admin", "auditor"])
require_analyst = RoleChecker(["admin", "super_admin", "auditor", "analyst"])
require_viewer = RoleChecker(["admin", "super_admin", "auditor", "analyst", "viewer"])


def check_agency_access(user: dict, resource_agency_id: int) -> bool:
    """Check if user has access to resources from a specific agency"""
    # Super admin has access to all agencies
    if user["role"] == "super_admin":
        return True
    
    # Other users can only access their own agency's resources
    return user["agency_id"] == resource_agency_id


def require_agency_access(resource_agency_id: int, current_user: dict = Depends(get_current_user)):
    """Dependency to ensure user has access to agency resources"""
    if not check_agency_access(current_user, resource_agency_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: insufficient agency permissions"
        )
    return current_user