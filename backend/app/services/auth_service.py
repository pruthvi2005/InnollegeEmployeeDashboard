import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional

import httpx
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.user import User, AuthSession, OtpChallenge, LoginEvent, UserRole
from app.models.employee import Employee
from app.models.activity import ActivityLog
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    generate_otp,
    hash_otp,
    verify_otp,
)
from app.core.exceptions import AppException, AuthenticationError, NotFoundError

logger = logging.getLogger(__name__)

MSG91_FLOW_URL = "https://control.msg91.com/api/v5/flow"


def _phone_lookup_values(phone: str) -> Tuple[str, set[str]]:
    digits = re.sub(r"\D", "", phone)
    country_code = re.sub(r"\D", "", settings.MSG91_COUNTRY_CODE)

    if len(digits) == 10:
        digits = f"{country_code}{digits}"
    elif len(digits) == 11 and digits.startswith("0"):
        digits = f"{country_code}{digits[1:]}"

    if not country_code or not 7 <= len(digits) <= 15:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone number must be a valid international number.",
            error_code="INVALID_PHONE_NUMBER",
        )

    canonical_phone = f"+{digits}"
    lookup_values = {canonical_phone, digits}
    if digits.startswith(country_code) and len(digits) == len(country_code) + 10:
        national_number = digits[len(country_code):]
        lookup_values.update({national_number, f"+{national_number}"})

    return canonical_phone, lookup_values


class AuthService:
    """Service handling password login, OTP passwordless flow, and token lifecycles."""

    @staticmethod
    def login_with_password(
        db: Session,
        email: str,
        password: str,
        ip: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Authenticate user by email and password, creating a persistent session."""
        stmt = select(User).where(User.email == email)
        user = db.execute(stmt).scalar_one_or_none()

        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            if user:
                event = LoginEvent(
                    user_id=user.id,
                    event_type="login_failed",
                    ip_address=ip,
                    device_info=device_info,
                )
                db.add(event)
                db.commit()
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive. Please contact administrator.")

        # Create tokens
        access_token = create_access_token(
            {"sub": user.id, "email": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
        )
        refresh_token = create_refresh_token(
            {"sub": user.id, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
        )

        # Store session
        rf_hash = hash_token(refresh_token)
        session = AuthSession(
            user_id=user.id,
            refresh_token_hash=rf_hash,
            device_info=device_info,
            ip_address=ip,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
        login_event = LoginEvent(
            user_id=user.id,
            event_type="login_success",
            ip_address=ip,
            device_info=device_info,
        )

        user.last_login = datetime.now(timezone.utc)
        db.add(session)
        db.add(login_event)
        db.add(
            ActivityLog(
                user_id=user.id,
                employee_id=user.employee.id if user.employee else None,
                event_type="user_login",
                event_data={"role": user.role.value},
                ip_address=ip,
            )
        )
        db.commit()
        db.refresh(user)

        return user, access_token, refresh_token

    @staticmethod
    def request_otp(
        db: Session,
        phone: str,
        ip: Optional[str] = None,
    ) -> Tuple[Optional[OtpChallenge], Optional[str]]:
        """Issue or recycle OTP challenge for a given phone number."""
        development_stub = (
            settings.OTP_STUB_MODE and settings.ENVIRONMENT == "development"
        )
        if not development_stub and (
            not settings.MSG91_API_KEY.strip()
            or not settings.MSG91_TEMPLATE_ID.strip()
        ):
            raise AppException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MSG91 SMS delivery is not configured. Set MSG91_API_KEY and MSG91_TEMPLATE_ID.",
                error_code="OTP_DELIVERY_UNAVAILABLE",
            )

        canonical_phone, phone_values = _phone_lookup_values(phone)
        stmt = select(User).where(User.phone.in_(phone_values))
        matching_users = db.execute(stmt).scalars().all()
        if len(matching_users) > 1:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This phone number is linked to multiple accounts. Contact an administrator.",
                error_code="PHONE_NUMBER_AMBIGUOUS",
            )
        user = matching_users[0] if matching_users else None

        if (
            not user
            or not user.is_active
            or (
                user.role == UserRole.employee
                and user.employee is None
            )
        ):
            return None, None

        otp = generate_otp()
        otp_hash = hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        challenge = OtpChallenge(
            user_id=user.id,
            otp_hash=otp_hash,
            phone=canonical_phone,
            attempts=0,
            max_attempts=5,
            expires_at=expires_at,
            is_used=False,
        )
        event = LoginEvent(
            user_id=user.id,
            event_type="otp_requested",
            ip_address=ip,
        )
        db.add(challenge)
        db.add(event)
        db.commit()
        db.refresh(challenge)

        if development_stub:
            logger.info("Development OTP generated for a registered account.")
            return challenge, otp

        otp_variable = settings.MSG91_OTP_VARIABLE.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}", otp_variable):
            challenge.is_used = True
            db.commit()
            raise AppException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MSG91_OTP_VARIABLE must be a valid template variable name.",
                error_code="OTP_DELIVERY_UNAVAILABLE",
            )

        payload = {
            "template_id": settings.MSG91_TEMPLATE_ID.strip(),
            "recipients": [
                {
                    "mobiles": canonical_phone[1:],
                    otp_variable: otp,
                }
            ],
        }
        try:
            response = httpx.post(
                MSG91_FLOW_URL,
                headers={"authkey": settings.MSG91_API_KEY.strip()},
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            provider_response = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            challenge.is_used = True
            db.commit()
            logger.error("MSG91 OTP delivery failed (%s).", type(exc).__name__)
            raise AppException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The SMS provider could not deliver the OTP. Please try again.",
                error_code="OTP_DELIVERY_FAILED",
            ) from exc

        if (
            not isinstance(provider_response, dict)
            or str(provider_response.get("type", "")).lower() != "success"
        ):
            challenge.is_used = True
            db.commit()
            logger.error("MSG91 rejected the OTP delivery request.")
            raise AppException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The SMS provider could not deliver the OTP. Please try again.",
                error_code="OTP_DELIVERY_FAILED",
            )

        return challenge, None

    @staticmethod
    def verify_otp(
        db: Session,
        phone: str,
        otp: str,
        ip: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Verify OTP, activate session, and issue tokens."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(OtpChallenge)
            .where(
                OtpChallenge.phone == phone,
                OtpChallenge.is_used == False,  # noqa: E712
            )
            .order_by(OtpChallenge.created_at.desc())
            .limit(1)
        )
        challenge = db.execute(stmt).scalar_one_or_none()

        if not challenge:
            raise AuthenticationError("No pending OTP challenge found")

        # Handle naive datetime comparison if needed
        challenge_exp = challenge.expires_at
        if challenge_exp.tzinfo is None:
            challenge_exp = challenge_exp.replace(tzinfo=timezone.utc)

        if challenge_exp < now:
            raise AuthenticationError("OTP has expired")

        if challenge.attempts >= challenge.max_attempts:
            raise AuthenticationError("Maximum OTP attempts exceeded. Please request a new code.")

        challenge.attempts += 1

        if not verify_otp(otp, challenge.otp_hash):
            db.commit()
            raise AuthenticationError("Invalid OTP code")

        challenge.is_used = True

        user_stmt = select(User).where(User.id == challenge.user_id)
        user = db.execute(user_stmt).scalar_one()

        if not user.is_active:
            db.commit()
            raise AuthenticationError("Account is inactive")

        user.phone_verified = True
        user.last_login = now

        access_token = create_access_token(
            {"sub": user.id, "email": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
        )
        refresh_token = create_refresh_token(
            {"sub": user.id, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
        )

        session = AuthSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            device_info=device_info,
            ip_address=ip,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
        event = LoginEvent(
            user_id=user.id,
            event_type="otp_verified",
            ip_address=ip,
            device_info=device_info,
        )
        db.add(session)
        db.add(event)
        db.commit()
        db.refresh(user)

        return user, access_token, refresh_token

    @staticmethod
    def refresh_tokens(
        db: Session,
        refresh_token: str,
        ip: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Rotate refresh token and issue a fresh access token."""
        token_hash = hash_token(refresh_token)
        now = datetime.now(timezone.utc)

        stmt = select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
        session = db.execute(stmt).scalar_one_or_none()

        if not session or session.is_revoked:
            raise AuthenticationError("Invalid or revoked refresh token")

        session_exp = session.expires_at
        if session_exp.tzinfo is None:
            session_exp = session_exp.replace(tzinfo=timezone.utc)

        if session_exp < now:
            raise AuthenticationError("Refresh session expired")

        user_stmt = select(User).where(User.id == session.user_id)
        user = db.execute(user_stmt).scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Issue new token pair
        new_access_token = create_access_token(
            {"sub": user.id, "email": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
        )
        new_refresh_token = create_refresh_token(
            {"sub": user.id, "role": user.role.value if hasattr(user.role, "value") else str(user.role)}
        )

        # Rotate session hash
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session.ip_address = ip

        event = LoginEvent(
            user_id=user.id,
            event_type="token_refresh",
            ip_address=ip,
        )
        db.add(event)
        db.commit()

        return new_access_token, new_refresh_token

    @staticmethod
    def logout(
        db: Session,
        user_id: str,
        refresh_token: Optional[str] = None,
        access_jti: Optional[str] = None,
    ) -> None:
        """Revoke active session and record logout event."""
        if refresh_token:
            token_hash = hash_token(refresh_token)
            stmt = select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
            session = db.execute(stmt).scalar_one_or_none()
            if session:
                session.is_revoked = True

        event = LoginEvent(
            user_id=user_id,
            event_type="logout",
        )
        db.add(event)
        db.commit()

    @staticmethod
    def get_me(db: Session, user_id: str) -> User:
        """Load user along with linked employee profile."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.employee).joinedload(Employee.department))
        )
        user = db.execute(stmt).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return user
