#!/bin/bash
set -e

echo "Starting QA Compliance Assistant API..."
echo "Current directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# Change to the api directory
cd /app/api

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting uvicorn server..."
cd /app
exec uvicorn api.src.main:app --host 0.0.0.0 --port 8000
