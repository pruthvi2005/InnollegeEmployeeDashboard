from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee, EmployeeProfile
from app.models.project import ProjectMember
from app.models.task import TaskAssignment, TaskUpdate, TaskComment
from app.models.attendance import Attendance, AttendanceAdjustment, AttendanceEvent
from app.models.report import DailyReport, DailyReportTask
from app.models.file import ReportFile
from app.models.leave import LeaveRequest, LeaveAction
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeStatusUpdate,
    EmployeePasswordResetRequest,
    EmployeeResponse,
    EmployeeListResponse,
)
from app.services.employee_service import EmployeeService
from app.dependencies import (
    require_founder,
    require_employee,
    get_employee_from_user,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


def _to_employee_response(emp: Employee) -> EmployeeResponse:
    """Format SQLAlchemy Employee model into EmployeeResponse schema."""
    dept_name = emp.department.name if emp.department else None
    role_val = (
        emp.user.role.value
        if hasattr(emp.user.role, "value")
        else str(emp.user.role)
    )
    return EmployeeResponse(
        id=emp.id,
        user_id=emp.user_id,
        employee_id=emp.employee_id,
        full_name=emp.full_name,
        email=emp.user.email,
        phone=emp.user.phone,
        department_id=emp.department_id,
        department_name=dept_name,
        designation=emp.designation,
        joining_date=emp.joining_date,
        profile_photo_url=emp.profile_photo_url,
        is_active=emp.is_active,
        role=role_val,
        created_at=emp.created_at,
    )


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Create a new employee and underlying user account (Founder only)."""
    emp = EmployeeService.create_employee(db=db, data=payload, founder_user=founder)
    return _to_employee_response(emp)


@router.get("/", response_model=EmployeeListResponse, status_code=status.HTTP_200_OK)
def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """List employees directory with filtering and search (Founder only)."""
    items, total = EmployeeService.list_employees(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        department_id=department_id,
        is_active=is_active,
    )
    return EmployeeListResponse(
        items=[_to_employee_response(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
def get_my_employee_record(
    employee: Employee = Depends(get_employee_from_user),
):
    """Retrieve self employee profile (Employee only)."""
    return _to_employee_response(employee)


@router.patch("/me", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
def update_my_employee_record(
    payload: EmployeeUpdate,
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Allow an employee to update their own editable profile fields."""
    if payload.full_name is not None:
        employee.full_name = payload.full_name
    if payload.phone is not None:
        employee.phone = payload.phone
    if payload.profile_photo_url is not None:
        employee.profile_photo_url = payload.profile_photo_url
    db.commit()
    db.refresh(employee)
    return _to_employee_response(employee)


@router.get("/{employee_id}", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
def get_employee(
    employee_id: str,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Fetch employee by UUID or employee code (Founder only)."""
    emp = EmployeeService.get_employee(db=db, employee_id=employee_id)
    return _to_employee_response(emp)


@router.patch("/{employee_id}", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Update employee details (Founder only)."""
    emp = EmployeeService.update_employee(db=db, employee_id=employee_id, data=payload)
    return _to_employee_response(emp)


@router.patch("/{employee_id}/status", response_model=EmployeeResponse, status_code=status.HTTP_200_OK)
def update_employee_status(
    employee_id: str,
    payload: EmployeeStatusUpdate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Activate or deactivate employee account (Founder only)."""
    emp = EmployeeService.update_employee_status(db=db, employee_id=employee_id, is_active=payload.is_active)
    return _to_employee_response(emp)


@router.patch("/{employee_id}/password", status_code=status.HTTP_200_OK)
def reset_employee_password(
    employee_id: str,
    payload: EmployeePasswordResetRequest,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Allow a founder to reset an employee password without returning it."""
    EmployeeService.reset_employee_password(
        db=db,
        employee_id=employee_id,
        new_password=payload.new_password,
        founder_user=founder,
    )
    return {"message": "Employee password reset successfully."}


@router.delete("/{employee_id}", status_code=status.HTTP_200_OK)
def delete_employee(
    employee_id: str,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Permanently remove an employee and their associated employee records."""
    employee = EmployeeService.get_employee(db=db, employee_id=employee_id)
    user_id = employee.user_id

    assignment_ids = select(TaskAssignment.id).where(TaskAssignment.employee_id == employee.id)
    db.execute(delete(TaskUpdate).where(TaskUpdate.assignment_id.in_(assignment_ids)))
    db.execute(delete(TaskAssignment).where(TaskAssignment.employee_id == employee.id))
    db.execute(delete(TaskComment).where(TaskComment.employee_id == employee.id))
    db.execute(delete(ProjectMember).where(ProjectMember.employee_id == employee.id))

    attendance_ids = select(Attendance.id).where(Attendance.employee_id == employee.id)
    db.execute(delete(AttendanceEvent).where(AttendanceEvent.attendance_id.in_(attendance_ids)))
    db.execute(delete(AttendanceAdjustment).where(AttendanceAdjustment.attendance_id.in_(attendance_ids)))
    db.execute(delete(Attendance).where(Attendance.employee_id == employee.id))

    report_ids = select(DailyReport.id).where(DailyReport.employee_id == employee.id)
    db.execute(delete(DailyReportTask).where(DailyReportTask.report_id.in_(report_ids)))
    db.execute(delete(ReportFile).where(ReportFile.report_id.in_(report_ids)))
    db.execute(delete(DailyReport).where(DailyReport.employee_id == employee.id))

    leave_ids = select(LeaveRequest.id).where(LeaveRequest.employee_id == employee.id)
    db.execute(delete(LeaveAction).where(LeaveAction.leave_request_id.in_(leave_ids)))
    db.execute(delete(LeaveRequest).where(LeaveRequest.employee_id == employee.id))

    db.execute(delete(EmployeeProfile).where(EmployeeProfile.employee_id == employee.id))
    db.delete(employee)
    user = db.get(User, user_id)
    if user:
        db.delete(user)
    db.commit()
    return {"message": "Employee and associated records deleted"}
