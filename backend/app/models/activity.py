from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin


class ActivityLog(Base, UUIDMixin):
    """System activity log for tracking user actions and business events."""

    __tablename__ = "activity_logs"

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    user = relationship("User")
    employee = relationship("Employee")


class AuditLog(Base, UUIDMixin):
    """Immutable audit trail for critical resource mutations and compliance."""

    __tablename__ = "audit_logs"

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    user = relationship("User")
