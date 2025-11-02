from pydantic import BaseModel, EmailStr
from datetime import datetime
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
    status: str = "active"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class Project(ProjectBase):
    id: int
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
