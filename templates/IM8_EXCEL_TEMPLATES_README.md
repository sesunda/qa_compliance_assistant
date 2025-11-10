# IM8 Excel Templates

## Overview
This folder contains IM8 assessment Excel templates for the QA Compliance Assistant.

## Templates

### 1. IM8_Assessment_Template.xlsx (Blank Template)
**Purpose**: For auditors to share with analysts for new assessments

**Structure**:
- **Instructions Sheet**: How to use the template, embedding PDFs, completion guide
- **Metadata Sheet**: Project information (ID, name, agency, period, contact)
- **Domain_1_Info_Security_Governance Sheet**: 2 controls (IM8-01-01, IM8-01-02)
- **Domain_2_Network_Security Sheet**: 2 controls (IM8-02-01, IM8-02-02)
- **Reference_Policies Sheet**: Supporting policy documents list
- **Summary Sheet**: Auto-calculated assessment progress

### 2. IM8_Assessment_Sample_Completed.xlsx (Sample)
**Purpose**: Example of a completed IM8 assessment with embedded PDFs

**Sample Data**:
- **Project**: "Digital Services Platform" (Agency: Government Digital Services)
- **4 Controls**: 3 Implemented, 1 Partial
- **4 Embedded PDFs**: 
  - access_control_policy.pdf (Domain 1, Control 01)
  - user_access_review_q4_2024.pdf (Domain 1, Control 02)
  - network_diagram.pdf (Domain 2, Control 01)
  - firewall_rules_review.pdf (Domain 2, Control 02)

## Sheet Details

### Instructions Sheet
```
IM8 Assessment Template - Instructions

Purpose: This template is used to document IM8 framework compliance assessment

How to Complete:
1. Fill in the Metadata sheet with project information
2. For each domain sheet, complete all control rows
3. Embed PDF evidence documents in the 'Evidence' column
4. Add implementation notes in the 'Notes' column
5. Upload the completed file through the QA Compliance Assistant

Embedding PDFs:
- Click on the Evidence cell
- Insert > Object > Create from File
- Browse and select your PDF document
- Check 'Display as icon' for better visibility

Required Fields:
- All Control IDs must be filled
- All Status fields must be: Implemented, Partial, or Not Started
- At least one PDF evidence per control

Questions? Contact your auditor.
```

### Metadata Sheet
| Field | Value |
|-------|-------|
| Project ID | [Auto-filled from system] |
| Project Name | [Enter project name] |
| Framework | IM8 |
| Assessment Period | [e.g., Q4 2025] |
| Submitted By | [Auto-filled from user] |
| Submission Date | [Auto-filled] |
| Version | 1.0 |
| Agency | [Select from dropdown] |
| Contact Email | [Enter email] |

### Domain Sheet Structure
Each domain sheet has these columns:

| Column | Description | Required | Validation |
|--------|-------------|----------|------------|
| Control ID | IM8 control identifier | Yes | Format: IM8-DD-CC |
| Control Name | Short control title | Yes | Text |
| Description | Full control requirement | Yes | Text |
| Status | Implementation status | Yes | Dropdown: Implemented, Partial, Not Started |
| Evidence | Embedded PDF document | Yes | Must have embedded file |
| Implementation Date | When control was implemented | Yes | Date format |
| Notes | Additional implementation details | No | Text |

### Domain 1: Information Security Governance

**IM8-01-01: Identity and Access Management**
- Description: Implement robust identity and access management controls including authentication, authorization, and user lifecycle management
- Expected Evidence: Access control policy, MFA configuration, user provisioning process

**IM8-01-02: User Access Reviews**
- Description: Conduct regular user access reviews to ensure appropriate access levels and remove unnecessary permissions
- Expected Evidence: Access review reports, remediation evidence, review schedule

### Domain 2: Network Security

**IM8-02-01: Network Segmentation**
- Description: Implement network segmentation between production, development, and DMZ zones with appropriate firewall rules
- Expected Evidence: Network diagrams, segmentation policies, VLAN configurations

**IM8-02-02: Firewall Management**
- Description: Maintain firewall rules following allow-by-exception principle with regular rule reviews
- Expected Evidence: Firewall rule documentation, review logs, change management records

### Reference_Policies Sheet
| Policy Name | Version | Approval Date | Document Location | Notes |
|-------------|---------|---------------|-------------------|-------|
| Access Control Policy | | | | |
| Network Security Policy | | | | |
| Data Classification Standard | | | | |
| Incident Response Plan | | | | |

### Summary Sheet
```
IM8 Assessment Summary

Total Controls: 4
Implemented: [Auto-calculated]
Partial: [Auto-calculated]
Not Started: [Auto-calculated]
Completion %: [Auto-calculated]

Evidence Attached: Check each domain sheet

Assessment Date: [From metadata]
Next Review Date: [From metadata]
```

## How to Embed PDFs

### Method 1: Insert Object (Excel Desktop)
1. Click on the Evidence cell (Column E)
2. Go to Insert tab → Object
3. Click "Create from File"
4. Browse and select your PDF
5. Check "Display as icon"
6. Optional: Check "Link to file" if PDF may be updated
7. Click OK

### Method 2: Drag and Drop
1. Open the PDF in Adobe Reader
2. Drag the PDF file directly into the Evidence cell
3. Excel will automatically create an embedded object

### Method 3: Copy-Paste (from Adobe Reader)
1. Open PDF in Adobe Reader
2. Right-click → Copy
3. In Excel, right-click the Evidence cell → Paste Special → Adobe Acrobat Document

## Validation Rules

The system validates:
1. ✅ All required sheets present (Instructions, Metadata, Domain_1, Domain_2, Summary, Reference_Policies)
2. ✅ Control ID format: `IM8-\d{2}-\d{2}` (e.g., IM8-01-01)
3. ✅ Status values: Only "Implemented", "Partial", or "Not Started"
4. ✅ At least one embedded PDF per control
5. ✅ Valid date formats (YYYY-MM-DD or Excel date)
6. ✅ Required metadata fields filled

## Upload Workflow

### For Analysts:
1. Download blank template from auditor or system
2. Complete all fields in Metadata sheet
3. For each control in Domain sheets:
   - Fill Control ID, Name, Description (pre-filled)
   - Select Status from dropdown
   - Embed PDF evidence using Insert > Object
   - Enter Implementation Date
   - Add Notes (optional but recommended)
4. Review Reference_Policies sheet
5. Check Summary sheet for completion %
6. Upload to QA Compliance Assistant
7. File automatically goes to "Under Review" status

### For Auditors:
1. Review submitted IM8 documents in "Under Review" queue
2. Open and verify:
   - All controls addressed
   - PDFs embedded and accessible
   - Evidence supports claimed status
   - Implementation dates reasonable
3. Decision:
   - **Approve**: Document marked as "Approved", evidence accepted
   - **Reject**: Document returned to analyst with review comments
4. Add review comments explaining decision

## Future Integration: Findings Link

**Note**: Future enhancement will link IM8 evidence to Findings:
- Vulnerability Assessment findings → IM8 controls
- Infrastructure Penetration Test findings → IM8 controls
- Allows auditors to see which findings relate to which IM8 controls
- Helps track remediation across compliance frameworks

## File Naming Convention
- Blank: `IM8_Assessment_Template.xlsx`
- Completed: `IM8_Assessment_[ProjectName]_[Date].xlsx`
- Example: `IM8_Assessment_DigitalServices_20251110.xlsx`

## Technical Details

### Embedded PDF Extraction
When uploaded, the system:
1. Uses `openpyxl` to read Excel file
2. Extracts OLE objects (embedded PDFs)
3. Saves PDFs to evidence storage with checksums
4. Links PDFs to Evidence records via metadata_json
5. Maintains original Excel file as master document

### Metadata JSON Structure
```json
{
  "evidence_type": "im8_assessment_document",
  "framework": "IM8",
  "project_id": "1",
  "project_name": "Digital Services Platform",
  "assessment_period": "Q4 2025",
  "domains": [
    {
      "domain_name": "Domain 1: Information Security Governance",
      "controls": [
        {
          "control_id": "IM8-01-01",
          "control_name": "Identity and Access Management",
          "status": "Implemented",
          "implementation_date": "2024-10-15",
          "evidence_file_id": "uuid-of-extracted-pdf",
          "notes": "MFA enabled for all admin accounts..."
        }
      ]
    }
  ],
  "reference_policies": [...],
  "total_controls": 4,
  "implemented": 3,
  "partial": 1,
  "not_started": 0,
  "completion_percentage": 75
}
```

## Sample Data Details

### Sample Project: Digital Services Platform
- **Agency**: Government Digital Services
- **Period**: Q4 2025
- **Submitted By**: analyst@example.com
- **Submission Date**: 2025-11-10

### Sample Controls Status:
1. **IM8-01-01** (Identity and Access Management): ✅ Implemented
   - Evidence: access_control_policy.pdf
   - Notes: MFA enabled, Azure AD integrated, quarterly reviews

2. **IM8-01-02** (User Access Reviews): ✅ Implemented
   - Evidence: user_access_review_q4_2024.pdf
   - Notes: Quarterly reviews, last Q4 2024, 3 accounts disabled

3. **IM8-02-01** (Network Segmentation): ⚠️ Partial
   - Evidence: network_diagram.pdf
   - Notes: DMZ/prod segmented, internal segmentation Q1 2026

4. **IM8-02-02** (Firewall Management): ✅ Implemented
   - Evidence: firewall_rules_review.pdf
   - Notes: Annual review, 342 rules reviewed, 15 removed

### Completion: 75% (3 Implemented, 1 Partial, 0 Not Started)

## Questions?
Contact your system administrator or auditor for assistance.
