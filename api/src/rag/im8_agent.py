"""Agentic Reasoning System for Singapore IM8 Compliance"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from .llm_service import llm_service
from .enhanced_embeddings import enhanced_embedding_service
from .im8_knowledge_base import IM8_CONTROLS, SINGAPORE_COMPLIANCE_CONTEXT, IM8_FRAMEWORK_MAPPINGS

class ReasoningStep(Enum):
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    VALIDATE = "validate"
    SYNTHESIZE = "synthesize"

@dataclass
class ReasoningResult:
    step: ReasoningStep
    content: str
    confidence: float
    sources: List[Dict[str, Any]]
    next_actions: List[str]

class IM8ComplianceAgent:
    """Agentic reasoning system for Singapore IM8 compliance analysis"""
    
    def __init__(self):
        self.reasoning_history: List[ReasoningResult] = []
        self.singapore_context = SINGAPORE_COMPLIANCE_CONTEXT
        self.im8_controls = IM8_CONTROLS
        self.framework_mappings = IM8_FRAMEWORK_MAPPINGS
    
    async def analyze_compliance_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for agentic compliance analysis"""
        
        print(f"🤖 IM8 Agent: Starting analysis for: {query}")
        
        # Step 1: Analyze the query to understand requirements
        analysis_result = await self._analyze_requirements(query, context)
        
        # Step 2: Plan the compliance assessment approach
        plan_result = await self._plan_assessment(query, analysis_result)
        
        # Step 3: Execute the assessment using IM8 knowledge
        execution_result = await self._execute_assessment(query, plan_result)
        
        # Step 4: Validate findings against Singapore regulations
        validation_result = await self._validate_against_regulations(execution_result)
        
        # Step 5: Synthesize final recommendations
        synthesis_result = await self._synthesize_recommendations(query, validation_result)
        
        return {
            "query": query,
            "agent_reasoning": [
                analysis_result.__dict__,
                plan_result.__dict__,
                execution_result.__dict__,
                validation_result.__dict__,
                synthesis_result.__dict__
            ],
            "final_answer": synthesis_result.content,
            "confidence_score": synthesis_result.confidence,
            "singapore_specific": True,
            "im8_controls_referenced": self._extract_im8_controls(synthesis_result.sources),
            "compliance_gaps": self._identify_gaps(synthesis_result.sources),
            "next_steps": synthesis_result.next_actions
        }
    
    async def _analyze_requirements(self, query: str, context: Dict[str, Any]) -> ReasoningResult:
        """Step 1: Analyze what the user is asking for"""
        
        analysis_prompt = f"""
        As a Singapore Government IM8 compliance expert, analyze this query:
        
        Query: "{query}"
        Context: {json.dumps(context or {}, indent=2)}
        
        Analyze:
        1. What specific IM8 compliance areas are being asked about?
        2. Which Singapore government regulations are relevant?
        3. What type of analysis is needed (gap analysis, implementation guidance, risk assessment)?
        4. What government context should be considered (agency type, data sensitivity, etc.)?
        
        Focus on Singapore government requirements and IM8 framework.
        """
        
        response = await llm_service.generate_completion([{"role": "user", "content": analysis_prompt}])
        
        # Find relevant IM8 controls
        relevant_controls = []
        query_lower = query.lower()
        for control_id, control_data in self.im8_controls.items():
            if (control_data["title"].lower() in query_lower or 
                control_data["category"].lower() in query_lower or
                any(keyword in query_lower for keyword in control_data.get("singapore_context", "").lower().split())):
                relevant_controls.append({
                    "control_id": control_id,
                    "title": control_data["title"],
                    "category": control_data["category"]
                })
        
        return ReasoningResult(
            step=ReasoningStep.ANALYZE,
            content=response,
            confidence=0.85,
            sources=relevant_controls,
            next_actions=["plan_assessment", "identify_im8_controls"]
        )
    
    async def _plan_assessment(self, query: str, analysis: ReasoningResult) -> ReasoningResult:
        """Step 2: Plan the assessment approach"""
        
        planning_prompt = f"""
        Based on the requirements analysis, plan a comprehensive IM8 compliance assessment:
        
        Requirements Analysis: {analysis.content}
        Relevant Controls: {json.dumps(analysis.sources, indent=2)}
        
        Create a structured plan that includes:
        1. Which IM8 control families to examine (AC, DG, RM, IM, etc.)
        2. Singapore-specific considerations (regulations, government context)
        3. Assessment methodology (gap analysis, risk assessment, implementation review)
        4. Expected deliverables and recommendations
        
        Focus on practical implementation for Singapore government agencies.
        """
        
        response = await llm_service.generate_completion([{"role": "user", "content": planning_prompt}])
        
        # Identify control families and Singapore regulations
        control_families = set()
        singapore_regs = []
        
        for source in analysis.sources:
            if "control_id" in source:
                family = source["control_id"].split(".")[1]  # Extract family (AC, DG, etc.)
                control_families.add(family)
        
        # Map to Singapore regulations
        for family in control_families:
            if family == "AC":
                singapore_regs.append("Cybersecurity Act 2018")
            elif family == "DG":
                singapore_regs.extend(["PDPA 2012", "Official Secrets Act"])
            elif family == "RM":
                singapore_regs.append("Cybersecurity Act 2018")
        
        return ReasoningResult(
            step=ReasoningStep.PLAN,
            content=response,
            confidence=0.90,
            sources=[{"control_families": list(control_families), "singapore_regulations": list(set(singapore_regs))}],
            next_actions=["execute_assessment", "gather_im8_guidance"]
        )
    
    async def _execute_assessment(self, query: str, plan: ReasoningResult) -> ReasoningResult:
        """Step 3: Execute the detailed IM8 assessment"""
        
        # Get detailed IM8 control information
        relevant_im8_controls = []
        for control_id, control_data in self.im8_controls.items():
            control_family = control_id.split(".")[1]
            if any(control_family in str(source) for source in plan.sources):
                relevant_im8_controls.append({
                    "id": control_id,
                    "title": control_data["title"],
                    "description": control_data["description"],
                    "category": control_data["category"],
                    "singapore_context": control_data["singapore_context"],
                    "implementation_guidance": control_data["implementation_guidance"],
                    "related_regulations": control_data["related_regulations"],
                    "risk_rating": control_data["risk_rating"],
                    "dependencies": control_data.get("dependencies", [])
                })
        
        execution_prompt = f"""
        Execute detailed IM8 compliance assessment based on the plan:
        
        Assessment Plan: {plan.content}
        Query: "{query}"
        
        IM8 Controls to Assess:
        {json.dumps(relevant_im8_controls, indent=2)}
        
        Provide:
        1. Detailed analysis of each relevant IM8 control
        2. Singapore government implementation requirements
        3. Regulatory compliance mapping
        4. Specific gaps or recommendations
        5. Risk assessment from Singapore government perspective
        
        Focus on actionable guidance for Singapore government agencies.
        """
        
        response = await llm_service.generate_completion([{"role": "user", "content": execution_prompt}])
        
        return ReasoningResult(
            step=ReasoningStep.EXECUTE,
            content=response,
            confidence=0.88,
            sources=relevant_im8_controls,
            next_actions=["validate_regulations", "check_dependencies"]
        )
    
    async def _validate_against_regulations(self, execution: ReasoningResult) -> ReasoningResult:
        """Step 4: Validate against Singapore regulations"""
        
        # Extract relevant Singapore regulations
        singapore_regs = set()
        for source in execution.sources:
            if "related_regulations" in source:
                singapore_regs.update(source["related_regulations"])
        
        validation_prompt = f"""
        Validate the IM8 assessment against Singapore government regulations:
        
        Assessment Results: {execution.content}
        
        Singapore Regulations to Validate Against:
        {json.dumps(list(singapore_regs), indent=2)}
        
        Singapore Compliance Context:
        {json.dumps(self.singapore_context, indent=2)}
        
        Validate:
        1. Compliance with Cybersecurity Act 2018 requirements
        2. PDPA 2012 considerations for government data
        3. Alignment with Whole-of-Government standards
        4. Smart Nation initiative compatibility
        5. Critical Information Infrastructure requirements (if applicable)
        
        Highlight any regulatory gaps or conflicts.
        """
        
        response = await llm_service.generate_completion([{"role": "user", "content": validation_prompt}])
        
        regulatory_sources = []
        for reg in singapore_regs:
            if reg in self.singapore_context["regulations"]:
                regulatory_sources.append({
                    "regulation": reg,
                    "details": self.singapore_context["regulations"][reg]
                })
        
        return ReasoningResult(
            step=ReasoningStep.VALIDATE,
            content=response,
            confidence=0.92,
            sources=regulatory_sources,
            next_actions=["synthesize_recommendations", "prioritize_actions"]
        )
    
    async def _synthesize_recommendations(self, query: str, validation: ReasoningResult) -> ReasoningResult:
        """Step 5: Synthesize final recommendations"""
        
        synthesis_prompt = f"""
        Synthesize comprehensive IM8 compliance recommendations:
        
        Original Query: "{query}"
        Validation Results: {validation.content}
        
        Provide a comprehensive response that includes:
        1. Executive summary for Singapore government stakeholders
        2. Specific IM8 control implementation guidance
        3. Regulatory compliance requirements
        4. Prioritized action plan
        5. Risk mitigation strategies
        6. Integration with existing government systems
        7. Timeline and resource considerations
        
        Make recommendations practical and actionable for Singapore government agencies.
        Include specific next steps and implementation priorities.
        """
        
        response = await llm_service.generate_completion([{"role": "user", "content": synthesis_prompt}])
        
        # Create comprehensive source list
        all_sources = []
        for step_result in [validation]:  # Could include all previous steps
            all_sources.extend(step_result.sources)
        
        # Generate specific next actions
        next_actions = [
            "Review IM8 control implementation requirements",
            "Assess current compliance gaps",
            "Develop implementation roadmap",
            "Coordinate with GovTech and CSA",
            "Plan staff training and awareness"
        ]
        
        return ReasoningResult(
            step=ReasoningStep.SYNTHESIZE,
            content=response,
            confidence=0.94,
            sources=all_sources,
            next_actions=next_actions
        )
    
    def _extract_im8_controls(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract IM8 control IDs from sources"""
        controls = []
        for source in sources:
            if "id" in source and source["id"].startswith("IM8"):
                controls.append(source["id"])
            elif "control_id" in source and source["control_id"].startswith("IM8"):
                controls.append(source["control_id"])
        return list(set(controls))
    
    def _identify_gaps(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Identify potential compliance gaps"""
        gaps = []
        
        # Check for missing high-risk controls
        high_risk_controls = [cid for cid, data in self.im8_controls.items() 
                             if data.get("risk_rating") == "Critical"]
        referenced_controls = self._extract_im8_controls(sources)
        
        for control in high_risk_controls:
            if control not in referenced_controls:
                gaps.append(f"Missing critical control: {control}")
        
        return gaps

# Global agent instance
im8_agent = IM8ComplianceAgent()