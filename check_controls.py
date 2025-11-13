#!/usr/bin/env python3
"""Check controls in database"""

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

print("\n=== CONTROLS TABLE ===\n")

cursor.execute("SELECT COUNT(*) as count FROM controls")
count = cursor.fetchone()['count']
print(f"Total controls: {count}")

if count > 0:
    cursor.execute("""
        SELECT id, name, description, status, created_at
        FROM controls
        ORDER BY id
        LIMIT 20
    """)
    controls = cursor.fetchall()
    
    print("\nFirst 20 controls:")
    for ctrl in controls:
        print(f"  [{ctrl['id']}] {ctrl['name']} - Status: {ctrl['status']}")
else:
    print("\n❌ NO CONTROLS FOUND! Need to seed controls data.\n")

cursor.close()
conn.close()
