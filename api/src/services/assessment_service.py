"""
Assessment Service - Business logic for assessment management
Handles auto-status updates, progress calculation, and validation
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.src.models import Assessment, Finding, AssessmentControl, Control


class AssessmentService:
    """Service for assessment business logic"""
    
    @staticmethod
    def calculate_progress(assessment: Assessment, db: Session) -> int:
        """
        Calculate assessment progress based on:
        - Controls tested / Total controls
        - Findings resolved / Total findings
        """
        total_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.selected_for_testing == True
        ).count()
        
        if total_controls == 0:
            return 0
        
        completed_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.selected_for_testing == True,
            AssessmentControl.testing_status.in_(['completed', 'passed'])
        ).count()
        
        control_progress = (completed_controls / total_controls) * 70  # 70% weight
        
        # Finding resolution progress (30% weight)
        total_findings = db.query(Finding).filter(
            Finding.assessment_id == assessment.id
        ).count()
        
        if total_findings > 0:
            resolved_findings = db.query(Finding).filter(
                Finding.assessment_id == assessment.id,
                Finding.resolution_status.in_(['resolved', 'accepted_risk', 'false_positive'])
            ).count()
            finding_progress = (resolved_findings / total_findings) * 30
        else:
            finding_progress = 30  # If no findings, consider this part complete
        
        return min(100, int(control_progress + finding_progress))
    
    @staticmethod
    def update_assessment_counts(assessment: Assessment, db: Session):
        """Update assessment counts for controls tested and findings"""
        assessment.controls_tested_count = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status.in_(['completed', 'passed', 'failed'])
        ).count()
        
        assessment.findings_count = db.query(Finding).filter(
            Finding.assessment_id == assessment.id
        ).count()
        
        db.commit()
    
    @staticmethod
    def auto_update_status(assessment: Assessment, db: Session):
        """
        Automatically update assessment status based on progress
        - open: 0-10% progress
        - in_progress: 10-90% progress
        - under_review: 90-100% progress, not all findings resolved
        - completed: 100% progress, all critical findings resolved
        """
        progress = AssessmentService.calculate_progress(assessment, db)
        
        if progress == 0:
            new_status = 'open'
        elif progress < 90:
            new_status = 'in_progress'
        elif progress >= 90:
            # Check if all critical findings are resolved
            critical_open = db.query(Finding).filter(
                Finding.assessment_id == assessment.id,
                Finding.severity.in_(['critical', 'high']),
                Finding.resolution_status == 'open'
            ).count()
            
            if critical_open == 0 and progress == 100:
                new_status = 'completed'
                assessment.completed_at = datetime.utcnow()
            else:
                new_status = 'under_review'
        else:
            new_status = assessment.status
        
        if new_status != assessment.status:
            assessment.status = new_status
            db.commit()
    
    @staticmethod
    def validate_assessment(assessment: Assessment, db: Session) -> List[str]:
        """
        Validate assessment data and return list of validation errors
        """
        errors = []
        
        # Check title
        if not assessment.title or len(assessment.title) < 5:
            errors.append("Assessment title must be at least 5 characters")
        
        # Check framework
        valid_frameworks = ['NIST', 'ISO27001', 'SOC2', 'FISMA', 'HIPAA', 'PCI-DSS']
        if assessment.framework and assessment.framework.upper() not in valid_frameworks:
            errors.append(f"Framework must be one of: {', '.join(valid_frameworks)}")
        
        # Check dates
        if assessment.assessment_period_start and assessment.assessment_period_end:
            if assessment.assessment_period_start > assessment.assessment_period_end:
                errors.append("Assessment start date must be before end date")
        
        if assessment.target_completion_date:
            if assessment.target_completion_date < datetime.utcnow().date():
                errors.append("Target completion date cannot be in the past")
        
        # Check controls
        controls_count = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id
        ).count()
        if controls_count == 0:
            errors.append("Assessment must have at least one control selected")
        
        return errors
    
    @staticmethod
    def get_assessment_metrics(assessment: Assessment, db: Session) -> dict:
        """Get comprehensive metrics for an assessment"""
        
        # Control metrics
        total_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id
        ).count()
        
        passed_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status == 'passed'
        ).count()
        
        failed_controls = db.query(AssessmentControl).filter(
            AssessmentControl.assessment_id == assessment.id,
            AssessmentControl.testing_status == 'failed'
        ).count()
        
        # Finding metrics by severity
        findings_by_severity = db.query(
            Finding.severity,
            func.count(Finding.id)
        ).filter(
            Finding.assessment_id == assessment.id
        ).group_by(Finding.severity).all()
        
        severity_counts = {severity: count for severity, count in findings_by_severity}
        
        # Finding metrics by status
        findings_by_status = db.query(
            Finding.resolution_status,
            func.count(Finding.id)
        ).filter(
            Finding.assessment_id == assessment.id
        ).group_by(Finding.resolution_status).all()
        
        status_counts = {status: count for status, count in findings_by_status}
        
        # Calculate completion time estimate
        days_elapsed = (datetime.utcnow() - assessment.created_at).days
        if assessment.progress_percentage > 0:
            estimated_total_days = int((days_elapsed / assessment.progress_percentage) * 100)
            days_remaining = max(0, estimated_total_days - days_elapsed)
        else:
            days_remaining = None
        
        return {
            "progress_percentage": assessment.progress_percentage,
            "status": assessment.status,
            "controls": {
                "total": total_controls,
                "tested": assessment.controls_tested_count,
                "passed": passed_controls,
                "failed": failed_controls,
                "pending": total_controls - assessment.controls_tested_count
            },
            "findings": {
                "total": assessment.findings_count,
                "by_severity": severity_counts,
                "by_status": status_counts
            },
            "timeline": {
                "days_elapsed": days_elapsed,
                "days_remaining": days_remaining,
                "target_date": assessment.target_completion_date.isoformat() if assessment.target_completion_date else None
            }
        }
    
    @staticmethod
    def check_overdue(assessment: Assessment) -> bool:
        """Check if assessment is overdue"""
        if not assessment.target_completion_date:
            return False
        return datetime.utcnow().date() > assessment.target_completion_date
    
    @staticmethod
    def get_at_risk_assessments(db: Session, days_threshold: int = 7) -> List[Assessment]:
        """Get assessments at risk of missing deadline"""
        threshold_date = datetime.utcnow().date() + timedelta(days=days_threshold)
        
        return db.query(Assessment).filter(
            Assessment.status.in_(['open', 'in_progress']),
            Assessment.target_completion_date.isnot(None),
            Assessment.target_completion_date <= threshold_date,
            Assessment.progress_percentage < 80
        ).all()
