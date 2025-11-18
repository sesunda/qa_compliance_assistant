import psycopg2

# Same connection as check_conversation.py
conn = psycopg2.connect('postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db')
cur = conn.cursor()

print("\n🔍 Checking current data...")

# Get counts before deletion
cur.execute("SELECT COUNT(*) FROM conversation_sessions")
conv_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM agent_tasks")
task_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM evidence")
evidence_count = cur.fetchone()[0]

print(f"\nBefore deletion:")
print(f"  Conversations: {conv_count}")
print(f"  Agent tasks: {task_count}")
print(f"  Evidence: {evidence_count}")

if conv_count == 0 and task_count == 0 and evidence_count == 0:
    print("\n✓ Database is already clean!")
    conn.close()
    exit(0)

# Delete all data
print("\n🗑️  Deleting all data...")
cur.execute("DELETE FROM conversation_sessions")
cur.execute("DELETE FROM agent_tasks")
cur.execute("DELETE FROM evidence")

conn.commit()

print(f"\n✓ Deleted:")
print(f"  {conv_count} conversations")
print(f"  {task_count} agent tasks")
print(f"  {evidence_count} evidence items")

# Verify deletion
cur.execute("SELECT COUNT(*) FROM conversation_sessions")
conv_remaining = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM agent_tasks")
task_remaining = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM evidence")
evidence_remaining = cur.fetchone()[0]

print(f"\nAfter deletion:")
print(f"  Conversations remaining: {conv_remaining}")
print(f"  Agent tasks remaining: {task_remaining}")
print(f"  Evidence remaining: {evidence_remaining}")

print("\n✅ All data cleared successfully!")
print("\n📝 Next steps:")
print("   1. Refresh the frontend")
print("   2. Start a new conversation to test optimized AI (revision 0000065)")
print("   3. Observe: Single focused questions, no random tangents\n")

conn.close()
