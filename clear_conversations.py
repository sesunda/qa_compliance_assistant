"""Clear conversation history from PostgreSQL database"""
import os
import sys
import psycopg2
from getpass import getpass

# Database configuration
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_NAME = "qca_db"
DB_USER = "qcaadmin"

def clear_conversations():
    """Delete all conversation sessions from database"""
    print("\n🗑️  Clearing Conversation History...\n")
    
    # Get password
    password = getpass("Enter PostgreSQL admin password: ")
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=password,
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        # Execute delete
        print("Deleting conversation sessions (including all messages)...")
        cursor.execute("DELETE FROM conversation_sessions;")
        deleted_count = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM conversation_sessions;")
        remaining = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Successfully deleted {deleted_count} conversation sessions with all their messages!")
        print(f"   Remaining conversations: {remaining}")
        print("\n📝 Next steps:")
        print("   1. Refresh the frontend (Ctrl+F5)")
        print("   2. Start a new conversation")
        print("   3. All timestamps will now show Singapore time (SGT)\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    clear_conversations()
