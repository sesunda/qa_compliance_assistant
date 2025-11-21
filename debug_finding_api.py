"""Direct test of findings API to debug field issue"""
import requests
import json

BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Login
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "alice", "password": "pass123"}
)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get finding 12 detail
print("Getting finding 12 detail...")
finding_response = requests.get(
    f"{BASE_URL}/findings/12",
    headers=headers
)

print(f"Status: {finding_response.status_code}")
finding = finding_response.json()
print("\nFull response:")
print(json.dumps(finding, indent=2, default=str))

print("\n" + "="*80)
print("KEY FIELDS CHECK:")
print("="*80)
print(f"discovery_date: {finding.get('discovery_date', 'MISSING')}")
print(f"business_impact: {finding.get('business_impact', 'MISSING')}")
