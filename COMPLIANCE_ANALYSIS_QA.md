# Comprehensive Answers to Compliance Analysis Questions

## Question 1: Data Collection Before Background Worker Queries

### **Current Data Collection Methods:**

#### **A. Manual Evidence Upload (Primary Method)**
```
User Journey:
1. Navigate to Evidence page (/evidence)
2. Click "Upload Evidence" button
3. Fill form:
   - Select Control (dropdown from project)
   - Upload file (PDF, Word, Excel, screenshots, etc.)
   - Add title, description, evidence type
4. Submit → File saved to `/evidence_storage/` directory
5. Metadata stored in database:
   - control_id (which control this evidence supports)
   - agency_id (IMDA)
   - file_path, filename, mime_type
   - file_size, SHA-256 checksum
   - uploaded_by (user who uploaded)
   - uploaded_at (timestamp)
```

**Storage Location:**
```
/evidence_storage/
├── agency_1/
│   ├── control_1/
│   │   ├── access_control_policy.pdf
│   │   ├── user_access_matrix.xlsx
│   │   └── firewall_config.png
│   └── control_2/
│       └── incident_response_plan.docx
└── agency_2/  (IMDA)
    ├── control_10/
    │   └── network_diagram.pdf
    └── control_15/
        └── encryption_policy.docx
```

#### **B. Automated Evidence Fetching (Agent Task)**
```
User Journey:
1. Navigate to Agent Tasks page
2. Click "Create Task" → Select "Fetch Evidence"
3. Provide payload:
   {
     "control_id": 10,
     "sources": [
       {
         "type": "url",
         "url": "https://docs.imda.gov.sg/security-policy.pdf",
         "description": "IMDA Security Policy"
       },
       {
         "type": "local",
         "path": "/shared/policies/access_control.pdf",
         "description": "Access Control Policy"
       }
     ]
   }
4. Background worker:
   - Downloads files from URLs
   - Copies local files
   - Calculates SHA-256 checksums
   - Detects MIME types
   - Stores in evidence_storage/
   - Creates evidence records in database
```

#### **C. Control/Project Setup (Manual)**
```
User Journey:
1. Create Project: "IMDA IM8 Compliance 2025"
   - Name, description, status
   - Assigned to IMDA agency

2. Add Controls to Project:
   - Option 1: Manual creation
     * Navigate to Controls page
     * Click "Add Control"
     * Fill: name, description, status, type
   
   - Option 2: Bulk import from framework
     * Import IM8 controls from control_catalog
     * Maps external_id → project controls
     * Example: IM8-AC-1 → Control #10 in project

3. Update Control Status:
   - pending → in_progress → completed
   - Tracks implementation progress
```

#### **D. Database Pre-Population**
```sql
-- Control catalog (IM8 framework) pre-loaded:
INSERT INTO control_catalog (external_id, title, description, family, domain)
VALUES 
  ('IM8-AC-1', 'Access Control Policy', 'Establish access control policies...', 'IM8', 'Access Control'),
  ('IM8-AC-2', 'Account Management', 'Manage user accounts...', 'IM8', 'Access Control'),
  ...
  (133 total IM8 controls);

-- User manually creates project-specific controls:
INSERT INTO controls (project_id, name, status, external_id)
SELECT 1, cc.title, 'pending', cc.external_id
FROM control_catalog cc
WHERE cc.family = 'IM8';
```

---

### **Data Sources for Compliance Analysis:**

```
┌─────────────────────────────────────────┐
│     COMPLIANCE ANALYSIS INPUT DATA      │
└─────────────────────────────────────────┘
             ↓
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼────┐
│Database│      │File     │
│Tables  │      │Storage  │
└───┬────┘      └────┬────┘
    │                │
    ├─ projects      ├─ PDFs (policies, procedures)
    ├─ controls      ├─ Word docs (plans, checklists)
    ├─ evidence      ├─ Excel (access matrices, logs)
    ├─ control_catalog └─ Images (screenshots, diagrams)
    ├─ agencies
    └─ users
```

**When Analysis Task Runs:**
1. Queries database for control status, evidence metadata
2. Accesses file storage to read evidence content
3. Loads framework requirements from knowledge base
4. Uses RAG to analyze evidence quality

---

## Question 2: Tools the Compliance Task Uses

### **Tool Stack:**

#### **1. Database Query Tools (SQLAlchemy ORM)**
```python
# Queries database for project data
def get_project_controls(project_id: int, db: Session):
    return db.query(models.Control)\
             .filter(models.Control.project_id == project_id)\
             .all()

def get_control_evidence(control_id: int, db: Session):
    return db.query(models.Evidence)\
             .filter(models.Evidence.control_id == control_id)\
             .all()

def get_framework_requirements(framework: str, db: Session):
    return db.query(models.ControlCatalog)\
             .filter(models.ControlCatalog.family == framework)\
             .all()
```

#### **2. File Processing Tools**
```python
# PDF text extraction
import PyPDF2
def extract_pdf_text(file_path: str) -> str:
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

# Word document processing
import docx
def extract_docx_text(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Excel processing
import pandas as pd
def extract_excel_data(file_path: str) -> dict:
    df = pd.read_excel(file_path)
    return df.to_dict()
```

#### **3. RAG/AI Analysis Tools**
```python
# Vector search (Qdrant)
from api.src.rag.enhanced_embeddings import enhanced_embedding_service

async def search_similar_controls(query: str):
    return await enhanced_embedding_service.search(
        query=query,
        collection="im8_controls",
        limit=5
    )

# LLM analysis (Groq/Llama)
from api.src.rag.llm_service import llm_service

async def analyze_evidence_quality(evidence_text: str, control_req: str):
    prompt = f"""
    Analyze if this evidence satisfies the control requirement:
    
    Control Requirement: {control_req}
    Evidence Content: {evidence_text}
    
    Return: compliant (yes/no) and gaps found.
    """
    return await llm_service.generate_completion([
        {"role": "user", "content": prompt}
    ])
```

#### **4. Scoring/Calculation Tools**
```python
# Compliance score calculator
def calculate_compliance_score(controls: list, evidence: list) -> float:
    total_controls = len(controls)
    completed = sum(1 for c in controls if c.status == 'completed')
    
    # Factor in evidence quality
    evidence_score = 0
    for ctrl in controls:
        ctrl_evidence = [e for e in evidence if e.control_id == ctrl.id]
        if len(ctrl_evidence) >= ctrl.required_evidence_count:
            evidence_score += 1
    
    return (completed * 0.7 + evidence_score * 0.3) / total_controls * 100

# Gap identification
def identify_gaps(framework_controls: list, project_controls: list):
    implemented = {c.external_id for c in project_controls}
    required = {c.external_id for c in framework_controls}
    return required - implemented  # Set difference = missing controls
```

#### **5. Report Generation Tools** (To be implemented)
```python
# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_compliance_report(analysis_data: dict, output_path: str):
    pdf = canvas.Canvas(output_path, pagesize=letter)
    pdf.drawString(100, 750, f"Compliance Analysis Report")
    pdf.drawString(100, 730, f"Score: {analysis_data['score']}%")
    # ... add sections, charts, gap lists
    pdf.save()

# Word generation (python-docx)
from docx import Document

def generate_word_report(analysis_data: dict, output_path: str):
    doc = Document()
    doc.add_heading('Compliance Analysis Report', 0)
    doc.add_paragraph(f"Overall Score: {analysis_data['score']}%")
    # ... add tables, recommendations
    doc.save(output_path)
```

---

## Question 3: Which Agent Handles Compliance Task?

### **Agent Architecture:**

```
┌──────────────────────────────────────────────┐
│         IM8ComplianceAgent                   │
│  (Primary Agent - Agentic Reasoning)         │
│                                              │
│  Location: api/src/rag/im8_agent.py          │
│                                              │
│  Capabilities:                               │
│  ├─ 5-step reasoning process                 │
│  ├─ Singapore-specific context              │
│  ├─ IM8 framework knowledge                 │
│  ├─ Gap analysis with recommendations       │
│  └─ Multi-turn reasoning chains             │
└──────────────────────────────────────────────┘
                    ↓ uses
┌──────────────────────────────────────────────┐
│         HybridRAG                            │
│  (Supporting System)                         │
│                                              │
│  Location: api/src/rag/hybrid_rag.py         │
│                                              │
│  Capabilities:                               │
│  ├─ Vector search (Qdrant)                  │
│  ├─ BM25 keyword search                     │
│  ├─ Hybrid ranking                          │
│  └─ Context retrieval                       │
└──────────────────────────────────────────────┘
                    ↓ uses
┌──────────────────────────────────────────────┐
│         LLM Service (Groq/Llama)             │
│                                              │
│  Location: api/src/rag/llm_service.py        │
│                                              │
│  Model: llama-3.1-8b-instant                 │
│  Purpose: Text generation, analysis          │
└──────────────────────────────────────────────┘
```

### **Agent Workflow:**

```python
# api/src/rag/im8_agent.py
class IM8ComplianceAgent:
    async def analyze_compliance_query(self, query: str, context: dict):
        # STEP 1: Analyze requirements
        analysis = await self._analyze_requirements(query, context)
        
        # STEP 2: Plan assessment approach
        plan = await self._plan_assessment(query, analysis)
        
        # STEP 3: Execute assessment
        execution = await self._execute_assessment(query, plan)
        
        # STEP 4: Validate against regulations
        validation = await self._validate_against_regulations(execution)
        
        # STEP 5: Synthesize recommendations
        synthesis = await self._synthesize_recommendations(query, validation)
        
        return {
            "final_answer": synthesis.content,
            "confidence_score": synthesis.confidence,
            "compliance_gaps": self._identify_gaps(synthesis.sources),
            "next_steps": synthesis.next_actions
        }
```

### **Task Handler Integration:**

```python
# api/src/workers/task_handlers.py
async def handle_analyze_compliance_task(task_id, payload, db):
    """
    This handler will orchestrate the compliance analysis:
    
    1. Extract project_id from payload
    2. Query database for controls + evidence
    3. Call IM8ComplianceAgent.analyze_compliance_query()
    4. Process agent response
    5. Calculate scores
    6. Generate report
    7. Return results
    """
    
    project_id = payload.get("project_id")
    
    # Step 1: Collect data
    controls = db.query(models.Control)\
                 .filter(models.Control.project_id == project_id)\
                 .all()
    
    # Step 2: Build context for agent
    context = {
        "project_id": project_id,
        "total_controls": len(controls),
        "framework": payload.get("framework", "IM8"),
        "controls_data": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "evidence_count": len(c.evidence)
            }
            for c in controls
        ]
    }
    
    # Step 3: Call IM8 agent
    agent_result = await im8_agent.analyze_compliance_query(
        query=f"Analyze compliance for project {project_id}",
        context=context
    )
    
    # Step 4: Return results
    return {
        "compliance_score": agent_result["confidence_score"],
        "gaps": agent_result["compliance_gaps"],
        "recommendations": agent_result["next_steps"],
        "full_analysis": agent_result
    }
```

---

## Question 4: Starting Point of Compliance Task

### **Entry Points:**

#### **Option 1: Frontend UI (User-Initiated)**
```
User Action:
1. Navigate to http://localhost:3000/agent-tasks
2. Click "Create Task" button
3. Select task type: "Analyze Compliance"
4. Fill form:
   ┌─────────────────────────────────────┐
   │  Create Compliance Analysis Task    │
   ├─────────────────────────────────────┤
   │  Project: [IMDA IM8 Assessment ▼]   │
   │  Framework: [IM8 ▼]                 │
   │  Analysis Type: [Full ▼]            │
   │  Include Recommendations: [✓]       │
   │  Generate Report: [✓]               │
   │                                     │
   │  [Cancel]  [Create Task]            │
   └─────────────────────────────────────┘
5. Click "Create Task"
```

**Backend API Call:**
```javascript
// frontend/src/services/agentTasks.ts
const response = await api.post('/agent-tasks/', {
  task_type: 'analyze_compliance',
  title: 'IMDA IM8 Compliance Analysis',
  description: 'Full compliance assessment for IMDA',
  payload: {
    project_id: 1,
    framework: 'IM8',
    analysis_type: 'full',
    include_recommendations: true,
    generate_report: true
  }
});
```

#### **Option 2: API Direct Call (Programmatic)**
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "imda_ciso", "password": "SecurePass123!"}' \
  | jq -r '.access_token')

# Create analysis task
curl -X POST http://localhost:8000/agent-tasks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analyze_compliance",
    "title": "IMDA Q4 Compliance Check",
    "description": "Quarterly compliance assessment",
    "payload": {
      "project_id": 1,
      "framework": "IM8",
      "analysis_type": "quick"
    }
  }'
```

#### **Option 3: Scheduled/Automated**
```python
# Future enhancement: Scheduled tasks
# api/src/scheduler/compliance_scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', month='*/3')  # Every 3 months
async def quarterly_compliance_check():
    """Auto-create compliance analysis task quarterly"""
    
    # For each active project
    projects = db.query(models.Project)\
                 .filter(models.Project.status == 'active')\
                 .all()
    
    for project in projects:
        task = models.AgentTask(
            task_type='analyze_compliance',
            title=f'Q{quarter} Compliance Check - {project.name}',
            created_by=1,  # System user
            payload={
                'project_id': project.id,
                'framework': 'IM8',
                'analysis_type': 'full',
                'scheduled': True
            }
        )
        db.add(task)
    
    db.commit()
```

---

### **Task Lifecycle After Creation:**

```
1. Task Created (status: pending)
   ↓
2. Background Worker Polls Database (every 5 seconds)
   ↓
3. Worker Picks Up Task (status: pending → running)
   ↓
4. Handler Execution (handle_analyze_compliance_task)
   ├─ Progress: 10% - "Loading project data"
   ├─ Progress: 25% - "Mapping framework requirements"
   ├─ Progress: 50% - "Analyzing evidence"
   ├─ Progress: 75% - "Generating recommendations"
   └─ Progress: 100% - "Analysis complete"
   ↓
5. Task Completed (status: running → completed)
   ↓
6. Results Stored in task.result (JSONB)
   ↓
7. Report Generated (PDF saved to /reports/)
   ↓
8. User Notified (frontend shows completion)
```

---

## Question 5: Basis Document/Template for Analysis

### **Current Knowledge Base Documents:**

#### **A. IM8 Control Framework** (`api/src/rag/im8_knowledge_base.py`)
```python
IM8_CONTROLS = {
    "AC-1": {
        "title": "Access Control Policy and Procedures",
        "description": "Establish, document, and disseminate...",
        "category": "Policy",
        "domain": "Access Control",
        "singapore_context": "Whole-of-Government access control standards",
        "implementation_guidance": "Must align with Singapore Government security policies",
        "required_evidence": [
            "Access control policy document",
            "Access control procedures",
            "Policy approval records",
            "Policy review and update records"
        ],
        "testing_procedures": [
            "Verify policy exists and is approved",
            "Verify policy covers all required areas",
            "Verify policy is reviewed annually"
        ]
    },
    # ... 132 more controls
}
```

#### **B. Singapore Compliance Context**
```python
SINGAPORE_COMPLIANCE_CONTEXT = {
    "regulations": {
        "IM8": {
            "authority": "Cyber Security Agency of Singapore (CSA)",
            "applicability": "All Singapore Government agencies",
            "version": "Version 5.1 (2024)",
            "update_frequency": "Annual review required"
        },
        "PDPA": {
            "authority": "Personal Data Protection Commission (PDPC)",
            "applicability": "Organizations handling personal data"
        }
    },
    "government_initiatives": [
        "Smart Nation",
        "Digital Government Blueprint",
        "Government on Commercial Cloud (GCC)"
    ]
}
```

#### **C. Framework Mappings**
```python
IM8_FRAMEWORK_MAPPINGS = {
    "IM8_to_ISO27001": {
        "AC-1": ["A.5.1", "A.5.15"],  # IM8 AC-1 maps to ISO controls
        "AC-2": ["A.5.15", "A.5.18"]
    },
    "IM8_to_NIST": {
        "AC-1": ["AC-1"],  # IM8 aligned with NIST
        "AC-2": ["AC-2", "IA-2"]
    }
}
```

---

### **Proposed Analysis Template (To Be Created):**

```markdown
# COMPLIANCE ANALYSIS TEMPLATE

## SECTION 1: EXECUTIVE SUMMARY
- Agency: [IMDA]
- Framework: [IM8 v5.1]
- Assessment Date: [2025-11-02]
- Overall Score: [___%]
- Certification Status: [Ready/Not Ready]

## SECTION 2: SCOPE
- Project: [IMDA IM8 Compliance Assessment 2025]
- Systems Assessed: [List]
- Controls Assessed: [133 IM8 controls]
- Evidence Reviewed: [67 documents]

## SECTION 3: METHODOLOGY
1. Control implementation review
2. Evidence quality assessment
3. Gap identification
4. Risk scoring
5. Recommendation generation

## SECTION 4: CONTROL SUMMARY BY DOMAIN
### Access Control (AC) - 55% Compliant
- Total Controls: 15
- Implemented: 8
- In Progress: 4
- Not Started: 3

[Table of controls with status]

### Audit & Accountability (AU) - 70% Compliant
...

## SECTION 5: CRITICAL FINDINGS
### Finding 1: Missing Incident Response Plan (IR-1)
- **Severity**: Critical
- **Current State**: No documented plan
- **Required State**: Approved IR plan with procedures
- **Risk**: Slow incident response, regulatory non-compliance
- **Recommendation**: Create IR plan using CSA template

## SECTION 6: GAP ANALYSIS
[Detailed list of gaps by priority]

## SECTION 7: RECOMMENDATIONS
[AI-generated actionable steps]

## SECTION 8: REMEDIATION ROADMAP
Phase 1 (Immediate): [0-4 weeks]
Phase 2 (Short-term): [1-3 months]
Phase 3 (Medium-term): [3-6 months]

## SECTION 9: NEXT ASSESSMENT
Recommended Date: [2026-02-02]
```

### **Template Location (To Be Created):**
```
/reports/templates/
├── compliance_analysis_template.docx
├── compliance_analysis_template.html
└── compliance_analysis_template.json
```

---

## Question 6: Updating the Analyze Compliance Guide

### **Documentation Strategy:**

#### **Living Documents:**
```
/workspaces/qa_compliance_assistant/
├── ANALYZE_COMPLIANCE_GUIDE.md  ← Main guide (you're reading it)
├── docs/
│   ├── compliance/
│   │   ├── data_collection.md
│   │   ├── agent_architecture.md
│   │   ├── scoring_methodology.md
│   │   └── report_templates.md
│   └── api/
│       └── agent_tasks_api.md
```

#### **Version Control in Document:**
```markdown
# Analyze Compliance Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-02
**Status**: Living Document - Updated Continuously

## Change Log

### Version 1.1.0 (2025-11-15) - Planned
- [ ] Add multi-modal document analysis
- [ ] Add automated evidence fetching examples
- [ ] Add report generation implementation

### Version 1.0.0 (2025-11-02) - Current
- [x] Initial 7-step process documented
- [x] Data collection methods outlined
- [x] Agent architecture described
- [x] Tool stack defined
```

#### **Update Process:**
```
When to Update:
1. After implementing new features (e.g., report generation)
2. After adding new frameworks (ISO 27001, NIST)
3. After improving AI analysis capabilities
4. After user feedback/testing

How to Update:
1. Edit ANALYZE_COMPLIANCE_GUIDE.md
2. Update version number
3. Add to change log
4. Commit with message: "docs: update compliance guide - [feature]"
5. Tag release if major change
```

---

## Question 7: Multi-Modal Functionality

### **Current Capabilities:**

#### **Text-Based Processing ✅**
```python
# Currently supported
- PDF text extraction (PyPDF2)
- Word document processing (python-docx)
- Excel data extraction (pandas)
- Plain text files
- JSON/XML structured data
```

#### **Image Processing ❌ (Not Yet Implemented)**
```python
# Planned capabilities:
# 1. OCR for scanned documents
from PIL import Image
import pytesseract

def extract_text_from_image(image_path: str) -> str:
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# 2. Screenshot analysis
# 3. Network diagram interpretation
# 4. Chart/graph data extraction
```

#### **Vision LLM Integration ❌ (Future Enhancement)**
```python
# Potential: Use GPT-4 Vision or similar
async def analyze_screenshot_evidence(image_path: str, control_req: str):
    """
    Analyze screenshot to verify control implementation
    Example: Firewall configuration screenshot for SC-7
    """
    with open(image_path, 'rb') as image:
        response = await vision_llm.analyze(
            image=image,
            prompt=f"Does this screenshot show {control_req}?"
        )
    return response
```

---

### **Recommended Multi-Modal Approach:**

```
┌──────────────────────────────────────┐
│     EVIDENCE FILE RECEIVED            │
└──────────────────────────────────────┘
             ↓
    ┌────────┴────────┐
    │  MIME Type?     │
    └────────┬────────┘
             ↓
   ┌─────────┼─────────┐
   │         │         │
┌──▼──┐  ┌──▼──┐  ┌──▼──┐
│PDF  │  │Image│  │Word │
│Docs │  │Files│  │Docs │
└──┬──┘  └──┬──┘  └──┬──┘
   │         │         │
   ↓         ↓         ↓
┌──▼─────────▼─────────▼──┐
│   Extract Text/Data      │
│   - PyPDF2 (PDF)         │
│   - Tesseract OCR (Img)  │
│   - python-docx (Word)   │
└──────────┬───────────────┘
           ↓
    ┌──────▼──────┐
    │ Text        │
    │ Embedding   │
    └──────┬──────┘
           ↓
    ┌──────▼──────┐
    │ RAG/LLM     │
    │ Analysis    │
    └─────────────┘
```

---

## Question 8: AI Assistant Document Upload Intention

### **Current State:**

#### **RAG Assistant** (`/rag` page)
```typescript
// frontend/src/pages/RAGPage.tsx
// Currently: Text input only

<TextField
  multiline
  rows={4}
  placeholder="Ask a question about IM8 compliance..."
  value={query}
  onChange={(e) => setQuery(e.target.value)}
/>

// NO FILE UPLOAD CAPABILITY ❌
```

#### **Evidence Upload** (`/evidence` page)
```typescript
// frontend/src/pages/EvidencePage.tsx
// Has file upload ✅

<input
  type="file"
  accept=".pdf,.docx,.xlsx,.png,.jpg"
  onChange={handleFileSelect}
/>
```

---

### **Design Intent & Roadmap:**

#### **Why RAG Assistant Doesn't Allow Upload (Yet):**

**1. Different Use Cases:**
```
Evidence Upload:
- Purpose: Store compliance evidence
- Destination: Database (evidence table)
- Use: Permanent project documentation
- Access: Auditors, compliance teams

RAG Assistant:
- Purpose: Ask questions, get answers
- Current: Query pre-loaded knowledge base
- Future: Analyze uploaded docs on-the-fly
- Access: All users, quick analysis
```

**2. Planned Enhancement:**

```typescript
// Future: RAG Assistant with Document Upload

interface RAGQuery {
  query: string;
  context_documents?: File[];  // NEW
  search_type: 'hybrid' | 'uploaded_docs';  // NEW
}

// User workflow:
1. Upload policy document (not saved permanently)
2. Ask: "Does this policy meet IM8 AC-1 requirements?"
3. RAG analyzes uploaded doc + knowledge base
4. Returns: Yes/No + specific gaps
5. Document discarded after analysis (or cached temporarily)
```

---

### **Proposed Implementation:**

#### **Backend API Enhancement:**
```python
# api/src/routers/rag.py

@router.post("/ask-with-document")
async def ask_with_uploaded_document(
    query: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze uploaded document in context of query
    Document is NOT saved permanently
    """
    
    # Extract text from upload
    text_content = await extract_text_from_file(file)
    
    # Add to temporary context
    context = {
        "uploaded_document": text_content,
        "filename": file.filename,
        "query": query
    }
    
    # Analyze using RAG
    response = await hybrid_rag.ask_with_context(
        query=query,
        additional_context=text_content
    )
    
    return {
        "answer": response["answer"],
        "analyzed_document": file.filename,
        "sources": response["sources"]
    }
```

#### **Frontend Enhancement:**
```typescript
// frontend/src/pages/RAGPage.tsx

const [uploadedFile, setUploadedFile] = useState<File | null>(null);

<Box>
  <TextField
    multiline
    placeholder="Ask about IM8 compliance..."
    value={query}
    onChange={(e) => setQuery(e.target.value)}
  />
  
  {/* NEW: Optional document upload */}
  <Button
    component="label"
    startIcon={<UploadIcon />}
  >
    Upload Document for Analysis
    <input
      type="file"
      hidden
      accept=".pdf,.docx,.txt"
      onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
    />
  </Button>
  
  {uploadedFile && (
    <Chip
      label={uploadedFile.name}
      onDelete={() => setUploadedFile(null)}
    />
  )}
  
  <Button onClick={handleAskWithDocument}>
    Ask Question
  </Button>
</Box>
```

---

### **Use Cases for RAG Document Upload:**

```
Scenario 1: Pre-Check Policy Compliance
- User drafts access control policy
- Uploads to RAG Assistant
- Asks: "Does this meet IM8 AC-1?"
- Gets instant feedback BEFORE formal submission

Scenario 2: Compare Policies
- Upload current policy
- Ask: "How does this compare to IM8 best practices?"
- Get gap analysis without creating project

Scenario 3: Quick Evidence Validation
- Upload screenshot
- Ask: "Does this show proper firewall configuration?"
- Verify before adding to formal evidence

Scenario 4: Training/Learning
- Upload sample policy
- Ask: "Explain how this satisfies IM8 requirements"
- Learn compliance requirements
```

---

## Summary

### **Answers Recap:**

1. **Data Collection**: Manual upload + automated fetching + database queries
2. **Tools Used**: SQLAlchemy, PyPDF2, RAG/LLM, scoring algorithms
3. **Agent**: IM8ComplianceAgent (5-step reasoning) + HybridRAG + LLM
4. **Starting Point**: Frontend UI → API call → Background worker picks up
5. **Basis Document**: IM8 knowledge base + proposed analysis template
6. **Guide Updates**: Living document, version controlled, updated with features
7. **Multi-Modal**: Text ✅, Images planned, Vision LLM future
8. **RAG Upload Intent**: Planned feature for on-the-fly document analysis

---

**Next Steps:**
1. Implement `handle_analyze_compliance_task` fully
2. Add multi-modal processing (OCR, image analysis)
3. Create report templates
4. Add RAG document upload capability
5. Build compliance dashboard with trends

**This document will be updated as features are implemented.**
