# IM8 ULTRA-SIMPLIFIED WORKFLOW - FINAL SPECIFICATION

**Date**: November 10, 2025  
**Status**: FINAL - Ready for Implementation

---

## 🎯 **1-STEP WORKFLOW**

```
ANALYST uploads IM8 Excel file
    ↓ (automatic)
Status: "under_review"
    ↓
AUDITOR reviews and approves/rejects
    ↓
Status: "approved" or "rejected"
```

**That's it!** No separate submit step needed.

---

## 📋 **Complete Flow**

### **Step 1: Auditor Shares Template**
```python
POST /api/evidence/upload
  - evidence_type: "im8_template"
  - file: im8_template.xlsx
  
Result: Template available for download
```

### **Step 2: Analyst Downloads Template**
```python
GET /api/evidence/{template_id}/download

Returns: Excel file
```

### **Step 3: Analyst Uploads Completed Document**
```python
POST /api/evidence/upload
  - evidence_type: "im8_assessment_document"
  - file: im8_completed_v1.xlsx

Backend Processing:
1. Parse Excel (domains, controls)
2. Extract embedded PDFs
3. Validate structure
4. Set verification_status = "under_review"  ← AUTO-SUBMITTED!
5. Set submitted_by = analyst_id

Result: Immediately ready for auditor review
```

### **Step 4: Auditor Reviews & Approves/Rejects**
```python
# Download to review
GET /api/evidence/{evidence_id}/download

# Approve
POST /api/evidence/{evidence_id}/approve
  - comments: "Looks good!"

# OR Reject
POST /api/evidence/{evidence_id}/reject
  - comments: "Missing network diagram for IM8-02-01"
```

### **Step 5: If Rejected, Analyst Resubmits**
```python
POST /api/evidence/upload
  - evidence_type: "im8_assessment_document"
  - file: im8_completed_v2.xlsx  (corrected version)

Result: Auto-submitted again with verification_status = "under_review"
```

---

## 🔧 **Implementation Changes**

### **ONLY 1 Modification to Existing Code:**

```python
# api/src/routers/evidence.py - upload_evidence()

# ADD these lines after file is saved:
if evidence_type == "im8_assessment_document":
    # Process IM8 document
    processor = ExcelProcessor()
    validator = IM8Validator()
    
    # Parse and validate
    parsed_data = processor.parse_im8_document(saved_file_path)
    extracted_pdfs = processor.extract_embedded_pdfs(saved_file_path, output_dir)
    validation_result = validator.validate_excel_structure(saved_file_path)
    
    # Store metadata
    db_evidence.metadata_json = {
        "document_version": 1,
        "framework": "IM8",
        "domain_areas": parsed_data["domains"],
        "extracted_pdfs": extracted_pdfs,
        "validation_result": validation_result
    }
    
    # AUTO-SUBMIT for review
    db_evidence.verification_status = "under_review"
    db_evidence.submitted_by = current_user["id"]
```

---

## ✅ **What Gets Reused (No Changes)**

- ✅ `/evidence/upload` endpoint
- ✅ `/evidence/{id}/download` endpoint
- ✅ `/evidence/{id}/approve` endpoint
- ✅ `/evidence/{id}/reject` endpoint
- ✅ `/evidence/{id}/review-history` endpoint
- ✅ Evidence table structure
- ✅ All maker-checker logic
- ✅ Segregation of duties
- ✅ Agency access control

**Total reuse: 95% of existing code!**

---

## 🆕 **What Gets Created (New)**

1. **ExcelProcessor** (`api/src/services/excel_processor.py`)
   - Parse IM8 Excel structure
   - Extract embedded PDFs
   
2. **IM8Validator** (`api/src/services/im8_validator.py`)
   - Validate required sheets
   - Validate control data
   
3. **Excel Templates** (manual creation)
   - Blank template
   - Sample with embedded PDFs

---

## 📊 **Simplified Checklist**

### ✅ **Task 1: Create ExcelProcessor** (3 hours)
```python
class ExcelProcessor:
    def parse_im8_document(self, file_path: str) -> dict:
        """Extract domains and controls from Excel"""
        
    def extract_embedded_pdfs(self, file_path: str, output_dir: str) -> list:
        """Extract and save embedded PDF objects"""
```

### ✅ **Task 2: Create IM8Validator** (1 hour)
```python
class IM8Validator:
    def validate_excel_structure(self, file_path: str) -> dict:
        """Validate sheets, controls, and data"""
```

### ✅ **Task 3: Modify Upload Endpoint** (1 hour)
```python
# Add IM8 detection and auto-submit logic
# ~20 lines of code
```

### ✅ **Task 4: Update Agentic Chat** (1 hour)
```python
# Add role-specific prompts
# Add IM8 document type validation
```

### ✅ **Task 5: Create Templates** (2 hours)
```
- Blank IM8 template (5 sheets)
- Sample with 4 embedded PDFs
```

**TOTAL: 8 hours**

---

## 💬 **Agentic Chat Flow**

### **Auditor Flow:**
```
User: "I want to share the IM8 template"

Bot: "I'll help you upload the IM8 template. Please upload the Excel file."

User: [uploads file]

Bot: "Template uploaded successfully! Analysts can now download it from 
      Evidence ID: 123"
```

### **Analyst Flow:**
```
User: "I want to submit my IM8 assessment"

Bot: "I'll help you submit your IM8 assessment. Please upload the completed 
      Excel file with embedded PDFs."

User: [uploads file]

Bot: "Processing your IM8 document...
     ✓ Parsed 2 domains, 4 controls
     ✓ Extracted 4 embedded PDFs
     ✓ Validation passed
     
     Your assessment has been submitted for review (Status: under_review)
     Evidence ID: 124"
```

### **Auditor Review Flow:**
```
User: "Review assessment 124"

Bot: "Here's the IM8 assessment for Evidence ID 124:
     - Framework: IM8
     - Domains: 2
     - Controls: 4
     - Submitted by: analyst@example.com
     
     Would you like to:
     1. Download and review
     2. Approve
     3. Reject with comments"
```

---

## 🎯 **Key Benefits**

1. ✅ **Simpler for users** - Upload = Auto-submit (1 step instead of 2)
2. ✅ **Less code** - No changes to approval endpoints
3. ✅ **Faster workflow** - Immediately available for review
4. ✅ **Same security** - All existing controls remain
5. ✅ **Clear audit trail** - submitted_by, reviewed_by tracked

---

## 📝 **Status Definitions**

```python
# For IM8 Documents only:
"under_review"  # Uploaded by analyst, waiting for auditor
"approved"      # Auditor approved
"rejected"      # Auditor rejected, needs resubmission

# NOT USED for IM8:
"pending"       # (skipped - goes straight to under_review)
```

---

## 🚀 **Implementation Order**

1. Create ExcelProcessor service
2. Create IM8Validator service
3. Modify upload endpoint (add IM8 detection + auto-submit)
4. Test upload → approve flow
5. Create Excel templates
6. Update agentic chat prompts
7. End-to-end testing

---

**Status**: Simplified to 1-step workflow, ready to implement! ✅
