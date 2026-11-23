import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class ProjectStatus(str, enum.Enum):
    planning = "planning"
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    archived = "archived"


class Project(Base, UUIDMixin, TimestampMixin):
    """Company project management model."""

    __tablename__ = "projects"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(ProjectStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProjectStatus.planning,
        index=True,
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator = relationship("User", foreign_keys=[created_by])
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    tasks = relationship("Task", back_populates="project")


class ProjectMember(Base, UUIDMixin):
    """Association table linking employees to projects with assigned role."""

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "employee_id", name="uq_project_members_project_employee"),
    )

    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(100), nullable=True)
    joined_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="members")
    employee = relationship("Employee", back_populates="project_members")
