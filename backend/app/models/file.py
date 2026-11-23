from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base, UUIDMixin


class File(Base, UUIDMixin):
    """File storage metadata for attachments stored in S3/MinIO."""

    __tablename__ = "files"

    original_filename = Column(String(500), nullable=False)
    storage_key = Column(String(1000), nullable=False, unique=True)
    content_type = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    uploader = relationship("User")
    task_files = relationship("TaskFile", back_populates="file", cascade="all, delete-orphan")
    report_files = relationship("ReportFile", back_populates="file", cascade="all, delete-orphan")


class TaskFile(Base, UUIDMixin):
    """Attachment file mapping to a Task."""

    __tablename__ = "task_files"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id = Column(
        String(36),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    task = relationship("Task", back_populates="files")
    file = relationship("File", back_populates="task_files")
    uploader = relationship("User")


class ReportFile(Base, UUIDMixin):
    """Attachment file mapping to a DailyReport."""

    __tablename__ = "report_files"

    report_id = Column(
        String(36),
        ForeignKey("daily_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id = Column(
        String(36),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    report = relationship("DailyReport", back_populates="files")
    file = relationship("File", back_populates="report_files")
    uploader = relationship("User")
