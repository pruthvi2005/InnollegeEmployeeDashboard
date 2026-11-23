from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.services.notification_service import NotificationService
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListResponse, status_code=status.HTTP_200_OK)
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve personal notifications list with unread counter."""
    items, unread_count = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        unread_count=unread_count,
    )


@router.patch("/{id}/read", response_model=NotificationResponse, status_code=status.HTTP_200_OK)
def mark_notification_read(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    notification = NotificationService.mark_read(
        db=db,
        notification_id=id,
        user_id=current_user.id,
    )
    return NotificationResponse.model_validate(notification)


@router.patch("/mark-all-read", status_code=status.HTTP_200_OK)
@router.patch("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark all unread notifications as read."""
    count = NotificationService.mark_all_read(db=db, user_id=current_user.id)
    return {"message": "All notifications marked as read", "updated_count": count}
