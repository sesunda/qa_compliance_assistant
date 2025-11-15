"""Conversation Session Manager
Handles multi-turn conversation state and context management
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc

from api.src.models import ConversationSession, User
from api.src.schemas import ConversationMessage
import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation sessions and message history"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def create_session(self, title: Optional[str] = None, session_id: Optional[str] = None) -> ConversationSession:
        """Create a new conversation session
        
        Args:
            title: Optional title for the session
            session_id: Optional custom session ID (if not provided, generates UUID)
            
        Returns:
            ConversationSession object
            
        Raises:
            ValueError: If provided session_id already exists in database
        """
        # Use provided session_id or generate new one
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check if session_id already exists
        existing = self.db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id
        ).first()
        
        if existing:
            raise ValueError(f"Session ID {session_id} already exists")
        
        # Generate default title if not provided
        if not title:
            title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        db_session = ConversationSession(
            session_id=session_id,
            user_id=self.user_id,
            title=title,
            messages=[],
            context={},
            active=True
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        logger.info(f"Created conversation session {session_id} for user {self.user_id}")
        return db_session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID"""
        return self.db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id,
            ConversationSession.user_id == self.user_id
        ).first()
    
    def get_active_sessions(self, limit: int = 10) -> List[ConversationSession]:
        """Get active conversation sessions for user"""
        return self.db.query(ConversationSession).filter(
            ConversationSession.user_id == self.user_id,
            ConversationSession.active == True
        ).order_by(desc(ConversationSession.last_activity)).limit(limit).all()
    
    def get_all_sessions(self, limit: int = 50) -> List[ConversationSession]:
        """Get all conversation sessions for user"""
        return self.db.query(ConversationSession).filter(
            ConversationSession.user_id == self.user_id
        ).order_by(desc(ConversationSession.last_activity)).limit(limit).all()
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        task_id: Optional[int] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationSession:
        """Add a message to conversation session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Create message
        # CRITICAL: Use datetime.now(timezone.utc) for proper timezone-aware timestamp
        # This ensures ISO format includes 'Z' suffix for unambiguous UTC time
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "tool_calls": tool_calls
        }
        
        # Append to messages
        messages = session.messages or []
        messages.append(message)
        
        # Update session - IMPORTANT: flag_modified needed for JSONB updates
        session.messages = messages
        flag_modified(session, "messages")
        session.last_activity = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Added {role} message to session {session_id}")
        return session
    
    def update_context(
        self, 
        session_id: str, 
        context_updates: Dict[str, Any]
    ) -> ConversationSession:
        """Update conversation context (extracted entities, control IDs, etc)"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Merge context updates
        current_context = session.context or {}
        current_context.update(context_updates)
        
        session.context = current_context
        flag_modified(session, "context")
        session.last_activity = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Updated context for session {session_id}: {context_updates}")
        return session
    
    def close_session(self, session_id: str) -> ConversationSession:
        """Mark conversation session as inactive"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.active = False
        session.last_activity = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Closed session {session_id}")
        return session
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages or []
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get current conversation context"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return session.context or {}
    
    def update_title(self, session_id: str, title: str) -> ConversationSession:
        """Update session title"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.title = title
        self.db.commit()
        self.db.refresh(session)
        
        return session
