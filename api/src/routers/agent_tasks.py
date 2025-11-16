"""API endpoints for agent tasks management"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import datetime
from api.src.utils.datetime_utils import now_sgt

from api.src.database import get_db
from api.src.models import AgentTask, User
from api.src.agent_schemas import (
    AgentTaskCreate,
    AgentTaskUpdate,
    AgentTaskResponse,
    AgentTaskListResponse,
    TaskStats,
    TaskStatus
)
from api.src.auth import get_current_user


router = APIRouter(prefix="/agent-tasks", tags=["agent-tasks"])


@router.post("/", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
def create_agent_task(
    task_data: AgentTaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new agent task.
    
    The task will be queued for execution by the background worker.
    """
    new_task = AgentTask(
        task_type=task_data.task_type,
        title=task_data.title,
        description=task_data.description,
        payload=task_data.payload,
        created_by=current_user["id"],
        status=TaskStatus.PENDING.value,
        progress=0
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return new_task


@router.get("/", response_model=AgentTaskListResponse)
def list_agent_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List agent tasks with pagination and filtering.
    
    Regular users see only their own tasks.
    Admins see all tasks.
    """
    query = db.query(AgentTask)
    
    # Filter by user unless admin
    is_admin = current_user.get("role") in ['super_admin', 'admin']
    if not is_admin:
        query = query.filter(AgentTask.created_by == current_user["id"])
    
    # Apply filters
    if status:
        query = query.filter(AgentTask.status == status)
    if task_type:
        query = query.filter(AgentTask.task_type == task_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    tasks = query.order_by(AgentTask.created_at.desc()).offset(offset).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return AgentTaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/stats", response_model=TaskStats)
def get_task_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get task statistics.
    
    Regular users see stats for their own tasks.
    Admins see stats for all tasks.
    """
    query = db.query(AgentTask)
    
    # Filter by user unless admin
    is_admin = current_user.get("role") in ['super_admin', 'admin']
    if not is_admin:
        query = query.filter(AgentTask.created_by == current_user["id"])
    
    total = query.count()
    pending = query.filter(AgentTask.status == TaskStatus.PENDING.value).count()
    running = query.filter(AgentTask.status == TaskStatus.RUNNING.value).count()
    completed = query.filter(AgentTask.status == TaskStatus.COMPLETED.value).count()
    failed = query.filter(AgentTask.status == TaskStatus.FAILED.value).count()
    cancelled = query.filter(AgentTask.status == TaskStatus.CANCELLED.value).count()
    
    return TaskStats(
        total=total,
        pending=pending,
        running=running,
        completed=completed,
        failed=failed,
        cancelled=cancelled
    )


@router.get("/{task_id}", response_model=AgentTaskResponse)
def get_agent_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific agent task.
    
    Regular users can only access their own tasks.
    Admins can access any task.
    """
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Check permission
    is_admin = current_user.get("role") in ['super_admin', 'admin']
    if not is_admin and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own tasks"
        )
    
    return task


@router.put("/{task_id}/cancel", response_model=AgentTaskResponse)
def cancel_agent_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a pending or running task.
    
    Users can cancel their own tasks.
    Admins can cancel any task.
    """
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Check permission
    is_admin = current_user.get("role") in ['super_admin', 'admin']
    if not is_admin and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own tasks"
        )
    
    # Can only cancel pending or running tasks
    if task.status not in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status: {task.status}"
        )
    
    task.status = TaskStatus.CANCELLED.value
    task.updated_at = now_sgt()
    task.completed_at = now_sgt()
    
    db.commit()
    db.refresh(task)
    
    return task


@router.patch("/{task_id}", response_model=AgentTaskResponse)
def update_agent_task(
    task_id: int,
    task_update: AgentTaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a task's status, progress, result, or error message.
    
    This is typically called by the task worker system to update task progress.
    Users can update their own tasks.
    Admins can update any task.
    """
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Check permission
    is_admin = current_user.get("role") in ['super_admin', 'admin']
    if not is_admin and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tasks"
        )
    
    # Update fields if provided
    if task_update.status is not None:
        task.status = task_update.status
        if task_update.status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
            task.completed_at = now_sgt()
    
    if task_update.progress is not None:
        task.progress = task_update.progress
    
    if task_update.result is not None:
        task.result = task_update.result
    
    if task_update.error_message is not None:
        task.error_message = task_update.error_message
    
    task.updated_at = now_sgt()
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a task.
    
    Users can delete their own tasks.
    Admins can delete any task.
    """
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Check permission
    is_admin = current_user.get("role") in ['super_admin', 'admin']
    if not is_admin and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tasks"
        )
    
    db.delete(task)
    db.commit()
    
    return None
