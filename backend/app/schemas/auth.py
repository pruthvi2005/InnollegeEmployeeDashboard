import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class LoginRequest(BaseModel):
    """User email and password credentials login payload."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class OtpRequestSchema(BaseModel):
    """Phone number for requesting login OTP challenge."""
    phone: str = Field(..., description="Phone number in E.164 format")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Standard E.164 format: + followed by 7 to 15 digits
        cleaned = v.strip()
        if not re.match(r"^\+?[1-9]\d{6,14}$", cleaned):
            raise ValueError("Phone number must follow valid E.164 international format (e.g. +919876543210)")
        return cleaned


class OtpVerifySchema(BaseModel):
    """Payload to verify 6-digit OTP challenge."""
    phone: str
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must contain numeric digits only")
        return v


class TokenResponse(BaseModel):
    """Successful authentication token response."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class RefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user account information."""
    id: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeInfoForMe(BaseModel):
    """Nested employee details in MeResponse."""
    id: str
    employee_id: str
    full_name: str
    designation: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    profile_photo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MeResponse(UserResponse):
    """Current authenticated user profile including employee info."""
    employee: Optional[EmployeeInfoForMe] = None

    model_config = ConfigDict(from_attributes=True)
