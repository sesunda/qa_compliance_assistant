#!/bin/bash
# Check API endpoints status

API_URL="https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

echo "🔍 Testing API Endpoints"
echo "======================="
echo ""

echo "1. Health Check:"
curl -s "$API_URL/health" | python3 -m json.tool 2>/dev/null || echo "FAILED"
echo ""

echo "2. Root Endpoint:"
curl -s "$API_URL/" | python3 -m json.tool 2>/dev/null || echo "FAILED"
echo ""

echo "3. Analytics Dashboard (needs auth):"
curl -s -w "\nHTTP Status: %{http_code}\n" "$API_URL/analytics/dashboard" 2>/dev/null
echo ""

echo "4. Assessments List (needs auth):"
curl -s -w "\nHTTP Status: %{http_code}\n" "$API_URL/assessments" 2>/dev/null
echo ""

echo "5. Checking if container is responding:"
if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding - container may not be running"
fi
