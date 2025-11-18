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

# Run fix script if migration state needs correction (with timeout)
echo "Running migration state fix if needed..."
timeout 30 python -m api.scripts.fix_migration_state || echo "Fix script completed, not needed, or timed out"

# Run migrations with timeout - if already migrated, this will be fast
echo "Applying database migrations..."
timeout 60 alembic upgrade head || {
    echo "WARNING: Migration failed or timed out - database may already be migrated"
    echo "Continuing with startup..."
}

# Seed default users and data
echo "Seeding authentication system..."
cd /app
python -m api.scripts.seed_auth || echo "Warning: Failed to seed auth data (may already exist)"

# Start the application from /app directory
echo "Starting uvicorn server..."
cd /app
echo "Uvicorn command: exec uvicorn api.src.main:app --host 0.0.0.0 --port 8000 --proxy-headers"
exec uvicorn api.src.main:app --host 0.0.0.0 --port 8000 --proxy-headers
