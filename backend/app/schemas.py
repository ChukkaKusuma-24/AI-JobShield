"""Pydantic request/response schemas."""
from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# RFC-inspired email shape (local@domain.tld) — not a domain allowlist.
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


def _normalize_and_validate_email(v: str) -> str:
    v = v.strip().lower()
    if len(v) > 255 or not _EMAIL_RE.match(v):
        raise ValueError("Invalid email address")
    return v


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[Any] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(v) > 128:
        raise ValueError("Password cannot exceed 128 characters")
    has_letter = any(c.isalpha() for c in v)
    has_digit_or_special = any(c.isdigit() or not c.isalnum() for c in v)
    if not (has_letter and has_digit_or_special):
        raise ValueError("Password must contain both letters and at least one number or special character")
    return v


# ---- Auth ----
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_and_validate_email(v)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_and_validate_email(v)


class VerifyEmailRequest(BaseModel):
    email: str = Field(..., max_length=255)
    otp: str = Field(..., min_length=4, max_length=12)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_and_validate_email(v)

    @field_validator("otp")
    @classmethod
    def normalize_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Verification code must be numeric")
        if len(v) != 6:
            raise ValueError("Verification code must be a 6-digit number")
        return v


class ResendOtpRequest(BaseModel):
    email: str = Field(..., max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_and_validate_email(v)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_and_validate_email(v)


class ResetPasswordRequest(BaseModel):
    email: str = Field(..., max_length=255)
    otp: str = Field(..., min_length=4, max_length=12)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return _normalize_and_validate_email(v)

    @field_validator("otp")
    @classmethod
    def normalize_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Verification code must be numeric")
        if len(v) != 6:
            raise ValueError("Verification code must be a 6-digit number")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_verified: bool = False
    email_verified: bool = False
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class AuthResponse(BaseModel):
    user: UserOut
    token: str


class RegisterPendingResponse(BaseModel):
    requires_verification: bool = True
    email: str
    message: str = "Verification code sent. Check your email to complete registration."


class MessageResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    user: UserOut


# ---- Analyze ----
class AnalyzeRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=30, max_length=20000)
    salary: Optional[str] = Field(None, max_length=120)
    email: Optional[str] = Field(None, max_length=255)
    url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[str] = Field(None, max_length=80)

    @field_validator("title", "company_name", "description", "salary", "email", "url", "location", "job_type")
    @classmethod
    def strip_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip()


class UrlAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=4, max_length=500)
    company_name: Optional[str] = Field(None, max_length=255)


class CompanyVerifyRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)


class ReportCreate(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10, max_length=10000)
    url: Optional[str] = Field(None, max_length=500)
    reason: str = Field(..., min_length=5, max_length=2000)


class FeedbackCreate(BaseModel):
    analysis_id: int
    label: Literal["correct", "incorrect", "report"]
    comment: Optional[str] = Field(None, max_length=2000)


class HealthResponse(BaseModel):
    status: str
    ml_available: bool
    ocr_available: bool
    online_lookup_enabled: bool
