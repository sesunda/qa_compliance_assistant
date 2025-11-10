# Evidence Upload Templates Guide

## Overview

The QA Compliance Assistant provides downloadable templates to help users upload evidence for IM8 controls in a structured format. This guide explains the available templates, validation rules, and best practices.

## Available Templates

### 1. CSV Template (Empty)
**Endpoint:** `GET /templates/evidence-upload.csv`

Download an empty CSV template with column headers and example rows.

**Columns:**
- `control_id` (Required) - The ID of the control this evidence supports
- `title` (Required) - Short descriptive title of the evidence
- `description` (Optional) - Detailed description of what this evidence demonstrates
- `evidence_type` (Required) - Type of evidence (see Evidence Types below)
- `file_path` (Optional) - Path to the actual evidence file if uploading separately
- `notes` (Optional) - Additional notes or context for reviewers

### 2. JSON Template (Empty)
**Endpoint:** `GET /templates/evidence-upload.json`

Download a JSON template with structure and instructions.

### 3. IM8 Controls Sample (Filled Example)
**Endpoint:** `GET /templates/im8-controls-sample.csv`

Download a realistic sample CSV file with 35+ evidence items covering all 10 IM8 domain areas. This shows:
- How to structure multiple evidence items per control
- Realistic titles, descriptions, and notes
- Examples of different evidence types
- Best practices for documentation

**Use Cases:**
- Understanding the expected format
- Learning how to describe evidence effectively
- Reference for IM8 compliance coverage
- Testing the upload functionality

### 4. Validation Rules
**Endpoint:** `GET /templates/template-validation-rules`

Get comprehensive validation rules including:
- Required vs. optional fields
- Field data types and max lengths
- Allowed values for enums
- IM8-specific guidance
- Quality guidelines

## Evidence Types

The system supports the following evidence types:

| Value | Label | Description |
|-------|-------|-------------|
| `policy_document` | Policy Document | Organizational policies, standards, and guidelines |
| `procedure` | Procedure/Process Document | Step-by-step procedures and workflows |
| `audit_report` | Audit Report | Internal or external audit findings and reports |
| `configuration_screenshot` | Configuration Screenshot | Screenshots showing system configurations |
| `log_file` | Log File/Export | System logs, access logs, audit trails |
| `certificate` | Certificate/Attestation | Certificates, licenses, attestations |
| `training_record` | Training Record | Training completion certificates and records |
| `test_result` | Test Result | Vulnerability scan results, penetration test reports |
| `other` | Other | Other types of evidence |

## Validation Rules

### Required Fields
- `control_id` - Must be a valid integer matching an existing control in the project
- `title` - String, max 255 characters
- `evidence_type` - Must be one of the values listed above

### Optional Fields
- `description` - String, max 5000 characters
- `file_path` - String, max 500 characters
- `notes` - String, max 2000 characters

### General Rules
1. CSV must be UTF-8 encoded
2. First row must contain column headers exactly as specified
3. Each row represents one evidence item
4. Multiple evidence items can reference the same `control_id`
5. Empty rows are ignored during processing
6. Commas within field values should be quoted (e.g., "This, has a comma")
7. Line breaks within fields are not recommended

## IM8 Domain Areas Reference

The sample template covers all 10 IM8 domain areas:

| Code | Name | Description |
|------|------|-------------|
| IM8-01 | Access & Identity Management | User accounts, roles, privileged access |
| IM8-02 | Network & Connectivity Security | Network segmentation, allow-by-exception |
| IM8-03 | Application & Data Protection | Data classification, encryption, output sanitisation |
| IM8-04 | Infrastructure & System Hardening | Patch management, least functionality, EOS assets |
| IM8-05 | Secure Development & Supply Chain | Code repository controls, dependency pinning |
| IM8-06 | Logging, Monitoring & Incident Response | Log aggregation, retention, alerting |
| IM8-07 | Third-Party & Vendor Management | Outsourcing, supply-chain governance |
| IM8-08 | Change, Release & Configuration Management | Change approvals, configuration drift control |
| IM8-09 | Governance, Risk & Compliance (GRC) | Risk registers, SSPs, residual risk acceptance |
| IM8-10 | Digital Service & Delivery Standards | DSS, agile delivery, lifecycle of digital services |

## Best Practices

### Evidence Quality Guidelines
1. **Recency** - Evidence should be recent (within last 12 months unless policy documents)
2. **Versioning** - Include version numbers and dates where applicable
3. **Traceability** - Reference the IM8 domain area being addressed
4. **Context** - Provide context in the notes field for reviewers
5. **Accessibility** - Ensure file paths are accessible to the system

### Recommended Coverage
- **3-5 evidence items per control** for comprehensive coverage
- Mix different evidence types (policy, procedure, audit, technical)
- Include both preventive and detective controls evidence
- Document both design and operating effectiveness

### Example Evidence Mix for One Control
For **IM8-01: Access & Identity Management**, you might include:
1. Policy document (design evidence)
2. Configuration screenshot (implementation evidence)
3. Audit report (operating effectiveness)
4. Log file (continuous monitoring)
5. Training record (awareness evidence)

## Using Templates in Agentic Chat

When the AI Assistant asks you to "upload evidence for control 5", you can:

1. **Download the empty template:**
   ```
   Download from: /templates/evidence-upload.csv
   ```

2. **View the sample for reference:**
   ```
   Download from: /templates/im8-controls-sample.csv
   ```

3. **Fill in your evidence details** following the format

4. **Upload via the chat interface** using the attach button

## API Integration

### Downloading Templates Programmatically

```bash
# Download empty CSV template
curl -X GET "https://ca-api-qca-dev.redcoast-ce82f6ff.westus2.azurecontainerapps.io/templates/evidence-upload.csv" -o template.csv

# Download IM8 sample
curl -X GET "https://ca-api-qca-dev.redcoast-ce82f6ff.westus2.azurecontainerapps.io/templates/im8-controls-sample.csv" -o sample.csv

# Get validation rules (JSON)
curl -X GET "https://ca-api-qca-dev.redcoast-ce82f6ff.westus2.azurecontainerapps.io/templates/template-validation-rules" | jq
```

### PowerShell Examples

```powershell
# Download empty template
Invoke-WebRequest -Uri "https://ca-api-qca-dev.redcoast-ce82f6ff.westus2.azurecontainerapps.io/templates/evidence-upload.csv" -OutFile "template.csv"

# Download IM8 sample
Invoke-WebRequest -Uri "https://ca-api-qca-dev.redcoast-ce82f6ff.westus2.azurecontainerapps.io/templates/im8-controls-sample.csv" -OutFile "sample.csv"

# Get validation rules
Invoke-RestMethod -Uri "https://ca-api-qca-dev.redcoast-ce82f6ff.westus2.azurecontainerapps.io/templates/template-validation-rules" | ConvertTo-Json -Depth 10
```

## Sample Data Reference

The `im8-controls-sample.csv` file includes 35+ realistic evidence items:

### Coverage Summary
- **IM8-01 (Access Control)**: 5 evidence items
- **IM8-02 (Network Security)**: 3 evidence items
- **IM8-03 (Data Protection)**: 3 evidence items
- **IM8-04 (System Hardening)**: 3 evidence items
- **IM8-05 (Secure Development)**: 3 evidence items
- **IM8-06 (Logging & Monitoring)**: 4 evidence items
- **IM8-07 (Vendor Management)**: 3 evidence items
- **IM8-08 (Change Management)**: 3 evidence items
- **IM8-09 (GRC)**: 4 evidence items
- **IM8-10 (Digital Standards)**: 3 evidence items

### Example Entries

#### Access Control Evidence (Control ID: 5)
```csv
5,Access Control Policy v2.1,Organization-wide access control policy covering authentication and RBAC,policy_document,/storage/uploads/access_control_policy_v2.1.pdf,Approved by CISO on 2024-11-01. Covers IM8-01 requirements.
5,User Access Review Report Q4 2024,Quarterly user access review showing all privileged accounts were reviewed,audit_report,/storage/uploads/user_access_review_q4_2024.xlsx,All exceptions documented. 3 accounts disabled per review.
```

#### Network Security Evidence (Control ID: 12)
```csv
12,Network Segmentation Architecture,Network diagram showing segmentation between DMZ production and internal networks,configuration_screenshot,/storage/uploads/network_segmentation_diagram.png,Updated after last penetration test.
12,Firewall Rule Review Report,Annual firewall rule review report showing all rules were validated,audit_report,/storage/uploads/firewall_rule_review_2024.pdf,Review completed on 2024-08-30.
```

## Troubleshooting

### Common Validation Errors

1. **"control_id must be an integer"**
   - Ensure control_id contains only numbers (e.g., `5` not `"5"`)

2. **"Invalid evidence_type"**
   - Check spelling and use exact values from the Evidence Types table
   - Common mistake: `policy` should be `policy_document`

3. **"Title too long"**
   - Keep titles under 255 characters
   - Move longer descriptions to the `description` field

4. **"control_id does not exist"**
   - Verify the control exists in your project
   - Check that you're uploading to the correct project

5. **"CSV parsing error"**
   - Ensure file is UTF-8 encoded
   - Check for unquoted commas in field values
   - Verify column headers match exactly

### Getting Help

If you encounter issues:
1. Download the validation rules: `/templates/template-validation-rules`
2. Compare your file to the sample: `/templates/im8-controls-sample.csv`
3. Check field lengths and data types
4. Verify control IDs exist in your project
5. Use the Agentic Chat to ask questions

## Future Enhancements

Planned features:
- Excel template support (.xlsx)
- Bulk upload validation endpoint
- Template for IM8 controls creation (not just evidence)
- Automated evidence type detection
- Template customization per agency
- Integration with document management systems

## Related Documentation

- [API Documentation](../README.md)
- [MCP Testing Guide](../../MCP_TESTING_GUIDE.md)
- [Evidence Control Mapping](../../EVIDENCE_CONTROL_MAPPING.md)
- [Testing Guide](../../TESTING_GUIDE.md)
