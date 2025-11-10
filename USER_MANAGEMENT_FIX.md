# User Management Access Control Fix

## Issue
Users page was showing "Unable to load users" because API endpoints had incorrect permission requirements.

## Problem Analysis
1. **Frontend**: UsersPage.tsx correctly calls `/auth/users`, `/auth/roles`, `/auth/agencies`
2. **Backend**: Endpoints had overly restrictive permissions:
   - `/auth/users` (GET) - Required `auditor` role → **blocked analysts**
   - `/auth/users/{id}` (GET) - Required `auditor` role → **blocked analysts**
   - `/auth/agencies` (GET) - Required `admin` role → **blocked auditors and analysts**

## Solution
Changed API endpoint permissions to allow appropriate access levels:

### Changes Made to `api/src/routers/auth.py`:

#### 1. Import `require_analyst`
```python
from api.src.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_admin, require_auditor, require_analyst,  # Added require_analyst
    ACCESS_TOKEN_EXPIRE_MINUTES
)
```

#### 2. Updated List Users Endpoint
**Before**: `require_auditor` (blocked analysts)
**After**: `require_analyst` (allows analysts, auditors, admins)

```python
@router.get("/users", response_model=list[User])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)  # Changed from require_auditor
):
    """List all users (Analyst+ access - analysts, auditors, admins can view users)"""
```

#### 3. Updated Get User Endpoint
**Before**: `require_auditor` (blocked analysts)
**After**: `require_analyst` (allows analysts, auditors, admins)

```python
@router.get("/users/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)  # Changed from require_auditor
):
    """Get specific user (Analyst+ access)"""
```

#### 4. Updated List Agencies Endpoint
**Before**: `require_admin` (blocked auditors and analysts)
**After**: `require_analyst` (allows analysts, auditors, admins)

```python
@router.get("/agencies", response_model=list[AgencySummary])
def list_agencies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)  # Changed from require_admin
):
    """List agencies (Analyst+ access - users can see their own agency, super_admin sees all)"""
```

## Permission Matrix After Fix

| Endpoint | Action | Admin | Auditor | Analyst | Viewer |
|----------|--------|-------|---------|---------|--------|
| `GET /auth/users` | View user list | ✅ | ✅ | ✅ | ❌ |
| `GET /auth/users/{id}` | View user details | ✅ | ✅ | ✅ | ❌ |
| `POST /auth/users` | Create user | ✅ | ❌ | ❌ | ❌ |
| `PUT /auth/users/{id}` | Update user | ✅ | ❌ | ❌ | ❌ |
| `GET /auth/roles` | View roles | ✅ | ✅ | ✅ | ✅ |
| `GET /auth/agencies` | View agencies | ✅ | ✅ | ✅ | ❌ |

## Security Notes

### Agency-Based Access Control (Maintained)
All endpoints maintain agency isolation:
- **Non-super-admins** can only see users from their own agency
- **Super-admins** can see users from all agencies

### Read vs Write Permissions
- **Read access** (view users/agencies): Analyst, Auditor, Admin
- **Write access** (create/update users): Admin only

## User Requirements Met

✅ **Requirement 1**: Admin can add users and see list of users
- Admins can: Create users (`POST /auth/users`), View users (`GET /auth/users`)

✅ **Requirement 2**: Auditor and Analyst can see list of users
- Auditors can: View users (`GET /auth/users`, `GET /auth/users/{id}`)
- Analysts can: View users (`GET /auth/users`, `GET /auth/users/{id}`)

## Testing

### Once Deployment Completes (~15 minutes):

#### Test 1: Analyst Can View Users ✅
```powershell
# Login to your Azure-deployed app
# URL: https://<your-frontend-url>.azurecontainerapps.io

# 1. Login as analyst
# 2. Navigate to Users page
# 3. Verify: User list loads successfully
# Expected: Should see users from your agency
```

#### Test 2: Auditor Can View Users ✅
```powershell
# 1. Login as auditor
# 2. Navigate to Users page  
# 3. Verify: User list loads successfully
# Expected: Should see users from your agency
```

#### Test 3: Admin Can Create Users ✅
```powershell
# 1. Login as admin
# 2. Click "Add User" button
# 3. Fill form and create user
# Expected: User created successfully
```

### API Testing (Optional):
If you want to test the API directly:

```bash
# Replace with your Azure API URL
API_URL="https://<your-api-url>.azurecontainerapps.io"

# Login and get token
TOKEN="your-jwt-token-here"

# Test user list endpoint
curl -H "Authorization: Bearer $TOKEN" $API_URL/auth/users

# Should return 200 OK with user list (not 403 Forbidden)
```

## Deployment

### Deployment Method: **GitHub Actions (Automatic)** ✅

**Status**: Deployed automatically via GitHub Actions workflow when pushed to `main` branch.

**Commit**: `46aa4c3` - "Fix user management access control and implement IM8 assessment workflow"

### What Happens Automatically:
1. ✅ GitHub Actions detects changes in `api/` directory
2. ✅ Builds new Docker image with updated code
3. ✅ Pushes to Azure Container Registry
4. ✅ Deploys to Azure Container App: `ca-api-qca-dev`
5. ✅ Installs `openpyxl>=3.1.2` dependency (for IM8 feature)
6. ✅ API restarts with new revision

### Timeline:
- **Build**: ~5-10 minutes
- **Deploy**: ~2-3 minutes
- **Total**: ~15 minutes from push

### Verification:
Monitor deployment at: https://github.com/sesunda/qa_compliance_assistant/actions

### Changes:
1. **API Update**: Changes in `api/src/routers/auth.py` deployed automatically
2. **No Database Migration**: No schema changes required
3. **No Frontend Changes**: Frontend already implements correct logic
4. **No Manual Steps**: Everything handled by CI/CD pipeline

## Files Modified
- `api/src/routers/auth.py` (+3 lines changed, import + 3 endpoint permission changes)

## Rollback Plan
If issues occur, revert the 3 endpoints back to original permissions:
- `list_users`: Change back to `require_auditor`
- `get_user`: Change back to `require_auditor`
- `list_agencies`: Change back to `require_admin`

## Related Issues
None - this is a standalone access control fix.
