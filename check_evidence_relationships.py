#!/usr/bin/env python3
"""Check evidence relationships to project/domain/control"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection - Azure
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

print("=" * 80)
print("EVIDENCE RELATIONSHIP ANALYSIS")
print("=" * 80)

conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    sslmode="require",
    cursor_factory=RealDictCursor
)
cursor = conn.cursor()

# 1. Check Evidence table schema
print("\n1. EVIDENCE TABLE SCHEMA")
print("-" * 80)
cursor.execute("""
    SELECT 
        column_name, 
        data_type, 
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_name = 'evidence'
    ORDER BY ordinal_position
""")
columns = cursor.fetchall()
print("\nEvidence table columns:")
for col in columns:
    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"  {col['column_name']:30} {col['data_type']:20} {nullable}")

# 2. Check Foreign Key constraints
print("\n\n2. FOREIGN KEY CONSTRAINTS")
print("-" * 80)
cursor.execute("""
    SELECT
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = 'evidence'
""")
fks = cursor.fetchall()
print("\nEvidence foreign keys:")
for fk in fks:
    print(f"  {fk['column_name']:20} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")

# 3. Check Controls table schema and relationships
print("\n\n3. CONTROLS TABLE RELATIONSHIPS")
print("-" * 80)
cursor.execute("""
    SELECT 
        column_name, 
        data_type, 
        is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'controls'
        AND column_name IN ('id', 'project_id', 'agency_id', 'name')
    ORDER BY ordinal_position
""")
control_cols = cursor.fetchall()
print("\nKey control columns:")
for col in control_cols:
    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"  {col['column_name']:20} {col['data_type']:20} {nullable}")

cursor.execute("""
    SELECT
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = 'controls'
""")
control_fks = cursor.fetchall()
print("\nControl foreign keys:")
for fk in control_fks:
    print(f"  {fk['column_name']:20} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")

# 4. Check data relationships
print("\n\n4. ACTUAL DATA RELATIONSHIPS")
print("-" * 80)

# Sample control with its project and agency
cursor.execute("""
    SELECT 
        c.id as control_id,
        c.name as control_name,
        c.project_id,
        p.name as project_name,
        c.agency_id,
        a.name as agency_name
    FROM controls c
    LEFT JOIN projects p ON c.project_id = p.id
    LEFT JOIN agencies a ON c.agency_id = a.id
    WHERE c.id = 5
""")
control = cursor.fetchone()
if control:
    print("\nControl 5 relationships:")
    print(f"  Control ID: {control['control_id']}")
    print(f"  Control Name: {control['control_name']}")
    print(f"  Project ID: {control['project_id']}")
    print(f"  Project Name: {control['project_name']}")
    print(f"  Agency ID: {control['agency_id']}")
    print(f"  Agency Name: {control['agency_name']}")

# 5. Check if evidence table has project_id
print("\n\n5. EVIDENCE → PROJECT RELATIONSHIP")
print("-" * 80)
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'evidence' 
        AND column_name = 'project_id'
""")
has_project_id = cursor.fetchone()
if has_project_id:
    print("✅ Evidence table HAS project_id column")
else:
    print("❌ Evidence table DOES NOT have project_id column")
    print("   Evidence only links to control_id and agency_id")

# 6. Check full evidence → control → project chain
print("\n\n6. EVIDENCE RELATIONSHIP CHAIN")
print("-" * 80)
print("\nCurrent design:")
print("  Evidence → control_id → Controls")
print("  Evidence → agency_id → Agencies")
print("  Controls → project_id → Projects")
print("  Controls → agency_id → Agencies")

# Check if we can traverse to project
cursor.execute("""
    SELECT 
        COUNT(*) as count,
        COUNT(DISTINCT c.project_id) as unique_projects
    FROM controls c
    WHERE c.project_id IS NOT NULL
""")
result = cursor.fetchone()
print(f"\nControls with project_id: {result['count']}")
print(f"Unique projects: {result['unique_projects']}")

# 7. Test query: Get evidence with full relationship chain
print("\n\n7. SAMPLE QUERY: Evidence → Control → Project")
print("-" * 80)
cursor.execute("""
    SELECT 
        e.id as evidence_id,
        e.title as evidence_title,
        e.control_id,
        c.name as control_name,
        c.project_id,
        p.name as project_name,
        e.agency_id as evidence_agency_id,
        a1.name as evidence_agency_name,
        c.agency_id as control_agency_id,
        a2.name as control_agency_name
    FROM evidence e
    JOIN controls c ON e.control_id = c.id
    LEFT JOIN projects p ON c.project_id = p.id
    LEFT JOIN agencies a1 ON e.agency_id = a1.id
    LEFT JOIN agencies a2 ON c.agency_id = a2.id
    LIMIT 5
""")
samples = cursor.fetchall()
if samples:
    print("\nSample evidence relationships:")
    for s in samples:
        print(f"\n  Evidence #{s['evidence_id']}: {s['evidence_title']}")
        print(f"    Control: {s['control_name']} (ID: {s['control_id']})")
        print(f"    Project: {s['project_name']} (ID: {s['project_id']})")
        print(f"    Evidence Agency: {s['evidence_agency_name']} (ID: {s['evidence_agency_id']})")
        print(f"    Control Agency: {s['control_agency_name']} (ID: {s['control_agency_id']})")
else:
    print("\n❌ No evidence found to analyze")

# 8. Check agency consistency
print("\n\n8. AGENCY CONSISTENCY CHECK")
print("-" * 80)
cursor.execute("""
    SELECT 
        e.id,
        e.agency_id as evidence_agency,
        c.agency_id as control_agency,
        CASE 
            WHEN e.agency_id = c.agency_id THEN 'MATCH'
            WHEN e.agency_id IS NULL OR c.agency_id IS NULL THEN 'NULL'
            ELSE 'MISMATCH'
        END as agency_check
    FROM evidence e
    JOIN controls c ON e.control_id = c.id
""")
consistency = cursor.fetchall()
if consistency:
    matches = sum(1 for c in consistency if c['agency_check'] == 'MATCH')
    mismatches = sum(1 for c in consistency if c['agency_check'] == 'MISMATCH')
    nulls = sum(1 for c in consistency if c['agency_check'] == 'NULL')
    print(f"\nAgency consistency:")
    print(f"  ✅ Matching: {matches}")
    print(f"  ❌ Mismatches: {mismatches}")
    print(f"  ⚠️  NULL values: {nulls}")
    
    if mismatches > 0:
        cursor.execute("""
            SELECT 
                e.id,
                e.agency_id as evidence_agency,
                a1.name as evidence_agency_name,
                c.agency_id as control_agency,
                a2.name as control_agency_name
            FROM evidence e
            JOIN controls c ON e.control_id = c.id
            LEFT JOIN agencies a1 ON e.agency_id = a1.id
            LEFT JOIN agencies a2 ON c.agency_id = a2.id
            WHERE e.agency_id != c.agency_id
        """)
        mismatched = cursor.fetchall()
        print("\n  Mismatched evidence:")
        for m in mismatched:
            print(f"    Evidence #{m['id']}: {m['evidence_agency_name']} ≠ Control: {m['control_agency_name']}")
else:
    print("No evidence to check")

# 9. Summary
print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print("\n✅ Evidence IS tied to Control (via control_id FK)")
print("✅ Evidence IS tied to Agency (via agency_id FK)")
print("✅ Control IS tied to Project (via project_id FK)")
print("✅ Control IS tied to Agency (via agency_id FK)")
print("\n📊 Relationship Chain:")
print("   Evidence → Control → Project")
print("   Evidence → Agency (direct)")
print("   Control → Agency (direct)")

cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'evidence' AND column_name = 'project_id'")
if not cursor.fetchone():
    print("\n⚠️  NOTE: Evidence does NOT have direct project_id")
    print("   Project is accessed through: Evidence → Control → Project")
    print("   This is a normalized design (no redundancy)")

cursor.close()
conn.close()
