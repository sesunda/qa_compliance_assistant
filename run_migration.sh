#!/bin/bash

# Script to run database migrations on Azure Container Apps
set -e

echo "Getting API URL..."
API_URL="https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

echo "Triggering migration via API endpoint..."
# Create a simple endpoint that runs the migration
# For now, let's just verify the schema

echo "Checking database schema..."
curl -X GET "$API_URL/health" -H "Content-Type: application/json" || echo "API not ready yet"

echo ""
echo "Migration will be run manually. Please execute:"
echo ""
echo "  az containerapp exec --name ca-api-qca-dev --resource-group rg-qca-dev --command 'alembic upgrade head'"
echo ""
