import psycopg2
import json
from datetime import datetime

conn = psycopg2.connect('postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db')
cur = conn.cursor()

# Get the most recent conversation
cur.execute("""
    SELECT session_id, user_id, title, messages, created_at, last_activity 
    FROM conversation_sessions 
    ORDER BY last_activity DESC 
    LIMIT 1
""")

row = cur.fetchone()
if row:
    print(f"\n{'='*100}")
    print(f"RECENT CONVERSATION ANALYSIS")
    print(f"{'='*100}")
    print(f"Session ID: {row[0]}")
    print(f"User ID: {row[1]}")
    print(f"Title: {row[2]}")
    print(f"Created: {row[4]}")
    print(f"Last Activity: {row[5]}")
    print(f"{'='*100}\n")
    
    messages = row[3] if row[3] else []
    print(f"Total Messages: {len(messages)}\n")
    
    for i, msg in enumerate(messages):
        role = msg.get('role', 'unknown').upper()
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', 'N/A')
        
        print(f"\n{'─'*100}")
        print(f"Message {i+1} [{role}] - {timestamp}")
        print(f"{'─'*100}")
        
        # Truncate very long content for readability
        if len(content) > 2000:
            print(content[:2000])
            print(f"\n... [TRUNCATED - {len(content) - 2000} more characters] ...")
        else:
            print(content)
        
        # Check for tool calls in assistant messages
        if role == 'ASSISTANT' and 'tool_calls' in msg and msg.get('tool_calls'):
            print(f"\n{'─'*50}")
            print("TOOL CALLS:")
            print(f"{'─'*50}")
            tool_calls = msg.get('tool_calls', [])
            if tool_calls and isinstance(tool_calls, list):
                for tool_call in tool_calls:
                    print(f"  Function: {tool_call.get('function', {}).get('name', 'unknown')}")
                    print(f"  Arguments: {tool_call.get('function', {}).get('arguments', '{}')}")
        
        # Check for tool results
        if role == 'TOOL':
            print(f"\n{'─'*50}")
            print("TOOL RESULT:")
            print(f"{'─'*50}")
            try:
                result_data = json.loads(content) if isinstance(content, str) else content
                print(json.dumps(result_data, indent=2))
            except:
                print(content)

# Check if any agent tasks were created
print(f"\n\n{'='*100}")
print("AGENT TASKS FROM THIS SESSION")
print(f"{'='*100}")

cur.execute("""
    SELECT id, task_type, status, title, created_by, payload, result, 
           created_at, started_at, completed_at
    FROM agent_tasks 
    WHERE created_at >= (SELECT created_at FROM conversation_sessions ORDER BY last_activity DESC LIMIT 1)
    ORDER BY created_at DESC
""")

tasks = cur.fetchall()
if tasks:
    for task in tasks:
        print(f"\n{'─'*100}")
        print(f"Task ID: {task[0]}")
        print(f"Type: {task[1]}")
        print(f"Status: {task[2]}")
        print(f"Title: {task[3]}")
        print(f"Created By User ID: {task[4]}")
        print(f"Created: {task[7]}")
        print(f"Started: {task[8]}")
        print(f"Completed: {task[9]}")
        print(f"\nPayload:")
        print(json.dumps(task[5], indent=2) if task[5] else "None")
        print(f"\nResult:")
        print(json.dumps(task[6], indent=2) if task[6] else "None")
else:
    print("\nNo agent tasks found for this session.")

# Check if any evidence was created
print(f"\n\n{'='*100}")
print("EVIDENCE RECORDS FROM THIS SESSION")
print(f"{'='*100}")

cur.execute("""
    SELECT id, control_id, title, description, file_path, evidence_type,
           uploaded_by, created_at
    FROM evidence 
    WHERE created_at >= (SELECT created_at FROM conversation_sessions ORDER BY last_activity DESC LIMIT 1)
    ORDER BY created_at DESC
""")

evidence_records = cur.fetchall()
if evidence_records:
    for evidence in evidence_records:
        print(f"\n{'─'*100}")
        print(f"Evidence ID: {evidence[0]}")
        print(f"Control ID: {evidence[1]}")
        print(f"Title: {evidence[2]}")
        print(f"Description: {evidence[3]}")
        print(f"File Path: {evidence[4]}")
        print(f"Evidence Type: {evidence[5]}")
        print(f"Uploaded By User ID: {evidence[6]}")
        print(f"Created: {evidence[7]}")
else:
    print("\nNo evidence records found for this session.")

conn.close()

print(f"\n{'='*100}")
print("ANALYSIS COMPLETE")
print(f"{'='*100}")
