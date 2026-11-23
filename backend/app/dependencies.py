from typing import Optional
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.core.security import decode_token
from app.core.redis_client import is_blacklisted
from app.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT token prioritizing httpOnly cookie, then Authorization header."""
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Validate access token from cookie/header and return authenticated User."""
    token = extract_token_from_request(request)
    if not token:
        raise AuthenticationError("Authentication token is missing")

    payload = decode_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")

    token_type = payload.get("token_type")
    if token_type and token_type != "access":
        raise AuthenticationError("Invalid token type")

    jti = payload.get("jti")
    if jti and is_blacklisted(jti):
        raise AuthenticationError("Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user subject")

    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise AuthenticationError("User not found")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that the authenticated user account is active."""
    if not current_user.is_active:
        raise AuthorizationError("Account is inactive")
    return current_user


async def require_founder(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Authorize founder-role users only."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "founder":
        raise AuthorizationError("Founder privileges required")
    return current_user


async def require_employee(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Authorize employee-role users only."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "employee":
        raise AuthorizationError("Employee privileges required")
    return current_user


async def get_employee_from_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Employee:
    """Retrieve the Employee record associated with the current user."""
    stmt = select(Employee).where(Employee.user_id == current_user.id)
    employee = db.execute(stmt).scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee record not found for user")
    return employee
