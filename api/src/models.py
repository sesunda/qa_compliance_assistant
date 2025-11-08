from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from api.src.database import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # admin, auditor, analyst, viewer
    description = Column(Text)
    permissions = Column(JSON)  # Store permissions as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agency = relationship("Agency", back_populates="users")
    role = relationship("UserRole", back_populates="users")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(500))


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(100), nullable=True)
    description = Column(Text)
    contact_email = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="agency")
    projects = relationship("Project", back_populates="agency")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String(255), nullable=False)
    assessment_type = Column(String(50))  # vapt, infra_pt, compliance_audit
    performed_by = Column(String(255))
    scope = Column(Text)
    metadata_json = Column('metadata', JSON)
    status = Column(String(50), default="open", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New workflow fields
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)
    target_completion_date = Column(DateTime, nullable=True)
    framework = Column(String(100), nullable=True, index=True)  # NIST, ISO27001, SOC2, FISMA
    assessment_period_start = Column(Date, nullable=True)
    assessment_period_end = Column(Date, nullable=True)
    findings_count = Column(Integer, default=0, nullable=False)
    controls_tested_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    agency = relationship("Agency", foreign_keys=[agency_id])
    analyst = relationship("User", foreign_keys=[assigned_to])
    controls = relationship("AssessmentControl", back_populates="assessment", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    control_id = Column(Integer, ForeignKey("controls.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(String(50))  # critical/high/medium/low/info
    cve = Column(String(100))
    cvss = Column(String(20))
    remediation = Column(Text)
    evidence = Column(JSON)  # list of evidence ids or metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New workflow fields
    resolution_status = Column(String(50), default="open", nullable=False, index=True)
    # Values: open, in_progress, resolved, accepted_risk, false_positive
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)
    false_positive = Column(Boolean, default=False, nullable=False)
    validated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    due_date = Column(DateTime, nullable=True, index=True)
    priority = Column(String(20), nullable=True, index=True)  # critical, high, medium, low
    remediation_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    assessment = relationship("Assessment", foreign_keys=[assessment_id])
    control = relationship("Control", foreign_keys=[control_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    validator = relationship("User", foreign_keys=[validated_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    resolution_evidence = relationship("Evidence", foreign_keys=[resolution_evidence_id])
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    finding = relationship("Finding", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])
