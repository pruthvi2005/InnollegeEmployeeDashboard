from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)
from app.dependencies import require_founder, get_current_active_user
from app.core.exceptions import NotFoundError, ConflictError

router = APIRouter(prefix="/departments", tags=["Departments"])


def _to_department_response(dept: Department, db: Session) -> DepartmentResponse:
    count = db.execute(
        select(func.count(Employee.id)).where(
            Employee.department_id == dept.id,
            Employee.is_active.is_(True),
        )
    ).scalar() or 0
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        is_active=dept.is_active,
        employee_count=count,
        created_at=dept.created_at,
    )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Create a new department (Founder only)."""
    existing = db.execute(select(Department).where(Department.name == payload.name)).scalar_one_or_none()
    if existing:
        raise ConflictError(f"Department '{payload.name}' already exists")

    dept = Department(
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return _to_department_response(dept, db)


@router.get("/", response_model=List[DepartmentResponse], status_code=status.HTTP_200_OK)
def list_departments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all active departments (Authenticated)."""
    stmt = select(Department).where(Department.is_active.is_(True)).order_by(Department.name.asc())
    departments = db.execute(stmt).scalars().all()
    return [_to_department_response(d, db) for d in departments]


@router.patch("/{id}", response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
def update_department(
    id: str,
    payload: DepartmentUpdate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Update department details (Founder only)."""
    dept = db.execute(select(Department).where(Department.id == id)).scalar_one_or_none()
    if not dept:
        raise NotFoundError("Department not found")

    if payload.name is not None and payload.name != dept.name:
        existing = db.execute(select(Department).where(Department.name == payload.name)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Department '{payload.name}' already exists")
        dept.name = payload.name

    if payload.description is not None:
        dept.description = payload.description

    if payload.is_active is not None:
        dept.is_active = payload.is_active

    db.commit()
    db.refresh(dept)
    return _to_department_response(dept, db)
