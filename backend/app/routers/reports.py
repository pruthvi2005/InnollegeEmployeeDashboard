from datetime import datetime, timezone, date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.employee import Employee
from app.models.report import DailyReport, DailyReportTask, ReportStatus
from app.services.notification_service import NotificationService
from app.schemas.report import (
    DailyReportCreate,
    DailyReportResponse,
    ReportReviewRequest,
    ReportTaskItem,
)
from app.dependencies import (
    require_founder,
    get_employee_from_user,
    get_current_active_user,
)
from app.core.exceptions import NotFoundError, AuthorizationError, ConflictError

router = APIRouter(prefix="/reports", tags=["Daily Reports"])


def _to_report_response(report: DailyReport, emp_name: str) -> DailyReportResponse:
    tasks = [
        ReportTaskItem(
            task_id=t.task_id,
            task_description=t.task_description,
            time_spent_hours=t.time_spent_hours,
            notes=t.notes,
        )
        for t in report.task_items
    ]
    status_str = report.status.value if hasattr(report.status, "value") else str(report.status)

    return DailyReportResponse(
        id=report.id,
        employee_id=report.employee_id,
        employee_name=emp_name,
        report_date=report.report_date,
        completed_work=report.completed_work,
        pending_work=report.pending_work,
        challenges=report.challenges,
        tomorrow_plan=report.tomorrow_plan,
        total_hours_worked=report.total_hours_worked,
        task_items=tasks,
        status=status_str,
        founder_feedback=report.founder_feedback,
        reviewed_at=report.reviewed_at,
        submitted_at=report.submitted_at,
        created_at=report.created_at,
    )


@router.get("/today", status_code=status.HTTP_200_OK)
def get_today_report_status(
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Get today's report status for the signed-in employee."""
    from pytz import timezone
    tz = timezone(settings.COMPANY_TIMEZONE)
    today = datetime.now(tz).date()
    report = db.execute(
        select(DailyReport).where(
            DailyReport.employee_id == employee.id,
            DailyReport.report_date == today,
        )
    ).scalar_one_or_none()

    if not report:
        return {"status": "not_submitted", "submitted_at": None, "report_id": None}

    status_str = report.status.value if hasattr(report.status, "value") else str(report.status)
    return {
        "status": status_str,
        "submitted_at": report.submitted_at,
        "report_id": report.id,
    }


@router.post("/", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
def submit_or_save_report(
    payload: DailyReportCreate,
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Save draft or submit end-of-day work report."""
    stmt = (
        select(DailyReport)
        .where(
            DailyReport.employee_id == employee.id,
            DailyReport.report_date == payload.report_date,
        )
        .options(joinedload(DailyReport.task_items))
    )
    existing = db.execute(stmt).scalar_one_or_none()

    now_utc = datetime.now(timezone.utc)

    if existing:
        if existing.status in (ReportStatus.submitted, ReportStatus.reviewed):
            raise ConflictError("Report for this date has already been submitted and cannot be modified")

        # Update existing draft
        existing.completed_work = payload.completed_work
        existing.pending_work = payload.pending_work
        existing.challenges = payload.challenges
        existing.tomorrow_plan = payload.tomorrow_plan
        existing.total_hours_worked = payload.total_hours_worked
        existing.status = payload.status
        if payload.status == ReportStatus.submitted:
            existing.submitted_at = now_utc

        # Replace task items
        for old_item in list(existing.task_items):
            db.delete(old_item)
        existing.task_items = [
            DailyReportTask(
                report_id=existing.id,
                task_id=item.task_id,
                task_description=item.task_description,
                time_spent_hours=item.time_spent_hours,
                notes=item.notes,
            )
            for item in payload.task_items
        ]
        if payload.status == ReportStatus.submitted and employee.user_id:
            NotificationService.add_to_founders(
                db=db,
                title=f"Daily report submitted by {employee.full_name}",
                message=f"{employee.full_name} submitted the daily report for {payload.report_date}.",
                type="info",
                reference_id=existing.id,
                reference_type="report",
            )
        db.commit()
        db.refresh(existing)
        return _to_report_response(existing, employee.full_name)

    # Create new report
    report = DailyReport(
        employee_id=employee.id,
        report_date=payload.report_date,
        completed_work=payload.completed_work,
        pending_work=payload.pending_work,
        challenges=payload.challenges,
        tomorrow_plan=payload.tomorrow_plan,
        total_hours_worked=payload.total_hours_worked,
        status=payload.status,
        submitted_at=now_utc if payload.status == ReportStatus.submitted else None,
    )
    db.add(report)
    db.flush()

    for item in payload.task_items:
        task_item = DailyReportTask(
            report_id=report.id,
            task_id=item.task_id,
            task_description=item.task_description,
            time_spent_hours=item.time_spent_hours,
            notes=item.notes,
        )
        db.add(task_item)

    if payload.status == ReportStatus.submitted and employee.user_id:
        NotificationService.add_to_founders(
            db=db,
            title=f"Daily report submitted by {employee.full_name}",
            message=f"{employee.full_name} submitted the daily report for {payload.report_date}.",
            type="info",
            reference_id=report.id,
            reference_type="report",
        )
    db.commit()
    db.refresh(report)
    return _to_report_response(report, employee.full_name)


@router.get("/", response_model=List[DailyReportResponse], status_code=status.HTTP_200_OK)
def list_reports(
    employee_id: Optional[str] = Query(None),
    report_date: Optional[date] = Query(None),
    status_filter: Optional[ReportStatus] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List daily reports. Founder can inspect all; employees see only their own."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    query = (
        select(DailyReport)
        .options(
            joinedload(DailyReport.employee),
            joinedload(DailyReport.task_items),
        )
        .order_by(DailyReport.report_date.desc())
    )

    if role_val != "founder":
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp:
            return []
        query = query.where(DailyReport.employee_id == emp.id)
    else:
        if employee_id:
            query = query.where(DailyReport.employee_id == employee_id)

    if report_date:
        query = query.where(DailyReport.report_date == report_date)
    if status_filter:
        query = query.where(DailyReport.status == status_filter)

    reports = db.execute(query).scalars().unique().all()
    results = []
    for r in reports:
        emp_name = r.employee.full_name if r.employee else "Unknown"
        results.append(_to_report_response(r, emp_name))

    return results


@router.get("/{id}", response_model=DailyReportResponse, status_code=status.HTTP_200_OK)
def get_report(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed report with access check."""
    stmt = (
        select(DailyReport)
        .where(DailyReport.id == id)
        .options(
            joinedload(DailyReport.employee),
            joinedload(DailyReport.task_items),
        )
    )
    report = db.execute(stmt).unique().scalar_one_or_none()
    if not report:
        raise NotFoundError("Report not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "founder":
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp or report.employee_id != emp.id:
            raise AuthorizationError("Access denied: You can only view your own reports")

    emp_name = report.employee.full_name if report.employee else "Unknown"
    return _to_report_response(report, emp_name)


@router.patch("/{id}/review", response_model=DailyReportResponse, status_code=status.HTTP_200_OK)
def review_report(
    id: str,
    payload: ReportReviewRequest,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Add founder review comments and mark report as reviewed (Founder only)."""
    stmt = (
        select(DailyReport)
        .where(DailyReport.id == id)
        .options(
            joinedload(DailyReport.employee),
            joinedload(DailyReport.task_items),
        )
    )
    report = db.execute(stmt).unique().scalar_one_or_none()
    if not report:
        raise NotFoundError("Report not found")

    report.status = ReportStatus.reviewed
    report.founder_feedback = payload.founder_feedback
    report.reviewed_by = founder.id
    report.reviewed_at = datetime.now(timezone.utc)

    if report.employee and report.employee.user_id:
        NotificationService.add_notifications(
            db=db,
            user_ids=[report.employee.user_id],
            title="Daily report reviewed",
            message="The founder reviewed your daily report."
            + (f" Feedback: {payload.founder_feedback}" if payload.founder_feedback else ""),
            type="success",
            reference_id=report.id,
            reference_type="report",
        )
    db.commit()
    db.refresh(report)

    emp_name = report.employee.full_name if report.employee else "Unknown"
    return _to_report_response(report, emp_name)
