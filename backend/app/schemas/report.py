from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.report import ReportStatus


class ReportTaskItem(BaseModel):
    """Line item representing work on a task within daily report."""
    task_id: Optional[str] = None
    task_description: str = Field(..., min_length=1, max_length=1000)
    time_spent_hours: Optional[Decimal] = Field(None, ge=0, le=24)
    notes: Optional[str] = None


class DailyReportCreate(BaseModel):
    """Payload to create a daily work report."""
    report_date: date
    completed_work: Optional[str] = None
    pending_work: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    total_hours_worked: Optional[Decimal] = Field(None, ge=0, le=24)
    task_items: List[ReportTaskItem] = Field(default_factory=list)
    status: ReportStatus = ReportStatus.draft


class DailyReportUpdate(BaseModel):
    """Payload to update an existing daily report."""
    completed_work: Optional[str] = None
    pending_work: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    total_hours_worked: Optional[Decimal] = Field(None, ge=0, le=24)
    task_items: Optional[List[ReportTaskItem]] = None
    status: Optional[ReportStatus] = None


class ReportReviewRequest(BaseModel):
    """Founder review payload for a submitted report."""
    founder_feedback: Optional[str] = None
    status: ReportStatus = ReportStatus.reviewed


class DailyReportResponse(BaseModel):
    """Daily report response representation."""
    id: str
    employee_id: str
    employee_name: str
    report_date: date
    completed_work: Optional[str] = None
    pending_work: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    total_hours_worked: Optional[Decimal] = None
    task_items: List[ReportTaskItem] = Field(default_factory=list)
    status: str
    founder_feedback: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
