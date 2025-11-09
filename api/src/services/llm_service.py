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
    
    def parse_user_intent(self, user_prompt: str, conversation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse user's natural language prompt to extract intent and parameters
        Supports multi-turn conversation for gathering missing parameters
        
        Args:
            user_prompt: User's message
            conversation_context: Previous conversation state with partial parameters
        
        Returns:
        {
            "action": "create_controls" | "create_findings" | "analyze_evidence" | "generate_report",
            "entity": "control" | "finding" | "evidence" | "assessment" | "report",
            "count": int,
            "parameters": {...},
            "missing_parameters": [...],  # List of parameters still needed
            "clarifying_question": str,    # Next question to ask user
            "is_ready": bool               # True if all required params collected
        }
        """
        if not self.is_available():
            raise ValueError("LLM service not available. Configure AZURE_OPENAI or OPENAI credentials.")
        
        # Build context-aware system prompt
        context_info = ""
        if conversation_context:
            context_info = f"\n\nCONVERSATION CONTEXT (previous information collected):\n{json.dumps(conversation_context, indent=2)}\n\nMerge this context with any new information from the user's message."
        
        system_prompt = f"""You are an AI assistant for a compliance management system that uses CONVERSATIONAL information gathering.

Your task: Parse the user's request and identify what information is still needed.

REQUIRED PARAMETERS by action:
- create_controls: project_id (required - must exist in database), framework (default: IM8), count (default: 30), domain_areas (default: all)
- create_findings: assessment_id (required - must exist in database), findings_description (from user message)
- analyze_evidence: control_id (required - must exist in database), evidence_ids (optional - can be all evidence for that control)
- generate_report: assessment_id (required - must exist in database), report_type (default: executive)

CRITICAL: Do NOT mark as is_ready=true if required parameters are missing OR use placeholders like "control 5" without validation.

SMART DEFAULTS (use these if not specified):
- framework: "IM8"
- count: 30 for controls
- domain_areas: ["IM8-01", "IM8-02", "IM8-03", "IM8-04", "IM8-05", "IM8-06", "IM8-07", "IM8-08", "IM8-09", "IM8-10"]
- report_type: "executive"

Return JSON:
{{
    "action": "action_name",
    "entity": "entity_type",
    "count": number_or_default,
    "parameters": {{}},
    "missing_parameters": [],  // List parameters still needed
    "clarifying_question": "",  // Natural question to ask user (max 80 chars)
    "suggested_responses": [],  // 3-5 suggested quick responses
    "is_ready": false,  // True only when ALL required params collected
    "expert_mode_detected": false  // True if user provides complete info upfront
}}

QUESTION GUIDELINES:
1. Ask ONE question at a time
2. Keep questions under 80 characters
3. Provide 3-5 concrete suggestions
4. Use friendly, conversational tone
5. Maximum 5 questions total per task

EXAMPLES:

User: "Upload controls"
Response: {{
    "action": "create_controls",
    "entity": "control",
    "count": 30,
    "parameters": {{"framework": "IM8"}},
    "missing_parameters": ["project_id", "domain_areas"],
    "clarifying_question": "Which project should I add these controls to?",
    "suggested_responses": ["Project 1: 2025 Annual Compliance", "Project 2: Q4 Security Audit", "Show all projects"],
    "is_ready": false,
    "expert_mode_detected": false
}}

User: "Upload 30 IM8 controls for Access Control domain to project 1"
Response: {{
    "action": "create_controls",
    "entity": "control",
    "count": 30,
    "parameters": {{"framework": "IM8", "domain_areas": ["IM8-01"], "project_id": 1}},
    "missing_parameters": [],
    "clarifying_question": "",
    "suggested_responses": [],
    "is_ready": true,
    "expert_mode_detected": true
}}

User (after being asked about project): "Project 1"
Response: {{
    "action": "create_controls",
    "entity": "control",
    "count": 30,
    "parameters": {{"framework": "IM8", "project_id": 1, "domain_areas": ["all"]}},
    "missing_parameters": [],
    "is_ready": true
}}{context_info}
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
    
    def get_smart_suggestions(self, parameter_name: str, db_session: Any, user: Any) -> List[str]:
        """
        Generate smart suggestions for a parameter based on database context
        
        Args:
            parameter_name: Name of parameter needing suggestions
            db_session: Database session for queries
            user: Current user object
        
        Returns:
            List of 3-5 suggested responses
        """
        suggestions = []
        
        try:
            if parameter_name == "project_id":
                # Fetch user's recent projects
                from api.src.models import Project
                projects = db_session.query(Project).filter(
                    Project.agency_id == user.agency_id,
                    Project.status == "active"
                ).order_by(Project.updated_at.desc()).limit(5).all()
                
                suggestions = [f"Project {p.id}: {p.name}" for p in projects]
                if suggestions:
                    suggestions.append("Show all projects")
                else:
                    suggestions = ["Create new project first"]
            
            elif parameter_name == "assessment_id":
                # Fetch recent assessments
                from api.src.models import Assessment
                assessments = db_session.query(Assessment).filter(
                    Assessment.agency_id == user.agency_id
                ).order_by(Assessment.created_at.desc()).limit(5).all()
                
                suggestions = [f"Assessment {a.id}: {a.title}" for a in assessments]
                if suggestions:
                    suggestions.append("Show all assessments")
            
            elif parameter_name == "control_id":
                # Fetch recent controls
                from api.src.models import Control
                controls = db_session.query(Control).filter(
                    Control.agency_id == user.agency_id
                ).order_by(Control.created_at.desc()).limit(5).all()
                
                suggestions = [f"Control {c.id}: {c.name}" for c in controls]
                if suggestions:
                    suggestions.append("Show all controls")
                else:
                    suggestions = ["Create controls first"]
            
            elif parameter_name == "evidence_ids":
                # Fetch recent evidence
                from api.src.models import Evidence
                evidence = db_session.query(Evidence).filter(
                    Evidence.agency_id == user.agency_id
                ).order_by(Evidence.created_at.desc()).limit(5).all()
                
                suggestions = [f"Evidence {e.id}: {e.title}" for e in evidence]
                if suggestions:
                    suggestions.append("All evidence for this control")
            
            elif parameter_name == "domain_areas":
                # Offer IM8 domains
                suggestions = [
                    "IM8-01: Access Control",
                    "IM8-02: Network Security",
                    "IM8-03: Data Protection",
                    "IM8-06: Logging & Monitoring",
                    "All 10 IM8 domains"
                ]
            
            elif parameter_name == "report_type":
                suggestions = ["Executive Summary", "Technical Audit Report", "Compliance Certificate"]
            
            elif parameter_name == "count":
                suggestions = ["5 controls", "10 controls", "30 controls (full set)", "50 controls"]
        
        except Exception as e:
            logger.error(f"Error generating suggestions for {parameter_name}: {str(e)}")
            suggestions = [f"Enter {parameter_name}"]
        
        return suggestions[:5]  # Max 5 suggestions
    
    def validate_parameters(self, action: str, parameters: Dict[str, Any], db_session: Any, user: Any) -> tuple[bool, List[str], str]:
        """
        Validate that required parameters exist in database
        
        Args:
            action: Action type
            parameters: Parameters to validate
            db_session: Database session
            user: Current user
        
        Returns:
            (is_valid, missing_params, error_message)
        """
        from api.src.models import Project, Assessment, Control, Evidence
        
        missing = []
        error_msg = ""
        
        try:
            if action == "create_controls":
                project_id = parameters.get("project_id")
                if not project_id:
                    missing.append("project_id")
                else:
                    # Validate project exists and user has access
                    project = db_session.query(Project).filter(
                        Project.id == project_id,
                        Project.agency_id == user.agency_id
                    ).first()
                    if not project:
                        error_msg = f"Project {project_id} not found or you don't have access to it."
                        return False, missing, error_msg
            
            elif action == "create_findings" or action == "generate_report":
                assessment_id = parameters.get("assessment_id")
                if not assessment_id:
                    missing.append("assessment_id")
                else:
                    # Validate assessment exists and user has access
                    assessment = db_session.query(Assessment).filter(
                        Assessment.id == assessment_id,
                        Assessment.agency_id == user.agency_id
                    ).first()
                    if not assessment:
                        error_msg = f"Assessment {assessment_id} not found or you don't have access to it."
                        return False, missing, error_msg
            
            elif action == "analyze_evidence":
                control_id = parameters.get("control_id")
                if not control_id:
                    missing.append("control_id")
                else:
                    # Validate control exists and user has access
                    control = db_session.query(Control).filter(
                        Control.id == control_id,
                        Control.agency_id == user.agency_id
                    ).first()
                    if not control:
                        error_msg = f"Control {control_id} not found or you don't have access to it."
                        return False, missing, error_msg
                
                # Evidence IDs are optional - if not provided, analyze all evidence for that control
                evidence_ids = parameters.get("evidence_ids", [])
                if evidence_ids:
                    # Validate all evidence IDs exist
                    for eid in evidence_ids:
                        evidence = db_session.query(Evidence).filter(Evidence.id == eid).first()
                        if not evidence:
                            error_msg = f"Evidence {eid} not found."
                            return False, missing, error_msg
        
        except Exception as e:
            logger.error(f"Error validating parameters: {str(e)}")
            error_msg = f"Validation error: {str(e)}"
            return False, missing, error_msg
        
        return len(missing) == 0 and not error_msg, missing, error_msg
    
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
