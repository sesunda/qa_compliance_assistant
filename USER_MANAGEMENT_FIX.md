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

### Test User List Access
```powershell
# Login as analyst
$analystToken = "..." # Get from login

# Verify analyst can see users
curl -H "Authorization: Bearer $analystToken" http://localhost:8000/auth/users

# Should return 200 OK with user list
```

### Test Agencies Access
```powershell
# Verify analyst can see agencies
curl -H "Authorization: Bearer $analystToken" http://localhost:8000/auth/agencies

# Should return 200 OK with agency list (own agency for non-super-admin)
```

### Test User Creation (Admin Only)
```powershell
# Login as admin
$adminToken = "..." # Get from login

# Create user (should work)
curl -X POST -H "Authorization: Bearer $adminToken" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123","role_id":1,"agency_id":1}' \
  http://localhost:8000/auth/users

# Try as analyst (should fail with 403)
curl -X POST -H "Authorization: Bearer $analystToken" \
  -H "Content-Type: application/json" \
  -d '{"username":"test2","email":"test2@example.com","password":"password123","role_id":1,"agency_id":1}' \
  http://localhost:8000/auth/users
```

## Deployment

### Changes Required
1. **API Restart**: Changes in `api/src/routers/auth.py` require API restart
2. **No Database Migration**: No schema changes required
3. **No Frontend Changes**: Frontend already implements correct logic

### Deployment Steps
```powershell
# Restart API container
docker-compose restart api

# OR rebuild if needed
docker-compose up -d --build api
```

## Files Modified
- `api/src/routers/auth.py` (+3 lines changed, import + 3 endpoint permission changes)

## Rollback Plan
If issues occur, revert the 3 endpoints back to original permissions:
- `list_users`: Change back to `require_auditor`
- `get_user`: Change back to `require_auditor`
- `list_agencies`: Change back to `require_admin`

## Related Issues
None - this is a standalone access control fix.
