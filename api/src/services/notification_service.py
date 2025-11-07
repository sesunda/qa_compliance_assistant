"""
Notification Service - Email notifications for findings, SLA breaches, and updates
Supports SMTP and SendGrid
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from api.src.models import Finding, Assessment, User


class NotificationService:
    """Service for sending email notifications"""
    
    def __init__(self):
        """Initialize notification service"""
        self.smtp_enabled = all([
            os.getenv("SMTP_HOST"),
            os.getenv("SMTP_PORT"),
            os.getenv("SMTP_USERNAME"),
            os.getenv("SMTP_PASSWORD")
        ])
        
        self.sendgrid_enabled = SENDGRID_AVAILABLE and os.getenv("SENDGRID_API_KEY")
        
        self.from_email = os.getenv("NOTIFICATION_FROM_EMAIL", "noreply@qca.com")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send email using available service (SendGrid or SMTP)
        """
        if self.sendgrid_enabled:
            return self._send_via_sendgrid(to_email, subject, body_html, body_text)
        elif self.smtp_enabled:
            return self._send_via_smtp(to_email, subject, body_html, body_text)
        else:
            return {
                "status": "disabled",
                "message": "Email service not configured"
            }
    
    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str]
    ) -> Dict[str, any]:
        """Send email via SendGrid"""
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=body_html,
                plain_text_content=body_text or body_html
            )
            
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            response = sg.send(message)
            
            return {
                "status": "success",
                "service": "sendgrid",
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "sendgrid",
                "error": str(e)
            }
    
    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str]
    ) -> Dict[str, any]:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
            
            # Connect and send
            with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))) as server:
                server.starttls()
                server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
                server.send_message(msg)
            
            return {
                "status": "success",
                "service": "smtp"
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "smtp",
                "error": str(e)
            }
    
    def notify_finding_assigned(self, finding: Finding, assignee: User) -> Dict[str, any]:
        """Notify user when a finding is assigned to them"""
        subject = f"[QCA] New Finding Assigned: {finding.title}"
        
        body_html = f"""
        <html>
        <body>
            <h2>New Finding Assigned</h2>
            <p>Hi {assignee.full_name},</p>
            <p>A new finding has been assigned to you:</p>
            
            <div style="border-left: 4px solid #1976d2; padding-left: 15px; margin: 20px 0;">
                <h3>{finding.title}</h3>
                <p><strong>Severity:</strong> <span style="color: {'red' if finding.severity == 'critical' else 'orange' if finding.severity == 'high' else 'black'}">{finding.severity.upper()}</span></p>
                <p><strong>Description:</strong> {finding.description}</p>
                <p><strong>Due Date:</strong> {finding.due_date.strftime('%Y-%m-%d') if finding.due_date else 'Not set'}</p>
            </div>
            
            <p><a href="{self.frontend_url}/findings/{finding.id}" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Finding</a></p>
            
            <p>Best regards,<br>QCA Team</p>
        </body>
        </html>
        """
        
        body_text = f"""
        New Finding Assigned
        
        Hi {assignee.full_name},
        
        A new finding has been assigned to you:
        
        Title: {finding.title}
        Severity: {finding.severity.upper()}
        Description: {finding.description}
        Due Date: {finding.due_date.strftime('%Y-%m-%d') if finding.due_date else 'Not set'}
        
        View finding: {self.frontend_url}/findings/{finding.id}
        
        Best regards,
        QCA Team
        """
        
        return self.send_email(assignee.email, subject, body_html, body_text)
    
    def notify_sla_breach(self, finding: Finding, assignee: User) -> Dict[str, any]:
        """Notify about SLA breach"""
        subject = f"[QCA] ⚠️ SLA Breach: {finding.title}"
        
        days_overdue = (datetime.utcnow() - finding.due_date).days if finding.due_date else 0
        
        body_html = f"""
        <html>
        <body>
            <h2 style="color: red;">⚠️ SLA Breach Alert</h2>
            <p>Hi {assignee.full_name},</p>
            <p>The following finding is <strong>{days_overdue} days overdue</strong>:</p>
            
            <div style="border-left: 4px solid red; padding-left: 15px; margin: 20px 0; background-color: #fff3f3;">
                <h3>{finding.title}</h3>
                <p><strong>Severity:</strong> {finding.severity.upper()}</p>
                <p><strong>Status:</strong> {finding.resolution_status}</p>
                <p><strong>Due Date:</strong> {finding.due_date.strftime('%Y-%m-%d')}</p>
                <p><strong>Days Overdue:</strong> {days_overdue}</p>
            </div>
            
            <p>Please take immediate action to resolve this finding.</p>
            
            <p><a href="{self.frontend_url}/findings/{finding.id}" style="background-color: red; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Finding</a></p>
            
            <p>Best regards,<br>QCA Team</p>
        </body>
        </html>
        """
        
        return self.send_email(assignee.email, subject, body_html)
    
    def notify_finding_resolved(self, finding: Finding, resolver: User, validator: User) -> Dict[str, any]:
        """Notify QA when finding is marked as resolved"""
        subject = f"[QCA] Finding Ready for QA: {finding.title}"
        
        body_html = f"""
        <html>
        <body>
            <h2>Finding Ready for QA Validation</h2>
            <p>Hi {validator.full_name},</p>
            <p>A finding has been marked as resolved and is ready for your validation:</p>
            
            <div style="border-left: 4px solid green; padding-left: 15px; margin: 20px 0;">
                <h3>{finding.title}</h3>
                <p><strong>Severity:</strong> {finding.severity.upper()}</p>
                <p><strong>Resolved By:</strong> {resolver.full_name}</p>
                <p><strong>Resolved At:</strong> {finding.resolved_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Resolution Notes:</strong> {finding.remediation_notes or 'None provided'}</p>
            </div>
            
            <p><a href="{self.frontend_url}/qa-review" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Review Finding</a></p>
            
            <p>Best regards,<br>QCA Team</p>
        </body>
        </html>
        """
        
        return self.send_email(validator.email, subject, body_html)
    
    def notify_assessment_completed(self, assessment: Assessment, stakeholders: List[User]) -> Dict[str, any]:
        """Notify stakeholders when assessment is completed"""
        subject = f"[QCA] Assessment Completed: {assessment.title}"
        
        results = []
        for user in stakeholders:
            body_html = f"""
            <html>
            <body>
                <h2>✅ Assessment Completed</h2>
                <p>Hi {user.full_name},</p>
                <p>The following assessment has been completed:</p>
                
                <div style="border-left: 4px solid green; padding-left: 15px; margin: 20px 0;">
                    <h3>{assessment.title}</h3>
                    <p><strong>Framework:</strong> {assessment.framework}</p>
                    <p><strong>Completed:</strong> {assessment.completed_at.strftime('%Y-%m-%d') if assessment.completed_at else 'N/A'}</p>
                    <p><strong>Progress:</strong> {assessment.progress_percentage}%</p>
                    <p><strong>Controls Tested:</strong> {assessment.controls_tested_count}</p>
                    <p><strong>Findings:</strong> {assessment.findings_count}</p>
                </div>
                
                <p><a href="{self.frontend_url}/assessments/{assessment.id}" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Assessment</a></p>
                
                <p>Best regards,<br>QCA Team</p>
            </body>
            </html>
            """
            
            result = self.send_email(user.email, subject, body_html)
            results.append({"user": user.email, "result": result})
        
        return {
            "status": "success",
            "notifications_sent": len(results),
            "results": results
        }
    
    def send_daily_digest(self, user: User, summary: Dict) -> Dict[str, any]:
        """Send daily digest of pending items"""
        subject = f"[QCA] Daily Digest - {datetime.now().strftime('%Y-%m-%d')}"
        
        body_html = f"""
        <html>
        <body>
            <h2>Your Daily QCA Digest</h2>
            <p>Hi {user.full_name},</p>
            <p>Here's your summary for today:</p>
            
            <div style="margin: 20px 0;">
                <h3>Findings</h3>
                <ul>
                    <li><strong>Open:</strong> {summary.get('open_findings', 0)}</li>
                    <li><strong>In Progress:</strong> {summary.get('in_progress_findings', 0)}</li>
                    <li><strong>Overdue:</strong> <span style="color: red;">{summary.get('overdue_findings', 0)}</span></li>
                    <li><strong>Pending QA:</strong> {summary.get('pending_qa', 0)}</li>
                </ul>
                
                <h3>Assessments</h3>
                <ul>
                    <li><strong>In Progress:</strong> {summary.get('in_progress_assessments', 0)}</li>
                    <li><strong>Due Soon:</strong> {summary.get('due_soon_assessments', 0)}</li>
                </ul>
            </div>
            
            <p><a href="{self.frontend_url}/dashboard" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Go to Dashboard</a></p>
            
            <p>Best regards,<br>QCA Team</p>
        </body>
        </html>
        """
        
        return self.send_email(user.email, subject, body_html)


# Global instance
notification_service = NotificationService()
