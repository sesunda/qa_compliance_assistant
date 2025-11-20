"""
Migration: Add business_impact column to findings table
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api', 'src'))

def run_migration():
    """Add business_impact column to findings table"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='findings' AND column_name='business_impact'
            """))
            
            if result.fetchone():
                print("✅ business_impact column already exists in findings table")
                return True
            
            # Add the column
            print("Adding business_impact column to findings table...")
            conn.execute(text("""
                ALTER TABLE findings 
                ADD COLUMN business_impact TEXT NULL
            """))
            conn.commit()
            
            print("✅ Successfully added business_impact column to findings table")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
