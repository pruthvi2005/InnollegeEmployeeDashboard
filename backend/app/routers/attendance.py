from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Optional
import pytz
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance, AttendanceEvent, AttendanceStatus
from app.models.activity import ActivityLog
from app.schemas.attendance import (
    CheckInRequest,
    CheckOutRequest,
    AttendanceResponse,
    AttendanceSummary,
    format_to_ist,
)
from app.dependencies import (
    require_founder,
    get_employee_from_user,
    get_current_active_user,
)
from app.core.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _get_company_today() -> date:
    tz = pytz.timezone(settings.COMPANY_TIMEZONE)
    return datetime.now(tz).date()


@router.get("/today", status_code=status.HTTP_200_OK)
def get_today_attendance(
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Get the signed-in employee's attendance status for today."""
    today = _get_company_today()
    attendance = db.execute(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.work_date == today,
        )
    ).scalar_one_or_none()

    if not attendance:
        return {
            "status": "not_checked_in",
            "check_in_time": None,
            "check_out_time": None,
            "working_hours": 0,
        }

    status_str = attendance.status.value if hasattr(attendance.status, "value") else str(attendance.status)
    if attendance.check_in_time and attendance.check_out_time:
        status_str = "present"

    return {
        "status": status_str,
        "check_in_time": format_to_ist(attendance.check_in_time),
        "check_out_time": format_to_ist(attendance.check_out_time),
        "working_hours": float(attendance.working_hours or 0),
    }


def _to_attendance_response(att: Attendance, emp_name: str) -> AttendanceResponse:
    status_str = att.status.value if hasattr(att.status, "value") else str(att.status)
    return AttendanceResponse(
        id=att.id,
        employee_id=att.employee_id,
        employee_name=emp_name,
        work_date=att.work_date,
        check_in_time=format_to_ist(att.check_in_time),
        check_out_time=format_to_ist(att.check_out_time),
        working_hours=att.working_hours,
        status=status_str,
        is_late=att.is_late,
    )


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_200_OK)
def check_in(
    payload: CheckInRequest,
    request: Request,
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Employee check-in for the current day."""
    today = _get_company_today()
    now_utc = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else None

    # Check for existing record
    stmt = select(Attendance).where(
        Attendance.employee_id == employee.id,
        Attendance.work_date == today,
    )
    attendance = db.execute(stmt).scalar_one_or_none()

    if attendance and attendance.check_in_time:
        raise ConflictError("Check-in already registered for today")

    # Determine if late (e.g. check-in past 10:00 AM IST)
    tz = pytz.timezone(settings.COMPANY_TIMEZONE)
    local_now = datetime.now(tz)
    is_late = local_now.hour > 10 or (local_now.hour == 10 and local_now.minute > 15)

    if not attendance:
        attendance = Attendance(
            employee_id=employee.id,
            work_date=today,
            check_in_time=now_utc,
            status=AttendanceStatus.present,
            is_late=is_late,
            notes=payload.notes,
        )
        db.add(attendance)
        db.flush()
    else:
        attendance.check_in_time = now_utc
        attendance.status = AttendanceStatus.present
        attendance.is_late = is_late
        if payload.notes:
            attendance.notes = payload.notes

    event = AttendanceEvent(
        attendance_id=attendance.id,
        event_type="check_in",
        timestamp=now_utc,
        ip_address=client_ip,
    )
    db.add(event)
    db.add(
        ActivityLog(
            user_id=employee.user_id,
            employee_id=employee.id,
            event_type="attendance_check_in",
            event_data={"work_date": today.isoformat()},
            ip_address=client_ip,
        )
    )
    db.commit()
    db.refresh(attendance)

    return _to_attendance_response(attendance, employee.full_name)


@router.post("/check-out", response_model=AttendanceResponse, status_code=status.HTTP_200_OK)
def check_out(
    payload: CheckOutRequest,
    request: Request,
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Employee check-out for the current day."""
    today = _get_company_today()
    now_utc = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else None

    stmt = select(Attendance).where(
        Attendance.employee_id == employee.id,
        Attendance.work_date == today,
    )
    attendance = db.execute(stmt).scalar_one_or_none()

    if not attendance or not attendance.check_in_time:
        raise ConflictError("Cannot check out without prior check-in for today")

    if attendance.check_out_time:
        raise ConflictError("Check-out already registered for today")

    attendance.check_out_time = now_utc

    # Calculate working hours
    cin = attendance.check_in_time
    if cin.tzinfo is None:
        cin = cin.replace(tzinfo=timezone.utc)
    diff_hours = (now_utc - cin).total_seconds() / 3600.0
    attendance.working_hours = Decimal(f"{max(0.0, diff_hours):.2f}")

    if payload.notes:
        existing_notes = attendance.notes or ""
        attendance.notes = f"{existing_notes} | Out: {payload.notes}".strip(" |")

    event = AttendanceEvent(
        attendance_id=attendance.id,
        event_type="check_out",
        timestamp=now_utc,
        ip_address=client_ip,
    )
    db.add(event)
    db.add(
        ActivityLog(
            user_id=employee.user_id,
            employee_id=employee.id,
            event_type="attendance_check_out",
            event_data={"work_date": today.isoformat()},
            ip_address=client_ip,
        )
    )
    db.commit()
    db.refresh(attendance)

    return _to_attendance_response(attendance, employee.full_name)


@router.get("/me", status_code=status.HTTP_200_OK)
def get_my_attendance(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Retrieve personal attendance records and summary metrics."""
    offset = max(0, (page - 1) * page_size)
    stmt = (
        select(Attendance)
        .where(Attendance.employee_id == employee.id)
        .order_by(Attendance.work_date.desc())
        .offset(offset)
        .limit(page_size)
    )
    records = db.execute(stmt).scalars().all()

    # Aggregate summary
    all_records = db.execute(
        select(Attendance).where(Attendance.employee_id == employee.id)
    ).scalars().all()

    total_days = len(all_records)
    present_days = sum(1 for r in all_records if r.status == AttendanceStatus.present)
    absent_days = sum(1 for r in all_records if r.status == AttendanceStatus.absent)
    late_days = sum(1 for r in all_records if r.is_late)
    leave_days = sum(1 for r in all_records if r.status == AttendanceStatus.on_leave)
    attendance_rate = (present_days / total_days * 100.0) if total_days > 0 else 0.0

    summary = AttendanceSummary(
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        leave_days=leave_days,
        attendance_rate=round(attendance_rate, 2),
    )

    items = [_to_attendance_response(r, employee.full_name) for r in records]
    return {
        "items": items,
        "summary": summary,
        "page": page,
        "page_size": page_size,
    }


@router.get("/", response_model=List[AttendanceResponse], status_code=status.HTTP_200_OK)
def list_all_attendance(
    employee_id: Optional[str] = Query(None),
    work_date: Optional[date] = Query(None),
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Query company-wide attendance records with filters (Founder only)."""
    stmt = select(Attendance).options(joinedload(Attendance.employee))

    if employee_id:
        stmt = stmt.where(Attendance.employee_id == employee_id)
    if work_date:
        stmt = stmt.where(Attendance.work_date == work_date)

    records = db.execute(stmt.order_by(Attendance.work_date.desc())).scalars().all()
    results = []
    for r in records:
        emp_name = r.employee.full_name if r.employee else "Unknown"
        results.append(_to_attendance_response(r, emp_name))

    return results
