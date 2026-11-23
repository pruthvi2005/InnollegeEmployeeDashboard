from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "jyohar_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.deadline_checker"],
)

celery_app.conf.update(
    timezone=settings.COMPANY_TIMEZONE,
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule={
        "check_overdue_tasks_hourly": {
            "task": "app.workers.deadline_checker.check_overdue_tasks",
            "schedule": 3600.0,  # Run every 1 hour
        },
        "send_deadline_reminders_daily_9am": {
            "task": "app.workers.deadline_checker.send_deadline_reminders",
            "schedule": crontab(hour=9, minute=0),  # 9:00 AM IST daily
        },
    },
)
