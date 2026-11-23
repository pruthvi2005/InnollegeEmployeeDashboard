import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    submitted = "submitted"
    under_review = "under_review"
    completed = "completed"
    revision_required = "revision_required"
    overdue = "overdue"


class Task(Base, UUIDMixin, TimestampMixin):
    """Core Task definition created by founders/management."""

    __tablename__ = "tasks"

    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    priority = Column(
        SAEnum(TaskPriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskPriority.medium,
        index=True,
    )
    start_date = Column(Date, nullable=True)
    deadline = Column(DateTime, nullable=True, index=True)
    instructions = Column(Text, nullable=True)
    created_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    project = relationship("Project", back_populates="tasks")
    creator = relationship("User", foreign_keys=[created_by])
    assignments = relationship(
        "TaskAssignment", back_populates="task", cascade="all, delete-orphan"
    )
    comments = relationship(
        "TaskComment", back_populates="task", cascade="all, delete-orphan"
    )
    checklists = relationship(
        "TaskChecklist", back_populates="task", cascade="all, delete-orphan"
    )
    files = relationship(
        "TaskFile", back_populates="task", cascade="all, delete-orphan"
    )


class TaskAssignment(Base, UUIDMixin):
    """Employee assignment tracking for an individual task."""

    __tablename__ = "task_assignments"
    __table_args__ = (
        UniqueConstraint("task_id", "employee_id", name="uq_task_assignments_task_employee"),
    )

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        SAEnum(AssignmentStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AssignmentStatus.pending,
        index=True,
    )
    progress_percent = Column(Integer, default=0, nullable=False)
    assigned_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="assignments")
    employee = relationship("Employee", back_populates="task_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    updates = relationship(
        "TaskUpdate", back_populates="assignment", cascade="all, delete-orphan"
    )


class TaskUpdate(Base, UUIDMixin):
    """Progress update log for task assignments."""

    __tablename__ = "task_updates"

    assignment_id = Column(
        String(36),
        ForeignKey("task_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(50), nullable=False)
    progress_percent = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    created_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    assignment = relationship("TaskAssignment", back_populates="updates")
    author = relationship("User", foreign_keys=[created_by])


class TaskComment(Base, UUIDMixin, TimestampMixin):
    """Collaboration discussion thread on a task."""

    __tablename__ = "task_comments"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    content = Column(Text, nullable=False)
    is_founder_comment = Column(Boolean, default=False, nullable=False)

    task = relationship("Task", back_populates="comments")
    employee = relationship("Employee")


class TaskChecklist(Base, UUIDMixin):
    """Actionable checklist items associated with a task."""

    __tablename__ = "task_checklists"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_text = Column(String(1000), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    task = relationship("Task", back_populates="checklists")
    completer = relationship("User", foreign_keys=[completed_by])
