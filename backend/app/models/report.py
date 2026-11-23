import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class ReportStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    reviewed = "reviewed"


class DailyReport(Base, UUIDMixin, TimestampMixin):
    """End-of-day report submitted by employees."""

    __tablename__ = "daily_reports"
    __table_args__ = (
        UniqueConstraint("employee_id", "report_date", name="uq_daily_reports_employee_date"),
    )

    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_date = Column(Date, nullable=False, index=True)
    completed_work = Column(Text, nullable=True)
    pending_work = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    tomorrow_plan = Column(Text, nullable=True)
    total_hours_worked = Column(Numeric(5, 2), nullable=True)
    status = Column(
        SAEnum(ReportStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ReportStatus.draft,
        index=True,
    )
    founder_feedback = Column(Text, nullable=True)
    reviewed_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="daily_reports")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    task_items = relationship(
        "DailyReportTask", back_populates="report", cascade="all, delete-orphan"
    )
    files = relationship(
        "ReportFile", back_populates="report", cascade="all, delete-orphan"
    )


class DailyReportTask(Base, UUIDMixin):
    """Individual line item task breakdown in a daily report."""

    __tablename__ = "daily_report_tasks"

    report_id = Column(
        String(36),
        ForeignKey("daily_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_description = Column(String(1000), nullable=False)
    time_spent_hours = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    report = relationship("DailyReport", back_populates="task_items")
    task = relationship("Task")
