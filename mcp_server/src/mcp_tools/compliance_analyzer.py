"""
Compliance Analyzer MCP Tool
Analyzes project compliance against IM8/ISO/NIST frameworks.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ComplianceAnalyzerInput(BaseModel):
    """Input schema for compliance analyzer tool"""
    project_id: int = Field(..., description="Project ID to analyze")
    framework: str = Field(default="IM8", description="Framework: IM8, ISO27001, NIST")
    include_evidence: bool = Field(default=True, description="Include evidence analysis")
    generate_recommendations: bool = Field(default=True, description="Generate AI recommendations")


class ControlAssessment(BaseModel):
    """Assessment result for a single control"""
    control_id: int
    control_code: str
    control_name: str
    status: str  # implemented, partial, not_implemented, not_applicable
    score: float  # 0.0 to 1.0
    evidence_count: int
    gaps: List[str]
    recommendations: List[str]


class ComplianceAnalyzerOutput(BaseModel):
    """Output schema for compliance analyzer tool"""
    success: bool
    project_id: int
    framework: str
    overall_score: float = Field(..., description="Overall compliance score (0-100)")
    total_controls: int
    implemented_controls: int
    partial_controls: int
    not_implemented_controls: int
    not_applicable_controls: int
    critical_gaps: List[str] = Field(default_factory=list)
    control_assessments: List[ControlAssessment] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analyzed_at: str


class ComplianceAnalyzerTool:
    """
    MCP Tool: Compliance Analyzer
    
    Analyzes project compliance by:
    1. Fetching project controls and evidence
    2. Calculating compliance scores
    3. Identifying gaps
    4. Generating AI-powered recommendations
    """
    
    name = "analyze_compliance"
    description = "Analyze project compliance against IM8/ISO/NIST frameworks"
    
    def __init__(self, db_connection_string: str):
        """
        Initialize the compliance analyzer tool.
        
        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        return ComplianceAnalyzerInput.model_json_schema()
    
    @property
    def output_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool output"""
        return ComplianceAnalyzerOutput.model_json_schema()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the compliance analyzer tool.
        
        Args:
            params: Dictionary matching ComplianceAnalyzerInput schema
            
        Returns:
            Dictionary matching ComplianceAnalyzerOutput schema
        """
        # Validate input
        input_data = ComplianceAnalyzerInput(**params)
        
        # Get project controls
        controls = await self._get_project_controls(
            input_data.project_id,
            input_data.framework
        )
        
        # Assess each control
        control_assessments = []
        total_score = 0.0
        status_counts = {
            "implemented": 0,
            "partial": 0,
            "not_implemented": 0,
            "not_applicable": 0
        }
        critical_gaps = []
        
        for control in controls:
            assessment = await self._assess_control(
                control,
                input_data.project_id,
                input_data.include_evidence,
                input_data.generate_recommendations
            )
            
            control_assessments.append(assessment)
            total_score += assessment.score
            status_counts[assessment.status] += 1
            
            # Collect critical gaps (score < 0.3)
            if assessment.score < 0.3 and assessment.status != "not_applicable":
                critical_gaps.extend([
                    f"{assessment.control_code}: {gap}"
                    for gap in assessment.gaps
                ])
        
        # Calculate overall score
        total_applicable = len(controls) - status_counts["not_applicable"]
        overall_score = (total_score / total_applicable * 100) if total_applicable > 0 else 0.0
        
        # Generate high-level recommendations
        recommendations = await self._generate_recommendations(
            control_assessments,
            overall_score
        )
        
        return ComplianceAnalyzerOutput(
            success=True,
            project_id=input_data.project_id,
            framework=input_data.framework,
            overall_score=round(overall_score, 2),
            total_controls=len(controls),
            implemented_controls=status_counts["implemented"],
            partial_controls=status_counts["partial"],
            not_implemented_controls=status_counts["not_implemented"],
            not_applicable_controls=status_counts["not_applicable"],
            critical_gaps=critical_gaps[:10],  # Top 10
            control_assessments=control_assessments,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow().isoformat()
        ).model_dump()
    
    async def _get_project_controls(
        self,
        project_id: int,
        framework: str
    ) -> List[Dict[str, Any]]:
        """Fetch controls for the project and framework"""
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(self.db_connection_string)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Get controls for the project - controls table has project_id, no join table needed
            query = text("""
                SELECT 
                    c.id,
                    c.name,
                    c.description,
                    c.control_type,
                    c.status,
                    c.test_results
                FROM controls c
                WHERE c.project_id = :project_id
                ORDER BY c.id
            """)
            
            result = session.execute(query, {
                "project_id": project_id
            })
            
            controls = []
            for row in result:
                controls.append({
                    "id": row[0],
                    "control_code": f"CTRL-{row[0]}",  # Generate code from ID
                    "control_name": row[1],
                    "description": row[2],
                    "category": row[3],  # Using control_type as category
                    "priority": "medium",  # Default priority
                    "status": row[4] or "not_started",  # c.status with default
                    "implementation_notes": row[5] or ""  # c.test_results used as notes
                })
            
            return controls
    
    async def _assess_control(
        self,
        control: Dict[str, Any],
        project_id: int,
        include_evidence: bool,
        generate_recommendations: bool
    ) -> ControlAssessment:
        """Assess a single control"""
        # Count evidence
        evidence_count = 0
        if include_evidence:
            evidence_count = await self._count_evidence(
                control["id"],
                project_id
            )
        
        # Calculate score based on status and evidence
        status = control.get("status", "not_implemented")
        if status is None:
            status = "not_implemented"
        
        score = self._calculate_control_score(status, evidence_count)
        
        # Identify gaps
        gaps = self._identify_gaps(control, status, evidence_count)
        
        # Generate recommendations
        recommendations = []
        if generate_recommendations and score < 1.0:
            recommendations = self._generate_control_recommendations(
                control,
                gaps,
                evidence_count
            )
        
        return ControlAssessment(
            control_id=control["id"],
            control_code=control["control_code"],
            control_name=control["control_name"],
            status=status,
            score=score,
            evidence_count=evidence_count,
            gaps=gaps,
            recommendations=recommendations
        )
    
    async def _count_evidence(
        self,
        control_id: int,
        project_id: int
    ) -> int:
        """Count evidence for a control"""
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(self.db_connection_string)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Evidence table only has control_id, not project_id
            query = text("""
                SELECT COUNT(*)
                FROM evidence
                WHERE control_id = :control_id
            """)
            
            result = session.execute(query, {
                "control_id": control_id
            })
            
            return result.scalar_one()
    
    def _calculate_control_score(
        self,
        status: str,
        evidence_count: int
    ) -> float:
        """
        Calculate compliance score for a control.
        
        Logic:
        - not_applicable: 1.0 (doesn't count against score)
        - implemented + evidence >= 2: 1.0
        - implemented + evidence == 1: 0.8
        - implemented + no evidence: 0.6
        - partial + evidence >= 1: 0.5
        - partial + no evidence: 0.3
        - not_implemented: 0.0
        """
        if status == "not_applicable":
            return 1.0
        elif status == "implemented":
            if evidence_count >= 2:
                return 1.0
            elif evidence_count == 1:
                return 0.8
            else:
                return 0.6
        elif status == "partial":
            if evidence_count >= 1:
                return 0.5
            else:
                return 0.3
        else:  # not_implemented
            return 0.0
    
    def _identify_gaps(
        self,
        control: Dict[str, Any],
        status: str,
        evidence_count: int
    ) -> List[str]:
        """Identify gaps for a control"""
        gaps = []
        
        if status == "not_implemented":
            gaps.append("Control not yet implemented")
        elif status == "partial":
            gaps.append("Control only partially implemented")
        
        if status in ["implemented", "partial"] and evidence_count == 0:
            gaps.append("No evidence uploaded")
        elif status == "implemented" and evidence_count == 1:
            gaps.append("Insufficient evidence (minimum 2 recommended)")
        
        if control.get("priority") == "critical" and status != "implemented":
            gaps.append("CRITICAL priority control requires immediate attention")
        
        return gaps
    
    def _generate_control_recommendations(
        self,
        control: Dict[str, Any],
        gaps: List[str],
        evidence_count: int
    ) -> List[str]:
        """Generate recommendations for a control"""
        recommendations = []
        
        if "not yet implemented" in str(gaps):
            recommendations.append(
                f"Begin implementation of {control['control_code']} - {control['control_name']}"
            )
        
        if "partially implemented" in str(gaps):
            recommendations.append(
                f"Complete implementation of {control['control_code']}"
            )
        
        if evidence_count == 0:
            recommendations.append(
                f"Upload evidence for {control['control_code']}: policies, "
                f"procedures, screenshots, audit logs, or configuration files"
            )
        elif evidence_count == 1:
            recommendations.append(
                f"Upload additional evidence for {control['control_code']} "
                f"to strengthen compliance demonstration"
            )
        
        if control.get("priority") == "critical":
            recommendations.insert(0, "⚠️ HIGH PRIORITY: Address this critical control immediately")
        
        return recommendations
    
    async def _generate_recommendations(
        self,
        control_assessments: List[ControlAssessment],
        overall_score: float
    ) -> List[str]:
        """Generate high-level recommendations"""
        recommendations = []
        
        # Score-based recommendations
        if overall_score < 30:
            recommendations.append(
                "🚨 URGENT: Compliance score is critically low. Immediate action required."
            )
        elif overall_score < 50:
            recommendations.append(
                "⚠️ WARNING: Compliance score is below acceptable threshold. "
                "Focus on implementing critical controls."
            )
        elif overall_score < 70:
            recommendations.append(
                "📊 MODERATE: Compliance is progressing but needs improvement. "
                "Prioritize completing partially implemented controls."
            )
        elif overall_score < 90:
            recommendations.append(
                "✓ GOOD: Strong compliance posture. Focus on evidence collection "
                "and closing remaining gaps."
            )
        else:
            recommendations.append(
                "✅ EXCELLENT: High compliance score. Maintain current controls "
                "and keep evidence up to date."
            )
        
        # Count controls needing evidence
        needs_evidence = sum(
            1 for ca in control_assessments
            if ca.status in ["implemented", "partial"] and ca.evidence_count == 0
        )
        
        if needs_evidence > 0:
            recommendations.append(
                f"📎 Upload evidence for {needs_evidence} control(s) to strengthen "
                f"compliance demonstration"
            )
        
        # Count not implemented
        not_implemented = sum(
            1 for ca in control_assessments
            if ca.status == "not_implemented"
        )
        
        if not_implemented > 0:
            recommendations.append(
                f"🔧 Implement {not_implemented} control(s) to improve compliance score"
            )
        
        return recommendations
