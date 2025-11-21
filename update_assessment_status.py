"""
Update assessment status to make it show as active
"""
import os
from sqlalchemy import create_engine, text

os.environ['DATABASE_URL'] = "postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db?sslmode=require"
engine = create_engine(os.environ['DATABASE_URL'])

# Update assessment 1 status from 'not_started' to 'in_progress'
with engine.connect() as conn:
    conn.execute(text("""
        UPDATE assessments 
        SET status = 'in_progress'
        WHERE id = 1
    """))
    conn.commit()
    
    # Verify the update
    result = conn.execute(text("""
        SELECT id, name, status, lead_assessor_user_id 
        FROM assessments 
        WHERE id = 1
    """))
    row = result.fetchone()
    
    print("✅ Assessment updated successfully!")
    print(f"   ID: {row[0]}")
    print(f"   Name: {row[1]}")
    print(f"   Status: {row[2]}")
    print(f"   Lead Assessor: {row[3]}")
    print()
    print("The assessment will now appear in 'My Active Assessments' on the dashboard.")
