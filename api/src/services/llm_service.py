"""
LLM Service for Agentic AI
Provides natural language understanding and generation capabilities
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Azure OpenAI / OpenAI for agentic capabilities"""
    
    def __init__(self):
        # Try Azure OpenAI first, fall back to OpenAI
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
        
        if self.azure_endpoint and self.azure_api_key:
            self.client = AzureOpenAI(
                api_key=self.azure_api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=self.azure_endpoint
            )
            self.provider = "azure"
            logger.info("Initialized Azure OpenAI client")
        elif self.openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.openai_api_key)
            self.provider = "openai"
            logger.info("Initialized OpenAI client")
        else:
            self.client = None
            self.provider = None
            logger.warning("No LLM provider configured. Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY or OPENAI_API_KEY")
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None
    
    def parse_user_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Parse user's natural language prompt to extract intent and parameters
        
        Returns:
        {
            "action": "create_controls" | "create_findings" | "analyze_evidence" | "generate_report",
            "entity": "control" | "finding" | "evidence" | "assessment" | "report",
            "count": int,
            "parameters": {...}
        }
        """
        if not self.is_available():
            raise ValueError("LLM service not available. Configure AZURE_OPENAI or OPENAI credentials.")
        
        system_prompt = """You are an AI assistant for a compliance management system.
Parse the user's request and extract:
1. The action they want to perform (create, upload, analyze, generate, etc.)
2. The entity type (controls, findings, evidence, assessment, report)
3. Relevant parameters (count, framework, domain, etc.)

Return a JSON object with:
{
    "action": "action_name",
    "entity": "entity_type",
    "count": number_if_applicable,
    "parameters": {
        "framework": "IM8" if mentioned,
        "domain_areas": list of domains,
        "assessment_id": id if mentioned,
        "severity": if mentioned,
        etc.
    }
}

Valid actions:
- create_controls: Generate new security controls
- create_findings: Create security findings
- create_assessment: Create new assessment
- analyze_evidence: Analyze uploaded evidence
- generate_report: Generate compliance report
- bulk_upload: Bulk upload from template

Examples:
User: "Upload 30 IM8 controls covering all 10 domains"
Response: {"action": "create_controls", "entity": "control", "count": 30, "parameters": {"framework": "IM8", "domains": "all"}}

User: "Create findings from VAPT report: SQL injection (critical), XSS (high)"
Response: {"action": "create_findings", "entity": "finding", "count": 2, "parameters": {"findings": [{"title": "SQL Injection", "severity": "critical"}, {"title": "XSS", "severity": "high"}]}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            intent = json.loads(response.choices[0].message.content)
            logger.info(f"Parsed intent: {intent}")
            return intent
        except Exception as e:
            logger.error(f"Error parsing intent: {str(e)}")
            raise
    
    def generate_controls(self, framework: str, domain_areas: List[str], count: int) -> List[Dict[str, Any]]:
        """
        Generate security controls based on framework and domains
        
        Args:
            framework: Security framework (e.g., "IM8", "NIST", "ISO27001")
            domain_areas: List of domain areas to cover
            count: Number of controls to generate
        
        Returns:
            List of control dictionaries
        """
        if not self.is_available():
            raise ValueError("LLM service not available")
        
        system_prompt = f"""You are a security compliance expert specializing in {framework}.
Generate {count} detailed security controls covering these domains: {', '.join(domain_areas)}

For each control, provide:
- name: Full control name with ID (e.g., "AC-1: Access Control Policy")
- description: Detailed description of the control
- control_type: Category (Access Control, Network Security, etc.)
- framework: {framework}
- control_id: Unique ID (e.g., "AC-1", "NS-2")
- category: Domain category
- requirement_level: Mandatory, Recommended, or Optional
- implementation_guidance: Practical guidance for implementation
- evidence_requirements: List of required evidence types
- testing_frequency: Quarterly, Semi-Annual, or Annual

Return a JSON object:
{{
    "controls": [
        {{"name": "...", "description": "...", ...}},
        ...
    ]
}}
"""
        
        user_prompt = f"Generate {count} {framework} security controls distributed across: {', '.join(domain_areas)}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=4000
            )
            
            result = json.loads(response.choices[0].message.content)
            controls = result.get("controls", [])
            logger.info(f"Generated {len(controls)} controls")
            return controls
        except Exception as e:
            logger.error(f"Error generating controls: {str(e)}")
            raise
    
    def generate_findings(self, findings_description: str, assessment_id: int, framework: str = "IM8") -> List[Dict[str, Any]]:
        """
        Generate structured findings from natural language description
        
        Args:
            findings_description: Natural language description of findings (e.g., VAPT report summary)
            assessment_id: Assessment ID to link findings to
            framework: Framework for control mapping
        
        Returns:
            List of finding dictionaries
        """
        if not self.is_available():
            raise ValueError("LLM service not available")
        
        system_prompt = f"""You are a security analyst. Parse the findings description and generate structured findings.

For each finding, extract:
- title: Short title
- description: Detailed description
- severity: critical, high, medium, low, or informational
- cvss: CVSS score (0.0-10.0)
- cve: CVE ID if applicable
- remediation: Remediation steps
- priority: critical, high, medium, or low
- im8_domain: Map to IM8 domain (IM8-01 through IM8-10)
- control_mapping: Suggested control IDs

Return JSON:
{{
    "findings": [
        {{
            "title": "...",
            "description": "...",
            "severity": "critical",
            "cvss": "9.8",
            "remediation": "...",
            "priority": "critical",
            "im8_domain": "IM8-03",
            "control_mapping": ["DP-1", "DP-2"]
        }},
        ...
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": findings_description}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            findings = result.get("findings", [])
            
            # Add assessment_id to each finding
            for finding in findings:
                finding["assessment_id"] = assessment_id
            
            logger.info(f"Generated {len(findings)} findings")
            return findings
        except Exception as e:
            logger.error(f"Error generating findings: {str(e)}")
            raise
    
    def analyze_evidence(self, evidence_content: str, control_requirements: List[str]) -> Dict[str, Any]:
        """
        Analyze evidence document against control requirements
        
        Args:
            evidence_content: Content of the evidence document
            control_requirements: List of requirements the evidence should satisfy
        
        Returns:
            Analysis results with completeness score and gaps
        """
        if not self.is_available():
            raise ValueError("LLM service not available")
        
        system_prompt = """You are a compliance auditor. Analyze the evidence document against the control requirements.

Provide:
1. completeness_score: 0-100 based on how well evidence satisfies requirements
2. satisfied_requirements: List of requirements that are satisfied
3. missing_requirements: List of requirements not addressed
4. gaps: List of specific gaps found
5. recommendations: Suggestions for improvement
6. metadata: Any relevant metadata extracted (dates, owners, versions, etc.)

Return JSON:
{
    "completeness_score": 85,
    "satisfied_requirements": [...],
    "missing_requirements": [...],
    "gaps": [...],
    "recommendations": [...],
    "metadata": {...}
}
"""
        
        user_prompt = f"""Evidence Content:
{evidence_content[:2000]}... (truncated)

Control Requirements:
{json.dumps(control_requirements, indent=2)}

Analyze this evidence."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Evidence analysis complete. Score: {analysis.get('completeness_score', 'N/A')}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing evidence: {str(e)}")
            raise
    
    def generate_report(self, report_type: str, data: Dict[str, Any]) -> str:
        """
        Generate compliance report in markdown format
        
        Args:
            report_type: "executive" or "technical"
            data: Report data (assessment results, findings, metrics)
        
        Returns:
            Report content in markdown format
        """
        if not self.is_available():
            raise ValueError("LLM service not available")
        
        if report_type == "executive":
            system_prompt = """You are a compliance report writer. Generate an executive summary report for senior management.

The report should:
- Be clear and concise
- Use non-technical language
- Focus on business impact
- Include key metrics and trends
- Provide actionable recommendations
- Use bullet points and sections

Format in Markdown with sections:
# Executive Summary
## Overall Compliance Status
## Key Findings
## Risk Assessment
## Recommendations
## Conclusion
"""
        else:  # technical
            system_prompt = """You are a compliance auditor. Generate a detailed technical audit report.

The report should:
- Include complete control testing results
- List all findings with CVSS scores
- Detail evidence inventory
- Provide gap analysis
- Include technical details
- Reference specific controls and standards

Format in Markdown with sections:
# Technical Audit Report
## Assessment Overview
## Control Testing Results
## Findings Analysis
## Evidence Review
## Gap Analysis
## Recommendations
## Appendices
"""
        
        user_prompt = f"""Generate a {report_type} compliance report using this data:

{json.dumps(data, indent=2)}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            report_content = response.choices[0].message.content
            logger.info(f"Generated {report_type} report ({len(report_content)} chars)")
            return report_content
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
