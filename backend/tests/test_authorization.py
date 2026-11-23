from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, timezone

from app.models.employee import Employee
from app.models.leave import LeaveType, LeaveRequest, LeaveRequestStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import AuthSession
from app.core.security import verify_password
from app.services.analytics_service import AnalyticsService


def test_employee_cannot_create_employee(test_client: TestClient, employee_token: str):
    """Test RBAC blocks employee role from provisioning new employees."""
    response = test_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "email": "hacker@jyohartech.com",
            "full_name": "Unauthorized User",
            "password": "Password123!",
        },
    )
    assert response.status_code == 403


def test_employee_cannot_view_all_attendance(test_client: TestClient, employee_token: str):
    """Test RBAC blocks employee from accessing company-wide attendance directory."""
    response = test_client.get(
        "/api/v1/attendance/",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 403


def test_employee_cannot_view_analytics(test_client: TestClient, employee_token: str):
    """Test RBAC blocks employee from accessing executive analytics."""
    response = test_client.get(
        "/api/v1/analytics/overview",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 403


def test_founder_can_create_employee(test_client: TestClient, founder_token: str):
    """Test founder can provision new employee records."""
    response = test_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {founder_token}"},
        json={
            "email": "rahul.verma@jyohartech.com",
            "full_name": "Rahul Verma",
            "password": "TemporaryPassword123!",
            "designation": "Backend Developer",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "rahul.verma@jyohartech.com"
    assert data["full_name"] == "Rahul Verma"
    assert data["employee_id"].startswith("JT-")
    assert "password_hash" not in data


def test_founder_can_reset_employee_password_and_revoke_sessions(
    test_client: TestClient,
    test_db: Session,
    test_employee: Employee,
    founder_token: str,
):
    session = AuthSession(
        user_id=test_employee.user_id,
        refresh_token_hash="employee-refresh-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_revoked=False,
    )
    test_db.add(session)
    test_db.commit()

    response = test_client.patch(
        f"/api/v1/employees/{test_employee.id}/password",
        headers={"Authorization": f"Bearer {founder_token}"},
        json={"new_password": "NewEmployeePassword123!"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Employee password reset successfully."}
    test_db.refresh(test_employee.user)
    test_db.refresh(session)
    assert verify_password("NewEmployeePassword123!", test_employee.user.password_hash)
    assert session.is_revoked is True
    login = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_employee.user.email,
            "password": "NewEmployeePassword123!",
        },
    )
    assert login.status_code == 200
    assert login.json()["role"] == "employee"


def test_employee_cannot_reset_an_employee_password(
    test_client: TestClient,
    test_employee: Employee,
    employee_token: str,
):
    response = test_client.patch(
        f"/api/v1/employees/{test_employee.id}/password",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={"new_password": "NewEmployeePassword123!"},
    )

    assert response.status_code == 403


def test_founder_can_view_analytics(
    test_client: TestClient,
    test_db: Session,
    founder_token: str,
    test_employee: Employee,
):
    """Test founder can query overview analytics dashboard."""
    today = AnalyticsService._get_current_company_date()
    test_db.add(
        Attendance(
            employee_id=test_employee.id,
            work_date=today,
            status=AttendanceStatus.present,
        )
    )
    test_db.commit()

    response = test_client.get(
        "/api/v1/analytics/overview",
        headers={"Authorization": f"Bearer {founder_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_employees" in data
    assert "present_today" in data
    assert "active_projects" in data
    assert len(data["attendance_chart"]) == 7
    today_point = next(point for point in data["attendance_chart"] if point["date"] == today.isoformat())
    assert today_point == {"date": today.isoformat(), "present": 1, "absent": 0, "leave": 0}


def test_employee_cannot_approve_own_leave(
    test_client: TestClient,
    test_db: Session,
    employee_token: str,
    test_employee: Employee,
):
    """Test employee cannot approve or reject leave requests."""
    # Create a leave type and leave request
    leave_type = LeaveType(name="Sick Leave Test", days_per_year=10)
    test_db.add(leave_type)
    test_db.flush()

    leave_req = LeaveRequest(
        employee_id=test_employee.id,
        leave_type_id=leave_type.id,
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 2),
        total_days=2,
        reason="Feeling unwell",
        status=LeaveRequestStatus.pending,
    )
    test_db.add(leave_req)
    test_db.commit()
    test_db.refresh(leave_req)

    # Employee attempts to self-approve
    response = test_client.patch(
        f"/api/v1/leaves/{leave_req.id}/decision",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={"action": "approved", "comment": "Self approval attempt"},
    )
    assert response.status_code == 403
