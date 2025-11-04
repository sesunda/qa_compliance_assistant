# MCP Integration Testing & Demonstration Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-02  
**Status:** 🧪 Testing Ready

---

## Overview

This guide explains how to test and demonstrate the MCP (Model Context Protocol) integration in the QCA Compliance Assistant system.

### Architecture Summary

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Frontend   │ ──HTTP─→│ FastAPI      │ ──MCP──→│ MCP Server  │
│  (React)    │         │  Backend     │ Protocol│  (Tools)    │
└─────────────┘         └──────────────┘         └─────────────┘
                             │                         │
                             │ Agent orchestrates      │ Tools execute
                             │ tasks via MCP           │ specific actions
                             ↓                         ↓
                        [IM8ComplianceAgent]     [EvidenceFetcher]
                        [Task Worker]            [ComplianceAnalyzer]
```

---

## Phase 1: Installation & Setup

### Step 1.1: Install Dependencies

```bash
# Rebuild containers with new dependencies
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**What to check:**
- ✅ All containers start successfully
- ✅ No import errors in logs
- ✅ MCP server shows "2 tools registered" in logs

**Verification:**
```bash
# Check container status
docker-compose ps

# Check MCP server logs
docker-compose logs mcp_server | grep "tools_registered"
# Expected: "tools_registered": 2

# Check API logs
docker-compose logs api | grep "MCP Client"
# Expected: "MCP Client initialized: http://mcp_server:8001"
```

---

## Phase 2: MCP Server Tool Registration

### Step 2.1: List Available Tools

**API Endpoint:**
```bash
curl http://localhost:8001/tools | jq
```

**Expected Output:**
```json
{
  "tools": [
    {
      "name": "fetch_evidence",
      "description": "Fetch evidence documents from URLs or local filesystem",
      "input_schema": { ... },
      "output_schema": { ... }
    },
    {
      "name": "analyze_compliance",
      "description": "Analyze project compliance against IM8/ISO/NIST frameworks",
      "input_schema": { ... },
      "output_schema": { ... }
    }
  ]
}
```

**What to verify:**
- ✅ 2 tools are registered
- ✅ Each tool has name, description, and schemas
- ✅ Schemas match expected input/output format

### Step 2.2: Get Specific Tool Info

**API Endpoint:**
```bash
# Get evidence fetcher info
curl http://localhost:8001/tools/fetch_evidence | jq

# Get compliance analyzer info
curl http://localhost:8001/tools/analyze_compliance | jq
```

**What to check:**
- ✅ Input schema shows required fields (sources, project_id, created_by)
- ✅ Output schema shows expected result structure
- ✅ No 404 errors

---

## Phase 3: MCP Tool Invocation (Direct Testing)

### Step 3.1: Test Evidence Fetcher Tool (Direct Call)

**Purpose:** Verify MCP server can execute tools directly

**API Endpoint:**
```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "fetch_evidence",
    "parameters": {
      "sources": [
        {
          "type": "url",
          "location": "https://example.com/sample-policy.pdf",
          "description": "Sample security policy",
          "control_id": 1
        }
      ],
      "project_id": 1,
      "created_by": 1
    }
  }' | jq
```

**Expected Output:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "evidence_ids": [123],
    "checksums": ["abc123..."],
    "errors": [],
    "total_fetched": 1,
    "total_failed": 0
  }
}
```

**What to verify:**
- ✅ Tool executes without errors
- ✅ Evidence is downloaded to /app/evidence_storage
- ✅ Database record is created in `evidence` table
- ✅ Checksum is calculated correctly

**Troubleshooting:**
- ❌ 404 error: Tool not registered (check tool name)
- ❌ Connection error: Database connection failed (check DATABASE_URL)
- ❌ Permission error: Storage path not writable (check volume mounts)

### Step 3.2: Test Compliance Analyzer Tool (Direct Call)

**Prerequisites:**
- Project must exist in database (ID=1)
- Controls must exist for framework (IM8)

**API Endpoint:**
```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "analyze_compliance",
    "parameters": {
      "project_id": 1,
      "framework": "IM8",
      "include_evidence": true,
      "generate_recommendations": true
    }
  }' | jq
```

**Expected Output:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "project_id": 1,
    "framework": "IM8",
    "overall_score": 62.5,
    "total_controls": 133,
    "implemented_controls": 45,
    "partial_controls": 30,
    "not_implemented_controls": 58,
    "not_applicable_controls": 0,
    "critical_gaps": [
      "IM8-AC-1: Control not yet implemented",
      "IM8-AC-2: No evidence uploaded"
    ],
    "recommendations": [
      "📊 MODERATE: Compliance is progressing but needs improvement...",
      "📎 Upload evidence for 75 control(s)...",
      "🔧 Implement 58 control(s)..."
    ],
    "analyzed_at": "2025-11-02T10:30:00"
  }
}
```

**What to verify:**
- ✅ Overall score is calculated correctly
- ✅ Control counts match database
- ✅ Gaps are identified for low-scoring controls
- ✅ Recommendations are generated

---

## Phase 4: MCP Client Testing (from FastAPI Backend)

### Step 4.1: Test MCP Client Health Check

**Python Script:**
```bash
docker-compose exec api python -c "
import asyncio
from api.src.mcp.client import mcp_client

async def test():
    healthy = await mcp_client.health_check()
    print(f'MCP Server Health: {healthy}')
    
    tools = await mcp_client.list_tools()
    print(f'Available Tools: {len(tools[\"tools\"])}')
    
    for tool in tools['tools']:
        print(f'  - {tool[\"name\"]}: {tool[\"description\"]}')

asyncio.run(test())
"
```

**Expected Output:**
```
MCP Server Health: True
Available Tools: 2
  - fetch_evidence: Fetch evidence documents from URLs or local filesystem
  - analyze_compliance: Analyze project compliance against IM8/ISO/NIST frameworks
```

### Step 4.2: Test MCP Client Tool Calls

**Python Script:**
```bash
docker-compose exec api python -c "
import asyncio
from api.src.mcp.client import mcp_client

async def test():
    # Test evidence fetcher
    result = await mcp_client.fetch_evidence(
        sources=[
            {
                'type': 'url',
                'location': 'https://example.com/test.pdf',
                'description': 'Test document',
                'control_id': 1
            }
        ],
        project_id=1,
        created_by=1
    )
    print(f'Evidence Fetch Result: {result}')
    
    # Test compliance analyzer
    analysis = await mcp_client.analyze_compliance(
        project_id=1,
        framework='IM8'
    )
    print(f'Compliance Score: {analysis[\"overall_score\"]}%')
    print(f'Total Controls: {analysis[\"total_controls\"]}')

asyncio.run(test())
"
```

---

## Phase 5: End-to-End Agentic Workflow Testing

### Step 5.1: Create Evidence Fetch Task (via Agent)

**Purpose:** Test full workflow: Frontend → API → Agent → MCP Tool

**API Endpoint:**
```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@qca.com","password":"admin123"}' \
  | jq -r '.token')

# Create evidence fetch task
curl -X POST http://localhost:8000/agent-tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "fetch_evidence",
    "payload": {
      "sources": [
        {
          "type": "url",
          "location": "https://example.com/security-policy.pdf",
          "description": "Security Policy v2.0",
          "control_id": 1
        },
        {
          "type": "url",
          "location": "https://example.com/access-control-procedure.docx",
          "description": "Access Control Procedures",
          "control_id": 2
        }
      ],
      "project_id": 1,
      "created_by": 1
    }
  }' | jq
```

**Expected Output:**
```json
{
  "id": 456,
  "task_type": "fetch_evidence",
  "status": "pending",
  "created_at": "2025-11-02T10:35:00",
  "payload": { ... }
}
```

**What happens:**
1. ✅ Task created with status "pending"
2. ✅ Background worker picks up task (within 5 seconds)
3. ✅ Handler calls MCP client
4. ✅ MCP client calls MCP server tool
5. ✅ Tool downloads files and stores in database
6. ✅ Task status changes to "completed"

**Monitor Progress:**
```bash
# Watch task status (replace 456 with actual task ID)
watch -n 1 "curl -s -H 'Authorization: Bearer $TOKEN' http://localhost:8000/agent-tasks/456 | jq '.status, .progress, .progress_message'"
```

**Expected Progress:**
```
Status: "pending" → "running" → "completed"
Progress: 0 → 10 → 20 → 90 → 100
Message: "Preparing..." → "Calling MCP tool..." → "Fetched 2 items"
```

### Step 5.2: Create Compliance Analysis Task (via Agent)

**API Endpoint:**
```bash
curl -X POST http://localhost:8000/agent-tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analyze_compliance",
    "payload": {
      "project_id": 1,
      "framework": "IM8",
      "include_evidence": true,
      "generate_recommendations": true
    }
  }' | jq
```

**Expected Workflow:**
1. ✅ Task created and queued
2. ✅ Background worker picks up task
3. ✅ Handler calls MCP compliance analyzer tool
4. ✅ Tool queries database for controls and evidence
5. ✅ Tool calculates compliance scores
6. ✅ Tool identifies gaps and generates recommendations
7. ✅ Task completes with analysis results

**Retrieve Results:**
```bash
# Get task result (replace 457 with actual task ID)
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/agent-tasks/457 | jq '.result'
```

**Expected Result:**
```json
{
  "status": "success",
  "overall_score": 62.5,
  "total_controls": 133,
  "implemented_controls": 45,
  "critical_gaps": [
    "IM8-AC-1: Control not yet implemented",
    "IM8-AC-2: No evidence uploaded"
  ],
  "recommendations": [
    "📊 MODERATE: Compliance is progressing...",
    "📎 Upload evidence for 75 control(s)...",
    "🔧 Implement 58 control(s)..."
  ]
}
```

---

## Phase 6: Frontend Testing

### Step 6.1: Test via Agent Tasks Page

**Navigate to:** `http://localhost:3000/agent-tasks`

**Test Evidence Fetch:**
1. Click "Create Task" button
2. Select task type: "Fetch Evidence"
3. Fill in payload:
   ```json
   {
     "sources": [
       {
         "type": "url",
         "location": "https://example.com/policy.pdf",
         "description": "Security Policy",
         "control_id": 1
       }
     ],
     "project_id": 1,
     "created_by": 1
   }
   ```
4. Click "Create"
5. Watch task card update with progress
6. Verify task completes successfully

**Test Compliance Analysis:**
1. Click "Create Task" button
2. Select task type: "Analyze Compliance"
3. Fill in payload:
   ```json
   {
     "project_id": 1,
     "framework": "IM8",
     "include_evidence": true,
     "generate_recommendations": true
   }
   ```
4. Click "Create"
5. Watch progress updates
6. Click "View Details" to see full analysis

**What to verify:**
- ✅ Task status updates in real-time
- ✅ Progress bar shows percentage
- ✅ Progress messages update (via MCP handler)
- ✅ Results display correctly
- ✅ Error handling works (try invalid payload)

---

## Phase 7: Demonstration Script

### **Demo Narrative:**

> **"Let me demonstrate our Agentic Reasoning System with MCP Tool Orchestration."**

### **Part 1: Show MCP Architecture (5 minutes)**

```bash
# 1. Show MCP server is running with registered tools
curl http://localhost:8001/ | jq
# Point out: "tools_registered": 2

# 2. List available tools
curl http://localhost:8001/tools | jq '.tools[].name'
# Show: fetch_evidence, analyze_compliance

# 3. Show tool schema
curl http://localhost:8001/tools/fetch_evidence | jq '.input_schema'
# Explain: Agents call tools using this schema
```

**Key Points:**
- ✅ Tools are hosted in separate MCP Server (not in main API)
- ✅ Tools have well-defined schemas
- ✅ Agents discover and call tools via MCP protocol

### **Part 2: Show Direct Tool Invocation (5 minutes)**

```bash
# Call evidence fetcher directly
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "fetch_evidence",
    "parameters": {
      "sources": [
        {
          "type": "url",
          "location": "https://example.com/sample.pdf",
          "description": "Sample evidence",
          "control_id": 1
        }
      ],
      "project_id": 1,
      "created_by": 1
    }
  }' | jq
```

**Key Points:**
- ✅ MCP server executes tool
- ✅ Tool downloads file, calculates checksum, stores in DB
- ✅ Returns structured result with evidence IDs

### **Part 3: Show Agent Orchestration (10 minutes)**

**Open Frontend:** `http://localhost:3000/agent-tasks`

```
1. Create "Analyze Compliance" task
   - Project: IMDA
   - Framework: IM8
   
2. Show task in queue (status: pending)

3. Background worker picks it up (status: running)

4. Progress updates appear:
   - "Initializing compliance analysis..."
   - "Analyzing IM8 compliance for project 1..."
   - "Analysis complete: 62.5% compliance"

5. Task completes (status: completed)

6. View results:
   - Overall score: 62.5%
   - 133 controls assessed
   - 45 implemented, 30 partial, 58 not implemented
   - Critical gaps listed
   - AI-generated recommendations
```

**Key Points:**
- ✅ Agent thinks and plans (5-step reasoning)
- ✅ Agent calls MCP tool to execute analysis
- ✅ Tool does the heavy lifting (DB queries, scoring, recommendations)
- ✅ Agent gets structured result back
- ✅ User sees final analysis with recommendations

### **Part 4: Show Agentic Reasoning (5 minutes)**

**Show Logs:**
```bash
# Agent task handler logs
docker-compose logs api | grep "Compliance analysis task"

# Expected output:
# "Compliance analysis task 123 started - calling MCP tool"
# "Analyzing IM8 compliance for project 1..."
# "Analysis complete: 62.5% compliance"
# "Compliance analysis task 123 completed: 62.5% compliance, 133 controls assessed"
```

**Explain:**
1. **Agent Reasoning:**
   - Analyzes user request ("analyze compliance")
   - Plans approach (fetch controls, calculate scores, identify gaps)
   - Decides which tool to use (analyze_compliance)
   
2. **Tool Execution:**
   - MCP client calls MCP server
   - Tool executes isolated logic
   - Returns structured result
   
3. **Agent Synthesis:**
   - Receives tool result
   - Updates task status
   - Presents to user

**Key Points:**
- ✅ Separation of concerns: Agent = orchestration, Tool = execution
- ✅ Reusable tools (same tool can be used by multiple agents)
- ✅ Scalable architecture (MCP server can be scaled independently)

---

## Phase 8: Troubleshooting

### Common Issues

#### Issue 1: MCP Server Not Reachable
**Symptom:** `Connection refused` errors

**Check:**
```bash
# Verify MCP server is running
docker-compose ps mcp_server

# Check logs for errors
docker-compose logs mcp_server
```

**Solution:**
```bash
docker-compose restart mcp_server
```

#### Issue 2: Tools Not Registered
**Symptom:** 404 error when calling tool

**Check:**
```bash
curl http://localhost:8001/tools | jq '.tools | length'
# Should return: 2
```

**Solution:**
- Check import errors in mcp_server logs
- Verify dependencies are installed
- Rebuild container: `docker-compose build mcp_server`

#### Issue 3: Database Connection Failed
**Symptom:** `sqlalchemy` errors in tool execution

**Check:**
```bash
# Verify DATABASE_URL environment variable
docker-compose exec mcp_server env | grep DATABASE_URL
```

**Solution:**
- Update `docker-compose.yml` to set DATABASE_URL
- Restart MCP server

#### Issue 4: Evidence Files Not Saved
**Symptom:** Tool succeeds but files missing

**Check:**
```bash
# Check volume mount
docker-compose exec mcp_server ls -la /app/evidence_storage

# Check permissions
docker-compose exec mcp_server touch /app/evidence_storage/test.txt
```

**Solution:**
- Add volume mount in docker-compose.yml
- Check directory permissions

---

## Success Criteria

### ✅ Phase 1: Installation
- [ ] All containers start without errors
- [ ] MCP server shows 2 tools registered
- [ ] No import errors in logs

### ✅ Phase 2: Tool Registration
- [ ] `/tools` endpoint lists 2 tools
- [ ] Each tool has input/output schema
- [ ] Tool info endpoint works for each tool

### ✅ Phase 3: Direct Tool Testing
- [ ] Evidence fetcher downloads files
- [ ] Compliance analyzer calculates scores
- [ ] Database records are created
- [ ] Structured results are returned

### ✅ Phase 4: MCP Client Testing
- [ ] Health check returns true
- [ ] List tools shows 2 tools
- [ ] Tool calls succeed from Python

### ✅ Phase 5: Agent Orchestration
- [ ] Tasks are created and queued
- [ ] Background worker picks up tasks
- [ ] Handlers call MCP client
- [ ] Tasks complete successfully
- [ ] Results are stored in database

### ✅ Phase 6: Frontend Testing
- [ ] Agent tasks page loads
- [ ] Create task dialog works
- [ ] Task cards show progress
- [ ] Results display correctly

### ✅ Phase 7: Demonstration
- [ ] Can explain MCP architecture
- [ ] Can show tool registration
- [ ] Can demonstrate agent orchestration
- [ ] Can explain agentic reasoning flow

---

## Next Steps

After successful testing:

1. **Add More Tools:**
   - Report generator (PDF/Word)
   - Control mapper (IM8 ↔ ISO ↔ NIST)
   - Text extractor (OCR, document parsing)

2. **Enhance Agent Reasoning:**
   - Multi-step planning
   - Self-correction on errors
   - Context management across tasks

3. **Add Monitoring:**
   - Tool execution metrics
   - Performance tracking
   - Error rate monitoring

4. **Documentation:**
   - API documentation for MCP tools
   - Developer guide for adding new tools
   - Architecture decision records

---

**Version History:**
- v1.0.0 (2025-11-02): Initial testing guide
