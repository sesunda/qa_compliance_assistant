#!/usr/bin/env python3
"""Seed test data: 2 agencies, roles, and users"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '/workspaces/qa_compliance_assistant')

from api.src.database import SessionLocal
from api.src.models import Agency, User, UserRole
from api.src.auth import get_password_hash

db = SessionLocal()

try:
    print("Creating roles...")
    
    # Create roles if they don't exist
    roles_data = [
        {"name": "Admin", "description": "Full system access"},
        {"name": "Analyst", "description": "Create and manage findings"},
        {"name": "QA", "description": "Review and validate findings"},
        {"name": "Auditor", "description": "View and audit compliance data"}
    ]
    
    roles = {}
    for role_data in roles_data:
        role = db.query(UserRole).filter(UserRole.name == role_data["name"]).first()
        if not role:
            role = UserRole(**role_data, created_at=datetime.utcnow())
            db.add(role)
            db.commit()
            db.refresh(role)
            print(f"  Created role: {role.name}")
        else:
            print(f"  Role exists: {role.name}")
        roles[role.name] = role

    print("\nCreating agencies...")
    
    # Create agencies
    agencies_data = [
        {"name": "Health Sciences Authority", "code": "HSA", "description": "Singapore Health Sciences Authority", "contact_email": "contact@hsa.gov.sg"},
        {"name": "Inland Revenue Authority of Singapore", "code": "IRAS", "description": "Singapore tax authority", "contact_email": "contact@iras.gov.sg"}
    ]
    
    agencies = {}
    for agency_data in agencies_data:
        agency = db.query(Agency).filter(Agency.code == agency_data["code"]).first()
        if not agency:
            agency = Agency(**agency_data, active=True, created_at=datetime.utcnow())
            db.add(agency)
            db.commit()
            db.refresh(agency)
            print(f"  Created agency: {agency.name} ({agency.code})")
        else:
            print(f"  Agency exists: {agency.name} ({agency.code})")
        agencies[agency.code] = agency

    print("\nCreating users...")
    
    # Common password for all users
    password = "pass123"
    hashed_password = get_password_hash(password)
    
    # Users to create: 2 per agency (Analyst + QA), plus 2 Auditors (shared)
    users_data = [
        # HSA users
        {"username": "alice", "email": "alice@hsa.gov.sg", "full_name": "Alice Tan", "role": "Analyst", "agency": "HSA"},
        {"username": "bob", "email": "bob@hsa.gov.sg", "full_name": "Bob Lim", "role": "QA", "agency": "HSA"},
        
        # IRAS users
        {"username": "charlie", "email": "charlie@iras.gov.sg", "full_name": "Charlie Wong", "role": "Analyst", "agency": "IRAS"},
        {"username": "diana", "email": "diana@iras.gov.sg", "full_name": "Diana Ng", "role": "QA", "agency": "IRAS"},
        
        # Shared Auditors
        {"username": "edward", "email": "edward@audit.gov.sg", "full_name": "Edward Koh", "role": "Auditor", "agency": "HSA"},
        {"username": "fiona", "email": "fiona@audit.gov.sg", "full_name": "Fiona Lee", "role": "Auditor", "agency": "IRAS"},
    ]
    
    for user_data in users_data:
        user = db.query(User).filter(User.username == user_data["username"]).first()
        if not user:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_password,
                role_id=roles[user_data["role"]].id,
                agency_id=agencies[user_data["agency"]].id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  Created user: {user.username} ({user.full_name}) - {user_data['role']} @ {user_data['agency']}")
        else:
            print(f"  User exists: {user.username}")

    print(f"\n✓ Test data created successfully!")
    print(f"\nLogin credentials (all users):")
    print(f"  Password: {password}")
    print(f"\nUsers created:")
    print(f"  HSA: alice (Analyst), bob (QA)")
    print(f"  IRAS: charlie (Analyst), diana (QA)")
    print(f"  Auditors: edward, fiona")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
    raise
finally:
    db.close()
