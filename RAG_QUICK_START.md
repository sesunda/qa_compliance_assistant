# 🚀 Quick RAG Testing Reference

## Immediate Test Commands

### 1. Check System Health ✅
```powershell
Invoke-RestMethod -Uri "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/api/v1/rag/health"
```

### 2. Test Control Search (Ready Now!) 🔍

**Open Compliance Assistant Chat and try these:**

```
What controls cover access control requirements?
```

```
Find all incident response controls
```

```
Show me controls related to audit logging
```

### 3. Upload Evidence 📤

**Use the sample files in `/sample_evidence/`:**
- `incident_response_plan_2025.txt` - Upload to IM-8 control
- `access_control_policy.txt` - Upload to AC-2 or AC-3 control

**Steps:**
1. Navigate to a control in UI
2. Click "Add Evidence"
3. Upload one of the sample files
4. Fill in details and submit

### 4. Test Evidence Search (After Upload) 🔎

**Wait 2-3 minutes after upload, then try:**

```
Find evidence about incident response procedures
```

```
What evidence do we have for multi-factor authentication?
```

```
Show me our access control policies
```

### 5. Combined Test 🎯

```
Analyze IM-8 control requirements and show related evidence
```

```
What controls and evidence do we have for access control?
```

## Expected Results

- ✅ **43/44 controls** are searchable now
- ✅ Evidence will be searchable **2-3 min after upload**
- ✅ AI assistants will **cite specific sections** from evidence
- ✅ Semantic search understands **related terms** (e.g., "MFA" finds "multi-factor authentication")

## Troubleshooting

### Evidence not appearing?
```powershell
# Check logs
az containerapp logs show --name ca-api-qca-dev --resource-group rg-qca-dev --tail 50 | Select-String "evidence"

# Re-index if needed
Invoke-RestMethod -Uri "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/api/v1/rag/backfill/evidence" -Method Post -Headers @{"Content-Type"="application/json"} -TimeoutSec 300
```

## Key Files

- **Full Testing Guide**: `RAG_TESTING_GUIDE.md`
- **Sample Evidence**: `sample_evidence/*.txt`
- **Backend Logs**: Check Azure Container Apps logs

---
**Status**: ✅ RAG system deployed and 43 controls indexed!
**Next**: Upload sample evidence and test search
