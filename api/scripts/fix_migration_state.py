#!/usr/bin/env python3
"""
Fix migration state for migrations 003/004 (Assessments and Findings upgrade).
Drops old indexes and resets alembic version if needed.
"""

from sqlalchemy import create_engine, text
import os

def main():
    """Fix database state to allow migrations 003/004 to run cleanly."""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set, skipping fix")
        return
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.fetchone()[0]
            
            print(f"Current migration version: {current_version}")
            
            # If at old version 0000053, jump to 002 (skip timezone migration that was already done)
            if current_version == '0000053':
                conn.execute(text("UPDATE alembic_version SET version_num = '002'"))
                conn.commit()
                print("Jumped from 0000053 to 002 (timezone already migrated)")
                current_version = '002'
            
            # Only fix if we're at version 002 or 003 (need assessments/findings upgrade)
            if current_version not in ['002', '003']:
                print(f"No fix needed for version {current_version}")
                return
            
            print("Applying migration state fixes...")
            
            # Drop old indexes that might conflict with migrations 003/004
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
                    conn.execute(text(f"DROP INDEX IF EXISTS {idx}"))
                    conn.commit()
                    print(f"  ✓ Dropped index {idx}")
                except Exception as e:
                    print(f"  ⚠ {idx}: {str(e)[:60]}")
            
            # Reset to version 002 if we're at 003 (failed)
            if current_version == '003':
                conn.execute(text("UPDATE alembic_version SET version_num = '002'"))
                conn.commit()
                print("  ✓ Reset alembic version to 002 for clean migration")
            
            print("✅ Database state fixed - ready for migration")
            
    except Exception as e:
        print(f"⚠ Fix script error (non-fatal): {str(e)[:100]}")
        # Don't fail startup if fix fails

if __name__ == "__main__":
    main()
