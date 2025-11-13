#!/usr/bin/env python3
"""Check Project 1 controls"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection - Azure
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

print("Connecting to Azure database...")
conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    sslmode="require",
    cursor_factory=RealDictCursor
)
cursor = conn.cursor()

print("\n=== PROJECT 1 CHECK ===\n")

cursor.execute("SELECT * FROM projects WHERE id = 1")
project = cursor.fetchone()

if project:
    print(f"Project 1: {project['name']}")
    print(f"Agency ID: {project['agency_id']}")
    print(f"Status: {project['status']}")
    
    # Check controls in Project 1
    cursor.execute("""
        SELECT id, name, status, project_id
        FROM controls
        WHERE project_id = 1
        ORDER BY id
    """)
    controls = cursor.fetchall()
    
    print(f"\nControls in Project 1: {len(controls)}")
    for ctrl in controls[:10]:
        print(f"  [{ctrl['id']}] {ctrl['name']} - Status: {ctrl['status']}")
    
    # Check if Control 5 is in Project 1
    cursor.execute("SELECT * FROM controls WHERE id = 5")
    control5 = cursor.fetchone()
    if control5:
        print(f"\n✓ Control 5 exists: {control5['name']}")
        print(f"  Project ID: {control5['project_id']}")
        print(f"  Agency ID: {control5['agency_id']}")
else:
    print("❌ Project 1 NOT FOUND!")

# Check Alice's agency
cursor.execute("SELECT id, agency_id, full_name FROM users WHERE username = 'alice'")
alice = cursor.fetchone()
if alice:
    print(f"\nAlice's Agency ID: {alice['agency_id']}")

cursor.close()
conn.close()
