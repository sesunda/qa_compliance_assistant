"""Singapore Government IM8 Compliance Framework Knowledge Base"""

# Singapore IM8 Control Framework
# Information Management Manual 8 - Security Controls

IM8_CONTROLS = {
    "IM8.AC.01": {
        "title": "Access Control Policy and Procedures",
        "description": "Establish, document, and disseminate access control policies and procedures that address purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance.",
        "category": "Access Control",
        "control_family": "AC",
        "singapore_context": "Whole-of-Government access control standards",
        "implementation_guidance": "Must align with Singapore Government security policies and Smart Nation initiatives",
        "related_regulations": ["Cybersecurity Act 2018", "Government Instruction Manual"],
        "dependencies": ["IM8.PS.01", "IM8.RA.01"],
        "risk_rating": "High"
    },
    "IM8.AC.02": {
        "title": "Account Management",
        "description": "Manage information system accounts including establishing, activating, modifying, disabling, and removing accounts.",
        "category": "Access Control", 
        "control_family": "AC",
        "singapore_context": "Government identity and access management",
        "implementation_guidance": "Must integrate with WOG identity management systems",
        "related_regulations": ["PDPA 2012", "Cybersecurity Act 2018"],
        "dependencies": ["IM8.AC.01", "IM8.IA.01"],
        "risk_rating": "High"
    },
    "IM8.AC.03": {
        "title": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access to information and system resources.",
        "category": "Access Control",
        "control_family": "AC", 
        "singapore_context": "Government system access enforcement",
        "implementation_guidance": "Must support role-based access for government functions",
        "related_regulations": ["Cybersecurity Act 2018"],
        "dependencies": ["IM8.AC.01", "IM8.AC.02"],
        "risk_rating": "High"
    },
    "IM8.DG.01": {
        "title": "Data Classification",
        "description": "Classify government data according to sensitivity levels and handling requirements.",
        "category": "Data Governance",
        "control_family": "DG",
        "singapore_context": "Singapore Government data classification scheme",
        "implementation_guidance": "Must follow Singapore Government data classification guidelines",
        "related_regulations": ["PDPA 2012", "Official Secrets Act"],
        "dependencies": ["IM8.PS.01"],
        "risk_rating": "High"
    },
    "IM8.DG.02": {
        "title": "Data Protection",
        "description": "Protect government data at rest, in transit, and during processing.",
        "category": "Data Governance",
        "control_family": "DG",
        "singapore_context": "Whole-of-Government data protection standards",
        "implementation_guidance": "Must use approved encryption for sensitive government data",
        "related_regulations": ["PDPA 2012", "Cybersecurity Act 2018"],
        "dependencies": ["IM8.DG.01", "IM8.SC.01"],
        "risk_rating": "Critical"
    },
    "IM8.RM.01": {
        "title": "Risk Assessment",
        "description": "Conduct comprehensive risk assessments of government information systems.",
        "category": "Risk Management",
        "control_family": "RM",
        "singapore_context": "Government enterprise risk management",
        "implementation_guidance": "Must align with national cybersecurity risk framework",
        "related_regulations": ["Cybersecurity Act 2018"],
        "dependencies": ["IM8.PS.01"],
        "risk_rating": "High"
    },
    "IM8.RM.02": {
        "title": "Risk Response",
        "description": "Implement appropriate risk response strategies for identified risks.",
        "category": "Risk Management", 
        "control_family": "RM",
        "singapore_context": "National cybersecurity risk mitigation",
        "implementation_guidance": "Must coordinate with national cyber incident response capabilities",
        "related_regulations": ["Cybersecurity Act 2018"],
        "dependencies": ["IM8.RM.01", "IM8.IR.01"],
        "risk_rating": "High"
    },
    "IM8.IM.01": {
        "title": "Incident Response Capability",
        "description": "Establish incident response capability for government information systems.",
        "category": "Incident Management",
        "control_family": "IM",
        "singapore_context": "National cyber incident response coordination",
        "implementation_guidance": "Must integrate with SingCERT and national incident response",
        "related_regulations": ["Cybersecurity Act 2018"],
        "dependencies": ["IM8.PS.01", "IM8.RM.01"],
        "risk_rating": "Critical"
    }
}

# Singapore-specific compliance contexts
SINGAPORE_COMPLIANCE_CONTEXT = {
    "regulations": {
        "Cybersecurity Act 2018": {
            "scope": "Critical Information Infrastructure protection",
            "authority": "Cyber Security Agency of Singapore (CSA)",
            "key_requirements": ["CII designation", "Cybersecurity codes of practice", "Incident reporting"]
        },
        "PDPA 2012": {
            "scope": "Personal data protection",
            "authority": "Personal Data Protection Commission (PDPC)", 
            "key_requirements": ["Consent management", "Data breach notification", "Data protection officer"]
        },
        "Government Instruction Manual": {
            "scope": "Whole-of-Government IT governance",
            "authority": "Government Technology Agency (GovTech)",
            "key_requirements": ["Security standards", "Architecture principles", "Procurement guidelines"]
        }
    },
    "government_context": {
        "Smart Nation": ["Digital identity", "Data sharing", "Interoperability", "Citizen services"],
        "Whole-of-Government": ["Shared services", "Common infrastructure", "Standardization"],
        "Digital Government": ["Cloud-first", "API-first", "Mobile-first", "Data-driven"]
    },
    "sector_specific": {
        "Critical Information Infrastructure": ["Essential services", "Cybersecurity codes", "Threat intelligence"],
        "Government Agencies": ["Data governance", "Information sharing", "Service delivery"],
        "Smart Systems": ["IoT security", "AI governance", "Data analytics"]
    }
}

# IM8 Control mappings to international frameworks
IM8_FRAMEWORK_MAPPINGS = {
    "IM8.AC.01": {
        "ISO27001": ["A.9.1.1", "A.9.1.2"],
        "NIST_CSF": ["PR.AC-1", "PR.AC-2"],
        "NIST_800_53": ["AC-1"],
        "CIS_Controls": ["5.1", "5.2"]
    },
    "IM8.AC.02": {
        "ISO27001": ["A.9.2.1", "A.9.2.2", "A.9.2.3"],
        "NIST_CSF": ["PR.AC-1", "PR.AC-3"],
        "NIST_800_53": ["AC-2"],
        "CIS_Controls": ["5.3", "5.4"]
    },
    "IM8.DG.01": {
        "ISO27001": ["A.8.2.1", "A.8.2.2"],
        "NIST_CSF": ["PR.DS-5"],
        "NIST_800_53": ["SC-8"],
        "CIS_Controls": ["3.1", "3.2"]
    }
}