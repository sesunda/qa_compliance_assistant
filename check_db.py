from api.src.database import SessionLocal
from api.src.models import User, ConversationSession
from sqlalchemy import desc
import json

db = SessionLocal()
try:
    alice = db.query(User).filter(User.username == 'alice').first()
    if not alice:
        print("ERROR: Alice not found!")
        exit(1)
    
    print(f"Alice User ID: {alice.id}")
    print(f"Alice Role: {alice.role}")
    print()
    
    sessions = db.query(ConversationSession).filter(
        ConversationSession.user_id == alice.id
    ).order_by(desc(ConversationSession.last_activity)).all()
    
    print(f"Total conversation sessions for Alice: {len(sessions)}")
    print("=" * 80)
    
    for i, session in enumerate(sessions, 1):
        print(f"\n[Session {i}]")
        print(f"  Session ID: {session.session_id}")
        print(f"  Title: {session.title}")
        print(f"  Active: {session.active}")
        print(f"  Created: {session.created_at}")
        print(f"  Last Activity: {session.last_activity}")
        print(f"  Message Count: {len(session.messages or [])}")
        
        if session.messages:
            print(f"  First message preview: {session.messages[0].get('content', '')[:100]}...")
            print(f"  Last message preview: {session.messages[-1].get('content', '')[:100]}...")
    
finally:
    db.close()
