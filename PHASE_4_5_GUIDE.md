# Phase 4 & 5 Implementation Guide

## Overview

This document covers the implementation of Phase 4 (Business Logic Services) and Phase 5 (AI Integration & Automation) for the QCA Compliance Assistant.

## Phase 4: Business Logic Services

### 1. Assessment Service (`api/src/services/assessment_service.py`)

**Features:**
- **Progress Calculation**: Automatically calculates assessment progress based on controls tested and findings resolved
- **Status Management**: Auto-updates assessment status (open → in_progress → under_review → completed)
- **Metrics Generation**: Comprehensive metrics including control pass/fail rates, finding breakdowns
- **Validation**: Business rule validation for assessments
- **Risk Tracking**: Identifies at-risk assessments (approaching deadlines with low progress)

**Key Methods:**
```python
# Calculate progress (0-100%)
progress = AssessmentService.calculate_progress(assessment, db)

# Auto-update status based on progress
AssessmentService.auto_update_status(assessment, db)

# Get comprehensive metrics
metrics = AssessmentService.get_assessment_metrics(assessment, db)

# Check if overdue
is_overdue = AssessmentService.check_overdue(assessment)

# Get at-risk assessments
at_risk = AssessmentService.get_at_risk_assessments(db, days_threshold=7)
```

**API Endpoints:**
- `POST /services/assessment/{id}/update-progress` - Calculate and update progress
- `GET /services/assessment/{id}/metrics` - Get comprehensive metrics

---

### 2. Finding Service (`api/src/services/finding_service.py`)

**Features:**
- **Risk Scoring**: Calculates risk score (0-100) based on severity, CVSS, age, and business impact
- **SLA Tracking**: Tracks SLA compliance with configurable thresholds by severity
- **Priority Assignment**: Auto-assigns priority based on calculated risk
- **QA Validation**: Workflow for QA to validate finding resolutions
- **Escalation Detection**: Identifies findings needing escalation
- **Comment Management**: Track discussion and updates on findings

**SLA Configuration:**
```python
SLA_DAYS = {
    'critical': 7,
    'high': 30,
    'medium': 60,
    'low': 90,
    'info': 120
}
```

**Key Methods:**
```python
# Calculate risk score
risk_score = FindingService.calculate_risk_score(finding)

# Check SLA breach
sla_status = FindingService.check_sla_breach(finding)
# Returns: {breached, at_risk, days_overdue, days_remaining}

# Auto-assign priority
priority = FindingService.auto_assign_priority(finding)

# QA validation
approved = FindingService.validate_resolution(finding, validator_id, approved=True, comments="...", db)

# Get findings needing escalation
escalations = FindingService.get_findings_needing_escalation(db)

# Add comment
comment = FindingService.add_comment(finding_id, user_id, "Comment text", "update", db)
```

**API Endpoints:**
- `POST /services/finding/{id}/calculate-risk` - Calculate risk and SLA status
- `GET /services/findings/needing-escalation` - Get overdue critical/high findings
- `GET /services/findings/metrics` - Comprehensive finding metrics

---

### 3. Compliance Service (`api/src/services/compliance_service.py`)

**Features:**
- **Compliance Scoring**: Calculate overall compliance score (0-100%) based on control coverage, effectiveness, and finding resolution
- **Gap Analysis**: Identify missing/failing controls and generate recommendations
- **Framework Mapping**: Map controls between different compliance frameworks
- **Framework Statistics**: Aggregate statistics across all assessments for a framework

**Supported Frameworks:**
- NIST (200 controls)
- ISO27001 (114 controls)
- SOC2 (64 controls)
- FISMA (325 controls)

**Scoring Formula:**
```
Total Score = (Coverage × 0.4) + (Effectiveness × 0.4) + (Findings Resolution × 0.2)

Coverage = (Controls Implemented / Required Controls) × 100
Effectiveness = (Passed Controls / Tested Controls) × 100
Findings Resolution = (Resolved Critical Findings / Total Critical Findings) × 100
```

**Compliance Status:**
- **Compliant**: Score ≥ 90%
- **Substantially Compliant**: Score ≥ 70%
- **Partially Compliant**: Score ≥ 50%
- **Non-Compliant**: Score < 50%

**Key Methods:**
```python
# Calculate compliance score
score = ComplianceService.calculate_compliance_score(assessment, db)

# Perform gap analysis
gaps = ComplianceService.perform_gap_analysis(assessment, db)

# Map control to framework
mapped_id = ComplianceService.map_control_to_framework(control, "ISO27001", db)

# Get framework statistics
stats = ComplianceService.get_framework_statistics("NIST", db)
```

**API Endpoints:**
- `GET /services/assessment/{id}/compliance-score` - Get compliance score
- `GET /services/assessment/{id}/gap-analysis` - Perform gap analysis

---

## Phase 5: AI Integration & Automation

### 1. AI Finding Analyzer (`api/src/services/ai_finding_analyzer.py`)

**Features:**
- **AI-Powered Analysis**: Uses GitHub Models (Azure OpenAI) to analyze findings
- **Risk Assessment**: AI evaluates business impact and provides detailed risk analysis
- **Remediation Suggestions**: Generates detailed remediation steps beyond basic guidance
- **Root Cause Analysis**: Identifies potential root causes
- **Preventive Measures**: Suggests measures to prevent similar findings
- **Effort Estimation**: Estimates remediation effort in days
- **Batch Processing**: Analyze multiple findings efficiently
- **Priority Suggestions**: AI-recommended remediation priority order

**Configuration:**
```bash
# Environment variables required
GITHUB_TOKEN=your_github_token_here
AI_MODEL=gpt-4o  # Optional, defaults to gpt-4o
```

**Key Methods:**
```python
# Analyze single finding
analysis = ai_analyzer.analyze_finding(finding, control)

# Batch analyze
results = ai_analyzer.batch_analyze_findings(findings_list)

# Suggest priority order
priority = ai_analyzer.suggest_remediation_priority(findings_list)
```

**Response Format:**
```json
{
  "status": "success",
  "finding_id": 123,
  "analyzed_at": "2025-11-07T10:00:00",
  "ai_model": "gpt-4o",
  "analysis": {
    "risk_assessment": "...",
    "business_impact": "...",
    "detailed_remediation": "...",
    "root_causes": ["...", "..."],
    "preventive_measures": ["...", "..."],
    "estimated_effort_days": 14
  }
}
```

**API Endpoints:**
- `POST /services/ai/analyze-finding/{id}` - Analyze single finding
- `POST /services/ai/analyze-findings-batch` - Batch analyze (background task)
- `POST /services/ai/suggest-priority` - Get AI-suggested priority order

---

### 2. Report Generator (`api/src/services/report_generator.py`)

**Features:**
- **PDF Generation**: Professional PDF reports using ReportLab
- **Comprehensive Reports**: Full assessment reports with findings and controls
- **Executive Summaries**: Condensed reports for executives
- **Charts and Tables**: Visual representation of metrics
- **Customizable**: Choose to include/exclude sections
- **Automated Generation**: Background task processing

**Report Sections:**
1. Executive Summary (status, progress, compliance score)
2. Controls Summary (total, tested, passed, failed)
3. Findings Summary (by severity and status)
4. Detailed Findings (full list with descriptions)
5. Compliance Analysis (breakdown by category)

**Requirements:**
```bash
pip install reportlab>=4.0.0
```

**Key Methods:**
```python
# Generate full report
result = report_generator.generate_assessment_report(
    assessment,
    db,
    include_findings=True,
    include_controls=True
)

# Generate executive summary
result = report_generator.generate_executive_summary(assessment, db)
```

**API Endpoints:**
- `POST /services/reports/generate/{assessment_id}` - Generate report (background task)

---

### 3. Notification Service (`api/src/services/notification_service.py`)

**Features:**
- **Email Notifications**: SMTP or SendGrid support
- **Event-Based**: Trigger on assignment, SLA breach, resolution, completion
- **HTML Templates**: Professional email templates
- **Daily Digests**: Summary of pending items
- **Customizable**: Configure sender and frontend URL

**Notification Types:**
1. **Finding Assigned**: Notify analyst of new assignment
2. **SLA Breach**: Alert on overdue findings
3. **Finding Resolved**: Notify QA validator
4. **Assessment Completed**: Notify stakeholders
5. **Daily Digest**: Summary of open items

**Configuration:**
```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# OR SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key

# Common Configuration
NOTIFICATION_FROM_EMAIL=noreply@qca.com
FRONTEND_URL=https://your-frontend-url.com
```

**Key Methods:**
```python
# Send finding assignment notification
result = notification_service.notify_finding_assigned(finding, assignee)

# Send SLA breach alert
result = notification_service.notify_sla_breach(finding, assignee)

# Notify QA of resolved finding
result = notification_service.notify_finding_resolved(finding, resolver, validator)

# Notify stakeholders of completion
result = notification_service.notify_assessment_completed(assessment, stakeholders)

# Send daily digest
result = notification_service.send_daily_digest(user, summary)
```

**API Endpoints:**
- `POST /services/notifications/finding-assigned` - Send assignment notification
- `POST /services/notifications/sla-breach` - Send SLA breach alert

---

## Installation & Setup

### 1. Install Dependencies

```bash
cd /workspaces/qa_compliance_assistant
pip install -r api/requirements.txt
```

### 2. Configure Environment Variables

```bash
# AI Services (optional but recommended)
export GITHUB_TOKEN=ghp_your_github_token_here
export AI_MODEL=gpt-4o

# Email Services (choose one)
# Option 1: SMTP
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your_email
export SMTP_PASSWORD=your_password

# Option 2: SendGrid
export SENDGRID_API_KEY=your_sendgrid_key

# Common
export NOTIFICATION_FROM_EMAIL=noreply@qca.com
export FRONTEND_URL=https://your-frontend.com
```

### 3. Deploy to Azure

```bash
git add -A
git commit -m "Add Phase 4 & 5: Business Logic and AI Services"
git push origin main
```

---

## API Endpoints Summary

### Business Logic (Phase 4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/services/assessment/{id}/update-progress` | Calculate and update progress |
| GET | `/services/assessment/{id}/metrics` | Get comprehensive metrics |
| GET | `/services/assessment/{id}/compliance-score` | Calculate compliance score |
| GET | `/services/assessment/{id}/gap-analysis` | Perform gap analysis |
| POST | `/services/finding/{id}/calculate-risk` | Calculate risk score |
| GET | `/services/findings/needing-escalation` | Get overdue findings |
| GET | `/services/findings/metrics` | Get finding metrics |

### AI Services (Phase 5)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/services/ai/analyze-finding/{id}` | AI analyze single finding |
| POST | `/services/ai/analyze-findings-batch` | AI batch analyze |
| POST | `/services/ai/suggest-priority` | AI suggest priority order |
| POST | `/services/reports/generate/{id}` | Generate PDF report |
| POST | `/services/notifications/finding-assigned` | Send assignment email |
| POST | `/services/notifications/sla-breach` | Send SLA breach email |
| GET | `/services/health/services` | Check all services health |

---

## Usage Examples

### Example 1: Calculate Risk and Update Priority

```python
# API call
POST /services/finding/123/calculate-risk

# Response
{
  "finding_id": 123,
  "risk_score": 85,
  "recommended_priority": "critical",
  "current_priority": "high",
  "sla_status": {
    "breached": false,
    "at_risk": true,
    "days_remaining": 2
  }
}
```

### Example 2: Generate Assessment Report

```python
# API call
POST /services/reports/generate/456
{
  "include_findings": true,
  "include_controls": true
}

# Response
{
  "status": "generating",
  "assessment_id": 456,
  "message": "Report generation started in background"
}

# Report will be saved to /app/storage/reports/assessment_456_20251107_100000.pdf
# Email notification sent to analyst when complete
```

### Example 3: AI Analyze Finding

```python
# API call
POST /services/ai/analyze-finding/789

# Response
{
  "status": "success",
  "finding_id": 789,
  "ai_model": "gpt-4o",
  "analysis": {
    "risk_assessment": "High risk due to potential data exposure",
    "business_impact": "Could lead to regulatory fines and reputational damage",
    "detailed_remediation": [
      "1. Implement input validation...",
      "2. Add rate limiting...",
      "3. Enable logging..."
    ],
    "root_causes": [
      "Lack of input validation",
      "Missing security controls"
    ],
    "preventive_measures": [
      "Implement SAST in CI/CD",
      "Regular security training"
    ],
    "estimated_effort_days": 14
  }
}
```

---

## Monitoring & Health Checks

Check service availability:

```bash
GET /services/health/services

Response:
{
  "business_logic": {
    "assessment_service": "operational",
    "finding_service": "operational",
    "compliance_service": "operational"
  },
  "ai_services": {
    "ai_analyzer": "operational",
    "model": "gpt-4o"
  },
  "reporting": {
    "pdf_generator": "operational"
  },
  "notifications": {
    "email_service": "operational",
    "smtp": "enabled"
  }
}
```

---

## Testing

After deployment, test services:

```bash
# 1. Check service health
curl https://your-api-url/services/health/services

# 2. Update assessment progress
curl -X POST https://your-api-url/services/assessment/1/update-progress \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Calculate finding risk
curl -X POST https://your-api-url/services/finding/1/calculate-risk \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Get compliance score
curl https://your-api-url/services/assessment/1/compliance-score \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Notes

- **AI Features**: Require valid `GITHUB_TOKEN` with access to GitHub Models
- **PDF Generation**: Requires `reportlab` library (included in requirements.txt)
- **Email Notifications**: Require either SMTP or SendGrid configuration
- **Background Tasks**: Long-running operations (report generation, batch AI analysis) run as background tasks
- **Storage**: Reports saved to `/app/storage/reports/` directory
- **Fallbacks**: Services gracefully degrade if optional dependencies unavailable

---

## Next Steps

1. Deploy to Azure (in progress)
2. Configure environment variables for AI and email services
3. Test all endpoints with Postman or curl
4. Integrate with frontend dashboards
5. Set up scheduled tasks for:
   - Daily SLA breach checks
   - Daily digest emails
   - Automated risk recalculation
   - Weekly compliance score reports

---

## Support

For issues or questions:
- Check service health: `GET /services/health/services`
- Review logs: `az containerapp logs show --name ca-api-qca-dev`
- Verify environment variables are set correctly
