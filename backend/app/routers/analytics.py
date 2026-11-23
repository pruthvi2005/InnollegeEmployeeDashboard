from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.analytics import OverviewStats, AttendanceAnalytics, TaskAnalytics
from app.services.analytics_service import AnalyticsService
from app.dependencies import require_founder

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewStats, status_code=status.HTTP_200_OK)
def get_overview_analytics(
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Retrieve executive overview metrics and KPIs (Founder only)."""
    return AnalyticsService.get_overview_stats(db=db)


@router.get("/attendance", response_model=AttendanceAnalytics, status_code=status.HTTP_200_OK)
def get_attendance_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Retrieve aggregate attendance distribution metrics (Founder only)."""
    return AnalyticsService.get_attendance_analytics(
        db=db, start_date=start_date, end_date=end_date
    )


@router.get("/tasks", response_model=TaskAnalytics, status_code=status.HTTP_200_OK)
def get_tasks_analytics(
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Retrieve task completion efficiency metrics (Founder only)."""
    return AnalyticsService.get_task_analytics(db=db)


@router.get("/employees/{id}/performance", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_employee_performance_metrics(
    id: str,
    founder: User = Depends(require_founder),
    db: Session = Depends(get_db),
):
    """Retrieve single employee performance statistics (Founder only)."""
    return AnalyticsService.get_employee_performance(db=db, employee_id=id)
