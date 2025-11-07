#!/bin/bash
# Reset database and apply consolidated migration

echo "=== Database Reset Script ==="
echo ""

# Get the latest active revision
REVISION=$(az containerapp revision list \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --query "[?properties.active==\`true\` && properties.trafficWeight==\`100\`].name" \
  --output tsv)

echo "Active revision: $REVISION"
echo ""

echo "Step 1: Dropping all tables and recreating fresh..."
az containerapp exec \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --revision "$REVISION" \
  --command "python -c \"
from api.src.database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()
try:
    # Drop all tables
    print('Dropping all tables...')
    db.execute(text('DROP SCHEMA public CASCADE'))
    db.execute(text('CREATE SCHEMA public'))
    db.execute(text('GRANT ALL ON SCHEMA public TO qca_admin'))
    db.execute(text('GRANT ALL ON SCHEMA public TO public'))
    db.commit()
    print('✓ All tables dropped, schema recreated')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
\""

echo ""
echo "Step 2: Running alembic upgrade head..."
az containerapp exec \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --revision "$REVISION" \
  --command "cd /app/api && alembic upgrade head"

echo ""
echo "Step 3: Seeding admin user..."
az containerapp exec \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --revision "$REVISION" \
  --command "cd /app && python -m api.scripts.seed_auth"

echo ""
echo "=== Database reset complete! ==="
echo "You can now login with: admin / admin123"
