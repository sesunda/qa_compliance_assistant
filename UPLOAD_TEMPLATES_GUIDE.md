# Upload Templates - Quick Reference Guide

## Available Upload Templates with Data

### 1. IM8 Controls Bulk Upload Template
**File**: `storage/im8_controls_bulk_upload.json`

**Contains**: 10 complete IM8 framework controls covering all 10 domain areas

**Sample Structure**:
```json
{
  "project_id": 1,
  "framework": "IM8",
  "upload_metadata": {
    "upload_date": "2025-11-10",
    "uploaded_by": "System Administrator",
    "description": "IM8 Framework Controls - Complete Set",
    "version": "1.0"
  },
  "controls": [
    {
      "control_id": "IM8-01",
      "name": "Identity and Access Management",
      "description": "Implement robust identity and access management...",
      "control_type": "Technical",
      "status": "pending",
      "framework": "IM8",
      "category": "Access Control",
      "requirement_level": "Mandatory",
      "implementation_guidance": "Establish centralized identity...",
      "evidence_requirements": [...],
      "testing_frequency": "Quarterly",
      "test_procedure": "1. Review access control policies...",
      "domain": "1. Information Security Governance"
    }
  ]
}
```

**Controls Included**:
- IM8-01: Identity and Access Management
- IM8-02: Network Security and Segmentation
- IM8-03: Data Protection and Classification
- IM8-04: Vulnerability and Patch Management
- IM8-05: Secure Software Development
- IM8-06: Security Monitoring and Logging
- IM8-07: Third-Party Risk Management
- IM8-08: Change and Configuration Management
- IM8-09: Risk Assessment and Compliance
- IM8-10: Digital Service Standards Compliance

---

### 2. IM8 Evidence Bulk Upload Template
**File**: `storage/im8_evidence_bulk_upload.json`

**Contains**: 16 evidence documents mapped to IM8 controls

**Sample Structure**:
```json
{
  "project_id": 1,
  "framework": "IM8",
  "upload_metadata": {
    "upload_date": "2025-11-10",
    "uploaded_by": "Compliance Officer",
    "description": "Evidence documents for IM8 controls - Q4 2025",
    "version": "1.0"
  },
  "evidence_items": [
    {
      "control_id": "IM8-01",
      "title": "Access Control Policy v2.1",
      "description": "Organization-wide access control policy...",
      "evidence_type": "policy_document",
      "file_path": "/storage/uploads/access_control_policy_v2.1.pdf",
      "verification_status": "pending",
      "metadata": {
        "document_version": "2.1",
        "approval_date": "2024-11-01",
        "approver": "Chief Information Security Officer",
        "review_date": "2025-11-01",
        "classification": "Internal Use Only"
      }
    }
  ]
}
```

**Evidence Types Included**:
- policy_document (5 items)
- audit_report (7 items)
- configuration_screenshot (3 items)
- procedure (1 item)

**Evidence Coverage**:
- IM8-01: 3 evidence items (policy, audit report, screenshot)
- IM8-02: 2 evidence items (diagram, audit report)
- IM8-03: 2 evidence items (policy, configuration)
- IM8-04: 2 evidence items (patch report, scan results)
- IM8-05: 1 evidence item (code review report)
- IM8-06: 2 evidence items (SIEM docs, IR plan)
- IM8-07: 1 evidence item (cloud assessment)
- IM8-08: 1 evidence item (change policy)
- IM8-09: 1 evidence item (risk register)
- IM8-10: 1 evidence item (DSS assessment)

---

## Usage Instructions

### Option 1: Direct API Upload (After Implementation)

**Upload Controls**:
```bash
curl -X POST "http://localhost:8000/api/controls/bulk-upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @storage/im8_controls_bulk_upload.json
```

**Upload Evidence**:
```bash
curl -X POST "http://localhost:8000/api/evidence/bulk-upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @storage/im8_evidence_bulk_upload.json
```

### Option 2: Via Agentic Chat (Natural Language)

**Example Prompts**:
```
"Upload the IM8 controls from the bulk upload file"

"Load all IM8 framework controls for project 1"

"Import the evidence documents for IM8 compliance"

"Bulk upload controls from storage/im8_controls_bulk_upload.json"
```

### Option 3: Validation Dry-Run (Test Before Upload)

Modify the JSON file to add validation mode:
```json
{
  "project_id": 1,
  "framework": "IM8",
  "validation_mode": "dry-run",
  "controls": [...]
}
```

---

## Validation Modes

### Strict Mode (Default)
- All items must be valid
- Transaction rolled back if any item fails
- Best for production uploads

### Lenient Mode
- Skips invalid items, processes valid ones
- Useful for partial imports
- Returns list of skipped items

### Dry-Run Mode
- Validates without saving to database
- Returns full validation report
- Perfect for testing before actual upload

---

## Expected Validation Results

### Controls File (im8_controls_bulk_upload.json)
✅ **All Valid** - Ready for upload
- 10 controls with complete data
- All required fields present
- Valid enum values
- Proper structure

### Evidence File (im8_evidence_bulk_upload.json)
⚠️ **Validation Warnings Expected**:
- File paths reference files that don't exist yet
- In production: upload actual files first, then reference them
- In testing: validation will flag missing files

**Recommended Flow**:
1. Upload controls first
2. Upload actual evidence files
3. Then link evidence metadata to controls

---

## Field Customization Guide

### Required Fields (Must be present)

**For Controls**:
- `project_id` - Integer (your project ID)
- `control_id` - String (unique identifier)
- `name` - String (3-500 chars)
- `description` - String (10-5000 chars)
- `framework` - String (IM8, NIST-800-53, ISO27001, etc.)

**For Evidence**:
- `control_id` - String (must match existing control)
- `title` - String (3-500 chars)
- `description` - String (10-5000 chars)
- `evidence_type` - Valid enum value

### Optional Fields (Can be customized)

- `status` - Change to match your workflow
- `requirement_level` - Adjust based on your needs
- `testing_frequency` - Modify schedule
- `metadata` - Add custom key-value pairs

---

## Common Modifications

### Change Project ID
Find and replace `"project_id": 1` with your actual project ID

### Change Framework
Find and replace `"framework": "IM8"` with your framework

### Adjust Testing Frequency
Change values like `"testing_frequency": "Quarterly"` to match your schedule

### Add Custom Metadata
In evidence items, expand the `metadata` object:
```json
"metadata": {
  "custom_field_1": "value",
  "custom_field_2": "value",
  "department": "IT Security",
  "cost_center": "CC-12345"
}
```

---

## File Locations

```
qa_compliance_assistant/
├── storage/
│   ├── im8_controls_bulk_upload.json      ← Controls template (READY)
│   ├── im8_evidence_bulk_upload.json      ← Evidence template (READY)
│   └── sample_im8_controls_evidence.csv   ← Original CSV format
├── VALIDATION_PLAN.md                     ← Detailed validation plan
└── UPLOAD_TEMPLATES_GUIDE.md              ← This file
```

---

## Next Steps

1. **Review the validation plan**: See `VALIDATION_PLAN.md`
2. **Confirm implementation approach**
3. **Customize templates** if needed for your specific use case
4. **Approve validation rules** and error codes
5. **Proceed with implementation** after your confirmation

---

## Questions?

- Want to customize the templates? → Modify the JSON files directly
- Need different framework? → Change "framework" field and control_id patterns
- Want to add more fields? → Extend the schema in validation plan
- Ready to proceed? → Confirm and we'll implement the validation service

---

**Status**: Templates Ready ✅  
**Validation Plan**: Pending Review  
**Implementation**: Awaiting Approval
