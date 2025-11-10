# IM8 Template Creation Guide

## Quick Start: CSV to Excel Conversion

### Option 1: Manual Creation in Excel (Recommended for now)
1. Open Excel
2. Create new workbook: `IM8_Assessment_Template.xlsx`
3. Create 6 sheets: Instructions, Metadata, Domain_1_Info_Security_Governance, Domain_2_Network_Security, Reference_Policies, Summary

#### Instructions Sheet:
```
Row 1: IM8 Assessment Template - Instructions
Row 3: Purpose: This template is used to document IM8 framework compliance assessment
Row 5-9: How to Complete (see full text in IM8_EXCEL_TEMPLATES_README.md)
Row 11-15: Embedding PDFs (see full text in IM8_EXCEL_TEMPLATES_README.md)
```

#### Other Sheets:
- Import each CSV from `/templates` folder:
  - `im8_template_metadata.csv` → Metadata sheet
  - `im8_template_domain1.csv` → Domain_1_Info_Security_Governance sheet
  - `im8_template_domain2.csv` → Domain_2_Network_Security sheet  
  - `im8_template_reference_policies.csv` → Reference_Policies sheet

#### Summary Sheet:
Create with formulas (see IM8_EXCEL_TEMPLATES_README.md)

### Option 2: Use Python Script (when Python is available)
```powershell
# Configure Python environment first
python -m pip install openpyxl

# Run template generator
python scripts/create_excel_templates.py
```

## Files Created

### CSV Templates (for manual conversion):
- ✅ `im8_template_metadata.csv`
- ✅ `im8_template_domain1.csv`
- ✅ `im8_template_domain2.csv`
- ✅ `im8_template_reference_policies.csv`
- ✅ `im8_sample_completed_metadata.csv`
- ✅ `im8_sample_completed_domain1.csv`
- ✅ `im8_sample_completed_domain2.csv`
- ✅ `im8_sample_completed_reference_policies.csv`

### Documentation:
- ✅ `IM8_EXCEL_TEMPLATES_README.md` - Complete guide

## Next Steps: Jump into Code

Now that templates are ready, we'll implement:

### 1. ExcelProcessor Service (Priority 2)
**File**: `api/src/services/excel_processor.py`
- Parse IM8 Excel structure
- Extract embedded PDFs
- Convert to structured data

### 2. IM8Validator Service (Priority 3)
**File**: `api/src/services/im8_validator.py`
- Validate required sheets
- Check control ID format
- Verify status values
- Ensure PDFs embedded

### 3. Modify Upload Endpoint (Priority 4)
**File**: `api/src/routers/evidence.py`
- Detect IM8 evidence type
- Parse and validate
- Auto-submit to "under_review"

### 4. Update Agentic Chat (Priority 5)
**File**: `api/src/services/agentic_assistant.py`
- Add role-specific IM8 guidance
- Auditor: template sharing prompts
- Analyst: completion instructions

## Status
✅ Templates designed
✅ CSV data created
✅ Documentation complete
🔄 Ready for code implementation
