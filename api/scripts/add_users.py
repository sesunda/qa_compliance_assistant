"""Add users for testing"""

from api.src.models import User, UserRole, Agency
from api.src.auth import get_password_hash
from api.src.database import SessionLocal

def add_users():
    """Add test users to the system"""
    db = SessionLocal()
    
    try:
        # Get roles
        analyst_role = db.query(UserRole).filter_by(name="analyst").first()
        auditor_role = db.query(UserRole).filter_by(name="auditor").first()
        
        # Create Agency 1 - HSA
        agency1 = db.query(Agency).filter_by(code="HSA").first()
        if not agency1:
            agency1 = Agency(
                name="Health Sciences Authority",
                code="HSA",
                description="National agency for health sciences regulation",
                contact_email="contact@hsa.gov.sg",
                active=True
            )
            db.add(agency1)
            db.commit()
            db.refresh(agency1)
        
        # Create Agency 2 - IRAS
        agency2 = db.query(Agency).filter_by(code="IRAS").first()
        if not agency2:
            agency2 = Agency(
                name="Inland Revenue Authority of Singapore",
                code="IRAS",
                description="Tax administration and revenue collection",
                contact_email="contact@iras.gov.sg",
                active=True
            )
            db.add(agency2)
            db.commit()
            db.refresh(agency2)
        
        # Create Central Audit Office for auditors
        audit_office = db.query(Agency).filter_by(code="CAO").first()
        if not audit_office:
            audit_office = Agency(
                name="Central Audit Office",
                code="CAO",
                description="Independent audit and compliance verification",
                contact_email="audit@cao.gov.sg",
                active=True
            )
            db.add(audit_office)
            db.commit()
            db.refresh(audit_office)
        
        # Common password
        common_password = "Welcome@2025"
        hashed_password = get_password_hash(common_password)
        
        # Define users to create
        users_to_create = [
            # Analysts - Agency-specific
            {
                "username": "alice_analyst",
                "email": "alice@hsa.gov.sg",
                "full_name": "Alice Tan",
                "agency_id": agency1.id,
                "role_id": analyst_role.id
            },
            {
                "username": "bob_analyst",
                "email": "bob@iras.gov.sg",
                "full_name": "Bob Lim",
                "agency_id": agency2.id,
                "role_id": analyst_role.id
            },
            # Auditors - Centralized (can audit across agencies)
            {
                "username": "carol_auditor",
                "email": "carol@cao.gov.sg",
                "full_name": "Carol Chen",
                "agency_id": audit_office.id,
                "role_id": auditor_role.id
            },
            {
                "username": "david_auditor",
                "email": "david@cao.gov.sg",
                "full_name": "David Wong",
                "agency_id": audit_office.id,
                "role_id": auditor_role.id
            }
        ]
        
        print("\n=== Creating Users ===\n")
        
        for user_data in users_to_create:
            # Check if user exists
            existing_user = db.query(User).filter_by(username=user_data["username"]).first()
            if existing_user:
                print(f"⚠️  User {user_data['username']} already exists, skipping...")
                continue
            
            # Create user
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_password,
                agency_id=user_data["agency_id"],
                role_id=user_data["role_id"],
                is_active=True,
                is_verified=True
            )
            db.add(new_user)
            db.commit()
            
            # Get agency and role names for display
            agency = db.query(Agency).filter_by(id=user_data["agency_id"]).first()
            role = db.query(UserRole).filter_by(id=user_data["role_id"]).first()
            
            print(f"✅ Created: {user_data['username']}")
            print(f"   Name: {user_data['full_name']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Agency: {agency.name}")
            print(f"   Role: {role.name}")
            print()
        
        print("\n=== Summary ===")
        print(f"Common Password: {common_password}")
        print("\nAll users created successfully!")
        
        # Print all users
        print("\n=== All Users in System ===\n")
        all_users = db.query(User).all()
        for user in all_users:
            agency = db.query(Agency).filter_by(id=user.agency_id).first()
            role = db.query(UserRole).filter_by(id=user.role_id).first()
            print(f"Username: {user.username:20} | Role: {role.name:15} | Agency: {agency.name}")
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_users()
