from typing import List, Optional, Dict
from pydantic import BaseModel


class OverviewAttendancePoint(BaseModel):
    """Single day in the founder's weekly attendance chart."""
    date: str
    present: int
    absent: int
    leave: int


class OverviewStats(BaseModel):
    """High-level platform executive overview statistics."""
    total_employees: int
    present_today: int
    absent_today: int
    on_leave_today: int
    active_projects: int
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    pending_reports: int
    pending_leaves: int
    attendance_chart: List[OverviewAttendancePoint] = []


class AttendanceDailyPoint(BaseModel):
    """Single date attendance breakdown."""
    date: str
    present: int
    absent: int
    on_leave: int


class AttendanceAnalytics(BaseModel):
    """Aggregated attendance statistics across a given date range."""
    start_date: str
    end_date: str
    total_expected: int
    total_present: int
    total_absent: int
    total_leaves: int
    average_attendance_rate: float
    daily_breakdown: List[AttendanceDailyPoint] = []


class EmployeeTaskMetric(BaseModel):
    """Task performance metric for an individual employee."""
    employee_id: str
    employee_name: str
    assigned_count: int
    completed_count: int
    overdue_count: int
    completion_rate: float
    on_time_rate: float


class TaskAnalytics(BaseModel):
    """Overall and per-entity task completion analytics."""
    total_assignments: int
    completed_assignments: int
    overdue_assignments: int
    overall_completion_rate: float
    overall_on_time_rate: float
    by_employee: List[EmployeeTaskMetric] = []
