from pydantic import BaseModel
from typing import Optional


class SampleEvidence(BaseModel):
    id: int
    title: str
    description: str
    file_name: str
    evidence_type: str
    sample_data: Optional[str] = None


# Sample evidence data
SAMPLE_EVIDENCE = [
    {
        "id": 1,
        "title": "Security Audit Report",
        "description": "Annual security audit findings and recommendations",
        "file_name": "security_audit_2024.pdf",
        "evidence_type": "audit_report",
        "sample_data": "Security audit completed with 95% compliance score"
    },
    {
        "id": 2,
        "title": "Access Control List",
        "description": "Current system access control configurations",
        "file_name": "acl_config.json",
        "evidence_type": "configuration",
        "sample_data": '{"users": ["admin", "auditor"], "permissions": ["read", "write"]}'
    },
    {
        "id": 3,
        "title": "Backup Verification Log",
        "description": "Daily backup verification results",
        "file_name": "backup_log_2024.csv",
        "evidence_type": "log",
        "sample_data": "2024-01-01,SUCCESS,100%\n2024-01-02,SUCCESS,100%"
    },
    {
        "id": 4,
        "title": "Compliance Training Certificate",
        "description": "Employee compliance training completion certificate",
        "file_name": "training_cert.pdf",
        "evidence_type": "certificate",
        "sample_data": "Certificate of completion for security awareness training"
    },
    {
        "id": 5,
        "title": "Incident Response Plan",
        "description": "Documented incident response procedures",
        "file_name": "incident_response_plan.pdf",
        "evidence_type": "policy",
        "sample_data": "Step-by-step procedures for handling security incidents"
    }
]
