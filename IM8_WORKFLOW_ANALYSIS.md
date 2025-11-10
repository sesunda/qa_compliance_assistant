# IM8 Document Workflow - System Analysis & Implementation Plan

**Date**: November 10, 2025  
**Status**: Analysis Complete - Ready for Implementation Review

---

## 📊 Current System Analysis

### ✅ **What Already Exists**

#### 1. **Database Models** (`api/src/models.py`)
```python
✅ User with role_id (admin, auditor, analyst, viewer, super_admin)
✅ Control model with:
   - reviewed_by, review_status, assessment_score
   - test_procedure, testing_frequency
   - Supports workflow already
✅ Evidence model with:
   - verification_status (pending, under_review, approved, rejected)
   - submitted_by, reviewed_by, review_comments
   - Maker-checker workflow ALREADY IMPLEMENTED
✅ JSON column support (metadata_json in Assessment model)
```

#### 2. **Authentication & Authorization** (`api/src/auth.py`)
```python
✅ Role-based access control (RoleChecker)
✅ require_auditor, require_analyst, require_viewer decorators
✅ check_agency_access() for multi-tenancy
✅ Segregation of duties built-in
```

#### 3. **Evidence Upload Workflow** (`api/src/routers/evidence.py`)
```python
✅ /evidence/upload - Upload with file
✅ /evidence/{id}/submit-for-review - Analyst submits
✅ /evidence/{id}/approve - Auditor approves
✅ /evidence/{id}/reject - Auditor rejects
✅ Segregation of duties (cannot approve own submission)
✅ Status transitions validated
```

#### 4. **File Storage** (`api/src/services/evidence_storage.py`)
```python
✅ File upload handling
✅ Checksum generation (SHA-256)
✅ File metadata tracking
✅ Agency-based folder structure
```

#### 5. **Agentic Chat** (`api/src/routers/agentic_chat.py`)
```python
✅ Multi-turn conversation with context
✅ File upload support
✅ Role-based conversation (current_user available)
✅ Validation (file size, file type)
✅ Error handling with detailed messages
```

### ⚠️ **What's Missing for IM8 Document Workflow**

#### 1. **IM8 Document Model** - NEW TABLE NEEDED
```python
❌ No dedicated table for IM8 Assessment Documents
❌ No version tracking for document submissions
❌ No structure to store domain areas and control mappings
❌ No embedded PDF metadata storage
```

#### 2. **Template Management** - NEW FUNCTIONALITY
```python
❌ No template upload/download for Auditors
❌ No template version management
❌ No template-control mapping
```

#### 3. **Excel Processing** - NEW UTILITY
```python
❌ No Excel file parsing (read sheets, extract data)
❌ No embedded PDF extraction from Excel
❌ No Excel validation logic
```

#### 4. **Supervisor Role** - ROLE ENHANCEMENT NEEDED
```python
❌ 'supervisor' role not in current system (only admin, auditor, analyst, viewer)
❌ Need to add supervisor role with approval permissions
```

#### 5. **Agentic Chat Role-Specific Questions** - ENHANCEMENT NEEDED
```python
✅ Basic role detection exists
❌ Not asking role-specific questions for IM8 workflow
❌ Not validating IM8-specific fields
❌ Not handling template operations
```

---

## 🎯 **Minimal Changes Implementation Plan**

### **Strategy**: Extend existing system, don't rebuild

---

## Phase 1: Database Extensions (Minimal Schema Changes)

### Option A: **Use Existing Evidence Table** (RECOMMENDED - Zero Schema Changes)
```python
# Leverage existing Evidence model with metadata_json
# Store IM8 document as special evidence type

evidence_type = "im8_assessment_document"
metadata_json = {
    "document_version": 1,
    "parent_version_id": null,  # For resubmissions
    "framework": "IM8",
    "domain_areas": [
        {
            "domain_id": "1",
            "domain_name": "Information Security Governance",
            "controls": [
                {
                    "control_id": "IM8-01-01",
                    "control_name": "Identity and Access Management",
                    "status": "Implemented",
                    "notes": "...",
                    "embedded_pdf": {
                        "filename": "access_control_policy.pdf",
                        "extracted_path": "/storage/evidence/project_1/control_1/access_control_policy.pdf",
                        "checksum": "abc123..."
                    }
                }
            ]
        }
    ],
    "extracted_pdfs": [...]  # List of extracted PDF metadata
}
```

**✅ Advantages**:
- Zero database migrations
- Reuse existing maker-checker workflow
- Reuse existing file storage
- Reuse existing versioning (via parent relationships)
- Works with current code

### Option B: **New IM8Document Table** (If more structure needed)
```python
# Only if Option A becomes too complex
class IM8Document(Base):
    __tablename__ = "im8_documents"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    version = Column(Integer, default=1)
    parent_version_id = Column(Integer, ForeignKey("im8_documents.id"), nullable=True)
    file_path = Column(String(500))
    metadata_json = Column(JSON)  # Store domain/control structure
    verification_status = Column(String(50), default="pending")
    submitted_by = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))  # Supervisor
    ...
```

---

## Phase 2: Add Supervisor Role (Auth Enhancement)

### Changes to `api/src/auth.py`:
```python
# Add supervisor role checker
require_supervisor = RoleChecker(["admin", "super_admin", "supervisor"])

# Update approval logic to require supervisor
def require_approval_permission(current_user: dict = Depends(get_current_user)):
    """Only supervisors and admins can give final approval"""
    if current_user["role"] not in ["supervisor", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only supervisors can approve evidence"
        )
    return current_user
```

### Workflow Update:
```
Current: Analyst → Auditor (approve/reject)
New:     Analyst → Auditor (review) → Supervisor (approve/reject)
```

---

## Phase 3: Excel Processing Utility (New Service)

### Create `api/src/services/excel_processor.py`:
```python
import openpyxl
from typing import Dict, List
import os

class ExcelProcessor:
    """Process IM8 assessment Excel files"""
    
    def parse_im8_document(self, file_path: str) -> Dict:
        """
        Extract structure and data from IM8 Excel template
        Returns: domain areas, controls, embedded PDFs
        """
        wb = openpyxl.load_workbook(file_path)
        
        metadata = self._extract_metadata(wb['Metadata'])
        domains = []
        
        # Process domain sheets
        for sheet_name in ['Domain_1', 'Domain_2']:
            domain_data = self._extract_domain_data(wb[sheet_name])
            embedded_pdfs = self._extract_embedded_pdfs(wb[sheet_name])
            domain_data['embedded_pdfs'] = embedded_pdfs
            domains.append(domain_data)
        
        return {
            "metadata": metadata,
            "domains": domains
        }
    
    def extract_embedded_pdfs(self, file_path: str, output_dir: str) -> List[Dict]:
        """
        Extract all embedded PDF objects from Excel
        Returns: List of {filename, path, control_id}
        """
        # Use python-oletools or zipfile to extract embedded objects
        ...
    
    def validate_im8_structure(self, file_path: str) -> Dict:
        """
        Validate Excel file has correct structure
        Returns: {valid: bool, errors: [...]}
        """
        ...
```

---

## Phase 4: IM8 Document Endpoints (New Router)

### Create `api/src/routers/im8_documents.py`:
```python
from fastapi import APIRouter, Depends, UploadFile, File
from api.src.auth import require_auditor, require_analyst, require_supervisor

router = APIRouter(prefix="/im8-documents", tags=["im8-documents"])

# AUDITOR: Upload template
@router.post("/template/upload")
async def upload_im8_template(
    project_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_auditor),
    db: Session = Depends(get_db)
):
    """Auditor uploads blank IM8 template for analysts"""
    # Validate Excel structure
    # Save as template
    # Link to project
    ...

# AUDITOR: Download template
@router.get("/template/download/{project_id}")
async def download_im8_template(
    project_id: int,
    current_user: dict = Depends(require_auditor),
    db: Session = Depends(get_db)
):
    """Anyone can download template for their project"""
    ...

# ANALYST: Upload completed document
@router.post("/submit")
async def submit_im8_document(
    project_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_analyst),
    db: Session = Depends(get_db)
):
    """
    Analyst submits completed IM8 document with embedded PDFs
    1. Validate Excel structure
    2. Extract embedded PDFs
    3. Parse control data
    4. Create evidence records
    5. Set status: under_review
    """
    # Use ExcelProcessor to parse
    # Extract PDFs to storage
    # Create evidence record with metadata_json
    # Link controls
    ...

# AUDITOR: Review document
@router.post("/{document_id}/review")
async def review_im8_document(
    document_id: int,
    decision: str,  # "recommend_approval" or "reject"
    comments: str,
    current_user: dict = Depends(require_auditor),
    db: Session = Depends(get_db)
):
    """Auditor reviews and recommends for approval or rejects"""
    ...

# SUPERVISOR: Final approval
@router.post("/{document_id}/approve")
async def approve_im8_document(
    document_id: int,
    comments: Optional[str],
    current_user: dict = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """Supervisor gives final approval"""
    ...
```

---

## Phase 5: Agentic Chat Enhancements

### Update `api/src/services/agentic_assistant.py`:

```python
# Add role-specific prompt context
def _get_role_context(self, user_role: str, intent: str) -> str:
    """Return role-specific prompts and validations"""
    
    if user_role == "auditor" and intent == "upload_template":
        return """
        AUDITOR TEMPLATE UPLOAD:
        Required information:
        - project_id (which project is this template for?)
        - Excel file (IM8 template with correct structure)
        
        Validate:
        - File is .xlsx
        - Has required sheets: Metadata, Domain_1, Domain_2, Summary
        - Structure matches IM8 template format
        """
    
    elif user_role == "analyst" and intent == "submit_evidence":
        return """
        ANALYST EVIDENCE SUBMISSION:
        Required information:
        - project_id
        - Excel file (completed IM8 template with embedded PDFs)
        
        Validate:
        - All controls have status filled
        - All controls have embedded PDF evidence
        - Notes/comments provided where required
        """
    
    elif user_role == "supervisor" and intent == "approve_evidence":
        return """
        SUPERVISOR APPROVAL:
        Required information:
        - document_id (which submission to approve?)
        - Optional: approval comments
        
        Validate:
        - Document is in "auditor_reviewed" status
        - Cannot approve if already approved/rejected
        """
    ...
```

### Add validation before processing:
```python
async def chat(self, message, conversation_manager, session_id, db, current_user, file_path=None):
    # Get user role
    user_role = current_user.get("role")
    
    # Classify intent
    intent = await self.llm_service.classify_intent(...)
    
    # Get role-specific requirements
    role_context = self._get_role_context(user_role, intent["intent"])
    
    # Validate parameters against role requirements
    validation_result = self._validate_role_action(user_role, intent, file_path)
    
    if not validation_result["valid"]:
        return {
            "answer": validation_result["error_message"],
            "is_clarifying": True,
            "parameters_missing": validation_result["missing_params"]
        }
    
    # Proceed with action
    ...
```

---

## Phase 6: Validation Service (Extend existing)

### Create `api/src/services/im8_validator.py`:
```python
class IM8Validator:
    """Validation logic for IM8 documents"""
    
    def validate_excel_structure(self, file_path: str) -> Dict:
        """Validate Excel file structure"""
        errors = []
        warnings = []
        
        try:
            wb = openpyxl.load_workbook(file_path)
            
            # Check required sheets
            required_sheets = ['Metadata', 'Domain_1', 'Domain_2', 'Summary', 'Reference_Policies']
            for sheet in required_sheets:
                if sheet not in wb.sheetnames:
                    errors.append(f"Missing required sheet: {sheet}")
            
            # Validate metadata
            if 'Metadata' in wb.sheetnames:
                metadata_validation = self._validate_metadata_sheet(wb['Metadata'])
                errors.extend(metadata_validation['errors'])
            
            # Validate domain sheets
            for domain_sheet in ['Domain_1', 'Domain_2']:
                if domain_sheet in wb.sheetnames:
                    domain_validation = self._validate_domain_sheet(wb[domain_sheet])
                    errors.extend(domain_validation['errors'])
                    warnings.extend(domain_validation['warnings'])
            
            # Check for embedded PDFs
            pdf_check = self._check_embedded_pdfs(wb)
            if pdf_check['count'] == 0:
                errors.append("No embedded PDF evidence found")
            
        except Exception as e:
            errors.append(f"Failed to read Excel file: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_domain_sheet(self, sheet) -> Dict:
        """Validate domain sheet structure and data"""
        errors = []
        warnings = []
        
        # Check columns exist
        required_columns = ['Control ID', 'Control Name', 'Status', 'Evidence', 'Notes']
        ...
        
        # Check each control row
        for row in sheet.iter_rows(min_row=3):  # Skip header rows
            control_id = row[0].value
            if not control_id:
                continue
            
            # Validate control ID format
            if not re.match(r'^IM8-\d{2}-\d{2}$', control_id):
                errors.append(f"Invalid control ID format: {control_id}")
            
            # Check status is filled
            status = row[2].value
            if not status or status not in ['Implemented', 'Partial', 'Not Started']:
                errors.append(f"Control {control_id}: Invalid or missing status")
            
            # Check evidence column (should have embedded PDF)
            if not row[3].value and not self._has_embedded_object(row[3]):
                warnings.append(f"Control {control_id}: No evidence provided")
        
        return {"errors": errors, "warnings": warnings}
```

---

## 🎯 **Summary of Required Changes**

### **MINIMAL APPROACH** (Recommended):

| Component | Change Type | Complexity | Estimated Effort |
|-----------|-------------|------------|------------------|
| Database | **None** (use existing Evidence + JSON) | ✅ Low | 0 hours |
| Add Supervisor Role | Auth enhancement | ✅ Low | 1 hour |
| Excel Processing | New service | 🟡 Medium | 4 hours |
| IM8 Endpoints | New router | 🟡 Medium | 3 hours |
| Validation Service | New service | 🟡 Medium | 3 hours |
| Agentic Chat Enhancement | Modify existing | ✅ Low | 2 hours |
| Create Excel Templates | Manual work | ✅ Low | 2 hours |
| **TOTAL** | | | **15 hours** |

---

## 📋 **Detailed Implementation Checklist**

### ✅ **Step 1: Create Excel Templates** (2 hours)
- [ ] Create blank IM8 template with 5 sheets
- [ ] Create sample PDFs for embedding
- [ ] Create completed sample with embedded PDFs
- [ ] Test embedding/extraction manually

### ✅ **Step 2: Add Supervisor Role** (1 hour)
- [ ] Add `require_supervisor` to auth.py
- [ ] Update evidence approval endpoint to check supervisor role
- [ ] Update agentic assistant to recognize supervisor role

### ✅ **Step 3: Excel Processing Service** (4 hours)
- [ ] Create `excel_processor.py`
- [ ] Implement `parse_im8_document()`
- [ ] Implement `extract_embedded_pdfs()`
- [ ] Test with sample files

### ✅ **Step 4: IM8 Validator** (3 hours)
- [ ] Create `im8_validator.py`
- [ ] Implement structure validation
- [ ] Implement data validation
- [ ] Add error codes and messages

### ✅ **Step 5: IM8 Document Endpoints** (3 hours)
- [ ] Create `im8_documents.py` router
- [ ] Implement template upload/download
- [ ] Implement document submission
- [ ] Implement review/approval endpoints

### ✅ **Step 6: Agentic Chat Updates** (2 hours)
- [ ] Add role-specific context in agentic_assistant.py
- [ ] Add IM8 document intent handling
- [ ] Add validation before processing
- [ ] Test multi-turn conversations for each role

---

## 🚀 **Recommendation**

**GO WITH MINIMAL APPROACH**:
- Reuse existing Evidence table with `evidence_type = "im8_assessment_document"`
- Store all IM8 structure in `metadata_json` (JSON column)
- Reuse existing maker-checker workflow
- Add Excel processing and validation as new services
- Enhance agentic chat with role-specific prompts

**Benefits**:
- No database migrations
- Minimal code changes
- Reuses proven workflows
- Quick to implement (15 hours)
- Easy to test

---

## ❓ **Questions for Confirmation**

1. **Approve minimal approach?** (Use existing Evidence table + JSON)
2. **Supervisor role** - Should supervisor ONLY do final approval, or also review like auditor?
3. **Template versioning** - Should templates have versions or just "latest"?
4. **Excel validation** - Should we validate deeply (formulas, data types) or just structure?
5. **Embedded PDF limits** - Max size per PDF? Max number of PDFs per document?

---

**Status**: Ready to proceed with implementation upon your confirmation! 🎯
