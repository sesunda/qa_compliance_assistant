# Analyst Evidence Samples & System Analysis
**Date**: November 10, 2025  
**Purpose**: Analysis of evidence upload format, validation capabilities, and auditor control setup workflow

---

## 1. EVIDENCE SAMPLE FOR ANALYST UPLOAD ✅

### Sample 1: JSON Format (Recommended for AI-Assisted Upload)

**File**: `analyst_evidence_sample_im8.json`

```json
{
  "project_id": 1,
  "evidence_items": [
    {
      "control_id": 5,
      "title": "Access Control Policy v2.1",
      "description": "Organization-wide access control policy covering authentication, authorization, and RBAC. Approved by CISO on 2024-11-01. Addresses IM8-01 Identity and Access Management requirements.",
      "evidence_type": "policy_document",
      "file_path": "/storage/uploads/access_control_policy_v2.1.pdf",
      "metadata": {
        "document_version": "2.1",
        "approval_date": "2024-11-01",
        "approver": "Chief Information Security Officer",
        "next_review_date": "2025-11-01",
        "classification": "Internal Use Only"
      }
    },
    {
      "control_id": 5,
      "title": "User Access Review Report Q4 2024",
      "description": "Quarterly user access review showing all privileged accounts were reviewed and recertified. All exceptions documented with approval. 3 inactive accounts were disabled per review findings.",
      "evidence_type": "audit_report",
      "file_path": "/storage/uploads/user_access_review_q4_2024.xlsx",
      "metadata": {
        "review_period": "Q4 2024",
        "reviewer": "IT Security Team",
        "accounts_reviewed": 450,
        "accounts_disabled": 3,
        "review_completion_date": "2024-12-15"
      }
    },
    {
      "control_id": 5,
      "title": "Multi-Factor Authentication Configuration",
      "description": "Screenshot showing MFA enabled for all administrative accounts in Azure AD. Configured on 2024-10-15 and enforced for all admin roles.",
      "evidence_type": "configuration_screenshot",
      "file_path": "/storage/uploads/mfa_config_screenshot.png",
      "metadata": {
        "system": "Azure Active Directory",
        "configuration_date": "2024-10-15",
        "enforcement_level": "Required for all admin roles"
      }
    },
    {
      "control_id": 12,
      "title": "Network Segmentation Architecture",
      "description": "Network diagram showing segmentation between DMZ, production, and internal networks. Updated after last penetration test with firewall rules documented.",
      "evidence_type": "configuration_screenshot",
      "file_path": "/storage/uploads/network_segmentation_diagram.png",
      "metadata": {
        "diagram_version": "3.1",
        "last_updated": "2024-09-15",
        "reviewed_by": "Network Security Team"
      }
    },
    {
      "control_id": 12,
      "title": "Firewall Rule Review Report 2024",
      "description": "Annual firewall rule review report showing all 342 rules were validated. 15 obsolete rules were removed. Review completed on 2024-08-30.",
      "evidence_type": "audit_report",
      "file_path": "/storage/uploads/firewall_rule_review_2024.pdf",
      "metadata": {
        "review_date": "2024-08-30",
        "total_rules": 342,
        "rules_removed": 15,
        "next_review_date": "2025-08-30"
      }
    }
  ]
}
```

### Sample 2: CSV Format (For Manual Entry)

**File**: `analyst_evidence_sample_im8.csv`

```csv
control_id,title,description,evidence_type,file_path,metadata_json
5,Access Control Policy v2.1,Organization-wide access control policy covering authentication and RBAC. Approved by CISO on 2024-11-01.,policy_document,/storage/uploads/access_control_policy_v2.1.pdf,"{""document_version"":""2.1"",""approval_date"":""2024-11-01"",""approver"":""CISO""}"
5,User Access Review Report Q4 2024,Quarterly user access review with all privileged accounts reviewed and recertified,audit_report,/storage/uploads/user_access_review_q4_2024.xlsx,"{""review_period"":""Q4 2024"",""accounts_reviewed"":450}"
5,MFA Configuration Screenshot,Screenshot showing MFA enabled for all administrative accounts in Azure AD,configuration_screenshot,/storage/uploads/mfa_config_screenshot.png,"{""system"":""Azure AD"",""configuration_date"":""2024-10-15""}"
12,Network Segmentation Diagram,Network diagram showing DMZ production and internal network segmentation,configuration_screenshot,/storage/uploads/network_segmentation_diagram.png,"{""diagram_version"":""3.1"",""last_updated"":""2024-09-15""}"
12,Firewall Rule Review Report 2024,Annual firewall rule review with 15 obsolete rules removed,audit_report,/storage/uploads/firewall_rule_review_2024.pdf,"{""review_date"":""2024-08-30"",""rules_removed"":15}"
```

### Sample 3: Individual File Upload via API (Current Method)

**Usage**: Analyst uploads one file at a time via Evidence page

```bash
# Example: Upload via curl (analyst credentials)
curl -X POST "https://your-api.azurecontainerapps.io/evidence/upload" \
  -H "Authorization: Bearer ANALYST_TOKEN" \
  -F "control_id=5" \
  -F "title=Access Control Policy v2.1" \
  -F "description=Organization-wide access control policy" \
  -F "evidence_type=policy_document" \
  -F "file=@access_control_policy_v2.1.pdf"
```

---

## 2. EVIDENCE VALIDATION CAPABILITIES - STATUS ✅

### Current Validation (IMPLEMENTED)

#### A. Upload Endpoint Validation (`api/src/routers/evidence.py`)

**✅ ALREADY IMPLEMENTED**:

1. **Control Existence Check**:
   ```python
   control = _get_control(db, control_id)
   if not control:
       raise HTTPException(status_code=404, detail="Control not found")
   ```

2. **Agency Access Control**:
   ```python
   if not check_agency_access(current_user, control.agency_id):
       raise HTTPException(status_code=403, detail="Access denied")
   ```

3. **File Storage Validation** (via `EvidenceStorageService`):
   - File size limits
   - File type validation
   - Checksum generation (SHA-256)
   - Duplicate detection

4. **IM8 Document Specific Validation**:
   ```python
   if evidence_type == "im8_assessment_document":
       # Excel parsing
       parsed_data = excel_processor.parse_im8_document(file_content, filename)
       
       # Structure validation
       is_valid, validation_errors = validator.validate_im8_document(parsed_data)
       
       # Completion stats
       completion_stats = excel_processor.calculate_completion_stats(parsed_data)
   ```

### Missing Validations (GAPS IDENTIFIED)

#### ❌ Gap 1: Bulk Evidence Upload Validation

**Current State**: Only single file upload supported  
**Missing**: Batch validation for multiple evidence items  
**Impact**: Analyst must upload files one-by-one (slow, error-prone)

**Solution Needed**:
```python
# New endpoint needed
@router.post("/bulk-upload")
async def bulk_upload_evidence(
    evidence_list: List[schemas.EvidenceCreate],
    files: List[UploadFile],
    db: Session,
    current_user: dict
):
    # Validate all items before processing
    # Support CSV/JSON + multiple files
    # Return validation report
```

#### ❌ Gap 2: Evidence Type vs File Extension Matching

**Current State**: Not validated  
**Example Problem**: 
- `evidence_type="policy_document"` 
- But file is `screenshot.png` ❌

**Solution Needed**:
```python
EVIDENCE_TYPE_EXTENSIONS = {
    "policy_document": [".pdf", ".docx", ".doc"],
    "audit_report": [".pdf", ".xlsx", ".docx"],
    "configuration_screenshot": [".png", ".jpg", ".jpeg"],
    "log_file": [".csv", ".txt", ".log", ".json"],
    "certificate": [".pdf", ".pem", ".crt"],
    "procedure": [".pdf", ".docx"]
}

def validate_evidence_type_match(evidence_type, filename):
    ext = os.path.splitext(filename)[1].lower()
    allowed = EVIDENCE_TYPE_EXTENSIONS.get(evidence_type, [])
    if ext not in allowed:
        raise ValidationError(f"File type {ext} not allowed for {evidence_type}")
```

#### ❌ Gap 3: Required Evidence Per Control

**Current State**: No validation that control has minimum evidence  
**Example Problem**: Control marked "Implemented" but has 0 evidence documents

**Solution Needed**:
```python
# In Control model or validation service
def validate_control_evidence_completeness(control_id, db):
    control = db.query(Control).filter(Control.id == control_id).first()
    evidence_count = db.query(Evidence).filter(Evidence.control_id == control_id).count()
    
    if control.status == "implemented" and evidence_count == 0:
        raise ValidationError("Implemented controls must have at least 1 evidence document")
```

#### ❌ Gap 4: Metadata Schema Validation

**Current State**: `metadata_json` accepts any JSON, no schema enforcement  
**Example Problem**: Inconsistent metadata structure across evidence items

**Solution Needed**:
```python
# Define Pydantic schemas for metadata
class PolicyMetadata(BaseModel):
    document_version: str
    approval_date: str
    approver: str
    review_date: Optional[str]
    classification: str

class AuditReportMetadata(BaseModel):
    review_period: str
    reviewer: str
    findings_count: Optional[int]
    review_completion_date: str

# Validate during upload
def validate_evidence_metadata(evidence_type, metadata):
    if evidence_type == "policy_document":
        PolicyMetadata(**metadata)  # Pydantic validation
```

#### ❌ Gap 5: File Content Validation

**Current State**: Only checks file exists, not content validity  
**Example Problem**: Corrupt PDF uploaded but marked as valid

**Solution Needed**:
```python
def validate_file_content(file_path, evidence_type):
    if evidence_type == "policy_document" and file_path.endswith(".pdf"):
        # Try to open PDF
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if len(reader.pages) == 0:
                    raise ValidationError("PDF is empty")
        except Exception as e:
            raise ValidationError(f"Invalid PDF: {str(e)}")
```

### Validation Summary

| Validation Type | Status | Priority | Effort |
|----------------|--------|----------|--------|
| Control existence | ✅ Implemented | - | - |
| Agency access control | ✅ Implemented | - | - |
| File storage (size, checksum) | ✅ Implemented | - | - |
| IM8 Excel validation | ✅ Implemented | - | - |
| **Bulk upload validation** | ❌ Missing | **HIGH** | 4 hours |
| **Evidence type/file match** | ❌ Missing | **MEDIUM** | 2 hours |
| **Required evidence per control** | ❌ Missing | **LOW** | 1 hour |
| **Metadata schema validation** | ❌ Missing | **MEDIUM** | 3 hours |
| **File content validation** | ❌ Missing | **LOW** | 2 hours |

---

## 3. AUDITOR CONTROL SETUP WORKFLOW - ANALYSIS 🔍

### Current Capabilities ✅

#### A. Backend Support - FULLY IMPLEMENTED

**1. Projects API** (`/api/projects`):
```python
# Create project
POST /projects
{
  "name": "Digital Services Platform",
  "description": "IM8 compliance assessment",
  "status": "active"
}

# List projects
GET /projects?agency_id=1
```

**2. Controls API** (`/api/controls`):
```python
# Create control
POST /controls
{
  "project_id": 1,
  "name": "Identity and Access Management",
  "description": "Implement robust IAM controls...",
  "control_type": "IM8-01-01",
  "status": "pending"
}

# List controls by project
GET /controls?project_id=1
```

**3. AI Task: Create Controls** (`task_type="create_controls"`):
```python
# Already implemented in task_handlers.py!
{
  "task_type": "create_controls",
  "payload": {
    "framework": "IM8",
    "count": 30,
    "domain_areas": ["IM8-01", "IM8-02", ..., "IM8-10"],
    "project_id": 1,
    "agency_id": 1
  }
}
```

**Result**: Backend **FULLY SUPPORTS** auditor setting up IM8 controls! ✅

### Current LLM Capabilities - NEEDS ENHANCEMENT ⚠️

#### What LLM Can Currently Do:

✅ **Generic control creation** (via AI Task Orchestrator)  
✅ **Evidence upload guidance**  
✅ **Compliance analysis**  
❌ **Conversational control setup for auditors** ← **MISSING**

#### What's Missing for Auditor Workflow:

**Gap**: LLM doesn't guide auditors through control setup conversation

**Current Behavior**:
```
Auditor: "Set up IM8 controls for project 1"
LLM: "I can help you with that" [generic response]
```

**Desired Behavior**:
```
Auditor: "Set up IM8 controls"
LLM: "I'll help you set up IM8 controls. Let me gather the required information:

1. Which project should I add these controls to?
   [Shows list of projects]

2. Which IM8 domains do you want to include?
   ☐ IM8-01: Identity and Access Management
   ☐ IM8-02: Network Security
   ☐ IM8-03: Data Protection
   ... [all 10 domains]

3. Do you want me to:
   a) Create all 30 standard IM8 controls (recommended)
   b) Create controls for specific domains only
   c) Upload a custom control template

Please provide your selection."

Auditor: "Create all 30 controls for Project 1"
LLM: [Creates AI task, returns task ID]
     "✅ I've created a task to set up all 30 IM8 controls for Project 1. 
     Task ID: 123. You can monitor progress in the Agent Tasks page."
```

### Implementation Requirements

#### Option 1: Enhance Agentic Assistant Prompt (QUICK - 2 hours)

**File**: `api/src/services/agentic_assistant.py`

**Add to auditor prompt**:
```python
5. **Set Up IM8 Controls for Projects**:
   When auditor asks to "set up IM8 controls" or "create controls":
   
   Step 1: Ask for project selection
   "Which project should I add controls to? You can:
    - Provide project ID (e.g., 'Project 1')
    - Provide project name (e.g., 'Digital Services Platform')
    - Say 'create new project' if project doesn't exist"
   
   Step 2: Ask for domain coverage
   "Which IM8 domains should I include?
    - All 10 domains (recommended - creates 30 controls)
    - Specific domains only (e.g., 'IM8-01, IM8-02, IM8-05')"
   
   Step 3: Confirm and create task
   "I'll create {count} IM8 controls for {project_name}. 
    This includes:
    - IM8-01: Identity and Access Management (3 controls)
    - IM8-02: Network Security (3 controls)
    ... [full breakdown]
    
    Shall I proceed? (yes/no)"
   
   Step 4: Execute via AI task
   Create task with type "create_controls" and payload:
   {
     "task_type": "create_controls",
     "framework": "IM8",
     "domain_areas": [...],
     "project_id": <extracted_id>,
     "agency_id": <current_user_agency>
   }
```

#### Option 2: Add Dedicated Tool/MCP Server (COMPREHENSIVE - 8 hours)

**Create**: `mcp_setup_im8_controls` tool

**Capabilities**:
1. Project selection (list, create new)
2. Domain selection (checkboxes via UI)
3. Preview control list before creation
4. Bulk create + validation
5. Progress tracking

**Benefits**: Better UX, more control, validation before creation

#### Option 3: Hybrid Approach (RECOMMENDED - 4 hours)

**Enhance LLM prompt** + **Add parameter validation**

**Changes**:
1. Update auditor prompt with step-by-step guidance (2 hours)
2. Add intent detection for "setup controls" (1 hour)
3. Add parameter extraction and validation (1 hour)
4. Test conversational flow (30 min)

---

## 4. RECOMMENDATIONS

### Priority 1: Evidence Upload Validation (CRITICAL)

**Why**: Analysts need confidence their evidence is valid before auditor review

**Tasks**:
1. ✅ **Implement evidence type/file extension matching** - 2 hours
2. ✅ **Add bulk upload endpoint with validation** - 4 hours
3. ✅ **Create validation report UI component** - 3 hours

**Total**: 9 hours

### Priority 2: LLM Control Setup Guidance (HIGH)

**Why**: Auditor workflow is blocked without conversational control setup

**Tasks**:
1. ✅ **Enhance auditor prompt with control setup steps** - 2 hours
2. ✅ **Add intent detection for control setup** - 1 hour
3. ✅ **Add parameter extraction (project, domains)** - 1 hour
4. ✅ **Test end-to-end flow** - 1 hour

**Total**: 5 hours

### Priority 3: Evidence Completeness Validation (MEDIUM)

**Why**: Prevents incomplete control submissions

**Tasks**:
1. ✅ **Add validation rule: implemented controls need evidence** - 1 hour
2. ✅ **Update control review UI to show evidence status** - 2 hours

**Total**: 3 hours

---

## 5. SAMPLE FILES PROVIDED

**Location**: Create these files for analyst use

### File 1: `analyst_evidence_sample_im8.json`
- 5 evidence items for 2 IM8 controls
- Realistic metadata
- Ready for API upload

### File 2: `analyst_evidence_sample_im8.csv`
- Same 5 evidence items in CSV format
- Can be imported to Excel
- Easier for manual editing

### File 3: `auditor_control_setup_guide.md`
- Step-by-step guide for auditors
- Example prompts to use with LLM
- Expected responses

---

## 6. VALIDATION CHECKLIST

Before deploying evidence upload validation:

- [ ] Test file type matching (PDF for policies, PNG for screenshots)
- [ ] Test metadata schema validation (Pydantic)
- [ ] Test bulk upload with 5+ evidence items
- [ ] Test validation error messages are clear
- [ ] Test file content validation (corrupt PDFs rejected)
- [ ] Test control completeness check (implemented = needs evidence)
- [ ] Test edge cases (empty files, huge files, wrong extensions)

---

## 7. QUESTIONS TO CONFIRM

1. **Evidence Upload Format**: 
   - Should we support bulk JSON/CSV upload? ✅ Recommended
   - Or keep single file upload only? ❌ Too slow

2. **Validation Strictness**:
   - Strict mode (reject any invalid item)? ✅ For auditors
   - Lenient mode (skip invalid, process valid)? ✅ For analysts migrating data

3. **Control Setup via LLM**:
   - Conversational flow (LLM asks questions)? ✅ Better UX
   - Or template-based (JSON upload)? ✅ Faster for bulk

4. **Metadata Requirements**:
   - Enforce metadata schema? ✅ Yes, for consistency
   - Or allow free-form JSON? ❌ Causes inconsistency

---

**Status**: Analysis Complete ✅  
**Next**: Await your confirmation on priorities and approach
