"""
Comprehensive validation for Assessment model vs create_assessment tool
"""
import os
import sys
from sqlalchemy import create_engine, inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api', 'src'))
from api.src import models

def validate_assessment_fields():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    engine = create_engine(database_url)
    
    try:
        print("\n" + "=" * 80)
        print("ASSESSMENT FIELD VALIDATION")
        print("=" * 80)
        
        # Get database columns
        inspector = inspect(engine)
        db_columns = {}
        for col in inspector.get_columns('assessments'):
            db_columns[col['name']] = {
                'nullable': col['nullable'],
                'default': col.get('default')
            }
        
        # Get model columns
        model_columns = set(models.Assessment.__table__.columns.keys())
        
        # Fields set by create_assessment code
        code_sets_fields = {
            'project_id',
            'agency_id',
            'name',
            'description',
            'assessment_type',
            'framework',
            'status',
            'scope',
            'planned_start_date',
            'planned_end_date',
            'lead_assessor_user_id',
            'created_by_user_id'
        }
        
        # Find required fields
        auto_fields = {'id', 'created_at', 'updated_at'}
        required_fields = [
            col for col, info in db_columns.items()
            if col not in auto_fields and not info['nullable'] and info['default'] is None
        ]
        
        print(f"\nRequired fields: {len(required_fields)}")
        print(f"Code sets: {len(code_sets_fields)} fields\n")
        
        has_errors = False
        for field in sorted(required_fields):
            in_model = field in model_columns
            in_code = field in code_sets_fields
            
            status = "✅" if (in_model and in_code) else "❌"
            print(f"  {field:30} | Model: {'✅' if in_model else '❌':3} | Code: {'✅' if in_code else '❌':3} | {status}")
            
            if not in_code:
                has_errors = True
        
        if has_errors:
            print("\n❌ Assessment creation may fail!")
            return False
        else:
            print("\n✅ All Assessment required fields are set!")
            return True
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = validate_assessment_fields()
    sys.exit(0 if success else 1)
