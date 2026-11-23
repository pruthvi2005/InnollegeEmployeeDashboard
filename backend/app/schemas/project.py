from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    """Payload to create a new project."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.planning
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    """Payload to update an existing project."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectMemberAdd(BaseModel):
    """Payload to assign an employee to a project."""
    employee_id: str
    role: Optional[str] = None


class ProjectMemberResponse(BaseModel):
    """Project member response representation."""
    id: str
    employee_id: str
    employee_name: str
    role: Optional[str] = None
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """Project response representation."""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    member_count: int = 0
    task_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
