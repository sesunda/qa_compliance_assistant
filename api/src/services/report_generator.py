"""
Report Generator Service - Generate PDF reports for assessments
Uses ReportLab for PDF generation with charts and tables
"""
import io
import os
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from api.src.models import Assessment, Finding, Control, AssessmentControl
from api.src.services.assessment_service import AssessmentService
from api.src.services.compliance_service import ComplianceService


class ReportGenerator:
    """Service for generating PDF reports"""
    
    def __init__(self, storage_path: str = "/app/storage/reports"):
        """Initialize report generator"""
        self.storage_path = storage_path
        self.enabled = REPORTLAB_AVAILABLE
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
    
    def generate_assessment_report(
        self,
        assessment: Assessment,
        db: Session,
        include_findings: bool = True,
        include_controls: bool = True
    ) -> Dict[str, any]:
        """
        Generate comprehensive assessment report
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "PDF generation not available (reportlab not installed)"
            }
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"assessment_{assessment.id}_{timestamp}.pdf"
            filepath = os.path.join(self.storage_path, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1976d2'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph(f"Assessment Report: {assessment.title}", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            
            metrics = AssessmentService.get_assessment_metrics(assessment, db)
            compliance_score = ComplianceService.calculate_compliance_score(assessment, db)
            
            summary_data = [
                ['Assessment ID', str(assessment.id)],
                ['Status', assessment.status.upper()],
                ['Framework', assessment.framework or 'N/A'],
                ['Progress', f"{assessment.progress_percentage}%"],
                ['Compliance Score', f"{compliance_score['score']}%"],
                ['Created', assessment.created_at.strftime("%Y-%m-%d")],
                ['Analyst', assessment.analyst.full_name if assessment.analyst else 'Unassigned']
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Controls Summary
            if include_controls:
                story.append(Paragraph("Controls Summary", styles['Heading2']))
                
                controls_data = [
                    ['Metric', 'Count', 'Percentage'],
                    ['Total Controls', str(metrics['controls']['total']), '100%'],
                    ['Tested', str(metrics['controls']['tested']), 
                     f"{(metrics['controls']['tested']/metrics['controls']['total']*100) if metrics['controls']['total'] > 0 else 0:.1f}%"],
                    ['Passed', str(metrics['controls']['passed']), 
                     f"{(metrics['controls']['passed']/metrics['controls']['total']*100) if metrics['controls']['total'] > 0 else 0:.1f}%"],
                    ['Failed', str(metrics['controls']['failed']), 
                     f"{(metrics['controls']['failed']/metrics['controls']['total']*100) if metrics['controls']['total'] > 0 else 0:.1f}%"],
                ]
                
                controls_table = Table(controls_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                controls_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(controls_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Findings Summary
            if include_findings:
                story.append(Paragraph("Findings Summary", styles['Heading2']))
                
                severity_colors = {
                    'critical': colors.red,
                    'high': colors.orange,
                    'medium': colors.yellow,
                    'low': colors.lightblue,
                    'info': colors.lightgrey
                }
                
                findings_data = [['Severity', 'Count', 'Resolved', 'Open']]
                
                for severity in ['critical', 'high', 'medium', 'low', 'info']:
                    total = metrics['findings']['by_severity'].get(severity, 0)
                    resolved = len([
                        f for f in db.query(Finding).filter(
                            Finding.assessment_id == assessment.id,
                            Finding.severity == severity,
                            Finding.resolution_status.in_(['resolved', 'accepted_risk'])
                        ).all()
                    ])
                    open_count = total - resolved
                    
                    findings_data.append([
                        severity.upper(),
                        str(total),
                        str(resolved),
                        str(open_count)
                    ])
                
                findings_table = Table(findings_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                findings_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(findings_table)
                story.append(Spacer(1, 0.3*inch))
                
                # Detailed findings list
                story.append(PageBreak())
                story.append(Paragraph("Detailed Findings", styles['Heading2']))
                
                findings = db.query(Finding).filter(
                    Finding.assessment_id == assessment.id
                ).order_by(Finding.severity, Finding.created_at).all()
                
                for i, finding in enumerate(findings, 1):
                    story.append(Paragraph(f"{i}. [{finding.severity.upper()}] {finding.title}", styles['Heading3']))
                    story.append(Paragraph(f"<b>Description:</b> {finding.description}", styles['Normal']))
                    story.append(Paragraph(f"<b>Status:</b> {finding.resolution_status}", styles['Normal']))
                    story.append(Paragraph(f"<b>Remediation:</b> {finding.remediation or 'N/A'}", styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))
            
            # Compliance Analysis
            story.append(PageBreak())
            story.append(Paragraph("Compliance Analysis", styles['Heading2']))
            
            story.append(Paragraph(f"<b>Compliance Status:</b> {compliance_score['status'].replace('_', ' ').title()}", styles['Normal']))
            story.append(Paragraph(f"<b>Overall Score:</b> {compliance_score['score']}%", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            breakdown_data = [
                ['Category', 'Score'],
                ['Coverage', f"{compliance_score['breakdown']['coverage']:.1f}%"],
                ['Effectiveness', f"{compliance_score['breakdown']['effectiveness']:.1f}%"],
                ['Findings Resolution', f"{compliance_score['breakdown']['findings_resolution']:.1f}%"],
            ]
            
            breakdown_table = Table(breakdown_data, colWidths=[3*inch, 2*inch])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(breakdown_table)
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Quantique Compliance Assistant",
                footer_style
            ))
            
            # Build PDF
            doc.build(story)
            
            return {
                "status": "success",
                "filename": filename,
                "filepath": filepath,
                "size_bytes": os.path.getsize(filepath),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_executive_summary(
        self,
        assessment: Assessment,
        db: Session
    ) -> Dict[str, any]:
        """Generate executive summary (shorter report)"""
        # Similar to full report but condensed
        return self.generate_assessment_report(
            assessment,
            db,
            include_findings=False,
            include_controls=True
        )


# Global instance
report_generator = ReportGenerator()
