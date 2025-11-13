#!/usr/bin/env python3
"""Check conversations for Analyst users"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# Database connection - Azure
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

print("=" * 80)
print("ANALYST CONVERSATIONS CHECK")
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

    # Get analyst users
    print("=" * 80)
    print("FINDING ANALYST USERS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT u.id, u.username, u.full_name, u.email, ur.name as role_name, a.name as agency_name
        FROM users u
        LEFT JOIN user_roles ur ON u.role_id = ur.id
        LEFT JOIN agencies a ON u.agency_id = a.id
        WHERE ur.name = 'Analyst'
        ORDER BY u.id
    """)
    
    analysts = cursor.fetchall()
    
    if not analysts:
        print("❌ No analyst users found!")
        cursor.close()
        conn.close()
        exit(1)
    
    print(f"\nFound {len(analysts)} analyst user(s):\n")
    for analyst in analysts:
        print(f"  ID: {analyst['id']}")
        print(f"  Username: {analyst['username']}")
        print(f"  Full Name: {analyst['full_name']}")
        print(f"  Email: {analyst['email']}")
        print(f"  Agency: {analyst['agency_name']}")
        print()

    # Check conversations for each analyst
    for analyst in analysts:
        print("=" * 80)
        print(f"CONVERSATIONS FOR: {analyst['full_name']} ({analyst['username']})")
        print("=" * 80)
        
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
        """, (analyst['id'],))
        
        conversations = cursor.fetchall()
        
        if not conversations:
            print(f"\n❌ No conversations found for {analyst['username']}\n")
            continue
        
        print(f"\n✓ Found {len(conversations)} conversation(s)\n")
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n{'─' * 80}")
            print(f"CONVERSATION #{i}")
            print(f"{'─' * 80}")
            print(f"ID: {conv['id']}")
            print(f"Session ID: {conv['session_id']}")
            print(f"Title: {conv['title'] or '(Untitled)'}")
            print(f"Created: {conv['created_at']}")
            print(f"Last Activity: {conv['last_activity']}")
            print(f"Status: {'🟢 Active' if conv['active'] else '🔴 Closed'}")
            
            # Parse messages
            messages = conv['messages'] if isinstance(conv['messages'], list) else []
            print(f"\nMessages: {len(messages)}")
            
            if messages:
                print("\n" + "─" * 80)
                print("MESSAGE HISTORY")
                print("─" * 80)
                
                for msg_idx, msg in enumerate(messages, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    timestamp = msg.get('timestamp', 'N/A')
                    
                    role_emoji = "👤" if role == "user" else "🤖"
                    print(f"\n{msg_idx}. {role_emoji} {role.upper()}")
                    print(f"   Time: {timestamp}")
                    print(f"   Content: {content[:200]}{'...' if len(content) > 200 else ''}")
                    
                    # Show tool calls if present
                    if 'tool_calls' in msg and msg['tool_calls']:
                        print(f"   🔧 Tool Calls:")
                        for tool in msg['tool_calls']:
                            tool_name = tool.get('tool', 'unknown')
                            print(f"      - {tool_name}")
                    
                    # Show task ID if present
                    if 'task_id' in msg:
                        print(f"   📋 Task ID: {msg['task_id']}")
            
            # Show context if present
            if conv['context']:
                print("\n" + "─" * 80)
                print("CONVERSATION CONTEXT")
                print("─" * 80)
                context = conv['context'] if isinstance(conv['context'], dict) else {}
                print(json.dumps(context, indent=2))
            
            print()

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_conversations,
            COUNT(CASE WHEN active = true THEN 1 END) as active_conversations,
            COUNT(CASE WHEN active = false THEN 1 END) as closed_conversations,
            MIN(created_at) as first_conversation,
            MAX(last_activity) as most_recent_activity
        FROM conversation_sessions cs
        JOIN users u ON cs.user_id = u.id
        JOIN user_roles ur ON u.role_id = ur.id
        WHERE ur.name = 'Analyst'
    """)
    
    stats = cursor.fetchone()
    
    print(f"\nTotal Conversations: {stats['total_conversations']}")
    print(f"Active: {stats['active_conversations']}")
    print(f"Closed: {stats['closed_conversations']}")
    
    if stats['first_conversation']:
        print(f"First Conversation: {stats['first_conversation']}")
    if stats['most_recent_activity']:
        print(f"Most Recent Activity: {stats['most_recent_activity']}")
    
    # Message count per conversation
    cursor.execute("""
        SELECT 
            cs.session_id,
            cs.title,
            u.username,
            jsonb_array_length(cs.messages) as message_count
        FROM conversation_sessions cs
        JOIN users u ON cs.user_id = u.id
        JOIN user_roles ur ON u.role_id = ur.id
        WHERE ur.name = 'Analyst'
        ORDER BY message_count DESC
    """)
    
    msg_stats = cursor.fetchall()
    
    if msg_stats:
        print("\n\nMessage Count by Conversation:")
        print("─" * 80)
        for stat in msg_stats:
            print(f"{stat['username']:20} | {stat['title'] or '(Untitled)':40} | {stat['message_count']:3} messages")

    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ DONE!")
    print("=" * 80)

except psycopg2.Error as e:
    print(f"\n❌ Database error: {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
