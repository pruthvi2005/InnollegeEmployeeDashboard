from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class LeaveRequestCreate(BaseModel):
    """Payload to submit a leave request."""
    leave_type_id: str
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=2)


class LeaveDecisionRequest(BaseModel):
    """Payload for founder approving or rejecting a leave request."""
    action: Literal["approved", "rejected"]
    comment: Optional[str] = None


class LeaveTypeResponse(BaseModel):
    """Leave type categorization representation."""
    id: str
    name: str
    description: Optional[str] = None
    days_per_year: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestResponse(BaseModel):
    """Leave request response representation."""
    id: str
    employee_id: str
    employee_name: str
    leave_type_name: str
    start_date: date
    end_date: date
    total_days: int
    reason: str
    status: str
    decision_comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
