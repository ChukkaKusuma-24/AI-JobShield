"""Password hashing (bcrypt), OTP hashing (HMAC), and JWT helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def generate_otp(length: int | None = None) -> str:
    settings = get_settings()
    digits = length or settings.OTP_LENGTH
    # Cryptographically secure numeric OTP (zero-padded)
    upper = 10**digits
    return f"{secrets.randbelow(upper):0{digits}d}"


def hash_otp(otp: str) -> str:
    """HMAC-SHA256 digest — OTPs are never stored in plain text."""
    settings = get_settings()
    digest = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def verify_otp(otp: str, otp_hash: str | None) -> bool:
    if not otp_hash:
        return False
    return hmac.compare_digest(hash_otp(otp), otp_hash)


def otp_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM])
