"""
Verify business_impact column exists in findings table
"""
import os
import sys
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api', 'src'))

def verify_column():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check column exists
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='findings' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"\n✅ Findings table has {len(columns)} columns:\n")
            
            business_impact_found = False
            for col in columns:
                col_name, data_type, nullable = col
                marker = "👉" if col_name == 'business_impact' else "  "
                print(f"{marker} {col_name:35} {data_type:15} nullable={nullable}")
                if col_name == 'business_impact':
                    business_impact_found = True
            
            if business_impact_found:
                print("\n✅ business_impact column confirmed in database!")
                return True
            else:
                print("\n❌ business_impact column NOT found")
                return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = verify_column()
    sys.exit(0 if success else 1)
