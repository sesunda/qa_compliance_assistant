"""
Test script to verify role-based permissions for all user roles
Tests both backend API and simulates frontend behavior
"""
import requests
import json
from typing import Dict, Optional

# Azure API URL
API_BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Test users (from seed data)
TEST_USERS = {
    "admin": {"username": "hsa_admin", "password": "admin123"},
    "analyst": {"username": "hsa_analyst", "password": "analyst123"},
    "qa_reviewer": {"username": "hsa_qa", "password": "qa123"},
    "auditor": {"username": "auditor1", "password": "auditor123"},
}

# Endpoints to test
ENDPOINTS = {
    "list_users": {"method": "GET", "url": "/auth/users", "allowed": ["admin", "analyst", "auditor"]},
    "get_user": {"method": "GET", "url": "/auth/users/1", "allowed": ["admin", "analyst", "auditor"]},
    "list_agencies": {"method": "GET", "url": "/auth/agencies", "allowed": ["admin", "analyst", "auditor"]},
    "list_roles": {"method": "GET", "url": "/auth/roles", "allowed": ["admin"]},
    "get_me": {"method": "GET", "url": "/auth/me", "allowed": ["admin", "analyst", "qa_reviewer", "auditor"]},
    "list_projects": {"method": "GET", "url": "/projects", "allowed": ["admin", "analyst", "auditor"]},
    "list_controls": {"method": "GET", "url": "/controls", "allowed": ["admin", "analyst", "auditor"]},
    "list_evidence": {"method": "GET", "url": "/evidence", "allowed": ["admin", "analyst", "auditor"]},
}


class PermissionTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tokens: Dict[str, Optional[str]] = {}
        self.test_results = []

    def login(self, role: str, credentials: dict) -> Optional[str]:
        """Login and get access token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=credentials,
                timeout=10
            )
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                print(f"✓ Login successful: {role} ({credentials['username']})")
                return token
            else:
                print(f"✗ Login failed: {role} - {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Login error: {role} - {str(e)}")
            return None

    def test_endpoint(self, role: str, token: str, endpoint_name: str, endpoint_config: dict) -> dict:
        """Test a single endpoint with given role"""
        method = endpoint_config["method"]
        url = f"{self.base_url}{endpoint_config['url']}"
        allowed_roles = endpoint_config["allowed"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json={}, timeout=10)
            else:
                return {"status": "skipped", "reason": "unsupported method"}
            
            expected_success = role in allowed_roles
            actual_success = response.status_code in [200, 201]
            
            result = {
                "endpoint": endpoint_name,
                "role": role,
                "expected": "success" if expected_success else "forbidden",
                "actual_status": response.status_code,
                "actual": "success" if actual_success else "forbidden",
                "pass": (expected_success == actual_success),
                "response_preview": response.text[:200] if not actual_success else f"✓ {len(response.json()) if isinstance(response.json(), list) else 'OK'}"
            }
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint_name,
                "role": role,
                "expected": "success" if role in allowed_roles else "forbidden",
                "actual": "error",
                "pass": False,
                "error": str(e)
            }

    def run_tests(self):
        """Run all permission tests"""
        print("=" * 80)
        print("ROLE-BASED PERMISSION TESTING")
        print("=" * 80)
        print(f"\nAPI Base URL: {self.base_url}")
        print(f"Test Users: {', '.join(TEST_USERS.keys())}")
        print(f"Endpoints to Test: {len(ENDPOINTS)}")
        print("\n" + "=" * 80)
        
        # Step 1: Login all users
        print("\n[STEP 1] Logging in all test users...")
        print("-" * 80)
        for role, credentials in TEST_USERS.items():
            token = self.login(role, credentials)
            self.tokens[role] = token
        
        # Step 2: Test endpoints for each role
        print("\n[STEP 2] Testing endpoint permissions...")
        print("-" * 80)
        
        for role, token in self.tokens.items():
            if not token:
                print(f"\n⚠ Skipping tests for {role} (login failed)")
                continue
            
            print(f"\n--- Testing as {role.upper()} ---")
            
            for endpoint_name, endpoint_config in ENDPOINTS.items():
                result = self.test_endpoint(role, token, endpoint_name, endpoint_config)
                self.test_results.append(result)
                
                status_icon = "✓" if result["pass"] else "✗"
                expected_str = result["expected"]
                actual_str = f"{result['actual_status']} ({result['actual']})"
                
                print(f"  {status_icon} {endpoint_name:20} | Expected: {expected_str:10} | Got: {actual_str:20}")
                
                if not result["pass"]:
                    print(f"      ⚠ FAILED: {result.get('response_preview', result.get('error', 'Unknown'))}")
        
        # Step 3: Summary
        print("\n" + "=" * 80)
        print("[SUMMARY]")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["pass"])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✓ Passed: {passed_tests}")
        print(f"✗ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n⚠ FAILED TESTS:")
            for result in self.test_results:
                if not result["pass"]:
                    print(f"  - {result['role']:15} | {result['endpoint']:20} | "
                          f"Expected: {result['expected']:10} | Got: {result['actual_status']}")
        
        print("\n" + "=" * 80)
        
        return passed_tests == total_tests


if __name__ == "__main__":
    tester = PermissionTester(API_BASE_URL)
    success = tester.run_tests()
    
    exit(0 if success else 1)
