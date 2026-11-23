from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import pytz
from pydantic import BaseModel, ConfigDict, field_validator


def format_to_ist(dt: Optional[datetime]) -> Optional[str]:
    """Convert UTC datetime to Asia/Kolkata formatted string."""
    if dt is None:
        return None
    ist_tz = pytz.timezone("Asia/Kolkata")
    if dt.tzinfo is None:
        # Assume stored as naive UTC
        utc_dt = pytz.utc.localize(dt)
    else:
        utc_dt = dt.astimezone(pytz.utc)
    ist_dt = utc_dt.astimezone(ist_tz)
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")


class CheckInRequest(BaseModel):
    """Payload for employee check-in."""
    notes: Optional[str] = None


class CheckOutRequest(BaseModel):
    """Payload for employee check-out."""
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    """Attendance record representation with timestamps formatted in IST."""
    id: str
    employee_id: str
    employee_name: str
    work_date: date
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    working_hours: Optional[Decimal] = None
    status: str
    is_late: bool

    model_config = ConfigDict(from_attributes=True)


class AttendanceSummary(BaseModel):
    """Aggregated attendance metrics."""
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    leave_days: int
    attendance_rate: float  # Percentage (0 - 100)
