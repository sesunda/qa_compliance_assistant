#!/usr/bin/env python3
"""
Fix migration state and add missing columns
Run this script inside the Azure Container App
"""

from sqlalchemy import create_engine, text
import os
import sys

def main():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Step 1: Check if trigger already exists, if so set version to 0000053
        print("\n=== Step 1: Checking migration state ===")
        
        # Check if notify trigger exists
        trigger_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_trigger 
                WHERE tgname = 'agent_task_insert_trigger'
            )
        """))
        trigger_exists = trigger_check.fetchone()[0]
        
        if trigger_exists:
            print("✓ Trigger 'agent_task_insert_trigger' already exists")
            # Set migration to 0000053 to skip trigger creation
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0000053')"))
            conn.commit()
            print("✓ Set migration version to 0000053 (trigger migration)")
        else:
            print("⚠ Trigger does not exist, setting to 001 for clean migration")
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001')"))
            conn.commit()
            print("✓ Set migration version to 001")
        
        # Step 2: Add project_type column
        print("\n=== Step 2: Adding project_type column ===")
        try:
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS project_type VARCHAR(100) DEFAULT 'compliance_assessment'
            """))
            conn.commit()
            print("✓ Added project_type column")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠ project_type column already exists")
            else:
                raise
        
        # Step 3: Add start_date column
        print("\n=== Step 3: Adding start_date column ===")
        try:
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS start_date DATE
            """))
            conn.commit()
            print("✓ Added start_date column")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠ start_date column already exists")
            else:
                raise
        
        # Step 4: Verify
        print("\n=== Step 4: Verification ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            AND column_name IN ('project_type', 'start_date')
            ORDER BY column_name
        """))
        
        print("\nProjects table columns:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (default: {row[2]})")
        
        # Check migration version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.fetchone()[0]
        print(f"\nCurrent migration version: {version}")
        
    print("\n✅ Migration state fixed successfully!")
    print("You can now restart the container for clean startup.")

if __name__ == "__main__":
    main()
