"""
Test script for conversation session fix
Tests create_session() with and without session_id parameter
"""
import requests
import json
import uuid

API_BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Test users
TEST_USERS = {
    "auditor": {"username": "auditor1", "password": "auditor123"},
    "analyst": {"username": "hsa_analyst", "password": "analyst123"},
    "admin": {"username": "hsa_admin", "password": "admin123"},
}

def login(credentials):
    """Login and get token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json=credentials,
        timeout=10
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception(f"Login failed: {response.status_code} - {response.text}")

def test_conversation_scenarios(role, credentials):
    """Test all conversation scenarios"""
    print(f"\n{'='*80}")
    print(f"Testing: {role.upper()}")
    print(f"{'='*80}")
    
    # Login
    print("\n[1] Logging in...")
    token = login(credentials)
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  [OK] Logged in successfully")
    
    # Scenario 1: New conversation (no conversation_id)
    print("\n[2] Test: New conversation (no conversation_id)")
    try:
        formData = {
            'message': 'Hello, this is my first message'
        }
        response = requests.post(
            f"{API_BASE_URL}/agentic-chat/",
            data=formData,
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            conv_id_1 = data.get('conversation_id')
            print(f"  [OK] New conversation created")
            print(f"      Conversation ID: {conv_id_1}")
        else:
            print(f"  [FAIL] Status: {response.status_code}")
            print(f"      Error: {response.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {str(e)}")
        return False
    
    # Scenario 2: Continue existing conversation
    print("\n[3] Test: Continue existing conversation")
    try:
        formData = {
            'message': 'This is my second message',
            'conversation_id': conv_id_1
        }
        response = requests.post(
            f"{API_BASE_URL}/agentic-chat/",
            data=formData,
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            conv_id_2 = data.get('conversation_id')
            print(f"  [OK] Continued conversation")
            print(f"      Conversation ID: {conv_id_2}")
            if conv_id_1 == conv_id_2:
                print(f"      [OK] Same conversation ID maintained")
            else:
                print(f"      [WARN] Different conversation ID!")
        else:
            print(f"  [FAIL] Status: {response.status_code}")
            print(f"      Error: {response.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {str(e)}")
        return False
    
    # Scenario 3: Orphaned session ID (the bug scenario)
    print("\n[4] Test: Orphaned session ID (simulates localStorage issue)")
    fake_session_id = str(uuid.uuid4())
    try:
        formData = {
            'message': 'This message has a fake session ID',
            'conversation_id': fake_session_id
        }
        response = requests.post(
            f"{API_BASE_URL}/agentic-chat/",
            data=formData,
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            conv_id_3 = data.get('conversation_id')
            print(f"  [OK] Handled orphaned session gracefully")
            print(f"      New Conversation ID: {conv_id_3}")
            if conv_id_3 == fake_session_id:
                print(f"      [OK] Used provided session ID")
            else:
                print(f"      [INFO] Generated new session ID")
        else:
            print(f"  [FAIL] Status: {response.status_code}")
            print(f"      Error: {response.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {str(e)}")
        return False
    
    # Scenario 4: Multiple messages in sequence
    print("\n[5] Test: Multiple messages in same conversation")
    try:
        for i in range(3):
            formData = {
                'message': f'Message {i+1} in conversation',
                'conversation_id': conv_id_1
            }
            response = requests.post(
                f"{API_BASE_URL}/agentic-chat/",
                data=formData,
                headers=headers,
                timeout=120
            )
            if response.status_code != 200:
                print(f"  [FAIL] Message {i+1} failed: {response.status_code}")
                return False
        print(f"  [OK] Sent 3 messages successfully in same conversation")
    except Exception as e:
        print(f"  [FAIL] Error: {str(e)}")
        return False
    
    print(f"\n  [SUCCESS] All scenarios passed for {role}")
    return True

def main():
    print("="*80)
    print("CONVERSATION SESSION FIX - COMPREHENSIVE TEST")
    print("="*80)
    print(f"\nAPI: {API_BASE_URL}")
    print(f"Testing {len(TEST_USERS)} roles\n")
    
    results = []
    for role, credentials in TEST_USERS.items():
        try:
            success = test_conversation_scenarios(role, credentials)
            results.append({"role": role, "success": success})
        except Exception as e:
            print(f"\n[ERROR] {role} test failed: {str(e)}")
            results.append({"role": role, "success": False})
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    for result in results:
        icon = "[PASS]" if result["success"] else "[FAIL]"
        print(f"  {icon} {result['role'].upper()}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"\n{'='*80}")
    print(f"Result: {passed}/{total} roles passed ({passed/total*100:.0f}%)")
    print(f"{'='*80}\n")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
