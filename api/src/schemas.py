from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List, Dict, Any


# Agency Schemas
class AgencyBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    active: bool = True


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    active: Optional[bool] = None


class Agency(AgencyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = "compliance_assessment"
    status: str = "active"
    start_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None


class Project(ProjectBase):
    id: int
    agency_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Control Schemas
class ControlBase(BaseModel):
    name: str
    description: Optional[str] = None
    control_type: Optional[str] = None
    status: str = "pending"


class ControlCreate(ControlBase):
    project_id: int


class ControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    control_type: Optional[str] = None
    status: Optional[str] = None


class Control(ControlBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Evidence Schemas
class EvidenceBase(BaseModel):
    title: str
    description: Optional[str] = None
    evidence_type: Optional[str] = None
    verified: bool = False


class EvidenceCreate(EvidenceBase):
    control_id: int


class EvidenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    evidence_type: Optional[str] = None
    verified: Optional[bool] = None
    verification_status: Optional[str] = None
    review_comments: Optional[str] = None


class Evidence(EvidenceBase):
    id: int
    control_id: int
    agency_id: int
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    storage_backend: Optional[str] = None
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    verification_status: str = "pending"
    submitted_by: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Report Schemas
class ReportBase(BaseModel):
    title: str
    content: Optional[str] = None
    report_type: Optional[str] = None


class ReportCreate(ReportBase):
    project_id: int


class Report(ReportBase):
    id: int
    project_id: int
    generated_at: datetime
    file_path: Optional[str] = None
    
    class Config:
        from_attributes = True


# Control Testing Schemas
class ControlTestCreate(BaseModel):
    test_result: str  # passed, failed, not_applicable
    assessment_score: Optional[int] = None
    test_notes: Optional[str] = None


class ControlReviewCreate(BaseModel):
    review_status: str  # approved, needs_improvement, rejected
    review_notes: Optional[str] = None


class ControlTestProcedureUpdate(BaseModel):
    test_procedure: Optional[str] = None
    testing_frequency: Optional[str] = None  # daily, weekly, monthly, quarterly, annual


# Control Catalog Schemas
class ControlCatalogCreate(BaseModel):
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    family: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
    proposed_domain_code: Optional[str] = None
    proposed_confidence: Optional[float] = None
    mapping_rationale: Optional[str] = None


class ControlCatalog(BaseModel):
    id: int
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    family: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
    proposed_domain_id: Optional[int] = None
    proposed_confidence: Optional[str] = None
    mapping_rationale: Optional[str] = None
    approved_domain_id: Optional[int] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Conversation Session Schemas
class ConversationMessage(BaseModel):
    """Single message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    task_id: Optional[int] = None  # Link to created task if any
    tool_calls: Optional[List[Dict[str, Any]]] = None  # For LLM tool executions


class ConversationSessionCreate(BaseModel):
    """Create new conversation session"""
    title: Optional[str] = None


class ConversationSessionUpdate(BaseModel):
    """Update conversation session"""
    title: Optional[str] = None
    active: Optional[bool] = None


class ConversationSession(BaseModel):
    """Full conversation session"""
    id: int
    session_id: str
    user_id: int
    title: Optional[str]
    messages: List[ConversationMessage]
    context: Optional[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    active: bool
    
    class Config:
        from_attributes = True


class ConversationSessionSummary(BaseModel):
    """Summary of conversation session (for list view)"""
    id: int
    session_id: str
    title: Optional[str]
    message_count: int
    created_at: datetime
    last_activity: datetime
    active: bool
    
    class Config:
        from_attributes = True


# Assessment Schemas
class AssessmentCreate(BaseModel):
    title: str
    assessment_type: str  # vapt, infra_pt, compliance_audit
    framework: Optional[str] = None  # ISO27001, NIST, PCI-DSS, etc.
    scope: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigned_to: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    scope: Optional[str] = None
    status: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AssessmentAssignment(BaseModel):
    assigned_to: int


class AssessmentProgressUpdate(BaseModel):
    progress_percentage: int


class AssessmentListResponse(BaseModel):
    id: int
    title: str
    assessment_type: str
    framework: Optional[str] = None
    status: str
    progress_percentage: int
    assigned_to: Optional[str] = None
    findings_count: int
    controls_tested_count: int
    target_completion_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    id: int
    agency_id: int
    title: str
    assessment_type: str
    framework: Optional[str] = None
    scope: Optional[str] = None
    status: str
    progress_percentage: int
    assigned_to: Optional[int] = None
    assigned_to_username: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    assessment_period_start: Optional[datetime] = None
    assessment_period_end: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    findings_count: int
    findings_resolved: int
    findings_by_severity: Dict[str, int]
    controls_tested_count: int
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AssessmentSummary(BaseModel):
    id: int
    title: str
    assessment_type: str
    status: str
    findings_count: int
    
    class Config:
        from_attributes = True


# Finding Schemas
class FindingCreate(BaseModel):
    assessment_id: int
    control_id: Optional[int] = None
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    priority: Optional[str] = "medium"
    risk_rating: Optional[str] = None
    affected_systems: Optional[str] = None
    remediation_recommendation: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class FindingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    affected_systems: Optional[str] = None
    remediation_recommendation: Optional[str] = None
    due_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class FindingAssignment(BaseModel):
    assigned_to: int


class FindingResolution(BaseModel):
    remediation_notes: str


class FindingValidation(BaseModel):
    approved: bool
    validation_notes: Optional[str] = None


class FindingListResponse(BaseModel):
    id: int
    title: str
    severity: str
    priority: str
    resolution_status: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    assessment_title: str
    created_at: datetime
    false_positive: bool
    
    class Config:
        from_attributes = True


class FindingResponse(BaseModel):
    id: int
    assessment_id: int
    control_id: Optional[int] = None
    title: str
    description: str
    severity: str
    priority: str
    resolution_status: str
    assigned_to: Optional[int] = None
    assigned_to_username: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_by_username: Optional[str] = None
    validated_by: Optional[int] = None
    validated_by_username: Optional[str] = None
    risk_rating: Optional[str] = None
    affected_systems: Optional[str] = None
    remediation_recommendation: Optional[str] = None
    remediation_notes: Optional[str] = None
    false_positive: bool
    due_date: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    assessment_title: str
    control_name: Optional[str] = None
    comments_count: int
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# Finding Comment Schemas
class FindingCommentCreate(BaseModel):
    comment_type: str  # general, resolution, validation, false_positive
    comment_text: str


class FindingCommentResponse(BaseModel):
    id: int
    finding_id: int
    user_id: int
    username: str
    comment_type: str
    comment_text: str
    created_at: datetime
    
    class Config:
        from_attributes = True

