"""
Conversation Session Router
Endpoints for managing multi-turn conversations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.src.database import get_db
from api.src.auth import get_current_user
from api.src.models import User
from api.src.schemas import (
    ConversationSession,
    ConversationSessionCreate,
    ConversationSessionUpdate,
    ConversationSessionSummary
)
from api.src.services.conversation_manager import ConversationManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationSession)
async def create_conversation_session(
    session_data: ConversationSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation session"""
    try:
        manager = ConversationManager(db, current_user["id"])
        session = manager.create_session(title=session_data.title)
        
        return ConversationSession(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            messages=[],
            context=session.context,
            created_at=session.created_at,
            last_activity=session.last_activity,
            active=session.active
        )
    except Exception as e:
        logger.error(f"Error creating conversation session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ConversationSessionSummary])
async def list_conversation_sessions(
    active_only: bool = True,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List conversation sessions for current user"""
    try:
        manager = ConversationManager(db, current_user["id"])
        
        if active_only:
            sessions = manager.get_active_sessions(limit=limit)
        else:
            sessions = manager.get_all_sessions(limit=limit)
        
        return [
            ConversationSessionSummary(
                id=s.id,
                session_id=s.session_id,
                title=s.title,
                message_count=len(s.messages or []),
                created_at=s.created_at,
                last_activity=s.last_activity,
                active=s.active
            )
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=ConversationSession)
async def get_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation session by ID with full message history"""
    try:
        manager = ConversationManager(db, current_user["id"])
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return ConversationSession(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            messages=session.messages or [],
            context=session.context,
            created_at=session.created_at,
            last_activity=session.last_activity,
            active=session.active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{session_id}", response_model=ConversationSession)
async def update_conversation_session(
    session_id: str,
    updates: ConversationSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update conversation session (title, active status)"""
    try:
        manager = ConversationManager(db, current_user["id"])
        session = manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if updates.title is not None:
            session = manager.update_title(session_id, updates.title)
        
        if updates.active is not None:
            if not updates.active:
                session = manager.close_session(session_id)
            else:
                session.active = True
                db.commit()
                db.refresh(session)
        
        return ConversationSession(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title,
            messages=session.messages or [],
            context=session.context,
            created_at=session.created_at,
            last_activity=session.last_activity,
            active=session.active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def close_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Close/deactivate a conversation session"""
    try:
        manager = ConversationManager(db, current_user["id"])
        session = manager.close_session(session_id)
        
        return {"message": "Session closed successfully", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing conversation session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
