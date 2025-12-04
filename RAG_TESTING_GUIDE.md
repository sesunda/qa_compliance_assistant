# RAG Testing Guide - Evidence & Control Search

## Overview
The RAG (Retrieval-Augmented Generation) system indexes evidence files and control catalog entries in Azure Search, making them searchable through natural language queries in the AI assistants.

## ✅ Current Status
- **Controls Indexed**: 43/44 controls from catalog
- **Evidence Indexed**: 0 (none uploaded yet)
- **System Status**: Healthy and ready

---

## Part 1: Testing Control Search (Already Indexed)

### Test Prompts for Control Search

Use these prompts in the **Compliance Analyst** or **Compliance Assistant** chat:

#### 1. Basic Control Search
```
Search the control catalog for access control requirements
```

Expected: Should return controls related to access control (AC family)

#### 2. Specific Control Family
```
Find all controls related to incident response
```

Expected: Should return IR (Incident Response) family controls

#### 3. Technical Implementation Search
```
What controls cover encryption and data protection?
```

Expected: Should return SC (System and Communications Protection) controls about encryption

#### 4. Compliance-Specific Search
```
Show me controls for audit logging and monitoring
```

Expected: Should return AU (Audit and Accountability) controls

#### 5. Multi-Factor Authentication
```
Find controls that require multi-factor authentication
```

Expected: Should return controls mentioning MFA or multi-factor authentication

#### 6. Risk Assessment Controls
```
What controls are there for risk assessment and management?
```

Expected: Should return RA (Risk Assessment) family controls

---

## Part 2: Testing Evidence Upload & Indexing

### Step-by-Step Evidence Upload Test

#### Test Scenario 1: Upload PDF Evidence

1. **Navigate to Evidence Upload**
   - Go to a control (e.g., IM-8: Information Spillage Response)
   - Click "Add Evidence" or "Upload Evidence"

2. **Upload Sample Files**
   
   **Option A: Create a test document**
   - Create a Word document named: `incident_response_plan_2025.docx`
   - Content:
     ```
     INCIDENT RESPONSE PLAN 2025
     
     1. INCIDENT DETECTION
     - 24/7 monitoring through SIEM system
     - Automated alerts for security events
     - Log correlation and analysis
     
     2. INCIDENT CLASSIFICATION
     - Severity levels: Critical, High, Medium, Low
     - Response time SLAs based on severity
     
     3. RESPONSE PROCEDURES
     - Containment strategies
     - Evidence preservation
     - Root cause analysis
     - Remediation steps
     
     4. COMMUNICATION PLAN
     - Internal notification procedures
     - External stakeholder communication
     - Regulatory reporting requirements
     
     5. POST-INCIDENT REVIEW
     - Lessons learned documentation
     - Process improvement recommendations
     - Control effectiveness assessment
     ```

   **Option B: Create a test PDF**
   - Create a PDF named: `access_control_policy.pdf`
   - Content:
     ```
     ACCESS CONTROL POLICY
     
     1. USER ACCESS MANAGEMENT
     - Role-based access control (RBAC)
     - Principle of least privilege
     - Periodic access reviews (quarterly)
     
     2. AUTHENTICATION REQUIREMENTS
     - Multi-factor authentication (MFA) for all users
     - Password complexity: 12+ characters
     - Password rotation: every 90 days
     
     3. PRIVILEGED ACCESS
     - Separate admin accounts required
     - Just-in-time access provisioning
     - All privileged actions logged and monitored
     
     4. ACCESS REVOCATION
     - Immediate termination of access upon employee separation
     - Transfer procedures for role changes
     - Automated deprovisioning workflows
     ```

3. **Fill Evidence Details**
   - Title: `Incident Response Plan 2025` or `Access Control Policy`
   - Description: `Comprehensive incident response procedures and escalation matrix` or `Organization-wide access control policy`
   - Evidence Type: `Policy` or `Procedure`

4. **Submit Evidence**
   - Click "Upload" or "Submit"
   - Wait for success message

5. **Verify Indexing (Background Process)**
   - Evidence is automatically indexed after upload
   - Indexing happens asynchronously
   - Check backend logs: `az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --tail 50`
   - Look for log messages: `✅ Indexed evidence X: [filename]`

---

## Part 3: Testing Evidence Search After Upload

### Wait 2-3 minutes after upload for indexing to complete

### Test Prompts for Evidence Search

#### 1. Search by Policy Content
```
Find evidence about our incident response procedures
```

Expected: Should return the uploaded incident response plan

#### 2. Search by Specific Terms
```
What evidence do we have about multi-factor authentication requirements?
```

Expected: Should return access control policy mentioning MFA

#### 3. Search Across Evidence
```
Show me all evidence related to access control and authentication
```

Expected: Should return relevant evidence documents

#### 4. Specific Procedure Search
```
What are our procedures for privileged access management?
```

Expected: Should find content about admin accounts and just-in-time access

#### 5. Compliance Evidence Search
```
Find evidence showing how we handle security incidents
```

Expected: Should return incident response related evidence

#### 6. Combined Control + Evidence Search
```
What controls and evidence do we have for IM-8 Information Spillage Response?
```

Expected: Should return both the IM-8 control details AND any uploaded evidence for that control

---

## Part 4: Testing RAG Integration in Chat

### Full Conversation Flow Test

#### Test 1: Analyze Control Coverage

```
User: What controls do we have for incident response?

Expected: Lists IR family controls from catalog

User: What evidence supports our incident response capabilities?

Expected: Returns uploaded incident response plan with relevant excerpts

User: Is our incident response plan sufficient for IM-8 compliance?

Expected: Analyzes control requirements against evidence content
```

#### Test 2: Gap Analysis

```
User: Review our access control evidence against AC-2 requirements

Expected: Retrieves AC-2 control + searches evidence, provides gap analysis

User: What's missing from our access control policy?

Expected: Identifies gaps between control requirements and evidence
```

#### Test 3: Evidence Recommendations

```
User: I need to upload evidence for AU-6 Audit Review. What should I include?

Expected: Retrieves AU-6 control, suggests what evidence would satisfy requirements

User: [After upload] Analyze if my audit logs meet AU-6 requirements

Expected: Searches uploaded evidence, compares to AU-6 requirements
```

---

## Part 5: Monitoring and Verification

### Check Indexing Status

#### Check Backend Logs
```powershell
az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --follow false --tail 100
```

Look for:
- `✅ Indexed evidence X: [filename]` - Successful indexing
- `📄 Processing evidence` - Indexing in progress  
- `❌ Failed to index` - Indexing errors

#### Check RAG Health
```powershell
$health = Invoke-RestMethod -Uri "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/api/v1/rag/health"
$health | ConvertTo-Json
```

Expected output:
```json
{
  "status": "healthy",
  "evidence_indexer": "ready",
  "control_indexer": "ready"
}
```

#### Manual Re-index (if needed)
```powershell
# Re-index all evidence
$result = Invoke-RestMethod -Uri "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/api/v1/rag/backfill/evidence" -Method Post -Headers @{"Content-Type"="application/json"} -TimeoutSec 300
$result | ConvertTo-Json

# Re-index all controls
$result = Invoke-RestMethod -Uri "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/api/v1/rag/backfill/controls" -Method Post -Headers @{"Content-Type"="application/json"} -TimeoutSec 300
$result | ConvertTo-Json
```

---

## Part 6: Advanced Testing Scenarios

### Scenario 1: Multi-Document Evidence Chain

1. Upload 3 related documents:
   - `network_security_policy.pdf`
   - `firewall_configuration_standards.docx`
   - `network_segmentation_diagram.pdf`

2. Test query:
```
Analyze our network security controls and show evidence from all related documents
```

Expected: Should retrieve and synthesize information from all 3 documents

### Scenario 2: Partial Match Testing

1. Upload evidence with specific technical details
2. Test queries with:
   - Exact technical terms (should match)
   - Similar/related terms (should match via semantic search)
   - Unrelated terms (should not match)

### Scenario 3: Version Tracking

1. Upload `security_policy_v1.pdf`
2. Later upload `security_policy_v2.pdf` for same control
3. Test query:
```
What's our latest security policy?
```

Expected: Should prioritize most recent upload

---

## Troubleshooting

### Evidence Not Appearing in Search

**Check 1: File Format**
- Supported: PDF (.pdf), Word (.docx, .doc), Text (.txt)
- Unsupported: Images, Excel, PowerPoint (not yet implemented)

**Check 2: File Content**
- File must have extractable text
- Scanned PDFs without OCR won't work
- Empty or corrupted files won't index

**Check 3: Indexing Delay**
- Wait 2-3 minutes after upload
- Check logs for indexing completion
- Try manual re-index if needed

**Check 4: Azure Search Configuration**
- Verify `AZURE_SEARCH_ENABLED=true`
- Check `AZURE_SEARCH_ENDPOINT` is set
- Verify `GITHUB_TOKEN` for embeddings is valid

### Rate Limiting

If you see rate limit errors:
```
Rate limit of 15 per 60s exceeded
```

**Solution**: 
- Wait 1 minute between large batch uploads
- GitHub Models API has 15 requests/minute limit
- Consider spacing out evidence uploads

---

## Expected Behavior Summary

### ✅ What Works Now
1. **Control Search**: All 43 controls indexed and searchable
2. **Evidence Upload**: Files uploaded and stored in Azure Blob
3. **Evidence Indexing**: Automatic background indexing on upload
4. **Semantic Search**: Natural language queries work across controls and evidence
5. **AI Integration**: Both assistants can search controls and evidence

### ⏳ What Happens Behind the Scenes
1. File uploaded → Saved to Azure Blob Storage
2. Document processor extracts text from PDF/Word/TXT
3. Text chunked into ~1000 character segments with overlap
4. Each chunk embedded using OpenAI text-embedding-3-small (via GitHub Models)
5. Chunks + embeddings stored in Azure Search
6. Search queries use semantic similarity to find relevant chunks
7. AI assistants use retrieved chunks for context-aware responses

### 🎯 Success Criteria
- [ ] Can search and retrieve control catalog entries
- [ ] Can upload evidence files successfully
- [ ] Evidence appears in search within 3 minutes
- [ ] AI assistants cite specific evidence in responses
- [ ] Gap analysis works (compares controls vs evidence)
- [ ] Multiple evidence documents can be searched together

---

## Quick Start Commands

### Upload Evidence via UI
1. Go to: https://[your-frontend-url]/projects/[project-id]/controls
2. Select a control
3. Click "Add Evidence"
4. Upload file + fill details
5. Submit

### Test Control Search in Chat
```
Open Compliance Assistant chat → Type:
"What controls cover access control and authentication?"
```

### Test Evidence Search After Upload
```
Wait 2-3 min → Type in chat:
"Show me evidence about [topic from your uploaded file]"
```

### Verify Everything Works
```powershell
# Health check
Invoke-RestMethod -Uri "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/api/v1/rag/health"

# Check logs
az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --tail 50 | Select-String "evidence|index"
```

---

## Next Steps

After successful testing:
1. Upload actual compliance evidence documents
2. Train users on effective search queries
3. Monitor indexing performance and adjust chunk sizes if needed
4. Consider implementing OCR for scanned documents
5. Add support for Excel/PowerPoint if needed

## Support

If issues persist:
- Check application logs for errors
- Verify Azure Search service is running
- Confirm GitHub token hasn't expired
- Test with simple text files first before complex PDFs
