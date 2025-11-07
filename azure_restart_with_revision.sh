#!/bin/bash
# Get the active revision and restart the API container

echo "🔍 Getting active revision for ca-api-qca-dev..."
echo ""

# Get the active revision name
REVISION=$(az containerapp revision list \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --query "[?properties.active==\`true\`].name" \
  -o tsv | head -1)

if [ -z "$REVISION" ]; then
    echo "❌ Could not find active revision"
    echo ""
    echo "Alternative: Restart via container app update"
    echo ""
    echo "Run this command instead:"
    echo ""
    echo "az containerapp update \\"
    echo "  --name ca-api-qca-dev \\"
    echo "  --resource-group rg-qca-dev \\"
    echo "  --min-replicas 0 \\"
    echo "  --max-replicas 1"
    echo ""
    echo "Then run:"
    echo ""
    echo "az containerapp update \\"
    echo "  --name ca-api-qca-dev \\"
    echo "  --resource-group rg-qca-dev \\"
    echo "  --min-replicas 1 \\"
    echo "  --max-replicas 1"
    exit 1
fi

echo "✅ Active revision: $REVISION"
echo ""
echo "🔄 Restarting revision..."

az containerapp revision restart \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --revision "$REVISION"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Restart command successful!"
    echo ""
    echo "⏱️  Waiting 30 seconds for container to start..."
    sleep 30
    
    echo ""
    echo "🔍 Checking for migration logs..."
    az containerapp logs show \
      --name ca-api-qca-dev \
      --resource-group rg-qca-dev \
      --tail 100 | grep -E "(alembic|migration|Running upgrade)" | tail -15
    
    echo ""
    echo "✅ Done! Refresh your browser now."
else
    echo ""
    echo "❌ Restart failed"
fi
