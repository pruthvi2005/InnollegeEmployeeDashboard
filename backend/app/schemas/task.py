from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.task import TaskPriority, AssignmentStatus


class TaskCreate(BaseModel):
    """Payload to create a task and assign to employees."""
    title: str = Field(..., min_length=2, max_length=500)
    description: Optional[str] = None
    project_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.medium
    start_date: Optional[date] = None
    deadline: Optional[datetime] = None
    instructions: Optional[str] = None
    assigned_employee_ids: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Payload for updating task core metadata (founder only)."""
    title: Optional[str] = Field(None, min_length=2, max_length=500)
    description: Optional[str] = None
    project_id: Optional[str] = None
    priority: Optional[TaskPriority] = None
    start_date: Optional[date] = None
    deadline: Optional[datetime] = None
    instructions: Optional[str] = None


class TaskAssignmentUpdate(BaseModel):
    """Payload for an employee updating progress on their assignment."""
    status: Optional[AssignmentStatus] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    note: Optional[str] = None


class TaskCommentCreate(BaseModel):
    """Payload for adding a collaboration comment to a task."""
    content: str = Field(..., min_length=1)


class TaskCommentResponse(BaseModel):
    """Response representation of a task comment."""
    id: str
    task_id: str
    employee_id: str
    employee_name: str
    content: str
    is_founder_comment: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSubmitRequest(BaseModel):
    """Payload when employee submits their completed assignment."""
    note: Optional[str] = None


class AssignmentResponse(BaseModel):
    """Assignment details for an individual employee on a task."""
    id: str
    employee_id: str
    employee_name: str
    status: str
    progress_percent: int
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """Full task response model with assigned members and metadata."""
    id: str
    title: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    priority: str
    start_date: Optional[date] = None
    deadline: Optional[datetime] = None
    instructions: Optional[str] = None
    assignments: List[AssignmentResponse] = Field(default_factory=list)
    comment_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
