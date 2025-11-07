#!/bin/bash
# Manual migration trigger via API endpoint

echo "🔧 Manually Triggering Database Migration"
echo "=========================================="
echo ""

API_URL="https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

echo "📡 Calling /admin/migrate endpoint..."
echo ""

RESPONSE=$(curl -X POST "$API_URL/admin/migrate" \
  -H "Content-Type: application/json" \
  -s -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Migration triggered successfully!"
    echo ""
    echo "📋 Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "🎉 Next Steps:"
    echo "   1. Wait 10 seconds for migration to complete"
    echo "   2. Refresh your browser (Ctrl+F5)"
    echo "   3. Dashboard should now load successfully"
else
    echo "❌ Migration trigger failed"
    echo ""
    echo "📋 Response:"
    echo "$BODY"
    echo ""
    echo "⚠️  This endpoint may not be accessible without authentication"
    echo "   or the API container needs to be restarted first"
    echo ""
    echo "   Try the restart method instead:"
    echo "   ./restart_api_container.sh"
fi
