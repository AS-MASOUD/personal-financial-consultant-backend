import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
IRAN_PHONE_REGEX = re.compile(r"^09\d{9}$")


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name")
    email: str | None = Field(default=None, description="User email address")
    phone_number: str | None = Field(default=None, description="Iranian mobile number (e.g. 09123456789)")
    password: str | None = Field(default=None, min_length=6, max_length=128, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format")
        return clean


class LoginWithPasswordRequest(BaseModel):
    identifier: str = Field(
        ...,
        description="User email address or mobile phone number (e.g. 09123456789 or user@example.com)",
    )
    password: str = Field(..., description="User password")


class RequestOTPRequest(BaseModel):
    identifier: str = Field(
        ...,
        description="Mobile phone number (e.g. 09123456789) or email address to receive OTP code",
    )


class LoginWithOTPRequest(BaseModel):
    identifier: str = Field(
        ...,
        description="Mobile phone number or email address",
    )
    code: str = Field(..., min_length=4, max_length=8, description="OTP code received")


class UserLoginRequest(BaseModel):
    """Backward compatible login request accepting either email or identifier."""
    email: str | None = Field(default=None, description="User email address")
    identifier: str | None = Field(default=None, description="Email or mobile number")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None = None
    phone_number: str | None = None
    full_name: str
    role: str
    age: int | None = None
    job: str | None = None
    bio: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None = None


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: str | None = Field(default=None)
    phone_number: str | None = Field(default=None)
    age: int | None = Field(default=None, ge=10, le=120)
    job: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if not v or not v.strip():
            return None
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("قالب آدرس ایمیل نامعتبر است.")
        return clean


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class OTPResponse(BaseModel):
    identifier: str
    channel: str
    expires_in: int
    cooldown_seconds: int
    debug_code: str | None = None
    message: str = "کد یکبار مصرف با موفقیت ارسال شد."


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)
