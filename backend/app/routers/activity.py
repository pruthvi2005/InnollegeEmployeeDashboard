from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_founder
from app.models.user import User
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activities", tags=["Activity"])


@router.get("/recent")
def get_recent_activity(
    limit: int = Query(50, ge=1, le=100),
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict[str, Any]]]:
    events = ActivityService.get_recent_activity(db=db, limit=limit)
    return {
        "items": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "actor_name": (
                    event.employee.full_name
                    if event.employee
                    else event.user.email if event.user else "System"
                ),
                "created_at": event.created_at.isoformat(),
                "event_data": event.event_data or {},
            }
            for event in events
        ]
    }
