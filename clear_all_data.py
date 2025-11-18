"""Clear all conversation history, evidence, and tasks from database"""
import sys
from sqlalchemy import create_engine, text

# Database URL - Updated to match check_conversation.py connection
DATABASE_URL = "postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db"

def clear_all_data():
    """Delete all conversations, messages, evidence, and tasks"""
    print("\n🗑️  Clearing All Data...\n")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("Connected to database")
            
            # Get counts before deletion
            conv_count = conn.execute(text("SELECT COUNT(*) FROM conversation_sessions")).scalar()
            msg_count = conn.execute(text("SELECT COUNT(*) FROM conversation_sessions WHERE messages IS NOT NULL AND json_array_length(messages::json) > 0")).scalar()
            evidence_count = conn.execute(text("SELECT COUNT(*) FROM evidence")).scalar()
            task_count = conn.execute(text("SELECT COUNT(*) FROM agent_tasks")).scalar()
            
            print(f"\nBefore deletion:")
            print(f"  Conversation Sessions: {conv_count}")
            print(f"  Sessions with Messages: {msg_count}")
            print(f"  Evidence: {evidence_count}")
            print(f"  Agent tasks: {task_count}")
            
            if conv_count == 0 and evidence_count == 0 and task_count == 0:
                print("\n✓ Database is already clean!")
                return
            
            # Confirm deletion
            response = input(f"\n⚠️  Delete all data? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return
            
            # Delete all data in transaction
            print("\nDeleting...")
            conn.execute(text("DELETE FROM conversation_sessions"))
            conn.execute(text("DELETE FROM evidence"))
            conn.execute(text("DELETE FROM agent_tasks"))
            
            conn.commit()
            
            print(f"\nDeleted:")
            print(f"  {conv_count} conversation sessions")
            print(f"  {evidence_count} evidence items")
            print(f"  {task_count} agent tasks")
            
            # Verify deletion
            conv_remaining = conn.execute(text("SELECT COUNT(*) FROM conversation_sessions")).scalar()
            evidence_remaining = conn.execute(text("SELECT COUNT(*) FROM evidence")).scalar()
            task_remaining = conn.execute(text("SELECT COUNT(*) FROM agent_tasks")).scalar()
            
            print(f"\nAfter deletion:")
            print(f"  Conversation sessions remaining: {conv_remaining}")
            print(f"  Evidence remaining: {evidence_remaining}")
            print(f"  Agent tasks remaining: {task_remaining}")
            
            print("\n✓ All data cleared successfully!")
            print("\n📝 Next steps:")
            print("   1. Refresh the frontend")
            print("   2. Start a new conversation to test optimized AI\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    clear_all_data()
