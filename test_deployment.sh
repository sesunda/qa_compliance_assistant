#!/bin/bash
# Quick test script for deployed application

echo "🔍 Testing Deployed Azure Application"
echo "======================================"
echo ""

# Get frontend URL
echo "📍 Getting Frontend URL..."
FRONTEND_URL=$(az containerapp show \
  --name ca-frontend-qca-dev \
  --resource-group rg-qca-dev \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$FRONTEND_URL" ]; then
  echo "✅ Frontend: https://$FRONTEND_URL"
else
  echo "❌ Could not get frontend URL (az CLI not available or not logged in)"
  echo "   Please check Azure Portal manually"
fi

echo ""

# Get API URL
echo "📍 Getting API URL..."
API_URL=$(az containerapp show \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$API_URL" ]; then
  echo "✅ API: https://$API_URL"
  
  echo ""
  echo "🔍 Testing API Endpoints..."
  
  # Test health endpoint
  echo -n "   /health: "
  if curl -s -f "https://$API_URL/health" >/dev/null 2>&1; then
    echo "✅ OK"
  else
    echo "❌ FAILED"
  fi
  
  # Test root endpoint
  echo -n "   /: "
  if curl -s -f "https://$API_URL/" >/dev/null 2>&1; then
    echo "✅ OK"
  else
    echo "❌ FAILED"
  fi
  
else
  echo "❌ Could not get API URL (az CLI not available or not logged in)"
fi

echo ""
echo "📋 Default Login Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""

# Check container logs for migration status
echo "🔍 Checking Migration Status..."
if command -v az &> /dev/null; then
  MIGRATION_LOG=$(az containerapp logs show \
    --name ca-api-qca-dev \
    --resource-group rg-qca-dev \
    --tail 200 2>/dev/null | grep -E "(alembic|Running upgrade|migration)" | tail -10)
  
  if [ -n "$MIGRATION_LOG" ]; then
    echo "   Recent migration activity:"
    echo "$MIGRATION_LOG" | sed 's/^/   /'
  else
    echo "   ⚠️  No migration logs found in recent output"
    echo "   This might mean:"
    echo "      - Container hasn't restarted since startup.sh was added"
    echo "      - Migrations ran successfully earlier"
    echo "      - Need to check full logs in Azure Portal"
  fi
else
  echo "   ⚠️  az CLI not available - check Azure Portal for logs"
fi

echo ""
echo "✅ Test Complete!"
echo ""
echo "Next Steps:"
echo "1. Visit the frontend URL in your browser"
echo "2. Login with admin/admin123"
echo "3. If you see errors, check browser console (F12)"
echo "4. Report any API errors you encounter"
