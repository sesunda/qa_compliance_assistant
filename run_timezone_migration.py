"""Run timezone migration directly on database"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db"

engine = create_engine(DATABASE_URL)

print("\n🔄 Starting timezone migration...\n")

with engine.connect() as conn:
    # Start transaction
    trans = conn.begin()
    
    try:
        tables_to_migrate = [
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
        
        for table_name, columns in tables_to_migrate:
            print(f"Migrating table: {table_name}")
            for column in columns:
                sql = f"ALTER TABLE {table_name} ALTER COLUMN {column} TYPE timestamp with time zone USING {column} AT TIME ZONE 'UTC'"
                print(f"  - {column}")
                conn.execute(text(sql))
        
        # Record migration in alembic_version table
        conn.execute(text("DELETE FROM alembic_version WHERE version_num = '002'"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('002')"))
        
        trans.commit()
        print("\n✅ Timezone migration completed successfully!")
        print("All timestamp columns now use 'timestamp with time zone'\n")
        
    except Exception as e:
        trans.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise

# Verify changes
print("Verifying migration...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'evidence' 
        AND column_name = 'created_at'
    """))
    row = result.fetchone()
    print(f"Evidence.created_at type: {row[1]}")
    
    # Check actual data
    result = conn.execute(text("SELECT id, created_at FROM evidence WHERE id = 39"))
    row = result.fetchone()
    if row:
        print(f"Evidence #39 created_at: {row[1]}")
    
print("\n✅ Migration verification complete!")
