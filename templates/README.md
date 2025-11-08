# Compliance Assistant Upload Templates

This directory contains JSON templates for bulk uploading data to the Compliance Assistant system using the AI-powered agent task system.

## Available Templates

### 1. Controls Upload Template (`controls_upload_template.json`)
**Purpose**: Bulk upload compliance controls from frameworks like IM8, ISO27001, or NIST.

**Usage**:
- Modify the `controls` array with your control data
- Set the correct `project_id`
- Submit via AI Assistant or POST to `/agent-tasks/`

**Fields**:
- `name`: Control name/title
- `description`: Detailed control description
- `control_type`: Category (Access Control, Audit, etc.)
- `framework`: IM8, ISO27001, NIST, etc.
- `control_id`: Unique identifier (e.g., AC-1, AU-2)
- `evidence_requirements`: List of required evidence types

---

### 2. Assessment Template (`assessment_template.json`)
**Purpose**: Create a new security assessment or compliance audit.

**Usage**:
- Update assessment details (title, dates, scope)
- Specify which controls to test
- Assign to a team member (optional)

**Fields**:
- `assessment_type`: compliance_audit, vapt, infra_pt
- `framework`: Target compliance framework
- `scope`: What systems/processes are covered
- `controls_to_test`: List of control IDs to assess

---

### 3. Findings Upload Template (`findings_upload_template.json`)
**Purpose**: Bulk import security findings from VAPT, audits, or assessments.

**Usage**:
- Set the `assessment_id` to link findings to an assessment
- Add findings with severity, remediation, and evidence
- Set due dates and priorities

**Fields**:
- `severity`: critical, high, medium, low, informational
- `cvss`: CVSS score (0.0-10.0)
- `remediation`: Detailed remediation steps
- `priority`: critical, high, medium, low
- `assigned_to`: User ID to assign finding to

---

### 4. Evidence Upload Template (`evidence_upload_template.json`)
**Purpose**: Upload evidence documents and link them to controls.

**Usage**:
- Specify file locations (Azure Blob Storage paths)
- Link to specific control IDs
- Request AI analysis for automatic metadata extraction

**Fields**:
- `type`: file, screenshot, url, document
- `location`: File path or URL
- `control_id`: Which control this evidence supports
- `evidence_type`: policy, audit_log, screenshot, configuration
- `ai_analysis_requested`: Enable AI-powered analysis

---

## Maker-Checker Workflow

Evidence submissions support a maker-checker workflow:

1. **Maker** (Analyst): Uploads evidence with `verification_status: "pending"`
2. **Checker** (Reviewer): Reviews evidence and sets status to:
   - `"approved"` - Evidence accepted
   - `"rejected"` - Evidence rejected (with comments)
   - `"under_review"` - Needs more information

**Workflow Fields**:
- `verification_status`: pending, under_review, approved, rejected
- `submitted_by`: User ID who submitted
- `reviewed_by`: User ID who reviewed
- `review_comments`: Reviewer's feedback

---

## AI-Powered Features

### Automatic Evidence Analysis
When `ai_analysis_requested: true`, the system will:
- Extract metadata from documents
- Validate completeness against control requirements
- Suggest control mappings
- Generate quality scores
- Identify missing information

### Natural Language Upload
You can also upload via AI Assistant conversation:
```
User: "Upload 10 IM8 access control policies"
AI: "I'll help you upload those. Do you have the file path?"
User: "/storage/controls/im8_access_controls.json"
AI: *Creates agent task and processes upload*
```

---

## API Endpoint

All templates are submitted via:
```http
POST /agent-tasks/
Content-Type: application/json
Authorization: Bearer <your-token>

{
  "task_type": "bulk_upload_controls",
  "title": "Upload IM8 Controls",
  ...template payload...
}
```

---

## Example Workflow

### Complete Assessment Workflow:
1. **Create Assessment** using `assessment_template.json`
2. **Upload Controls** using `controls_upload_template.json`
3. **Perform Testing** (manual or automated)
4. **Upload Findings** using `findings_upload_template.json`
5. **Upload Evidence** using `evidence_upload_template.json`
6. **Generate Report** via `/reports/generate`

---

## Notes

- All templates include example data - replace with your actual data
- File paths should point to Azure Blob Storage locations
- User IDs must exist in the system
- Control IDs must match existing controls
- Dates should be in ISO 8601 format (YYYY-MM-DD)

---

## Support

For questions or issues:
1. Check the API documentation at `/docs`
2. View agent task status at `/agent-tasks/{task_id}`
3. Use AI Assistant for guided uploads
