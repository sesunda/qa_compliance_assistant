# Evidence-Control Mapping Architecture

## Overview

The QCA system uses an intelligent evidence-control mapping architecture that automatically links uploaded evidence to the appropriate security controls based on natural language understanding.

## Architecture Components

### 1. Control Catalog vs. Controls

The system maintains two separate control tables:

- **`control_catalog`**: Framework control templates (generic, reusable controls from frameworks like IM8, ISO27001)
- **`controls`**: Project-specific control instances (active controls assigned to projects)

```
control_catalog (3 framework templates)
    ↓ (seeded via seed_controls.py)
controls (4 project controls)
    ↑ (referenced by)
evidence (10+ evidence records)
```

### 2. Evidence Storage

Evidence records are stored in the `evidence` table with these key fields:

```sql
CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    control_id INTEGER REFERENCES controls(id),  -- Links to specific control
    title VARCHAR(512),
    description TEXT,
    file_path VARCHAR(1024),
    checksum VARCHAR(64),  -- SHA-256 for integrity
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    ...
);
```

## How Evidence Maps to Controls

### Automatic Mapping Process

When a user uploads evidence via the AI Assistant:

1. **Intent Detection**: System detects `upload_evidence` intent
2. **Control Extraction**: AI extracts which control the evidence relates to using:
   - **Explicit ID**: "Upload evidence for control 3"
   - **Keyword Matching**: "Evidence for MFA" → matches "Enforce MFA for privileged accounts"
   - **Semantic Matching**: "Network security document" → matches "Network segmentation for sensitive systems"

3. **Evidence Storage**: MCP `fetch_evidence` tool stores the file with:
   - SHA-256 checksum for integrity
   - Link to matched `control_id`
   - Metadata (title, description, upload time)

4. **Verification**: Evidence starts as `verified=FALSE` until reviewed

### Intelligent Control Matching

The `AITaskOrchestrator` uses multiple strategies to match evidence to controls:

```python
# Example user inputs and their mappings:
"Upload MFA policy document"           → control_id=4 (Enforce MFA for privileged accounts)
"Evidence for network segmentation"    → control_id=2 (Network segmentation for sensitive systems)
"Encryption configuration file"        → control_id=3 (Encrypt data at rest)
"Upload evidence for control 2"        → control_id=2 (explicit ID)
```

**Matching Algorithm**:
1. Check for explicit control_id in message
2. Match keywords in message to control names
3. Use semantic keyword groups (e.g., "mfa" → "multi-factor authentication")
4. Default to control_id=1 if no match found

## Seeding Controls

### From Control Catalog

Use the `seed_controls.py` script to create project controls from the catalog:

```bash
docker exec qca_api python -m api.scripts.seed_controls
```

This creates control instances for a project (default: project_id=1) from the `control_catalog` templates.

### Current Controls (Project 1)

| ID | Name | Description | Type |
|----|------|-------------|------|
| 1 | Test Control | Test Control Description | security |
| 2 | Network segmentation for sensitive systems | - | - |
| 3 | Encrypt data at rest | - | - |
| 4 | Enforce MFA for privileged accounts | - | - |

## API Endpoints

### Get All Controls
```bash
GET /controls/
Authorization: Bearer <token>
```

Returns all active controls for the current project.

### Get Control Evidence
```bash
GET /controls/{control_id}/evidence
Authorization: Bearer <token>
```

Returns all evidence linked to a specific control.

### Upload Evidence (via AI Assistant)
```bash
POST /rag/ask-with-file
Content-Type: multipart/form-data

query: "Upload evidence for MFA"
file: <document>
enable_task_execution: true
```

The AI will:
1. Detect `upload_evidence` intent
2. Extract control from query ("MFA" → control_id=4)
3. Create agent task with `fetch_evidence` task_type
4. Store file with checksum and link to control

## Example Workflows

### Workflow 1: Upload Evidence for Specific Control

**User**: "I'm uploading an evidence document for the MFA policy"

**System**:
1. ✅ Detects intent: `upload_evidence`
2. ✅ Matches control: "Enforce MFA for privileged accounts" (ID: 4)
3. ✅ Creates task: Agent Task #35 (fetch_evidence)
4. ✅ Stores file: `/app/storage/evidence/<filename>`
5. ✅ Calculates checksum: SHA-256 hash
6. ✅ Creates evidence record: Links to control_id=4

### Workflow 2: Analyze Compliance

**User**: "Check our compliance status for IM8"

**System**:
1. ✅ Detects intent: `analyze_compliance`
2. ✅ Creates task: Agent Task #36 (analyze_compliance)
3. ✅ Scans all controls and their evidence
4. ✅ Generates compliance score (e.g., 80%)
5. ✅ Identifies gaps (controls without evidence)
6. ✅ Provides recommendations

### Workflow 3: View Controls with Evidence

**User**: Navigates to Controls page

**System**:
1. ✅ Fetches all controls via `/controls/` endpoint
2. ✅ Displays statistics:
   - Total Controls: 4
   - Implemented: 3
   - Partial: 1
   - Not Implemented: 0
3. ✅ Shows each control with:
   - Implementation status
   - Evidence count
   - Last updated timestamp

## Database Queries

### Find Evidence for a Control
```sql
SELECT e.id, e.title, e.file_path, e.verified, e.created_at
FROM evidence e
WHERE e.control_id = 4
ORDER BY e.created_at DESC;
```

### Find Controls Without Evidence
```sql
SELECT c.id, c.name
FROM controls c
LEFT JOIN evidence e ON e.control_id = c.id
WHERE e.id IS NULL
  AND c.status = 'active';
```

### Evidence-Control Summary
```sql
SELECT 
    c.name AS control_name,
    COUNT(e.id) AS evidence_count,
    SUM(CASE WHEN e.verified THEN 1 ELSE 0 END) AS verified_count
FROM controls c
LEFT JOIN evidence e ON e.control_id = c.id
WHERE c.status = 'active'
GROUP BY c.id, c.name
ORDER BY c.id;
```

## Key Files

- **`/api/src/services/ai_task_orchestrator.py`**: Intent detection and control matching
- **`/mcp_server/src/mcp_tools/evidence_fetcher.py`**: Evidence storage with checksums
- **`/api/scripts/seed_controls.py`**: Control seeding from catalog
- **`/api/src/models.py`**: Control and Evidence database models

## Future Enhancements

1. **ML-Based Matching**: Use NLP embeddings for semantic control matching
2. **Auto-Control Creation**: Create controls on-the-fly when new control types are mentioned
3. **Evidence Tagging**: Tag evidence with multiple controls (many-to-many)
4. **Confidence Scores**: Show matching confidence when AI maps evidence to controls
5. **Bulk Upload**: Support uploading multiple evidence files at once
6. **Evidence Verification Workflow**: Approval process for evidence verification

## Troubleshooting

### Issue: All evidence maps to control_id=1

**Cause**: User message doesn't contain control keywords, system uses default

**Solution**: 
- Include control-specific keywords in upload message
- Explicitly mention control ID: "evidence for control 3"
- Use descriptive terms: "MFA", "encryption", "network segmentation"

### Issue: Controls page is empty

**Cause**: Controls not seeded from catalog

**Solution**:
```bash
docker exec qca_api python -m api.scripts.seed_controls
```

### Issue: React Query shows stale data

**Fix**: Updated React Query with `refetchOnMount: true` in `ControlsPage.tsx`

## Summary

**Yes, evidence and controls map automatically!** The system uses:
- 🎯 **Intelligent keyword matching** to detect which control evidence relates to
- 🔐 **SHA-256 checksums** for evidence integrity verification
- 📊 **Compliance scoring** based on control-evidence relationships
- 🤖 **AI-driven orchestration** to create and link evidence without manual intervention

The architecture ensures evidence is always linked to specific controls, enabling accurate compliance reporting and gap analysis.
