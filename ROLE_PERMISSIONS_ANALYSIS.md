# Role Permissions Analysis - Project and Control Creation

## 📋 Executive Summary

**CONFUSION IDENTIFIED**: The AI assistant is incorrectly blocking auditors from creating projects. The screenshot shows:
> "Unfortunately, I cannot create projects directly. Please reach out to the appropriate personnel or system admin to set up the 'Health Sciences Project'."

This is **WRONG** behavior based on your clarified requirements.

---

## ✅ **CORRECT Role Permissions (Per Your Requirements)**

### **AUDITOR Role Permissions:**
1. ✅ **CAN create projects** (via Projects page or AI conversation)
2. ✅ **CAN set up IM8 controls** (tie controls to projects they created)
3. ✅ **CAN review and approve/reject evidence** (checker role in maker-checker workflow)
4. ❌ **CANNOT upload evidence** (separation of duties)

### **ANALYST Role Permissions:**
1. ❌ **CANNOT create projects**
2. ❌ **CANNOT create controls**
3. ✅ **CAN upload evidence** (ONLY for controls tied to their agency)
4. ✅ **CAN submit evidence for review** (maker role in maker-checker workflow)
5. ⚠️ **MUST be filtered by agency** - Can only see/upload to their own agency's projects/controls

---

## 🐛 **Root Causes of Confusion**

### **Issue 1: Backend API Has NO Authentication on Project/Control Creation**

**Current State:**
```python
# api/src/routers/projects.py
@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    # ❌ NO AUTHENTICATION - Anyone can create projects!
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    return db_project

# api/src/routers/controls.py
@router.post("/", response_model=schemas.Control)
def create_control(control: schemas.ControlCreate, db: Session = Depends(get_db)):
    # ❌ NO AUTHENTICATION - Anyone can create controls!
    db_control = models.Control(**control.model_dump())
    db.add(db_control)
    db.commit()
    return db_control
```

**Impact:**
- NO role-based access control on these endpoints
- Auditors, analysts, viewers - EVERYONE can create projects/controls via API
- No enforcement of "analysts cannot create" rule
- No enforcement of "auditors can create" rule

---

### **Issue 2: Frontend Has NO Role-Based UI Restrictions**

**Current State:**
```tsx
// frontend/src/pages/ProjectsPage.tsx
const ProjectsPage: React.FC = () => {
  // ❌ NO role checking - Shows "Add Project" button to everyone
  return (
    <Button startIcon={<Add />} onClick={handleOpen}>
      Add Project
    </Button>
  );
};

// frontend/src/pages/ControlsPage.tsx
const ControlsPage: React.FC = () => {
  // ❌ NO role checking - Shows "Add Control" button to everyone
  return (
    <Button startIcon={<Add />} variant="contained">
      Add Control
    </Button>
  );
};
```

**Impact:**
- No role-based hiding of create buttons
- Analysts see "Add Project" and "Add Control" buttons (shouldn't see them)
- Auditors see buttons (correct, but no guidance)

---

### **Issue 3: AI Assistant Has NO Project Creation Tool**

**Current State:**
```python
# api/src/services/agentic_assistant.py
task_type_map = {
    "upload_evidence": "fetch_evidence",
    "fetch_evidence": "fetch_evidence",
    "analyze_compliance": "analyze_compliance",
    "generate_report": "generate_report",
    "submit_for_review": "submit_for_review"
    # ❌ NO "create_project" mapping!
}
```

**Impact:**
- AI assistant cannot create projects via conversation
- When auditor asks "create project", AI responds: "I cannot create projects directly"
- This is what you saw in the screenshot
- AI was being truthful - it literally cannot create projects programmatically

---

### **Issue 4: AI Prompts Don't Guide Project Creation**

**Current State:**
```python
# Auditor prompt (lines 325-350)
**Step 1: Ask for Project (with Agency Filtering)**
"Which project should I add the IM8 controls to?
...
- Say 'create new project' if you need to set up a new project first"
```

**Issue:**
- Prompt mentions "create new project" option
- But AI has NO TOOL to actually create it
- AI can only suggest: "Go to Projects page" or "Contact admin"
- Creates user frustration

---

## 🔍 **What Actually Works vs What Doesn't**

### ✅ **What Works:**
1. **Direct API calls** - `POST /projects` and `POST /controls` work (no auth checks)
2. **Frontend CRUD** - Projects and Controls pages can create/edit/delete
3. **AI control setup** - `create_controls` AI task generates controls via background worker
4. **Evidence upload restrictions** - Just fixed (analysts only) ✅
5. **Multi-tenant filtering** - AI prompts now filter by agency_id ✅

### ❌ **What Doesn't Work:**
1. **AI project creation** - No tool/handler for `create_project` task
2. **Role-based API enforcement** - No `require_auditor` on project/control endpoints
3. **Frontend role restrictions** - No hiding of buttons based on role
4. **Conversational project creation** - AI cannot guide auditors through project setup

---

## 🎯 **Gap Analysis**

| **Requirement** | **Backend API** | **Frontend UI** | **AI Assistant** | **Status** |
|-----------------|-----------------|-----------------|------------------|------------|
| Auditor can create projects | ✅ No auth (everyone can) | ✅ Button visible | ❌ No tool | **Partially works** |
| Auditor can create controls | ✅ No auth (everyone can) | ✅ Button visible | ✅ AI task handler | **Works** |
| Analyst cannot create projects | ❌ No restriction | ❌ Button visible | ❌ No check | **NOT enforced** |
| Analyst cannot create controls | ❌ No restriction | ❌ Button visible | ⚠️ Could use AI task | **NOT enforced** |
| Analyst can upload evidence | ✅ require_analyst | ⚠️ No role check | ✅ Conversational flow | **Works (API)** |
| Agency isolation in AI | N/A | N/A | ✅ Just implemented | **Works** |

---

## 📊 **Current vs Required State**

### **Projects Endpoint:**

**Current:**
```python
@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
```

**Required:**
```python
@router.post("/", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)  # ← Add this
):
    # Automatically set agency_id from current user
    project_data = project.model_dump()
    project_data["agency_id"] = current_user["agency_id"]
    
    db_project = models.Project(**project_data)
    db.add(db_project)
    db.commit()
    return db_project
```

**Changes:**
1. Add `require_auditor` dependency → Only auditors can create
2. Auto-set `agency_id` from JWT token → Ensures multi-tenant isolation
3. Analysts will get `403 Forbidden` if they try

---

### **Controls Endpoint:**

**Current:**
```python
@router.post("/", response_model=schemas.Control)
def create_control(control: schemas.ControlCreate, db: Session = Depends(get_db)):
```

**Required:**
```python
@router.post("/", response_model=schemas.Control)
def create_control(
    control: schemas.ControlCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auditor)  # ← Add this
):
    # Verify project exists and belongs to user's agency
    project = db.query(models.Project).filter(models.Project.id == control.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not check_agency_access(current_user, project.agency_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    control_data = control.model_dump()
    control_data["agency_id"] = current_user["agency_id"]
    
    db_control = models.Control(**control_data)
    db.add(db_control)
    db.commit()
    return db_control
```

**Changes:**
1. Add `require_auditor` dependency → Only auditors can create
2. Validate project belongs to user's agency
3. Auto-set `agency_id` from JWT token
4. Analysts will get `403 Forbidden` if they try

---

### **Frontend ProjectsPage:**

**Required Changes:**
```tsx
import { useAuth } from '../context/AuthContext'; // Add this

const ProjectsPage: React.FC = () => {
  const { user } = useAuth(); // Get current user
  
  const canCreateProject = user?.role === 'auditor' || user?.role === 'super_admin';
  
  return (
    <>
      {canCreateProject && (
        <Button startIcon={<Add />} onClick={handleOpen}>
          Add Project
        </Button>
      )}
    </>
  );
};
```

**Changes:**
1. Import `useAuth` hook to get current user role
2. Calculate `canCreateProject` based on role
3. Conditionally render "Add Project" button
4. Analysts won't see the button

---

### **Frontend ControlsPage:**

**Required Changes:**
```tsx
import { useAuth } from '../context/AuthContext'; // Add this

const ControlsPage: React.FC = () => {
  const { user } = useAuth(); // Get current user
  
  const canCreateControl = user?.role === 'auditor' || user?.role === 'super_admin';
  
  return (
    <>
      {canCreateControl && (
        <Button startIcon={<Add />} variant="contained">
          Add Control
        </Button>
      )}
    </>
  );
};
```

---

### **AI Assistant - Add Project Creation Tool:**

**Required: New Task Handler:**
```python
# api/src/workers/task_handlers.py

async def handle_create_project_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Create a new project
    
    Payload:
        name: str - Project name
        description: str - Project description
        project_type: str - Type of project
        agency_id: int - Agency ID (from current user)
        created_by: int - User ID who created it
    """
    logger.info(f"Create project task {task_id} started")
    await update_progress(task_id, 20, "Creating project...")
    
    try:
        from api.src.models import Project
        
        project = Project(
            name=payload["name"],
            description=payload.get("description", ""),
            project_type=payload.get("project_type", "compliance_assessment"),
            status="pending",
            agency_id=payload["agency_id"],
            start_date=payload.get("start_date")
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        await update_progress(task_id, 100, f"Project '{project.name}' created successfully")
        
        return {
            "status": "success",
            "message": f"Project '{project.name}' created successfully",
            "project_id": project.id,
            "project_name": project.name
        }
    
    except Exception as e:
        logger.error(f"Create project task {task_id} failed: {e}")
        return {
            "status": "error",
            "message": f"Failed to create project: {str(e)}"
        }

# Add to TASK_HANDLERS
TASK_HANDLERS = {
    # ... existing handlers
    "create_project": handle_create_project_task,  # ← Add this
}
```

**Required: Update AI Assistant Tool Mapping:**
```python
# api/src/services/agentic_assistant.py (line ~930)

task_type_map = {
    "create_project": "create_project",  # ← Add this
    "upload_evidence": "fetch_evidence",
    "fetch_evidence": "fetch_evidence",
    "analyze_compliance": "analyze_compliance",
    "generate_report": "generate_report",
    "submit_for_review": "submit_for_review"
}
```

**Required: Update Auditor Prompt:**
```python
# Add to auditor prompt (after Step 1 Ask for Project)

**Option B: Create New Project**
If auditor says "create new project" or "I need to set up a new project":
1. Ask for project details:
   - Project name (required)
   - Project description
   - Project type (compliance_assessment, security_audit, risk_management)
   - Start date (YYYY-MM-DD format)

2. Confirm details:
   "I will create a new project:
   - Name: {name}
   - Description: {description}
   - Type: {type}
   - Agency: {agency_name}
   
   Shall I proceed?"

3. Create AI task:
   - Task type: "create_project"
   - Payload: {name, description, project_type, agency_id, start_date}
   
4. Return: "✅ I've created Project '{name}' (ID: {project_id}) for your agency. You can now set up IM8 controls for this project. Would you like to proceed with control setup?"
```

---

## 🚨 **Critical Security Gap**

**CURRENT PROBLEM:**
- **NO authentication** on project/control creation endpoints
- Anyone can hit the API directly and create projects/controls
- Analysts can create projects/controls via API (even though UI might hide buttons)
- No multi-tenant isolation enforcement at API level

**RISK:**
- Analyst from Agency A could create projects for Agency B (if they know the agency_id)
- No audit trail of who created what
- Violates separation of duties principle

**SOLUTION:**
Must add `require_auditor` to both endpoints + enforce agency_id from JWT token.

---

## 📝 **Recommended Fixes (In Priority Order)**

### **Priority 1: Backend API Authentication (CRITICAL)**
**Files:** `api/src/routers/projects.py`, `api/src/routers/controls.py`
**Action:** Add `require_auditor` dependency to `create_project()` and `create_control()`
**Impact:** Enforces "only auditors can create" at API level
**Effort:** 10 lines of code
**Risk:** Low - existing auditor flows continue working

### **Priority 2: Frontend Role-Based UI**
**Files:** `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/ControlsPage.tsx`
**Action:** Hide "Add Project" and "Add Control" buttons for non-auditor roles
**Impact:** Cleaner UX, prevents confusion
**Effort:** 15 lines of code
**Risk:** Low - just UI changes

### **Priority 3: AI Project Creation Tool**
**Files:** `api/src/workers/task_handlers.py`, `api/src/services/agentic_assistant.py`
**Action:** Add `create_project` task handler and AI tool mapping
**Impact:** Enables conversational project creation via AI
**Effort:** 60 lines of code (new handler + prompt updates)
**Risk:** Medium - new feature, needs testing

### **Priority 4: Update AI Prompts**
**Files:** `api/src/services/agentic_assistant.py`
**Action:** Add project creation conversation flow to auditor prompt
**Impact:** AI can guide auditors through project creation
**Effort:** 30 lines (prompt text)
**Risk:** Low - just documentation

---

## 🧪 **Testing Checklist**

### **After Priority 1 Fix (Backend API):**
- [ ] Login as auditor → POST /projects → Should succeed (201)
- [ ] Login as analyst → POST /projects → Should fail (403)
- [ ] Login as auditor → POST /controls → Should succeed (201)
- [ ] Login as analyst → POST /controls → Should fail (403)
- [ ] Verify agency_id auto-set from JWT token
- [ ] Cross-agency attempt should fail (403)

### **After Priority 2 Fix (Frontend UI):**
- [ ] Login as auditor → See "Add Project" button
- [ ] Login as analyst → "Add Project" button hidden
- [ ] Login as auditor → See "Add Control" button
- [ ] Login as analyst → "Add Control" button hidden
- [ ] Login as viewer → Both buttons hidden

### **After Priority 3 Fix (AI Tool):**
- [ ] Login as auditor → Tell AI "create project Health Sciences"
- [ ] AI should ask for details (description, type, start date)
- [ ] Confirm → AI creates task → Task executes → Project created
- [ ] Verify project.agency_id matches auditor's agency
- [ ] Verify project appears in Projects page
- [ ] Login as analyst → Tell AI "create project" → Should refuse

### **After Priority 4 Fix (AI Prompts):**
- [ ] AI should guide through project creation step-by-step
- [ ] AI should show confirmation before creating
- [ ] AI should link to "set up controls" after project creation
- [ ] AI should respect agency filtering

---

## 💡 **Summary**

**Why the confusion?**

1. **Backend APIs have NO authentication** - Everyone can create projects/controls
2. **Frontend UIs have NO role restrictions** - Everyone sees create buttons
3. **AI has NO project creation tool** - Can only suggest "go to Projects page"
4. **AI prompts mention "create project"** - But AI cannot actually do it

**What needs fixing?**

1. **Add `require_auditor` to project/control creation endpoints** (CRITICAL)
2. **Hide create buttons for non-auditors in frontend** (UX improvement)
3. **Add `create_project` task handler** (Optional - enables AI project creation)
4. **Update AI prompts** (Optional - conversational guidance)

**What's the priority?**

**MUST FIX:** Priority 1 (API authentication) - Security risk  
**SHOULD FIX:** Priority 2 (Frontend UI) - User experience  
**NICE TO HAVE:** Priority 3 & 4 (AI project creation) - Feature enhancement

---

## ⏭️ **Next Steps**

1. **Review this analysis** - Confirm understanding of requirements
2. **Approve fixes** - Which priorities to implement?
3. **Implement changes** - Start with Priority 1 (API auth)
4. **Test thoroughly** - Ensure role separation works
5. **Deploy** - Push to production

**Your confirmation needed before I make any changes!**
