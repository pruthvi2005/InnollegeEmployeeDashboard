import hmac
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.config import settings

# Argon2id password hasher configuration (Memory=64MB, TimeCost=2, Parallelism=1)
_pwd_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
)


def hash_password(plain: str) -> str:
    """Hash password using Argon2id."""
    return _pwd_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against Argon2id hash."""
    if not hashed:
        return False
    try:
        return _pwd_hasher.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token with expiration and unique jti."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": "access",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT refresh token with 7-day expiration."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": "refresh",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token claims."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash token using SHA-256 for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_otp() -> str:
    """Generate cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(otp: str) -> str:
    """Hash OTP using HMAC-SHA256 with application secret key."""
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), otp.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_otp(plain: str, hashed: str) -> bool:
    """Verify plain OTP against stored hash using constant-time comparison."""
    if not plain or not hashed:
        return False
    computed = hash_otp(plain)
    return hmac.compare_digest(computed, hashed)
