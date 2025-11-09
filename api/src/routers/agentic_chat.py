"""
Agentic Chat API
Natural language interface for compliance automation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from api.src.database import get_db
from api.src.auth import get_current_user
from api.src.models import AgentTask, User
from api.src.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agentic-chat", tags=["agentic-chat"])


class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None  # Track conversation thread
    edit_parameter: Optional[Dict[str, Any]] = None  # For editing previous answers


class ChatResponse(BaseModel):
    response: str
    task_created: bool = False
    task_id: Optional[int] = None
    task_type: Optional[str] = None
    intent: Optional[Dict[str, Any]] = None
    
    # Multi-turn conversation fields
    is_clarifying: bool = False  # True if asking for more info
    clarifying_question: Optional[str] = None
    suggested_responses: Optional[list] = None
    conversation_context: Optional[Dict[str, Any]] = None  # State to send back
    parameters_collected: Optional[Dict[str, Any]] = None  # What we have so far
    parameters_missing: Optional[list] = None  # What's still needed
    conversation_id: Optional[str] = None
    can_edit: bool = True  # Allow user to edit previous answers


@router.post("/", response_model=ChatResponse)
async def process_chat_message(
    chat_message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process natural language message with multi-turn conversation support
    
    This endpoint:
    1. Parses user intent using LLM
    2. Detects missing required parameters
    3. Asks clarifying questions with smart suggestions
    4. Creates task only when all parameters collected
    5. Supports editing previous answers
    
    Example conversation flow:
    User: "Upload IM8 controls"
    Bot: "Which project should I add these controls to?" [suggestions: Project 1, Project 2...]
    User: "Project 1"
    Bot: "Which IM8 domains?" [suggestions: IM8-01, IM8-02, All domains...]
    User: "All domains"
    Bot: ✅ Task created! [executes]
    """
    try:
        llm_service = get_llm_service()
        
        if not llm_service.is_available():
            return ChatResponse(
                response="❌ AI service is not configured. Please set up OpenAI or Azure OpenAI credentials.",
                task_created=False
            )
        
        # Get user details
        user = db.query(User).filter(User.id == current_user["id"]).first()
        
        # Handle edit requests
        conversation_context = chat_message.context or {}
        if chat_message.edit_parameter:
            # User wants to edit a previous answer
            param_name = chat_message.edit_parameter.get("parameter")
            param_value = chat_message.edit_parameter.get("value")
            if param_name and conversation_context.get("parameters"):
                conversation_context["parameters"][param_name] = param_value
                logger.info(f"Edited parameter {param_name} to {param_value}")
        
        # Parse user intent with conversation context
        logger.info(f"Parsing message from user {current_user['id']}: {chat_message.message}")
        logger.info(f"Conversation context: {conversation_context}")
        
        intent = llm_service.parse_user_intent(
            user_prompt=chat_message.message,
            conversation_context=conversation_context
        )
        
        # Store original message for findings description
        intent["original_message"] = chat_message.message
        
        # Check if we have all required parameters
        is_ready = intent.get("is_ready", False)
        missing_params = intent.get("missing_parameters", [])
        
        action = intent.get("action")
        parameters = intent.get("parameters", {})
        
        # DEBUG: Log what we're about to validate
        logger.info(f"DEBUG: action={action}, parameters={parameters}, is_ready={is_ready}")
        
        # CRITICAL: ALWAYS validate parameters against database, even if LLM says is_ready=True
        # The LLM doesn't know if control_id=5 actually exists, so we must check
        # Run validation even if parameters is empty - validation will check for missing params
        if action:
            logger.info(f"DEBUG: Running validation for action={action}")
            is_valid, validation_missing, error_msg = llm_service.validate_parameters(
                action=action,
                parameters=parameters,
                db_session=db,
                user=user
            )
            
            logger.info(f"DEBUG: Validation result: is_valid={is_valid}, error_msg={error_msg}, missing={validation_missing}")
            
            if not is_valid:
                # Database validation failed
                if error_msg:
                    # Entity doesn't exist - ask user to clarify
                    suggestions = []
                    if "project" in error_msg.lower() or "Project" in error_msg:
                        suggestions = llm_service.get_smart_suggestions("project_id", db, user)
                    elif "assessment" in error_msg.lower() or "Assessment" in error_msg:
                        suggestions = llm_service.get_smart_suggestions("assessment_id", db, user)
                    elif "control" in error_msg.lower() or "Control" in error_msg:
                        suggestions = llm_service.get_smart_suggestions("control_id", db, user)
                    elif "evidence" in error_msg.lower() or "Evidence" in error_msg:
                        suggestions = llm_service.get_smart_suggestions("evidence_ids", db, user)
                    
                    if not suggestions:
                        suggestions = ["Show me what's available"]
                    
                    return ChatResponse(
                        response=f"❌ {error_msg}\n\nPlease select from available options below:",
                        task_created=False,
                        is_clarifying=True,
                        clarifying_question=error_msg,
                        suggested_responses=suggestions,
                        conversation_context=intent,
                        parameters_collected=parameters,
                        parameters_missing=validation_missing,
                        conversation_id=chat_message.conversation_id or f"conv_{current_user['id']}_{int(datetime.now().timestamp())}",
                        can_edit=True,
                        intent=intent
                    )
                elif validation_missing:
                    # Missing required params
                    is_ready = False
                    missing_params.extend(validation_missing)
        
        # If expert mode detected or all params ready AND validated, execute immediately
        if is_ready:
            # FINAL VALIDATION GATE: Run database validation one more time before executing
            # This ensures we NEVER create a task with invalid parameters
            logger.info(f"DEBUG: Final validation gate before task execution")
            final_is_valid, final_missing, final_error = llm_service.validate_parameters(
                action=action,
                parameters=parameters,
                db_session=db,
                user=user
            )
            logger.info(f"DEBUG: Final validation result: is_valid={final_is_valid}, error={final_error}, missing={final_missing}")
            
            if not final_is_valid:
                # Validation failed - ask for clarification instead of executing
                suggestions = []
                if final_error:
                    # Entity doesn't exist
                    if "control" in final_error.lower():
                        suggestions = llm_service.get_smart_suggestions("control_id", db, user)
                    elif "project" in final_error.lower():
                        suggestions = llm_service.get_smart_suggestions("project_id", db, user)
                    elif "assessment" in final_error.lower():
                        suggestions = llm_service.get_smart_suggestions("assessment_id", db, user)
                elif final_missing:
                    # Parameters missing
                    first_missing = final_missing[0]
                    suggestions = llm_service.get_smart_suggestions(first_missing, db, user)
                
                if not suggestions:
                    suggestions = ["Show me what's available"]
                
                error_message = final_error or f"Missing required parameters: {', '.join(final_missing)}"
                
                return ChatResponse(
                    response=f"❌ {error_message}\n\nPlease select from available options:",
                    task_created=False,
                    is_clarifying=True,
                    clarifying_question=error_message,
                    suggested_responses=suggestions,
                    conversation_context=intent,
                    parameters_collected=parameters,
                    parameters_missing=final_missing,
                    conversation_id=chat_message.conversation_id or f"conv_{current_user['id']}_{int(datetime.now().timestamp())}",
                    can_edit=True,
                    intent=intent
                )
            
            # Validation passed - safe to execute
            return await _execute_task(intent, user, db, chat_message.conversation_id or "")
        
        # Otherwise, ask clarifying question
        clarifying_question = intent.get("clarifying_question", "")
        suggested_responses = intent.get("suggested_responses", [])
        
        # Enhance suggestions with database context
        if missing_params and len(missing_params) > 0:
            first_missing = missing_params[0]
            db_suggestions = llm_service.get_smart_suggestions(first_missing, db, user)
            if db_suggestions:
                suggested_responses = db_suggestions
        
        # Generate conversation ID if not exists
        conversation_id = chat_message.conversation_id or f"conv_{current_user['id']}_{int(datetime.now().timestamp())}"
        
        return ChatResponse(
            response=clarifying_question,
            task_created=False,
            is_clarifying=True,
            clarifying_question=clarifying_question,
            suggested_responses=suggested_responses,
            conversation_context=intent,  # Send full intent as context for next turn
            parameters_collected=intent.get("parameters", {}),
            parameters_missing=missing_params,
            conversation_id=conversation_id,
            can_edit=True,
            intent=intent
        )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


async def _execute_task(
    intent: Dict[str, Any],
    user: User,
    db: Session,
    conversation_id: str
) -> ChatResponse:
async def _execute_task(
    intent: Dict[str, Any],
    user: User,
    db: Session,
    conversation_id: str
) -> ChatResponse:
    """
    Execute task once all parameters are collected
    """
    action = intent.get("action")
    entity = intent.get("entity")
    parameters = intent.get("parameters", {})
    count = intent.get("count")
    
    # Route to appropriate task handler
    task_type = None
    task_title = None
    task_payload = {
        "agency_id": user.agency_id,
        "created_by": user.id
    }
    
    if action == "create_controls":
        task_type = "create_controls"
        framework = parameters.get("framework", "IM8")
        project_id = parameters.get("project_id")  # REQUIRED - no default
        
        if not project_id:
            raise ValueError("project_id is required for create_controls")
        
        task_title = f"Generate {count or 30} {framework} Controls"
        task_payload.update({
            "framework": framework,
            "count": count or 30,
            "domain_areas": parameters.get("domain_areas", [
                "IM8-01", "IM8-02", "IM8-03", "IM8-04", "IM8-05",
                "IM8-06", "IM8-07", "IM8-08", "IM8-09", "IM8-10"
            ]),
            "project_id": project_id
        })
        response_text = f"✅ I'll generate {count or 30} {framework} security controls for you. This may take a minute..."
    
    elif action == "create_findings":
        task_type = "create_findings"
        assessment_id = parameters.get("assessment_id")  # REQUIRED - no default
        
        if not assessment_id:
            raise ValueError("assessment_id is required for create_findings")
        
        task_title = f"Generate Security Findings for Assessment {assessment_id}"
        task_payload.update({
            "findings_description": intent.get("original_message", ""),
            "assessment_id": assessment_id,
            "framework": parameters.get("framework", "IM8"),
            "assigned_to": user.id
        })
        response_text = f"✅ I'll create the security findings and link them to assessment {assessment_id}. Processing..."
    
    elif action == "analyze_evidence":
        task_type = "analyze_evidence"
        control_id = parameters.get("control_id")  # REQUIRED - no default
        
        if not control_id:
            raise ValueError("control_id is required for analyze_evidence")
        
        evidence_ids = parameters.get("evidence_ids", [])
        task_title = f"AI Evidence Analysis for Control {control_id}"
        task_payload.update({
            "control_id": control_id,
            "evidence_ids": evidence_ids
        })
        response_text = f"✅ I'll analyze the evidence items against control requirements. This will take a moment..."
    
    elif action == "generate_report":
        task_type = "generate_compliance_report"
        assessment_id = parameters.get("assessment_id")  # REQUIRED - no default
        
        if not assessment_id:
            raise ValueError("assessment_id is required for generate_report")
        
        report_type = parameters.get("report_type", "executive")
        task_title = f"Generate {report_type.title()} Compliance Report"
        task_payload.update({
            "assessment_id": assessment_id,
            "report_type": report_type
        })
        response_text = f"✅ I'll generate the {report_type} compliance report for assessment {assessment_id}. Compiling data..."
        
        else:
            return ChatResponse(
                response=f"🤔 I understand you want to {action} {entity}, but I'm not sure how to do that yet. Can you try rephrasing? I can help you:\n\n• Create controls\n• Create findings\n• Analyze evidence\n• Generate reports",
                task_created=False,
                intent=intent
            )
        
        # Create agent task
        agent_task = AgentTask(
            task_type=task_type,
            title=task_title,
            description=f"Requested via agentic chat (conversation: {conversation_id})",
            status="pending",
            progress=0,
            created_by=user.id,
            payload=task_payload
        )
        
        db.add(agent_task)
        db.commit()
        db.refresh(agent_task)
        
        logger.info(f"Created agent task {agent_task.id} of type {task_type}")
        
        return ChatResponse(
            response=f"{response_text}\n\n📊 Task ID: {agent_task.id}\n\nYou can monitor progress in the 'Agent Tasks' page.",
            task_created=True,
            task_id=agent_task.id,
            task_type=task_type,
            intent=intent,
            conversation_id=conversation_id
        )


@router.get("/capabilities")
async def get_capabilities():
    """Get list of available agentic capabilities"""
    return {
        "capabilities": [
            {
                "action": "create_controls",
                "description": "Generate security controls based on framework and domains",
                "example": "Upload 30 IM8 controls covering all 10 domain areas",
                "parameters": ["framework", "count", "domain_areas", "project_id"]
            },
            {
                "action": "create_findings",
                "description": "Create security findings from natural language descriptions",
                "example": "Create findings: SQL injection (critical), XSS (high), weak passwords (medium)",
                "parameters": ["findings_description", "assessment_id", "framework"]
            },
            {
                "action": "analyze_evidence",
                "description": "AI-powered evidence analysis against control requirements",
                "example": "Analyze evidence items 1, 2, 3 for control 5",
                "parameters": ["evidence_ids", "control_id"]
            },
            {
                "action": "generate_report",
                "description": "Generate executive or technical compliance reports",
                "example": "Generate executive compliance report for assessment 1",
                "parameters": ["assessment_id", "report_type"]
            }
        ],
        "status": "active" if get_llm_service().is_available() else "unavailable",
        "provider": get_llm_service().provider
    }
