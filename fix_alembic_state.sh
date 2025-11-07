#!/bin/bash
# Fix alembic migration state by resetting to migration 007

DB_HOST="psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER="qca_admin"
DB_PASS="Welcome@2025"
DB_NAME="qcadb"

echo "Fixing alembic migration state..."
echo "Current state:"

# Check current version
az containerapp exec \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --command "python -c \"
from api.src.database import SessionLocal
db = SessionLocal()
result = db.execute('SELECT version_num FROM alembic_version').fetchall()
print('Current alembic version:', result)
db.close()
\""

echo ""
echo "Resetting to migration 007..."

# Reset to migration 007 (last known good state before the split)
az containerapp exec \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --command "python -c \"
from api.src.database import SessionLocal
db = SessionLocal()
try:
    db.execute('UPDATE alembic_version SET version_num = \\'007\\'')
    db.commit()
    print('✓ Reset alembic_version to 007')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
\""

echo ""
echo "Restarting API container to apply migrations 008, 009, 009_5, 010..."
az containerapp revision restart \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --revision ca-api-qca-dev--r1762504518

echo ""
echo "Waiting for container to restart (30 seconds)..."
sleep 30

echo ""
echo "Checking logs..."
az containerapp logs show \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --tail 50 \
  --follow false 2>&1 | grep -E "Migration|upgrade|Seeding|admin|Created default"
