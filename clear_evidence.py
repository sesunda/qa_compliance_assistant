"""
Clean up evidence database for fresh testing
Removes all evidence records while preserving controls and other data
"""
import os
import psycopg2

db_url = os.getenv("DATABASE_URL", "")

if not db_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Get count before deletion
    cur.execute("SELECT COUNT(*) FROM evidence")
    count_before = cur.fetchone()[0]
    print(f"Total evidence records before cleanup: {count_before}")
    
    # Show breakdown by status
    cur.execute("""
        SELECT verification_status, COUNT(*) 
        FROM evidence 
        GROUP BY verification_status
        ORDER BY COUNT(*) DESC
    """)
    print("\nBreakdown by status:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} records")
    
    # Confirm deletion
    print(f"\n⚠️  This will DELETE all {count_before} evidence records!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("Cancelled. No changes made.")
        exit(0)
    
    # Delete all evidence records
    cur.execute("DELETE FROM evidence")
    deleted = cur.rowcount
    
    conn.commit()
    
    print(f"\n✅ Deleted {deleted} evidence records")
    print("✅ Evidence database cleaned for fresh testing")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
