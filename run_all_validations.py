"""
Master validation script - runs all validations before deployment
"""
import subprocess
import sys
import os

def run_validation(script_name, description):
    """Run a validation script and report results"""
    print("\n" + "=" * 80)
    print(f"Running: {description}")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            [r"C:\ProgramData\anaconda3\python.exe", script_name],
            capture_output=False,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE PRE-DEPLOYMENT VALIDATION SUITE")
    print("=" * 80)
    print("\nThis will validate ALL field mappings before deployment")
    print("Environment: Azure PostgreSQL Database")
    print()
    
    # Check DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nSet it with:")
        print('$env:DATABASE_URL = "postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db?sslmode=require"')
        return False
    
    validations = [
        ("validate_finding_fields.py", "Finding Model Field Validation"),
        ("test_finding_creation_exact.py", "Finding Creation E2E Test"),
        ("validate_assessment_fields.py", "Assessment Model Field Validation"),
        ("check_assessment_created.py", "Assessment Creation E2E Test (existing)"),
        ("test_analytics_fields.py", "Analytics Field Name Validation"),
    ]
    
    results = {}
    for script, description in validations:
        if os.path.exists(script):
            results[description] = run_validation(script, description)
        else:
            print(f"\n⚠️  Skipping {description} - script not found: {script}")
            results[description] = None
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80 + "\n")
    
    all_passed = True
    for description, passed in results.items():
        if passed is None:
            status = "⚠️  SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
            all_passed = False
        
        print(f"{status:12} | {description}")
    
    print("\n" + "=" * 80)
    if all_passed and None not in results.values():
        print("✅ ALL VALIDATIONS PASSED - SAFE TO DEPLOY")
    else:
        print("❌ SOME VALIDATIONS FAILED - DO NOT DEPLOY")
        print("\nFix the issues above before building and deploying!")
    print("=" * 80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
