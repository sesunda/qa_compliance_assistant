# Testing Checklist - Bug Fixes Deployed (Nov 15, 2025)

## ⚠️ IMPORTANT: Hard Refresh Required
Before testing, perform a **hard refresh** in your browser:
- **Windows/Linux**: `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac**: `Cmd + Shift + R`

This is required to clear cached JavaScript and load the latest frontend code.

---

## Test 1: Login Fix ✅
**Status**: CONFIRMED WORKING

**Test Steps**:
- Navigate to login page
- Enter Edward's credentials
- Click login once
- **Expected**: Login succeeds on first attempt (no double login needed)

**Result**: ✅ Working (confirmed by user)

---

## Test 2: Approve/Reject Buttons 🔄
**Status**: PENDING HARD REFRESH

**Test Steps**:
1. **Hard refresh browser** (Ctrl+Shift+R)
2. Login as Edward (Auditor role)
3. Navigate to Evidence page
4. Find evidence with status "Under Review"
5. **Expected**: Approve and Reject buttons visible for evidence submitted by others

**Technical Details**:
- Database fix applied: Edward's role (ID: 9) now has proper permissions
- Updated `user_roles` table with JSONB permissions: `evidence: ['read', 'update']`
- Frontend checks: `user?.permissions?.evidence?.includes('update')`

**Result**: _Awaiting test after hard refresh_

---

## Test 3: Session Restoration (Alice) 🔄
**Status**: PENDING HARD REFRESH

**Test Steps**:
1. **Hard refresh browser** (Ctrl+Shift+R)
2. Login as Alice (Analyst role)
3. Navigate to Agentic Chat
4. Send 2-3 messages in conversation
5. Navigate away to another page (e.g., Projects)
6. Return to Agentic Chat
7. **Expected**: Previous conversation messages still displayed (no welcome message)

**Technical Details**:
- Frontend fix deployed: Commit b86ac3a
- Added `isRestoringSession` flag to prevent welcome message during restoration
- ACR build ccv completed (1m 36s), container app updated

**Result**: _Awaiting test after hard refresh_

---

## Deployment Status

### API Container (Login Fix)
- **Build ID**: ccu
- **Duration**: 7m 48s
- **Status**: ✅ Deployed
- **Image**: `acrqcadev2f37g0.azurecr.io/api:latest`
- **Fix**: SQLAlchemy eager loading for role/agency relationships

### Frontend Container (Session Fix)
- **Build ID**: ccv
- **Duration**: 1m 36s
- **Status**: ✅ Deployed
- **Image**: `acrqcadev2f37g0.azurecr.io/frontend:latest`
- **Fix**: isRestoringSession flag to prevent duplicate welcome messages

### Database (Permissions Fix)
- **Script**: fix_role_permissions_azure.py
- **Status**: ✅ Executed
- **Fixed Roles**: 
  - Auditor (ID: 9) - Edward's role ✅
  - Admin (ID: 6) ✅
  - Analyst (ID: 7) ✅
  - Plus 5 lowercase roles (IDs 1-5) ✅

---

## Next Steps

1. **Perform hard refresh** in browser (Ctrl+Shift+R)
2. **Test scenarios 2 & 3** as outlined above
3. **Report results** - note any issues or unexpected behavior
4. If all tests pass → Proceed with resource cleanup (optional cost optimization)

---

## Known Issues & Notes

- **Cache Problem**: Browser may cache old frontend JavaScript - hard refresh is mandatory
- **Database Password**: Exposed in command history (`admin123`) - consider rotating
- **Duplicate Roles**: Database has both lowercase and uppercase role names (e.g., 'auditor' and 'Auditor') - may need cleanup later

---

## Contact Info

- **Database**: `psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db`
- **API**: `ca-api-qca-dev.westus2.azurecontainerapps.io`
- **Frontend**: `ca-frontend-qca-dev.westus2.azurecontainerapps.io`
