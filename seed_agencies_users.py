#!/usr/bin/env python3
"""Seed agencies and users for testing"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
import bcrypt

# Database connection
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

print("Connecting to database...")
conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    sslmode="require"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Hash password function
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("\n=== Creating Agencies ===")

# Create agencies
agencies = [
    ("Health Sciences Authority", "HSA", "Health Sciences Authority - Singapore"),
    ("Inland Revenue Authority of Singapore", "IRAS", "Inland Revenue Authority of Singapore")
]

agency_ids = {}
for name, code, description in agencies:
    cursor.execute("""
        INSERT INTO agencies (name, code, description, active, created_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (name, code, description, True, datetime.utcnow()))
    agency_id = cursor.fetchone()[0]
    agency_ids[code] = agency_id
    print(f"✓ Created agency: {name} (ID: {agency_id})")

print("\n=== Creating User Roles ===")

# Create roles
roles = [
    ("Admin", "Full system access", '{"all": true}'),
    ("Analyst", "Create and manage findings", '{"findings": ["create", "update", "view"]}'),
    ("QA Reviewer", "Review and validate findings", '{"findings": ["view", "validate", "approve"]}'),
    ("Auditor", "View all assessments and findings", '{"assessments": ["view"], "findings": ["view"], "reports": ["view"]}')
]

role_ids = {}
for name, description, permissions in roles:
    cursor.execute("""
        INSERT INTO user_roles (name, description, permissions, created_at)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (name, description, permissions, datetime.utcnow()))
    role_id = cursor.fetchone()[0]
    role_ids[name] = role_id
    print(f"✓ Created role: {name} (ID: {role_id})")

print("\n=== Creating Users ===")

# Create users
users = [
    # HSA Users
    ("hsa_admin", "admin123", "HSA Admin", "admin@hsa.gov.sg", "Admin", "HSA", True),
    ("hsa_analyst", "analyst123", "Alice Tan", "alice.tan@hsa.gov.sg", "Analyst", "HSA", True),
    ("hsa_qa", "qa123", "Bob Lee", "bob.lee@hsa.gov.sg", "QA Reviewer", "HSA", True),
    
    # IRAS Users
    ("iras_admin", "admin123", "IRAS Admin", "admin@iras.gov.sg", "Admin", "IRAS", True),
    ("iras_analyst", "analyst123", "Carol Wong", "carol.wong@iras.gov.sg", "Analyst", "IRAS", True),
    ("iras_qa", "qa123", "David Lim", "david.lim@iras.gov.sg", "QA Reviewer", "IRAS", True),
    
    # Common Auditors (no agency affiliation)
    ("auditor1", "auditor123", "Emma Chen", "emma.chen@audit.gov.sg", "Auditor", None, True),
    ("auditor2", "auditor123", "Frank Kumar", "frank.kumar@audit.gov.sg", "Auditor", None, True),
]

for username, password, full_name, email, role_name, agency_code, is_active in users:
    hashed_pw = hash_password(password)
    role_id = role_ids[role_name]
    agency_id = agency_ids[agency_code] if agency_code else None
    
    cursor.execute("""
        INSERT INTO users (username, email, full_name, hashed_password, role_id, agency_id, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (username, email, full_name, hashed_pw, role_id, agency_id, is_active, datetime.utcnow()))
    
    user_id = cursor.fetchone()[0]
    agency_name = agency_code if agency_code else "No Agency"
    print(f"✓ Created user: {username} ({full_name}) - {role_name} @ {agency_name} (ID: {user_id})")

print("\n=== Summary ===")
print("Agencies created: 2")
print("  - Health Sciences Authority (HSA)")
print("  - Inland Revenue Authority of Singapore (IRAS)")
print("\nRoles created: 4")
print("  - Admin, Analyst, QA Reviewer, Auditor")
print("\nUsers created: 8")
print("  HSA: hsa_admin, hsa_analyst, hsa_qa")
print("  IRAS: iras_admin, iras_analyst, iras_qa")
print("  Auditors: auditor1, auditor2")
print("\nDefault password for all users: See username pattern")
print("  - admins: admin123")
print("  - analysts: analyst123")
print("  - qa: qa123")
print("  - auditors: auditor123")

cursor.close()
conn.close()
print("\n✅ Done!")
