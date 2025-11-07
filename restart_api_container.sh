#!/bin/bash
# Script to restart API container and verify Migration 010 is applied

echo "🔄 Restarting API Container to Apply Migration 010"
echo "=================================================="
echo ""

# Check if az CLI is available
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI (az) is not installed or not in PATH"
    echo ""
    echo "Please run this command manually in Azure Cloud Shell or locally:"
    echo ""
    echo "  az containerapp revision restart \\"
    echo "    --name ca-api-qca-dev \\"
    echo "    --resource-group rg-qca-dev"
    echo ""
    exit 1
fi

# Restart the API container
echo "🔄 Restarting ca-api-qca-dev container..."
az containerapp revision restart \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev

if [ $? -eq 0 ]; then
    echo "✅ Restart command sent successfully"
    echo ""
    echo "⏱️  Waiting 30 seconds for container to restart..."
    sleep 30
    
    echo ""
    echo "🔍 Checking container logs for migration activity..."
    echo ""
    
    # Get recent logs
    LOGS=$(az containerapp logs show \
      --name ca-api-qca-dev \
      --resource-group rg-qca-dev \
      --tail 100 2>&1)
    
    # Look for migration-related output
    MIGRATION_LOGS=$(echo "$LOGS" | grep -E "(alembic|migration|Running upgrade|009.*010)" | tail -20)
    
    if [ -n "$MIGRATION_LOGS" ]; then
        echo "📋 Migration Activity Found:"
        echo "$MIGRATION_LOGS" | sed 's/^/   /'
        echo ""
        
        # Check if upgrade completed
        if echo "$MIGRATION_LOGS" | grep -q "Running upgrade.*009.*010"; then
            echo "✅ Migration 010 was applied successfully!"
            echo ""
            echo "🎉 Next Steps:"
            echo "   1. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)"
            echo "   2. The dashboard should now load without errors"
            echo "   3. If still errors, wait another 30 seconds and refresh again"
        else
            echo "⚠️  Migration logs found but upgrade not confirmed"
            echo "   Check full logs in Azure Portal"
        fi
    else
        echo "⚠️  No migration logs found yet"
        echo "   The container may still be starting up"
        echo ""
        echo "   Wait 30-60 more seconds, then check manually:"
        echo "   az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --tail 50"
    fi
    
    echo ""
    echo "📊 Container Status:"
    az containerapp show \
      --name ca-api-qca-dev \
      --resource-group rg-qca-dev \
      --query "{Status: properties.runningStatus, Replicas: properties.template.scale}" \
      -o table
      
else
    echo "❌ Failed to restart container"
    echo "   Please restart manually via Azure Portal:"
    echo "   1. Go to Azure Portal"
    echo "   2. Navigate to ca-api-qca-dev container app"
    echo "   3. Click 'Restart' button"
    exit 1
fi

echo ""
echo "✅ Done!"
echo ""
echo "🌐 Test your application:"
echo "   https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/dashboard"
