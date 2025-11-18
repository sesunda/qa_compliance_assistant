"""Fix existing data timestamps"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db"

engine = create_engine(DATABASE_URL)

print("\n🔧 Fixing existing data timestamps...\n")

with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Add 16 hours to correct the timestamps (8 hours were subtracted during migration, need to add back 16)
        conn.execute(text("UPDATE evidence SET created_at = created_at + INTERVAL '16 hours' WHERE id = 40"))
        conn.execute(text("UPDATE agent_tasks SET created_at = created_at + INTERVAL '16 hours', started_at = started_at + INTERVAL '16 hours', completed_at = completed_at + INTERVAL '16 hours' WHERE id = 109"))
        conn.execute(text("UPDATE conversation_sessions SET created_at = created_at + INTERVAL '16 hours', last_activity = last_activity + INTERVAL '16 hours' WHERE session_id = 'becd3c82-ac88-4dc1-9402-df12b6587b5f'"))
        
        trans.commit()
        print("✅ Fixed existing data timestamps\n")
        
        # Verify
        result = conn.execute(text("SELECT created_at FROM evidence WHERE id = 40"))
        row = result.fetchone()
        print(f"Evidence #40 created_at: {row[0]}")
        
        result = conn.execute(text("SELECT created_at, completed_at FROM agent_tasks WHERE id = 109"))
        row = result.fetchone()
        print(f"Task #109 created_at: {row[0]}, completed_at: {row[1]}")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Error: {e}")
