"""Upload compliance documents to Azure Search with embeddings"""
import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI

# Compliance knowledge base documents
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

def generate_embeddings(texts):
    """Generate embeddings using OpenAI (via GitHub Models)"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    print(f"Using OpenAI embeddings via GitHub Models")
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token
    )
    
    print("Generating embeddings...")
    embeddings = []
    for i, text in enumerate(texts):
        print(f"  Processing {i+1}/{len(texts)}")
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embeddings.append(response.data[0].embedding)
    
    return embeddings

def upload_to_azure_search():
    """Upload documents to Azure Search with embeddings"""
    
    # Get credentials
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "compliance-knowledge")
    
    print(f"Connecting to: {endpoint}")
    print(f"Index: {index_name}")
    
    # Create search client
    credential = AzureKeyCredential(api_key)
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    
    # Generate embeddings for all documents
    texts = [doc["content"] for doc in COMPLIANCE_DOCS]
    embeddings = generate_embeddings(texts)
    
    # Add embeddings to documents
    for doc, embedding in zip(COMPLIANCE_DOCS, embeddings):
        doc["content_vector"] = embedding
    
    # Upload documents
    print(f"\nUploading {len(COMPLIANCE_DOCS)} documents...")
    try:
        result = search_client.upload_documents(documents=COMPLIANCE_DOCS)
        print(f"✅ Successfully uploaded {len(result)} documents")
        
        # Verify upload
        results = search_client.search(search_text="*", include_total_count=True)
        count = results.get_count()
        print(f"✅ Index now contains {count} documents")
        
        # Show sample
        print("\nSample documents in index:")
        for doc in search_client.search(search_text="*", top=3):
            print(f"  - [{doc['framework']}] {doc['title']}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise

if __name__ == "__main__":
    upload_to_azure_search()
