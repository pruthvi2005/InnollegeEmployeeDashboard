import enum
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    founder = "founder"
    employee = "employee"


class User(Base, UUIDMixin, TimestampMixin):
    """User account model supporting founder and employee credentials."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(
        SAEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.employee,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    auth_sessions = relationship(
        "AuthSession", back_populates="user", cascade="all, delete-orphan"
    )
    otp_challenges = relationship(
        "OtpChallenge", back_populates="user", cascade="all, delete-orphan"
    )
    login_events = relationship(
        "LoginEvent", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    employee = relationship(
        "Employee",
        back_populates="user",
        uselist=False,
        foreign_keys="Employee.user_id",
    )


class AuthSession(Base, UUIDMixin, TimestampMixin):
    """Track active user authentication sessions and refresh tokens."""

    __tablename__ = "auth_sessions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="auth_sessions")


class OtpChallenge(Base, UUIDMixin):
    """Store OTP verification challenges for passwordless/phone login."""

    __tablename__ = "otp_challenges"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    otp_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="otp_challenges")


class LoginEvent(Base, UUIDMixin):
    """Audit log of authentication attempts and events."""

    __tablename__ = "login_events"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # login_success, login_failed, logout, token_refresh, otp_requested, otp_verified
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="login_events")
