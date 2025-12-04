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
        "search_evidence_content": {"temperature": 0.3, "max_tokens": 800},  # Evidence content search
        "analyze_evidence": {"temperature": 0.2, "max_tokens": 600},
        "analyze_evidence_rag": {"temperature": 0.2, "max_tokens": 600},
        "analyze_evidence_for_control": {"temperature": 0.3, "max_tokens": 1000},  # AI insights need more space
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
            # DEPRECATED: Old analyze_compliance tool - use mcp_analyze_compliance instead
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "analyze_compliance",
            #         "description": "Analyze compliance status and generate insights. Use when user wants compliance analysis or assessment.",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "control_id": {
            #                     "type": "string",
            #                     "description": "The control ID to analyze (can be numeric)"
            #                 },
            #                 "analysis_type": {
            #                     "type": "string",
            #                     "enum": ["gap", "status", "risk"],
            #                     "description": "Type of compliance analysis"
            #                 }
            #             },
            #             "required": ["control_id"]
            #         }
            #     }
            # },
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
                    "description": "Analyze uploaded evidence against control requirements using RAG. Validates if evidence satisfies control acceptance criteria and suggests improvements. ONLY use when you have a valid numeric evidence_id from a previous upload or query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "integer",
                                "description": "Evidence ID to analyze - must be a valid numeric ID from uploaded evidence"
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
                    "description": "ONLY use AFTER evidence has been uploaded. Suggest other controls that the uploaded evidence might also satisfy. This is for evidence reuse workflow, NOT for general questions about controls. If user asks about control requirements or policies without uploading evidence first, use search_documents instead. Requires valid evidence_id from a recent upload.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "integer",
                                "description": "Evidence ID to analyze (required) - must be from a recent upload"
                            },
                            "control_id": {
                                "type": "integer",
                                "description": "Primary control ID (required) - the control this evidence was uploaded for"
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
                    "name": "analyze_evidence_for_control",
                    "description": "AI-powered analysis of evidence quality and coverage for a control. Provides insights on: evidence completeness, quality scoring, gaps identified, recommendations for improvement. Use when user asks: 'analyze evidence for control X', 'how good is our evidence for control Y', 'what's missing for control Z', 'assess evidence quality for control'. DO NOT use for simple listing - use get_evidence_by_control instead.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "integer",
                                "description": "The control ID to analyze evidence for"
                            }
                        },
                        "required": ["control_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_evidence_by_control",
                    "description": "Retrieve all evidence documents for a specific control. Returns evidence ID, title, file name, type, upload date, and status. Use when user asks: 'show evidence for control X', 'what evidence do we have for control Y', 'list all evidence for control Z'. This is for LISTING only - for AI analysis use analyze_evidence_for_control instead.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "integer",
                                "description": "The control ID to retrieve evidence for"
                            }
                        },
                        "required": ["control_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recent_evidence",
                    "description": "Retrieve recently uploaded evidence documents. Returns evidence ID, title, control ID, file name, upload date. Use when user asks: 'show my recent uploads', 'what did I just upload', 'list recent evidence'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of recent evidence items to return (default: 10)",
                                "default": 10
                            },
                            "user_id": {
                                "type": "integer",
                                "description": "Filter by user ID (optional - defaults to current user)"
                            }
                        },
                        "required": []
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
                    "name": "create_assessment",
                    "description": "Create a comprehensive security or compliance assessment. Use when user wants to initiate a formal assessment (e.g., 'Create an IM8 assessment for HSA', 'Start a penetration test assessment'). Captures full assessment scope, schedule, team, and deliverables.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID this assessment belongs to"
                            },
                            "name": {
                                "type": "string",
                                "description": "Assessment name (e.g., 'Q4 2025 IM8 Compliance Assessment')"
                            },
                            "assessment_type": {
                                "type": "string",
                                "enum": ["compliance", "risk", "security_audit", "penetration_test", "gap_analysis"],
                                "description": "Type of assessment"
                            },
                            "framework": {
                                "type": "string",
                                "enum": ["IM8", "ISO27001", "NIST", "SOC2", "FISMA"],
                                "description": "Compliance framework"
                            },
                            "scope_description": {
                                "type": "string",
                                "description": "Detailed scope and boundaries of assessment"
                            },
                            "lead_assessor_user_id": {
                                "type": "integer",
                                "description": "User ID of the lead assessor"
                            },
                            "team_members": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Array of team member user IDs"
                            },
                            "planned_start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Planned start date (YYYY-MM-DD)"
                            },
                            "planned_end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Planned end date (YYYY-MM-DD)"
                            }
                        },
                        "required": ["project_id", "name", "assessment_type", "framework", "lead_assessor_user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_finding",
                    "description": "Create a comprehensive security finding or compliance gap. Use when user reports vulnerabilities, non-compliance issues, or security concerns (e.g., 'Create a finding for weak password policy', 'Log this SQL injection vulnerability'). Captures technical details, impact, and remediation guidance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "assessment_id": {
                                "type": "integer",
                                "description": "Assessment ID this finding belongs to"
                            },
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID this finding belongs to"
                            },
                            "title": {
                                "type": "string",
                                "description": "Clear, concise finding title (e.g., 'Weak Password Policy - No Complexity Requirements')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the finding, including what was observed"
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low", "info"],
                                "description": "Severity level"
                            },
                            "cvss_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 10.0,
                                "description": "CVSS score (0.0-10.0)"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["injection", "broken_auth", "sensitive_data", "xxe", "access_control", "security_misconfiguration", "xss", "insecure_deserialization", "logging", "ssrf"],
                                "description": "OWASP category"
                            },
                            "affected_asset": {
                                "type": "string",
                                "description": "Affected system/asset name"
                            },
                            "reproduction_steps": {
                                "type": "string",
                                "description": "Step-by-step reproduction instructions"
                            },
                            "remediation_recommendation": {
                                "type": "string",
                                "description": "Recommended remediation actions"
                            },
                            "business_impact": {
                                "type": "string",
                                "description": "Business impact analysis"
                            },
                            "control_id": {
                                "type": "integer",
                                "description": "Related control ID (optional)"
                            }
                        },
                        "required": ["assessment_id", "project_id", "title", "description", "severity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "resolve_control_to_evidence",
                    "description": "Resolve Control ID to available evidence that can be submitted. Use when user mentions 'submit Control [X]' or 'Control [X] for review' to find which evidence records are available. Returns list of pending/rejected evidence for that control. ALWAYS call this tool first before responding to 'submit Control X' requests.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "control_id": {
                                "type": "integer",
                                "description": "Control ID to find evidence for"
                            }
                        },
                        "required": ["control_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search compliance knowledge base for control requirements, policies, best practices, and standards. Use this tool when user asks: 'What are the requirements for Control X?', 'Tell me about password policies', 'What does Control Y require?', 'Show me MFA requirements', etc. This searches the compliance document library, NOT uploaded evidence. Returns relevant excerpts with source citations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query about control requirements or policies"
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
            },
            {
                "type": "function",
                "function": {
                    "name": "search_evidence_content",
                    "description": "Search INSIDE uploaded evidence documents (PDFs, Word docs, etc.) for specific content. Use this tool when user asks: 'Find evidence mentioning password policy', 'Which documents talk about MFA?', 'Search uploaded files for audit logs', 'What evidence discusses encryption?'. This searches the CONTENT of uploaded files, not just metadata. Different from search_documents which searches the compliance knowledge base.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query to find inside evidence documents"
                            },
                            "control_id": {
                                "type": "integer",
                                "description": "Filter by specific control ID (optional)"
                            },
                            "project_id": {
                                "type": "integer",
                                "description": "Filter by specific project ID (optional)"
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

EVIDENCE BUSINESS RULES:
- Evidence is PERMANENTLY BOUND to one Control (immutable binding)
- Evidence CANNOT be reassigned to a different Control or Project
- Analyst can submit MULTIPLE evidences per Control until audit closes
- If user asks to "move" or "reassign" evidence: Explain it's not allowed, guide them to upload NEW evidence for the target Control instead

TOOL SELECTION RULES:
- When user asks "What are the requirements for Control X?" or "Tell me about Control X" → USE search_documents tool
- When user asks about policies, standards, best practices → USE search_documents tool
- NEVER use suggest_related_controls unless you have a valid evidence_id from a recent evidence upload
- suggest_related_controls is ONLY for evidence reuse workflow after evidence upload

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
            'analyze_evidence_for_control',  # AI-powered evidence quality analysis
            'suggest_related_controls',  # Auditors can use Graph RAG for relationships
            'get_evidence_by_control',  # Query evidence for specific control
            'get_recent_evidence',  # View recently uploaded evidence
            'resolve_control_to_evidence'  # Resolve control ID to available evidence
        ]
        ASSESSMENT_FINDING_TOOLS = [
            'create_assessment',  # Create comprehensive security/compliance assessments
            'create_finding'  # Create security findings and compliance gaps
        ]
        COMMON_TOOLS = ['mcp_fetch_evidence', 'mcp_analyze_compliance', 'generate_report', 'search_documents', 'search_evidence_content', 'list_projects']
        
        user_role_lower = user_role.lower()
        
        if user_role_lower == 'super_admin':
            # Super admin has access to all tools
            logger.info(f"Role '{user_role}': Granting access to ALL tools")
            return self.all_tools
        
        elif user_role_lower == 'auditor':
            # Auditor: project/control creation + assessment/finding creation + evidence queries + common tools (NO evidence upload)
            allowed_tools = AUDITOR_ONLY_TOOLS + ASSESSMENT_FINDING_TOOLS + EVIDENCE_QUERY_TOOLS + COMMON_TOOLS
            filtered_tools = [t for t in self.all_tools if t['function']['name'] in allowed_tools]
            logger.info(f"Role '{user_role}': Granting access to {len(filtered_tools)} tools: {allowed_tools}")
            return filtered_tools
        
        elif user_role_lower == 'analyst':
            # Analyst: evidence upload/submit + assessment/finding creation + evidence queries + common tools (NO project/control creation)
            allowed_tools = ANALYST_ONLY_TOOLS + ASSESSMENT_FINDING_TOOLS + EVIDENCE_QUERY_TOOLS + COMMON_TOOLS
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
AUDITOR ACTIONS:
- View available projects (list_projects tool)
- Create IM8 controls for projects (your agency only)
- Create assessments and findings for security/compliance tracking
- Review evidence submissions
- Generate compliance reports
- Query evidence relationships

ASSESSMENT & FINDING MANAGEMENT:
- create_assessment: Initiate formal assessments (IM8, ISO27001, NIST, penetration tests)
- create_finding: Document security vulnerabilities and compliance gaps with full CVSS scoring

CONTROL CREATION - INTELLIGENT PARSING:
When user says "create controls for [project name]":
1. FIRST: Extract project name from message (e.g., "create controls for HSA" → project_name="HSA")
2. ONLY ask for project name if NOT provided in message
3. Once project name obtained, execute create_controls tool immediately

EXAMPLES:
❌ WRONG: User: "Create controls for HSA" → AI: "Which project?"
✅ RIGHT: User: "Create controls for HSA" → AI: [Calls create_controls with project_name="HSA"]

❌ WRONG: User: "Set up controls for Government Portal" → AI: "What's the project name?"
✅ RIGHT: User: "Set up controls for Government Portal" → AI: [Calls create_controls with project_name="Government Portal"]
""",
            
            "analyst": """

ANALYST ACTIONS:
- View available projects (list_projects tool)
- Create assessments and findings for security/compliance tracking
- Upload evidence for controls (your agency only)
- Analyze evidence quality and coverage (NEW: use analyze_evidence_for_control)
- List evidence documents (use get_evidence_by_control)
- Analyze compliance status
- Submit evidence for review

EVIDENCE TOOLS - KNOW THE DIFFERENCE:
1. analyze_evidence_for_control: AI-powered quality analysis, gap identification, recommendations
   - Use when: "analyze evidence for Control X", "how good is evidence for X", "what's missing for X"
   - Returns: quality score, completeness rating, gaps, recommendations
   
2. get_evidence_by_control: Simple listing of evidence documents
   - Use when: "show evidence for Control X", "list evidence for X", "what evidence exists for X"
   - Returns: list of evidence IDs, titles, types, dates

3. get_recent_evidence: List your recent uploads
   - Use when: "show my recent uploads", "what did I upload"

WHEN USER ASKS TO "ANALYZE" EVIDENCE:
- They want AI insights, NOT a simple list
- Use analyze_evidence_for_control tool
- Provide quality assessment, gaps, and actionable recommendations
- Example: "Overall quality: good (72%). Missing audit logs. Recommend adding test results."

WHEN USER ASKS TO "LIST" OR "SHOW" EVIDENCE:
- They want to see what exists
- Use get_evidence_by_control tool
- Return simple list with IDs, titles, types

ASSESSMENT & FINDING CREATION:
When user wants to create assessments or findings, use these tools:
- create_assessment: For formal compliance assessments (IM8, ISO27001, NIST, penetration tests)
- create_finding: For security vulnerabilities and compliance gaps

ASSESSMENT CREATION - INTELLIGENT PARSING:
When user says "Create an IM8 assessment for [project]" or "Start [framework] assessment":
1. Extract from message: project name, framework, assessment type
2. Infer reasonable defaults for missing fields:
   - assessment_type: "compliance" (most common)
   - framework: Extract from message (IM8, ISO27001, NIST, SOC2)
   - project_id: 1 (current project) or lookup from project name
   - lead_assessor_user_id: current user's ID
3. Call create_assessment immediately with inferred values
4. Only ask if framework or project is ambiguous

EXAMPLES:
✅ "Create an IM8 assessment for HSA" → Extract: framework=IM8, project="HSA", call tool
✅ "Start ISO27001 audit" → Extract: framework=ISO27001, type="compliance", call tool
❌ WRONG: User: "Create IM8 assessment" → AI asks every single field separately

FINDING CREATION - CONVERSATIONAL FLOW:
When user provides a finding description (e.g., "Create a critical finding for weak password policy"):
1. Extract what you can from the message (title, severity, description)
2. Infer reasonable defaults:
   - Use assessment_id=1 and project_id=1 (current project)
   - Set cvss_score based on severity (critical=9.0, high=7.5, medium=5.0, low=3.0)
   - Set remediation_recommendation based on context (e.g., "Implement strong password policy per IM8")
   - Set business_impact based on severity (e.g., critical="High risk of unauthorized access")
3. Call create_finding tool immediately with all inferred values
4. Only ask for clarification if critical info is missing (title, description, severity)

Examples:
✅ "Create an IM8 assessment for HSA" → Use create_assessment tool
✅ "Log a finding for weak password policy" → Infer: title="Weak Password Policy", severity="medium", call tool
✅ "Create a critical SQL injection finding" → Infer: severity="critical", cvss=9.0, call tool immediately
✅ "Finding: no MFA on admin accounts" → Infer: title="Missing MFA on Admin Accounts", severity="high", call tool

NATURAL LANGUAGE HANDLING FOR EVIDENCE SUBMISSION:
When user says "submit Control [X]" or "submit Control [X] for review" or "Control [X] for review":
1. Interpret this as: "submit evidence for Control [X]"
2. ALWAYS call resolve_control_to_evidence tool first with control_id=[X]
3. Based on tool result:
   - If ONE evidence found → Submit it immediately using submit_for_review tool
   - If MULTIPLE evidence found → List all with format "Evidence [ID]: [Title]" and ask "Which one?"
   - If NONE found → Say "No pending evidence for Control [X]. Would you like to upload evidence first?"

USER INTENT PATTERNS (recognize these as evidence submission requests):
- "submit Control [X]" → means "submit evidence for Control [X]"
- "submit Control [X] for review" → means "submit evidence for Control [X] for review"
- "Control [X] for review" → means "evidence for Control [X] for review"
- "please submit Control [X]" → means "submit evidence for Control [X]"

EXAMPLES:
✅ User: "Please submit Control 3 for review"
   AI: [calls resolve_control_to_evidence with control_id=3]
   AI: "Found Evidence 11 and Evidence 15 for Control 3. Which one would you like to submit?"

✅ User: "Submit Control 5"
   AI: [calls resolve_control_to_evidence with control_id=5]
   AI: [if only one found, calls submit_for_review immediately]
   AI: "Submitted Evidence 20 for Control 5 for review."

✅ User: "Control 4 for review"
   AI: [calls resolve_control_to_evidence with control_id=4]
   AI: "No pending evidence for Control 4. Would you like to upload evidence first?"

EVIDENCE UPLOAD - INTELLIGENT PARSING:
FIRST: Parse user's message to extract any provided information:
- "upload evidence for Control 5" → control_id=5 (extracted)
- "upload evidence for db_control_13" → control_id=13 (extracted from db_control_13)
- "upload evidence for Control ID db_control_5" → control_id=5 (extracted)
- "upload MFA policy for Control 3" → control_id=3, title might be "MFA policy"
- "upload audit report" → check if control mentioned

CRITICAL - CONTROL ID EXTRACTION:
✅ User message contains "db_control_13" → Extract control_id=13, skip asking for control
✅ User message contains "Control ID db_control_5" → Extract control_id=5, skip asking
✅ User message contains "Control 7" → Extract control_id=7, skip asking
✅ Previous message mentioned specific control ID → Remember it from context
❌ Only ask "Which control?" if NO control ID found in current OR previous message

THEN: Ask ONLY for missing required fields, ONE at a time, in this order:
1. Control ID (if not in current message AND not in recent context) → "Which control? (1, 3, 4, or 5)"
2. Title (if not in message) → "What is the title?"
3. Description → "What does this demonstrate?"
4. Type → "Type: policy_document, audit_report, configuration_screenshot, log_file, certificate, procedure, or test_result"
5. File → "Please attach the file"

CRITICAL - FILE ATTACHMENT DETECTION:
When user attaches a file, you'll see: "[File uploaded: filename.txt]" or "[File: filename.txt]" in the user message.
✅ If you see "[File uploaded: ...]" OR "[File: ...]" → File is attached! Skip asking for file.
❌ If NO file marker present → Ask "Please attach the file"

Once all 5 collected (including file attachment detected) → Execute upload_evidence tool immediately.

EXAMPLES OF PARSING:
❌ WRONG: User: "Upload evidence for Control 5" → AI: "Which control?"
✅ RIGHT: User: "Upload evidence for Control 5" → AI: "What is the title?" (control already provided!)

❌ WRONG: User: "upload evidence for db_control_13" → AI: "Which control?"
✅ RIGHT: User: "upload evidence for db_control_13" → AI: "What is the title?" (control_id=13 extracted!)

❌ WRONG: User: "upload MFA policy for control 3" → AI: "Which control?"
✅ RIGHT: User: "upload MFA policy for control 3" → AI: "What does this demonstrate?" (control=3, title="MFA policy" extracted!)

❌ WRONG: Previous message said "Control db_control_7", now user says "upload evidence" → AI: "Which control?"
✅ RIGHT: Previous message said "Control db_control_7", now user says "upload evidence" → AI: "What is the title?" (control_id=7 from context!)

ALLOWED QUESTIONS (Use these exact formats):
- "Which control? (1, 3, 4, or 5)"
- "What is the title?"
- "What does this demonstrate?"
- "Type: [list types]"
- "Please attach the file" (ONLY if no file attached yet)

FORBIDDEN:
❌ Say "file attachment not recognized" when you see "[File uploaded: ...]"
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

✅ User: "policy_document\n[File uploaded: sample.txt]"
   AI: [calls upload_evidence tool immediately - all 5 fields collected!]

✅ User: "configuration_screenshot\n[File: config.txt]"
   AI: [calls upload_evidence tool immediately - file IS attached!]

❌ User: "config attached\n[File uploaded: config.txt]"
   AI: "It seems the file attachment is not recognized" [NO! File IS attached]

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
                    elif function_name == "search_evidence_content":
                        # Search inside uploaded evidence documents
                        tool_result = await self.handle_search_evidence_content(
                            query=function_args.get("query"),
                            control_id=function_args.get("control_id"),
                            project_id=function_args.get("project_id"),
                            top_k=function_args.get("top_k", 5),
                            db=db,
                            current_user=current_user
                        )
                    elif function_name == "list_projects":
                        # List projects
                        tool_result = await self.handle_list_projects(
                            user_id=current_user["id"],
                            limit=function_args.get("limit", 10),
                            status=function_args.get("status", "all"),
                            db=db
                        )
                    elif function_name == "resolve_control_to_evidence":
                        # Resolve control ID to available evidence
                        tool_result = await self.handle_resolve_control_to_evidence(
                            control_id=function_args.get("control_id"),
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
                            session_id=session_id,
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
            from ..rag.vector_search import unified_search
            
            logger.info(f"Searching documents: {query} (backend: {'Azure AI Search' if unified_search.backend else 'In-Memory'})")
            
            # Perform vector search using unified interface (routes to Azure Search when enabled)
            search_results = await unified_search.search(
                query=query,
                top_k=top_k,
                framework_filter=None,  # Can add filtering later
                category_filter=None
            )
            
            # Format results (works with both Azure Search and in-memory)
            context_chunks = []
            sources = []
            
            for result in search_results:
                # Extract content
                content = result.get("content", "")
                context_chunks.append(content)
                
                # Build source metadata (compatible with frontend expectations)
                # Frontend expects: document_name, page, score
                framework = result.get("framework", "Unknown")
                control_id = result.get("id", "N/A")
                title = result.get("title", "Untitled")
                
                # Format document_name: "Framework - Control ID: Title"
                document_name = f"{framework} - {control_id}: {title}"
                
                source = {
                    "document_name": document_name,
                    "page": None,  # Documents don't have page numbers
                    "score": result.get("similarity_score", 0.0),
                    # Keep extra metadata for debugging
                    "framework": framework,
                    "category": result.get("category", "General"),
                    "control_id": control_id,
                    "search_type": result.get("search_type", "unknown")
                }
                sources.append(source)
            
            return {
                "success": True,
                "context": "\n\n---\n\n".join(context_chunks),
                "sources": sources,
                "total_results": len(search_results),
                "backend": "Azure AI Search" if unified_search.backend else "In-Memory"
            }
            
        except Exception as e:
            logger.error(f"Document search failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "context": "",
                "sources": []
            }
    
    async def handle_search_evidence_content(
        self,
        query: str,
        control_id: Optional[int] = None,
        project_id: Optional[int] = None,
        top_k: int = 5,
        db: Session = None,
        current_user: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Search inside uploaded evidence documents for specific content.
        Uses the evidence-content Azure Search index.
        
        Args:
            query: Search query to find inside evidence documents
            control_id: Filter by control ID (optional)
            project_id: Filter by project ID (optional)
            top_k: Number of results
            db: Database session
            current_user: Current user context
            
        Returns:
            Search results with matching evidence content and sources
        """
        try:
            from ..rag.azure_search import AzureSearchVectorStore
            from ..rag.llm_service import LLMService
            from ..config import settings
            
            logger.info(f"Searching evidence content: '{query}' (control_id={control_id}, project_id={project_id})")
            
            # Check if Azure Search is enabled
            if not settings.AZURE_SEARCH_ENABLED:
                return {
                    "success": False,
                    "error": "Evidence content search requires Azure AI Search to be enabled",
                    "context": "",
                    "sources": []
                }
            
            # Initialize Azure Search for evidence-content index
            evidence_search = AzureSearchVectorStore(index_name="evidence-content")
            llm_service = LLMService()
            
            # Generate embedding for the query
            query_embedding = await llm_service.get_embedding(query)
            
            # Build filter for Azure Search
            filters = []
            if current_user and current_user.get("agency_id"):
                filters.append(f"agency_id eq '{current_user['agency_id']}'")
            if control_id:
                filters.append(f"control_id eq '{control_id}'")
            if project_id:
                filters.append(f"project_id eq '{project_id}'")
            
            filter_str = " and ".join(filters) if filters else None
            
            # Perform hybrid search on evidence content
            search_results = await evidence_search.search(
                query_text=query,
                query_embedding=query_embedding,
                top_k=top_k,
                filter_expression=filter_str
            )
            
            # Format results
            context_chunks = []
            sources = []
            
            for result in search_results:
                content = result.get("content", "")
                context_chunks.append(content)
                
                # Build source metadata
                source = {
                    "document_name": result.get("file_name", "Unknown"),
                    "evidence_id": result.get("evidence_id"),
                    "evidence_title": result.get("title", "Untitled"),
                    "control_id": result.get("control_id"),
                    "chunk_index": result.get("chunk_index", 0),
                    "total_chunks": result.get("total_chunks", 1),
                    "score": result.get("@search.score", 0.0)
                }
                sources.append(source)
            
            return {
                "success": True,
                "context": "\n\n---\n\n".join(context_chunks),
                "sources": sources,
                "total_results": len(search_results),
                "message": f"Found {len(search_results)} matching excerpts from uploaded evidence"
            }
            
        except Exception as e:
            logger.error(f"Evidence content search failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "context": "",
                "sources": []
            }
    
    async def handle_resolve_control_to_evidence(
        self,
        control_id: int,
        db: Session,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve Control ID to available evidence that can be submitted for review.
        Returns list of pending/rejected evidence for that control.
        
        Args:
            control_id: Control ID to find evidence for
            db: Database session
            current_user: Current user context
            
        Returns:
            Dict with success, evidence list, and count
        """
        try:
            from api.src.models import Evidence, Control
            
            logger.info(f"Resolving Control {control_id} to available evidence for user {current_user.get('id')}")
            
            # Query evidence for this control that can be submitted
            # Only pending or rejected status can be submitted
            evidence_list = db.query(Evidence, Control).join(
                Control, Evidence.control_id == Control.id
            ).filter(
                Evidence.control_id == control_id,
                Evidence.agency_id == current_user.get("agency_id"),
                Evidence.verification_status.in_(['pending', 'rejected'])
            ).order_by(Evidence.created_at.desc()).all()
            
            if not evidence_list:
                return {
                    "success": True,
                    "count": 0,
                    "evidence": [],
                    "message": f"No pending or rejected evidence found for Control {control_id}. Would you like to upload evidence first?"
                }
            
            # Format evidence list
            formatted_evidence = []
            for evidence, control in evidence_list:
                formatted_evidence.append({
                    "evidence_id": evidence.id,
                    "title": evidence.title,
                    "control_id": control.id,
                    "control_name": control.name,
                    "verification_status": evidence.verification_status,
                    "created_at": evidence.created_at.isoformat() if evidence.created_at else None
                })
            
            return {
                "success": True,
                "count": len(formatted_evidence),
                "evidence": formatted_evidence,
                "message": f"Found {len(formatted_evidence)} evidence for Control {control_id}"
            }
            
        except Exception as e:
            logger.error(f"Resolve control to evidence failed: {e}", exc_info=True)
            return {
                "success": False,
                "count": 0,
                "evidence": [],
                "error": str(e)
            }
    
    def _validate_tool_parameters(
        self,
        function_name: str,
        args: Dict[str, Any],
        db: Session,
        current_user: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate tool parameters BEFORE task creation
        Prevents invalid tasks from being created
        
        Args:
            function_name: Name of the tool/function being validated
            args: Arguments provided by the LLM
            db: Database session
            current_user: Current user context
            file_path: Path to uploaded file (if any) - passed from chat endpoint
        
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
                # Check for placeholder file paths - use actual file_path parameter if provided
                actual_file_path = file_path or args.get("file_path", "")
                if not actual_file_path or actual_file_path in ["path_to_your_file", "path/to/file", "", "file_path"]:
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
            "create_controls": ["project_id"],
            "analyze_evidence": ["evidence_id", "control_id"],
            "analyze_evidence_for_control": ["control_id"],
            "suggest_related_controls": ["evidence_id", "control_id"],
            "get_evidence_by_control": ["control_id"],
            "get_recent_evidence": ["limit", "user_id"]
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
        session_id: Optional[str] = None,
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
        # Pass file_path to validation so it can properly validate upload_evidence
        validation_result = self._validate_tool_parameters(function_name, function_args, db, current_user, file_path)
        if not validation_result["valid"]:
            logger.error(f"Tool validation failed for {function_name}: {validation_result['error']}")
            return {
                "error": validation_result["error"],
                "status": "validation_failed",
                "suggestion": validation_result.get("suggestion", "Please check your inputs and try again.")
            }
        
        # FAST PATH: Execute upload_evidence synchronously (no async task)
        if function_name == "upload_evidence":
            logger.info(f"Executing upload_evidence synchronously (fast path)")
            
            # Coerce argument types
            function_args = self._coerce_argument_types(function_name, function_args)
            
            # Build payload
            payload = function_args.copy()
            
            # Add file_path - override LLM's suggestion with actual file
            if file_path:
                payload["file_path"] = file_path
                logger.info(f"Using actual file path for upload: {file_path}")
            
            # Add current user ID and agency_id
            payload["current_user_id"] = current_user.get("id")
            payload["agency_id"] = current_user.get("agency_id")
            
            # Execute immediately
            from api.src import models
            
            try:
                # Extract parameters
                control_id = payload.get("control_id")
                title = payload.get("title", "Evidence document")
                description = payload.get("description")
                evidence_type = payload.get("evidence_type", "policy_document")
                current_user_id = payload.get("current_user_id")
                agency_id = payload.get("agency_id")
                
                if not file_path or not control_id or not current_user_id:
                    return {
                        "error": "Missing required parameters",
                        "status": "validation_failed"
                    }
                
                # Get control to verify it exists
                control = db.query(models.Control).filter(models.Control.id == control_id).first()
                if not control:
                    return {
                        "error": f"Control {control_id} not found",
                        "status": "validation_failed"
                    }
                
                # Check if evidence already exists for this file
                existing = db.query(models.Evidence).filter(
                    models.Evidence.file_path == file_path
                ).first()
                
                if existing:
                    logger.info(f"Evidence already exists with ID {existing.id}")
                    return {
                        "status": "success",
                        "message": f"Evidence '{existing.title}' already uploaded. Evidence ID: {existing.id}",
                        "evidence_ids": [existing.id],
                        "CREATED_EVIDENCE_ID": existing.id,
                        "TOTAL_EVIDENCE_COUNT": 1
                    }
                
                # Create new evidence record
                evidence = models.Evidence(
                    control_id=control.id,
                    agency_id=agency_id or control.agency_id,
                    title=title,
                    description=description,
                    evidence_type=evidence_type,
                    file_path=file_path,
                    uploaded_by=current_user_id,
                    verification_status="pending"
                )
                
                db.add(evidence)
                db.commit()
                db.refresh(evidence)
                
                logger.info(f"✅ Synchronous upload completed: Evidence {evidence.id} created for control {control_id}")
                
                # Index evidence content for semantic search (async in background)
                try:
                    from ..rag.evidence_indexer import EvidenceIndexer
                    from ..config import settings
                    
                    if settings.AZURE_SEARCH_ENABLED:
                        indexer = EvidenceIndexer()
                        # Build evidence metadata dict
                        evidence_metadata = {
                            "control_id": control.id,
                            "project_id": control.project_id,
                            "agency_id": agency_id or control.agency_id,
                            "title": title,
                            "file_name": file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1],
                            "evidence_type": evidence_type
                        }
                        # Run indexing in background (don't block response)
                        import asyncio
                        asyncio.create_task(indexer.index_evidence(
                            evidence_id=evidence.id,
                            file_path=file_path,
                            evidence_metadata=evidence_metadata,
                            db=db
                        ))
                        logger.info(f"📚 Queued evidence {evidence.id} for content indexing")
                except Exception as indexing_error:
                    # Don't fail the upload if indexing fails
                    logger.warning(f"Evidence indexing queued but may fail: {indexing_error}")
                
                return {
                    "status": "success",
                    "message": f"Evidence '{evidence.title}' uploaded successfully. Evidence ID: {evidence.id}",
                    "evidence_ids": [evidence.id],
                    "CREATED_EVIDENCE_ID": evidence.id,
                    "TOTAL_EVIDENCE_COUNT": 1
                }
                
            except Exception as e:
                logger.error(f"Synchronous upload failed: {e}", exc_info=True)
                return {
                    "error": str(e),
                    "status": "error",
                    "message": f"Upload failed: {str(e)}"
                }
        
        # FAST PATH: Execute evidence query tools synchronously
        if function_name == "get_evidence_by_control":
            logger.info(f"Executing get_evidence_by_control synchronously (fast path)")
            
            from api.src import models
            
            try:
                control_id = function_args.get("control_id")
                
                if not control_id:
                    return {"error": "Missing required parameter: control_id", "status": "validation_failed"}
                
                # Query all evidence for the control
                evidence_list = db.query(models.Evidence).filter(
                    models.Evidence.control_id == control_id
                ).order_by(models.Evidence.uploaded_at.desc()).all()
                
                if not evidence_list:
                    return {
                        "status": "success",
                        "message": f"No evidence found for Control {control_id}",
                        "evidence_count": 0,
                        "evidence": []
                    }
                
                # Format evidence data
                evidence_data = []
                for ev in evidence_list:
                    evidence_data.append({
                        "id": ev.id,
                        "title": ev.title,
                        "file_name": ev.file_path.split("/")[-1] if ev.file_path else None,
                        "evidence_type": ev.evidence_type,
                        "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
                        "verification_status": ev.verification_status,
                        "description": ev.description
                    })
                
                logger.info(f"✅ Found {len(evidence_data)} evidence items for control {control_id}")
                
                return {
                    "status": "success",
                    "message": f"Found {len(evidence_data)} evidence item(s) for Control {control_id}",
                    "evidence_count": len(evidence_data),
                    "evidence": evidence_data
                }
                
            except Exception as e:
                logger.error(f"get_evidence_by_control failed: {e}", exc_info=True)
                return {"error": str(e), "status": "error"}
        
        if function_name == "get_recent_evidence":
            logger.info(f"Executing get_recent_evidence synchronously (fast path)")
            
            from api.src import models
            
            try:
                limit = function_args.get("limit", 10)
                user_id = function_args.get("user_id") or current_user.get("id")
                
                # Query recent evidence for the user
                query = db.query(models.Evidence).filter(
                    models.Evidence.uploaded_by == user_id
                ).order_by(models.Evidence.uploaded_at.desc()).limit(limit)
                
                evidence_list = query.all()
                
                if not evidence_list:
                    return {
                        "status": "success",
                        "message": "No recent evidence found",
                        "evidence_count": 0,
                        "evidence": []
                    }
                
                # Format evidence data
                evidence_data = []
                for ev in evidence_list:
                    evidence_data.append({
                        "id": ev.id,
                        "title": ev.title,
                        "control_id": ev.control_id,
                        "file_name": ev.file_path.split("/")[-1] if ev.file_path else None,
                        "evidence_type": ev.evidence_type,
                        "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
                        "verification_status": ev.verification_status
                    })
                
                logger.info(f"✅ Found {len(evidence_data)} recent evidence items")
                
                return {
                    "status": "success",
                    "message": f"Found {len(evidence_data)} recent evidence item(s)",
                    "evidence_count": len(evidence_data),
                    "evidence": evidence_data
                }
                
            except Exception as e:
                logger.error(f"get_recent_evidence failed: {e}", exc_info=True)
                return {"error": str(e), "status": "error"}
        
        # FAST PATH: AI-powered evidence analysis for control
        if function_name == "analyze_evidence_for_control":
            logger.info(f"Executing analyze_evidence_for_control synchronously (fast path)")
            
            from api.src import models
            
            try:
                control_id = function_args.get("control_id")
                
                if not control_id:
                    return {"error": "Missing required parameter: control_id", "status": "validation_failed"}
                
                # Get control details
                control = db.query(models.Control).filter(models.Control.id == control_id).first()
                if not control:
                    return {"error": f"Control {control_id} not found", "status": "not_found"}
                
                # Get all evidence for the control
                evidence_list = db.query(models.Evidence).filter(
                    models.Evidence.control_id == control_id
                ).order_by(models.Evidence.uploaded_at.desc()).all()
                
                if not evidence_list:
                    return {
                        "status": "success",
                        "control_id": control_id,
                        "control_name": control.name,
                        "evidence_count": 0,
                        "quality_score": 0.0,
                        "completeness": "none",
                        "analysis": {
                            "summary": f"No evidence has been uploaded for {control.name} yet.",
                            "gaps": [
                                "No policy documents provided",
                                "No audit reports available",
                                "No configuration evidence",
                                "No test results or validation"
                            ],
                            "recommendations": [
                                f"Upload policy document addressing {control.description[:100]}...",
                                "Provide audit logs or reports demonstrating compliance",
                                "Include configuration screenshots or settings exports",
                                "Add test results validating the control implementation"
                            ]
                        }
                    }
                
                # Calculate evidence quality metrics
                evidence_types = {}
                verified_count = 0
                total_evidence = len(evidence_list)
                
                for ev in evidence_list:
                    evidence_types[ev.evidence_type] = evidence_types.get(ev.evidence_type, 0) + 1
                    if ev.verification_status == "verified":
                        verified_count += 1
                
                # Quality scoring algorithm
                type_diversity_score = min(len(evidence_types) / 4.0, 1.0)  # 4 types = full score
                verification_score = verified_count / total_evidence if total_evidence > 0 else 0
                quantity_score = min(total_evidence / 3.0, 1.0)  # 3+ pieces = full score
                
                quality_score = round((type_diversity_score * 0.4 + verification_score * 0.4 + quantity_score * 0.2) * 100, 1)
                
                # Determine completeness level
                if quality_score >= 80:
                    completeness = "excellent"
                elif quality_score >= 60:
                    completeness = "good"
                elif quality_score >= 40:
                    completeness = "adequate"
                elif quality_score >= 20:
                    completeness = "partial"
                else:
                    completeness = "minimal"
                
                # Identify gaps
                gaps = []
                expected_types = ["policy_document", "audit_report", "configuration_screenshot", "test_result"]
                for exp_type in expected_types:
                    if exp_type not in evidence_types:
                        type_labels = {
                            "policy_document": "Policy documents",
                            "audit_report": "Audit reports or logs",
                            "configuration_screenshot": "Configuration evidence",
                            "test_result": "Test results or validation"
                        }
                        gaps.append(f"Missing {type_labels.get(exp_type, exp_type)}")
                
                if verified_count < total_evidence:
                    gaps.append(f"{total_evidence - verified_count} evidence item(s) pending verification")
                
                # Generate recommendations
                recommendations = []
                if len(evidence_types) < 3:
                    recommendations.append("Add more diverse evidence types (policy, audit, config, test)")
                if verified_count < total_evidence:
                    recommendations.append("Submit pending evidence for auditor verification")
                if total_evidence < 3:
                    recommendations.append("Upload additional supporting evidence to strengthen compliance proof")
                if "policy_document" not in evidence_types:
                    recommendations.append("Add policy document establishing the control requirement")
                if "audit_report" not in evidence_types:
                    recommendations.append("Provide audit logs or reports demonstrating ongoing compliance")
                
                # Build summary
                summary_parts = []
                summary_parts.append(f"Found {total_evidence} evidence item(s) for {control.name}.")
                summary_parts.append(f"Evidence types: {', '.join(evidence_types.keys())}.")
                summary_parts.append(f"{verified_count} verified, {total_evidence - verified_count} pending verification.")
                summary_parts.append(f"Overall quality: {completeness} ({quality_score}%).")
                
                logger.info(f"✅ Analyzed evidence for control {control_id}: {quality_score}% quality, {completeness} completeness")
                
                return {
                    "status": "success",
                    "control_id": control_id,
                    "control_name": control.name,
                    "evidence_count": total_evidence,
                    "quality_score": quality_score,
                    "completeness": completeness,
                    "analysis": {
                        "summary": " ".join(summary_parts),
                        "evidence_breakdown": evidence_types,
                        "verified_count": verified_count,
                        "pending_count": total_evidence - verified_count,
                        "gaps": gaps if gaps else ["No significant gaps identified"],
                        "recommendations": recommendations if recommendations else ["Evidence quality is excellent - no immediate action needed"]
                    }
                }
                
            except Exception as e:
                logger.error(f"analyze_evidence_for_control failed: {e}", exc_info=True)
                return {"error": str(e), "status": "error"}
        
        # FAST PATH: Create assessment synchronously
        if function_name == "create_assessment":
            logger.info(f"Executing create_assessment synchronously (fast path)")
            
            from api.src import models
            from datetime import datetime
            
            try:
                # Get current user
                user = db.query(models.User).filter(models.User.id == current_user.get("id")).first()
                if not user:
                    return {"error": "User not found", "status": "error"}
                
                # Parse dates if provided
                planned_start_date = None
                planned_end_date = None
                if function_args.get("planned_start_date"):
                    planned_start_date = datetime.strptime(function_args["planned_start_date"], "%Y-%m-%d").date()
                if function_args.get("planned_end_date"):
                    planned_end_date = datetime.strptime(function_args["planned_end_date"], "%Y-%m-%d").date()
                
                # Create assessment
                assessment = models.Assessment(
                    project_id=function_args["project_id"],
                    agency_id=user.agency_id,
                    name=function_args["name"],
                    assessment_type=function_args["assessment_type"],
                    framework=function_args["framework"],
                    scope_description=function_args.get("scope_description"),
                    included_controls=function_args.get("included_controls", []),
                    planned_start_date=planned_start_date,
                    planned_end_date=planned_end_date,
                    lead_assessor_user_id=function_args["lead_assessor_user_id"],
                    team_members=function_args.get("team_members", []),
                    status="not_started",
                    completion_percentage=0.0,
                    created_by_user_id=current_user.get("id")
                )
                
                db.add(assessment)
                db.commit()
                db.refresh(assessment)
                
                logger.info(f"✅ Assessment created: ID {assessment.id}")
                
                return {
                    "status": "success",
                    "message": f"Assessment '{assessment.name}' created successfully",
                    "assessment_id": assessment.id,
                    "assessment": {
                        "id": assessment.id,
                        "name": assessment.name,
                        "type": assessment.assessment_type,
                        "framework": assessment.framework,
                        "status": assessment.status
                    }
                }
                
            except Exception as e:
                logger.error(f"create_assessment failed: {e}", exc_info=True)
                return {"error": str(e), "status": "error"}
        
        # FAST PATH: Create finding synchronously
        if function_name == "create_finding":
            logger.info(f"Executing create_finding synchronously (fast path)")
            
            from api.src import models
            from datetime import datetime, timedelta
            
            try:
                # Get current user
                user = db.query(models.User).filter(models.User.id == current_user.get("id")).first()
                if not user:
                    return {"error": "User not found", "status": "error"}
                
                # Create finding
                finding = models.Finding(
                    assessment_id=function_args["assessment_id"],
                    project_id=function_args["project_id"],
                    agency_id=user.agency_id,
                    control_id=function_args.get("control_id"),
                    title=function_args["title"],
                    description=function_args["description"],
                    severity=function_args["severity"],
                    cvss_score=function_args.get("cvss_score"),
                    category=function_args.get("category"),
                    affected_asset=function_args.get("affected_asset"),
                    reproduction_steps=function_args.get("reproduction_steps"),
                    remediation_recommendation=function_args.get("remediation_recommendation"),
                    business_impact=function_args.get("business_impact"),
                    status="open",
                    discovery_date=datetime.now().date(),
                    target_remediation_date=datetime.now().date() + timedelta(days=30),
                    created_by_user_id=current_user.get("id")
                )
                
                db.add(finding)
                db.commit()
                db.refresh(finding)
                
                # Update assessment severity counts
                assessment = db.query(models.Assessment).filter(
                    models.Assessment.id == function_args["assessment_id"]
                ).first()
                
                if assessment:
                    if finding.severity == "critical":
                        assessment.findings_count_critical = (assessment.findings_count_critical or 0) + 1
                    elif finding.severity == "high":
                        assessment.findings_count_high = (assessment.findings_count_high or 0) + 1
                    elif finding.severity == "medium":
                        assessment.findings_count_medium = (assessment.findings_count_medium or 0) + 1
                    elif finding.severity == "low":
                        assessment.findings_count_low = (assessment.findings_count_low or 0) + 1
                    db.commit()
                
                logger.info(f"✅ Finding created: ID {finding.id}")
                
                return {
                    "status": "success",
                    "message": f"Finding '{finding.title}' created successfully",
                    "finding_id": finding.id,
                    "finding": {
                        "id": finding.id,
                        "title": finding.title,
                        "severity": finding.severity,
                        "cvss_score": finding.cvss_score,
                        "status": finding.status
                    }
                }
                
            except Exception as e:
                logger.error(f"create_finding failed: {e}", exc_info=True)
                return {"error": str(e), "status": "error"}
        
        # SLOW PATH: All other tools use async worker
        # Map tool to task type
        task_type_map = {
            "create_project": "create_project",
            "create_controls": "create_controls",
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
        if function_name == "fetch_evidence":
            if file_path:
                payload["file_path"] = file_path
                logger.info(f"Using actual file path for fetch: {file_path}")
            elif "file_path" in payload and not payload["file_path"].startswith("/app/storage"):
                # LLM provided relative path, make it absolute
                logger.warning(f"LLM provided relative path: {payload['file_path']}, need actual file")
        
        # Add current user ID, agency_id, and session_id
        payload["current_user_id"] = current_user.get("id")
        payload["agency_id"] = current_user.get("agency_id")
        if session_id:
            payload["session_id"] = session_id
        
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
        
        # Return task ID immediately for SSE streaming (no waiting)
        # The client will receive real-time updates via SSE when task completes
        logger.info(f"Task {task.id} created, returning immediately for SSE streaming")
        
        return {
            "task_id": task.id,
            "task_type": task_type,
            "status": "pending",
            "message": f"Task {task.id} created and processing in background. Results will be streamed via SSE."
        }


