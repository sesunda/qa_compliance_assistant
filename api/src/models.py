from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
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
    
    project = relationship("Project", back_populates="controls")
    evidence_items = relationship("Evidence", back_populates="control", cascade="all, delete-orphan")


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    control = relationship("Control", back_populates="evidence_items")


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
    assessment_type = Column(String(50))  # vapt, infra_pt, other
    performed_by = Column(String(255))
    scope = Column(Text)
    # 'metadata' is a reserved attribute name on Declarative base; store in DB column 'metadata'
    # but map to attribute name 'metadata_json' to avoid conflicts with SQLAlchemy internals.
    metadata_json = Column('metadata', JSON)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)


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
