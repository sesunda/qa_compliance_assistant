#!/bin/bash

# QCA API Test Script
# This script tests all API endpoints to ensure they are working correctly

set -e

echo "=========================================="
echo "Testing Quantique Compliance Assistant API"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local endpoint=$2
    local method=${3:-GET}
    local data=${4:-}
    
    echo -n "Testing $name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -X $method "http://localhost:8000$endpoint")
    else
        response=$(curl -s -X $method "http://localhost:8000$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    if [ -z "$response" ]; then
        echo -e "${RED}FAILED${NC}"
        return 1
    else
        echo -e "${GREEN}PASSED${NC}"
        return 0
    fi
}

# Test API root
test_endpoint "API Root" "/"

# Test health endpoint
test_endpoint "Health Check" "/health"

# Test projects endpoints
echo ""
echo "Testing Projects..."
test_endpoint "List Projects" "/projects/"
test_endpoint "Create Project" "/projects/" "POST" '{"name":"Test Project","description":"Test Description","status":"active"}'
test_endpoint "Get Project" "/projects/1"
test_endpoint "Update Project" "/projects/1" "PUT" '{"status":"completed"}'

# Test controls endpoints
echo ""
echo "Testing Controls..."
test_endpoint "List Controls" "/controls/"
test_endpoint "Create Control" "/controls/" "POST" '{"project_id":1,"name":"Test Control","description":"Test Control Description","control_type":"security","status":"active"}'
test_endpoint "Get Control" "/controls/1"

# Test evidence endpoints
echo ""
echo "Testing Evidence..."
test_endpoint "List Evidence" "/evidence/"
test_endpoint "Create Evidence" "/evidence/" "POST" '{"control_id":1,"title":"Test Evidence","description":"Test Evidence Description","evidence_type":"document","verified":true}'
test_endpoint "Get Evidence" "/evidence/1"

# Test reports endpoints
echo ""
echo "Testing Reports..."
test_endpoint "List Reports" "/reports/"
test_endpoint "Create Report" "/reports/" "POST" '{"project_id":1,"title":"Test Report","content":"Test Report Content","report_type":"quarterly"}'
test_endpoint "Get Report" "/reports/1"

echo ""
echo "=========================================="
echo "Testing MCP Server"
echo "=========================================="
echo ""

# Test MCP Server
echo -n "Testing MCP Server Root... "
response=$(curl -s http://localhost:8001/)
if [ -z "$response" ]; then
    echo -e "${RED}FAILED${NC}"
else
    echo -e "${GREEN}PASSED${NC}"
fi

echo -n "Testing Sample Evidence... "
response=$(curl -s http://localhost:8001/sample-evidence)
if [ -z "$response" ]; then
    echo -e "${RED}FAILED${NC}"
else
    echo -e "${GREEN}PASSED${NC}"
fi

echo -n "Testing Sample Evidence by ID... "
response=$(curl -s http://localhost:8001/sample-evidence/1)
if [ -z "$response" ]; then
    echo -e "${RED}FAILED${NC}"
else
    echo -e "${GREEN}PASSED${NC}"
fi

echo ""
echo "=========================================="
echo "All tests completed!"
echo "=========================================="
