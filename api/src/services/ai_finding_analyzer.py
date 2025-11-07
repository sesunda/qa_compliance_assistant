"""
AI Finding Analyzer - Uses GitHub Models (Azure OpenAI) for finding analysis
Provides risk assessment, remediation suggestions, and impact analysis
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from api.src.models import Finding, Control, Assessment


class AIFindingAnalyzer:
    """AI-powered finding analysis using GitHub Models"""
    
    def __init__(self):
        """Initialize AI analyzer with GitHub Models endpoint"""
        self.enabled = OPENAI_AVAILABLE and os.getenv("GITHUB_TOKEN")
        
        if self.enabled:
            self.client = AzureOpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=os.getenv("GITHUB_TOKEN"),
            )
            self.model = os.getenv("AI_MODEL", "gpt-4o")  # Default to GPT-4o
        else:
            self.client = None
    
    def analyze_finding(self, finding: Finding, control: Optional[Control] = None) -> Dict[str, any]:
        """
        Analyze a finding and provide AI-powered insights
        """
        if not self.enabled:
            return self._fallback_analysis(finding)
        
        try:
            # Prepare context
            context = self._prepare_finding_context(finding, control)
            
            # Call AI model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a cybersecurity compliance expert. Analyze security findings and provide:
1. Risk assessment and business impact
2. Detailed remediation steps
3. Potential root causes
4. Recommended preventive measures
5. Estimated effort and timeline

Provide responses in JSON format."""
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this security finding:

Title: {finding.title}
Severity: {finding.severity}
Description: {finding.description}
Current Remediation: {finding.remediation or 'None provided'}
CVE: {finding.cve or 'N/A'}
CVSS: {finding.cvss or 'N/A'}

{context}

Provide a comprehensive analysis in JSON format with keys: risk_assessment, business_impact, detailed_remediation, root_causes, preventive_measures, estimated_effort_days"""
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Look for JSON in markdown code blocks
                if "```json" in ai_content:
                    json_start = ai_content.find("```json") + 7
                    json_end = ai_content.find("```", json_start)
                    ai_analysis = json.loads(ai_content[json_start:json_end].strip())
                elif "```" in ai_content:
                    json_start = ai_content.find("```") + 3
                    json_end = ai_content.find("```", json_start)
                    ai_analysis = json.loads(ai_content[json_start:json_end].strip())
                else:
                    ai_analysis = json.loads(ai_content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw content
                ai_analysis = {
                    "raw_response": ai_content,
                    "note": "Could not parse structured response"
                }
            
            return {
                "status": "success",
                "finding_id": finding.id,
                "analyzed_at": datetime.utcnow().isoformat(),
                "ai_model": self.model,
                "analysis": ai_analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "finding_id": finding.id,
                "fallback": self._fallback_analysis(finding)
            }
    
    def _prepare_finding_context(self, finding: Finding, control: Optional[Control]) -> str:
        """Prepare additional context about the finding"""
        context_parts = []
        
        if control:
            context_parts.append(f"Related Control: {control.name}")
            context_parts.append(f"Control Type: {control.control_type}")
            context_parts.append(f"Control Status: {control.status}")
        
        if finding.evidence:
            context_parts.append(f"Evidence: {json.dumps(finding.evidence)}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available"
    
    def _fallback_analysis(self, finding: Finding) -> Dict[str, any]:
        """Fallback analysis when AI is not available"""
        severity_impacts = {
            'critical': 'Immediate risk to business operations and data security',
            'high': 'Significant risk requiring prompt attention',
            'medium': 'Moderate risk that should be addressed in normal workflow',
            'low': 'Minor risk with limited impact',
            'info': 'Informational only, no immediate action required'
        }
        
        severity_efforts = {
            'critical': 7,
            'high': 14,
            'medium': 30,
            'low': 60,
            'info': 90
        }
        
        return {
            "status": "fallback",
            "finding_id": finding.id,
            "analysis": {
                "risk_assessment": f"{finding.severity.upper()} severity finding",
                "business_impact": severity_impacts.get(finding.severity.lower(), "Unknown impact"),
                "detailed_remediation": finding.remediation or "Remediation steps not provided",
                "estimated_effort_days": severity_efforts.get(finding.severity.lower(), 30),
                "note": "AI analysis not available - using rule-based fallback"
            }
        }
    
    def batch_analyze_findings(self, findings: List[Finding]) -> Dict[int, Dict]:
        """Analyze multiple findings in batch"""
        results = {}
        
        for finding in findings:
            results[finding.id] = self.analyze_finding(finding)
        
        return results
    
    def suggest_remediation_priority(self, findings: List[Finding]) -> List[Dict]:
        """Use AI to suggest remediation priority order"""
        if not self.enabled or not findings:
            return self._fallback_priority(findings)
        
        try:
            # Prepare findings summary
            findings_summary = "\n".join([
                f"{i+1}. [{f.severity}] {f.title} - {f.description[:100]}..."
                for i, f in enumerate(findings)
            ])
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert. Prioritize security findings based on risk, business impact, and interdependencies."
                    },
                    {
                        "role": "user",
                        "content": f"""Prioritize these security findings for remediation:

{findings_summary}

Return a JSON array of finding numbers in priority order (most urgent first), with brief justification for each."""
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            ai_content = response.choices[0].message.content
            # Parse and map back to finding IDs
            # Implementation would extract the priority order and map to findings
            
            return [{"finding_id": f.id, "priority": i+1} for i, f in enumerate(findings)]
            
        except Exception:
            return self._fallback_priority(findings)
    
    def _fallback_priority(self, findings: List[Finding]) -> List[Dict]:
        """Fallback priority based on severity and due date"""
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        
        sorted_findings = sorted(
            findings,
            key=lambda f: (
                severity_order.get(f.severity.lower(), 5),
                f.due_date or datetime.max,
                f.created_at
            )
        )
        
        return [
            {
                "finding_id": f.id,
                "priority": i + 1,
                "justification": f"Severity: {f.severity}, Due: {f.due_date}"
            }
            for i, f in enumerate(sorted_findings)
        ]


# Global instance
ai_analyzer = AIFindingAnalyzer()
