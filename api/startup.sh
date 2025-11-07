#!/bin/bash
set -e

echo "Starting QA Compliance Assistant API..."
echo "Current directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"
echo "Contents of /app:"
ls -la /app/
echo "Contents of /app/api:"
ls -la /app/api/ || echo "No /app/api directory"

# Run database migrations from the api directory
echo "Running database migrations..."
cd /app/api

# Check if alembic_version exists and if it has broken state
echo "Checking migration state..."
python -c "
from sqlalchemy import text
from api.src.database import SessionLocal
try:
    db = SessionLocal()
    result = db.execute(text('SELECT version_num FROM alembic_version')).fetchone()
    if result:
        version = result[0]
        print(f'Current version: {version}')
        # If version is from old migration tree, reset it
        if version in ['5f706ede940a', '898cc8361b19', '002', '003', '004', '006', '007', '008', '008_add_conversation_sessions', '009_update_agent_tasks', '009_5', '010_complete_assessment_workflows']:
            print(f'Detected old migration version {version}, clearing...')
            db.execute(text('DELETE FROM alembic_version'))
            db.commit()
            print('Cleared old migration state. Will start fresh.')
    db.close()
except Exception as e:
    print(f'No existing alembic_version table or error: {e}')
" || echo "Migration state check completed"

alembic upgrade head || {
    echo "ERROR: Migration failed!"
    echo "Alembic config location:"
    find /app -name "alembic.ini" -type f
    exit 1
}

# Seed default users and data
echo "Seeding authentication system..."
cd /app
python -m api.scripts.seed_auth || echo "Warning: Failed to seed auth data (may already exist)"

# Start the application from /app directory
echo "Starting uvicorn server..."
cd /app
exec uvicorn api.src.main:app --host 0.0.0.0 --port 8000
