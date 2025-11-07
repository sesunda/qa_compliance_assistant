"""
Finding Service - Business logic for finding management
Handles risk scoring, SLA tracking, escalation, and validation
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.src.models import Finding, FindingComment, User, Assessment


class FindingService:
    """Service for finding business logic"""
    
    # Risk scoring weights
    SEVERITY_WEIGHTS = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25,
        'info': 10
    }
    
    # SLA days by severity
    SLA_DAYS = {
        'critical': 7,
        'high': 30,
        'medium': 60,
        'low': 90,
        'info': 120
    }
    
    @staticmethod
    def calculate_risk_score(finding: Finding) -> int:
        """
        Calculate risk score (0-100) based on:
        - Severity weight (base score)
        - CVSS score (if available)
        - Age of finding
        - Business impact
        """
        base_score = FindingService.SEVERITY_WEIGHTS.get(finding.severity.lower(), 25)
        
        # Adjust for CVSS if available
        cvss_adjustment = 0
        if finding.cvss:
            try:
                cvss_score = float(finding.cvss.split()[0])  # Extract numeric part
                cvss_adjustment = int((cvss_score / 10) * 20)  # Max +20 points
            except (ValueError, IndexError):
                pass
        
        # Adjust for age (overdue findings get higher score)
        age_adjustment = 0
        if finding.due_date and finding.due_date < datetime.utcnow():
            days_overdue = (datetime.utcnow() - finding.due_date).days
            age_adjustment = min(20, days_overdue * 2)  # Max +20 points
        
        return min(100, base_score + cvss_adjustment + age_adjustment)
    
    @staticmethod
    def calculate_due_date(finding: Finding) -> datetime:
        """Calculate due date based on severity and SLA"""
        sla_days = FindingService.SLA_DAYS.get(finding.severity.lower(), 90)
        return datetime.utcnow() + timedelta(days=sla_days)
    
    @staticmethod
    def auto_assign_priority(finding: Finding) -> str:
        """Auto-assign priority based on severity and risk score"""
        risk_score = FindingService.calculate_risk_score(finding)
        
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def check_sla_breach(finding: Finding) -> Dict[str, any]:
        """Check if finding is breaching or has breached SLA"""
        if not finding.due_date:
            return {"breached": False, "at_risk": False}
        
        now = datetime.utcnow()
        days_remaining = (finding.due_date - now).days
        
        breached = days_remaining < 0
        at_risk = 0 <= days_remaining <= 3  # 3 day warning
        
        return {
            "breached": breached,
            "at_risk": at_risk,
            "days_overdue": abs(days_remaining) if breached else 0,
            "days_remaining": days_remaining if not breached else 0
        }
    
    @staticmethod
    def validate_finding(finding: Finding, db: Session) -> List[str]:
        """Validate finding data and return list of errors"""
        errors = []
        
        # Title validation
        if not finding.title or len(finding.title) < 10:
            errors.append("Finding title must be at least 10 characters")
        
        # Severity validation
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        if not finding.severity or finding.severity.lower() not in valid_severities:
            errors.append(f"Severity must be one of: {', '.join(valid_severities)}")
        
        # Description validation
        if not finding.description or len(finding.description) < 20:
            errors.append("Finding description must be at least 20 characters")
        
        # Remediation validation
        if not finding.remediation or len(finding.remediation) < 10:
            errors.append("Remediation guidance must be at least 10 characters")
        
        # Resolution validation
        if finding.resolution_status in ['resolved', 'accepted_risk']:
            if not finding.resolved_by:
                errors.append("Resolved findings must have resolver assigned")
            if not finding.resolved_at:
                errors.append("Resolved findings must have resolution date")
        
        # False positive validation
        if finding.false_positive and not finding.validated_by:
            errors.append("False positive findings must be validated by QA")
        
        return errors
    
    @staticmethod
    def add_comment(
        finding_id: int,
        user_id: int,
        comment_text: str,
        comment_type: Optional[str],
        db: Session
    ) -> FindingComment:
        """Add a comment to a finding"""
        comment = FindingComment(
            finding_id=finding_id,
            user_id=user_id,
            comment_text=comment_text,
            comment_type=comment_type,
            created_at=datetime.utcnow()
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
    
    @staticmethod
    def get_findings_needing_escalation(db: Session) -> List[Finding]:
        """Get findings that need escalation (overdue or high risk)"""
        return db.query(Finding).filter(
            Finding.resolution_status.in_(['open', 'in_progress']),
            Finding.due_date < datetime.utcnow(),
            Finding.severity.in_(['critical', 'high'])
        ).all()
    
    @staticmethod
    def get_findings_by_analyst(analyst_id: int, db: Session) -> Dict[str, List[Finding]]:
        """Get findings grouped by status for an analyst"""
        findings = db.query(Finding).filter(
            Finding.assigned_to == analyst_id
        ).all()
        
        grouped = {
            'open': [],
            'in_progress': [],
            'resolved': [],
            'overdue': []
        }
        
        for finding in findings:
            if finding.resolution_status == 'open':
                if finding.due_date and finding.due_date < datetime.utcnow():
                    grouped['overdue'].append(finding)
                else:
                    grouped['open'].append(finding)
            elif finding.resolution_status == 'in_progress':
                grouped['in_progress'].append(finding)
            elif finding.resolution_status in ['resolved', 'accepted_risk', 'false_positive']:
                grouped['resolved'].append(finding)
        
        return grouped
    
    @staticmethod
    def get_findings_for_qa_review(db: Session) -> List[Finding]:
        """Get findings pending QA validation"""
        return db.query(Finding).filter(
            Finding.resolution_status == 'resolved',
            Finding.validated_by.is_(None),
            Finding.false_positive == False
        ).all()
    
    @staticmethod
    def validate_resolution(
        finding: Finding,
        validator_id: int,
        approved: bool,
        comments: Optional[str],
        db: Session
    ) -> bool:
        """
        QA validates a finding resolution
        Returns True if approved, False if rejected
        """
        finding.validated_by = validator_id
        finding.validated_at = datetime.utcnow()
        
        if approved:
            # Keep as resolved
            if comments:
                FindingService.add_comment(
                    finding.id,
                    validator_id,
                    f"QA Approved: {comments}",
                    'validation',
                    db
                )
        else:
            # Reject and reopen
            finding.resolution_status = 'in_progress'
            finding.validated_by = None
            finding.validated_at = None
            
            if comments:
                FindingService.add_comment(
                    finding.id,
                    validator_id,
                    f"QA Rejected: {comments}",
                    'validation',
                    db
                )
        
        db.commit()
        return approved
    
    @staticmethod
    def get_finding_metrics(db: Session, assessment_id: Optional[int] = None) -> dict:
        """Get comprehensive finding metrics"""
        query = db.query(Finding)
        if assessment_id:
            query = query.filter(Finding.assessment_id == assessment_id)
        
        # Total counts
        total = query.count()
        
        # By severity
        by_severity = query.with_entities(
            Finding.severity,
            func.count(Finding.id)
        ).group_by(Finding.severity).all()
        
        # By status
        by_status = query.with_entities(
            Finding.resolution_status,
            func.count(Finding.id)
        ).group_by(Finding.resolution_status).all()
        
        # Overdue
        overdue = query.filter(
            Finding.resolution_status.in_(['open', 'in_progress']),
            Finding.due_date < datetime.utcnow()
        ).count()
        
        # Pending QA
        pending_qa = query.filter(
            Finding.resolution_status == 'resolved',
            Finding.validated_by.is_(None)
        ).count()
        
        # Average resolution time
        resolved_findings = query.filter(
            Finding.resolution_status == 'resolved',
            Finding.resolved_at.isnot(None)
        ).all()
        
        if resolved_findings:
            total_days = sum([
                (f.resolved_at - f.created_at).days
                for f in resolved_findings
            ])
            avg_resolution_days = total_days / len(resolved_findings)
        else:
            avg_resolution_days = 0
        
        return {
            "total": total,
            "by_severity": {sev: count for sev, count in by_severity},
            "by_status": {status: count for status, count in by_status},
            "overdue": overdue,
            "pending_qa_validation": pending_qa,
            "avg_resolution_days": round(avg_resolution_days, 1)
        }
