#!/usr/bin/env python3
"""Test script for agentic chat API"""
import requests
import json

API_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Login
print("🔐 Logging in...")
login_response = requests.post(
    f"{API_URL}/auth/login",
    json={"username": "edward", "password": "pass123"}
)
login_response.raise_for_status()
token = login_response.json()["access_token"]
print(f"✅ Login successful")

# Test chat
print("\n💬 Testing project creation...")
headers = {"Authorization": f"Bearer {token}"}
data = {"message": "Create a new project called Test Project for Q1 2025 compliance assessment"}

response = requests.post(
    f"{API_URL}/agentic-chat/",
    headers=headers,
    data=data  # Use data for form encoding
)

print(f"\n📊 Status Code: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"✅ AI Response: {result.get('response')}")
    if result.get('task_id'):
        print(f"📝 Task Created - ID: {result['task_id']}, Type: {result.get('task_type')}")
        print(f"   Status: {result.get('task_status', 'pending')}")
else:
    print(f"❌ Error: {response.text}")
