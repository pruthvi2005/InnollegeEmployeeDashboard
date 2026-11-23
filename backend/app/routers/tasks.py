from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.task import (
    Task,
    TaskAssignment,
    TaskUpdate,
    TaskComment,
    AssignmentStatus,
)
from app.services.notification_service import NotificationService
from app.schemas.task import (
    TaskCreate,
    TaskUpdate as TaskUpdateSchema,
    TaskAssignmentUpdate,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskSubmitRequest,
    TaskResponse,
    AssignmentResponse,
)
from app.dependencies import (
    require_founder,
    get_current_active_user,
    get_employee_from_user,
)
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _to_task_response(task: Task, db: Session) -> TaskResponse:
    """Format Task model into TaskResponse with populated assignments."""
    assignments = (
        db.execute(
            select(TaskAssignment)
            .where(TaskAssignment.task_id == task.id)
            .options(joinedload(TaskAssignment.employee))
        )
        .scalars()
        .all()
    )

    assign_responses = []
    for a in assignments:
        emp_name = a.employee.full_name if a.employee else "Unknown"
        status_str = a.status.value if hasattr(a.status, "value") else str(a.status)
        assign_responses.append(
            AssignmentResponse(
                id=a.id,
                employee_id=a.employee_id,
                employee_name=emp_name,
                status=status_str,
                progress_percent=a.progress_percent,
                submitted_at=a.submitted_at,
                completed_at=a.completed_at,
            )
        )

    comment_count = (
        db.execute(
            select(func.count(TaskComment.id)).where(TaskComment.task_id == task.id)
        ).scalar()
        or 0
    )

    priority_str = task.priority.value if hasattr(task.priority, "value") else str(task.priority)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        project_id=task.project_id,
        priority=priority_str,
        start_date=task.start_date,
        deadline=task.deadline,
        instructions=task.instructions,
        assignments=assign_responses,
        comment_count=comment_count,
        created_at=task.created_at,
    )


@router.get("/my-today", status_code=status.HTTP_200_OK)
def get_my_today_tasks(
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Get the signed-in employee's task summary for the dashboard."""
    assignments = (
        db.execute(
            select(TaskAssignment)
            .where(TaskAssignment.employee_id == employee.id)
            .options(
                joinedload(TaskAssignment.task).joinedload(Task.project)
            )
        )
        .scalars()
        .all()
    )

    items = []
    pending = 0
    in_progress = 0
    completed_today = 0
    now = datetime.now(timezone.utc)

    for assignment in assignments:
        task = assignment.task
        if not task:
            continue
        assignment_status = (
            assignment.status.value
            if hasattr(assignment.status, "value")
            else str(assignment.status)
        )
        if assignment_status == "pending":
            pending += 1
        elif assignment_status == "in_progress":
            in_progress += 1
        elif assignment_status in ("completed", "submitted"):
            finished_at = assignment.completed_at or assignment.submitted_at
            if finished_at and finished_at.date() == now.date():
                completed_today += 1

        priority = task.priority.value if hasattr(task.priority, "value") else str(task.priority)
        items.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": priority,
            "status": assignment_status,
            "due_date": task.deadline.isoformat() if task.deadline else None,
            "project_id": task.project_id,
            "project_name": task.project.name if task.project else None,
        })

    return {
        "items": items,
        "counts": {
            "assigned": len(items),
            "pending": pending,
            "in_progress": in_progress,
            "completed_today": completed_today,
        },
    }


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Create a new task and assign to designated employees (Founder only)."""
    task = Task(
        title=payload.title,
        description=payload.description,
        project_id=payload.project_id,
        priority=payload.priority,
        start_date=payload.start_date,
        deadline=payload.deadline,
        instructions=payload.instructions,
        created_by=founder.id,
    )
    db.add(task)
    db.flush()

    assigned_user_ids = []
    for emp_id in payload.assigned_employee_ids:
        # Check employee exists
        emp = db.execute(select(Employee).where(Employee.id == emp_id)).scalar_one_or_none()
        if emp:
            assignment = TaskAssignment(
                task_id=task.id,
                employee_id=emp.id,
                status=AssignmentStatus.pending,
                progress_percent=0,
                assigned_by=founder.id,
            )
            db.add(assignment)
            if emp.user_id:
                assigned_user_ids.append(emp.user_id)

    NotificationService.add_notifications(
        db=db,
        user_ids=assigned_user_ids,
        title=f"New task assigned: {task.title}",
        message=f"The founder assigned you a {task.priority.value} priority task.",
        type="info",
        reference_id=task.id,
        reference_type="task",
    )
    db.commit()
    db.refresh(task)
    return _to_task_response(task, db)


@router.get("/", response_model=List[TaskResponse], status_code=status.HTTP_200_OK)
def list_tasks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List tasks. Founders see all tasks; employees see tasks assigned to them."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    if role_val == "founder":
        tasks = db.execute(select(Task).order_by(Task.created_at.desc())).scalars().all()
    else:
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp:
            return []
        tasks = (
            db.execute(
                select(Task)
                .join(TaskAssignment, TaskAssignment.task_id == Task.id)
                .where(TaskAssignment.employee_id == emp.id)
                .order_by(Task.created_at.desc())
            )
            .scalars()
            .all()
        )

    return [_to_task_response(t, db) for t in tasks]


@router.get("/{id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def get_task(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve task details, enforcing role and assignment visibility."""
    task = db.execute(select(Task).where(Task.id == id)).scalar_one_or_none()
    if not task:
        raise NotFoundError("Task not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "founder":
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp:
            raise AuthorizationError("Access denied")
        is_assigned = db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == id, TaskAssignment.employee_id == emp.id
            )
        ).scalar_one_or_none()
        if not is_assigned:
            raise AuthorizationError("Access denied: You are not assigned to this task")

    return _to_task_response(task, db)


@router.patch("/{id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(
    id: str,
    payload: TaskUpdateSchema,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Update task metadata (Founder only)."""
    task = db.execute(select(Task).where(Task.id == id)).scalar_one_or_none()
    if not task:
        raise NotFoundError("Task not found")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.project_id is not None:
        task.project_id = payload.project_id
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.start_date is not None:
        task.start_date = payload.start_date
    if payload.deadline is not None:
        task.deadline = payload.deadline
    if payload.instructions is not None:
        task.instructions = payload.instructions

    db.commit()
    db.refresh(task)
    return _to_task_response(task, db)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_task(
    id: str,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Delete a task and its dependent assignments, comments, and checklist items."""
    task = db.execute(select(Task).where(Task.id == id)).scalar_one_or_none()
    if not task:
        raise NotFoundError("Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


@router.patch("/assignments/{id}", response_model=AssignmentResponse, status_code=status.HTTP_200_OK)
def update_assignment_progress(
    id: str,
    payload: TaskAssignmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update task assignment status or progress percentage (Employee on own assignment)."""
    assignment = (
        db.execute(
            select(TaskAssignment)
            .where(TaskAssignment.id == id)
            .options(
                joinedload(TaskAssignment.employee),
                joinedload(TaskAssignment.task),
            )
        )
        .scalar_one_or_none()
    )
    if not assignment:
        raise NotFoundError("Task assignment not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    previous_status = (
        assignment.status.value
        if hasattr(assignment.status, "value")
        else str(assignment.status)
    )
    if role_val != "founder":
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if not emp or assignment.employee_id != emp.id:
            raise AuthorizationError("You can only modify your own assignment")

    if payload.status is not None:
        assignment.status = payload.status
        if payload.status == AssignmentStatus.completed:
            assignment.completed_at = datetime.now(timezone.utc)
            assignment.progress_percent = 100

    if payload.progress_percent is not None:
        assignment.progress_percent = payload.progress_percent
        if payload.progress_percent == 100 and assignment.status != AssignmentStatus.completed:
            assignment.status = AssignmentStatus.completed
            assignment.completed_at = datetime.now(timezone.utc)

    # Record TaskUpdate
    status_str = assignment.status.value if hasattr(assignment.status, "value") else str(assignment.status)
    if (
        role_val == "employee"
        and status_str in ("completed", "submitted")
        and previous_status not in ("completed", "submitted")
    ):
        employee_name = assignment.employee.full_name if assignment.employee else "An employee"
        task_title = assignment.task.title if assignment.task else "a task"
        NotificationService.add_to_founders(
            db=db,
            title=f"Task completed: {task_title}",
            message=f"{employee_name} marked the task as {status_str}.",
            type="success",
            reference_id=assignment.task_id,
            reference_type="task",
        )
    update_log = TaskUpdate(
        assignment_id=assignment.id,
        status=status_str,
        progress_percent=assignment.progress_percent,
        note=payload.note,
        created_by=current_user.id,
    )
    db.add(update_log)
    db.commit()
    db.refresh(assignment)

    emp_name = assignment.employee.full_name if assignment.employee else "Unknown"
    return AssignmentResponse(
        id=assignment.id,
        employee_id=assignment.employee_id,
        employee_name=emp_name,
        status=status_str,
        progress_percent=assignment.progress_percent,
        submitted_at=assignment.submitted_at,
        completed_at=assignment.completed_at,
    )


@router.post("/{id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
def add_task_comment(
    id: str,
    payload: TaskCommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add discussion comment to task."""
    task = db.execute(select(Task).where(Task.id == id)).scalar_one_or_none()
    if not task:
        raise NotFoundError("Task not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_founder = (role_val == "founder")

    emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
    if not is_founder and not emp:
        raise AuthorizationError("Access denied")

    emp_id = emp.id if emp else None
    commenter_name = "Founder" if is_founder else emp.full_name

    comment = TaskComment(
        task_id=id,
        employee_id=emp_id,
        content=payload.content,
        is_founder_comment=is_founder,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return TaskCommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        employee_id=emp_id or "founder",
        employee_name=commenter_name,
        content=comment.content,
        is_founder_comment=comment.is_founder_comment,
        created_at=comment.created_at,
    )


@router.post("/{id}/submit", response_model=AssignmentResponse, status_code=status.HTTP_200_OK)
def submit_task_assignment(
    id: str,
    payload: TaskSubmitRequest,
    employee: Employee = Depends(get_employee_from_user),
    db: Session = Depends(get_db),
):
    """Submit completed work for review on a task assignment."""
    assignment = (
        db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == id,
                TaskAssignment.employee_id == employee.id,
            )
            .options(joinedload(TaskAssignment.task))
        )
        .scalar_one_or_none()
    )
    if not assignment:
        raise NotFoundError("No assignment found for this task")

    previous_status = (
        assignment.status.value
        if hasattr(assignment.status, "value")
        else str(assignment.status)
    )
    now = datetime.now(timezone.utc)
    assignment.status = AssignmentStatus.submitted
    assignment.submitted_at = now
    assignment.progress_percent = 100

    update_log = TaskUpdate(
        assignment_id=assignment.id,
        status="submitted",
        progress_percent=100,
        note=payload.note,
        created_by=employee.user_id,
    )
    db.add(update_log)
    if previous_status not in ("completed", "submitted"):
        task_title = assignment.task.title if assignment.task else "a task"
        NotificationService.add_to_founders(
            db=db,
            title=f"Task completed: {task_title}",
            message=f"{employee.full_name} submitted the task for review.",
            type="success",
            reference_id=assignment.task_id,
            reference_type="task",
        )
    db.commit()
    db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        employee_id=assignment.employee_id,
        employee_name=employee.full_name,
        status="submitted",
        progress_percent=100,
        submitted_at=assignment.submitted_at,
        completed_at=assignment.completed_at,
    )
