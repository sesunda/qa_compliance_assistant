"""
Agentic Chat API
Natural language interface for compliance automation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
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


class ChatResponse(BaseModel):
    response: str
    task_created: bool = False
    task_id: Optional[int] = None
    task_type: Optional[str] = None
    intent: Optional[Dict[str, Any]] = None


@router.post("/", response_model=ChatResponse)
async def process_chat_message(
    chat_message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process natural language message and create agent tasks
    
    This endpoint:
    1. Parses user intent using LLM
    2. Creates appropriate agent task
    3. Returns confirmation and task ID
    
    Example messages:
    - "Upload 30 IM8 controls covering all 10 domains"
    - "Create findings from VAPT: SQL injection (critical), XSS (high)"
    - "Generate executive compliance report for assessment 1"
    - "Analyze evidence for IM8-01 controls"
    """
    try:
        llm_service = get_llm_service()
        
        if not llm_service.is_available():
            return ChatResponse(
                response="❌ AI service is not configured. Please set up OpenAI or Azure OpenAI credentials.",
                task_created=False
            )
        
        # Parse user intent
        logger.info(f"Parsing message from user {current_user['id']}: {chat_message.message}")
        intent = llm_service.parse_user_intent(chat_message.message)
        
        action = intent.get("action")
        entity = intent.get("entity")
        parameters = intent.get("parameters", {})
        count = intent.get("count")
        
        # Get user details
        user = db.query(User).filter(User.id == current_user["id"]).first()
        
        # Route to appropriate task handler
        task_type = None
        task_title = None
        task_payload = {
            "agency_id": user.agency_id,
            "created_by": user.id
        }
        
        if action == "create_controls":
            task_type = "create_controls"
            task_title = f"Generate {count or 30} {parameters.get('framework', 'IM8')} Controls"
            task_payload.update({
                "framework": parameters.get("framework", "IM8"),
                "count": count or 30,
                "domain_areas": parameters.get("domain_areas", [
                    "IM8-01", "IM8-02", "IM8-03", "IM8-04", "IM8-05",
                    "IM8-06", "IM8-07", "IM8-08", "IM8-09", "IM8-10"
                ]),
                "project_id": parameters.get("project_id", 1)
            })
            response_text = f"✅ I'll generate {count or 30} {parameters.get('framework', 'IM8')} security controls for you. This may take a minute..."
        
        elif action == "create_findings":
            task_type = "create_findings"
            assessment_id = parameters.get("assessment_id", 1)
            task_title = f"Generate Security Findings for Assessment {assessment_id}"
            task_payload.update({
                "findings_description": chat_message.message,
                "assessment_id": assessment_id,
                "framework": parameters.get("framework", "IM8"),
                "assigned_to": user.id
            })
            response_text = f"✅ I'll create the security findings and link them to assessment {assessment_id}. Processing..."
        
        elif action == "analyze_evidence":
            task_type = "analyze_evidence"
            control_id = parameters.get("control_id", 1)
            evidence_ids = parameters.get("evidence_ids", [])
            task_title = f"AI Evidence Analysis for Control {control_id}"
            task_payload.update({
                "control_id": control_id,
                "evidence_ids": evidence_ids
            })
            response_text = f"✅ I'll analyze the evidence items against control requirements. This will take a moment..."
        
        elif action == "generate_report":
            task_type = "generate_compliance_report"
            assessment_id = parameters.get("assessment_id", 1)
            report_type = parameters.get("report_type", "executive")
            task_title = f"Generate {report_type.title()} Compliance Report"
            task_payload.update({
                "assessment_id": assessment_id,
                "report_type": report_type
            })
            response_text = f"✅ I'll generate the {report_type} compliance report for assessment {assessment_id}. Compiling data..."
        
        elif action == "create_assessment":
            # For now, guide user to create via UI
            # In future, implement assessment creation task
            return ChatResponse(
                response="📋 To create a new assessment, please use the 'Assessments' page and click 'New Assessment'. I can help you populate it with controls and findings once it's created!",
                task_created=False,
                intent=intent
            )
        
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
            description=f"Requested via agentic chat: {chat_message.message[:200]}",
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
            intent=intent
        )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
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
