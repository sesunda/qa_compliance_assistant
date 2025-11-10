# Evidence Tab Permissions - Analysis & Fix Required

**Date**: November 10, 2025  
**Issue**: Evidence upload permissions are incorrectly configured

---

## Current Problem ❌

### Evidence Upload Endpoint (`api/src/routers/evidence.py`)

**Line 50-58**:
```python
@router.post("/upload", response_model=schemas.Evidence)
async def upload_evidence(
    control_id: int = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)  # ❌ WRONG!
):
```

**Current Behavior**:
- ✅ Auditors CAN upload evidence
- ❌ Analysts CANNOT upload evidence

**Required Behavior**:
- ❌ Auditors CANNOT upload evidence (view only)
- ✅ Analysts CAN upload evidence (create + view)
- ✅ Auditors CAN view evidence (read only)

---

## Required Changes

### Change 1: Evidence Upload Permission

**File**: `api/src/routers/evidence.py`  
**Line**: 57

**BEFORE**:
```python
current_user: dict = Depends(require_auditor)
```

**AFTER**:
```python
current_user: dict = Depends(require_analyst)
```

**Impact**: 
- ✅ Analysts can now upload evidence
- ❌ Auditors cannot upload evidence (correct!)

---

### Change 2: Evidence Creation Endpoint

**File**: `api/src/routers/evidence.py`  
**Line**: 149

**BEFORE**:
```python
@router.post("/", response_model=schemas.Evidence)
def create_evidence(
    evidence: schemas.EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)  # ❌ WRONG!
):
```

**AFTER**:
```python
@router.post("/", response_model=schemas.Evidence)
def create_evidence(
    evidence: schemas.EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_analyst)  # ✅ CORRECT!
):
```

---

### Change 3: Keep View/List as Auditor+ (Correct)

These endpoints are already correct - auditors can view evidence:

✅ **GET /evidence** (line 234) - `require_auditor` (correct - auditors can list)  
✅ **GET /evidence/{id}** (line 253) - `require_auditor` (correct - auditors can view)  
✅ **GET /evidence/{id}/download** (line 311) - `require_auditor` (correct - auditors can download)

---

### Change 4: Keep Approval as Auditor (Correct)

These endpoints are already correct - only auditors can approve/reject:

✅ **POST /evidence/{id}/approve** (line 355) - `require_auditor` (correct)  
✅ **POST /evidence/{id}/reject** - `require_auditor` (correct)

---

## Summary of Permission Model

| Action | Auditor | Analyst | Viewer |
|--------|---------|---------|--------|
| **Upload Evidence** | ❌ No (view only) | ✅ Yes (primary responsibility) | ❌ No |
| **Create Evidence Record** | ❌ No | ✅ Yes | ❌ No |
| **View Evidence** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Download Evidence** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Approve Evidence** | ✅ Yes | ❌ No | ❌ No |
| **Reject Evidence** | ✅ Yes | ❌ No | ❌ No |
| **Set Up Controls** | ✅ Yes | ❌ No | ❌ No |

---

## Code Changes Required

### File: `api/src/routers/evidence.py`

**Change 1 - Line 57**:
```python
# CHANGE FROM:
current_user: dict = Depends(require_auditor)

# CHANGE TO:
current_user: dict = Depends(require_analyst)
```

**Change 2 - Line 149**:
```python
# CHANGE FROM:
current_user: dict = Depends(require_auditor)

# CHANGE TO:
current_user: dict = Depends(require_analyst)
```

**Total Changes**: 2 lines  
**Effort**: 5 minutes  
**Testing**: 15 minutes  
**Risk**: Low (simple permission change)

---

## Testing Checklist

After deploying changes:

### Test as Analyst:
- [ ] Can upload evidence via Evidence tab
- [ ] Can upload evidence via chat
- [ ] Can view all evidence
- [ ] Can download evidence files
- [ ] Cannot approve/reject evidence

### Test as Auditor:
- [ ] Cannot upload evidence via Evidence tab (403 Forbidden)
- [ ] Can view all evidence
- [ ] Can download evidence files
- [ ] Can approve evidence
- [ ] Can reject evidence with comments
- [ ] Can set up controls via Controls tab

### Test as Viewer:
- [ ] Cannot upload evidence (403 Forbidden)
- [ ] Can view evidence (read-only)
- [ ] Can download evidence files
- [ ] Cannot approve/reject evidence

---

## Frontend Impact

### Evidence Tab UI Updates Required

**File**: `frontend/src/pages/EvidencePage.tsx` (or similar)

**Required Changes**:
1. Hide "Upload Evidence" button for Auditors
2. Show "Upload Evidence" button for Analysts
3. Show "View Only" badge for Auditors

**Example Code**:
```typescript
const canUploadEvidence = currentUser.role === 'analyst' || currentUser.role === 'admin';

{canUploadEvidence && (
  <Button onClick={handleUploadEvidence}>
    Upload Evidence
  </Button>
)}

{!canUploadEvidence && currentUser.role === 'auditor' && (
  <Chip label="View Only - Analysts Upload Evidence" color="info" />
)}
```

---

## Rollout Plan

### Step 1: Backend API Changes (5 min)
- Change `require_auditor` → `require_analyst` in 2 places
- Commit: "Fix evidence upload permissions - analysts only"

### Step 2: Test API (15 min)
- Test with analyst token → Should work ✅
- Test with auditor token → Should get 403 ❌
- Test with viewer token → Should get 403 ❌

### Step 3: Frontend UI Update (30 min)
- Hide upload button for auditors
- Show "View Only" indicator
- Test UI with all three roles

### Step 4: Deploy to Azure (15 min)
- Push to main branch
- GitHub Actions auto-deploys
- Monitor deployment logs

### Step 5: User Communication (5 min)
- Notify auditors: "Evidence upload is now analyst-only. You can view and approve evidence."
- Notify analysts: "You can now upload evidence via Evidence tab or chat."

**Total Time**: ~70 minutes

---

## Conversation Flow Summary

### Auditor Control Setup Flow ✅ IMPLEMENTED
```
Auditor: "Set up IM8 controls"
LLM: "Which project?" → "Which domains?" → "Confirm?" → Creates task
```

### Analyst Evidence Upload Flow ✅ IMPLEMENTED (Just Added)
```
Analyst: "Upload evidence"
LLM: "Which control?" → "Evidence details?" → "Attach file" → "Metadata?" → "Confirm?" → Uploads evidence
```

---

## Recommendation

**PROCEED WITH CHANGES**:
1. ✅ Commit analyst evidence upload conversation flow (already done above)
2. ✅ Fix evidence upload permissions (2 lines changed)
3. ✅ Update frontend Evidence tab UI (hide upload for auditors)
4. ✅ Deploy and test

**Priority**: HIGH (blocking analyst workflow)  
**Risk**: LOW (simple permission fix)  
**Effort**: 1-2 hours total

---

**Status**: Analysis complete, awaiting confirmation to proceed with permission fixes
