#!/usr/bin/env python3
"""Check Alice's conversation history from Azure database"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# Azure Database connection
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

print("=" * 80)
print("ALICE'S CONVERSATION CHECK - AZURE DATABASE")
print("=" * 80)

try:
    print("\nConnecting to Azure database...")
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        sslmode="require",
        cursor_factory=RealDictCursor
    )
    cursor = conn.cursor()
    print("✓ Connected successfully\n")

    # Find Alice
    cursor.execute("""
        SELECT u.id, u.username, u.full_name, u.email, ur.name as role_name
        FROM users u
        LEFT JOIN user_roles ur ON u.role_id = ur.id
        WHERE u.username = 'alice'
    """)
    
    alice = cursor.fetchone()
    if not alice:
        print("❌ Alice not found!")
        cursor.close()
        conn.close()
        exit(1)
    
    print(f"👤 User Found:")
    print(f"   ID: {alice['id']}")
    print(f"   Username: {alice['username']}")
    print(f"   Full Name: {alice['full_name']}")
    print(f"   Email: {alice['email']}")
    print(f"   Role: {alice['role_name']}")
    print()
    
    # Get most recent conversation session
    cursor.execute("""
        SELECT 
            cs.id,
            cs.session_id,
            cs.title,
            cs.messages,
            cs.context,
            cs.created_at,
            cs.last_activity,
            cs.active
        FROM conversation_sessions cs
        WHERE cs.user_id = %s
        ORDER BY cs.last_activity DESC
        LIMIT 3
    """, (alice['id'],))
    
    sessions = cursor.fetchall()
    
    print(f"📊 Total sessions found: {len(sessions)}")
    print()
    
    for idx, session in enumerate(sessions, 1):
        print("=" * 80)
        print(f"SESSION #{idx} - {session['title'] or '(Untitled)'}")
        print("=" * 80)
        print(f"Session ID: {session['session_id']}")
        print(f"Status: {'🟢 Active' if session['active'] else '🔴 Closed'}")
        print(f"Created: {session['created_at']}")
        print(f"Last Activity: {session['last_activity']}")
        
        messages = session['messages'] if isinstance(session['messages'], list) else []
        print(f"Message Count: {len(messages)}")
        print()
        
        if messages:
            print("─" * 80)
            print("CONVERSATION MESSAGES:")
            print("─" * 80)
            
            for i, msg in enumerate(messages, 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', 'N/A')
                
                role_emoji = "👤" if role == "user" else "🤖"
                print(f"\n[Message {i}] {role_emoji} {role.upper()}")
                print(f"Timestamp: {timestamp}")
                print(f"Content:")
                print(content)
                
                if 'tool_calls' in msg and msg['tool_calls']:
                    print(f"\n🔧 Tool Calls:")
                    for tool in msg['tool_calls']:
                        print(f"   - {tool.get('tool', 'unknown')}")
                
                if 'task_id' in msg:
                    print(f"📋 Task ID: {msg['task_id']}")
                
                print("─" * 80)
        else:
            print("No messages in this session.")
        
        print("\n")
    
    if not sessions:
        print("❌ No conversation sessions found for Alice.")
    
    cursor.close()
    conn.close()
    
    print("=" * 80)
    print("✅ DONE!")
    print("=" * 80)

except psycopg2.Error as e:
    print(f"\n❌ Database error: {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
