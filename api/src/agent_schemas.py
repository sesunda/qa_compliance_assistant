"""Pydantic schemas for agent tasks"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Predefined task types"""
    TEST = "test"
    FETCH_EVIDENCE = "fetch_evidence"
    GENERATE_REPORT = "generate_report"
    ANALYZE_COMPLIANCE = "analyze_compliance"
    MAP_CONTROLS = "map_controls"
    CUSTOM = "custom"


class AgentTaskCreate(BaseModel):
    """Schema for creating a new agent task"""
    task_type: str = Field(..., description="Type of task to execute")
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    payload: Optional[Dict[str, Any]] = Field(None, description="Task input parameters")


class AgentTaskUpdate(BaseModel):
    """Schema for updating agent task (admin only)"""
    status: Optional[TaskStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AgentTaskResponse(BaseModel):
    """Schema for agent task response"""
    id: int
    task_type: str
    status: str
    title: str
    description: Optional[str]
    created_by: int
    payload: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    progress: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentTaskListResponse(BaseModel):
    """Schema for paginated task list response"""
    tasks: List[AgentTaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskStats(BaseModel):
    """Task statistics"""
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
