from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin


class Notification(Base, UUIDMixin):
    """User notification alerts and messages."""

    __tablename__ = "notifications"

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(100), nullable=False, index=True)
    reference_id = Column(String(36), nullable=True, index=True)
    reference_type = Column(String(100), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="notifications")
