# 🚀 Quick Start: Agentic AI Compliance Assistant

## 🔐 Test Users (DO NOT CHANGE WITHOUT PERMISSION)

**Application URL**: https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io

| Username | Password | Full Name | Role | Agency | Use Case |
|----------|----------|-----------|------|--------|----------|
| **admin** | admin123 | System Administrator | Super Admin | Default | Full system access |
| **alice** | pass123 | Alice Tan | Analyst | HSA | Evidence upload & testing |
| **bob** | pass123 | Bob Lim | QA | HSA | Quality review |
| **charlie** | pass123 | Charlie Wong | Analyst | IRAS | Evidence upload |
| **diana** | pass123 | Diana Ng | QA | IRAS | Quality review |
| **edward** | pass123 | Edward Koh | Auditor | Audit | Evidence review |
| **fiona** | pass123 | Fiona Lee | Auditor | Audit | Evidence review |

**Quick Test Login:**
- **Analyst (Alice)**: `alice` / `pass123`
- **Auditor (Edward)**: `edward` / `pass123`
- **Admin**: `admin` / `admin123`

---

## 📋 5-Minute Demo Workflow

### 1️⃣ Create Assessment (30 seconds)
Navigate to: **Assessments** → **New Assessment**
```
Title: Q4 2025 IM8 Compliance Audit
Type: compliance_audit
Framework: IM8
Period: 2025-10-01 to 2025-12-31
```

### 2️⃣ Upload Controls via AI (2 minutes)
Navigate to: **AI Assistant**
```
Prompt: "Upload 30 IM8 controls covering all 10 domain areas. 
Include Access Control, Network Security, Data Protection, 
System Hardening, Secure Development, Logging & Monitoring, 
Vendor Management, Change Management, GRC, and Digital Services. 
Each with implementation guidance and evidence requirements. 
Link to project ID 1."
```

### 3️⃣ Create Findings via AI (1 minute)
```
Prompt: "Create 5 security findings for assessment ID 1:
1. SQL Injection - Critical (CVSS 9.8) - IM8-03
2. XSS vulnerability - High (CVSS 7.2) - IM8-03  
3. Weak passwords - Medium (CVSS 5.0) - IM8-01
4. Missing MFA - High (CVSS 6.5) - IM8-01
5. Outdated libraries - Medium (CVSS 4.8) - IM8-05
Assign to analyst ID 2, set due dates based on severity."
```

### 4️⃣ View Dashboard (30 seconds)
Navigate to: **Dashboard**
- See compliance score
- View findings by severity
- Check assessment progress
- Monitor overdue items

### 5️⃣ Generate Report via AI (1 minute)
Navigate to: **AI Assistant**
```
Prompt: "Generate executive compliance report for assessment ID 1 
with overall score, findings summary by severity, compliance by 
IM8 domain, and top 3 recommendations."
```

---

## 🎯 Common AI Prompts

### Data Upload
```
"Upload 10 access control policies"
"Import VAPT findings from CSV"
"Add evidence for network segmentation"
```

### Analysis
```
"Show controls with no evidence"
"What are our top 5 risks?"
"Analyze compliance gaps in IM8-01"
```

### Reporting
```
"Create executive summary"
"Export critical findings to Excel"
"Generate IM8 compliance certificate"
```

### Automation
```
"Assign unassigned findings to available analysts"
"Send reminder for pending evidence reviews"
"Escalate overdue critical findings"
```

---

## 🏛️ IM8 Framework (10 Domains)

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

## 🔄 Maker-Checker Workflow

### Analyst (Maker)
1. Upload evidence → status: "pending"
2. Document findings
3. Submit for review

### Auditor (Checker)  
1. Review evidence → approve/reject
2. Validate findings
3. Add review comments

### Status Flow
`pending` → `under_review` → `approved` / `rejected`

---

## 📁 Templates Location

- **Controls**: `templates/controls_upload_template.json`
- **Assessments**: `templates/assessment_template.json`
- **Findings**: `templates/findings_upload_template.json`
- **Evidence**: `templates/evidence_upload_template.json`

---

## 🤖 What Makes This "Agentic"?

The AI can **autonomously**:
- ✅ Parse and analyze documents
- ✅ Extract structured data
- ✅ Map controls to frameworks
- ✅ Calculate risk scores
- ✅ Generate reports
- ✅ Execute multi-step workflows
- ✅ Send notifications
- ✅ Validate compliance
- ✅ Track and escalate tasks

**Just describe what you need in natural language!**

---

## 📖 Full Documentation

- **Complete Guide**: `AGENTIC_WORKFLOW_GUIDE.md`
- **API Docs**: `/docs` endpoint
- **Templates**: `templates/` directory

---

## 🎓 Demo Script

Run this to seed IM8 framework:
```powershell
.\demo_im8_setup.ps1
```

---

## 💡 Pro Tips

1. **Be Specific**: "Upload 30 IM8 controls" > "Upload controls"
2. **Use IDs**: Reference assessment ID, control ID, user ID
3. **Natural Language**: Describe outcomes, not steps
4. **Leverage AI**: Let the agent do the heavy lifting
5. **Link Everything**: Connect findings→assessments→controls→IM8

---

**Need Help?** Ask the AI Assistant anything! 🤖
