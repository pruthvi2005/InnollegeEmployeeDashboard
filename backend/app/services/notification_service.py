from typing import Iterable, List, Tuple, Optional
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundError, AuthorizationError


class NotificationService:
    """Service managing user notifications and read states."""

    @staticmethod
    def add_notifications(
        db: Session,
        user_ids: Iterable[str],
        title: str,
        message: str,
        type: str,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> List[Notification]:
        """Add notifications to the caller's transaction for the selected users."""
        notifications = [
            Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=type,
                reference_id=reference_id,
                reference_type=reference_type,
                is_read=False,
            )
            for user_id in set(user_ids)
        ]
        db.add_all(notifications)
        return notifications

    @staticmethod
    def add_to_founders(
        db: Session,
        title: str,
        message: str,
        type: str,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> List[Notification]:
        """Notify every active founder account in the same transaction."""
        founder_ids = db.execute(
            select(User.id).where(
                User.role == UserRole.founder,
                User.is_active == True,  # noqa: E712
            )
        ).scalars().all()
        return NotificationService.add_notifications(
            db=db,
            user_ids=founder_ids,
            title=title,
            message=message,
            type=type,
            reference_id=reference_id,
            reference_type=reference_type,
        )

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        title: str,
        message: str,
        type: str,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> Notification:
        """Create and persist a new notification record."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Notification], int]:
        """Fetch notifications for a user along with total unread count."""
        # Unread count
        unread_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        unread_count = db.execute(unread_stmt).scalar() or 0

        # Items paginated
        offset = max(0, (page - 1) * page_size)
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = db.execute(query).scalars().all()

        return list(items), unread_count

    @staticmethod
    def mark_read(
        db: Session,
        notification_id: str,
        user_id: str,
    ) -> Notification:
        """Mark a single notification as read, ensuring ownership."""
        stmt = select(Notification).where(Notification.id == notification_id)
        notification = db.execute(stmt).scalar_one_or_none()

        if not notification:
            raise NotFoundError("Notification not found")

        if notification.user_id != user_id:
            raise AuthorizationError("Access to notification denied")

        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_read(
        db: Session,
        user_id: str,
    ) -> int:
        """Mark all unread notifications for a user as read."""
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount or 0
