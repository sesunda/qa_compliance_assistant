from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Date, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from api.src.database import Base
from api.src.utils.datetime_utils import now_sgt


class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # admin, auditor, analyst, viewer
    description = Column(Text)
    permissions = Column(JSON)  # Store permissions as JSON
    created_at = Column(DateTime, default=now_sgt)
    
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=now_sgt)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt)
    
    agency = relationship("Agency", back_populates="users")
    role = relationship("UserRole", back_populates="users")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_type = Column(String(100), default="compliance_assessment")
    status = Column(String(50), default="active")
    start_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=now_sgt)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt)
    
    controls = relationship("Control", back_populates="project", cascade="all, delete-orphan")
    agency = relationship("Agency", back_populates="projects")


class Control(Base):
    __tablename__ = "controls"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    control_type = Column(String(100))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=now_sgt)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt)
    
    # New workflow fields
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_status = Column(String(50), default="pending", nullable=False, index=True)
    # Values: pending, in_review, passed, failed, not_applicable
    assessment_score = Column(Integer, nullable=True)  # 0-100
    test_procedure = Column(Text, nullable=True)
    test_results = Column(Text, nullable=True)
    testing_frequency = Column(String(50), nullable=True)  # annual, quarterly, monthly
    last_tested_at = Column(DateTime, nullable=True)
    next_test_due = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    project = relationship("Project", back_populates="controls")
    evidence_items = relationship("Evidence", back_populates="control", cascade="all, delete-orphan")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    assessment_links = relationship("AssessmentControl", back_populates="control")


class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    control_id = Column(Integer, ForeignKey("controls.id"), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    evidence_type = Column(String(100))
    verified = Column(Boolean, default=False)
    
    # File metadata (added in migration 004)
    original_filename = Column(String(255))
    mime_type = Column(String(100))
    file_size = Column(Integer)
    checksum = Column(String(64))  # SHA-256 hash
    storage_backend = Column(String(50), default="local")
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime)
    
    # Maker-Checker workflow fields (added in migration 007)
    verification_status = Column(String(50), default="pending", nullable=False)
    # Values: 'pending', 'under_review', 'approved', 'rejected'
    submitted_by = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_comments = Column(Text)
    
    created_at = Column(DateTime, default=now_sgt)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt)
    
    control = relationship("Control", back_populates="evidence_items")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    submitter = relationship("User", foreign_keys=[submitted_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    report_type = Column(String(100))
    generated_at = Column(DateTime, default=now_sgt)
    file_path = Column(String(500))


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(100), nullable=True)
    description = Column(Text)
    contact_email = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_sgt)
    
    users = relationship("User", back_populates="agency")
    projects = relationship("Project", back_populates="agency")


class Assessment(Base):
    """Comprehensive Assessment model for formal compliance evaluations"""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core Info
    name = Column(String(255), nullable=False)
    assessment_type = Column(String(100), nullable=False, index=True)
    # Values: compliance, risk, security_audit, penetration_test, gap_analysis
    framework = Column(String(100), nullable=False)
    # Values: IM8, ISO27001, NIST, SOC2, FISMA
    
    # Scope
    scope_description = Column(Text, nullable=True)
    included_controls = Column(JSON, nullable=True)  # Array of control IDs
    excluded_areas = Column(Text, nullable=True)
    
    # Schedule
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True, index=True)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    
    # Team
    lead_assessor_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    team_members = Column(JSON, nullable=True)  # Array of user IDs
    
    # Status
    status = Column(String(50), nullable=False, default='not_started', index=True)
    # Values: not_started, planning, fieldwork, review, final, archived
    completion_percentage = Column(Float, nullable=True, default=0)
    
    # Results
    overall_compliance_score = Column(Float, nullable=True)
    findings_count_critical = Column(Integer, nullable=True, default=0)
    findings_count_high = Column(Integer, nullable=True, default=0)
    findings_count_medium = Column(Integer, nullable=True, default=0)
    findings_count_low = Column(Integer, nullable=True, default=0)
    
    # Deliverables
    final_report_file_path = Column(String(500), nullable=True)
    executive_summary = Column(Text, nullable=True)
    
    # Approval
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Audit fields
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=now_sgt, nullable=False)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt, nullable=False)
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    agency = relationship("Agency", foreign_keys=[agency_id])
    lead_assessor = relationship("User", foreign_keys=[lead_assessor_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    controls = relationship("AssessmentControl", back_populates="assessment", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan")


class Finding(Base):
    """Comprehensive Finding model for vulnerabilities and compliance gaps"""
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    control_id = Column(Integer, ForeignKey("controls.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Core Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, index=True)
    # Values: critical, high, medium, low, info
    cvss_score = Column(Float, nullable=True)  # 0.0-10.0
    category = Column(String(100), nullable=True)
    # Values: injection, broken_auth, sensitive_data, xxe, access_control, security_misconfiguration, xss, insecure_deserialization, logging, ssrf
    
    # Asset Info
    affected_asset = Column(String(255), nullable=True)
    affected_url = Column(String(500), nullable=True)
    affected_component = Column(String(255), nullable=True)
    
    # Status Tracking
    status = Column(String(50), nullable=False, default='open', index=True)
    # Values: open, in_progress, resolved, accepted_risk, false_positive
    discovery_date = Column(Date, nullable=False)
    
    # Remediation
    remediation_recommendation = Column(Text, nullable=True)
    remediation_priority = Column(String(50), nullable=True)
    # Values: immediate, urgent, planned
    target_remediation_date = Column(Date, nullable=True, index=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actual_remediation_date = Column(Date, nullable=True)
    
    # Evidence/Proof
    evidence_file_paths = Column(JSON, nullable=True)  # Array of file paths for POC/screenshots
    reproduction_steps = Column(Text, nullable=True)
    
    # Verification
    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Audit fields
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=now_sgt, nullable=False)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt, nullable=False)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="findings")
    project = relationship("Project", foreign_keys=[project_id])
    agency = relationship("Agency", foreign_keys=[agency_id])
    control = relationship("Control", foreign_keys=[control_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    comments = relationship("FindingComment", back_populates="finding", cascade="all, delete-orphan")


class IM8DomainArea(Base):
    __tablename__ = "im8_domain_areas"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    framework_mappings = Column(JSON)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_area_id = Column(Integer, ForeignKey("im8_domain_areas.id"), nullable=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50))
    endpoint = Column(String(500))
    active = Column(Boolean, default=True)


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    name = Column(String(255), nullable=False)
    tool_type = Column(String(100))
    endpoint = Column(String(500))
    config = Column(JSON)


class ControlCatalog(Base):
    __tablename__ = "control_catalog"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), nullable=True)
    title = Column(String(512), nullable=False)
    description = Column(Text)
    family = Column(String(255))
    raw_json = Column(JSON)
    proposed_domain_id = Column(Integer, ForeignKey("im8_domain_areas.id"), nullable=True)
    proposed_confidence = Column(String(20), nullable=True)
    mapping_rationale = Column(Text)
    approved_domain_id = Column(Integer, ForeignKey("im8_domain_areas.id"), nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=now_sgt)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt)


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=now_sgt)
    updated_at = Column(DateTime, default=now_sgt, onupdate=now_sgt)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    creator = relationship("User", foreign_keys=[created_by])


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    messages = Column(JSON, nullable=False, default=list)  # List of message dicts
    context = Column(JSON, nullable=True)  # Store extracted entities, control IDs, etc
    created_at = Column(DateTime, default=now_sgt)
    last_activity = Column(DateTime, default=now_sgt, onupdate=now_sgt, index=True)
    active = Column(Boolean, default=True, index=True)
    
    user = relationship("User", foreign_keys=[user_id])


class AssessmentControl(Base):
    """Junction table for Assessment-Control many-to-many relationship"""
    __tablename__ = "assessment_controls"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    control_id = Column(Integer, ForeignKey("controls.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_for_testing = Column(Boolean, default=True, nullable=False)
    testing_status = Column(String(50), default="pending", nullable=False, index=True)
    # Values: pending, in_progress, completed, passed, failed
    testing_priority = Column(Integer, nullable=True)  # 1=highest priority
    created_at = Column(DateTime, default=now_sgt, nullable=False)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="controls")
    control = relationship("Control", back_populates="assessment_links")


class FindingComment(Base):
    """Comments and updates on findings for tracking discussion"""
    __tablename__ = "finding_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50), nullable=True)  # update, resolution, validation, general
    created_at = Column(DateTime, default=now_sgt, nullable=False)
    
    # Relationships
    finding = relationship("Finding", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])
