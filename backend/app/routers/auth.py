from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    OtpRequestSchema,
    OtpVerifySchema,
    TokenResponse,
    RefreshResponse,
    MeResponse,
    EmployeeInfoForMe,
)
from app.services.auth_service import AuthService
from app.dependencies import get_current_active_user, extract_token_from_request
from app.core.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password, establishing an httpOnly refresh cookie."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, access_token, refresh_token = AuthService.login_with_password(
        db=db,
        email=payload.email,
        password=payload.password,
        ip=client_ip,
        device_info=user_agent,
    )

    # Set httpOnly cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role_str,
        user_id=user.id,
    )


@router.post("/otp/request", status_code=status.HTTP_200_OK)
def request_otp(
    payload: OtpRequestSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    """Request a 6-digit OTP code sent via SMS to phone number."""
    client_ip = request.client.host if request.client else None
    challenge, development_otp = AuthService.request_otp(
        db=db,
        phone=payload.phone,
        ip=client_ip,
    )
    otp_sent = challenge is not None

    return {
        "message": (
            "Development OTP generated. Enter the code shown on screen."
            if development_otp
            else "OTP sent via SMS."
            if otp_sent
            else "No active account is registered with this phone number."
        ),
        "expires_in": 600,
        "otp_sent": otp_sent,
        "development_otp": development_otp,
    }


@router.post("/otp/verify", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def verify_otp(
    payload: OtpVerifySchema,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Verify phone OTP challenge and establish user session."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, access_token, refresh_token = AuthService.verify_otp(
        db=db,
        phone=payload.phone,
        otp=payload.otp,
        ip=client_ip,
        device_info=user_agent,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role_str,
        user_id=user.id,
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Rotate refresh token stored in cookie and return a new access token."""
    rf_token = request.cookies.get("refresh_token")
    if not rf_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            rf_token = auth_header.split(" ", 1)[1].strip()

    if not rf_token:
        raise AuthenticationError("Refresh token missing from cookie or header")

    client_ip = request.client.host if request.client else None
    new_access_token, new_refresh_token = AuthService.refresh_tokens(
        db=db,
        refresh_token=rf_token,
        ip=client_ip,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )

    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke session tokens and clear authentication cookies."""
    rf_token = request.cookies.get("refresh_token")
    access_token = extract_token_from_request(request)

    AuthService.logout(
        db=db,
        user_id=current_user.id,
        refresh_token=rf_token,
        access_jti=access_token,
    )

    response.delete_cookie(key="refresh_token", path="/")
    response.delete_cookie(key="access_token", path="/")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed identity and profile for authenticated user."""
    user = AuthService.get_me(db=db, user_id=current_user.id)
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

    emp_info = None
    if user.employee:
        emp = user.employee
        dept_name = emp.department.name if emp.department else None
        emp_info = EmployeeInfoForMe(
            id=emp.id,
            employee_id=emp.employee_id,
            full_name=emp.full_name,
            designation=emp.designation,
            department_id=emp.department_id,
            department_name=dept_name,
            profile_photo_url=emp.profile_photo_url,
        )

    return MeResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=role_str,
        is_active=user.is_active,
        created_at=user.created_at,
        employee=emp_info,
    )
