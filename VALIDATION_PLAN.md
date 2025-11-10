# Validation System Implementation Plan
## QA Compliance Assistant - Data Upload Validation

**Date**: November 10, 2025  
**Status**: Proposed - Awaiting Approval

---

## 1. Overview

This document outlines the comprehensive validation system for bulk data uploads (controls and evidence) in the QA Compliance Assistant application. The validation system ensures data integrity, prevents errors, and provides detailed feedback during both manual uploads and agentic workflows.

---

## 2. Validation Architecture

### 2.1 Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Validation Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Schema Validation (Pydantic)                      │
│  ├── Field types, required fields, format validation        │
│  ├── Data type coercion and normalization                   │
│  └── Basic structure validation                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Business Rules Validation                         │
│  ├── Cross-field dependencies                               │
│  ├── Enum values, status transitions                        │
│  ├── Reference integrity (project_id, control_id exists)    │
│  └── Domain-specific rules (IM8 framework compliance)       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Data Integrity Validation                         │
│  ├── Duplicate detection                                    │
│  ├── Circular dependency checks                             │
│  ├── Constraint validation (unique fields)                  │
│  └── Orphaned reference detection                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: File & Content Validation (Evidence only)         │
│  ├── File existence checks                                  │
│  ├── File type/extension validation                         │
│  ├── File size limits                                       │
│  ├── Malware scanning (future)                              │
│  └── Content format validation (PDF, CSV, etc.)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Validation Rules by Entity

### 3.1 Control Validation Rules

#### Required Fields
- ✅ `name` - Must be 3-500 characters
- ✅ `control_id` - Must follow pattern: `[A-Z0-9-]+` (e.g., IM8-01, AC-2)
- ✅ `description` - Must be 10-5000 characters
- ✅ `framework` - Must be one of: IM8, NIST-800-53, ISO27001, CIS, SOC2, Custom

#### Optional but Validated Fields
- `control_type` - Enum: Technical, Administrative, Physical
- `status` - Enum: pending, in_review, passed, failed, not_applicable
- `category` - String, 3-200 characters
- `requirement_level` - Enum: Mandatory, Recommended, Optional
- `testing_frequency` - Enum: Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Per-Project
- `assessment_score` - Integer: 0-100
- `test_procedure` - String, max 10,000 characters
- `evidence_requirements` - Array of strings, max 50 items

#### Business Rules
1. **Unique Control ID per Project**: No duplicate control_id within same project
2. **Framework Consistency**: All controls in batch must use same framework
3. **Status Transitions**: Valid status flow validation
4. **Testing Frequency Alignment**: If test_procedure exists, testing_frequency required
5. **Score Range**: If assessment_score provided, must be 0-100

#### Cross-Field Validation
- If `status` = "passed" → `assessment_score` should be ≥ 70
- If `test_procedure` provided → `testing_frequency` is required
- If `evidence_requirements` provided → must contain at least 1 item

---

### 3.2 Evidence Validation Rules

#### Required Fields
- ✅ `control_id` - Must reference existing control (reference check)
- ✅ `title` - Must be 3-500 characters
- ✅ `description` - Must be 10-5000 characters
- ✅ `evidence_type` - Must be one of valid types (see below)

#### Evidence Type Enum
- policy_document
- procedure
- audit_report
- audit_log
- configuration_screenshot
- test_result
- certificate
- log_file
- meeting_minutes
- training_record
- contract
- other

#### Optional but Validated Fields
- `file_path` - Valid path format, file must exist (if provided)
- `verification_status` - Enum: pending, under_review, approved, rejected
- `metadata` - JSON object with validated structure

#### Business Rules
1. **Control Reference Integrity**: control_id must exist in database or current batch
2. **Unique Evidence per Control**: No duplicate evidence titles per control
3. **File Path Validation**: If file_path provided, validate format and accessibility
4. **Evidence Type Matching**: Evidence type should align with file extension
5. **Metadata Structure**: Validate common metadata fields if present

#### File Validation (if file uploaded)
- **Size Limits**: Max 10MB per file (configurable)
- **Allowed Extensions**: .pdf, .docx, .txt, .csv, .json, .xml, .jpg, .jpeg, .png, .xlsx
- **File Naming**: Sanitize filenames, remove special characters
- **Storage Path**: Validate storage location is within allowed directories

---

## 4. Validation Service Implementation

### 4.1 File Structure

```
api/src/services/validation_service.py
├── ValidationService (main class)
├── ControlValidator
├── EvidenceValidator
├── BulkUploadValidator
└── ValidationResult (response model)
```

### 4.2 Validation Service Methods

```python
# Core validation methods
validate_control(control_data: dict) -> ValidationResult
validate_evidence(evidence_data: dict) -> ValidationResult
validate_bulk_controls(bulk_data: dict) -> BulkValidationResult
validate_bulk_evidence(bulk_data: dict) -> BulkValidationResult

# Helper methods
check_reference_integrity(entity_type, entity_id, db) -> bool
check_duplicates(data_list: list, key: str) -> List[dict]
validate_file_upload(file: UploadFile) -> ValidationResult
sanitize_filename(filename: str) -> str
```

### 4.3 Validation Result Schema

```python
class ValidationError(BaseModel):
    field: str
    message: str
    error_code: str
    severity: str  # error, warning, info

class ValidationResult(BaseModel):
    valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    data_normalized: Optional[dict] = None  # Cleaned/normalized data

class BulkValidationResult(BaseModel):
    valid: bool
    total_items: int
    valid_items: int
    invalid_items: int
    errors_by_item: Dict[int, List[ValidationError]]
    warnings_by_item: Dict[int, List[ValidationError]]
    summary: str
```

---

## 5. API Endpoint Specifications

### 5.1 Bulk Upload Controls

**Endpoint**: `POST /api/controls/bulk-upload`

**Request Body**:
```json
{
  "project_id": 1,
  "framework": "IM8",
  "upload_metadata": {
    "uploaded_by": "username",
    "description": "Batch description"
  },
  "controls": [
    {
      "control_id": "IM8-01",
      "name": "Control Name",
      "description": "Description",
      ...
    }
  ],
  "validation_mode": "strict"  // strict, lenient, dry-run
}
```

**Response** (Success):
```json
{
  "status": "success",
  "controls_created": 10,
  "validation_report": {
    "total": 10,
    "valid": 10,
    "invalid": 0,
    "warnings": []
  },
  "control_ids": [1, 2, 3, ...]
}
```

**Response** (Validation Failed):
```json
{
  "status": "validation_failed",
  "controls_created": 0,
  "validation_report": {
    "total": 10,
    "valid": 7,
    "invalid": 3,
    "errors": [
      {
        "item_index": 2,
        "field": "control_id",
        "message": "Duplicate control_id: IM8-03",
        "error_code": "DUPLICATE_CONTROL_ID"
      }
    ]
  }
}
```

---

### 5.2 Bulk Upload Evidence

**Endpoint**: `POST /api/evidence/bulk-upload`

**Request Body**:
```json
{
  "project_id": 1,
  "framework": "IM8",
  "upload_metadata": {
    "uploaded_by": "username",
    "description": "Evidence batch"
  },
  "evidence_items": [
    {
      "control_id": "IM8-01",
      "title": "Evidence Title",
      "description": "Description",
      "evidence_type": "policy_document",
      ...
    }
  ],
  "validation_mode": "strict"
}
```

---

## 6. Validation Modes

### 6.1 Strict Mode (Default)
- All validation rules enforced
- Transaction rolled back if ANY item fails
- Returns detailed error for each invalid item
- **Use Case**: Production uploads, compliance requirements

### 6.2 Lenient Mode
- Required field validation only
- Skips invalid items, processes valid ones
- Returns list of skipped items with reasons
- **Use Case**: Data migration, partial imports

### 6.3 Dry-Run Mode
- Validates data without persisting to database
- Returns full validation report
- Useful for pre-upload validation
- **Use Case**: Testing, validation before actual upload

---

## 7. Integration with Agentic Workflows

### 7.1 Agentic Assistant Integration

**Modified Flow**:
```
User Request → Intent Classification → Parameter Extraction
    ↓
Validation Service Check
    ↓
├── Valid → Execute Task → Persist Data
└── Invalid → Return Clarifying Questions + Errors
```

### 7.2 Tools to Update

1. **`mcp_fetch_evidence`** tool
   - Add validation before fetching/creating evidence
   - Return validation errors in tool response

2. **`mcp_analyze_compliance`** tool
   - Validate control data before analysis
   - Include validation status in analysis output

3. **`search_documents`** tool
   - Validate file types and sizes before indexing

4. **AI Task Orchestrator**
   - Add validation step in task execution pipeline
   - Store validation results in task metadata

---

## 8. Error Codes & Messages

### 8.1 Control Validation Error Codes

| Code | Message Template | Severity |
|------|------------------|----------|
| `CTRL_001` | Control ID is required | error |
| `CTRL_002` | Invalid control ID format: {value} | error |
| `CTRL_003` | Duplicate control ID: {control_id} | error |
| `CTRL_004` | Control name must be 3-500 characters | error |
| `CTRL_005` | Invalid framework: {value}. Must be one of: {allowed} | error |
| `CTRL_006` | Invalid status: {value} | error |
| `CTRL_007` | Assessment score must be 0-100, got: {value} | error |
| `CTRL_008` | Test procedure requires testing_frequency | warning |
| `CTRL_009` | Project ID {project_id} does not exist | error |
| `CTRL_010` | Status 'passed' with score < 70 is inconsistent | warning |

### 8.2 Evidence Validation Error Codes

| Code | Message Template | Severity |
|------|------------------|----------|
| `EVID_001` | Evidence title is required | error |
| `EVID_002` | Control ID {control_id} does not exist | error |
| `EVID_003` | Invalid evidence type: {value} | error |
| `EVID_004` | File path does not exist: {path} | error |
| `EVID_005` | File size exceeds limit: {size}MB > {limit}MB | error |
| `EVID_006` | File type not allowed: {extension} | error |
| `EVID_007` | Duplicate evidence title for control: {title} | warning |
| `EVID_008` | Evidence type mismatch with file extension | warning |
| `EVID_009` | Metadata validation failed: {details} | error |

---

## 9. Schema Enhancements

### 9.1 New Pydantic Schemas

**File**: `api/src/schemas.py`

```python
# Bulk Upload Schemas
class UploadMetadata(BaseModel):
    upload_date: Optional[str]
    uploaded_by: str
    description: Optional[str]
    version: Optional[str]

class ControlBulkCreate(BaseModel):
    control_id: str = Field(..., pattern=r'^[A-Z0-9-]+$', min_length=2, max_length=50)
    name: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    control_type: Optional[Literal['Technical', 'Administrative', 'Physical']]
    status: Optional[Literal['pending', 'in_review', 'passed', 'failed', 'not_applicable']]
    framework: str
    category: Optional[str] = Field(None, min_length=3, max_length=200)
    requirement_level: Optional[Literal['Mandatory', 'Recommended', 'Optional']]
    implementation_guidance: Optional[str]
    evidence_requirements: Optional[List[str]] = Field(None, max_items=50)
    testing_frequency: Optional[Literal['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual', 'Per-Project']]
    test_procedure: Optional[str] = Field(None, max_length=10000)
    assessment_score: Optional[int] = Field(None, ge=0, le=100)

class BulkUploadControls(BaseModel):
    project_id: int
    framework: str
    upload_metadata: UploadMetadata
    controls: List[ControlBulkCreate] = Field(..., min_items=1, max_items=500)
    validation_mode: Optional[Literal['strict', 'lenient', 'dry-run']] = 'strict'

class EvidenceBulkCreate(BaseModel):
    control_id: str
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    evidence_type: Literal[
        'policy_document', 'procedure', 'audit_report', 'audit_log',
        'configuration_screenshot', 'test_result', 'certificate',
        'log_file', 'meeting_minutes', 'training_record', 'contract', 'other'
    ]
    file_path: Optional[str]
    verification_status: Optional[Literal['pending', 'under_review', 'approved', 'rejected']]
    metadata: Optional[Dict[str, Any]]

class BulkUploadEvidence(BaseModel):
    project_id: int
    framework: str
    upload_metadata: UploadMetadata
    evidence_items: List[EvidenceBulkCreate] = Field(..., min_items=1, max_items=500)
    validation_mode: Optional[Literal['strict', 'lenient', 'dry-run']] = 'strict'
```

---

## 10. Implementation Steps

### Phase 1: Core Validation Service (Priority 1)
1. ✅ Create `validation_service.py` with base classes
2. ✅ Implement `ControlValidator` with all rules
3. ✅ Implement `EvidenceValidator` with all rules
4. ✅ Add error code system and messages
5. ✅ Write unit tests for validators

### Phase 2: Bulk Upload Endpoints (Priority 1)
1. ✅ Add bulk upload schemas to `schemas.py`
2. ✅ Create `POST /controls/bulk-upload` endpoint
3. ✅ Create `POST /evidence/bulk-upload` endpoint
4. ✅ Add transaction management (rollback on error)
5. ✅ Add validation mode support

### Phase 3: Agentic Integration (Priority 2)
1. ✅ Update `agentic_assistant.py` to use ValidationService
2. ✅ Update `ai_task_orchestrator.py` with validation steps
3. ✅ Modify MCP tools to return validation errors
4. ✅ Add validation results to task metadata

### Phase 4: Testing & Documentation (Priority 2)
1. ✅ Create test datasets (valid and invalid)
2. ✅ Integration tests for bulk uploads
3. ✅ API documentation updates
4. ✅ User guide for validation errors

### Phase 5: Enhancements (Priority 3)
1. ⬜ File content validation (PDF parsing, CSV structure)
2. ⬜ Malware scanning integration
3. ⬜ Async validation for large batches
4. ⬜ Validation caching for performance

---

## 11. Performance Considerations

### 11.1 Batch Size Limits
- **Controls**: Max 500 per batch
- **Evidence**: Max 500 per batch
- **Rationale**: Balance between throughput and transaction size

### 11.2 Validation Optimization
- Use database bulk queries for reference checks
- Cache validation results for duplicate detection
- Parallel validation for independent items (future)

### 11.3 Database Transactions
- Single transaction per batch (strict mode)
- Partial commits allowed (lenient mode)
- No database writes (dry-run mode)

---

## 12. Security Considerations

### 12.1 Input Sanitization
- SQL injection prevention via parameterized queries
- XSS prevention via input escaping
- Path traversal prevention in file paths
- Filename sanitization

### 12.2 Authorization Checks
- Verify user has permission for project_id
- Verify user role allows bulk upload
- Audit logging for all uploads

### 12.3 File Upload Security
- File type whitelist enforcement
- File size limits
- Malware scanning (future enhancement)
- Storage location restrictions

---

## 13. Monitoring & Logging

### 13.1 Validation Metrics
- Track validation success/failure rates
- Monitor common validation errors
- Alert on unusual validation patterns

### 13.2 Audit Trail
- Log all bulk upload attempts
- Store validation results
- Track data lineage

---

## 14. Questions for Review

1. **Batch Size Limits**: Is 500 items per batch appropriate? Should this be configurable?

2. **Validation Strictness**: Should we add a "custom" validation mode for specific use cases?

3. **File Validation**: Should we implement file content parsing (e.g., verify PDF is readable)?

4. **Async Processing**: For large batches (>100 items), should we use background task processing?

5. **Duplicate Strategy**: How should we handle duplicates in lenient mode? Skip, update, or create with suffix?

6. **Framework Validation**: Should we maintain a registry of allowed frameworks and their control ID patterns?

---

## 15. Recommendations

### ✅ Approve and Proceed
- Comprehensive validation at all layers
- Clear error messages for users
- Support for different validation modes
- Seamless integration with agentic workflows

### 🔄 Review Before Implementation
- Fine-tune batch size limits based on testing
- Confirm error code structure
- Validate file upload security measures

### 📋 Future Enhancements
- Add validation rule configuration UI
- Implement custom validation rules per framework
- Add machine learning for anomaly detection
- Real-time validation feedback during data entry

---

## Appendix A: Sample Upload Files

**Available Templates**:
1. ✅ `storage/im8_controls_bulk_upload.json` - 10 IM8 controls with complete data
2. ✅ `storage/im8_evidence_bulk_upload.json` - 16 evidence items mapped to IM8 controls
3. ⬜ `storage/sample_invalid_controls.json` - Test file with validation errors (to be created)

---

**Document Status**: Ready for Review  
**Next Action**: Await confirmation to proceed with implementation
