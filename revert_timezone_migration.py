"""Revert to timestamp without time zone and store naive SGT times"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db"

engine = create_engine(DATABASE_URL)

print("\n🔄 Reverting to timestamp without time zone...\n")

with engine.connect() as conn:
    trans = conn.begin()
    
    try:
        tables_to_revert = [
            ("agencies", ["created_at"]),
            ("user_roles", ["created_at"]),
            ("users", ["last_login", "created_at", "updated_at"]),
            ("projects", ["created_at", "updated_at"]),
            ("assessments", ["created_at", "completed_at", "target_completion_date"]),
            ("controls", ["created_at", "updated_at", "reviewed_at", "last_tested_at", "next_test_due"]),
            ("evidence", ["uploaded_at", "reviewed_at", "created_at", "updated_at"]),
            ("findings", ["created_at", "resolved_at", "validated_at", "due_date", "updated_at"]),
            ("reports", ["generated_at"]),
            ("control_catalog", ["approved_at", "created_at", "updated_at"]),
            ("agent_tasks", ["created_at", "updated_at", "started_at", "completed_at"]),
            ("conversation_sessions", ["created_at", "last_activity"]),
            ("assessment_controls", ["created_at"]),
            ("finding_comments", ["created_at"]),
        ]
        
        for table_name, columns in tables_to_revert:
            print(f"Reverting table: {table_name}")
            for column in columns:
                # Convert existing UTC timestamps to SGT and remove timezone
                sql = f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN {column} TYPE timestamp without time zone 
                    USING {column} AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Singapore'
                """
                print(f"  - {column}")
                conn.execute(text(sql))
        
        # Update migration version
        conn.execute(text("DELETE FROM alembic_version WHERE version_num = '003'"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('003')"))
        
        trans.commit()
        print("\n✅ Reverted to timestamp without time zone")
        print("All existing UTC timestamps converted to SGT\n")
        
    except Exception as e:
        trans.rollback()
        print(f"\n❌ Revert failed: {e}")
        raise

# Verify
print("Verifying...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'evidence' 
        AND column_name = 'created_at'
    """))
    row = result.fetchone()
    print(f"Evidence.created_at type: {row[1]}")

print("\n✅ Migration verification complete!")
