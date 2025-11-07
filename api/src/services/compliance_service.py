"""
Compliance Service - Business logic for compliance framework management
Handles gap analysis, framework mapping, and compliance scoring
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.src.models import Assessment, Control, Finding, AssessmentControl


class ComplianceService:
    """Service for compliance framework business logic"""
    
    # Framework control requirements (sample - would be loaded from database)
    FRAMEWORK_REQUIREMENTS = {
        'NIST': {
            'required_controls': 200,
            'control_families': ['AC', 'AU', 'CM', 'IA', 'IR', 'MA', 'MP', 'PS', 'PE', 'PL', 'SA', 'SC', 'SI', 'SR']
        },
        'ISO27001': {
            'required_controls': 114,
            'control_families': ['A.5', 'A.6', 'A.7', 'A.8', 'A.9', 'A.10', 'A.11', 'A.12', 'A.13', 'A.14', 'A.15', 'A.16', 'A.17', 'A.18']
        },
        'SOC2': {
            'required_controls': 64,
            'control_families': ['CC1', 'CC2', 'CC3', 'CC4', 'CC5', 'CC6', 'CC7', 'CC8', 'CC9']
        },
        'FISMA': {
            'required_controls': 325,
            'control_families': ['AC', 'AT', 'AU', 'CA', 'CM', 'CP', 'IA', 'IR', 'MA', 'MP', 'PE', 'PL', 'PS', 'PT', 'RA', 'SA', 'SC', 'SI', 'SR']
        }
    }
    
    @staticmethod
    def calculate_compliance_score(assessment: Assessment, db: Session) -> Dict[str, any]:
        """
        Calculate overall compliance score based on:
        - Controls implemented / Total required
        - Controls passed / Controls tested
        - Critical findings resolved / Total critical findings
        """
        framework = assessment.framework.upper() if assessment.framework else None
        
        if not framework or framework not in ComplianceService.FRAMEWORK_REQUIREMENTS:
            return {
                "score": 0,
                "compliance_percentage": 0,
                "status": "unknown",
                "message": "Framework not specified or not supported"
            }
        
        requirements = ComplianceService.FRAMEWORK_REQUIREMENTS[framework]
        required_controls = requirements['required_controls']
        
        # Get assessment controls
        total_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id
        ).count()
        
        passed_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status == 'passed'
        ).count()
        
        tested_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status.in_(['passed', 'failed'])
        ).count()
        
        # Control coverage score (40% weight)
        coverage_score = min(100, (total_controls / required_controls) * 100) * 0.4
        
        # Control effectiveness score (40% weight)
        if tested_controls > 0:
            effectiveness_score = (passed_controls / tested_controls) * 100 * 0.4
        else:
            effectiveness_score = 0
        
        # Finding resolution score (20% weight)
        critical_findings = db.query(Finding).filter(
            Finding.assessment_id == assessment.id,
            Finding.severity.in_(['critical', 'high'])
        ).count()
        
        if critical_findings > 0:
            resolved_critical = db.query(Finding).filter(
                Finding.assessment_id == assessment.id,
                Finding.severity.in_(['critical', 'high']),
                Finding.resolution_status.in_(['resolved', 'accepted_risk'])
            ).count()
            finding_score = (resolved_critical / critical_findings) * 100 * 0.2
        else:
            finding_score = 20  # Full score if no critical findings
        
        total_score = coverage_score + effectiveness_score + finding_score
        
        # Determine compliance status
        if total_score >= 90:
            status = "compliant"
        elif total_score >= 70:
            status = "substantially_compliant"
        elif total_score >= 50:
            status = "partially_compliant"
        else:
            status = "non_compliant"
        
        return {
            "score": round(total_score, 2),
            "compliance_percentage": round(total_score, 2),
            "status": status,
            "breakdown": {
                "coverage": round(coverage_score, 2),
                "effectiveness": round(effectiveness_score, 2),
                "findings_resolution": round(finding_score, 2)
            },
            "metrics": {
                "total_controls": total_controls,
                "required_controls": required_controls,
                "passed_controls": passed_controls,
                "tested_controls": tested_controls,
                "critical_findings": critical_findings,
                "resolved_critical": critical_findings - (critical_findings - int(finding_score / 20 * critical_findings)) if critical_findings > 0 else 0
            }
        }
    
    @staticmethod
    def perform_gap_analysis(assessment: Assessment, db: Session) -> Dict[str, any]:
        """
        Perform gap analysis to identify missing or failing controls
        """
        framework = assessment.framework.upper() if assessment.framework else None
        
        if not framework or framework not in ComplianceService.FRAMEWORK_REQUIREMENTS:
            return {"error": "Framework not specified or not supported"}
        
        requirements = ComplianceService.FRAMEWORK_REQUIREMENTS[framework]
        
        # Get failed controls
        failed_controls = db.query(Control).join(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status == 'failed'
        ).all()
        
        # Get untested controls
        untested_controls = db.query(Control).join(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status == 'pending'
        ).all()
        
        # Get controls with open findings
        controls_with_findings = db.query(Control).join(Finding).filter(
            Finding.assessment_id == assessment.id,
            Finding.resolution_status.in_(['open', 'in_progress']),
            Finding.severity.in_(['critical', 'high'])
        ).distinct().all()
        
        # Calculate coverage by control family
        family_coverage = {}
        for family in requirements['control_families']:
            total_in_family = db.query(Control).join(AssessmentControl).filter(
                AssessmentControl.assessment_id == assessment.id,
                Control.control_type.like(f'{family}%')
            ).count()
            
            passed_in_family = db.query(Control).join(AssessmentControl).filter(
                AssessmentControl.assessment_id == assessment.id,
                Control.control_type.like(f'{family}%'),
                AssessmentControl.testing_status == 'passed'
            ).count()
            
            family_coverage[family] = {
                'total': total_in_family,
                'passed': passed_in_family,
                'coverage_percentage': (passed_in_family / total_in_family * 100) if total_in_family > 0 else 0
            }
        
        return {
            "framework": framework,
            "gaps_identified": {
                "failed_controls": len(failed_controls),
                "untested_controls": len(untested_controls),
                "controls_with_critical_findings": len(controls_with_findings)
            },
            "family_coverage": family_coverage,
            "recommendations": ComplianceService._generate_recommendations(
                failed_controls,
                untested_controls,
                controls_with_findings
            )
        }
    
    @staticmethod
    def _generate_recommendations(
        failed_controls: List[Control],
        untested_controls: List[Control],
        controls_with_findings: List[Control]
    ) -> List[str]:
        """Generate recommendations based on gap analysis"""
        recommendations = []
        
        if failed_controls:
            recommendations.append(
                f"Remediate {len(failed_controls)} failed control(s) to improve compliance posture"
            )
        
        if untested_controls:
            recommendations.append(
                f"Complete testing of {len(untested_controls)} remaining control(s)"
            )
        
        if controls_with_findings:
            recommendations.append(
                f"Resolve critical/high findings for {len(controls_with_findings)} control(s)"
            )
        
        if not recommendations:
            recommendations.append("All controls are passing. Maintain current compliance posture.")
        
        return recommendations
    
    @staticmethod
    def map_control_to_framework(
        control: Control,
        target_framework: str,
        db: Session
    ) -> Optional[str]:
        """
        Map a control to a target framework
        Returns the mapped control ID or None if no mapping exists
        """
        # This would typically use a control catalog mapping table
        # For now, return a placeholder based on control_type
        if not control.control_type:
            return None
        
        # Example simple mapping logic
        framework = target_framework.upper()
        control_type = control.control_type.upper()
        
        # NIST to ISO27001 mapping examples
        nist_to_iso = {
            'AC': 'A.9',  # Access Control
            'AU': 'A.12', # Audit and Accountability
            'CM': 'A.12', # Configuration Management
            'IA': 'A.9',  # Identification and Authentication
            'IR': 'A.16', # Incident Response
        }
        
        # ISO27001 to NIST mapping
        iso_to_nist = {v: k for k, v in nist_to_iso.items()}
        
        # Simple bidirectional mapping
        if framework == 'ISO27001' and control_type[:2] in nist_to_iso:
            return nist_to_iso[control_type[:2]]
        elif framework == 'NIST' and control_type[:4] in iso_to_nist:
            return iso_to_nist[control_type[:4]]
        
        return None
    
    @staticmethod
    def get_framework_statistics(framework: str, db: Session) -> Dict[str, any]:
        """Get statistics for a specific framework across all assessments"""
        
        assessments = db.query(Assessment).filter(
            Assessment.framework == framework
        ).all()
        
        if not assessments:
            return {
                "framework": framework,
                "total_assessments": 0,
                "message": "No assessments found for this framework"
            }
        
        total = len(assessments)
        completed = len([a for a in assessments if a.status == 'completed'])
        in_progress = len([a for a in assessments if a.status == 'in_progress'])
        
        # Calculate average compliance score
        scores = []
        for assessment in assessments:
            score_data = ComplianceService.calculate_compliance_score(assessment, db)
            scores.append(score_data['score'])
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "framework": framework,
            "total_assessments": total,
            "completed_assessments": completed,
            "in_progress_assessments": in_progress,
            "average_compliance_score": round(avg_score, 2),
            "assessment_completion_rate": round((completed / total * 100), 2) if total > 0 else 0
        }
