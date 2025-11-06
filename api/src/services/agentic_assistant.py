"""
Groq-powered Agentic AI Assistant
Multi-turn conversation with tool calling for QA Compliance
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from groq import Groq
import logging

from api.src.services.conversation_manager import ConversationManager
from api.src.services.ai_task_orchestrator import ai_task_orchestrator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AgenticAssistant:
    """Groq-powered conversational agent with tool calling"""
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-70b-versatile"  # Stable model for agentic workflows
        
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
            }
        ]
        
        # System prompt
        self.system_prompt = """You are an AI compliance assistant for the Quantique QA Compliance platform.
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

Be conversational, helpful, and ask clarifying questions if needed.
Always confirm actions before executing them.
Maintain context across the conversation."""
    
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
            
            # Build messages for Groq
            messages = [{"role": "system", "content": self.system_prompt}]
            
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
                    
                    # Execute tool via AI Task Orchestrator
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
