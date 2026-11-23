from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.leave import (
    LeaveType,
    LeaveRequest,
    LeaveAction,
    LeaveRequestStatus,
)
from app.services.notification_service import NotificationService
from app.schemas.leave import (
    LeaveRequestCreate,
    LeaveDecisionRequest,
    LeaveRequestResponse,
    LeaveTypeResponse,
)
from app.dependencies import (
    require_founder,
    get_employee_from_user,
    get_current_active_user,
)
from app.core.exceptions import NotFoundError, AuthorizationError, ConflictError

router = APIRouter(prefix="/leaves", tags=["Leaves"])


def _to_leave_response(lr: LeaveRequest) -> LeaveRequestResponse:
    emp_name = lr.employee.full_name if lr.employee else "Unknown"
    type_name = lr.leave_type.name if lr.leave_type else "Unknown"
    last_comment = lr.actions[-1].comment if lr.actions else None
    status_str = lr.status.value if hasattr(lr.status, "value") else str(lr.status)

    return LeaveRequestResponse(
        id=lr.id,
        employee_id=lr.employee_id,
        employee_name=emp_name,
        leave_type_name=type_name,
        start_date=lr.start_date,
        end_date=lr.end_date,
        total_days=lr.total_days,
        reason=lr.reason,
        status=status_str,
        decision_comment=last_comment,
        created_at=lr.created_at,
    )


@router.get("/types", response_model=List[LeaveTypeResponse], status_code=status.HTTP_200_OK)
def list_leave_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List configured leave categories."""
    types = db.execute(select(LeaveType).where(LeaveType.is_active == True)).scalars().all()  # noqa: E712
    return [
        LeaveTypeResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            days_per_year=t.days_per_year,
        )
        for t in types
    ]


@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_leave_request(
    payload: LeaveRequestCreate,
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """File a leave request application (Employee only)."""
    if payload.end_date < payload.start_date:
        raise ConflictError("End date cannot be prior to start date")

    leave_type = db.execute(select(LeaveType).where(LeaveType.id == payload.leave_type_id)).scalar_one_or_none()
    if not leave_type:
        raise NotFoundError("Leave type not found")

    total_days = max(1, (payload.end_date - payload.start_date).days + 1)

    req = LeaveRequest(
        employee_id=employee.id,
        leave_type_id=payload.leave_type_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_days=total_days,
        reason=payload.reason,
        status=LeaveRequestStatus.pending,
    )
    db.add(req)
    db.flush()
    if employee.user_id:
        NotificationService.add_to_founders(
            db=db,
            title=f"Leave request from {employee.full_name}",
            message=(
                f"{employee.full_name} requested {total_days} day(s) of "
                f"{leave_type.name} from {payload.start_date} to {payload.end_date}."
            ),
            type="warning",
            reference_id=req.id,
            reference_type="leave",
        )
    db.commit()
    db.refresh(req)

    # Reload with joins
    loaded = (
        db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.id == req.id)
            .options(
                joinedload(LeaveRequest.employee),
                joinedload(LeaveRequest.leave_type),
                joinedload(LeaveRequest.actions),
            )
        )
        .unique()
        .scalar_one()
    )
    return _to_leave_response(loaded)


@router.get("/", response_model=List[LeaveRequestResponse], status_code=status.HTTP_200_OK)
def list_leave_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List leave requests. Founder views all; employee views only their own."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    query = (
        select(LeaveRequest)
        .options(
            joinedload(LeaveRequest.employee),
            joinedload(LeaveRequest.leave_type),
            joinedload(LeaveRequest.actions),
        )
        .order_by(LeaveRequest.created_at.desc())
    )

    if role_val != "founder":
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp:
            return []
        query = query.where(LeaveRequest.employee_id == emp.id)

    requests = db.execute(query).scalars().unique().all()
    return [_to_leave_response(r) for r in requests]


@router.patch("/{id}/decision", response_model=LeaveRequestResponse, status_code=status.HTTP_200_OK)
def review_leave_decision(
    id: str,
    payload: LeaveDecisionRequest,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Approve or reject leave request (Founder only)."""
    stmt = (
        select(LeaveRequest)
        .where(LeaveRequest.id == id)
        .options(
            joinedload(LeaveRequest.employee),
            joinedload(LeaveRequest.leave_type),
            joinedload(LeaveRequest.actions),
        )
    )
    leave_req = db.execute(stmt).unique().scalar_one_or_none()
    if not leave_req:
        raise NotFoundError("Leave request not found")

    new_status = LeaveRequestStatus.approved if payload.action == "approved" else LeaveRequestStatus.rejected
    leave_req.status = new_status

    action = LeaveAction(
        leave_request_id=leave_req.id,
        action_by=founder.id,
        action=payload.action,
        comment=payload.comment,
    )
    db.add(action)
    if leave_req.employee and leave_req.employee.user_id:
        status_label = "approved" if payload.action == "approved" else "rejected"
        NotificationService.add_notifications(
            db=db,
            user_ids=[leave_req.employee.user_id],
            title=f"Leave request {status_label}",
            message=(
                f"Your {leave_req.leave_type.name if leave_req.leave_type else 'leave'} "
                f"request from {leave_req.start_date} to {leave_req.end_date} was {status_label}."
            ),
            type="success" if status_label == "approved" else "alert",
            reference_id=leave_req.id,
            reference_type="leave",
        )
    db.commit()
    db.refresh(leave_req)

    return _to_leave_response(leave_req)
