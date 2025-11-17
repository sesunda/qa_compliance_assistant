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
    
    # Tool complexity configuration for dynamic LLM parameters
    TOOL_COMPLEXITY = {
        "upload_evidence": {"temperature": 0.2, "max_tokens": 400},
        "search_documents": {"temperature": 0.3, "max_tokens": 800},  # RAG needs more space
        "analyze_evidence": {"temperature": 0.2, "max_tokens": 600},
        "analyze_evidence_rag": {"temperature": 0.2, "max_tokens": 600},
        "submit_for_review": {"temperature": 0.1, "max_tokens": 300},
        "submit_evidence_for_review": {"temperature": 0.1, "max_tokens": 300},
        "request_evidence_upload": {"temperature": 0.2, "max_tokens": 400},
        "suggest_related_controls": {"temperature": 0.3, "max_tokens": 700},
        "fetch_evidence": {"temperature": 0.2, "max_tokens": 500},
        "mcp_fetch_evidence": {"temperature": 0.2, "max_tokens": 500},
        "mcp_analyze_compliance": {"temperature": 0.3, "max_tokens": 700},
        "list_projects": {"temperature": 0.2, "max_tokens": 500},
        # Default for unknown tools
        "default": {"temperature": 0.2, "max_tokens": 500}
    }
    
    def __init__(self):
        # Detect which provider to use (default to github for reliable tool calling)
        self.provider = os.getenv("LLM_PROVIDER", "github")  # github, groq, openai
        
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
            
        else:  # groq
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            # Use llama-3.3-70b-versatile - Production model with tool use support
            self.model = "llama-3.3-70b-versatile"
            logger.info(f"Using Groq with {self.model}")
        
        # Define ALL tools (will be filtered by role at runtime)
        self.all_tools = [
            {
                "type": "function",
                "function": {
                    "name": "upload_evidence",
                    "description": "Upload compliance evidence document for a control. ONLY call this tool when: (1) User HAS explicitly provided title, description, and evidence_type, (2) User HAS attached a file or provided file_path, (3) User HAS confirmed to proceed. DO NOT call with placeholder values like 'path_to_your_file' or default descriptions. If user just says 'upload evidence' without details, ASK for details instead of calling this tool.",
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
                            "title": {
                                "type": "string",
                                "description": "Specific, descriptive title for the evidence (e.g., 'MFA Policy v2.1', 'Access Control Audit Report Q4 2025')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the evidence"
                            },
                            "evidence_type": {
                                "type": "string",
                                "enum": ["policy_document", "audit_report", "configuration_screenshot", "log_file", "certificate", "procedure", "test_result"],
                                "description": "Type of evidence: policy_document, audit_report, configuration_screenshot, log_file, certificate, procedure, or test_result"
                            }
                        },
                        "required": ["file_path", "title", "evidence_type"]
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
                    "name": "request_evidence_upload",
                    "description": "Request evidence upload from analyst when NO file is attached. Creates a pending evidence record as placeholder. User must upload file separately. Use ONLY when user has NOT attached a file in chat. If file IS attached, use upload_evidence instead. After calling this tool successfully, DO NOT call it again even if user says 'yes' - the upload request is already created.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "integer",
                                "description": "Control ID this evidence relates to (required)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Brief title for the evidence (e.g., 'Access Control Policy Document')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of what evidence will be provided"
                            },
                            "evidence_type": {
                                "type": "string",
                                "enum": [
                                    "policy_document",
                                    "procedure", 
                                    "audit_report",
                                    "configuration_screenshot",
                                    "log_file",
                                    "certificate",
                                    "test_result",
                                    "document",
                                    "screenshot",
                                    "configuration",
                                    "log",
                                    "report",
                                    "other"
                                ],
                                "description": "Type of evidence - choose most specific type that matches",
                                "default": "document"
                            }
                        },
                        "required": ["control_id", "title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_evidence",
                    "description": "Analyze uploaded evidence against control requirements using RAG. Validates if evidence satisfies control acceptance criteria and suggests improvements. Use after evidence is uploaded to provide intelligent feedback.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "integer",
                                "description": "Evidence ID to analyze (required)"
                            },
                            "control_id": {
                                "type": "integer",
                                "description": "Control ID the evidence relates to (optional, can be inferred from evidence)"
                            }
                        },
                        "required": ["evidence_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "suggest_related_controls",
                    "description": "Suggest other controls that uploaded evidence might apply to using Graph RAG. Identifies related controls in the same domain or with similar requirements. Use to help analyst reuse evidence across multiple controls.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "integer",
                                "description": "Evidence ID to analyze (required)"
                            },
                            "control_id": {
                                "type": "integer",
                                "description": "Primary control ID (required)"
                            },
                            "max_suggestions": {
                                "type": "integer",
                                "description": "Maximum number of suggestions to return",
                                "default": 5
                            }
                        },
                        "required": ["evidence_id", "control_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "submit_evidence_for_review",
                    "description": "Submit evidence for auditor review and approval. Updates evidence status from 'pending' to 'under_review'. Use when analyst confirms they want to submit evidence after reviewing AI analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "integer",
                                "description": "Evidence ID to submit (required)"
                            },
                            "comments": {
                                "type": "string",
                                "description": "Optional comments for the auditor"
                            }
                        },
                        "required": ["evidence_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_project",
                    "description": "Create a new compliance or security project. Use when auditor wants to set up a new project for IM8 controls, security audit, risk assessment, etc. IMPORTANT: After successful creation, you MUST explicitly tell the user the project_id in your response (e.g., 'Project created successfully with ID: 11').",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Project name (required). Example: 'Health Sciences IM8 Compliance 2025'"
                            },
                            "description": {
                                "type": "string",
                                "description": "Project description. Example: 'Annual IM8 compliance assessment for Health Sciences division'"
                            },
                            "project_type": {
                                "type": "string",
                                "enum": ["compliance_assessment", "security_audit", "risk_management", "penetration_test"],
                                "description": "Type of project (default: compliance_assessment)"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Project start date in YYYY-MM-DD format. Example: '2025-01-15'"
                            }
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_projects",
                    "description": "List all projects for the user's agency. Shows project ID, name, type, status, and control count. Use when user asks to see projects, recent projects, available projects, or 'show me projects'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of recent projects to return (default: 10)",
                                "default": 10
                            },
                            "status": {
                                "type": "string",
                                "enum": ["active", "completed", "archived", "all"],
                                "description": "Filter by project status (default: all)",
                                "default": "all"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_controls",
                    "description": "Create IM8 compliance controls for a project. IMPORTANT: Before calling this tool, you MUST ask the user which project_id to use. Never assume or guess the project_id. Use when auditor wants to set up IM8 controls by selecting domains (1-10). Creates multiple controls based on selected domains.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID to add controls to (REQUIRED - must ask user if not provided)"
                            },
                            "domains": {
                                "type": "array",
                                "items": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 10
                                },
                                "description": "IM8 domain numbers to include. Domains: 1=Identity/Access, 2=Awareness/Training, 3=Data Protection, 4=Incident Response, 5=IT Security Operations, 6=Network Security, 7=System Security, 8=Application Security, 9=Mobile Device, 10=Cloud Security"
                            },
                            "framework": {
                                "type": "string",
                                "enum": ["IM8", "NIST", "ISO27001"],
                                "description": "Compliance framework (default: IM8)"
                            }
                        },
                        "required": ["project_id", "domains"]
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
        
        # Streamlined base system prompt
        self.base_system_prompt = """You are an AI compliance assistant for Singapore IM8 compliance tasks.

Available Controls: 1 (Test), 3 (Network segmentation), 4 (Data encryption), 5 (MFA for privileged accounts)

ROLE CAPABILITIES:
- ANALYST: Upload evidence, analyze compliance, submit for review
- AUDITOR: Create controls/projects, review evidence, generate reports  
- VIEWER: Read-only access

CORE RULES:
1. Ask ONE question at a time
2. Only ask if information is missing AND cannot be obtained from context or tools
3. Stay focused on user's current request
4. Be concise - use minimum words needed
5. Execute tools immediately when all required fields are collected"""
    
    def _get_tools_for_role(self, user_role: str) -> list:
        """
        Filter tools based on user role to enforce RBAC
        
        Role Permissions:
        - auditor: Can create projects, create controls, generate reports (NO evidence upload)
        - analyst: Can upload evidence, submit for review (NO project/control creation)
        - viewer: Can only view (NO tool access)
        - super_admin: Full access to all tools
        """
        # Define role-specific tool permissions
        AUDITOR_ONLY_TOOLS = ['create_project', 'create_controls']
        ANALYST_ONLY_TOOLS = [
            'upload_evidence', 
            'submit_for_review', 
            'request_evidence_upload', 
            'submit_evidence_for_review'
        ]
        EVIDENCE_QUERY_TOOLS = [
            'analyze_evidence',  # Auditors can query evidence analysis
            'suggest_related_controls'  # Auditors can use Graph RAG for relationships
        ]
        COMMON_TOOLS = ['mcp_fetch_evidence', 'generate_report', 'search_documents', 'list_projects']
        
        user_role_lower = user_role.lower()
        
        if user_role_lower == 'super_admin':
            # Super admin has access to all tools
            logger.info(f"Role '{user_role}': Granting access to ALL tools")
            return self.all_tools
        
        elif user_role_lower == 'auditor':
            # Auditor: project/control creation + evidence queries + common tools (NO evidence upload)
            allowed_tools = AUDITOR_ONLY_TOOLS + EVIDENCE_QUERY_TOOLS + COMMON_TOOLS
            filtered_tools = [t for t in self.all_tools if t['function']['name'] in allowed_tools]
            logger.info(f"Role '{user_role}': Granting access to {len(filtered_tools)} tools: {allowed_tools}")
            return filtered_tools
        
        elif user_role_lower == 'analyst':
            # Analyst: evidence upload/submit + evidence queries + common tools (NO project/control creation)
            allowed_tools = ANALYST_ONLY_TOOLS + EVIDENCE_QUERY_TOOLS + COMMON_TOOLS
            filtered_tools = [t for t in self.all_tools if t['function']['name'] in allowed_tools]
            logger.info(f"Role '{user_role}': Granting access to {len(filtered_tools)} tools: {allowed_tools}")
            return filtered_tools
        
        else:
            # Viewer or unknown: No tool access
            logger.info(f"Role '{user_role}': NO tool access granted (read-only)")
            return []
    
    def _build_role_specific_prompt(self, user_role: str) -> str:
        """Build concise role-specific system prompt"""
        role_prompts = {
            "auditor": """

AUDITOR ACTIONS:
- View available projects (list_projects tool)
- Create IM8 controls for projects (your agency only)
- Review evidence submissions
- Generate compliance reports
- Query evidence relationships

When creating controls: Ask for project name, then execute create_controls tool.
""",
            
            "analyst": """

ANALYST ACTIONS:
- View available projects (list_projects tool)
- Upload evidence for controls (your agency only)
- Analyze compliance status
- Submit evidence for review

EVIDENCE UPLOAD - STRICT SEQUENCE:
Ask for these fields IN ORDER, ONE at a time:
1. Control ID → "Which control? (1, 3, 4, or 5)"
2. Title → "What is the title?"
3. Description → "What does this demonstrate?"
4. Type → "Type: policy_document, audit_report, configuration_screenshot, log_file, certificate, procedure, or test_result"
5. File → "Please attach the file"

Once all 5 collected → Execute upload_evidence tool immediately.

ALLOWED QUESTIONS (Use these exact formats):
- "Which control? (1, 3, 4, or 5)"
- "What is the title?"
- "What does this demonstrate?"
- "Type: [list types]"
- "Please attach the file"

FORBIDDEN:
❌ Ask about agency (already known from context)
❌ Ask multiple questions in one response
❌ Explain IM8 framework unless asked
❌ Ask optional metadata before required fields
❌ Offer alternatives before collecting basics

EXAMPLES:
✅ User: "Upload evidence for Control 5"
   AI: "What is the title?"

✅ User: "Title: MFA Policy v2.1"  
   AI: "What does this demonstrate?"

❌ User: "Upload evidence"
   AI: "Let me explain the IM8 workflow..." [NO - just ask for control]
""",
            
            "viewer": """

VIEWER ACTIONS:
- View compliance status
- View reports
- No tool access (read-only)

Answer questions about current compliance state using available data.
"""
        }
        
        return self.base_system_prompt + role_prompts.get(user_role.lower(), "")
    
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
            
            # Get user's agency name
            from api.src.models import Agency
            agency_name = "Unknown Agency"
            if current_user.get("agency_id"):
                agency = db.query(Agency).filter(Agency.id == current_user["agency_id"]).first()
                if agency:
                    agency_name = agency.name
            
            # Build role-specific system prompt with user context
            user_role = current_user.get("role", "viewer")
            system_prompt = self._build_role_specific_prompt(user_role)
            
            # Add user context to system prompt
            user_context = f"""

CURRENT USER CONTEXT:
- Username: {current_user.get('username', 'Unknown')}
- Role: {user_role.upper()}
- Agency: {agency_name} (ID: {current_user.get('agency_id', 'N/A')})

You are currently assisting {current_user.get('username', 'the user')} from {agency_name}.
"""
            system_prompt += user_context
            
            # Get role-specific tools (RBAC enforcement)
            filtered_tools = self._get_tools_for_role(user_role)
            
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
            
            # Call Groq with tool calling (using filtered tools)
            # Use tight constraints for initial tool decision
            logger.info(f"Calling Groq LLM for session {session_id} with {len(filtered_tools)} role-filtered tools")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=filtered_tools if filtered_tools else None,  # Pass None if no tools
                tool_choice="auto" if filtered_tools else "none",
                max_tokens=150,  # Reduced: just enough to decide tool calls
                temperature=0.2
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
                    elif function_name == "list_projects":
                        # List projects
                        tool_result = await self.handle_list_projects(
                            user_id=current_user.id,
                            limit=function_args.get("limit", 10),
                            status=function_args.get("status", "all"),
                            db=db
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
                
                # Get final response with dynamic parameters based on tool complexity
                # Determine parameters based on first tool called
                tool_name = tool_calls[0].function.name
                params = self.TOOL_COMPLEXITY.get(tool_name, self.TOOL_COMPLEXITY["default"])
                logger.info(f"Using dynamic params for {tool_name}: temp={params['temperature']}, max_tokens={params['max_tokens']}")
                
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=params["max_tokens"],
                    temperature=params["temperature"]
                )
                
                final_answer = final_response.choices[0].message.content
            else:
                # No tool calls, just use assistant's response
                final_answer = assistant_message.content
            
            # Detect rich UI opportunities
            conversation_history = conversation_manager.get_conversation_history(session_id)
            rich_ui = self._detect_rich_ui_opportunity(final_answer, conversation_history)
            
            # Save assistant response to conversation
            conversation_manager.add_message(
                session_id,
                role="assistant",
                content=final_answer,
                tool_calls=tool_results if tool_results else None
            )
            
            result = {
                "answer": final_answer,
                "tool_calls": tool_results,
                "session_id": session_id
            }
            
            # Add rich UI component if detected
            if rich_ui:
                result["rich_ui"] = rich_ui
                logger.info(f"Rich UI component detected: {rich_ui['type']} - {rich_ui.get('form_type', 'unknown')}")
            
            return result
            
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
    
    async def handle_list_projects(
        self,
        user_id: int,
        limit: int = 10,
        status: str = "all",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        List projects for the user's agency
        
        Args:
            user_id: Current user ID
            limit: Number of projects to return
            status: Filter by status (active, completed, archived, all)
            db: Database session
            
        Returns:
            List of projects with details
        """
        try:
            from sqlalchemy import text
            
            logger.info(f"Listing projects for user {user_id}, status={status}, limit={limit}")
            
            # Get user's agency_id
            user_query = text("SELECT agency_id FROM users WHERE id = :user_id")
            user_result = db.execute(user_query, {"user_id": user_id})
            user_row = user_result.fetchone()
            
            if not user_row:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            agency_id = user_row[0]
            
            # Build query
            query = """
                SELECT 
                    p.id,
                    p.name,
                    p.description,
                    p.project_type,
                    p.status,
                    p.created_at,
                    COUNT(DISTINCT c.id) as control_count
                FROM projects p
                LEFT JOIN controls c ON c.project_id = p.id
                WHERE p.agency_id = :agency_id
            """
            
            params = {"agency_id": agency_id, "limit": limit}
            
            # Add status filter
            if status != "all":
                query += " AND p.status = :status"
                params["status"] = status
            
            query += """
                GROUP BY p.id, p.name, p.description, p.project_type, p.status, p.created_at
                ORDER BY p.created_at DESC
                LIMIT :limit
            """
            
            result = db.execute(text(query), params)
            
            # Format results
            projects = []
            for row in result:
                projects.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "project_type": row[3],
                    "status": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "control_count": row[6]
                })
            
            return {
                "success": True,
                "projects": projects,
                "count": len(projects)
            }
            
        except Exception as e:
            logger.error(f"List projects failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
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
    
    def _validate_tool_parameters(
        self,
        function_name: str,
        args: Dict[str, Any],
        db: Session,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate tool parameters BEFORE task creation
        Prevents invalid tasks from being created
        
        Returns:
            Dict with 'valid': bool, 'error': str, 'suggestion': str
        """
        # Validation for create_project
        if function_name == "create_project":
            # Check required fields
            if not args.get("name") or not args.get("name").strip():
                return {
                    "valid": False,
                    "error": "Project name is required and cannot be empty",
                    "suggestion": "Please provide a project name"
                }
            
            # Validate project_type enum
            valid_types = ["compliance_assessment", "security_audit", "risk_management", "penetration_test"]
            project_type = args.get("project_type", "compliance_assessment")
            if project_type not in valid_types:
                return {
                    "valid": False,
                    "error": f"Invalid project type: '{project_type}'. Must be one of: {', '.join(valid_types)}",
                    "suggestion": f"Please choose from: {', '.join(valid_types)}"
                }
            
            # Validate start_date format if provided
            if args.get("start_date"):
                try:
                    from datetime import datetime
                    datetime.strptime(args["start_date"], "%Y-%m-%d")
                except ValueError:
                    return {
                        "valid": False,
                        "error": f"Invalid start date format: '{args['start_date']}'. Expected YYYY-MM-DD",
                        "suggestion": "Please use date format: YYYY-MM-DD (e.g., 2025-12-01)"
                    }
            
            # Validate name length
            if len(args["name"]) > 255:
                return {
                    "valid": False,
                    "error": f"Project name too long ({len(args['name'])} characters). Maximum 255 characters",
                    "suggestion": "Please shorten the project name"
                }
        
        # Validation for create_controls
        elif function_name == "create_controls":
            # Check project_id
            if not args.get("project_id"):
                return {
                    "valid": False,
                    "error": "Missing required parameter: project_id",
                    "suggestion": "I need to know which project to add these controls to. Let me check your existing projects first. Please hold on."
                }
            
            # Check project exists and belongs to user's agency
            from api.src.models import Project
            project = db.query(Project).filter(Project.id == args["project_id"]).first()
            if not project:
                return {
                    "valid": False,
                    "error": f"Project ID {args['project_id']} not found",
                    "suggestion": "Please provide a valid project ID"
                }
            if project.agency_id != current_user.get("agency_id"):
                return {
                    "valid": False,
                    "error": f"Access denied: Project {args['project_id']} belongs to another agency",
                    "suggestion": "You can only add controls to your agency's projects"
                }
            
            # Check domains array
            if not args.get("domains") or not isinstance(args["domains"], list):
                return {
                    "valid": False,
                    "error": "Domains array is required",
                    "suggestion": "Please specify which IM8 domains to include (e.g., [1, 2, 3])"
                }
            
            # Validate domain numbers (1-10)
            invalid_domains = [d for d in args["domains"] if not isinstance(d, int) or d < 1 or d > 10]
            if invalid_domains:
                return {
                    "valid": False,
                    "error": f"Invalid domain numbers: {invalid_domains}. Must be integers between 1 and 10",
                    "suggestion": "IM8 domains are numbered 1-10. Please use valid domain numbers"
                }
        
        # Validation for upload_evidence, request_evidence_upload, fetch_evidence
        elif function_name in ["upload_evidence", "request_evidence_upload", "fetch_evidence"]:
            # CRITICAL: Prevent placeholder/default values for upload_evidence
            if function_name == "upload_evidence":
                # Check for placeholder file paths
                file_path = args.get("file_path", "")
                if not file_path or file_path in ["path_to_your_file", "path/to/file", "", "file_path"]:
                    return {
                        "valid": False,
                        "error": "Invalid or placeholder file_path provided",
                        "suggestion": "User must attach a file first. Ask user to attach the evidence file before calling upload_evidence."
                    }
                
                # Check for default/placeholder titles
                title = args.get("title", "")
                if title in ["Evidence document", "Document", "", "evidence", "file"]:
                    return {
                        "valid": False,
                        "error": "Generic or placeholder title provided",
                        "suggestion": "Ask user for a specific, descriptive title for the evidence (e.g., 'MFA Policy v2.1', 'Access Control Audit Report Q4')"
                    }
                
                # Require explicit evidence_type
                if not args.get("evidence_type"):
                    return {
                        "valid": False,
                        "error": "Evidence type is required",
                        "suggestion": "Ask user to specify evidence type: policy_document, audit_report, configuration_screenshot, log_file, certificate, procedure, or test_result"
                    }
            
            # Check control_id exists and belongs to user's agency
            if args.get("control_id"):
                from api.src.models import Control
                control = db.query(Control).filter(Control.id == args["control_id"]).first()
                if not control:
                    return {
                        "valid": False,
                        "error": f"Control ID {args['control_id']} not found",
                        "suggestion": "Please provide a valid control ID from your projects"
                    }
                if control.agency_id != current_user.get("agency_id"):
                    return {
                        "valid": False,
                        "error": f"Access denied: Control {args['control_id']} belongs to another agency",
                        "suggestion": "You can only upload evidence to your agency's controls"
                    }
        
        # Validation for submit_for_review
        elif function_name == "submit_for_review":
            if not args.get("evidence_id"):
                return {
                    "valid": False,
                    "error": "Evidence ID is required",
                    "suggestion": "Please provide the evidence ID to submit for review"
                }
            
            # Check evidence exists and belongs to user's agency
            from api.src.models import Evidence
            evidence = db.query(Evidence).filter(Evidence.id == args["evidence_id"]).first()
            if not evidence:
                return {
                    "valid": False,
                    "error": f"Evidence ID {args['evidence_id']} not found",
                    "suggestion": "Please provide a valid evidence ID"
                }
            if evidence.agency_id != current_user.get("agency_id"):
                return {
                    "valid": False,
                    "error": f"Access denied: Evidence {args['evidence_id']} belongs to another agency",
                    "suggestion": "You can only submit your agency's evidence"
                }
        
        # Validation for generate_report
        elif function_name == "generate_report":
            if args.get("project_id"):
                from api.src.models import Project
                project = db.query(Project).filter(Project.id == args["project_id"]).first()
                if not project:
                    return {
                        "valid": False,
                        "error": f"Project ID {args['project_id']} not found",
                        "suggestion": "Please provide a valid project ID"
                    }
                if project.agency_id != current_user.get("agency_id"):
                    return {
                        "valid": False,
                        "error": f"Access denied: Project {args['project_id']} belongs to another agency",
                        "suggestion": "You can only generate reports for your agency's projects"
                    }
        
        # All validations passed
        return {"valid": True}
    
    def _coerce_argument_types(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce argument types to match expected schema (fixes LLM string->int issues)"""
        # Define integer fields for each function
        integer_fields = {
            "upload_evidence": ["control_id", "project_id"],
            "fetch_evidence": ["control_id", "project_id"],
            "analyze_compliance": ["control_id", "project_id"],
            "generate_report": ["project_id"],
            "submit_for_review": ["evidence_id"],
            "submit_evidence_for_review": ["evidence_id"],
            "request_evidence_upload": ["control_id"],
            "create_project": ["agency_id"],
            "create_controls": ["project_id"]
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
    
    def _detect_rich_ui_opportunity(self, message: str, conversation_history: list) -> Optional[Dict[str, Any]]:
        """
        Detect if AI response should trigger rich UI component
        
        DISABLED: Using text-based conversational interface only.
        Rich UI frontend components are not implemented.
        
        Returns:
            None (Rich UI disabled)
        """
        # DISABLED: Text-based interface is superior for this use case
        return None
        
        # Original detection logic commented out for future reference
        message_lower = message.lower()
        
        # Detect project creation form request
        if any(phrase in message_lower for phrase in [
            "let's create a new project",
            "please fill in the details",
            "i'll need some details",
            "project name",
            "what should we call this project"
        ]):
            return {
                "type": "form",
                "form_type": "create_project",
                "title": "Create New Project",
                "fields": [
                    {
                        "name": "name",
                        "label": "Project Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "e.g., Health Sciences Compliance 2025"
                    },
                    {
                        "name": "description",
                        "label": "Description",
                        "type": "textarea",
                        "required": False,
                        "placeholder": "Brief description of the project"
                    },
                    {
                        "name": "project_type",
                        "label": "Project Type",
                        "type": "select",
                        "required": False,
                        "default": "compliance_assessment",
                        "options": [
                            {"value": "compliance_assessment", "label": "Compliance Assessment"},
                            {"value": "security_audit", "label": "Security Audit"},
                            {"value": "risk_management", "label": "Risk Management"},
                            {"value": "penetration_test", "label": "Penetration Test"}
                        ]
                    },
                    {
                        "name": "start_date",
                        "label": "Start Date",
                        "type": "date",
                        "required": False,
                        "placeholder": "YYYY-MM-DD"
                    }
                ],
                "submit_label": "Create Project"
            }
        
        # Detect IM8 domain selection request
        if any(phrase in message_lower for phrase in [
            "which im8 domains",
            "im8 framework has 10 domains",
            "select im8 domains",
            "im8-01:",
            "im8-02:"
        ]):
            return {
                "type": "checkbox_grid",
                "form_type": "select_im8_domains",
                "title": "Select IM8 Domains",
                "items": [
                    {"value": "IM8-01", "label": "IM8-01: Information Security Governance", "count": 3},
                    {"value": "IM8-02", "label": "IM8-02: Network Security", "count": 3},
                    {"value": "IM8-03", "label": "IM8-03: Data Protection", "count": 3},
                    {"value": "IM8-04", "label": "IM8-04: Vulnerability & Patch Management", "count": 3},
                    {"value": "IM8-05", "label": "IM8-05: Secure Software Development", "count": 3},
                    {"value": "IM8-06", "label": "IM8-06: Security Monitoring & Logging", "count": 3},
                    {"value": "IM8-07", "label": "IM8-07: Third-Party Risk Management", "count": 3},
                    {"value": "IM8-08", "label": "IM8-08: Change & Configuration Management", "count": 3},
                    {"value": "IM8-09", "label": "IM8-09: Risk Assessment & Compliance", "count": 3},
                    {"value": "IM8-10", "label": "IM8-10: Digital Service Standards", "count": 3}
                ],
                "select_all_label": "Select All (30 controls)",
                "submit_label": "Confirm Selection"
            }
        
        # Detect evidence upload request
        if any(phrase in message_lower for phrase in [
            "upload evidence",
            "please upload",
            "attach evidence",
            "upload document"
        ]):
            return {
                "type": "form",
                "form_type": "upload_evidence",
                "title": "Upload Evidence",
                "fields": [
                    {
                        "name": "file",
                        "label": "Evidence Document",
                        "type": "file",
                        "required": True,
                        "accept": ".pdf,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg"
                    },
                    {
                        "name": "control_id",
                        "label": "Control",
                        "type": "select",
                        "required": True,
                        "options": []  # Will be populated from user's controls
                    },
                    {
                        "name": "description",
                        "label": "Description",
                        "type": "textarea",
                        "required": False,
                        "placeholder": "Describe the evidence being uploaded"
                    }
                ],
                "submit_label": "Upload Evidence"
            }
        
        return None
    
    async def _execute_tool(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        db: Session,
        current_user: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a tool via AI Task Orchestrator"""
        
        # RBAC: Check role permissions before execution
        user_role = current_user.get("role", "").lower()
        
        # Define role-tool permissions
        AUDITOR_ONLY_TOOLS = ['create_project', 'create_controls']
        AUDITOR_ONLY_TOOLS = ['create_project', 'create_controls']
        ANALYST_ONLY_TOOLS = [
            'upload_evidence', 
            'submit_for_review', 
            'request_evidence_upload', 
            'submit_evidence_for_review'
        ]
        
        # Enforce role-based tool access
        if function_name in AUDITOR_ONLY_TOOLS:
            if user_role not in ['auditor', 'super_admin']:
                logger.error(f"RBAC violation: User role '{user_role}' attempted to use auditor-only tool '{function_name}'")
                return {
                    "error": "Access denied",
                    "status": "forbidden",
                    "message": f"Only auditors can use '{function_name}'. Your role: {user_role}. Auditors set up controls and projects."
                }
        
        if function_name in ANALYST_ONLY_TOOLS:
            if user_role not in ['analyst', 'super_admin']:
                logger.error(f"RBAC violation: User role '{user_role}' attempted to use analyst tool '{function_name}'")
                return {
                    "error": "Access denied",
                    "status": "forbidden",
                    "message": f"Only analysts can use '{function_name}'. Your role: {user_role}. Analysts upload and manage evidence documents. Auditors should use the Evidence page for review/approval."
                }
        
        # VALIDATION: Check parameters before creating task
        validation_result = self._validate_tool_parameters(function_name, function_args, db, current_user)
        if not validation_result["valid"]:
            logger.error(f"Tool validation failed for {function_name}: {validation_result['error']}")
            return {
                "error": validation_result["error"],
                "status": "validation_failed",
                "suggestion": validation_result.get("suggestion", "Please check your inputs and try again.")
            }
        
        # Map tool to task type
        task_type_map = {
            "create_project": "create_project",
            "create_controls": "create_controls",
            "upload_evidence": "upload_evidence",  # Direct upload handler (no MCP)
            "fetch_evidence": "fetch_evidence",  # MCP-based fetch
            "analyze_compliance": "analyze_compliance",
            "generate_report": "generate_report",
            "submit_for_review": "submit_for_review",
            "request_evidence_upload": "request_evidence_upload",
            "analyze_evidence": "analyze_evidence_rag",  # Use RAG version
            "suggest_related_controls": "suggest_related_controls",
            "submit_evidence_for_review": "submit_evidence_for_review"
        }
        
        task_type = task_type_map.get(function_name)
        if not task_type:
            return {"error": f"Unknown tool: {function_name}"}
        
        # Coerce argument types (fix LLM returning strings for integers)
        function_args = self._coerce_argument_types(function_name, function_args)
        
        # Build payload
        payload = function_args.copy()
        
        # Convert domains array to domain_areas for create_controls
        if function_name == "create_controls" and "domains" in payload:
            # Convert [1, 2, 3] to ["IM8-01", "IM8-02", "IM8-03"]
            domains = payload.pop("domains")
            payload["domain_areas"] = [f"IM8-{d:02d}" for d in domains]
            # Calculate count (3 controls per domain for IM8)
            payload["count"] = len(domains) * 3
            logger.info(f"Converted domains {domains} to domain_areas {payload['domain_areas']}, count={payload['count']}")
        
        # Add file_path for upload operations - override LLM's suggestion with actual file
        if function_name == "upload_evidence" or function_name == "fetch_evidence":
            if file_path:
                payload["file_path"] = file_path
                logger.info(f"Using actual file path for upload: {file_path}")
            elif "file_path" in payload and not payload["file_path"].startswith("/app/storage"):
                # LLM provided relative path, make it absolute
                logger.warning(f"LLM provided relative path: {payload['file_path']}, need actual file")
        
        # Add current user ID and agency_id
        payload["current_user_id"] = current_user.get("id")
        payload["agency_id"] = current_user.get("agency_id")
        
        # Generate title and description for the task
        title_map = {
            "create_project": "Create New Project",
            "create_controls": "Create IM8 Controls",
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
        import time
        
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
        
        # Send notification to task worker for immediate processing
        try:
            from sqlalchemy import text
            db.execute(text(f"NOTIFY new_task, '{task.id}'"))
            db.commit()
            logger.info(f"Sent NOTIFY for task {task.id}")
        except Exception as e:
            logger.warning(f"Failed to send NOTIFY for task {task.id}: {e}")
        
        logger.info(f"Created task {task.id} for tool {function_name}")
        
        # Wait for task to complete (max 60 seconds for file operations)
        max_wait = 60
        start_time = time.time()
        while (time.time() - start_time) < max_wait:
            db.refresh(task)
            if task.status in ['completed', 'failed', 'error']:
                break
            time.sleep(0.5)  # Poll every 500ms
        
        # Final refresh to ensure we have latest result
        db.refresh(task)
        
        # Log task completion status
        logger.info(f"Task {task.id} final status: {task.status}, result: {task.result}")
        
        # Return task result with actual data
        result = {
            "task_id": task.id,
            "task_type": task_type,
            "status": task.status,
            "message": f"Task {task.id} {task.status}"
        }
        
        # CRITICAL: Include actual result data from task (includes evidence_ids for uploads)
        if task.result:
            if isinstance(task.result, dict):
                result.update(task.result)
                logger.info(f"Task {task.id} merged result: {result}")
                
                # CRITICAL: For evidence uploads, explicitly log the evidence IDs to prevent LLM hallucination
                if function_name in ("upload_evidence", "fetch_evidence") and "evidence_ids" in result:
                    evidence_ids = result["evidence_ids"]
                    logger.warning(f"⚠️ EVIDENCE UPLOAD RESULT - Task {task.id}: Created Evidence IDs: {evidence_ids} - LLM MUST use these exact IDs, NOT make up numbers!")
                    # Add redundant field to make it crystal clear
                    result["CREATED_EVIDENCE_ID"] = evidence_ids[0] if evidence_ids else None
                    result["TOTAL_EVIDENCE_COUNT"] = len(evidence_ids)
            else:
                logger.warning(f"Task {task.id} result is not a dict: {type(task.result)}")
        else:
            logger.warning(f"Task {task.id} has no result data (status={task.status})")
        
        # If still pending and this is upload_evidence, warn about timeout
        if task.status == 'pending' and function_name == 'upload_evidence':
            logger.error(f"Task {task.id} upload_evidence still pending after {max_wait}s - evidence_ids not available")
            result["message"] = f"Task {task.id} timed out - evidence may not be ready"
        
        return result


