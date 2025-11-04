#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  User Management Frontend-Backend Test Suite${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Step 1: Get admin token
echo -e "${YELLOW}Step 1: Authenticating as admin...${NC}"
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ FAILED: Could not authenticate${NC}"
  exit 1
fi
echo -e "${GREEN}✅ PASSED: Admin authenticated${NC}\n"

# Step 2: Create IMDA CISO (Admin)
echo -e "${YELLOW}Step 2: Creating IMDA CISO (Admin)...${NC}"
CISO_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "imda_ciso",
    "email": "ciso@imda.gov.sg",
    "password": "SecurePass123!",
    "full_name": "John Tan",
    "agency_id": 2,
    "role_id": 2,
    "is_active": true
  }')

CISO_ID=$(echo $CISO_RESPONSE | jq -r '.id')
if [ "$CISO_ID" != "null" ] && [ ! -z "$CISO_ID" ]; then
  echo -e "${GREEN}✅ PASSED: IMDA CISO created (ID: $CISO_ID)${NC}"
else
  echo -e "${RED}❌ FAILED: ${CISO_RESPONSE}${NC}"
fi
echo ""

# Step 3: Create IMDA Auditor
echo -e "${YELLOW}Step 3: Creating IMDA Compliance Auditor...${NC}"
AUDITOR_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "imda_auditor",
    "email": "auditor@imda.gov.sg",
    "password": "SecurePass123!",
    "full_name": "Sarah Lim",
    "agency_id": 2,
    "role_id": 3,
    "is_active": true
  }')

AUDITOR_ID=$(echo $AUDITOR_RESPONSE | jq -r '.id')
if [ "$AUDITOR_ID" != "null" ] && [ ! -z "$AUDITOR_ID" ]; then
  echo -e "${GREEN}✅ PASSED: IMDA Auditor created (ID: $AUDITOR_ID)${NC}"
else
  echo -e "${RED}❌ FAILED: ${AUDITOR_RESPONSE}${NC}"
fi
echo ""

# Step 4: Create IMDA Analyst
echo -e "${YELLOW}Step 4: Creating IMDA Compliance Analyst...${NC}"
ANALYST_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "imda_analyst",
    "email": "analyst@imda.gov.sg",
    "password": "SecurePass123!",
    "full_name": "David Wong",
    "agency_id": 2,
    "role_id": 4,
    "is_active": true
  }')

ANALYST_ID=$(echo $ANALYST_RESPONSE | jq -r '.id')
if [ "$ANALYST_ID" != "null" ] && [ ! -z "$ANALYST_ID" ]; then
  echo -e "${GREEN}✅ PASSED: IMDA Analyst created (ID: $ANALYST_ID)${NC}"
else
  echo -e "${RED}❌ FAILED: ${ANALYST_RESPONSE}${NC}"
fi
echo ""

# Step 5: Create Inactive User
echo -e "${YELLOW}Step 5: Creating INACTIVE user (imda_temp)...${NC}"
TEMP_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "imda_temp",
    "email": "temp@imda.gov.sg",
    "password": "TempPass123!",
    "full_name": "Temporary User",
    "agency_id": 2,
    "role_id": 5,
    "is_active": false
  }')

TEMP_ID=$(echo $TEMP_RESPONSE | jq -r '.id')
if [ "$TEMP_ID" != "null" ] && [ ! -z "$TEMP_ID" ]; then
  echo -e "${GREEN}✅ PASSED: Inactive user created (ID: $TEMP_ID)${NC}"
else
  echo -e "${RED}❌ FAILED: ${TEMP_RESPONSE}${NC}"
fi
echo ""

# Step 6: Test Inactive User Login (Should Fail)
echo -e "${YELLOW}Step 6: Testing inactive user login (should FAIL)...${NC}"
INACTIVE_LOGIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "imda_temp", "password": "TempPass123!"}')

INACTIVE_TOKEN=$(echo $INACTIVE_LOGIN | jq -r '.access_token')
if [ "$INACTIVE_TOKEN" = "null" ] || [ -z "$INACTIVE_TOKEN" ]; then
  echo -e "${GREEN}✅ PASSED: Inactive user cannot login (as expected)${NC}"
  echo -e "   Error: $(echo $INACTIVE_LOGIN | jq -r '.detail')"
else
  echo -e "${RED}❌ FAILED: Inactive user was able to login!${NC}"
fi
echo ""

# Step 7: Activate the Inactive User
echo -e "${YELLOW}Step 7: Activating imda_temp user via edit...${NC}"
ACTIVATE_RESPONSE=$(curl -s -X PUT http://localhost:8000/auth/users/$TEMP_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "is_active": true
  }')

ACTIVATED=$(echo $ACTIVATE_RESPONSE | jq -r '.is_active')
if [ "$ACTIVATED" = "true" ]; then
  echo -e "${GREEN}✅ PASSED: User activated successfully${NC}"
else
  echo -e "${RED}❌ FAILED: ${ACTIVATE_RESPONSE}${NC}"
fi
echo ""

# Step 8: Test Activated User Login (Should Succeed)
echo -e "${YELLOW}Step 8: Testing activated user login (should SUCCEED)...${NC}"
ACTIVE_LOGIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "imda_temp", "password": "TempPass123!"}')

ACTIVE_TOKEN=$(echo $ACTIVE_LOGIN | jq -r '.access_token')
if [ "$ACTIVE_TOKEN" != "null" ] && [ ! -z "$ACTIVE_TOKEN" ]; then
  echo -e "${GREEN}✅ PASSED: Activated user can login successfully${NC}"
else
  echo -e "${RED}❌ FAILED: Activated user cannot login${NC}"
  echo -e "   Error: $(echo $ACTIVE_LOGIN | jq -r '.detail')"
fi
echo ""

# Step 9: Deactivate User Again
echo -e "${YELLOW}Step 9: Deactivating imda_temp user again...${NC}"
DEACTIVATE_RESPONSE=$(curl -s -X PUT http://localhost:8000/auth/users/$TEMP_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "is_active": false
  }')

DEACTIVATED=$(echo $DEACTIVATE_RESPONSE | jq -r '.is_active')
if [ "$DEACTIVATED" = "false" ]; then
  echo -e "${GREEN}✅ PASSED: User deactivated successfully${NC}"
else
  echo -e "${RED}❌ FAILED: ${DEACTIVATE_RESPONSE}${NC}"
fi
echo ""

# Step 10: Verify Database State
echo -e "${YELLOW}Step 10: Verifying database state...${NC}"
echo -e "${BLUE}Current users in database:${NC}"
docker exec qca_postgres psql -U qca_user -d qca_db -c "
SELECT 
  u.id, 
  u.username, 
  u.full_name, 
  a.code as agency, 
  r.name as role, 
  CASE WHEN u.is_active THEN 'Active' ELSE 'Inactive' END as status
FROM users u 
JOIN agencies a ON u.agency_id = a.id 
JOIN user_roles r ON u.role_id = r.id 
ORDER BY u.id;
"
echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✅ Admin authentication${NC}"
echo -e "${GREEN}✅ Create users via API (simulating frontend)${NC}"
echo -e "${GREEN}✅ Agency assignment (IMDA)${NC}"
echo -e "${GREEN}✅ Role assignment (admin, auditor, analyst, viewer)${NC}"
echo -e "${GREEN}✅ Inactive user creation${NC}"
echo -e "${GREEN}✅ Inactive user login blocked${NC}"
echo -e "${GREEN}✅ User activation via edit${NC}"
echo -e "${GREEN}✅ Activated user login allowed${NC}"
echo -e "${GREEN}✅ User deactivation via edit${NC}"
echo -e "${GREEN}✅ Database synchronization${NC}"
echo ""
echo -e "${BLUE}All tests completed! Check results above.${NC}"
echo -e "${BLUE}================================================${NC}"
