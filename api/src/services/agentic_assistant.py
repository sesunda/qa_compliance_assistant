"""
Groq-powered Agentic AI Assistant
Multi-turn conversation with tool calling for QA Compliance
Supports: Groq, GitHub Models (OpenAI-compatible API)
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from groq import Groq
from openai import OpenAI
import logging

from api.src.services.conversation_manager import ConversationManager
from api.src.services.ai_task_orchestrator import ai_task_orchestrator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AgenticAssistant:
    """Agentic conversational agent with tool calling (supports multiple providers)"""
    
    def __init__(self):
        # Detect which provider to use
        self.provider = os.getenv("LLM_PROVIDER", "groq")  # groq, github, openai
        
        if self.provider == "github":
            # GitHub Models (free tier)
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                raise ValueError("GITHUB_TOKEN required for GitHub Models")
            
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=github_token
            )
            # Available models: gpt-4o, gpt-4o-mini, Llama-3.1-70B-Instruct, Phi-3-medium-128k-instruct
            self.model = os.getenv("GITHUB_MODEL", "gpt-4o-mini")
            logger.info(f"Using GitHub Models with {self.model}")
            
        elif self.provider == "openai":
            # OpenAI (paid)
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            logger.info(f"Using OpenAI with {self.model}")
            
        else:  # groq (default)
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            # Check which models are available
            try:
                self.model = "llama-3.3-70b-versatile"  # Try newer model first
            except:
                self.model = "llama-3.1-8b-instant"  # Fallback to stable model
            logger.info(f"Using Groq with {self.model}")
        
        # Define tools available to the agent
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "upload_evidence",
                    "description": "Upload compliance evidence document for a control. Use when user wants to submit audit reports, assessment documents, or evidence files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "string",
                                "description": "The ID of the control this evidence relates to (can be numeric)"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to the uploaded file"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the evidence"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_evidence",
                    "description": "Retrieve compliance evidence for a specific control or project. Use when user wants to view or download evidence.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "string",
                                "description": "The control ID to fetch evidence for (can be numeric)"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "The project ID to fetch evidence for (can be numeric)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_compliance",
                    "description": "Analyze compliance status and generate insights. Use when user wants compliance analysis or assessment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "string",
                                "description": "The control ID to analyze (can be numeric)"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["gap", "status", "risk"],
                                "description": "Type of compliance analysis"
                            }
                        },
                        "required": ["control_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": "Generate compliance report for a framework or project. Use when user wants to create reports.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "framework": {
                                "type": "string",
                                "enum": ["IM8", "NIST", "ISO27001"],
                                "description": "Compliance framework"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Project ID for the report (can be numeric)"
                            },
                            "report_type": {
                                "type": "string",
                                "enum": ["compliance", "gap", "executive"],
                                "description": "Type of report to generate"
                            }
                        },
                        "required": ["framework"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "submit_for_review",
                    "description": "Submit evidence for maker-checker review. Use when user wants to submit evidence to auditor.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "string",
                                "description": "The evidence ID to submit for review (can be numeric)"
                            }
                        },
                        "required": ["evidence_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_fetch_evidence",
                    "description": "Fetch evidence from URLs or local filesystem using MCP server. Automatically downloads files, calculates SHA256 checksums, and stores in database with maker-checker workflow. Use when user provides URLs to download compliance evidence.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sources": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": ["url", "file"],
                                            "description": "Source type"
                                        },
                                        "location": {
                                            "type": "string",
                                            "description": "URL or file path"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Description of evidence"
                                        },
                                        "control_id": {
                                            "type": "integer",
                                            "description": "Control ID this evidence relates to"
                                        }
                                    },
                                    "required": ["type", "location", "control_id"]
                                },
                                "description": "List of evidence sources to fetch"
                            },
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID for evidence storage"
                            },
                            "created_by": {
                                "type": "integer",
                                "description": "User ID who initiated the fetch"
                            }
                        },
                        "required": ["sources", "project_id", "created_by"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_analyze_compliance",
                    "description": "Comprehensive compliance analysis using MCP server. Calculates overall compliance score (0-100), identifies gaps, assesses each control's implementation status, counts evidence, and generates AI-powered recommendations. Use when user requests full compliance analysis or assessment report.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID to analyze"
                            },
                            "framework": {
                                "type": "string",
                                "enum": ["IM8", "ISO27001", "NIST"],
                                "description": "Compliance framework",
                                "default": "IM8"
                            },
                            "include_evidence": {
                                "type": "boolean",
                                "description": "Include evidence analysis in assessment",
                                "default": True
                            },
                            "generate_recommendations": {
                                "type": "boolean",
                                "description": "Generate AI recommendations for gaps",
                                "default": True
                            }
                        },
                        "required": ["project_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search uploaded compliance documents using semantic vector search. Returns relevant document excerpts with similarity scores and source citations. Use when user asks questions about uploaded documents, policies, audit reports, or evidence content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query"
                            },
                            "control_id": {
                                "type": "integer",
                                "description": "Filter by specific control ID (optional)"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # System prompt (will be enhanced per role in chat method)
        self.base_system_prompt = """You are an AI compliance assistant for the Quantique QA Compliance platform.
You help users with Singapore IM8 compliance tasks including:
- Uploading and managing compliance evidence
- Analyzing compliance status and gaps
- Generating compliance reports
- Managing maker-checker workflows

IMPORTANT: Available control IDs in the system are: 1, 3, 4, 5
- Control 1: Test Control
- Control 3: Network segmentation for sensitive systems
- Control 4: Encrypt data at rest
- Control 5: Enforce MFA for privileged accounts

When users upload files or mention evidence, use the upload_evidence tool with a valid control_id (1, 3, 4, or 5).
If the user doesn't specify a control, use control_id=1 as default.
When users want to see evidence, use fetch_evidence tool.
When users want compliance analysis, use analyze_compliance tool.
When users want reports, use generate_report tool.

EVIDENCE UPLOAD TEMPLATES:
When asking users to upload evidence, ALWAYS mention that they can download pre-formatted templates:
- CSV template: GET /templates/evidence-upload.csv
- JSON template: GET /templates/evidence-upload.json
- IM8 Controls Sample (with realistic data): GET /templates/im8-controls-sample.csv
- Validation rules: GET /templates/template-validation-rules
Example: "Please upload evidence for control 5. You can download a CSV template from /templates/evidence-upload.csv or view a filled sample with IM8 controls at /templates/im8-controls-sample.csv to see the required format."

Be conversational, helpful, and ask clarifying questions if needed.
Always confirm actions before executing them.
Maintain context across the conversation."""
    
    def _build_role_specific_prompt(self, user_role: str) -> str:
        """Build role-specific system prompt with IM8 workflow guidance"""
        role_prompts = {
            "auditor": """

ROLE: AUDITOR - IM8 Workflow Guidance
======================================
As an auditor, you can:

1. **Set Up IM8 Controls for Projects**:
   - ✅ **You CAN set up IM8 controls** - Use the Controls tab or upload control templates
   - Navigate to Controls page, select project, add IM8 framework controls
   - Define control requirements, testing procedures, and evidence requirements
   - This establishes the compliance framework for analysts to work against

2. **Share Templates with Analysts**:
   - 📥 **Evidence Upload Template (CSV)**: [Download](/api/templates/evidence-upload.csv)
   - 📥 **Evidence Upload Template (JSON)**: [Download](/api/templates/evidence-upload.json)
   - 📥 **Sample IM8 Controls**: [Download](/api/templates/im8-controls-sample.csv)
   - Guide analysts: "Download the template, upload evidence for each control I've set up"

3. **Review Evidence Submissions**:
   - Check "Under Review" queue for evidence uploaded by analysts
   - View evidence documents, validation status, and analyst notes
   - Verify evidence supports the control implementation claims
   
4. **Approve/Reject Evidence**:
   - Approve: Evidence marked as verified, counts toward compliance
   - Reject: Return to analyst with specific review comments
   - IMPORTANT: Cannot approve your own submissions (segregation of duties)

⚠️ **IMPORTANT ROLE RESTRICTIONS**:
- ✅ **Auditors CAN set up IM8 controls** - You define the framework
- ❌ **Auditors CANNOT upload evidence** - Only analysts upload evidence documents
- **Clear separation**: You set up controls, analysts provide evidence, you review/approve
- If asked to upload evidence, respond: "As an auditor, you cannot upload evidence documents. Only analysts can upload evidence. Your role is to set up the controls and then review/approve evidence submitted by analysts."

4. **IM8 Template Structure**:
   - 2 Domains: Information Security Governance, Network Security
   - 4 Controls total (2 per domain)
   - Required: Control ID (IM8-DD-CC format), Status, Implementation Date, Evidence files
   - Status values: "Implemented", "Partial", "Not Started"

📥 **Download Templates**:
- [Evidence Upload CSV Template](/api/templates/evidence-upload.csv) - For structured evidence uploads
- [Evidence Upload JSON Template](/api/templates/evidence-upload.json) - For JSON-based uploads  
- [Sample IM8 Controls CSV](/api/templates/im8-controls-sample.csv) - Example with realistic data

Example guidance for analysts:
"Please download one of the templates above. The CSV template is easiest to fill out - complete all controls with their evidence details, then upload with the actual evidence files. The system will automatically validate and submit for review."
""",
            
            "analyst": """

ROLE: ANALYST - IM8 Workflow Guidance
======================================
As an analyst, you can:

1. **Download IM8 Templates**:
   📥 **Available Templates**:
   - [Evidence Upload CSV Template](/api/templates/evidence-upload.csv) - Easy to fill, supports all evidence types
   - [Evidence Upload JSON Template](/api/templates/evidence-upload.json) - For programmatic uploads
   - [Sample IM8 Controls CSV](/api/templates/im8-controls-sample.csv) - See realistic examples

2. **Complete IM8 Assessment**:
   - Fill Metadata sheet: Project name, agency, assessment period, contact
   - For each control in Domain sheets:
     * Set Status: "Implemented", "Partial", or "Not Started"
     * Embed PDF evidence: Insert > Object > Create from File
     * Enter Implementation Date (YYYY-MM-DD)
     * Add Notes explaining implementation
   - Update Reference Policies sheet with supporting documents

3. **Upload Evidence (YOUR PRIMARY RESPONSIBILITY)**:
   ⚠️ **IMPORTANT**: As an analyst, YOU are responsible for uploading all evidence documents
   - Upload completed Excel file with evidence_type="im8_assessment_document"
   - System validates: sheet structure, control IDs, status values, embedded PDFs
   - Auto-submits to "Under Review" if valid (no manual submit needed)
   - Auditor reviews and approves/rejects YOUR submissions

4. **IM8 Controls Structure**:
   - Domain 1: IM8-01-01 (Identity & Access), IM8-01-02 (Access Reviews)
   - Domain 2: IM8-02-01 (Network Segmentation), IM8-02-02 (Firewall Management)
   - Each control needs: Status + PDF evidence + Implementation Date + Notes

5. **Validation Requirements**:
   - Control ID format: IM8-DD-CC (e.g., IM8-01-01)
   - At least 1 embedded PDF per control
   - Valid status values only
   - Required metadata fields filled

TIP: Use the sample completed template to see examples of proper formatting and PDF embedding.
""",
            
            "viewer": """

ROLE: VIEWER - IM8 Read-Only Access
====================================
As a viewer, you can:

1. **View IM8 Documents**: See uploaded IM8 assessments and their status
2. **Check Compliance Status**: View completion %, implemented/partial/not started counts
3. **Download Evidence**: Access approved IM8 documents and embedded PDFs
4. **View Reports**: See compliance reports and gap analysis

You cannot upload, approve, or reject IM8 documents (read-only access).
"""
        }
        
        role_suffix = role_prompts.get(user_role.lower(), "")
        return self.base_system_prompt + role_suffix
    
    async def chat(
        self,
        message: str,
        conversation_manager: ConversationManager,
        session_id: str,
        db: Session,
        current_user: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message with agentic reasoning and tool calling
        
        Args:
            message: User's message
            conversation_manager: Conversation manager instance
            session_id: Current conversation session ID
            db: Database session
            current_user: Current user dict
            file_path: Optional uploaded file path
            
        Returns:
            Response dictionary with answer and tool execution results
        """
        try:
            # Get conversation history
            history = conversation_manager.get_conversation_history(session_id, limit=10)
            
            # Build role-specific system prompt
            user_role = current_user.get("role", "viewer")
            system_prompt = self._build_role_specific_prompt(user_role)
            
            # Build messages for LLM
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in history[:-1]:  # Exclude the last message (just added user message)
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            user_content = message
            if file_path:
                user_content += f"\n[File uploaded: {os.path.basename(file_path)}]"
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Call Groq with tool calling
            logger.info(f"Calling Groq LLM for session {session_id}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=2000,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls
            
            # Process tool calls if any
            tool_results = []
            if tool_calls:
                logger.info(f"Agent wants to call {len(tool_calls)} tool(s)")
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing tool: {function_name} with args: {function_args}")
                    
                    # Route to appropriate handler
                    if function_name.startswith("mcp_"):
                        # MCP Server tools
                        tool_result = await self.handle_mcp_tool_call(function_name, function_args)
                    elif function_name == "search_documents":
                        # RAG document search
                        tool_result = await self.handle_search_documents(
                            query=function_args.get("query"),
                            control_id=function_args.get("control_id"),
                            top_k=function_args.get("top_k", 5),
                            db=db,
                            current_user=current_user
                        )
                    else:
                        # Existing tools via AI Task Orchestrator
                        tool_result = await self._execute_tool(
                            function_name=function_name,
                            function_args=function_args,
                            db=db,
                            current_user=current_user,
                            file_path=file_path
                        )
                    
                    tool_results.append({
                        "tool": function_name,
                        "arguments": function_args,
                        "result": tool_result
                    })
                
                # Add tool results back to conversation for final response
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]
                })
                
                # Add tool results
                for tool_call, tool_result in zip(tool_calls, tool_results):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result["result"])
                    })
                
                # Get final response
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                final_answer = final_response.choices[0].message.content
            else:
                # No tool calls, just use assistant's response
                final_answer = assistant_message.content
            
            # Save assistant response to conversation
            conversation_manager.add_message(
                session_id,
                role="assistant",
                content=final_answer,
                tool_calls=tool_results if tool_results else None
            )
            
            return {
                "answer": final_answer,
                "tool_calls": tool_results,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in agentic chat: {str(e)}", exc_info=True)
            raise
    
    async def handle_mcp_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route tool calls to MCP server
        
        Args:
            tool_name: MCP tool name (mcp_fetch_evidence, mcp_analyze_compliance)
            arguments: Tool parameters
            
        Returns:
            MCP tool execution result
        """
        from ..mcp.client import mcp_client
        
        try:
            # Remove 'mcp_' prefix to get actual tool name
            actual_tool_name = tool_name.replace("mcp_", "")
            
            logger.info(f"Calling MCP tool: {actual_tool_name}")
            logger.debug(f"MCP tool arguments: {arguments}")
            
            # Call MCP server
            result = await mcp_client.call_tool(actual_tool_name, arguments)
            
            logger.info(f"MCP tool {actual_tool_name} completed successfully")
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    async def handle_search_documents(
        self,
        query: str,
        control_id: Optional[int] = None,
        top_k: int = 5,
        db: Session = None,
        current_user: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute semantic search on uploaded documents
        
        Args:
            query: Search query
            control_id: Filter by control ID
            top_k: Number of results
            db: Database session
            current_user: Current user context
            
        Returns:
            Search results with context and sources
        """
        try:
            from ..rag.vector_search import vector_store
            
            logger.info(f"Searching documents: {query}")
            
            # Perform vector search
            search_results = await vector_store.search(
                query=query,
                user_id=current_user["id"],
                agency_id=current_user.get("agency_id"),
                filters={"control_id": control_id} if control_id else {},
                top_k=top_k
            )
            
            # Format results
            context_chunks = []
            sources = []
            
            for result in search_results:
                context_chunks.append(result.get("content", ""))
                sources.append({
                    "document_name": result.get("metadata", {}).get("filename", "Unknown"),
                    "page": result.get("metadata", {}).get("page_number"),
                    "control_id": result.get("metadata", {}).get("control_id"),
                    "score": result.get("score", 0.0)
                })
            
            return {
                "success": True,
                "context": "\n\n---\n\n".join(context_chunks),
                "sources": sources,
                "total_results": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Document search failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "context": "",
                "sources": []
            }
    
    def _coerce_argument_types(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce argument types to match expected schema (fixes LLM string->int issues)"""
        # Define integer fields for each function
        integer_fields = {
            "upload_evidence": ["control_id", "project_id"],
            "fetch_evidence": ["control_id", "project_id"],
            "analyze_compliance": ["control_id", "project_id"],
            "generate_report": ["project_id"],
            "submit_for_review": ["evidence_id"]
        }
        
        coerced = args.copy()
        int_fields = integer_fields.get(function_name, [])
        
        for field in int_fields:
            if field in coerced and coerced[field] is not None:
                try:
                    # Convert to int if it's a string representation
                    if isinstance(coerced[field], str):
                        coerced[field] = int(coerced[field])
                        logger.info(f"Coerced {field} from string to int: {coerced[field]}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to coerce {field} to int: {e}")
        
        return coerced
    
    async def _execute_tool(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        db: Session,
        current_user: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a tool via AI Task Orchestrator"""
        
        # Map tool to task type
        task_type_map = {
            "upload_evidence": "fetch_evidence",  # Uses same handler
            "fetch_evidence": "fetch_evidence",
            "analyze_compliance": "analyze_compliance",
            "generate_report": "generate_report",
            "submit_for_review": "submit_for_review"
        }
        
        task_type = task_type_map.get(function_name)
        if not task_type:
            return {"error": f"Unknown tool: {function_name}"}
        
        # Coerce argument types (fix LLM returning strings for integers)
        function_args = self._coerce_argument_types(function_name, function_args)
        
        # Build payload
        payload = function_args.copy()
        
        # Add file_path for upload operations - override LLM's suggestion with actual file
        if function_name == "upload_evidence" or function_name == "fetch_evidence":
            if file_path:
                payload["file_path"] = file_path
                logger.info(f"Using actual file path for upload: {file_path}")
            elif "file_path" in payload and not payload["file_path"].startswith("/app/storage"):
                # LLM provided relative path, make it absolute
                logger.warning(f"LLM provided relative path: {payload['file_path']}, need actual file")
        
        # Add current user ID
        payload["current_user_id"] = current_user.get("id")
        
        # Generate title and description for the task
        title_map = {
            "upload_evidence": "Upload Evidence Document",
            "fetch_evidence": "Fetch Evidence",
            "analyze_compliance": "Analyze Compliance",
            "generate_report": "Generate Compliance Report",
            "submit_for_review": "Submit for Review"
        }
        
        title = title_map.get(function_name, "AI Assistant Task")
        description = f"Task created by AI Assistant: {function_name}"
        
        # Create and execute task
        from api.src.models import AgentTask
        from api.src.workers.task_worker import get_worker
        
        task = AgentTask(
            task_type=task_type,
            status="pending",
            title=title,
            description=description,
            payload=payload,
            created_by=current_user.get("id")
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Created task {task.id} for tool {function_name}")
        
        # For now, return task creation confirmation
        # Worker will execute in background
        return {
            "task_id": task.id,
            "task_type": task_type,
            "status": "created",
            "message": f"Task {task.id} created successfully"
        }
