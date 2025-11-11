# Evidence Workflow Implementation Progress

**Status**: Phase 1-2 Complete (Backend + Frontend Components) | Phase 3-4 Pending Integration
**Last Updated**: 2025-01-13
**Commits**: 2 commits (0fdf700, 3e525c8)

---

## ✅ PHASE 1: Backend AI Tools (COMPLETE)

### New AI Tools Added to `agentic_assistant.py`
1. **`request_evidence_upload`** - Creates pending evidence record for file upload
2. **`analyze_evidence`** (RAG) - Validates evidence against control requirements
3. **`suggest_related_controls`** (Graph RAG) - Suggests related controls using relationship graph
4. **`submit_evidence_for_review`** - Submits evidence for auditor approval

### Task Handlers Added to `task_handlers.py`
1. **`handle_request_evidence_upload_task`** - Creates evidence record, returns upload_id
2. **`handle_analyze_evidence_rag_task`** - RAG validation against CONTROL_REQUIREMENTS
3. **`handle_suggest_related_controls_task`** - Graph RAG using CONTROL_GRAPH
4. **`handle_submit_evidence_for_review_task`** - Updates status to 'under_review'

### Knowledge Bases Implemented
**CONTROL_REQUIREMENTS** (RAG):
- Control 1: Access Control Policy (IM8-01)
- Control 3: Incident Response Plan (IM8-06)
- Control 4: Data Backup Procedure (IM8-07)
- Control 5: Security Awareness Training (IM8-02)

Each includes:
- Title, domain, evidence types
- Requirements checklist
- Keywords for text analysis

**CONTROL_GRAPH** (Graph RAG):
- Relationship mapping: same_domain, related, upstream, downstream
- Supports control dependency analysis
- Enables evidence reuse suggestions

### RAG Analysis Features
- **Evidence Type Validation**: Checks if type matches accepted types
- **Keyword Coverage**: Analyzes title/description for relevant keywords (40% threshold)
- **Overall Scoring**: Weighted validation (60% pass threshold)
- **Recommendations**: Suggests improvements for failed checks

### Graph RAG Features
- **Multi-dimensional Relations**: Same domain, related objectives, dependencies
- **Relevance Scoring**: Base 50 + type match (30) + keyword overlap (20)
- **Smart Sorting**: Returns top N suggestions sorted by score

### RBAC Updates
- Added new tools to `ANALYST_ONLY_TOOLS` list (2 locations)
- Updated task_type_map with new tool mappings
- analyze_evidence routes to "analyze_evidence_rag" to avoid conflict

### API Endpoints (Already Exist!)
- ✅ `POST /evidence/{id}/submit-for-review`
- ✅ `POST /evidence/{id}/approve`
- ✅ `POST /evidence/{id}/reject`

---

## ✅ PHASE 2: Frontend Components (COMPLETE)

### Components Created

#### `EvidenceUploadWidget.tsx`
**Features:**
- Drag-and-drop file upload using react-dropzone
- File validation:
  * Types: PDF, DOCX, XLSX, PNG, JPG
  * Max size: 10MB
- Real-time upload progress bar
- Control metadata display (Control ID, title)
- Recommended evidence types display
- Success/error state handling
- Cancel upload functionality

**Props:**
```typescript
{
  evidenceId: number;
  uploadId: string;
  controlId: number;
  controlTitle: string;
  title: string;
  acceptedTypes?: string[];
  onUploadComplete: (evidence: any) => void;
  onCancel: () => void;
}
```

#### `EvidenceCard.tsx`
**Features:**
- Evidence metadata display (type, status, control, filename)
- Status badges (pending/under_review/approved/rejected) with colors
- RAG Analysis Results:
  * Compliance score bar
  * Validation checks with pass/fail icons
  * AI recommendations
- Graph RAG Suggestions:
  * Related controls list (top 3)
  * Relevance scores
  * Relationship reasons

**Props:**
```typescript
{
  evidence: {
    id, title, description, evidence_type, verification_status,
    control_id, original_filename, uploaded_at,
    analysis?: { overall_score, passed, validation_results, recommendations },
    suggestions?: [ { control_id, control_title, relevance_score, reason } ]
  };
  showAnalysis?: boolean;
}
```

### Dependencies Added
- `react-dropzone@14.2.3` - Drag-drop file upload

---

## 🚧 PHASE 3: Chat Integration (PENDING)

### What Needs to Be Done

#### 1. Update `AgenticChatPage.tsx`

**Add State Variables:**
```typescript
const [pendingUpload, setPendingUpload] = useState<{
  evidenceId: number;
  uploadId: string;
  controlId: number;
  controlTitle: string;
  title: string;
  acceptedTypes: string[];
} | null>(null);

const [evidenceAnalysis, setEvidenceAnalysis] = useState<any>(null);
const [relatedControls, setRelatedControls] = useState<any[]>([]);
```

**Detect AI Upload Request:**
In `handleSendMessage` response handler (after line 290):
```typescript
// Check if AI tool is request_evidence_upload
if (response.data.task_type === 'request_evidence_upload') {
  // Wait for task completion, then show upload widget
  const taskResult = await pollTaskCompletion(response.data.task_id);
  if (taskResult.status === 'success') {
    setPendingUpload({
      evidenceId: taskResult.result.evidence_id,
      uploadId: taskResult.result.upload_id,
      controlId: taskResult.result.control_id,
      controlTitle: taskResult.result.control_title,
      title: taskResult.result.instructions,
      acceptedTypes: taskResult.result.accepted_types
    });
  }
}

// Check if AI tool is analyze_evidence
if (response.data.task_type === 'analyze_evidence') {
  const taskResult = await pollTaskCompletion(response.data.task_id);
  if (taskResult.status === 'success') {
    setEvidenceAnalysis(taskResult.result.analysis);
  }
}

// Check if AI tool is suggest_related_controls
if (response.data.task_type === 'suggest_related_controls') {
  const taskResult = await pollTaskCompletion(response.data.task_id);
  if (taskResult.status === 'success') {
    setRelatedControls(taskResult.result.suggestions);
  }
}
```

**Render Upload Widget:**
After message rendering loop (around line 620):
```tsx
{/* Evidence Upload Widget */}
{pendingUpload && (
  <Box sx={{ mb: 2 }}>
    <EvidenceUploadWidget
      evidenceId={pendingUpload.evidenceId}
      uploadId={pendingUpload.uploadId}
      controlId={pendingUpload.controlId}
      controlTitle={pendingUpload.controlTitle}
      title={pendingUpload.title}
      acceptedTypes={pendingUpload.acceptedTypes}
      onUploadComplete={(evidence) => {
        setPendingUpload(null);
        // Trigger AI analysis automatically
        handleSendMessage(`Analyze evidence ${evidence.id}`);
      }}
      onCancel={() => setPendingUpload(null)}
    />
  </Box>
)}
```

**Render Evidence Cards:**
In message rendering (around line 510, after task_id display):
```tsx
{/* Evidence Analysis Results */}
{message.role === 'assistant' && evidenceAnalysis && (
  <Box sx={{ mt: 2 }}>
    <EvidenceCard
      evidence={{
        ...evidenceAnalysis,
        suggestions: relatedControls
      }}
      showAnalysis={true}
    />
  </Box>
)}
```

**Add Imports:**
```typescript
import EvidenceUploadWidget from '../components/EvidenceUploadWidget';
import EvidenceCard from '../components/EvidenceCard';
```

#### 2. Update ChatMessage Interface
Add evidence-related fields:
```typescript
interface ChatMessage {
  // ... existing fields
  evidence?: any;
  evidence_analysis?: any;
  related_controls?: any[];
}
```

---

## 🚧 PHASE 4: Evidence Page Enhancement (PENDING)

### What Needs to Be Done

#### 1. Update `EvidencePage.tsx`

**Add Status Filter:**
```tsx
const [statusFilter, setStatusFilter] = useState<string>('all');

<Select
  value={statusFilter}
  onChange={(e) => setStatusFilter(e.target.value)}
  size="small"
>
  <MenuItem value="all">All Status</MenuItem>
  <MenuItem value="pending">Pending</MenuItem>
  <MenuItem value="under_review">Under Review</MenuItem>
  <MenuItem value="approved">Approved</MenuItem>
  <MenuItem value="rejected">Rejected</MenuItem>
</Select>
```

**Add Columns:**
```tsx
{ field: 'verification_status', headerName: 'Status', width: 140,
  renderCell: (params) => {
    const statusConfig = {
      pending: { label: 'Pending', color: 'default' },
      under_review: { label: 'Under Review', color: 'warning' },
      approved: { label: 'Approved', color: 'success' },
      rejected: { label: 'Rejected', color: 'error' }
    };
    const config = statusConfig[params.value] || statusConfig.pending;
    return <Chip label={config.label} color={config.color} size="small" />;
  }
},
{ field: 'submitted_by', headerName: 'Submitted By', width: 150 },
{ field: 'reviewed_by', headerName: 'Reviewed By', width: 150 }
```

**Add Action Buttons (for Auditors):**
```tsx
{ field: 'actions', headerName: 'Actions', width: 200,
  renderCell: (params) => {
    if (currentUser.role !== 'auditor') return null;
    if (params.row.verification_status !== 'under_review') return null;
    
    return (
      <Stack direction="row" spacing={1}>
        <Button
          size="small"
          variant="contained"
          color="success"
          onClick={() => handleApprove(params.row.id)}
        >
          Approve
        </Button>
        <Button
          size="small"
          variant="contained"
          color="error"
          onClick={() => handleReject(params.row.id)}
        >
          Reject
        </Button>
      </Stack>
    );
  }
}
```

**Add Handler Functions:**
```typescript
const handleApprove = async (evidenceId: number) => {
  try {
    await api.post(`/evidence/${evidenceId}/approve`, {
      comments: 'Approved by auditor'
    });
    toast.success('Evidence approved');
    refetch();
  } catch (err) {
    toast.error('Failed to approve evidence');
  }
};

const handleReject = async (evidenceId: number) => {
  const comments = prompt('Reason for rejection:');
  if (!comments) return;
  
  try {
    await api.post(`/evidence/${evidenceId}/reject`, {
      comments
    });
    toast.success('Evidence rejected');
    refetch();
  } catch (err) {
    toast.error('Failed to reject evidence');
  }
};
```

---

## 📊 TESTING PLAN

### Backend Testing (via curl)

**1. Test request_evidence_upload:**
```bash
curl -X POST http://localhost:8000/api/agentic-chat/ \
  -H "Authorization: Bearer <analyst_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to upload evidence for control 1 - Access Control Policy document"}'

# Expected: AI creates evidence record, returns upload widget instructions
```

**2. Test analyze_evidence:**
```bash
# First upload evidence via /api/evidence/upload
# Then trigger analysis
curl -X POST http://localhost:8000/api/agentic-chat/ \
  -H "Authorization: Bearer <analyst_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze evidence 123 for compliance"}'

# Expected: RAG validation with score, validation results, recommendations
```

**3. Test suggest_related_controls:**
```bash
curl -X POST http://localhost:8000/api/agentic-chat/ \
  -H "Authorization: Bearer <analyst_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Suggest related controls for evidence 123"}'

# Expected: Graph RAG suggestions with relevance scores
```

**4. Test submit_evidence_for_review:**
```bash
curl -X POST http://localhost:8000/api/agentic-chat/ \
  -H "Authorization: Bearer <analyst_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Submit evidence 123 for auditor review"}'

# Expected: Status changes to 'under_review'
```

**5. Test Evidence Approval (API Direct):**
```bash
# Approve
curl -X POST http://localhost:8000/api/evidence/123/approve \
  -H "Authorization: Bearer <auditor_token>" \
  -H "Content-Type: application/json" \
  -d '{"comments": "Evidence meets requirements"}'

# Reject
curl -X POST http://localhost:8000/api/evidence/123/reject \
  -H "Authorization: Bearer <auditor_token>" \
  -H "Content-Type: application/json" \
  -d '{"comments": "Missing required documentation"}'
```

### Frontend Testing (Manual)

**1. Evidence Upload Flow:**
1. Login as Analyst
2. Go to Agentic Chat
3. Send: "Upload evidence for control 1"
4. Verify widget appears with drag-drop
5. Upload PDF file
6. Verify progress bar
7. Verify success message

**2. AI Analysis Flow:**
1. After upload, AI should auto-analyze
2. Verify EvidenceCard appears
3. Check score bar (should show percentage)
4. Check validation results (pass/fail icons)
5. Check recommendations

**3. Related Controls Flow:**
1. AI should suggest related controls
2. Verify related controls list appears
3. Check relevance scores
4. Verify top 3 suggestions only

**4. Evidence Page Flow:**
1. Login as Auditor
2. Go to Evidence page
3. Filter by "Under Review"
4. Click "Approve" or "Reject"
5. Verify status updates
6. Check "Reviewed By" column

---

## 🚀 DEPLOYMENT CHECKLIST

### Prerequisites
- [x] Backend tools implemented
- [x] Frontend components created
- [ ] Chat integration complete
- [ ] Evidence page updated
- [ ] End-to-end testing passed
- [ ] npm install (for react-dropzone)

### Deployment Commands
```bash
# Frontend
cd frontend
npm install
npm run build

# Deploy API
az containerapp up --name ca-api-qca-dev --source ./api

# Deploy Frontend  
az containerapp up --name ca-frontend-qca-dev --source ./frontend
```

---

## 📈 METRICS TO TRACK

### AI Performance
- Average RAG validation score
- Keyword coverage rates
- Graph RAG relevance accuracy
- False positive/negative rates

### User Adoption
- Evidence uploads per day
- AI-assisted vs manual uploads
- Evidence approval rate
- Average time to approval

### System Performance
- Evidence analysis latency
- Upload success rate
- API response times
- Task completion rates

---

## 🔧 KNOWN LIMITATIONS & FUTURE ENHANCEMENTS

### Current Limitations
1. **CONTROL_REQUIREMENTS**: Only 4 controls defined (need full NIST catalog)
2. **CONTROL_GRAPH**: Simplified relationships (needs domain expert input)
3. **Document Parsing**: Not implemented (basic MCP integration only)
4. **RAG Validation**: Simple keyword matching (upgrade to embedding search)

### Future Enhancements
1. **Advanced RAG**:
   - Vector embeddings for control requirements
   - Semantic similarity search
   - Document chunking and context retrieval

2. **Enhanced Graph RAG**:
   - Multi-hop relationship traversal
   - Control impact analysis
   - Evidence gap identification

3. **MCP Integration**:
   - PDF text extraction
   - DOCX content parsing
   - Table/image extraction
   - Metadata enrichment

4. **AI Intelligence**:
   - Auto-suggest evidence titles
   - Evidence quality scoring
   - Duplicate detection
   - Smart tagging

5. **Workflow Automation**:
   - Auto-submit high-scoring evidence
   - Batch approval for similar evidence
   - Evidence templates
   - Compliance reporting

---

## 📝 COMMIT HISTORY

### Commit 1: `0fdf700` - Backend AI Tools
```
feat: Add evidence AI tools with RAG and Graph RAG

- Add 4 new AI tools for evidence workflow
- Add CONTROL_REQUIREMENTS knowledge base (NIST top 4 controls)
- Add CONTROL_GRAPH relationship mapping for Graph RAG
- Update ANALYST_ONLY_TOOLS RBAC permissions
- RAG: Evidence type validation, keyword coverage, scoring
- Graph RAG: Multi-dimensional relations, relevance scoring
```

### Commit 2: `3e525c8` - Frontend Components
```
feat: Add evidence upload widget and card components

- Create EvidenceUploadWidget.tsx with drag-drop upload
- Create EvidenceCard.tsx for chat display
- Add react-dropzone@14.2.3 to dependencies
- File validation (PDF, DOCX, XLSX, PNG, JPG, max 10MB)
- RAG/Graph RAG results display
```

---

## 🎯 NEXT SESSION TASKS (Priority Order)

1. **Chat Integration** (~1-2 hours)
   - Update AgenticChatPage.tsx with evidence widget logic
   - Add evidence card rendering
   - Test upload → analyze → suggest flow

2. **Evidence Page Enhancement** (~1 hour)
   - Add status filter
   - Add approve/reject buttons
   - Test maker-checker workflow

3. **End-to-End Testing** (~1 hour)
   - Test full workflow as Analyst
   - Test approval as Auditor
   - Verify RBAC enforcement

4. **npm install & Build** (~15 minutes)
   ```bash
   cd frontend
   npm install
   npm run build
   ```

5. **Deployment** (~30 minutes)
   - Deploy API container
   - Deploy Frontend container
   - Smoke test production

6. **Documentation** (~30 minutes)
   - Update QUICK_START.md
   - Create EVIDENCE_WORKFLOW_GUIDE.md
   - Record demo video

**Total Estimated Time Remaining**: 4-5 hours

---

## 📞 SUPPORT & QUESTIONS

If you encounter issues:
1. Check error logs: `docker logs <container_id>`
2. Verify API health: `curl http://localhost:8000/health`
3. Check database: `psql -U postgres -d qa_compliance_db`
4. Review task status: Navigate to `/agent-tasks` page

**Common Issues:**
- **Upload fails**: Check file size (<10MB) and type
- **Analysis returns 0%**: Check CONTROL_REQUIREMENTS has control_id
- **No suggestions**: Check CONTROL_GRAPH has relationships
- **RBAC error**: Verify user role (analyst for upload, auditor for approve)

---

**Implementation Progress**: 50% Complete
**Estimated Completion**: 4-5 hours remaining
**Blocker Status**: None - all dependencies resolved
**Next Milestone**: Chat integration complete
