from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.activity import ActivityLog


class ActivityService:
    """Service recording and querying user and employee activity events."""

    @staticmethod
    def log_activity(
        db: Session,
        event_type: str,
        user_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> ActivityLog:
        """Create and store activity log record."""
        log = ActivityLog(
            user_id=user_id,
            employee_id=employee_id,
            event_type=event_type,
            event_data=event_data,
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_recent_activity(
        db: Session,
        limit: int = 50,
    ) -> List[ActivityLog]:
        """Fetch chronological recent activities with user and employee details."""
        stmt = (
            select(ActivityLog)
            .options(joinedload(ActivityLog.user), joinedload(ActivityLog.employee))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())
