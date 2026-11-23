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
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class LeaveRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class LeaveType(Base, UUIDMixin, TimestampMixin):
    """Categorization of leaves (e.g. Annual, Sick, Casual, Unpaid)."""

    __tablename__ = "leave_types"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    days_per_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    leave_requests = relationship("LeaveRequest", back_populates="leave_type")


class LeaveRequest(Base, UUIDMixin, TimestampMixin):
    """Leave application filed by an employee."""

    __tablename__ = "leave_requests"

    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leave_type_id = Column(
        String(36),
        ForeignKey("leave_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(
        SAEnum(LeaveRequestStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=LeaveRequestStatus.pending,
        index=True,
    )

    employee = relationship("Employee", back_populates="leave_requests")
    leave_type = relationship("LeaveType", back_populates="leave_requests")
    actions = relationship(
        "LeaveAction", back_populates="leave_request", cascade="all, delete-orphan"
    )


class LeaveAction(Base, UUIDMixin):
    """Workflow decision log on a leave application."""

    __tablename__ = "leave_actions"

    leave_request_id = Column(
        String(36),
        ForeignKey("leave_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action = Column(String(50), nullable=False)  # approved, rejected, cancelled
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    leave_request = relationship("LeaveRequest", back_populates="actions")
    action_user = relationship("User", foreign_keys=[action_by])
