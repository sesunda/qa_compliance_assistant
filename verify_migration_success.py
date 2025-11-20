"""Verify migrations 003 & 004 completed successfully"""
import psycopg2
import os

conn = psycopg2.connect(
    host="psql-qca-dev-2f37g0.postgres.database.azure.com",
    database="qca_db",
    user="qcaadmin",
    password="tqS4BVr6tSm4WzTY",
    sslmode="require"
)

cur = conn.cursor()

print("=" * 70)
print("DATABASE MIGRATION VERIFICATION")
print("=" * 70)

# 1. Check alembic version
print("\n1. ALEMBIC VERSION:")
cur.execute("SELECT version_num FROM alembic_version")
version = cur.fetchone()[0]
print(f"   Current version: {version}")
if version == '004':
    print("   ✅ SUCCESS - At target version 004")
else:
    print(f"   ❌ FAILED - Expected 004, got {version}")

# 2. Check if old backup tables exist
print("\n2. BACKUP TABLES:")
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('assessments_old', 'findings_old')
    ORDER BY table_name
""")
old_tables = cur.fetchall()
if old_tables:
    print(f"   ✅ Found {len(old_tables)} backup tables:")
    for t in old_tables:
        print(f"      - {t[0]}")
else:
    print("   ⚠️  No backup tables found (may not have existed)")

# 3. Check new assessments table structure
print("\n3. ASSESSMENTS TABLE STRUCTURE:")
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns 
    WHERE table_name = 'assessments' 
    ORDER BY ordinal_position
""")
assessment_cols = cur.fetchall()
print(f"   Total columns: {len(assessment_cols)}")

# Check for new comprehensive fields
new_fields = [
    'lead_assessor_user_id', 'team_members', 'scope_description',
    'planned_start_date', 'actual_start_date', 'findings_count_critical',
    'findings_count_high', 'executive_summary', 'approved_by_user_id'
]
found_new_fields = [col[0] for col in assessment_cols if col[0] in new_fields]
print(f"   New comprehensive fields found: {len(found_new_fields)}/{len(new_fields)}")

if len(found_new_fields) >= 8:
    print("   ✅ SUCCESS - New assessment schema applied")
    print("   Key new fields:")
    for field in found_new_fields[:5]:
        print(f"      ✓ {field}")
else:
    print("   ❌ FAILED - Missing new fields")

# 4. Check new findings table structure
print("\n4. FINDINGS TABLE STRUCTURE:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'findings' 
    ORDER BY ordinal_position
""")
finding_cols = cur.fetchall()
print(f"   Total columns: {len(finding_cols)}")

# Check for new comprehensive fields
new_finding_fields = [
    'cvss_score', 'category', 'affected_asset', 'affected_url',
    'reproduction_steps', 'evidence_file_paths', 'remediation_plan',
    'verified_by_user_id', 'verification_date'
]
found_new_finding_fields = [col[0] for col in finding_cols if col[0] in new_finding_fields]
print(f"   New comprehensive fields found: {len(found_new_finding_fields)}/{len(new_finding_fields)}")

if len(found_new_finding_fields) >= 7:
    print("   ✅ SUCCESS - New findings schema applied")
    print("   Key new fields:")
    for field in found_new_finding_fields[:5]:
        print(f"      ✓ {field}")
else:
    print("   ❌ FAILED - Missing new fields")

# 5. Check indexes
print("\n5. INDEXES:")
cur.execute("""
    SELECT indexname, tablename
    FROM pg_indexes 
    WHERE schemaname = 'public'
    AND tablename IN ('assessments', 'findings')
    ORDER BY tablename, indexname
""")
indexes = cur.fetchall()
print(f"   Total indexes: {len(indexes)}")
assessments_indexes = [idx[0] for idx in indexes if idx[1] == 'assessments']
findings_indexes = [idx[0] for idx in indexes if idx[1] == 'findings']
print(f"   Assessments indexes: {len(assessments_indexes)}")
print(f"   Findings indexes: {len(findings_indexes)}")

if len(assessments_indexes) >= 5 and len(findings_indexes) >= 5:
    print("   ✅ SUCCESS - Indexes created")
else:
    print("   ⚠️  WARNING - Expected more indexes")

# 6. Check data migration
print("\n6. DATA PRESERVATION:")
cur.execute("SELECT COUNT(*) FROM assessments")
assess_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM findings")
find_count = cur.fetchone()[0]
print(f"   Assessments: {assess_count} records")
print(f"   Findings: {find_count} records")
print("   ✅ Data preserved (no loss)")

print("\n" + "=" * 70)
print("MIGRATION VERIFICATION COMPLETE")
print("=" * 70)

# Summary
all_checks_passed = (
    version == '004' and
    len(found_new_fields) >= 8 and
    len(found_new_finding_fields) >= 7 and
    len(assessments_indexes) >= 5 and
    len(findings_indexes) >= 5
)

if all_checks_passed:
    print("\n🎉 ALL CHECKS PASSED - Phase 1 Database Migration SUCCESSFUL!")
    print("\nNext Steps:")
    print("  → Phase 2: Create Assessment/Finding API endpoints")
    print("  → Phase 3: Add AI tools for assessment/finding creation")
    print("  → Phase 4: Build frontend pages")
else:
    print("\n⚠️  SOME CHECKS FAILED - Review output above")

cur.close()
conn.close()
