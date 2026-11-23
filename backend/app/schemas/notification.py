from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Notification response model."""
    id: str
    title: str
    message: str
    type: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """List of notifications with unread count."""
    items: List[NotificationResponse]
    unread_count: int
