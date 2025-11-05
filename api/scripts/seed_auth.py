"""Seed authentication system with default roles and admin user"""

from api.src.models import UserRole, User, Agency
from api.src.auth import get_password_hash

# Default roles with permissions
default_roles = [
    {
        "name": "super_admin",
        "description": "Super administrator with full system access",
        "permissions": {
            "users": ["create", "read", "update", "delete"],
            "agencies": ["create", "read", "update", "delete"],
            "projects": ["create", "read", "update", "delete"],
            "controls": ["create", "read", "update", "delete"],
            "evidence": ["create", "read", "update", "delete"],
            "reports": ["create", "read", "update", "delete"],
            "system": ["configure", "monitor", "backup"]
        }
    },
    {
        "name": "admin",
        "description": "Agency administrator",
        "permissions": {
            "users": ["create", "read", "update"],
            "projects": ["create", "read", "update", "delete"],
            "controls": ["create", "read", "update", "delete"],
            "evidence": ["create", "read", "update", "delete"],
            "reports": ["create", "read", "update", "delete"]
        }
    },
    {
        "name": "auditor",
        "description": "Compliance auditor",
        "permissions": {
            "projects": ["read"],
            "controls": ["read", "update"],
            "evidence": ["create", "read", "update"],
            "reports": ["create", "read"]
        }
    },
    {
        "name": "analyst",
        "description": "Compliance analyst",
        "permissions": {
            "projects": ["read"],
            "controls": ["read"],
            "evidence": ["create", "read"],
            "reports": ["read"]
        }
    },
    {
        "name": "viewer",
        "description": "Read-only access",
        "permissions": {
            "projects": ["read"],
            "controls": ["read"],
            "evidence": ["read"],
            "reports": ["read"]
        }
    }
]


def seed_auth_system():
    """Seed the authentication system with default data"""
    from api.src.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Create default roles
        for role_data in default_roles:
            existing_role = db.query(UserRole).filter_by(name=role_data["name"]).first()
            if not existing_role:
                role = UserRole(
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"]
                )
                db.add(role)
        
        db.commit()
        
        # Get or create default agency
        default_agency = db.query(Agency).filter_by(name="Default Agency").first()
        if not default_agency:
            default_agency = Agency(
                name="Default Agency",
                code="DEFAULT",
                description="Default agency for system administration",
                contact_email="admin@qca.com",
                active=True
            )
            db.add(default_agency)
            db.commit()
            db.refresh(default_agency)
        
        # Get super_admin role
        super_admin_role = db.query(UserRole).filter_by(name="super_admin").first()
        
        # Create default admin user if it doesn't exist
        admin_user = db.query(User).filter_by(username="admin").first()
        if not admin_user:
            admin_password = "admin123"  # Shorter password
            admin_user = User(
                username="admin",
                email="admin@qca.com",
                full_name="System Administrator",
                hashed_password=get_password_hash(admin_password),
                agency_id=default_agency.id,
                role_id=super_admin_role.id,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            
            print("Created default admin user:")
            print("Username: admin")
            print("Password: admin123")
            print("⚠️  IMPORTANT: Change the default password after first login!")
        
        print("Authentication system seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding authentication system: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_auth_system()