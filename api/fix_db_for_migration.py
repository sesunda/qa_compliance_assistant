"""
One-time fix script to prepare database for re-running migrations 003 and 004.
This drops old indexes and resets alembic version.
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment or use Azure connection
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://qcaadmin:tqS4BVr6tSm4WzTY@psql-qca-dev-2f37g0.postgres.database.azure.com/qca_db?sslmode=require'
)

engine = create_engine(DATABASE_URL)

print("Fixing database state for migration re-run...")
print("=" * 60)

with engine.connect() as conn:
    # Drop old indexes
    old_indexes = [
        'ix_assessments_project_id',
        'ix_assessments_agency_id',
        'ix_assessments_status',
        'ix_assessments_assessment_type',
        'ix_assessments_planned_end_date',
        'ix_findings_assessment_id',
        'ix_findings_severity',
        'ix_findings_status',
        'ix_findings_assigned_to',
        'ix_findings_target_remediation_date'
    ]
    
    for idx in old_indexes:
        try:
            print(f"Dropping index {idx}...")
            conn.execute(text(f"DROP INDEX IF EXISTS {idx}"))
            conn.commit()
            print(f"  ✓ Dropped {idx}")
        except Exception as e:
            print(f"  ⚠ {idx}: {str(e)[:80]}")
    
    # Reset alembic version to 002
    try:
        print("\nResetting alembic version to 002...")
        conn.execute(text("UPDATE alembic_version SET version_num = '002'"))
        conn.commit()
        print("  ✓ Alembic version reset to 002")
    except Exception as e:
        print(f"  ⚠ Error: {str(e)[:80]}")
    
    # Verify state
    print("\nVerifying database state...")
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    version = result.fetchone()[0]
    print(f"  Current version: {version}")
    
    result = conn.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename IN ('assessments', 'findings')
        ORDER BY indexname
    """))
    indexes = result.fetchall()
    print(f"  Remaining indexes: {len(indexes)}")
    for idx in indexes:
        print(f"    - {idx[0]}")

print("\n" + "=" * 60)
print("Database ready for migration re-run!")
