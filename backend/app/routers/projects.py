from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectMemberAdd,
    ProjectMemberResponse,
)
from app.dependencies import require_founder, get_current_active_user
from app.core.exceptions import NotFoundError, AuthorizationError, ConflictError

router = APIRouter(prefix="/projects", tags=["Projects"])


def _to_project_response(p: Project, db: Session) -> ProjectResponse:
    m_count = db.execute(
        select(func.count(ProjectMember.id)).where(ProjectMember.project_id == p.id)
    ).scalar() or 0
    t_count = db.execute(
        select(func.count(Task.id)).where(Task.project_id == p.id)
    ).scalar() or 0
    status_val = p.status.value if hasattr(p.status, "value") else str(p.status)

    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        status=status_val,
        start_date=p.start_date,
        end_date=p.end_date,
        member_count=m_count,
        task_count=t_count,
        created_at=p.created_at,
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Create a new project (Founder only)."""
    project = Project(
        name=payload.name,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        created_by=founder.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _to_project_response(project, db)


@router.get("/", response_model=List[ProjectResponse], status_code=status.HTTP_200_OK)
def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List projects. Founders see all projects; employees see projects they belong to."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    if role_val == "founder":
        projects = db.execute(select(Project).order_by(Project.created_at.desc())).scalars().all()
    else:
        # Employee view
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp:
            return []
        projects = (
            db.execute(
                select(Project)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .where(ProjectMember.employee_id == emp.id)
                .order_by(Project.created_at.desc())
            )
            .scalars()
            .all()
        )

    return [_to_project_response(p, db) for p in projects]


@router.get("/{id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def get_project(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get project details with member access check."""
    project = db.execute(select(Project).where(Project.id == id)).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "founder":
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp:
            raise AuthorizationError("Access denied")
        member = db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == id, ProjectMember.employee_id == emp.id
            )
        ).scalar_one_or_none()
        if not member:
            raise AuthorizationError("You are not assigned to this project")

    return _to_project_response(project, db)


@router.patch("/{id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
def update_project(
    id: str,
    payload: ProjectUpdate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Update project details (Founder only)."""
    project = db.execute(select(Project).where(Project.id == id)).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.status is not None:
        project.status = payload.status
    if payload.start_date is not None:
        project.start_date = payload.start_date
    if payload.end_date is not None:
        project.end_date = payload.end_date

    db.commit()
    db.refresh(project)
    return _to_project_response(project, db)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_project(
    id: str,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Delete a project and remove its member links; retain its tasks."""
    project = db.execute(select(Project).where(Project.id == id)).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found")
    db.execute(delete(ProjectMember).where(ProjectMember.project_id == id))
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


@router.post("/{id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    id: str,
    payload: ProjectMemberAdd,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Add employee member to a project (Founder only)."""
    project = db.execute(select(Project).where(Project.id == id)).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found")

    emp = db.execute(select(Employee).where(Employee.id == payload.employee_id)).scalar_one_or_none()
    if not emp:
        raise NotFoundError("Employee not found")

    existing = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == id,
            ProjectMember.employee_id == payload.employee_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("Employee is already a member of this project")

    member = ProjectMember(
        project_id=id,
        employee_id=payload.employee_id,
        role=payload.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return ProjectMemberResponse(
        id=member.id,
        employee_id=emp.id,
        employee_name=emp.full_name,
        role=member.role,
        joined_at=member.joined_at,
    )
