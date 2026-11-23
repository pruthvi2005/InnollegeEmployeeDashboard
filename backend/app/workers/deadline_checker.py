import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.task import Task, TaskAssignment, AssignmentStatus
from app.models.notification import Notification
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.deadline_checker.check_overdue_tasks")
def check_overdue_tasks() -> int:
    """Identify tasks past their deadline and transition assignments to overdue status."""
    db = SessionLocal()
    updated_count = 0
    now = datetime.now(timezone.utc)

    try:
        stmt = (
            select(TaskAssignment)
            .join(Task, TaskAssignment.task_id == Task.id)
            .options(
                joinedload(TaskAssignment.task),
                joinedload(TaskAssignment.employee),
            )
            .where(
                Task.deadline.is_not(None),
                Task.deadline < now,
                TaskAssignment.status.not_in([
                    AssignmentStatus.completed,
                    AssignmentStatus.revision_required,
                    AssignmentStatus.overdue,
                ]),
            )
        )
        assignments = db.execute(stmt).scalars().all()

        for a in assignments:
            a.status = AssignmentStatus.overdue
            updated_count += 1

            if a.employee and a.employee.user_id:
                notif = Notification(
                    user_id=a.employee.user_id,
                    title=f"Task Overdue: {a.task.title}",
                    message=f"The deadline for task '{a.task.title}' has passed.",
                    type="task_overdue",
                    reference_id=a.task_id,
                    reference_type="task",
                    is_read=False,
                )
                db.add(notif)

        db.commit()
        logger.info("Marked %d assignments as overdue.", updated_count)
        return updated_count
    except Exception as e:
        db.rollback()
        logger.error("Error checking overdue tasks: %s", e)
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.deadline_checker.send_deadline_reminders")
def send_deadline_reminders() -> int:
    """Send reminder notifications for tasks due within the upcoming 24 hours."""
    db = SessionLocal()
    reminded_count = 0
    now = datetime.now(timezone.utc)
    in_24h = now + timedelta(hours=24)

    try:
        stmt = (
            select(TaskAssignment)
            .join(Task, TaskAssignment.task_id == Task.id)
            .options(
                joinedload(TaskAssignment.task),
                joinedload(TaskAssignment.employee),
            )
            .where(
                Task.deadline.is_not(None),
                Task.deadline >= now,
                Task.deadline <= in_24h,
                TaskAssignment.status != AssignmentStatus.completed,
            )
        )
        assignments = db.execute(stmt).scalars().all()

        for a in assignments:
            if a.employee and a.employee.user_id:
                notif = Notification(
                    user_id=a.employee.user_id,
                    title=f"Deadline Approaching: {a.task.title}",
                    message=f"Task '{a.task.title}' is due within 24 hours.",
                    type="deadline_approaching",
                    reference_id=a.task_id,
                    reference_type="task",
                    is_read=False,
                )
                db.add(notif)
                reminded_count += 1

        db.commit()
        logger.info("Sent %d deadline reminders.", reminded_count)
        return reminded_count
    except Exception as e:
        db.rollback()
        logger.error("Error sending deadline reminders: %s", e)
        raise
    finally:
        db.close()
