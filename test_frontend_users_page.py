"""
Frontend role-based UI test - Simulates what Users Page does
Tests if each role can:
1. Login successfully
2. Get current user info (/auth/me)
3. Fetch users list (/auth/users)
4. See proper role information returned
"""
import requests
import json

API_BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

TEST_SCENARIOS = [
    {
        "role_name": "Admin (HSA)",
        "username": "hsa_admin",
        "password": "admin123",
        "expected_db_role": "Admin",
        "expected_api_role": "admin",
        "should_see_users": True,
        "should_create_users": True,
    },
    {
        "role_name": "Analyst (Alice Tan)",
        "username": "hsa_analyst",
        "password": "analyst123",
        "expected_db_role": "Analyst",
        "expected_api_role": "analyst",
        "should_see_users": True,
        "should_create_users": False,
    },
    {
        "role_name": "QA Reviewer",
        "username": "hsa_qa",
        "password": "qa123",
        "expected_db_role": "QA Reviewer",
        "expected_api_role": "qa reviewer",
        "should_see_users": False,
        "should_create_users": False,
    },
    {
        "role_name": "Auditor",
        "username": "auditor1",
        "password": "auditor123",
        "expected_db_role": "Auditor",
        "expected_api_role": "auditor",
        "should_see_users": True,
        "should_create_users": False,
    },
]


def test_user_page_flow(scenario: dict):
    """Simulate the Users Page loading flow for a specific user"""
    print(f"\n{'='*80}")
    print(f"Testing: {scenario['role_name']} ({scenario['username']})")
    print(f"{'='*80}")
    
    # Step 1: Login
    print("\n[1] Login...")
    try:
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": scenario["username"], "password": scenario["password"]},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"  ✗ Login FAILED: {login_response.status_code}")
            print(f"    Response: {login_response.text}")
            return False
        
        token = login_response.json().get("access_token")
        print(f"  ✓ Login successful")
        print(f"    Token: {token[:20]}...")
        
    except Exception as e:
        print(f"  ✗ Login ERROR: {str(e)}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Get current user (/auth/me) - This is what frontend does on load
    print("\n[2] Fetching current user info (/auth/me)...")
    try:
        me_response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers, timeout=10)
        
        if me_response.status_code != 200:
            print(f"  ✗ Get /auth/me FAILED: {me_response.status_code}")
            return False
        
        user_data = me_response.json()
        print(f"  ✓ User info retrieved")
        print(f"    Username: {user_data.get('username')}")
        print(f"    Email: {user_data.get('email')}")
        print(f"    Role (from DB): {user_data.get('role', {}).get('name', 'N/A')}")
        print(f"    Role (API normalized): <check current_user dict>")
        
        # Check if role matches expected
        db_role = user_data.get('role', {}).get('name')
        if db_role != scenario['expected_db_role']:
            print(f"  ⚠ WARNING: DB role mismatch! Expected '{scenario['expected_db_role']}', got '{db_role}'")
        
    except Exception as e:
        print(f"  ✗ Get /auth/me ERROR: {str(e)}")
        return False
    
    # Step 3: Fetch users list (/auth/users) - This is what Users Page does
    print(f"\n[3] Fetching users list (/auth/users)...")
    print(f"    Expected: {'✓ Should load' if scenario['should_see_users'] else '✗ Should be forbidden'}")
    
    try:
        users_response = requests.get(f"{API_BASE_URL}/auth/users", headers=headers, timeout=10)
        
        if scenario['should_see_users']:
            # Should succeed
            if users_response.status_code == 200:
                users = users_response.json()
                print(f"  ✓ Users list loaded successfully")
                print(f"    Total users: {len(users)}")
                if users:
                    print(f"    First user: {users[0].get('username')} ({users[0].get('email')})")
                return True
            else:
                print(f"  ✗ FAILED: Expected 200, got {users_response.status_code}")
                print(f"    Error: {users_response.text}")
                return False
        else:
            # Should be forbidden
            if users_response.status_code == 403:
                print(f"  ✓ Correctly blocked (403 Forbidden)")
                return True
            elif users_response.status_code == 200:
                print(f"  ✗ FAILED: Should be forbidden, but got 200!")
                return False
            else:
                print(f"  ⚠ Unexpected status: {users_response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ✗ Fetch users ERROR: {str(e)}")
        return False


def main():
    print("="*80)
    print("FRONTEND USERS PAGE SIMULATION TEST")
    print("="*80)
    print(f"\nAPI: {API_BASE_URL}")
    print(f"Testing {len(TEST_SCENARIOS)} user roles\n")
    
    results = []
    for scenario in TEST_SCENARIOS:
        success = test_user_page_flow(scenario)
        results.append({
            "role": scenario["role_name"],
            "success": success
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    for result in results:
        icon = "✓" if result["success"] else "✗"
        print(f"  {icon} {result['role']}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"\n{'='*80}")
    print(f"Result: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*80}\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
