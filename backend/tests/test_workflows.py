from datetime import datetime

import pytz
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.employee import Employee
from app.models.leave import LeaveType
from app.models.notification import Notification
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


def test_employee_check_in_and_check_out_work(
    test_client: TestClient,
    employee_token: str,
):
    headers = {"Authorization": f"Bearer {employee_token}"}

    check_in = test_client.post("/api/v1/attendance/check-in", headers=headers, json={})
    assert check_in.status_code == 200
    assert check_in.json()["check_in_time"]

    today = test_client.get("/api/v1/attendance/today", headers=headers)
    assert today.status_code == 200
    assert today.json()["status"] == "present"

    check_out = test_client.post("/api/v1/attendance/check-out", headers=headers, json={})
    assert check_out.status_code == 200
    assert check_out.json()["check_out_time"]

    history = test_client.get("/api/v1/attendance/me", headers=headers)
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1


def test_employee_can_submit_and_read_daily_report(
    test_client: TestClient,
    employee_token: str,
):
    headers = {"Authorization": f"Bearer {employee_token}"}
    today = datetime.now(pytz.timezone(settings.COMPANY_TIMEZONE)).date().isoformat()
    response = test_client.post(
        "/api/v1/reports/",
        headers=headers,
        json={
            "report_date": today,
            "completed_work": "Completed the assigned work",
            "total_hours_worked": 7.5,
            "task_items": [],
            "status": "submitted",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "submitted"

    today_status = test_client.get("/api/v1/reports/today", headers=headers)
    assert today_status.status_code == 200
    assert today_status.json()["status"] == "submitted"

    reports = test_client.get("/api/v1/reports/", headers=headers)
    assert reports.status_code == 200
    assert len(reports.json()) == 1


def test_task_notifications_only_go_to_assignees_and_founders(
    test_client: TestClient,
    test_db: Session,
    founder_token: str,
    founder_user: User,
    test_employee: Employee,
    employee_token: str,
):
    other_user = User(
        email="other-employee@jyohartech.com",
        role="employee",
        is_active=True,
    )
    test_db.add(other_user)
    test_db.flush()
    other_employee = Employee(
        user_id=other_user.id,
        employee_id="JT-002",
        full_name="Other Employee",
        is_active=True,
        created_by=founder_user.id,
    )
    test_db.add(other_employee)
    test_db.commit()

    created = test_client.post(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {founder_token}"},
        json={
            "title": "Notify assigned employee",
            "assigned_employee_ids": [test_employee.id],
        },
    )
    assert created.status_code == 201

    assigned_notice = test_db.execute(
        select(Notification).where(
            Notification.user_id == test_employee.user_id,
            Notification.reference_id == created.json()["id"],
            Notification.reference_type == "task",
        )
    ).scalar_one()
    assert assigned_notice.title == "New task assigned: Notify assigned employee"
    assert test_db.execute(
        select(Notification).where(
            Notification.user_id == other_user.id,
            Notification.reference_id == created.json()["id"],
        )
    ).scalar_one_or_none() is None

    assignment_id = created.json()["assignments"][0]["id"]
    completed = test_client.patch(
        f"/api/v1/tasks/assignments/{assignment_id}",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={"status": "completed"},
    )
    assert completed.status_code == 200

    founder_notice = test_db.execute(
        select(Notification).where(
            Notification.user_id == founder_user.id,
            Notification.reference_id == created.json()["id"],
            Notification.title == "Task completed: Notify assigned employee",
        )
    ).scalar_one()
    assert "Pooja Sharma" in founder_notice.message


def test_employee_can_request_leave_and_founder_can_decide(
    test_client: TestClient,
    test_db: Session,
    founder_user: User,
    test_employee: Employee,
    employee_token: str,
    founder_token: str,
):
    leave_type = LeaveType(name="Workflow Test Leave", days_per_year=5)
    test_db.add(leave_type)
    test_db.commit()
    test_db.refresh(leave_type)

    created = test_client.post(
        "/api/v1/leaves/",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type_id": leave_type.id,
            "start_date": "2026-12-10",
            "end_date": "2026-12-11",
            "reason": "Personal appointment",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    founder_notice = test_db.execute(
        select(Notification).where(
            Notification.user_id == founder_user.id,
            Notification.reference_id == created.json()["id"],
            Notification.reference_type == "leave",
        )
    ).scalar_one()
    assert founder_notice.title == "Leave request from Pooja Sharma"

    decision = test_client.patch(
        f"/api/v1/leaves/{created.json()['id']}/decision",
        headers={"Authorization": f"Bearer {founder_token}"},
        json={"action": "approved", "comment": "Approved"},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"

    employee_leave_notice = test_db.execute(
        select(Notification).where(
            Notification.user_id == test_employee.user_id,
            Notification.reference_id == created.json()["id"],
            Notification.reference_type == "leave",
        )
    ).scalar_one()
    assert employee_leave_notice.title == "Leave request approved"


def test_submitted_report_notifies_founders_and_review_notifies_employee(
    test_client: TestClient,
    test_db: Session,
    founder_user: User,
    founder_token: str,
    test_employee: Employee,
    employee_token: str,
):
    today = datetime.now(pytz.timezone(settings.COMPANY_TIMEZONE)).date().isoformat()
    submitted = test_client.post(
        "/api/v1/reports/",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "report_date": today,
            "completed_work": "Completed the assigned work",
            "total_hours_worked": 7.5,
            "task_items": [],
            "status": "submitted",
        },
    )
    assert submitted.status_code == 201

    founder_notice = test_db.execute(
        select(Notification).where(
            Notification.user_id == founder_user.id,
            Notification.reference_id == submitted.json()["id"],
            Notification.reference_type == "report",
        )
    ).scalar_one()
    assert "Pooja Sharma" in founder_notice.title

    reviewed = test_client.patch(
        f"/api/v1/reports/{submitted.json()['id']}/review",
        headers={"Authorization": f"Bearer {founder_token}"},
        json={"founder_feedback": "Well done"},
    )
    assert reviewed.status_code == 200
    employee_notice = test_db.execute(
        select(Notification).where(
            Notification.user_id == test_employee.user_id,
            Notification.reference_id == submitted.json()["id"],
            Notification.title == "Daily report reviewed",
        )
    ).scalar_one()
    assert "Well done" in employee_notice.message


def test_employee_delete_removes_employee_and_user(
    test_client: TestClient,
    test_db: Session,
    founder_token: str,
):
    created = test_client.post(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {founder_token}"},
        json={
            "email": "delete-me@jyohartech.com",
            "full_name": "Delete Me",
            "password": "TemporaryPassword123!",
        },
    )
    assert created.status_code == 201
    employee_id = created.json()["id"]
    user_id = created.json()["user_id"]

    deleted = test_client.delete(
        f"/api/v1/employees/{employee_id}",
        headers={"Authorization": f"Bearer {founder_token}"},
    )
    assert deleted.status_code == 200
    assert test_db.get(Employee, employee_id) is None
    assert test_db.get(User, user_id) is None


def test_department_assignment_is_reflected_in_active_employee_count(
    test_client: TestClient,
    founder_token: str,
):
    headers = {"Authorization": f"Bearer {founder_token}"}
    department = test_client.post(
        "/api/v1/departments/",
        headers=headers,
        json={"name": "Workflow Department"},
    )
    assert department.status_code == 201

    employee = test_client.post(
        "/api/v1/employees/",
        headers=headers,
        json={
            "email": "department-member@jyohartech.com",
            "full_name": "Department Member",
            "password": "TemporaryPassword123!",
            "department_id": department.json()["id"],
        },
    )
    assert employee.status_code == 201

    departments = test_client.get("/api/v1/departments/", headers=headers)
    result = next(item for item in departments.json() if item["id"] == department.json()["id"])
    assert result["employee_count"] == 1

    deactivated = test_client.patch(
        f"/api/v1/employees/{employee.json()['id']}/status",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    departments = test_client.get("/api/v1/departments/", headers=headers)
    result = next(item for item in departments.json() if item["id"] == department.json()["id"])
    assert result["employee_count"] == 0


def test_founder_can_delete_project_and_task(
    test_client: TestClient,
    test_db: Session,
    founder_token: str,
):
    headers = {"Authorization": f"Bearer {founder_token}"}
    project = test_client.post(
        "/api/v1/projects/",
        headers=headers,
        json={"name": "Delete Project Test"},
    )
    assert project.status_code == 201
    deleted_project = test_client.delete(f"/api/v1/projects/{project.json()['id']}", headers=headers)
    assert deleted_project.status_code == 200
    assert test_db.execute(select(Project).where(Project.id == project.json()["id"])).scalar_one_or_none() is None

    task = test_client.post(
        "/api/v1/tasks/",
        headers=headers,
        json={"title": "Delete Task Test", "assigned_employee_ids": []},
    )
    assert task.status_code == 201
    deleted_task = test_client.delete(f"/api/v1/tasks/{task.json()['id']}", headers=headers)
    assert deleted_task.status_code == 200
    assert test_db.execute(select(Task).where(Task.id == task.json()["id"])).scalar_one_or_none() is None
