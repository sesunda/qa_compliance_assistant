# 🤖 Agentic AI System - Setup & Configuration Guide

## ✅ What We Just Built

Your compliance assistant now has **full agentic AI capabilities**! The system can autonomously:

1. **Understand Natural Language** - Parse user prompts like "Upload 30 IM8 controls"
2. **Generate Controls** - Create complete control definitions with implementation guidance
3. **Create Findings** - Parse VAPT reports and generate structured findings
4. **Analyze Evidence** - AI-powered document analysis against control requirements
5. **Generate Reports** - Auto-create executive and technical compliance reports
6. **Execute Multi-Step Workflows** - Orchestrate complex compliance tasks autonomously

---

## 🔧 Configuration Required

### Step 1: Set Up Azure OpenAI (Recommended) or OpenAI

You need to configure LLM credentials for the AI to work. Choose one option:

#### **Option A: Azure OpenAI (Recommended for Enterprise)**

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Copy the **Endpoint** and **API Key**
4. Set these environment variables in your Azure Container App:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_MODEL=gpt-4  # or gpt-35-turbo
```

#### **Option B: OpenAI (Simpler Setup)**

1. Get an API key from [OpenAI](https://platform.openai.com)
2. Set this environment variable:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### Step 2: Add Environment Variables to Azure

1. **Go to Azure Portal** → **Container Apps** → Your API app
2. **Go to Settings** → **Environment variables**
3. **Add the variables** from Option A or B above
4. **Save** and **Restart** the container

---

## 🚀 How to Use the Agentic AI

### Access the Interface

1. **Login** to your application
2. **Click "Agentic AI"** in the sidebar (new menu item)
3. **Start chatting** with natural language!

### Example Prompts

#### 1️⃣ **Generate IM8 Controls**

```
Upload 30 IM8 controls covering all 10 domain areas (Access Control, 
Network Security, Data Protection, System Hardening, Secure Development, 
Logging & Monitoring, Vendor Management, Change Management, GRC, and 
Digital Services). Include implementation guidance and evidence requirements.
```

**What Happens:**
- AI parses your intent
- Creates agent task `create_controls`
- LLM generates 30 detailed controls
- Saves to database linked to your agency
- Returns task ID for tracking

#### 2️⃣ **Create Security Findings**

```
Create security findings from our penetration test:

Critical:
1. SQL Injection in login form (CVSS 9.8)
2. Stored XSS in comment field (CVSS 7.2)

High:
3. Missing security headers (CVSS 6.5)
4. Weak password policy (CVSS 6.1)

Medium:
5. Information disclosure (CVSS 5.3)

Map to IM8-03 Application Security controls and set due dates.
```

**What Happens:**
- AI extracts finding details
- Maps to IM8 domains
- Creates structured records
- Assigns due dates based on severity
- Links to assessment

#### 3️⃣ **Analyze Evidence**

```
Analyze evidence items 1, 2, and 3 for control 5. Check if they meet 
all requirements and flag any gaps.
```

**What Happens:**
- AI retrieves control requirements
- Analyzes evidence content
- Validates completeness
- Identifies gaps
- Provides recommendations

#### 4️⃣ **Generate Compliance Report**

```
Generate an executive compliance report for assessment 1 including:
- Overall compliance score
- Findings by severity
- Recommendations

Make it suitable for senior management.
```

**What Happens:**
- AI gathers assessment data
- Aggregates metrics
- Generates formatted report
- Returns markdown content
- Can be exported to PDF

---

## 📊 Monitoring Agent Tasks

1. **Go to "Agent Tasks"** page
2. **See all tasks** created by the AI
3. **Track progress** in real-time
4. **View results** when complete

Task statuses:
- **Pending** - Waiting to start
- **Running** - In progress (shows %)
- **Completed** - Done ✓
- **Failed** - Error occurred ✗

---

## 🎯 Integration with Existing UI

The agentic system **complements** the existing UI. You can:

### **Agentic Approach** (New!)
Use natural language to create bulk data:
```
"Upload 30 controls"
"Create 5 findings"
"Generate report"
```

### **Manual Approach** (Existing)
Use the UI forms:
- **Assessments** → **New Assessment** → Fill form
- **Controls** → **Map Control** → Fill form
- **Findings** → **New Finding** → Fill form

**Best Practice**: Use **agentic for bulk operations**, **manual for individual items**.

---

## 🔒 Security & Access Control

- **Role-based**: Only authorized users can create tasks
- **Agency isolation**: All generated data is scoped to user's agency
- **Audit trail**: All agent actions are logged with user ID
- **Rate limiting**: Prevent abuse of LLM API

---

## 💰 Cost Considerations

### OpenAI/Azure OpenAI Pricing

**Typical costs per operation:**
- Generate 30 controls: ~$0.10 - $0.20 (depends on model)
- Create 5 findings: ~$0.05 - $0.10
- Analyze evidence: ~$0.05 per item
- Generate report: ~$0.10 - $0.15

**Recommended models:**
- **GPT-4**: Best quality, higher cost (~$0.03/1K tokens)
- **GPT-3.5-Turbo**: Good quality, lower cost (~$0.002/1K tokens)

**Pro tip**: Use GPT-4 for complex tasks (report generation), GPT-3.5 for simple tasks (finding creation).

---

## 🧪 Testing the System

### Quick Test Workflow

1. **Navigate to "Agentic AI"**
2. **Send this prompt**:
   ```
   Upload 5 IM8 controls for Access Control domain
   ```
3. **Check "Agent Tasks"** page - you should see task running
4. **Go to "Controls"** page - you should see 5 new controls
5. **Success!** 🎉

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "AI service not configured" | Add AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY env vars |
| Task stays "pending" | Check worker logs, restart container |
| Empty response | Check API logs for LLM errors |
| 500 error | Verify database schema is up-to-date |

---

## 🔄 Architecture Overview

```
┌──────────────┐
│   User UI    │  "Upload 30 controls"
└──────┬───────┘
       │
       v
┌──────────────┐
│ Agentic Chat │  POST /agentic-chat/
│    API       │  - Parse intent
└──────┬───────┘  - Create agent task
       │
       v
┌──────────────┐
│  Task Queue  │  AgentTask record
└──────┬───────┘  status: pending
       │
       v
┌──────────────┐
│ Task Worker  │  Background worker picks up task
└──────┬───────┘  Calls task handler
       │
       v
┌──────────────┐
│ Task Handler │  create_controls_task()
│ (Agent)      │  - Calls LLM service
└──────┬───────┘  - Generates controls
       │          - Saves to database
       │          - Updates progress
       v
┌──────────────┐
│ LLM Service  │  Azure OpenAI / OpenAI
│              │  - Generate structured data
└──────┬───────┘  - Parse natural language
       │
       v
┌──────────────┐
│  Database    │  Saves: controls, findings,
│              │  evidence analysis, reports
└──────────────┘
```

---

## 📝 API Endpoints

### Agentic Chat

**POST** `/agentic-chat/`
```json
{
  "message": "Upload 30 IM8 controls"
}
```

**Response:**
```json
{
  "response": "✅ I'll generate 30 IM8 controls...",
  "task_created": true,
  "task_id": 123,
  "task_type": "create_controls"
}
```

### Capabilities

**GET** `/agentic-chat/capabilities`

Returns list of available agent actions and example prompts.

---

## 🎓 Advanced Usage

### Custom Frameworks

The system supports multiple frameworks:
```
"Generate 20 NIST 800-53 controls"
"Create 15 ISO27001 controls"
"Upload 30 IM8 controls"
```

### Batch Operations

```
"Create 3 assessments:
1. Q4 2025 IM8 Audit
2. Penetration Test 2025
3. SOC2 Type II Assessment"
```

### Conditional Logic

```
"If assessment 1 has more than 10 critical findings, 
generate an executive summary report"
```

### Multi-Step Workflows

```
"First upload 30 IM8 controls, then create an assessment, 
then link all controls to that assessment"
```

---

## 🌟 Next Steps

1. **Set up Azure OpenAI** (see Step 1 above)
2. **Test with simple prompt** ("Upload 5 controls")
3. **Try each agent capability** (controls, findings, evidence, reports)
4. **Train your team** on natural language prompts
5. **Integrate into daily workflow**

---

## 🆘 Support

- **Check task status**: Agent Tasks page
- **View API logs**: Azure Container App logs
- **LLM errors**: Check AZURE_OPENAI_ENDPOINT/OPENAI_API_KEY
- **Worker not running**: Restart API container

---

## 📊 Success Metrics

Track your automation impact:

- **Time saved**: Compare manual vs. agentic approach
- **Tasks automated**: Count agent tasks completed
- **Data quality**: Validate AI-generated controls/findings
- **User adoption**: Monitor agentic chat usage

---

**Your compliance assistant is now truly agentic! 🚀**

Just set up the LLM credentials and start automating your compliance workflows!
