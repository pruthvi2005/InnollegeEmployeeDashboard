import uuid
from typing import Generator
from sqlalchemy import create_engine, MetaData, Column, CHAR, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase

from app.config import settings

# Explicit constraint naming convention for consistent Alembic migrations
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 DeclarativeBase."""
    metadata = metadata


class UUIDMixin:
    """Mixin for UUID CHAR(36) primary key."""
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)


class TimestampMixin:
    """Mixin for UTC audit timestamps."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
