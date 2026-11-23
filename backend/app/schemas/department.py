from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DepartmentCreate(BaseModel):
    """Payload to create a new department."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    """Payload to update an existing department."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    """Department model response representation."""
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    employee_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
