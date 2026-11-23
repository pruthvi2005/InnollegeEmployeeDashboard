from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class Department(Base, UUIDMixin, TimestampMixin):
    """Company department classification."""

    __tablename__ = "departments"

    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    employees = relationship("Employee", back_populates="department")
