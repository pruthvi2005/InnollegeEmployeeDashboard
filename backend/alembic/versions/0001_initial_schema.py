"""Initial complete database schema for Jyohar Tech × Innollege platform.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-18 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("role", sa.Enum("founder", "employee", name="user_role_enum"), nullable=False, server_default="employee"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.create_index("ix_users_created_at", "users", ["created_at"])

    # 2. departments
    op.create_table(
        "departments",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)

    # 3. employees (FK: users, departments)
    op.create_table(
        "employees",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("employee_id", sa.String(length=20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("department_id", sa.CHAR(length=36), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("designation", sa.String(length=255), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("profile_photo_url", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_employees_employee_id", "employees", ["employee_id"], unique=True)
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_is_active", "employees", ["is_active"])
    op.create_index("ix_employees_created_at", "employees", ["created_at"])

    # 4. employee_profiles (FK: employees)
    op.create_table(
        "employee_profiles",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("emergency_contact_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=20), nullable=True),
        sa.Column("bank_account", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_employee_profiles_employee_id", "employee_profiles", ["employee_id"])

    # 5. auth_sessions (FK: users)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False, unique=True),
        sa.Column("device_info", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_refresh_token_hash", "auth_sessions", ["refresh_token_hash"])

    # 6. otp_challenges (FK: users)
    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("otp_hash", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_otp_challenges_phone", "otp_challenges", ["phone"])
    op.create_index("ix_otp_challenges_user_id", "otp_challenges", ["user_id"])

    # 7. login_events (FK: users)
    op.create_table(
        "login_events",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("device_info", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_login_events_user_id", "login_events", ["user_id"])
    op.create_index("ix_login_events_created_at", "login_events", ["created_at"])

    # 8. projects (FK: users)
    op.create_table(
        "projects",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("planning", "active", "on_hold", "completed", "archived", name="project_status_enum"), nullable=False, server_default="planning"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])

    # 9. project_members (FK: projects, employees)
    op.create_table(
        "project_members",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.CHAR(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "employee_id", name="uq_project_members_project_employee"),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_employee_id", "project_members", ["employee_id"])

    # 10. tasks (FK: projects, users)
    op.create_table(
        "tasks",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_id", sa.CHAR(length=36), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("priority", sa.Enum("low", "medium", "high", "urgent", name="task_priority_enum"), nullable=False, server_default="medium"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_deadline", "tasks", ["deadline"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])

    # 11. task_assignments (FK: tasks, employees, users)
    op.create_table(
        "task_assignments",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("task_id", sa.CHAR(length=36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("pending", "in_progress", "submitted", "under_review", "completed", "revision_required", "overdue", name="assignment_status_enum"), nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("task_id", "employee_id", name="uq_task_assignments_task_employee"),
    )
    op.create_index("ix_task_assignments_task_id", "task_assignments", ["task_id"])
    op.create_index("ix_task_assignments_employee_id", "task_assignments", ["employee_id"])
    op.create_index("ix_task_assignments_status", "task_assignments", ["status"])

    # 12. task_updates (FK: task_assignments, users)
    op.create_table(
        "task_updates",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("assignment_id", sa.CHAR(length=36), sa.ForeignKey("task_assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_task_updates_assignment_id", "task_updates", ["assignment_id"])

    # 13. task_comments (FK: tasks, employees)
    op.create_table(
        "task_comments",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("task_id", sa.CHAR(length=36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_founder_comment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_task_comments_task_id", "task_comments", ["task_id"])
    op.create_index("ix_task_comments_employee_id", "task_comments", ["employee_id"])

    # 14. task_checklists (FK: tasks, users)
    op.create_table(
        "task_checklists",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("task_id", sa.CHAR(length=36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_text", sa.String(length=1000), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_task_checklists_task_id", "task_checklists", ["task_id"])

    # 15. attendance (FK: employees)
    op.create_table(
        "attendance",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("check_in_time", sa.DateTime(), nullable=True),
        sa.Column("check_out_time", sa.DateTime(), nullable=True),
        sa.Column("working_hours", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("status", sa.Enum("present", "absent", "half_day", "on_leave", "holiday", name="attendance_status_enum"), nullable=False, server_default="absent"),
        sa.Column("is_late", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )
    op.create_index("ix_attendance_employee_id", "attendance", ["employee_id"])
    op.create_index("ix_attendance_work_date", "attendance", ["work_date"])
    op.create_index("ix_attendance_status", "attendance", ["status"])

    # 16. attendance_events (FK: attendance)
    op.create_table(
        "attendance_events",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("attendance_id", sa.CHAR(length=36), sa.ForeignKey("attendance.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_attendance_events_attendance_id", "attendance_events", ["attendance_id"])

    # 17. attendance_adjustments (FK: attendance, users)
    op.create_table(
        "attendance_adjustments",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("attendance_id", sa.CHAR(length=36), sa.ForeignKey("attendance.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_attendance_adjustments_attendance_id", "attendance_adjustments", ["attendance_id"])

    # 18. daily_reports (FK: employees, users)
    op.create_table(
        "daily_reports",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("completed_work", sa.Text(), nullable=True),
        sa.Column("pending_work", sa.Text(), nullable=True),
        sa.Column("challenges", sa.Text(), nullable=True),
        sa.Column("tomorrow_plan", sa.Text(), nullable=True),
        sa.Column("total_hours_worked", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("status", sa.Enum("draft", "submitted", "reviewed", name="report_status_enum"), nullable=False, server_default="draft"),
        sa.Column("founder_feedback", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id", "report_date", name="uq_daily_reports_employee_date"),
    )
    op.create_index("ix_daily_reports_employee_id", "daily_reports", ["employee_id"])
    op.create_index("ix_daily_reports_report_date", "daily_reports", ["report_date"])
    op.create_index("ix_daily_reports_status", "daily_reports", ["status"])

    # 19. daily_report_tasks (FK: daily_reports, tasks)
    op.create_table(
        "daily_report_tasks",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("report_id", sa.CHAR(length=36), sa.ForeignKey("daily_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.CHAR(length=36), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task_description", sa.String(length=1000), nullable=False),
        sa.Column("time_spent_hours", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_daily_report_tasks_report_id", "daily_report_tasks", ["report_id"])

    # 20. leave_types
    op.create_table(
        "leave_types",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("days_per_year", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leave_types_name", "leave_types", ["name"])

    # 21. leave_requests (FK: employees, leave_types)
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type_id", sa.CHAR(length=36), sa.ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "cancelled", name="leave_request_status_enum"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leave_requests_employee_id", "leave_requests", ["employee_id"])
    op.create_index("ix_leave_requests_status", "leave_requests", ["status"])
    op.create_index("ix_leave_requests_start_date", "leave_requests", ["start_date"])
    op.create_index("ix_leave_requests_end_date", "leave_requests", ["end_date"])

    # 22. leave_actions (FK: leave_requests, users)
    op.create_table(
        "leave_actions",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("leave_request_id", sa.CHAR(length=36), sa.ForeignKey("leave_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leave_actions_leave_request_id", "leave_actions", ["leave_request_id"])

    # 23. notifications (FK: users)
    op.create_table(
        "notifications",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("reference_id", sa.CHAR(length=36), nullable=True),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # 24. files (FK: users)
    op.create_table(
        "files",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("storage_key", sa.String(length=1000), nullable=False, unique=True),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_files_uploaded_by", "files", ["uploaded_by"])

    # 25. task_files (FK: tasks, files, users)
    op.create_table(
        "task_files",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("task_id", sa.CHAR(length=36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.CHAR(length=36), sa.ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_task_files_task_id", "task_files", ["task_id"])
    op.create_index("ix_task_files_file_id", "task_files", ["file_id"])

    # 26. report_files (FK: daily_reports, files, users)
    op.create_table(
        "report_files",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("report_id", sa.CHAR(length=36), sa.ForeignKey("daily_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.CHAR(length=36), sa.ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_report_files_report_id", "report_files", ["report_id"])
    op.create_index("ix_report_files_file_id", "report_files", ["file_id"])

    # 27. activity_logs (FK: users, employees)
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("employee_id", sa.CHAR(length=36), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
    op.create_index("ix_activity_logs_employee_id", "activity_logs", ["employee_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])

    # 28. audit_logs (FK: users)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.CHAR(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.CHAR(length=36), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop in exact reverse order
    op.drop_table("audit_logs")
    op.drop_table("activity_logs")
    op.drop_table("report_files")
    op.drop_table("task_files")
    op.drop_table("files")
    op.drop_table("notifications")
    op.drop_table("leave_actions")
    op.drop_table("leave_requests")
    op.drop_table("leave_types")
    op.drop_table("daily_report_tasks")
    op.drop_table("daily_reports")
    op.drop_table("attendance_adjustments")
    op.drop_table("attendance_events")
    op.drop_table("attendance")
    op.drop_table("task_checklists")
    op.drop_table("task_comments")
    op.drop_table("task_updates")
    op.drop_table("task_assignments")
    op.drop_table("tasks")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("login_events")
    op.drop_table("otp_challenges")
    op.drop_table("auth_sessions")
    op.drop_table("employee_profiles")
    op.drop_table("employees")
    op.drop_table("departments")
    op.drop_table("users")
