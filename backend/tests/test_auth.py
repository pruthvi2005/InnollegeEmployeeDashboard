import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models.employee import Employee
from app.models.user import User
from app.services import auth_service


def test_login_success(test_client: TestClient, founder_user: User):
    """Test successful password login sets cookies and returns access token."""
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "founder@jyohartech.com", "password": "Jyohar@2024"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "founder"
    assert data["user_id"] == founder_user.id
    assert "refresh_token" in response.cookies


def test_login_invalid_password(test_client: TestClient, founder_user: User):
    """Test login rejection on bad password."""
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "founder@jyohartech.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_inactive_user(test_client: TestClient, test_db: Session, founder_user: User):
    """Test login rejection for deactivated user accounts."""
    founder_user.is_active = False
    test_db.commit()

    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "founder@jyohartech.com", "password": "Jyohar@2024"},
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


def test_get_me(test_client: TestClient, founder_token: str, founder_user: User):
    """Test reading own user information with valid JWT bearer token."""
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {founder_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "founder@jyohartech.com"
    assert data["role"] == "founder"
    assert "password_hash" not in data


def test_get_me_unauthorized(test_client: TestClient):
    """Test unauthorized rejection when accessing /me without token."""
    response = test_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_token(test_client: TestClient, founder_user: User):
    """Test token refresh rotation using httpOnly cookie."""
    login_resp = test_client.post(
        "/api/v1/auth/login",
        json={"email": "founder@jyohartech.com", "password": "Jyohar@2024"},
    )
    assert login_resp.status_code == 200
    refresh_cookie = login_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None

    refresh_resp = test_client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data


def test_logout(test_client: TestClient, founder_user: User):
    """Test session logout revokes cookies."""
    login_resp = test_client.post(
        "/api/v1/auth/login",
        json={"email": "founder@jyohartech.com", "password": "Jyohar@2024"},
    )
    access_token = login_resp.json()["access_token"]
    refresh_cookie = login_resp.cookies.get("refresh_token")

    logout_resp = test_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": refresh_cookie},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"


def test_development_otp_login_for_registered_employee(
    test_client: TestClient,
    test_employee: Employee,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "OTP_STUB_MODE", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    requested = test_client.post(
        "/api/v1/auth/otp/request",
        json={"phone": test_employee.user.phone},
    )
    assert requested.status_code == 200
    assert requested.json()["otp_sent"] is True
    development_otp = requested.json()["development_otp"]
    assert len(development_otp) == 6
    assert development_otp.isdigit()

    verified = test_client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": test_employee.user.phone, "otp": development_otp},
    )
    assert verified.status_code == 200
    assert verified.json()["user_id"] == test_employee.user_id


def test_otp_does_not_create_accounts_for_unknown_numbers(
    test_client: TestClient,
    test_db: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "OTP_STUB_MODE", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    existing_user_count = test_db.query(User).count()

    response = test_client.post(
        "/api/v1/auth/otp/request",
        json={"phone": "+919999999999"},
    )

    assert response.status_code == 200
    assert response.json()["otp_sent"] is False
    assert response.json()["development_otp"] is None
    assert test_db.query(User).count() == existing_user_count


def test_msg91_otp_sends_sms_without_returning_code(
    test_client: TestClient,
    test_employee: Employee,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "OTP_STUB_MODE", False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "MSG91_API_KEY", "test-api-key")
    monkeypatch.setattr(settings, "MSG91_TEMPLATE_ID", "test-template")
    captured_request = {}

    def fake_post(url, *, headers, json, timeout):
        captured_request.update(
            url=url,
            headers=headers,
            payload=json,
            timeout=timeout,
        )
        return httpx.Response(
            200,
            json={"type": "success", "request_id": "test"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(auth_service.httpx, "post", fake_post)
    response = test_client.post(
        "/api/v1/auth/otp/request",
        json={"phone": test_employee.user.phone},
    )

    assert response.status_code == 200
    assert response.json()["otp_sent"] is True
    assert response.json()["development_otp"] is None
    assert captured_request["url"] == auth_service.MSG91_FLOW_URL
    assert captured_request["headers"]["authkey"] == "test-api-key"
    assert captured_request["payload"]["template_id"] == "test-template"
    recipient = captured_request["payload"]["recipients"][0]
    assert recipient["mobiles"] == "919876543210"
    assert recipient["VAR1"].isdigit()
    assert len(recipient["VAR1"]) == 6


def test_msg91_otp_delivery_failure_is_reported(
    test_client: TestClient,
    test_employee: Employee,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "OTP_STUB_MODE", False)
    monkeypatch.setattr(settings, "MSG91_API_KEY", "test-api-key")
    monkeypatch.setattr(settings, "MSG91_TEMPLATE_ID", "test-template")

    def fake_post(url, *, headers, json, timeout):
        return httpx.Response(
            401,
            json={"type": "error"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(auth_service.httpx, "post", fake_post)
    response = test_client.post(
        "/api/v1/auth/otp/request",
        json={"phone": test_employee.user.phone},
    )

    assert response.status_code == 502
    assert response.json()["error_code"] == "OTP_DELIVERY_FAILED"


def test_otp_reports_unconfigured_sms_delivery_outside_development(
    test_client: TestClient,
    test_employee: Employee,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "OTP_STUB_MODE", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "MSG91_API_KEY", "")
    monkeypatch.setattr(settings, "MSG91_TEMPLATE_ID", "")

    response = test_client.post(
        "/api/v1/auth/otp/request",
        json={"phone": test_employee.user.phone},
    )

    assert response.status_code == 503
    assert response.json()["error_code"] == "OTP_DELIVERY_UNAVAILABLE"
