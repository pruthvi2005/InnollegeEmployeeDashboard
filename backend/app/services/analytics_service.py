from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
import pytz
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.employee import Employee
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskAssignment, AssignmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.report import DailyReport, ReportStatus
from app.models.leave import LeaveRequest, LeaveRequestStatus
from app.schemas.analytics import (
    OverviewStats,
    AttendanceAnalytics,
    AttendanceDailyPoint,
    TaskAnalytics,
    EmployeeTaskMetric,
)


class AnalyticsService:
    """Service providing aggregate analytics for founders and management."""

    @staticmethod
    def _get_current_company_date() -> date:
        """Get current calendar date in company operational timezone (Asia/Kolkata)."""
        tz = pytz.timezone(settings.COMPANY_TIMEZONE)
        return datetime.now(tz).date()

    @classmethod
    def get_overview_stats(cls, db: Session) -> OverviewStats:
        """Compile high-level KPIs from live database tables."""
        today = cls._get_current_company_date()

        # Employees
        total_employees = db.execute(
            select(func.count(Employee.id)).where(Employee.is_active == True)  # noqa: E712
        ).scalar() or 0

        # Attendance today
        present_today = db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.work_date == today,
                Attendance.status == AttendanceStatus.present,
            )
        ).scalar() or 0

        # Leave today
        on_leave_today = db.execute(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.status == LeaveRequestStatus.approved,
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
            )
        ).scalar() or 0

        absent_today = max(0, total_employees - present_today - on_leave_today)

        # Projects
        active_projects = db.execute(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.active)
        ).scalar() or 0

        # Tasks
        total_tasks = db.execute(select(func.count(Task.id))).scalar() or 0

        # Assignment statuses
        pending_tasks = db.execute(
            select(func.count(TaskAssignment.id)).where(
                TaskAssignment.status == AssignmentStatus.pending
            )
        ).scalar() or 0

        in_progress_tasks = db.execute(
            select(func.count(TaskAssignment.id)).where(
                TaskAssignment.status == AssignmentStatus.in_progress
            )
        ).scalar() or 0

        completed_tasks = db.execute(
            select(func.count(TaskAssignment.id)).where(
                TaskAssignment.status == AssignmentStatus.completed
            )
        ).scalar() or 0

        overdue_tasks = db.execute(
            select(func.count(TaskAssignment.id)).where(
                TaskAssignment.status == AssignmentStatus.overdue
            )
        ).scalar() or 0

        # Pending reports (submitted and not reviewed)
        pending_reports = db.execute(
            select(func.count(DailyReport.id)).where(
                DailyReport.status == ReportStatus.submitted,
                DailyReport.reviewed_by.is_(None),
            )
        ).scalar() or 0

        # Pending leave requests
        pending_leaves = db.execute(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.status == LeaveRequestStatus.pending
            )
        ).scalar() or 0
        attendance_chart = cls.get_weekly_attendance_chart(db=db, today=today)

        return OverviewStats(
            total_employees=total_employees,
            present_today=present_today,
            absent_today=absent_today,
            on_leave_today=on_leave_today,
            active_projects=active_projects,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            pending_reports=pending_reports,
            pending_leaves=pending_leaves,
            attendance_chart=attendance_chart,
        )

    @staticmethod
    def get_weekly_attendance_chart(db: Session, today: date) -> List[Dict[str, Any]]:
        """Build daily present, absent, and approved-leave counts for the last week."""
        start_date = today - timedelta(days=6)
        work_days = [start_date + timedelta(days=offset) for offset in range(7)]

        employees = db.execute(
            select(Employee.id, Employee.joining_date).where(Employee.is_active == True)  # noqa: E712
        ).all()
        expected_by_day = {
            day: {
                employee_id
                for employee_id, joining_date in employees
                if joining_date is None or joining_date <= day
            }
            for day in work_days
        }

        present_by_day = {day: set() for day in work_days}
        leave_by_day = {day: set() for day in work_days}

        attendance_records = db.execute(
            select(Attendance)
            .join(Employee, Attendance.employee_id == Employee.id)
            .where(
                Employee.is_active == True,  # noqa: E712
                Attendance.work_date >= start_date,
                Attendance.work_date <= today,
            )
        ).scalars().all()

        for record in attendance_records:
            if record.work_date not in expected_by_day:
                continue
            status_value = record.status.value if hasattr(record.status, "value") else str(record.status)
            if status_value in ("present", "half_day"):
                present_by_day[record.work_date].add(record.employee_id)
            elif status_value == "on_leave":
                leave_by_day[record.work_date].add(record.employee_id)

        approved_leaves = db.execute(
            select(LeaveRequest)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .where(
                Employee.is_active == True,  # noqa: E712
                LeaveRequest.status == LeaveRequestStatus.approved,
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= start_date,
            )
        ).scalars().all()

        for leave_request in approved_leaves:
            for day in work_days:
                if leave_request.start_date <= day <= leave_request.end_date:
                    leave_by_day[day].add(leave_request.employee_id)

        return [
            {
                "date": day.isoformat(),
                "present": len(present_by_day[day] & expected_by_day[day]),
                "leave": len((leave_by_day[day] - present_by_day[day]) & expected_by_day[day]),
                "absent": max(
                    0,
                    len(expected_by_day[day])
                    - len(present_by_day[day] & expected_by_day[day])
                    - len((leave_by_day[day] - present_by_day[day]) & expected_by_day[day]),
                ),
            }
            for day in work_days
        ]

    @classmethod
    def get_attendance_analytics(
        cls,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AttendanceAnalytics:
        """Calculate attendance ratios over date window."""
        today = cls._get_current_company_date()
        if not end_date:
            end_date = today
        if not start_date:
            start_date = end_date.replace(day=1)

        # Query all attendance in window
        records = db.execute(
            select(Attendance).where(
                Attendance.work_date >= start_date,
                Attendance.work_date <= end_date,
            )
        ).scalars().all()

        total_present = sum(1 for r in records if r.status == AttendanceStatus.present)
        total_absent = sum(1 for r in records if r.status == AttendanceStatus.absent)
        total_leaves = sum(1 for r in records if r.status == AttendanceStatus.on_leave)
        total_records = len(records)

        rate = (total_present / total_records * 100.0) if total_records > 0 else 0.0

        return AttendanceAnalytics(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            total_expected=total_records,
            total_present=total_present,
            total_absent=total_absent,
            total_leaves=total_leaves,
            average_attendance_rate=round(rate, 2),
            daily_breakdown=[],
        )

    @classmethod
    def get_task_analytics(cls, db: Session) -> TaskAnalytics:
        """Calculate task completion metrics globally and by employee."""
        assignments = db.execute(select(TaskAssignment)).scalars().all()
        total_assignments = len(assignments)
        completed_assignments = sum(
            1 for a in assignments if a.status == AssignmentStatus.completed
        )
        overdue_assignments = sum(
            1 for a in assignments if a.status == AssignmentStatus.overdue
        )

        overall_comp_rate = (
            (completed_assignments / total_assignments * 100.0)
            if total_assignments > 0
            else 0.0
        )
        overall_on_time_rate = (
            ((completed_assignments - overdue_assignments) / total_assignments * 100.0)
            if total_assignments > 0
            else 0.0
        )
        overall_on_time_rate = max(0.0, overall_on_time_rate)

        # Per employee breakdown
        employees = db.execute(select(Employee).where(Employee.is_active == True)).scalars().all()
        by_employee: List[EmployeeTaskMetric] = []
        for emp in employees:
            emp_assigns = [a for a in assignments if a.employee_id == emp.id]
            assigned_c = len(emp_assigns)
            comp_c = sum(1 for a in emp_assigns if a.status == AssignmentStatus.completed)
            overdue_c = sum(1 for a in emp_assigns if a.status == AssignmentStatus.overdue)
            comp_r = (comp_c / assigned_c * 100.0) if assigned_c > 0 else 0.0
            on_time_r = (
                max(0.0, (comp_c - overdue_c) / assigned_c * 100.0)
                if assigned_c > 0
                else 0.0
            )

            by_employee.append(
                EmployeeTaskMetric(
                    employee_id=emp.id,
                    employee_name=emp.full_name,
                    assigned_count=assigned_c,
                    completed_count=comp_c,
                    overdue_count=overdue_c,
                    completion_rate=round(comp_r, 2),
                    on_time_rate=round(on_time_r, 2),
                )
            )

        return TaskAnalytics(
            total_assignments=total_assignments,
            completed_assignments=completed_assignments,
            overdue_assignments=overdue_assignments,
            overall_completion_rate=round(overall_comp_rate, 2),
            overall_on_time_rate=round(overall_on_time_rate, 2),
            by_employee=by_employee,
        )

    @classmethod
    def get_employee_performance(cls, db: Session, employee_id: str) -> Dict[str, Any]:
        """Detailed individual employee metrics."""
        emp = db.execute(select(Employee).where(Employee.id == employee_id)).scalar_one_or_none()
        if not emp:
            return {}

        assignments = db.execute(
            select(TaskAssignment).where(TaskAssignment.employee_id == employee_id)
        ).scalars().all()

        total = len(assignments)
        completed = sum(1 for a in assignments if a.status == AssignmentStatus.completed)
        overdue = sum(1 for a in assignments if a.status == AssignmentStatus.overdue)

        return {
            "employee_id": emp.id,
            "employee_name": emp.full_name,
            "tasks_assigned": total,
            "tasks_completed": completed,
            "tasks_overdue": overdue,
            "completion_rate": round((completed / total * 100.0) if total else 0.0, 2),
        }
