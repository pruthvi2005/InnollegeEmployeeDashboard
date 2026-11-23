import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half_day"
    on_leave = "on_leave"
    holiday = "holiday"


class Attendance(Base, UUIDMixin, TimestampMixin):
    """Daily employee attendance record."""

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )

    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=True)  # Stored in UTC
    check_out_time = Column(DateTime, nullable=True)  # Stored in UTC
    working_hours = Column(Numeric(5, 2), nullable=True)
    status = Column(
        SAEnum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AttendanceStatus.absent,
        index=True,
    )
    is_late = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="attendance_records")
    events = relationship(
        "AttendanceEvent", back_populates="attendance", cascade="all, delete-orphan"
    )
    adjustments = relationship(
        "AttendanceAdjustment", back_populates="attendance", cascade="all, delete-orphan"
    )


class AttendanceEvent(Base, UUIDMixin):
    """Specific check-in / check-out telemetry event."""

    __tablename__ = "attendance_events"

    attendance_id = Column(
        String(36),
        ForeignKey("attendance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(50), nullable=False)  # check_in, check_out
    timestamp = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    attendance = relationship("Attendance", back_populates="events")


class AttendanceAdjustment(Base, UUIDMixin, TimestampMixin):
    """Adjustment request for regularization of attendance records."""

    __tablename__ = "attendance_adjustments"

    attendance_id = Column(
        String(36),
        ForeignKey("attendance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected
    reviewed_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = Column(DateTime, nullable=True)

    attendance = relationship("Attendance", back_populates="adjustments")
    requester = relationship("User", foreign_keys=[requested_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
