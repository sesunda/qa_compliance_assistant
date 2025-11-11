import psycopg2
from datetime import datetime

# Database connection
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    sslmode="require"
)
cursor = conn.cursor()

print("\n=== Task #25 Timeline ===")
cursor.execute("""
    SELECT id, task_type, status, created_at, updated_at, result 
    FROM agent_tasks 
    WHERE id = 25
""")
task = cursor.fetchone()
print(f"Task ID: {task[0]}")
print(f"Type: {task[1]}")
print(f"Status: {task[2]}")
print(f"Created: {task[3]}")
print(f"Completed: {task[4]}")
print(f"Result: {task[5]}")

print("\n=== Project #11 Timeline ===")
cursor.execute("""
    SELECT id, name, created_at 
    FROM projects 
    WHERE id = 11
""")
project = cursor.fetchone()
print(f"Project ID: {project[0]}")
print(f"Name: {project[1]}")
print(f"Created: {project[2]}")

print("\n=== Conversation Messages Around Task #25 ===")
cursor.execute("""
    SELECT cs.id, cs.title, cs.created_at, cs.user_id
    FROM conversation_sessions cs
    WHERE cs.user_id = 6
    ORDER BY cs.created_at DESC
    LIMIT 1
""")
session = cursor.fetchone()
print(f"\nLatest Session ID: {session[0]}")
print(f"Title: {session[1]}")
print(f"Created: {session[2]}")

cursor.execute("""
    SELECT id, role, content, timestamp
    FROM conversation_messages
    WHERE session_id = %s
    ORDER BY timestamp ASC
""", (session[0],))

messages = cursor.fetchall()
print(f"\n=== All {len(messages)} Messages in Session ===")
for msg in messages:
    print(f"\n[{msg[1]}] at {msg[3]}:")
    content = msg[2][:200] if len(msg[2]) > 200 else msg[2]
    print(content)

cursor.close()
conn.close()
