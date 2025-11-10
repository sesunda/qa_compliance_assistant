# IM8 Workflow - Maker-Checker Reuse Analysis

**Date**: November 10, 2025  
**Decision**: REUSE existing maker-checker logic with minimal additions

---

## 📊 Current Maker-Checker Logic Analysis

### **Existing Workflow** (Working Perfectly!)

```python
# Status Flow
"pending" → "under_review" → "approved" / "rejected"

# Roles & Actions
Analyst (Maker)  → Upload evidence → Status: "pending"
Analyst (Maker)  → Submit for review → Status: "under_review"
Auditor (Checker) → Approve → Status: "approved"
Auditor (Checker) → Reject (with comments) → Status: "rejected"

# Security Features
✅ Segregation of duties (cannot approve own submission)
✅ Agency-level access control
✅ Status transition validation
✅ Mandatory comments on rejection
✅ Audit trail (submitted_by, reviewed_by, timestamps)
```

### **Database Fields** (Evidence Table)
```python
verification_status: "pending" | "under_review" | "approved" | "rejected"
submitted_by: User ID who submitted
reviewed_by: User ID who reviewed
reviewed_at: Timestamp
review_comments: Text
uploaded_by: User ID who uploaded
uploaded_at: Timestamp
```

---

## ✅ **REUSE DECISION: 100% Compatible with IM8 Workflow**

### **Why It Works Perfectly:**

| Requirement | Current Support | IM8 Use Case |
|-------------|-----------------|--------------|
| **Analyst uploads** | ✅ `/evidence/upload` | Analyst uploads IM8 Excel |
| **Analyst submits** | ✅ `/evidence/{id}/submit-for-review` | Submit IM8 document for review |
| **Auditor reviews** | ✅ `/evidence/{id}/approve` or `/reject` | Auditor approves/rejects IM8 doc |
| **Status tracking** | ✅ verification_status field | Track IM8 document status |
| **Comments** | ✅ review_comments field | Feedback on IM8 submission |
| **Audit trail** | ✅ All user/timestamp fields | Complete history |
| **Segregation** | ✅ Cannot approve own | Already enforced |

---

## 🎯 **Implementation Strategy: EXTEND, DON'T REBUILD**

### **Approach**: Use existing endpoints + add IM8-specific features

```
REUSE 100%:
├── Evidence table structure
├── Maker-checker workflow endpoints
├── Status transition logic
├── Role-based authorization
├── File upload/download
└── Review history tracking

ADD ONLY:
├── Excel file parsing (new service)
├── Embedded PDF extraction (new service)
├── IM8 structure validation (new service)
└── IM8-specific metadata in JSON column
```

---

## 📋 **IM8 Workflow Mapping to Existing System**

### **Step 1: Auditor Shares Template**
```python
# USE: Existing /evidence/upload endpoint
# NEW: Add evidence_type = "im8_template"

POST /api/evidence/upload
Form Data:
  - control_id: (create a special "template" control or use project-level)
  - title: "IM8 Assessment Template"
  - description: "Blank IM8 template for Project X"
  - evidence_type: "im8_template"  # NEW TYPE
  - file: im8_template.xlsx

Result: Evidence record created with:
  - verification_status: "approved" (templates don't need review)
  - metadata_json: {"is_template": true, "framework": "IM8"}
```

### **Step 2: Analyst Downloads Template**
```python
# USE: Existing /evidence/{id}/download endpoint
GET /api/evidence/{template_id}/download

# Returns: Excel file
```

### **Step 3: Analyst Uploads Completed IM8 Document (AUTO-SUBMIT)**
```python
# USE: Existing /evidence/upload endpoint
# MODIFY: Set status to "under_review" automatically for IM8 docs

POST /api/evidence/upload
Form Data:
  - control_id: project_main_control_id
  - title: "IM8 Assessment - Project X - v1"
  - description: "Completed IM8 assessment with evidence"
  - evidence_type: "im8_assessment_document"  # NEW TYPE
  - file: im8_completed_v1.xlsx

BACKEND PROCESSING (NEW):
1. Save Excel file using existing evidence_storage_service
2. Parse Excel structure (NEW: excel_processor.py)
3. Extract embedded PDFs (NEW)
4. Validate structure (NEW: im8_validator.py)
5. Store metadata in metadata_json:
   {
     "document_version": 1,
     "framework": "IM8",
     "validation_result": {...},
     "domain_areas": [
       {
         "domain_id": "1",
         "controls": [
           {"control_id": "IM8-01-01", "status": "Implemented", "embedded_pdf": {...}}
         ]
       }
     ],
     "extracted_pdfs": [
       {"filename": "policy.pdf", "path": "/storage/...", "control_id": "IM8-01-01"}
     ]
   }

Result: Evidence record created with:
  - verification_status: "under_review"  # AUTO-SUBMITTED!
  - submitted_by: current_user["id"]     # Track who uploaded
  - evidence_type: "im8_assessment_document"
  - metadata_json: (detailed structure above)

✅ NO SEPARATE SUBMIT STEP NEEDED!
```

### **Step 4: Auditor Reviews**
```python
# USE: Existing endpoints AS-IS (no changes needed!)

# Auditor downloads to review
GET /api/evidence/{evidence_id}/download

# Auditor approves
POST /api/evidence/{evidence_id}/approve
{
  "comments": "All controls verified, evidence adequate"
}

# OR Auditor rejects
POST /api/evidence/{evidence_id}/reject
{
  "comments": "Control IM8-02-01 missing network diagram"
}

Result: verification_status changes to "approved" or "rejected"
```

### **Step 5: Analyst Resubmits (if rejected)**
```python
# USE: Existing upload endpoint with version tracking
# AUTO-SUBMITTED on upload!

POST /api/evidence/upload
Form Data:
  - control_id: same
  - title: "IM8 Assessment - Project X - v2"  # Increment version
  - evidence_type: "im8_assessment_document"
  - file: im8_completed_v2.xlsx

Store in metadata_json:
  {
    "document_version": 2,
    "parent_version_id": <previous_evidence_id>,  # Link to v1
    ...
  }

Result: Auto-submitted with verification_status: "under_review"
✅ NO SEPARATE SUBMIT STEP!
```

---

## 🔧 **What Needs to be Created (NEW Components)**

### 1. **Excel Processing Service** (NEW)
```python
# api/src/services/excel_processor.py

class ExcelProcessor:
    def parse_im8_document(self, file_path: str) -> dict:
        """Parse IM8 Excel structure"""
        # Read Excel using openpyxl
        # Extract metadata, domains, controls
        # Return structured data
    
    def extract_embedded_pdfs(self, file_path: str, output_dir: str) -> list:
        """Extract embedded PDFs from Excel"""
        # Use python-oletools or zipfile
        # Save PDFs to storage
        # Return list of extracted files
```

### 2. **IM8 Validator** (NEW)
```python
# api/src/services/im8_validator.py

class IM8Validator:
    def validate_excel_structure(self, file_path: str) -> dict:
        """Validate IM8 Excel structure"""
        # Check required sheets exist
        # Validate control IDs
        # Check status values
        # Return validation result
    
    def validate_embedded_pdfs(self, file_path: str) -> dict:
        """Check that PDFs are embedded for each control"""
        # Count embedded objects
        # Verify minimum requirements met
```

### 3. **Upload Endpoint Enhancement** (MODIFY EXISTING)
```python
# api/src/routers/evidence.py

# MODIFY existing upload_evidence() function
@router.post("/upload", response_model=schemas.Evidence)
async def upload_evidence(...):
    # ... existing code ...
    
    # ADD: Special handling for IM8 documents
    if evidence_type == "im8_assessment_document":
        # Parse Excel
        processor = ExcelProcessor()
        parsed_data = processor.parse_im8_document(file_path)
        
        # Extract PDFs
        extracted_pdfs = processor.extract_embedded_pdfs(file_path, pdf_output_dir)
        
        # Validate
        validator = IM8Validator()
        validation_result = validator.validate_excel_structure(file_path)
        
        # Store metadata
        db_evidence.metadata_json = {
            "document_version": 1,
            "framework": "IM8",
            "validation_result": validation_result,
            "domain_areas": parsed_data["domains"],
            "extracted_pdfs": extracted_pdfs
        }
        
        # AUTO-SUBMIT: Set status to "under_review" for IM8 docs
        db_evidence.verification_status = "under_review"
        db_evidence.submitted_by = current_user["id"]
    
    # ... rest of existing code ...
```

### 4. **Agentic Chat Enhancement** (MODIFY EXISTING)
```python
# api/src/services/agentic_assistant.py

# ADD: Role-specific prompts
def _get_role_specific_context(self, user_role: str, intent: str) -> str:
    if user_role == "auditor" and "template" in intent:
        return "To share IM8 template: Upload Excel file with evidence_type='im8_template'"
    
    elif user_role == "analyst" and "submit" in intent:
        return "To submit IM8 document: Upload completed Excel with embedded PDFs"
    
    # ... more role-specific guidance ...

# MODIFY: Add validation in chat processing
async def chat(self, message, ...):
    # ... existing code ...
    
    # ADD: Validate IM8-specific requirements
    if intent == "upload_im8_document":
        if not file_path:
            return {"answer": "Please upload the Excel file", "is_clarifying": True}
        
        if not file_path.endswith('.xlsx'):
            return {"answer": "Only Excel files (.xlsx) are supported", "is_clarifying": True}
    
    # ... proceed with existing logic ...
```

---

## 📊 **Summary: Minimal Changes Required**

### **REUSE (No Changes):**
✅ Evidence table  
✅ Maker-checker workflow endpoints (/submit-for-review, /approve, /reject)  
✅ File upload/download  
✅ Role-based auth  
✅ Agency access control  
✅ Review history  
✅ Status transitions  

**Lines of Code to Change: 0**

---

### **CREATE (New Services):**
🆕 ExcelProcessor service (150 lines)  
🆕 IM8Validator service (100 lines)  

**Lines of Code to Create: ~250**

---

### **MODIFY (Small Additions):**
📝 evidence.py: Add IM8 processing in upload endpoint (+50 lines)  
📝 agentic_assistant.py: Add role-specific prompts (+30 lines)  
📝 schemas.py: Add IM8 evidence types to enum (+2 lines)  

**Lines of Code to Modify: ~82**

---

## ✅ **TOTAL EFFORT: ~332 Lines of Code**

- **Reuse**: 100% of maker-checker logic
- **Database migrations**: 0
- **Breaking changes**: 0
- **New tables**: 0
- **Implementation time**: ~6 hours (vs 15 hours if building from scratch)

---

## 🚀 **Simplified Implementation Checklist**

### ✅ **Phase 1: Excel Processing** (3 hours)
- [ ] Create `excel_processor.py`
  - Parse Excel sheets
  - Extract embedded PDFs
  - Return structured data
- [ ] Create `im8_validator.py`
  - Validate structure
  - Check required fields
- [ ] Test with sample files

### ✅ **Phase 2: Integrate with Existing Upload** (2 hours)
- [ ] Modify `evidence.py` upload endpoint
  - Add IM8 document type detection
  - Call ExcelProcessor
  - Store metadata in JSON
- [ ] Test end-to-end upload

### ✅ **Phase 3: Agentic Chat Enhancement** (1 hour)
- [ ] Add role-specific prompts in `agentic_assistant.py`
- [ ] Add IM8 validation logic
- [ ] Test conversational flow

### ✅ **Phase 4: Create Templates** (2 hours)
- [ ] Create blank IM8 Excel template
- [ ] Create sample completed template with embedded PDFs
- [ ] Document how to embed PDFs

**TOTAL: 8 hours** (down from 15!)

---

## 💡 **Key Decisions Made**

1. ✅ **REUSE existing Evidence table** - Store IM8 docs as `evidence_type = "im8_assessment_document"`
2. ✅ **REUSE existing maker-checker workflow** - No changes to approval logic
3. ✅ **NO new database tables** - Use metadata_json for structure
4. ✅ **NO supervisor role** - Keep it simple: Analyst → Auditor (approve/reject)
5. ✅ **Template versioning**: "latest" only - Keep simple
6. ✅ **Validation**: Structure + required fields only - No deep validation
7. ✅ **Embedded PDFs**: Minimum viable - Extract and store

---

## 🎯 **Next Steps**

**Ready to implement!** Just need to:

1. Create ExcelProcessor service (parse + extract PDFs)
2. Create IM8Validator service (structure validation)
3. Add IM8 handling to existing upload endpoint
4. Add role-specific prompts to agentic chat
5. Create Excel templates

**All using existing infrastructure - NO breaking changes!** 🎉

---

**Status**: Analysis complete, ready to code! ✅
