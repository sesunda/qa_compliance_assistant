"""
Upload compliance documents by executing Python code directly in the running container
This uses az containerapp exec to run the upload script inside the container where all dependencies exist
"""
import subprocess
import json

COMPLIANCE_DOCS = [
    {
        "id": "iso27001_a5_access",
        "framework": "ISO 27001",
        "category": "access_control",
        "title": "ISO 27001 - A.5 Access Control",
        "content": "Access control policy requirements: Multi-factor authentication (MFA) for privileged accounts, Role-based access control (RBAC) implementation, Regular access reviews (quarterly), Least privilege principle enforcement, Password requirements: minimum 12 characters, complexity enabled, Account lockout after 5 failed attempts, Session timeout after 15 minutes of inactivity"
    },
    {
        "id": "iso27001_a9_crypto",
        "framework": "ISO 27001",
        "category": "cryptography",
        "title": "ISO 27001 - A.9 Cryptography",
        "content": "Cryptographic controls: Data encryption at rest using AES-256, Data encryption in transit using TLS 1.2+, Key management procedures, Encryption key rotation every 90 days, Secure key storage in hardware security modules (HSM)"
    },
    {
        "id": "nist_pr_access",
        "framework": "NIST CSF",
        "category": "access_control",
        "title": "NIST CSF - PR.AC: Identity Management and Access Control",
        "content": "Identity and access management requirements: Unique user identification, Physical and logical access controls, Remote access management, Network segregation, Principle of least privilege, Audit of access control activities"
    },
    {
        "id": "nist_pr_data",
        "framework": "NIST CSF",
        "category": "data_protection",
        "title": "NIST CSF - PR.DS: Data Security",
        "content": "Data protection requirements: Data at rest protection, Data in transit protection, Asset classification and handling, Data leakage prevention, Removable media protection"
    },
    {
        "id": "im8_control3",
        "framework": "IM8",
        "category": "network_security",
        "title": "IM8 Control 3 - Network Segmentation",
        "content": "Network segmentation requirements: Logical separation of networks based on sensitivity, Firewall rules between network zones, DMZ for external-facing systems, Internal network isolation for critical systems, Network access controls and monitoring"
    },
    {
        "id": "im8_control4",
        "framework": "IM8",
        "category": "cryptography",
        "title": "IM8 Control 4 - Data Encryption",
        "content": "Data encryption requirements: Encryption for data at rest, Encryption for data in transit, Use of approved encryption algorithms (AES-256, RSA-2048+), Secure key management practices, Regular cryptographic review"
    },
    {
        "id": "im8_control5",
        "framework": "IM8",
        "category": "access_control",
        "title": "IM8 Control 5 - Multi-Factor Authentication",
        "content": "MFA requirements for privileged accounts: All privileged accounts must use MFA, Supported MFA methods: hardware tokens, software authenticators, biometrics, MFA required for remote access, MFA required for administrative access, Backup authentication methods configured, Password requirements: minimum 14 characters, complexity required, no dictionary words, Password history: cannot reuse last 12 passwords, Password expiry: maximum 90 days"
    },
    {
        "id": "best_practice_incident",
        "framework": "Best Practice",
        "category": "incident_response",
        "title": "Security Incident Response Best Practices",
        "content": "Incident response procedures: 24/7 incident response capability, Incident classification and prioritization, Containment strategies, Evidence preservation, Communication protocols, Post-incident review and lessons learned, Incident response plan testing (annually)"
    },
    {
        "id": "best_practice_logging",
        "framework": "Best Practice",
        "category": "logging_monitoring",
        "title": "Logging and Monitoring Best Practices",
        "content": "Logging requirements: Centralized log management, Log retention: minimum 1 year, Security event monitoring, Log integrity protection, Regular log review, Alerting for critical security events, Clock synchronization (NTP)"
    },
    {
        "id": "best_practice_vuln",
        "framework": "Best Practice",
        "category": "vulnerability_management",
        "title": "Vulnerability Management Best Practices",
        "content": "Vulnerability management process: Regular vulnerability scanning (weekly), Patch management procedures, Critical patches within 30 days, High severity patches within 60 days, Vulnerability assessment reports, Exception handling process, Third-party software inventory"
    }
]

# Create inline Python script to run in container
upload_script = f"""
import asyncio
import os
import sys
sys.path.insert(0, '/app')

from api.src.rag.azure_search import azure_search_store

docs = {json.dumps(COMPLIANCE_DOCS)}

async def upload():
    print("Creating/verifying index...")
    await azure_search_store.create_index()
    print("Uploading documents...")
    result = await azure_search_store.upload_documents(docs)
    print(f"Upload result: {{result}}")
    count = await azure_search_store.get_document_count()
    print(f"Total documents in index: {{count}}")

asyncio.run(upload())
"""

print("=" * 70)
print("UPLOAD COMPLIANCE DOCUMENTS TO AZURE SEARCH")
print("=" * 70)
print(f"\nPreparing to upload {len(COMPLIANCE_DOCS)} documents...")
print("\nDocuments:")
for doc in COMPLIANCE_DOCS:
    print(f"  - [{doc['framework']}] {doc['title']}")

print("\n" + "=" * 70)
print("Executing upload in container...")
print("=" * 70)

# Save script to temp file
with open("temp_upload.py", "w") as f:
    f.write(upload_script)

print("\nScript created: temp_upload.py")
print("Run this command to upload:")
print("\naz containerapp exec --name ca-api-qca-dev --resource-group rg-qca-dev --command 'python /app/temp_upload.py'")
