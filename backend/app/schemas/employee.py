from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class EmployeeCreate(BaseModel):
    """Payload for creating a new employee."""
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=128)
    department_id: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None


class EmployeeUpdate(BaseModel):
    """Payload for updating employee details."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    profile_photo_url: Optional[str] = None


class EmployeeStatusUpdate(BaseModel):
    """Payload for activating or deactivating an employee account."""
    is_active: bool


class EmployeePasswordResetRequest(BaseModel):
    """New password chosen by a founder for an employee account."""
    new_password: str = Field(..., min_length=8, max_length=128)


class EmployeeResponse(BaseModel):
    """Employee record response representation."""
    id: str
    user_id: str
    employee_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    profile_photo_url: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeListResponse(BaseModel):
    """Paginated list of employees."""
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
