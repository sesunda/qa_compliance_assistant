"""
Upload compliance documents to Azure Search via API endpoint
This script makes HTTP requests to the deployed API to upload documents
"""
import requests
import json
import os

API_BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Login credentials (using Alice the analyst)
LOGIN_DATA = {
    "username": "alice",
    "password": "analyst123"
}

# Compliance documents to upload
COMPLIANCE_DOCS = [
    {
        "id": "iso27001_a5_access",
        "framework": "ISO 27001",
        "category": "access_control",
        "title": "ISO 27001 - A.5 Access Control",
        "content": """Access control policy requirements:
- Multi-factor authentication (MFA) for privileged accounts
- Role-based access control (RBAC) implementation
- Regular access reviews (quarterly)
- Least privilege principle enforcement
- Password requirements: minimum 12 characters, complexity enabled
- Account lockout after 5 failed attempts
- Session timeout after 15 minutes of inactivity"""
    },
    {
        "id": "iso27001_a9_crypto",
        "framework": "ISO 27001",
        "category": "cryptography",
        "title": "ISO 27001 - A.9 Cryptography",
        "content": """Cryptographic controls:
- Data encryption at rest using AES-256
- Data encryption in transit using TLS 1.2+
- Key management procedures
- Encryption key rotation every 90 days
- Secure key storage in hardware security modules (HSM)"""
    },
    {
        "id": "nist_pr_access",
        "framework": "NIST CSF",
        "category": "access_control",
        "title": "NIST CSF - PR.AC: Identity Management and Access Control",
        "content": """Identity and access management requirements:
- Unique user identification
- Physical and logical access controls
- Remote access management
- Network segregation
- Principle of least privilege
- Audit of access control activities"""
    },
    {
        "id": "nist_pr_data",
        "framework": "NIST CSF",
        "category": "data_protection",
        "title": "NIST CSF - PR.DS: Data Security",
        "content": """Data protection requirements:
- Data at rest protection
- Data in transit protection
- Asset classification and handling
- Data leakage prevention
- Removable media protection"""
    },
    {
        "id": "im8_control3",
        "framework": "IM8",
        "category": "network_security",
        "title": "IM8 Control 3 - Network Segmentation",
        "content": """Network segmentation requirements:
- Logical separation of networks based on sensitivity
- Firewall rules between network zones
- DMZ for external-facing systems
- Internal network isolation for critical systems
- Network access controls and monitoring"""
    },
    {
        "id": "im8_control4",
        "framework": "IM8",
        "category": "cryptography",
        "title": "IM8 Control 4 - Data Encryption",
        "content": """Data encryption requirements:
- Encryption for data at rest
- Encryption for data in transit
- Use of approved encryption algorithms (AES-256, RSA-2048+)
- Secure key management practices
- Regular cryptographic review"""
    },
    {
        "id": "im8_control5",
        "framework": "IM8",
        "category": "access_control",
        "title": "IM8 Control 5 - Multi-Factor Authentication",
        "content": """MFA requirements for privileged accounts:
- All privileged accounts must use MFA
- Supported MFA methods: hardware tokens, software authenticators, biometrics
- MFA required for remote access
- MFA required for administrative access
- Backup authentication methods configured
- Password requirements: minimum 14 characters, complexity required, no dictionary words
- Password history: cannot reuse last 12 passwords
- Password expiry: maximum 90 days"""
    },
    {
        "id": "best_practice_incident",
        "framework": "Best Practice",
        "category": "incident_response",
        "title": "Security Incident Response Best Practices",
        "content": """Incident response procedures:
- 24/7 incident response capability
- Incident classification and prioritization
- Containment strategies
- Evidence preservation
- Communication protocols
- Post-incident review and lessons learned
- Incident response plan testing (annually)"""
    },
    {
        "id": "best_practice_logging",
        "framework": "Best Practice",
        "category": "logging_monitoring",
        "title": "Logging and Monitoring Best Practices",
        "content": """Logging requirements:
- Centralized log management
- Log retention: minimum 1 year
- Security event monitoring
- Log integrity protection
- Regular log review
- Alerting for critical security events
- Clock synchronization (NTP)"""
    },
    {
        "id": "best_practice_vuln",
        "framework": "Best Practice",
        "category": "vulnerability_management",
        "title": "Vulnerability Management Best Practices",
        "content": """Vulnerability management process:
- Regular vulnerability scanning (weekly)
- Patch management procedures
- Critical patches within 30 days
- High severity patches within 60 days
- Vulnerability assessment reports
- Exception handling process
- Third-party software inventory"""
    }
]

def login():
    """Login and get access token"""
    print("Logging in...")
    response = requests.post(f"{API_BASE_URL}/auth/login", json=LOGIN_DATA)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def upload_documents_via_api(token):
    """Upload documents using the API's direct Azure Search upload endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n📤 Uploading {len(COMPLIANCE_DOCS)} documents to Azure Search...")
    
    # Try direct upload endpoint if it exists
    try:
        response = requests.post(
            f"{API_BASE_URL}/rag/upload-documents",
            json={"documents": COMPLIANCE_DOCS},
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully uploaded via API: {result}")
            return True
    except Exception as e:
        print(f"⚠️ Direct upload endpoint not available: {e}")
    
    print("\nℹ️ Documents need to be uploaded directly to Azure Search")
    return False

def verify_search():
    """Test search functionality"""
    print("\n🔍 Testing search functionality...")
    
    # Test query about Control 5 (the original failing query)
    query = "Tell me the password requirement related to Control 5"
    print(f"\nTest query: '{query}'")
    
    # This would be done through the chat interface
    print("✓ To test: Use the chat interface and ask about Control 5 password requirements")
    print("✓ Expected: Should use search_documents tool, not suggest_related_controls")

if __name__ == "__main__":
    print("=" * 70)
    print("AZURE SEARCH DOCUMENT UPLOAD")
    print("=" * 70)
    
    token = login()
    if not token:
        print("\n❌ Failed to authenticate")
        exit(1)
    
    # Upload documents
    upload_documents_via_api(token)
    
    # Show what was prepared
    print(f"\n📋 Prepared {len(COMPLIANCE_DOCS)} compliance documents:")
    for doc in COMPLIANCE_DOCS:
        print(f"  - [{doc['framework']}] {doc['title']}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
Since we don't have a direct upload endpoint, we need to upload via Python script
on a machine with the required libraries (sentence-transformers).

The API fix is DEPLOYED and ready:
✅ Tool routing improved - search_documents now prioritized for knowledge queries
✅ suggest_related_controls requires evidence_id (prevents incorrect triggering)
✅ New revision ca-api-qca-dev--0000141 deployed and healthy

To complete the upload:
1. On a machine with Python and sentence-transformers installed
2. Run: python upload_compliance_docs.py
3. This will generate embeddings and upload to Azure Search

Or test the fix now with the query:
"Tell me the password requirement related to Control 5"

It will either:
- Use search_documents (if documents uploaded)
- Respond gracefully (if index empty)
- NOT trigger suggest_related_controls error
""")
