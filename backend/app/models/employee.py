from sqlalchemy import (
    Column,
    String,
    Boolean,
    Date,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class Employee(Base, UUIDMixin, TimestampMixin):
    """Employee record linked to a User account."""

    __tablename__ = "employees"

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    department_id = Column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    designation = Column(String(255), nullable=True)
    joining_date = Column(Date, nullable=True)
    profile_photo_url = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="employee",
        foreign_keys=[user_id],
    )
    department = relationship("Department", back_populates="employees")
    created_by_user = relationship("User", foreign_keys=[created_by])
    profile = relationship(
        "EmployeeProfile",
        back_populates="employee",
        uselist=False,
        cascade="all, delete-orphan",
    )
    project_members = relationship("ProjectMember", back_populates="employee")
    task_assignments = relationship("TaskAssignment", back_populates="employee")
    attendance_records = relationship("Attendance", back_populates="employee")
    daily_reports = relationship("DailyReport", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")


class EmployeeProfile(Base, UUIDMixin, TimestampMixin):
    """Extended confidential profile for an employee."""

    __tablename__ = "employee_profiles"

    employee_id = Column(
        String(36),
        ForeignKey("employees.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    bank_account = Column(String(50), nullable=True)  # Application-level encrypted
    notes = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="profile")
