"""
IM8 Template Generator
Creates blank and sample IM8 assessment Excel templates
"""

import json
from datetime import datetime

# Template structure as JSON (to be converted to Excel manually or with a library)
BLANK_TEMPLATE = {
    "filename": "IM8_Assessment_Template.xlsx",
    "sheets": {
        "Instructions": {
            "description": "How to use this template",
            "content": [
                ["IM8 Assessment Template - Instructions"],
                [""],
                ["Purpose:", "This template is used to document IM8 framework compliance assessment"],
                [""],
                ["How to Complete:"],
                ["1. Fill in the Metadata sheet with project information"],
                ["2. For each domain sheet, complete all control rows"],
                ["3. Embed PDF evidence documents in the 'Evidence' column"],
                ["4. Add implementation notes in the 'Notes' column"],
                ["5. Upload the completed file through the QA Compliance Assistant"],
                [""],
                ["Embedding PDFs:"],
                ["- Click on the Evidence cell"],
                ["- Insert > Object > Create from File"],
                ["- Browse and select your PDF document"],
                ["- Check 'Display as icon' for better visibility"],
                [""],
                ["Required Fields:"],
                ["- All Control IDs must be filled"],
                ["- All Status fields must be: Implemented, Partial, or Not Started"],
                ["- At least one PDF evidence per control"],
                [""],
                ["Questions? Contact your auditor."]
            ]
        },
        "Metadata": {
            "description": "Project information",
            "headers": ["Field", "Value"],
            "data": [
                ["Project ID", ""],
                ["Project Name", ""],
                ["Framework", "IM8"],
                ["Assessment Period", ""],
                ["Submitted By", ""],
                ["Submission Date", ""],
                ["Version", "1.0"],
                ["Agency", ""],
                ["Contact Email", ""]
            ]
        },
        "Domain_1_Info_Security_Governance": {
            "domain_name": "Domain 1: Information Security Governance",
            "headers": ["Control ID", "Control Name", "Description", "Status", "Evidence", "Implementation Date", "Notes"],
            "controls": [
                {
                    "control_id": "IM8-01-01",
                    "control_name": "Identity and Access Management",
                    "description": "Implement robust identity and access management controls including authentication, authorization, and user lifecycle management",
                    "status": "",
                    "evidence": "[Embed PDF here]",
                    "implementation_date": "",
                    "notes": ""
                },
                {
                    "control_id": "IM8-01-02",
                    "control_name": "User Access Reviews",
                    "description": "Conduct regular user access reviews to ensure appropriate access levels and remove unnecessary permissions",
                    "status": "",
                    "evidence": "[Embed PDF here]",
                    "implementation_date": "",
                    "notes": ""
                }
            ]
        },
        "Domain_2_Network_Security": {
            "domain_name": "Domain 2: Network Security",
            "headers": ["Control ID", "Control Name", "Description", "Status", "Evidence", "Implementation Date", "Notes"],
            "controls": [
                {
                    "control_id": "IM8-02-01",
                    "control_name": "Network Segmentation",
                    "description": "Implement network segmentation between production, development, and DMZ zones with appropriate firewall rules",
                    "status": "",
                    "evidence": "[Embed PDF here]",
                    "implementation_date": "",
                    "notes": ""
                },
                {
                    "control_id": "IM8-02-02",
                    "control_name": "Firewall Management",
                    "description": "Maintain firewall rules following allow-by-exception principle with regular rule reviews",
                    "status": "",
                    "evidence": "[Embed PDF here]",
                    "implementation_date": "",
                    "notes": ""
                }
            ]
        },
        "Reference_Policies": {
            "description": "Reference documents and policies",
            "headers": ["Policy Name", "Version", "Approval Date", "Document Location", "Notes"],
            "data": [
                ["Access Control Policy", "", "", "", ""],
                ["Network Security Policy", "", "", "", ""],
                ["Data Classification Standard", "", "", "", ""],
                ["Incident Response Plan", "", "", "", ""]
            ]
        },
        "Summary": {
            "description": "Assessment summary",
            "content": [
                ["IM8 Assessment Summary"],
                [""],
                ["Total Controls", "4"],
                ["Implemented", "=COUNTIF(Domain_1_Info_Security_Governance!D3:D4,\"Implemented\")+COUNTIF(Domain_2_Network_Security!D3:D4,\"Implemented\")"],
                ["Partial", "=COUNTIF(Domain_1_Info_Security_Governance!D3:D4,\"Partial\")+COUNTIF(Domain_2_Network_Security!D3:D4,\"Partial\")"],
                ["Not Started", "=COUNTIF(Domain_1_Info_Security_Governance!D3:D4,\"Not Started\")+COUNTIF(Domain_2_Network_Security!D3:D4,\"Not Started\")"],
                ["Completion %", "=IF(B3>0,B4/B3*100,0)"],
                [""],
                ["Evidence Attached", "Check each domain sheet"],
                [""],
                ["Assessment Date", ""],
                ["Next Review Date", ""]
            ]
        }
    }
}

SAMPLE_COMPLETED_TEMPLATE = {
    "filename": "IM8_Assessment_Sample_Completed.xlsx",
    "sheets": {
        "Metadata": {
            "data": [
                ["Project ID", "1"],
                ["Project Name", "Digital Services Platform"],
                ["Framework", "IM8"],
                ["Assessment Period", "Q4 2025"],
                ["Submitted By", "analyst@example.com"],
                ["Submission Date", "2025-11-10"],
                ["Version", "1.0"],
                ["Agency", "Government Digital Services"],
                ["Contact Email", "analyst@example.com"]
            ]
        },
        "Domain_1_Info_Security_Governance": {
            "controls": [
                {
                    "control_id": "IM8-01-01",
                    "control_name": "Identity and Access Management",
                    "description": "Implement robust identity and access management controls including authentication, authorization, and user lifecycle management",
                    "status": "Implemented",
                    "evidence": "[PDF: access_control_policy.pdf embedded]",
                    "implementation_date": "2024-10-15",
                    "notes": "MFA enabled for all admin accounts. Azure AD integrated. Quarterly access reviews completed."
                },
                {
                    "control_id": "IM8-01-02",
                    "control_name": "User Access Reviews",
                    "description": "Conduct regular user access reviews to ensure appropriate access levels and remove unnecessary permissions",
                    "status": "Implemented",
                    "evidence": "[PDF: user_access_review_q4_2024.pdf embedded]",
                    "implementation_date": "2024-09-01",
                    "notes": "Quarterly reviews established. Last review: Q4 2024. 3 accounts disabled per review findings."
                }
            ]
        },
        "Domain_2_Network_Security": {
            "controls": [
                {
                    "control_id": "IM8-02-01",
                    "control_name": "Network Segmentation",
                    "description": "Implement network segmentation between production, development, and DMZ zones with appropriate firewall rules",
                    "status": "Partial",
                    "evidence": "[PDF: network_diagram.pdf embedded]",
                    "implementation_date": "2024-08-20",
                    "notes": "DMZ and production segmented. Internal network segmentation in progress (target: Q1 2026)."
                },
                {
                    "control_id": "IM8-02-02",
                    "control_name": "Firewall Management",
                    "description": "Maintain firewall rules following allow-by-exception principle with regular rule reviews",
                    "status": "Implemented",
                    "evidence": "[PDF: firewall_rules_review.pdf embedded]",
                    "implementation_date": "2024-07-10",
                    "notes": "Annual rule review completed. 342 rules reviewed, 15 obsolete rules removed. Next review: July 2025."
                }
            ]
        },
        "Reference_Policies": {
            "data": [
                ["Access Control Policy", "v2.1", "2024-11-01", "/policies/access_control_policy_v2.1.pdf", "Approved by CISO"],
                ["Network Security Policy", "v1.5", "2024-06-15", "/policies/network_security_policy.pdf", "Updated after pentest"],
                ["Data Classification Standard", "v1.0", "2024-03-01", "/policies/data_classification.pdf", "Aligned with IM8"],
                ["Incident Response Plan", "v2.0", "2024-09-10", "/policies/incident_response_plan.pdf", "Tested via tabletop"]
            ]
        }
    }
}

def save_templates():
    """Save template structures as JSON files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save blank template structure
    with open(f"storage/im8_template_blank_structure.json", "w") as f:
        json.dump(BLANK_TEMPLATE, f, indent=2)
    
    # Save sample template structure
    with open(f"storage/im8_template_sample_structure.json", "w") as f:
        json.dump(SAMPLE_COMPLETED_TEMPLATE, f, indent=2)
    
    print("✅ Template structures saved to storage/")
    print("   - im8_template_blank_structure.json")
    print("   - im8_template_sample_structure.json")
    print("\n📝 Next: Use these structures to create actual Excel files")
    print("   (Manual creation or use openpyxl to generate)")

if __name__ == "__main__":
    save_templates()
