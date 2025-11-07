#!/bin/bash
# Script to reset database via API endpoints

API_URL="https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

echo "=== Database Reset via API ==="
echo ""

echo "Step 1: Resetting database (drop all tables)..."
curl -X POST "$API_URL/admin/reset-database" \
  -H "Content-Type: application/json" \
  -s | python3 -m json.tool

echo ""
echo "Step 2: Waiting 10 seconds for database reset..."
sleep 10

echo ""
echo "Step 3: Restarting API container..."
az containerapp revision restart \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --revision $(az containerapp revision list \
    --name ca-api-qca-dev \
    --resource-group rg-qca-dev \
    --query "[?properties.active==\`true\` && properties.trafficWeight==\`100\`].name" \
    --output tsv)

echo ""
echo "Step 4: Waiting 60 seconds for container to restart and apply migrations..."
sleep 60

echo ""
echo "Step 5: Seeding admin user..."
curl -X POST "$API_URL/admin/seed-users" \
  -H "Content-Type: application/json" \
  -s | python3 -m json.tool

echo ""
echo ""
echo "=== Database Reset Complete! ==="
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Frontend URL:"
echo "  https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/dashboard"
