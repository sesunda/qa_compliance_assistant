# Agentic Reasoning System & MCP Architecture

## Your Question: Is MCP Server Hosting the Agent Tools?

**Short Answer:** Not currently, but **that's the vision** for the next evolution!

**Current State:**
- ✅ Agents exist (IM8ComplianceAgent)
- ✅ Tools exist (in FastAPI backend)
- ❌ MCP Server is minimal (only sample data provider)
- ❌ Tools NOT yet in MCP Server

**Target Architecture:**
- ✅ Agents orchestrate tasks
- ✅ **Tools hosted in MCP Server** (this is where you're heading!)
- ✅ Clean separation of concerns

---

## Current Architecture (As-Built)

### **What We Have Now:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  - AgentTasksPage                                           │
│  - User creates tasks                                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Main API)                     │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  Agent System (Agentic Reasoning)    │                  │
│  │  ├─ IM8ComplianceAgent               │                  │
│  │  ├─ HybridRAG                        │                  │
│  │  └─ LLM Service (Groq/Llama)         │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  Tools (Currently in API)            │                  │
│  │  ├─ Evidence Fetcher                 │ ← Should move   │
│  │  ├─ Report Generator                 │   to MCP!       │
│  │  ├─ Compliance Analyzer              │                  │
│  │  └─ Control Mapper                   │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  Background Worker                   │                  │
│  │  ├─ TaskWorker (polling)             │                  │
│  │  └─ Task Handlers                    │                  │
│  └──────────────────────────────────────┘                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL)                          │
│  - agent_tasks, controls, evidence, projects                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         MCP Server (Currently Minimal!)                     │
│  - Only serves sample evidence data                         │
│  - Has one tool: map_controls.py                           │
│  - NOT yet integrated with agents                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Target Architecture (MCP Integration)

### **What It Should Become:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  User: "Analyze IMDA's IM8 compliance"                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Orchestration Layer)          │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  Agent Orchestrator                  │                  │
│  │  ├─ IM8ComplianceAgent               │                  │
│  │  │  (Agentic Reasoning Logic)        │                  │
│  │  │                                   │                  │
│  │  │  Decides WHAT to do:              │                  │
│  │  │  1. Fetch evidence                │                  │
│  │  │  2. Analyze gaps                  │                  │
│  │  │  3. Generate report               │                  │
│  │  └──────────────────────────────────┘                  │
│  │                                                          │
│  │  ┌───────────────────────────────────┐                 │
│  │  │  MCP Client (Tool Caller)         │                 │
│  │  │  Calls tools hosted in MCP Server │                 │
│  │  └───────────┬───────────────────────┘                 │
│  └──────────────┼──────────────────────────────────────────┘
│                 │ MCP Protocol
│                 │ (JSON-RPC)
│                 ↓
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (Tool Hosting)                      │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  MCP Tools (Registered)              │                  │
│  │                                      │                  │
│  │  ├─ fetch_evidence_tool              │                  │
│  │  │  ∟ Download from URL              │                  │
│  │  │  ∟ Copy from filesystem           │                  │
│  │  │  ∟ Calculate checksums             │                  │
│  │  │                                   │                  │
│  │  ├─ analyze_compliance_tool          │                  │
│  │  │  ∟ Query database                 │                  │
│  │  │  ∟ Calculate scores               │                  │
│  │  │  ∟ Identify gaps                  │                  │
│  │  │  ∟ Use RAG for analysis           │                  │
│  │  │                                   │                  │
│  │  ├─ generate_report_tool             │                  │
│  │  │  ∟ Create PDF                     │                  │
│  │  │  ∟ Create Word doc                │                  │
│  │  │  ∟ Apply templates                │                  │
│  │  │                                   │                  │
│  │  ├─ map_controls_tool                │                  │
│  │  │  ∟ Use LLM to map controls        │                  │
│  │  │  ∟ IM8 ↔ ISO ↔ NIST               │                  │
│  │  │                                   │                  │
│  │  └─ extract_text_tool                │                  │
│  │     ∟ OCR for images                 │                  │
│  │     ∟ Parse PDFs/Word                │                  │
│  │     ∟ Extract from Excel             │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  MCP Resources (Data Access)         │                  │
│  │  ├─ Sample evidence repository       │                  │
│  │  ├─ Template library                 │                  │
│  │  └─ Knowledge base access            │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                     │
                     ↓ Shared database access
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## What is MCP (Model Context Protocol)?

### **Definition:**
MCP is a **standardized protocol** for connecting AI models/agents to external tools and data sources.

### **Key Concepts:**

#### **1. MCP Server**
```python
# Hosts tools and resources
# Exposes them via JSON-RPC protocol

class MCPServer:
    def __init__(self):
        self.tools = {}
        self.resources = {}
    
    def register_tool(self, name, handler):
        """Register a callable tool"""
        self.tools[name] = handler
    
    async def call_tool(self, tool_name, params):
        """Execute tool with parameters"""
        return await self.tools[tool_name](**params)
```

#### **2. MCP Client (in FastAPI Backend)**
```python
# Agent uses client to call tools

class MCPClient:
    async def call_tool(self, tool_name, params):
        """Send JSON-RPC request to MCP server"""
        response = await self.rpc_call({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        })
        return response["result"]
```

#### **3. Agent (Orchestration Logic)**
```python
# Agent decides WHAT tools to use and WHEN

class IM8ComplianceAgent:
    async def analyze_compliance(self, project_id):
        # Step 1: Fetch evidence (uses tool)
        evidence = await mcp_client.call_tool(
            "fetch_evidence_tool",
            {"project_id": project_id}
        )
        
        # Step 2: Analyze gaps (uses tool)
        gaps = await mcp_client.call_tool(
            "analyze_compliance_tool",
            {"evidence": evidence}
        )
        
        # Step 3: Generate report (uses tool)
        report = await mcp_client.call_tool(
            "generate_report_tool",
            {"gaps": gaps}
        )
        
        return report
```

---

## Why Use MCP? (Benefits)

### **1. Separation of Concerns**
```
Agent Logic (What/When):       Tool Implementation (How):
- IM8ComplianceAgent          - Evidence fetcher
- Decide task sequence        - Report generator
- Reasoning & planning        - Database queries
- Context management          - File processing

Location: FastAPI Backend     Location: MCP Server
```

### **2. Tool Reusability**
```
Multiple agents can use same tools:

IM8Agent → fetch_evidence_tool
ISO27001Agent → fetch_evidence_tool
NISTAgent → fetch_evidence_tool

All share the same implementation!
```

### **3. Scalability**
```
MCP Server can be scaled independently:

┌──────────┐     ┌──────────┐
│ MCP      │     │ MCP      │
│ Server 1 │     │ Server 2 │
│ (Tools)  │     │ (Tools)  │
└──────────┘     └──────────┘
      ↑                ↑
      └────────┬───────┘
               │ Load balanced
               ↓
        ┌──────────┐
        │ FastAPI  │
        │ Backend  │
        └──────────┘
```

### **4. Language Agnostic**
```
Tools can be written in different languages:

fetch_evidence_tool    → Python
generate_pdf_tool      → Node.js + Puppeteer
ocr_tool              → Python + Tesseract
excel_processor       → .NET Core

Agent doesn't care! MCP abstracts it.
```

### **5. Security**
```
Tools run in isolated MCP server:
- Sandboxed execution
- Resource limits
- Rate limiting
- Separate permissions
```

---

## Current State vs. Target

### **What Exists Now:**

| Component | Status | Location |
|-----------|--------|----------|
| **Agents** | ✅ Implemented | `api/src/rag/im8_agent.py` |
| **Tools** | ✅ Implemented | `api/src/workers/` (NOT in MCP!) |
| **MCP Server** | ⚠️ Minimal | `mcp_server/` (only sample data) |
| **MCP Integration** | ❌ Not done | N/A |
| **Background Worker** | ✅ Working | `api/src/workers/task_worker.py` |

### **Tools Currently in API (Should Move to MCP):**

1. **Evidence Fetcher** (`api/src/workers/evidence_fetcher.py`)
   - ✅ Implemented
   - ❌ In FastAPI, not MCP
   - 🎯 Should move to MCP

2. **Control Mapper** (`mcp_server/src/tools/map_controls.py`)
   - ✅ Implemented
   - ⚠️ In MCP but not registered
   - 🎯 Needs proper MCP registration

3. **Report Generator** (Not yet implemented)
   - ❌ Placeholder only
   - 🎯 Should be built as MCP tool

4. **Compliance Analyzer** (Not yet implemented)
   - ❌ Placeholder only
   - 🎯 Should be built as MCP tool

---

## Migration Path: Moving Tools to MCP

### **Step 1: Refactor Evidence Fetcher as MCP Tool**

**Current:** `api/src/workers/evidence_fetcher.py`
```python
# Tightly coupled to FastAPI

async def handle_fetch_evidence_task(task_id, payload, db):
    # Direct database access
    # Direct file system access
    pass
```

**Target:** `mcp_server/src/tools/evidence_fetcher_tool.py`
```python
# MCP Tool (isolated, reusable)

from mcp.server import Tool

class EvidenceFetcherTool(Tool):
    name = "fetch_evidence"
    description = "Fetch evidence from URLs or local files"
    
    async def execute(self, params):
        """
        Params:
          - sources: List[{type, url/path, description}]
          - control_id: int
        
        Returns:
          - evidence_ids: List[int]
          - checksums: List[str]
        """
        results = []
        for source in params["sources"]:
            if source["type"] == "url":
                result = await self._download_from_url(source["url"])
            else:
                result = await self._copy_from_path(source["path"])
            
            results.append(result)
        
        return {"evidence": results}
```

**Agent Calls MCP Tool:**
```python
# api/src/rag/im8_agent.py

async def fetch_project_evidence(self, project_id):
    # Instead of direct call, use MCP client
    result = await mcp_client.call_tool(
        "fetch_evidence",
        {
            "project_id": project_id,
            "sources": [
                {"type": "url", "url": "https://..."}
            ]
        }
    )
    return result
```

---

### **Step 2: Implement MCP Server Properly**

**Current MCP Server:** Only serves sample data
```python
# mcp_server/src/main.py
# Just a simple FastAPI app

@app.get("/sample-evidence")
def get_sample_evidence():
    return SAMPLE_EVIDENCE
```

**Target MCP Server:** Proper MCP implementation
```python
# mcp_server/src/main.py
from mcp.server import MCPServer
from mcp_server.src.tools import (
    EvidenceFetcherTool,
    ComplianceAnalyzerTool,
    ReportGeneratorTool,
    ControlMapperTool,
    TextExtractorTool
)

# Initialize MCP Server
mcp_server = MCPServer(
    name="QCA Compliance Tools",
    version="1.0.0"
)

# Register tools
mcp_server.register_tool(EvidenceFetcherTool())
mcp_server.register_tool(ComplianceAnalyzerTool())
mcp_server.register_tool(ReportGeneratorTool())
mcp_server.register_tool(ControlMapperTool())
mcp_server.register_tool(TextExtractorTool())

# Start server (JSON-RPC over HTTP/WebSocket)
if __name__ == "__main__":
    mcp_server.run(host="0.0.0.0", port=9000)
```

---

### **Step 3: Create MCP Client in FastAPI**

```python
# api/src/mcp/client.py

from mcp.client import MCPClient

class ComplianceToolsClient:
    def __init__(self):
        self.mcp = MCPClient(
            server_url="http://mcp_server:9000"
        )
    
    async def fetch_evidence(self, params):
        return await self.mcp.call_tool("fetch_evidence", params)
    
    async def analyze_compliance(self, params):
        return await self.mcp.call_tool("analyze_compliance", params)
    
    async def generate_report(self, params):
        return await self.mcp.call_tool("generate_report", params)

# Singleton instance
mcp_tools = ComplianceToolsClient()
```

---

### **Step 4: Update Agent to Use MCP Client**

```python
# api/src/rag/im8_agent.py

from api.src.mcp.client import mcp_tools

class IM8ComplianceAgent:
    async def analyze_compliance_query(self, query, context):
        # Step 1: Use MCP tool to fetch evidence
        evidence = await mcp_tools.fetch_evidence({
            "project_id": context["project_id"]
        })
        
        # Step 2: Use MCP tool to analyze
        analysis = await mcp_tools.analyze_compliance({
            "evidence": evidence,
            "framework": "IM8"
        })
        
        # Step 3: Use MCP tool to generate report
        report = await mcp_tools.generate_report({
            "analysis": analysis,
            "template": "im8_compliance"
        })
        
        return report
```

---

## Showcasing as Agentic Reasoning System

### **What Makes It "Agentic":**

#### **1. Multi-Step Reasoning**
```
User: "Analyze IMDA's IM8 compliance"

Agent Thinks:
├─ Step 1: ANALYZE requirements
│  ↳ "Need to assess IM8 controls for IMDA"
│
├─ Step 2: PLAN approach
│  ↳ "Fetch evidence → Calculate scores → Identify gaps"
│
├─ Step 3: EXECUTE plan
│  ├─ Call fetch_evidence_tool (MCP)
│  ├─ Call analyze_compliance_tool (MCP)
│  └─ Call generate_report_tool (MCP)
│
├─ Step 4: VALIDATE results
│  ↳ "Check if analysis is complete"
│
└─ Step 5: SYNTHESIZE recommendations
   ↳ "Generate Singapore-specific guidance"
```

#### **2. Tool Selection & Orchestration**
```python
# Agent decides WHICH tools to use based on context

if context["analysis_type"] == "quick":
    # Use lightweight tools
    tools_needed = ["fetch_evidence_tool", "quick_score_tool"]
elif context["analysis_type"] == "full":
    # Use comprehensive tools
    tools_needed = [
        "fetch_evidence_tool",
        "analyze_compliance_tool",
        "identify_gaps_tool",
        "generate_recommendations_tool",
        "generate_report_tool"
    ]

# Execute tools in order
for tool in tools_needed:
    result = await mcp_client.call_tool(tool, params)
```

#### **3. Context Management**
```python
# Agent maintains conversation context

class AgentContext:
    def __init__(self):
        self.history = []
        self.working_memory = {}
    
    def add_step(self, step, result):
        self.history.append({
            "step": step,
            "result": result,
            "timestamp": datetime.now()
        })
        
    def get_relevant_context(self, query):
        # Use last 5 interactions
        return self.history[-5:]
```

#### **4. Self-Correction**
```python
# Agent can retry if tool fails

async def execute_with_retry(tool_name, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await mcp_client.call_tool(tool_name, params)
            return result
        except ToolError as e:
            if attempt < max_retries - 1:
                # Modify params based on error
                params = self._adjust_params(params, e)
            else:
                raise
```

---

## Demo Script for Showcasing

### **Narrative:**

```
"This is an Agentic Reasoning System for compliance management.

The Agent (IM8ComplianceAgent) uses reasoning to break down complex
compliance tasks into steps, then orchestrates tools hosted in the
MCP Server to execute each step.

Watch as the agent:
1. Analyzes the user's request
2. Plans the assessment approach
3. Calls MCP tools to execute the plan
4. Validates the results
5. Synthesizes recommendations

All tools are modular, reusable, and isolated in the MCP Server,
making the system scalable and maintainable."
```

### **Live Demo Flow:**

```
1. User Input: "Analyze IMDA's IM8 compliance"

2. Agent Reasoning (Show logs):
   [ANALYZE] Understanding requirement: IM8 assessment for IMDA
   [PLAN] Approach: Fetch evidence → Score → Gaps → Report
   [EXECUTE] Calling MCP tool: fetch_evidence
   [EXECUTE] Calling MCP tool: analyze_compliance
   [EXECUTE] Calling MCP tool: generate_report
   [VALIDATE] Checking completeness: 133/133 controls assessed
   [SYNTHESIZE] Generating recommendations...

3. MCP Tool Execution (Show in separate terminal):
   [MCP] fetch_evidence_tool: Downloading 67 documents...
   [MCP] analyze_compliance_tool: Calculating scores...
   [MCP] generate_report_tool: Creating PDF report...

4. Final Output:
   ✅ Compliance Score: 62%
   ✅ Critical Gaps: 3
   ✅ Report: /reports/imda-im8-2025-11-02.pdf
```

---

## Summary

### **Your Understanding:**
✅ **Correct:** Agents orchestrate tasks using specific tools  
✅ **Correct:** Tools should be hosted in MCP Server  
⚠️ **Partially Correct:** Currently tools are in FastAPI, need migration to MCP

### **Current State:**
- Agents: ✅ Implemented (IM8ComplianceAgent)
- Tools: ✅ Implemented (in FastAPI, not MCP)
- MCP Server: ⚠️ Minimal (needs enhancement)
- Integration: ❌ Not yet connected

### **Next Steps to Achieve Vision:**
1. ✅ Implement proper MCP Server with tool registration
2. ✅ Move tools from FastAPI to MCP Server
3. ✅ Create MCP client in FastAPI
4. ✅ Update agents to use MCP client
5. ✅ Test end-to-end agentic workflow

### **For Showcase:**
**Positioning:** "Agentic Reasoning System with MCP Tool Orchestration"
- **Agent:** Thinks, plans, orchestrates
- **MCP Server:** Hosts reusable, isolated tools
- **Result:** Scalable, modular compliance automation

---

**Would you like me to start implementing the MCP integration?** I can:
1. Enhance MCP server with proper tool registration
2. Migrate evidence fetcher to MCP tool
3. Create MCP client in FastAPI
4. Update agents to use MCP tools
