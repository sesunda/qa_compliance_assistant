"""
Evidence Upload Templates API
Provides downloadable templates for evidence uploads
"""

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import io
import csv
import json
from datetime import datetime

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/evidence-upload.csv")
async def download_evidence_csv_template():
    """Download CSV template for evidence upload"""
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'control_id',
        'title',
        'description',
        'evidence_type',
        'file_path',
        'notes'
    ])
    
    # Example rows
    writer.writerow([
        '5',
        'Access Control Policy Document',
        'Organization-wide access control policy covering authentication and authorization',
        'policy_document',
        'path/to/policy.pdf',
        'Latest version approved by CISO'
    ])
    
    writer.writerow([
        '5',
        'User Access Review Report',
        'Quarterly user access review for Q1 2025',
        'audit_report',
        'path/to/access_review_q1.xlsx',
        'All exceptions documented and approved'
    ])
    
    # Get the CSV content
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=evidence_upload_template_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/evidence-upload.json")
async def download_evidence_json_template():
    """Download JSON template for evidence upload"""
    
    template = {
        "evidence_items": [
            {
                "control_id": 5,
                "title": "Access Control Policy Document",
                "description": "Organization-wide access control policy covering authentication and authorization",
                "evidence_type": "policy_document",
                "file_path": "path/to/policy.pdf",
                "notes": "Latest version approved by CISO"
            },
            {
                "control_id": 5,
                "title": "User Access Review Report",
                "description": "Quarterly user access review for Q1 2025",
                "evidence_type": "audit_report",
                "file_path": "path/to/access_review_q1.xlsx",
                "notes": "All exceptions documented and approved"
            }
        ],
        "metadata": {
            "template_version": "1.0",
            "evidence_types": [
                "policy_document",
                "procedure",
                "audit_report",
                "configuration_screenshot",
                "log_file",
                "certificate",
                "training_record",
                "other"
            ],
            "instructions": {
                "control_id": "Required. The ID of the control this evidence supports",
                "title": "Required. Short descriptive title of the evidence",
                "description": "Optional. Detailed description of what this evidence demonstrates",
                "evidence_type": "Required. Type of evidence from the list above",
                "file_path": "Optional. Path to the actual evidence file if uploading separately",
                "notes": "Optional. Additional notes or context for reviewers"
            }
        }
    }
    
    return Response(
        content=json.dumps(template, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=evidence_upload_template_{datetime.now().strftime('%Y%m%d')}.json"
        }
    )


@router.get("/evidence-types")
async def get_evidence_types():
    """Get list of valid evidence types"""
    return {
        "evidence_types": [
            {
                "value": "policy_document",
                "label": "Policy Document",
                "description": "Organizational policies, standards, and guidelines"
            },
            {
                "value": "procedure",
                "label": "Procedure/Process Document",
                "description": "Step-by-step procedures and workflows"
            },
            {
                "value": "audit_report",
                "label": "Audit Report",
                "description": "Internal or external audit findings and reports"
            },
            {
                "value": "configuration_screenshot",
                "label": "Configuration Screenshot",
                "description": "Screenshots showing system configurations"
            },
            {
                "value": "log_file",
                "label": "Log File/Export",
                "description": "System logs, access logs, audit trails"
            },
            {
                "value": "certificate",
                "label": "Certificate/Attestation",
                "description": "Certificates, licenses, attestations"
            },
            {
                "value": "training_record",
                "label": "Training Record",
                "description": "Training completion certificates and records"
            },
            {
                "value": "test_result",
                "label": "Test Result",
                "description": "Vulnerability scan results, penetration test reports"
            },
            {
                "value": "other",
                "label": "Other",
                "description": "Other types of evidence"
            }
        ]
    }


@router.get("/im8-controls-sample.csv")
async def download_im8_sample():
    """Download sample IM8 controls evidence CSV with realistic data"""
    
    # Read the sample file from storage
    sample_path = "storage/sample_im8_controls_evidence.csv"
    
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=sample_im8_controls_evidence_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except FileNotFoundError:
        # Fallback: generate minimal sample inline
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['control_id', 'title', 'description', 'evidence_type', 'file_path', 'notes'])
        writer.writerow([
            '5',
            'Access Control Policy v2.1',
            'Organization-wide access control policy covering authentication and RBAC',
            'policy_document',
            '/storage/uploads/access_control_policy.pdf',
            'Approved by CISO. Covers IM8-01 requirements.'
        ])
        
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=sample_im8_controls_evidence_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )


@router.get("/template-validation-rules")
async def get_template_validation_rules():
    """Get validation rules for evidence upload templates"""
    return {
        "csv_template_rules": {
            "required_columns": [
                "control_id",
                "title",
                "description",
                "evidence_type"
            ],
            "optional_columns": [
                "file_path",
                "notes"
            ],
            "field_validations": {
                "control_id": {
                    "type": "integer",
                    "required": True,
                    "description": "Must be a valid control ID that exists in the project"
                },
                "title": {
                    "type": "string",
                    "required": True,
                    "max_length": 255,
                    "description": "Short descriptive title of the evidence"
                },
                "description": {
                    "type": "string",
                    "required": False,
                    "max_length": 5000,
                    "description": "Detailed description of what this evidence demonstrates"
                },
                "evidence_type": {
                    "type": "enum",
                    "required": True,
                    "allowed_values": [
                        "policy_document",
                        "procedure",
                        "audit_report",
                        "configuration_screenshot",
                        "log_file",
                        "certificate",
                        "training_record",
                        "test_result",
                        "other"
                    ],
                    "description": "Type of evidence from the predefined list"
                },
                "file_path": {
                    "type": "string",
                    "required": False,
                    "max_length": 500,
                    "description": "Path to evidence file (if uploading separately)"
                },
                "notes": {
                    "type": "string",
                    "required": False,
                    "max_length": 2000,
                    "description": "Additional notes or context for reviewers"
                }
            },
            "general_rules": [
                "CSV must be UTF-8 encoded",
                "First row must contain column headers",
                "Each row represents one evidence item",
                "Multiple evidence items can reference the same control_id",
                "Empty rows are ignored",
                "Commas within fields should be quoted"
            ]
        },
        "im8_specific_info": {
            "domain_areas": [
                {"code": "IM8-01", "name": "Access & Identity Management"},
                {"code": "IM8-02", "name": "Network & Connectivity Security"},
                {"code": "IM8-03", "name": "Application & Data Protection"},
                {"code": "IM8-04", "name": "Infrastructure & System Hardening"},
                {"code": "IM8-05", "name": "Secure Development & Supply Chain"},
                {"code": "IM8-06", "name": "Logging, Monitoring & Incident Response"},
                {"code": "IM8-07", "name": "Third-Party & Vendor Management"},
                {"code": "IM8-08", "name": "Change, Release & Configuration Management"},
                {"code": "IM8-09", "name": "Governance, Risk & Compliance (GRC)"},
                {"code": "IM8-10", "name": "Digital Service & Delivery Standards"}
            ],
            "recommended_evidence_per_control": "3-5 evidence items per control for comprehensive coverage",
            "evidence_quality_guidelines": [
                "Evidence should be recent (within last 12 months unless policy documents)",
                "Include version numbers and dates where applicable",
                "Reference the IM8 domain area being addressed",
                "Provide context in notes field for reviewers",
                "Ensure file paths are accessible to the system"
            ]
        }
    }
