"""
Agentic Chat API
Natural language interface for compliance automation
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import os

from api.src.database import get_db
from api.src.auth import get_current_user
from api.src.models import AgentTask, User
from api.src.services.llm_service import get_llm_service
from api.src.services.conversation_manager import ConversationManager
from api.src.services.agentic_assistant import AgenticAssistant

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
    
    # Rich UI components
    rich_ui: Optional[Dict[str, Any]] = None  # Structured UI component data
    
    # RAG features
    sources: List[Dict[str, Any]] = []  # Document sources
    file_uploaded: bool = False  # File upload indicator


@router.post("/")
async def chat(
    message: str = Form(None),  # Temporarily make optional to debug
    context: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Unified chat endpoint with RAG, MCP tools, and validation
    
    Features:
    - Multi-turn conversation with suggested responses
    - File upload for evidence/documents
    - Semantic document search (via search_documents tool)
    - MCP tool calling (mcp_fetch_evidence, mcp_analyze_compliance)
    - Defensive validation (via AgenticAssistant)
    - Conversation persistence (via ConversationManager)
    
    This replaces the old implementation with AgenticAssistant integration.
    """
    logger.info(f"DEBUG: Received chat request: message='{message}', has_file={file is not None}, conversation_id={conversation_id}, context={context[:100] if context else None}")
    try:
        # PROACTIVE VALIDATION: Check message length
        if not message or not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty. Please provide a question or command."
            )
        
        if len(message) > 10000:
            raise HTTPException(
                status_code=400,
                detail=f"Message is too long ({len(message)} characters). Maximum allowed is 10,000 characters."
            )
        
        # PROACTIVE VALIDATION: Check file size and type
        if file:
            # Check file size (10MB limit)
            contents = await file.read()
            await file.seek(0)  # Reset file pointer
            
            if len(contents) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' is too large ({len(contents) / 1024 / 1024:.2f}MB). Maximum size is 10MB."
                )
            
            # Check file type
            allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv', '.json', '.xml', '.jpg', '.jpeg', '.png'}
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{file_extension}' is not supported. Allowed types: {', '.join(allowed_extensions)}"
                )
        
        # Parse conversation context
        conversation_context = json.loads(context) if context else None
        
        # Initialize services
        assistant = AgenticAssistant()  # Provider determined from LLM_PROVIDER env var
        conv_manager = ConversationManager(db, current_user["id"])
        
        # Get or create session
        session = None
        if conversation_id:
            session = conv_manager.get_session(conversation_id)
            if not session:
                # Create new session with provided ID
                session = conv_manager.create_session(
                    title=message[:50] + "..." if len(message) > 50 else message,
                    session_id=conversation_id
                )
        else:
            # Create new session
            session = conv_manager.create_session(
                title=message[:50] + "..." if len(message) > 50 else message
            )
        
        # Handle file upload
        file_path = None
        if file:
            # Create storage directory
            storage_dir = "/app/storage/uploads"
            os.makedirs(storage_dir, exist_ok=True)
            
            # Generate safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(storage_dir, safe_filename)
            
            # Save file
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved uploaded file: {file_path}")
        
        # Add user message to conversation
        conv_manager.add_message(
            session.session_id,
            role="user",
            content=message + (f" [File: {file.filename}]" if file else "")
        )
        
        # Call AgenticAssistant with all context
        result = await assistant.chat(
            message=message,
            conversation_manager=conv_manager,
            session_id=session.session_id,
            db=db,
            current_user=current_user,
            file_path=file_path
        )
        
        # Extract response
        response_text = result.get("answer", "")
        tool_calls = result.get("tool_calls", [])
        rich_ui = result.get("rich_ui")  # Extract rich UI component if present
        
        # Check if task was created
        task_created = len(tool_calls) > 0
        task_id = None
        task_type = None
        
        if task_created and len(tool_calls) > 0:
            # Get task info from first tool call
            first_tool = tool_calls[0]
            task_type = first_tool.get("tool")
            # Extract task_id from result if available
            task_result = first_tool.get("result", {})
            if isinstance(task_result, dict):
                task_id = task_result.get("task_id")
        
        # Get smart suggestions if conversation ongoing
        # Provide role-aware suggestions based on user permissions
        suggested_responses = []
        if not task_created and not rich_ui:  # Don't show suggestions if rich UI is present
            # Role-based suggestions (RBAC-compliant)
            user_role = current_user.get("role", "").lower()
            
            if user_role == "auditor":
                # Auditor can create projects and controls
                suggested_responses = [
                    "Show me recent projects",
                    "Create a new project",
                    "Create IM8 controls"
                ]
            elif user_role == "analyst":
                # Analyst can only upload evidence
                suggested_responses = [
                    "Show me recent projects",
                    "View available controls",
                    "Upload evidence for a control"
                ]
            else:
                # Default for other roles (viewer, etc.)
                suggested_responses = [
                    "Show me recent projects"
                ]
        
        # Extract sources from tool results (for RAG search_documents)
        sources = []
        for tool_call in tool_calls:
            if tool_call.get("tool") == "search_documents":
                result_data = tool_call.get("result", {})
                if isinstance(result_data, dict):
                    sources = result_data.get("sources", [])
        
        # Build response
        return ChatResponse(
            response=response_text,
            task_created=task_created,
            task_id=task_id,
            task_type=task_type,
            is_clarifying=not task_created,
            suggested_responses=suggested_responses,
            conversation_id=session.session_id,
            conversation_context=None,  # AgenticAssistant handles conversation internally
            parameters_collected={},
            parameters_missing=[],
            can_edit=True,
            rich_ui=rich_ui,  # Include rich UI component
            sources=sources,
            file_uploaded=file_path is not None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in context: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation context format. Please refresh the page and try again."
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        error_message = str(e).lower()
        
        # Database errors
        if "database" in error_message or "connection" in error_message:
            raise HTTPException(
                status_code=503,
                detail="Database connection error. Please try again in a moment."
            )
        
        # File system errors
        if "permission" in error_message or "access denied" in error_message:
            raise HTTPException(
                status_code=500,
                detail="File system error. Unable to save uploaded file."
            )
        
        # OpenAI/LLM errors
        if "rate limit" in error_message:
            raise HTTPException(
                status_code=429,
                detail="AI service rate limit exceeded. Please wait a moment and try again."
            )
        elif "api key" in error_message or "authentication" in error_message:
            raise HTTPException(
                status_code=503,
                detail="AI service authentication error. Please contact support."
            )
        elif "timeout" in error_message:
            raise HTTPException(
                status_code=504,
                detail="AI service timeout. Please try a simpler query."
            )
        
        # Generic error
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


@router.get("/capabilities")
async def get_capabilities():
    """Get list of available agentic capabilities"""
    # Get provider from AgenticAssistant (not LLMService) for accurate display
    try:
        assistant = AgenticAssistant()
        provider = assistant.provider
        model = assistant.model
        status = "active"
    except Exception as e:
        logger.error(f"Error initializing AgenticAssistant: {e}")
        provider = None
        model = None
        status = "unavailable"
    
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
        "status": status,
        "provider": provider,
        "model": model
    }


@router.get("/sessions/recent")
async def get_recent_session(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the most recent active conversation session for the current user"""
    try:
        conv_manager = ConversationManager(db, current_user["id"])
        sessions = conv_manager.get_active_sessions(limit=1)
        
        if not sessions or len(sessions) == 0:
            return {
                "session_id": None,
                "title": None,
                "messages": [],
                "created_at": None,
                "last_activity": None
            }
        
        session = sessions[0]
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "messages": session.messages or [],
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error fetching recent conversation session"
        )


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get message history for a conversation session"""
    try:
        conv_manager = ConversationManager(db, current_user["id"])
        session = conv_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Verify user owns this session
        if session.user_id != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You don't have permission to view this session"
            )
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "messages": session.messages or [],
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching session messages: {str(e)}"
        )

