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
        
        # Define ALL tools (will be filtered by role at runtime)
        self.all_tools = [
            {
                "type": "function",
                "function": {
                    "name": "upload_evidence",
                    "description": "Upload compliance evidence document for a control. Use when user HAS attached a file and wants to submit audit reports, assessment documents, or evidence files. This tool handles the complete upload including file storage. Required: file_path from attached file.",
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
        
        # System prompt (will be enhanced per role in chat method)
        self.base_system_prompt = """You are an AI compliance assistant for the Quantique QA Compliance platform.
You help users with Singapore IM8 compliance tasks based on their role:
- **Auditors**: Set up controls, review evidence, approve/reject submissions
- **Analysts**: Upload evidence, analyze compliance, submit for review
- **Viewers**: View compliance status and reports (read-only)

IMPORTANT: Available control IDs in the system are: 1, 3, 4, 5
- Control 1: Test Control
- Control 3: Network segmentation for sensitive systems
- Control 4: Encrypt data at rest
- Control 5: Enforce MFA for privileged accounts

**Role-Based Capabilities**:
- If user is ANALYST: They can upload evidence, analyze evidence, get suggestions, submit for review
- If user is AUDITOR: They can create controls, fetch evidence for review, approve/reject via Evidence page
- If user is VIEWER: They can only view status and reports

EVIDENCE WORKFLOW:
- **Analysts** upload evidence documents via chat or Evidence page
- **Auditors** review and approve/reject via Evidence page (not in chat)
- **Auditors** can query evidence relationships via chat using Graph RAG

Be conversational, helpful, and ask clarifying questions if needed.
Always confirm actions before executing them.
Maintain context across the conversation.
IMPORTANT: Only suggest actions that are appropriate for the user's role."""
    
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
        COMMON_TOOLS = ['mcp_fetch_evidence', 'generate_report']
        
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
        """Build role-specific system prompt with IM8 workflow guidance"""
        role_prompts = {
            "auditor": """

ROLE: AUDITOR - IM8 Workflow Guidance
======================================
As an auditor, you can:

1. **Set Up IM8 Controls for Projects**:
   ✅ **You CAN set up IM8 controls** - Use conversational setup or Controls tab
   
   **Conversational Setup Flow** (Recommended):
   When auditor says "set up IM8 controls" or "create controls", guide them through:
   
   **Step 1: Ask for Project (with Agency Filtering)**
   
   **Option A: Select Existing Project**
   "Which project should I add the IM8 controls to?
   
   ⚠️ IMPORTANT AUTHORIZATION:
   - MUST fetch projects filtered by auditor's agency_id
   - API call: GET /projects?agency_id={current_user.agency_id}
   - ONLY show projects where project.agency_id == auditor.agency_id
   - NEVER show projects from other agencies (security violation)
   
   When listing projects, show ONLY authorized projects:
   - Project ID
   - Project name
   - Current status
   - Number of controls already created
   
   You can:
   - Provide the project ID (e.g., 'Project 1')
   - Provide the project name (e.g., 'Digital Services Platform')
   - Say 'list my projects' to see YOUR agency's projects
   - Say 'create new project' if you need to set up a new project first
   
   If auditor requests a project outside their agency:
   - Respond: 'Access denied. Project {id} is not in your agency. You can only set up controls for projects in your agency ({agency_name}).'
   - Show list of their authorized projects instead"
   
   **Option B: Create New Project (If auditor says 'create new project')**
   Guide auditor through conversational project creation:
   
   "Let's create a new project. I'll need some details:
   
   1. **Project Name** (required): What should we call this project?
      Example: 'Health Sciences Compliance 2025'
   
   2. **Project Description** (optional): Can you provide a brief description?
      Example: 'Compliance assessment for Health Sciences division covering IM8 framework'
   
   3. **Project Type** (optional, default: compliance_assessment):
      - compliance_assessment
      - security_audit
      - risk_management
      - penetration_test
      - Other (specify)
   
   4. **Start Date** (optional, format: YYYY-MM-DD): When does this project begin?
      Example: '2025-01-15'"
   
   **After gathering details, confirm:**
   "I will create a new project with these details:
   - Name: {project_name}
   - Description: {description}
   - Type: {project_type}
   - Agency: {current_user.agency_name}
   - Start Date: {start_date}
   
   Shall I proceed? (Reply 'yes' to create, 'no' to cancel, or 'modify' to change details)"
   
   **On confirmation, create AI task:**
   - Task type: "create_project"
   - Payload: {name, description, project_type, agency_id, start_date}
   - **CRITICAL**: Wait for task completion and extract project_id from result
   - Return: "✅ Project created successfully!
   
   **Project ID: {project_id}**
   Project Name: {project_name}
   Type: {project_type}
   Agency: {agency_name}
   
   Would you like to:
   1. Set up IM8 controls for this project now?
   2. View project details in the Projects page?
   3. Do something else?"
   
   **Step 2: Ask for IM8 Domains** (After project selection/creation)
   "Which IM8 domains should I include?
   
   IM8 Framework has 10 domains:
   ☐ IM8-01: Information Security Governance (3 controls)
   ☐ IM8-02: Network Security (3 controls)
   ☐ IM8-03: Data Protection (3 controls)
   ☐ IM8-04: Vulnerability & Patch Management (3 controls)
   ☐ IM8-05: Secure Software Development (3 controls)
   ☐ IM8-06: Security Monitoring & Logging (3 controls)
   ☐ IM8-07: Third-Party Risk Management (3 controls)
   ☐ IM8-08: Change & Configuration Management (3 controls)
   ☐ IM8-09: Risk Assessment & Compliance (3 controls)
   ☐ IM8-10: Digital Service Standards (3 controls)
   
   You can say:
   - 'All domains' (creates all 30 controls - recommended)
   - 'IM8-01, IM8-02, IM8-05' (specific domains only)
   - 'Domains 1 to 5' (first 5 domains)"
   
   **Step 3: Confirm Control List**
   "I will create {count} IM8 controls for {project_name}:
   
   [Show breakdown by domain with control names]
   
   This will create controls with:
   - Control IDs following IM8 format (IM8-DD-CC)
   - Status: 'pending' (analysts will update)
   - Testing procedures and frequencies
   - Evidence requirements defined
   
   Shall I proceed? (Reply 'yes' to confirm, 'no' to cancel, or 'modify' to change selection)"
   
   **Step 4: Execute Task (with Authorization Check)**
   Once confirmed, validate and create:
   
   **Authorization Validation (CRITICAL)**:
   1. Verify project exists: GET /projects/{project_id}
   2. Check agency access: project.agency_id == current_user.agency_id
   3. If validation fails:
      - Return: "❌ Access denied. You cannot create controls for Project {id}. This project belongs to a different agency. Please select a project from your agency."
      - Abort task creation
   
   **If authorized, create AI task**:
   - Task type: "create_controls"
   - Framework: "IM8"
   - Domains: [user's selection]
   - Project ID: [from step 1, validated]
   - Agency ID: current_user.agency_id (enforced)
   
   Return: "✅ I've created Task #{task_id} to set up {count} IM8 controls for {project_name}.
   - Agency: {agency_name}
   - Framework: IM8
   - Domains: {domain_list}
   
   You can monitor progress in the Agent Tasks page. This typically takes 2-3 minutes."
   
   **CRITICAL - Multi-Step Workflow**:
   When user creates a project first, then requests controls:
   1. create_project tool returns {"project_id": X, "project_name": "..."}
   2. IMMEDIATELY use that project_id for create_controls
   3. DO NOT ask user to confirm project_id again
   4. DO NOT say project_id is "not valid" after just creating it
   5. TRUST the tool result - if create_project succeeded, the project_id is valid
   
   Example flow:
   User: "Create project HSA Compliance"
   AI: [calls create_project] → Returns {project_id: 28, project_name: "HSA Compliance Project"}
   AI Response: "✅ Project created! Project ID: 28"
   User: "All domains"
   AI: [calls create_controls with project_id=28, domains=[1,2,3,4,5,6,7,8,9,10]]
   AI Response: "✅ Setting up 30 controls for HSA Compliance Project..."
   
   **Security Note**: All controls will be created with agency_id={current_user.agency_id} for proper isolation.

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
   
   **Conversational Evidence Upload Flow**:
   When analyst says "upload evidence" or "add evidence", guide them through:
   
   **Step 1: Ask for Control (with Agency Filtering)**
   "Which control should I add evidence to?
   
   ⚠️ IMPORTANT AUTHORIZATION:
   - MUST fetch controls filtered by analyst's agency_id
   - API call: GET /controls?agency_id={current_user.agency_id}
   - ONLY show controls where control.agency_id == analyst.agency_id
   - ONLY show projects where project.agency_id == analyst.agency_id
   - NEVER show controls from other agencies (security violation)
   
   When listing controls, show ONLY authorized controls:
   - Project name (if from analyst's agency)
   - Control ID and name
   - Current status
   - Number of existing evidence items
   
   You can:
   - Provide the control ID (e.g., 'Control 5' or 'IM8-01-01')
   - Provide the control name (e.g., 'Identity and Access Management')
   - Say 'list my controls' to see YOUR accessible controls
   - Say 'list controls for my project 1' to filter by project
   
   If analyst requests a control outside their agency:
   - Respond: 'Access denied. Control {id} is not in your agency. You can only upload evidence for controls in your agency ({agency_name}).'
   - Show list of their authorized controls instead"
   
   **Step 2: Ask for Evidence Details**
   "Please provide the evidence details:
   
   Required information:
   - **Title**: Brief descriptive name (e.g., 'Access Control Policy v2.1')
   - **Description**: What this evidence demonstrates (e.g., 'Organization-wide access control policy covering authentication and RBAC')
   - **Evidence Type**: Choose one:
     • policy_document (policies, standards)
     • audit_report (audit findings, review reports)
     • configuration_screenshot (system configs, settings)
     • log_file (audit logs, security logs)
     • certificate (compliance certificates)
     • procedure (documented procedures)
     • test_result (test reports, scan results)
   
   You can provide this in natural language or structured format.
   Example: 'Title: Access Control Policy v2.1, Type: policy_document, Description: CISO-approved policy covering authentication'"
   
   **Step 3: Ask for File Upload**
   "Please attach the evidence file.
   
   Supported formats:
   - Documents: PDF, DOCX, TXT
   - Spreadsheets: XLSX, CSV
   - Images: PNG, JPG
   - Data: JSON, XML
   
   Maximum file size: 10MB
   
   You can:
   - Attach file directly in this chat (click 📎 attachment icon)
   - Upload via Evidence tab (I'll guide you to the right page)
   - Provide file path if already in system storage"
   
   **Step 4: Optional Metadata**
   "Would you like to add metadata? (optional)
   
   Common metadata fields:
   - Document version (e.g., 'v2.1')
   - Approval date (e.g., '2024-11-01')
   - Approver (e.g., 'CISO')
   - Review date (e.g., '2025-11-01')
   - Classification (e.g., 'Internal Use Only')
   
   Say 'skip' if not needed, or provide metadata in JSON format."
   
   **Step 5: Confirm and Upload**
   "I will upload evidence for {control_name}:
   - Title: {title}
   - Type: {evidence_type}
   - File: {filename}
   - Metadata: {metadata_summary}
   
   Shall I proceed? (Reply 'yes' to upload, 'no' to cancel, 'edit' to modify)"
   
   **Step 6: Execute Upload (with Authorization Check)**
   Once confirmed, validate and upload:
   
   **Authorization Validation (CRITICAL)**:
   1. Verify control exists: GET /controls/{control_id}
   2. Check agency access: control.agency_id == current_user.agency_id
   3. If validation fails:
      - Return: "❌ Access denied. You cannot upload evidence for Control {id}. This control belongs to a different agency. Please select a control from your agency."
      - Abort upload
   
   **CRITICAL - Choose Correct Tool Based on File Attachment**:
   
   **CASE A: User HAS attached a file in chat**
   - Use `upload_evidence` tool (NOT request_evidence_upload)
   - This will create the evidence record AND attach the file immediately
   - Pass control_id, file_path (from attached file), title, description, evidence_type
   - Tool handles complete upload with file storage
   - Status will be "pending" and ready for analyst to submit for review
   
   **CASE B: User has NOT attached a file**
   - Use `request_evidence_upload` tool
   - This creates a placeholder evidence record awaiting file upload
   - User must upload file separately via Evidence page
   - This is NOT the preferred workflow - encourage file attachment in chat
   
   **After upload_evidence completes**:
   Return: "✅ Evidence uploaded successfully! 
   - Evidence ID: {evidence_id}
   - Control: {control_name} ({control_id})
   - Title: {title}
   - File: {filename} ({file_size})
   - Status: Pending (ready to submit for review)
   - Agency: {agency_name}
   
   Next step: Would you like me to submit this evidence for auditor review?"
   
   **After request_evidence_upload completes**:
   Return: "✅ Evidence placeholder created! 
   - Evidence ID: {evidence_id}
   - Control: {control_name} ({control_id})
   - Title: {title}
   - Status: Awaiting file upload
   
   Please upload the actual evidence file via the Evidence Management page, or attach the file in this chat and I can upload it for you."
   
   **Security Note**: All evidence uploads are logged with analyst ID and agency for audit trail.
   
   **Alternative Methods**:
   - **Bulk Upload via Evidence Tab**: Navigate to Evidence page, select control, upload multiple files
   - **Template Upload**: Download CSV/JSON template, fill multiple evidence items, upload in bulk
   - **IM8 Assessment Document**: Upload complete Excel with embedded PDFs (auto-processes all controls)

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
            logger.info(f"Calling Groq LLM for session {session_id} with {len(filtered_tools)} role-filtered tools")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=filtered_tools if filtered_tools else None,  # Pass None if no tools
                tool_choice="auto" if filtered_tools else "none",
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
        
        # Validation for upload_evidence
        elif function_name == "upload_evidence" or function_name == "fetch_evidence":
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
        
        logger.info(f"Created task {task.id} for tool {function_name}")
        
        # Wait for task to complete (max 30 seconds)
        max_wait = 30
        start_time = time.time()
        while (time.time() - start_time) < max_wait:
            db.refresh(task)
            if task.status in ['completed', 'failed', 'error']:
                break
            time.sleep(0.5)  # Poll every 500ms
        
        # Return task result with actual data
        result = {
            "task_id": task.id,
            "task_type": task_type,
            "status": task.status,
            "message": f"Task {task.id} {task.status}"
        }
        
        # Include actual result data from task
        if task.result:
            if isinstance(task.result, dict):
                result.update(task.result)
            logger.info(f"Task {task.id} result: {task.result}")
        
        return result

