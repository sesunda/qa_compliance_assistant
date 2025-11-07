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
alembic upgrade head || {
    echo "ERROR: Migration failed!"
    echo "Alembic config location:"
    find /app -name "alembic.ini" -type f
    exit 1
}

# Start the application from /app directory
echo "Starting uvicorn server..."
cd /app
exec uvicorn api.src.main:app --host 0.0.0.0 --port 8000
