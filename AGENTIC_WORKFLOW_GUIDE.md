# Agentic AI Compliance Assistant - Complete Workflow Guide

## 🎯 Overview

This is an **agentic AI system** that automates compliance management workflows. The AI assistant can autonomously execute tasks, analyze evidence, generate reports, and coordinate multi-user workflows.

---

## 👥 User Roles & Responsibilities

### 1. **Super Admin** (Alice Tan - Current User)
- Full system access
- Create agencies and users
- Approve high-risk decisions
- System configuration

### 2. **Admin** (Agency Level)
- Manage agency users
- Create projects and assessments
- Approve critical findings
- Generate compliance reports

### 3. **Analyst** (Maker)
- Upload controls and evidence
- Map IM8 controls to systems
- Document compliance activities
- Submit evidence for review

### 4. **Auditor** (Checker)
- Review evidence submissions
- Validate control implementations
- Approve/reject findings
- Generate audit reports

### 5. **Viewer**
- Read-only access
- View dashboards
- Download reports
- Monitor compliance status

---

## 🏛️ Singapore IM8 Framework Structure

### 10 Domain Areas:

1. **IM8-01**: Access & Identity Management
2. **IM8-02**: Network & Connectivity Security
3. **IM8-03**: Application & Data Protection
4. **IM8-04**: Infrastructure & System Hardening
5. **IM8-05**: Secure Development & Supply Chain
6. **IM8-06**: Logging, Monitoring & Incident Response
7. **IM8-07**: Third-Party & Vendor Management
8. **IM8-08**: Change, Release & Configuration Management
9. **IM8-09**: Governance, Risk & Compliance (GRC)
10. **IM8-10**: Digital Service & Delivery Standards

---

## 📋 Complete Workflow: IM8 Compliance Assessment

### **Phase 1: Setup (Admin)**

#### Step 1.1: Create Project
Navigate to **Projects** → **New Project**

```json
{
  "name": "2025 Annual IM8 Compliance Assessment",
  "project_type": "compliance_audit",
  "description": "Annual compliance assessment against Singapore IM8 framework for all critical systems",
  "status": "planning"
}
```

#### Step 1.2: Create Assessment
Navigate to **Assessments** → **New Assessment**

```json
{
  "title": "Q4 2025 IM8 Compliance Audit",
  "assessment_type": "compliance_audit",
  "framework": "IM8",
  "scope": "All production systems, databases, and applications handling sensitive government data",
  "assessment_period_start": "2025-10-01",
  "assessment_period_end": "2025-12-31",
  "assigned_to": 2,
  "target_completion_date": "2025-12-31"
}
```

---

### **Phase 2: Control Mapping (Analyst - Agentic)**

#### Step 2.1: Use AI Assistant to Upload IM8 Controls

**Prompt to AI Assistant:**

```
I need to upload the complete IM8 framework controls for our compliance assessment. 
Please create 30 controls covering all 10 IM8 domain areas (IM8-01 through IM8-10). 
Include:
- Access Control (IM8-01): 5 controls
- Network Security (IM8-02): 3 controls  
- Data Protection (IM8-03): 4 controls
- System Hardening (IM8-04): 3 controls
- Secure Development (IM8-05): 3 controls
- Logging & Monitoring (IM8-06): 4 controls
- Vendor Management (IM8-07): 2 controls
- Change Management (IM8-08): 3 controls
- GRC (IM8-09): 2 controls
- Digital Services (IM8-10): 1 control

Each control should have:
- Clear implementation guidance
- Evidence requirements
- Testing frequency (Quarterly/Semi-Annual/Annual)
- Mandatory requirement level

Link them to project_id: 1
```

**What the Agent Does:**
1. ✅ Generates comprehensive control definitions
2. ✅ Maps to IM8 domain areas
3. ✅ Creates bulk upload task
4. ✅ Executes upload via background worker
5. ✅ Returns task ID for tracking

#### Step 2.2: Map Controls to Assessment

**Prompt to AI Assistant:**

```
Link all 30 IM8 controls I just uploaded to assessment ID 1 (Q4 2025 IM8 Compliance Audit).
Set initial testing status to "pending" for all controls.
```

---

### **Phase 3: Evidence Collection (Analyst - Maker)**

#### Step 3.1: Upload System Configuration Evidence

**Prompt to AI Assistant:**

```
I need to upload evidence for IM8-01 Access Control controls. I have:

1. Active Directory Group Policy export (ad_policies.json)
2. MFA configuration screenshot (mfa_config.png)
3. User access review spreadsheet (access_review_q4.xlsx)
4. Privileged access management policy (pam_policy.pdf)

Please analyze these files and:
- Extract relevant metadata
- Map to appropriate IM8-01 controls
- Validate completeness
- Flag any missing evidence requirements
- Set verification_status to "pending" for auditor review

Files are located in: /storage/evidence/2025/q4/access-control/
```

**What the Agent Does:**
1. ✅ Reads files from Azure Blob Storage
2. ✅ Performs AI analysis on content
3. ✅ Extracts metadata (dates, owners, coverage)
4. ✅ Maps evidence to specific controls
5. ✅ Validates against control requirements
6. ✅ Creates evidence records with status "pending"
7. ✅ Notifies auditor for review

#### Step 3.2: Upload Audit Logs

**Prompt to AI Assistant:**

```
Upload security event logs for IM8-06 (Logging & Monitoring) controls:

- Authentication logs: /storage/logs/auth_logs_oct_2025.json
- Admin activity logs: /storage/logs/admin_activity_oct_2025.json
- Database access logs: /storage/logs/db_access_oct_2025.json

Analyze for:
- Log completeness (are all required events logged?)
- Retention compliance (90-day minimum)
- Sensitive data exposure
- Suspicious activities

Map to controls: AU-1, AU-2, AU-3, AU-12
```

---

### **Phase 4: Testing & Findings (Analyst)**

#### Step 4.1: Document Test Results

**Prompt to AI Assistant:**

```
I performed penetration testing on the web application portal. 
Generate findings from this VAPT report:

Critical findings:
1. SQL Injection in login form (CVSS 9.8)
2. Stored XSS in comment field (CVSS 7.2)

High findings:
3. Missing security headers (CVSS 6.5)
4. Weak password policy (CVSS 6.1)

Medium findings:
5. Information disclosure in error messages (CVSS 5.3)
6. Session timeout too long (CVSS 4.8)

Create findings linked to assessment ID 1, assign to analyst ID 2, 
set appropriate due dates (Critical: 30 days, High: 60 days, Medium: 90 days),
and map to relevant IM8-03 (Application Security) controls.
```

**What the Agent Does:**
1. ✅ Parses VAPT findings
2. ✅ Creates structured finding records
3. ✅ Calculates risk scores
4. ✅ Sets priority and due dates
5. ✅ Maps to IM8 controls (IM8-03)
6. ✅ Assigns to responsible analyst
7. ✅ Triggers notification workflow

#### Step 4.2: Bulk Upload Infrastructure Findings

**Prompt to AI Assistant:**

```
Import findings from our infrastructure assessment CSV file:
/storage/assessments/infra_findings_2025.csv

The CSV has columns: title, severity, cvss, description, affected_system, remediation

Map these to IM8-04 (Infrastructure Hardening) controls and assessment ID 1.
Set priority based on CVSS score:
- 9.0-10.0: Critical priority
- 7.0-8.9: High priority
- 4.0-6.9: Medium priority
- 0.0-3.9: Low priority
```

---

### **Phase 5: Evidence Review (Auditor - Checker)**

#### Step 5.1: Review Pending Evidence

Navigate to **Evidence** → Filter by "Pending Review"

**Auditor Actions:**
1. Review evidence document
2. Verify against control requirements
3. Check completeness and validity

**Approval:**
```json
{
  "verification_status": "approved",
  "review_comments": "Evidence complete. MFA properly configured for all privileged accounts. Compliant with IM8-01 requirements."
}
```

**Rejection:**
```json
{
  "verification_status": "rejected",
  "review_comments": "Missing: Service account access review. Evidence only covers human users. Please provide complete access review including all service accounts per IM8-01 AC-2 requirements."
}
```

#### Step 5.2: AI-Assisted Bulk Review

**Prompt to AI Assistant:**

```
Review all pending evidence items for IM8-06 (Logging & Monitoring) controls.

For each evidence item, check:
1. Log retention period >= 90 days (IM8 requirement)
2. Contains authentication events
3. Contains administrative actions
4. Contains security events (failed logins, privilege escalation)
5. Logs are tamper-evident (integrity protection)

Auto-approve items meeting all criteria.
Flag items with issues for manual review.
Provide detailed review comments for each item.
```

---

### **Phase 6: Findings Resolution (Analyst)**

#### Step 6.1: Update Finding Status

**Prompt to AI Assistant:**

```
Update finding #7 (SQL Injection in login form):

Status: resolved
Resolution notes: "Implemented parameterized queries for all database calls. 
Deployed fix to production on 2025-11-05. Conducted regression testing."
Evidence: /storage/remediation/sql_injection_fix_validation.pdf

Request validation from auditor.
```

#### Step 6.2: Bulk Status Update

**Prompt to AI Assistant:**

```
Update all "Medium" severity findings that are past due:
- Change status from "open" to "in_progress"
- Add comment: "Remediation work initiated. Target completion within 30 days."
- Send notification to assigned analysts
```

---

### **Phase 7: Validation (Auditor - QA Review)**

Navigate to **QA Review** → **Findings Pending Validation**

**Prompt to AI Assistant:**

```
Validate all "resolved" findings for IM8-03 (Application Security):

For each finding:
1. Review resolution evidence
2. Verify remediation steps match best practices
3. Check if similar issues exist elsewhere
4. Validate retesting was performed

Auto-validate findings with complete evidence and successful retest results.
Flag findings needing manual validation.
```

---

### **Phase 8: Report Generation (Admin)**

#### Step 8.1: Executive Summary Report

**Prompt to AI Assistant:**

```
Generate an executive compliance report for assessment ID 1:

Include:
1. Overall compliance score (% of controls passed)
2. Compliance by IM8 domain area (10 sections)
3. Critical findings summary
4. Remediation progress (open vs resolved)
5. Risk heat map
6. Trend analysis (compared to previous quarter)
7. Recommendations for improvement

Format: PDF with charts and graphs
Audience: Senior management (non-technical)
```

#### Step 8.2: Technical Audit Report

**Prompt to AI Assistant:**

```
Generate detailed technical audit report for assessment ID 1:

Include:
1. Complete control testing results (all 30 controls)
2. Evidence inventory with verification status
3. Detailed findings list with CVSS scores
4. Gap analysis against IM8 requirements
5. Control effectiveness ratings
6. Audit trail of all review activities
7. Appendices with evidence samples

Format: PDF with technical details
Audience: Security team and auditors
```

#### Step 8.3: IM8 Compliance Certificate

**Prompt to AI Assistant:**

```
Generate IM8 compliance certificate if overall score >= 85%:

Include:
- Agency name
- Assessment period
- Overall compliance score
- Domain-level compliance scores
- Assessor details
- Approval signatures (digital)
- Valid until date (1 year)
```

---

## 🤖 Agentic AI Capabilities

### Autonomous Task Execution

The AI assistant can independently:

1. **Data Processing**
   - Parse CSV, JSON, XML, PDF files
   - Extract structured data from documents
   - Validate data formats and completeness

2. **Evidence Analysis**
   - Scan documents for required information
   - Verify compliance with control requirements
   - Identify gaps and missing evidence
   - Generate quality scores

3. **Control Mapping**
   - Map findings to IM8 controls
   - Suggest control improvements
   - Identify control overlaps
   - Recommend additional controls

4. **Risk Assessment**
   - Calculate CVSS scores
   - Prioritize findings by risk
   - Generate risk heat maps
   - Predict remediation effort

5. **Report Generation**
   - Create executive summaries
   - Generate technical reports
   - Produce compliance certificates
   - Export to multiple formats

6. **Workflow Orchestration**
   - Trigger notifications
   - Assign tasks to users
   - Track deadlines
   - Escalate overdue items

---

## 💬 Natural Language Prompts for Common Tasks

### Quick Upload Prompts

```
"Upload 10 access control policies for IM8-01"

"Import findings from last week's penetration test"

"Add evidence for network segmentation controls"

"Create assessment for 2026 Q1 compliance audit"
```

### Analysis Prompts

```
"Analyze all pending evidence and flag incomplete items"

"Show me controls with zero evidence"

"What are our top 5 compliance risks?"

"Compare this quarter's compliance vs last quarter"
```

### Reporting Prompts

```
"Generate executive summary for the board meeting"

"Create detailed audit report for CSA submission"

"Export all critical findings to Excel"

"Send compliance status update to all stakeholders"
```

### Workflow Prompts

```
"Assign all unassigned findings to available analysts"

"Send reminder to reviewers with pending evidence"

"Escalate overdue critical findings to management"

"Archive completed assessments from 2024"
```

---

## 📊 Multi-User Workflow Example

### Scenario: Quarterly IM8 Compliance Cycle

**Week 1-2: Planning (Admin)**
1. Create quarterly assessment
2. Assign controls to test
3. Allocate analysts and reviewers
4. Set deadlines and milestones

**Week 3-6: Evidence Collection (Analysts)**
1. Upload configuration files
2. Document control implementations
3. Collect audit logs
4. Screenshot security settings

**Week 7-8: Review (Auditors)**
1. Review submitted evidence
2. Approve/reject items
3. Request additional information
4. Document findings

**Week 9-10: Testing (Analysts)**
1. Perform control testing
2. Document test results
3. Create findings for gaps
4. Upload test evidence

**Week 11: Validation (Auditors)**
1. Validate resolved findings
2. Final evidence review
3. Approve for reporting

**Week 12: Reporting (Admin)**
1. Generate compliance report
2. Present to management
3. Submit to regulators
4. Archive assessment

**Ongoing: Remediation (Analysts)**
1. Fix identified issues
2. Upload remediation evidence
3. Request re-validation
4. Update control status

---

## 🎓 Best Practices

### 1. **Use Descriptive Titles**
```
✅ "Q4 2025 IM8 Access Control Assessment - Production Systems"
❌ "Assessment 1"
```

### 2. **Link Everything**
- Link findings to assessments
- Link evidence to controls
- Link controls to IM8 domains
- Link assessments to projects

### 3. **Leverage AI Analysis**
```
Always set "ai_analysis_requested": true for:
- Policy documents
- Configuration files
- Log files
- VAPT reports
```

### 4. **Use Natural Language**
```
✅ "Analyze all Windows Server configurations and check if they meet IM8-04 hardening requirements"
❌ Manually review 50 config files
```

### 5. **Automate Routine Tasks**
```
✅ "Send weekly compliance status report every Friday at 5pm"
✅ "Auto-escalate critical findings after 30 days"
✅ "Remind reviewers of pending evidence every 3 days"
```

---

## 📁 File Locations & Storage

### Azure Blob Storage Structure
```
/storage/
  ├── evidence/
  │   ├── 2025/
  │   │   ├── q1/
  │   │   ├── q2/
  │   │   ├── q3/
  │   │   └── q4/
  │   │       ├── access-control/
  │   │       ├── network-security/
  │   │       ├── data-protection/
  │   │       └── ...
  ├── assessments/
  │   ├── vapt_reports/
  │   ├── audit_reports/
  │   └── compliance_reports/
  ├── logs/
  │   ├── auth_logs/
  │   ├── admin_logs/
  │   └── security_logs/
  └── remediation/
      ├── fixes/
      ├── validation/
      └── retesting/
```

---

## 🔗 Quick Reference: Templates

### 1. Controls Upload
**File**: `templates/controls_upload_template.json`
**Use**: Bulk upload IM8 controls
**Prompt**: "Upload IM8 controls from this template with 30 controls covering all 10 domains"

### 2. Assessment Creation
**File**: `templates/assessment_template.json`
**Use**: Create new compliance assessment
**Prompt**: "Create Q1 2026 IM8 assessment using this template"

### 3. Findings Import
**File**: `templates/findings_upload_template.json`
**Use**: Bulk import VAPT/audit findings
**Prompt**: "Import findings from our VAPT report, map to IM8-03 controls"

### 4. Evidence Upload
**File**: `templates/evidence_upload_template.json`
**Use**: Upload evidence documents
**Prompt**: "Upload these 10 policy documents as evidence for IM8-01 controls"

---

## 🚀 Next Steps

1. **Seed IM8 Framework**
   ```powershell
   python -m api.scripts.seed_im8
   ```

2. **Create Test Users** (Analysts, Auditors, Viewers)
   ```powershell
   python -m api.scripts.add_users
   ```

3. **Start First Assessment**
   - Use AI Assistant with prompts above
   - Follow the 12-week workflow
   - Leverage agentic automation

4. **Configure Notifications**
   - Set up email/Teams integration
   - Configure escalation rules
   - Enable status reports

5. **Train Your Team**
   - Share this guide
   - Demo AI assistant capabilities
   - Establish maker-checker process

---

## 📞 Support

- **API Docs**: https://your-api.azurecontainerapps.io/docs
- **AI Assistant**: Click "AI Assistant" in sidebar
- **Agent Tasks**: Monitor at `/agent-tasks/`
- **System Status**: Check `/analytics/dashboard`

---

**Remember**: This is an agentic system. The AI can do most tasks autonomously. 
Just describe what you need in natural language, and the agent will execute! 🚀
