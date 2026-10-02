"""FastAPI dependencies: auth, DB, rate limit."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Annotated, Optional

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)

# Simple in-memory login rate limit: email -> list of timestamps
_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_LIMIT = 10
LOGIN_WINDOW_SEC = 60

_otp_resend_attempts: dict[str, list[float]] = defaultdict(list)


def check_login_rate_limit(email: str) -> bool:
    now = time.time()
    attempts = [t for t in _login_attempts[email] if now - t < LOGIN_WINDOW_SEC]
    _login_attempts[email] = attempts
    if len(attempts) >= LOGIN_LIMIT:
        return False
    _login_attempts[email].append(now)
    return True


def check_otp_resend_rate_limit(email: str) -> bool:
    """Allow one OTP resend per cooldown window per email (resend endpoint only)."""
    from app.config import get_settings

    window = get_settings().OTP_RESEND_COOLDOWN_SEC
    now = time.time()
    key = email.strip().lower()
    attempts = [t for t in _otp_resend_attempts[key] if now - t < window]
    _otp_resend_attempts[key] = attempts
    if attempts:
        return False
    _otp_resend_attempts[key].append(now)
    return True


def clear_otp_resend_rate_limit(email: str) -> None:
    """Clear resend cooldown (e.g. after a fresh registration OTP)."""
    _otp_resend_attempts.pop(email.strip().lower(), None)


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[list] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError("UNAUTHORIZED", "Authentication required", 401)
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise AppError("UNAUTHORIZED", "Invalid or expired token", 401)
    user = db.get(User, user_id)
    if not user:
        raise AppError("UNAUTHORIZED", "User not found", 401)
    if not user.is_verified:
        raise AppError(
            "EMAIL_NOT_VERIFIED",
            "Email verification required before accessing this resource",
            403,
        )
    return user


def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        return db.get(User, int(payload.get("sub", 0)))
    except Exception:
        return None


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise AppError("FORBIDDEN", "Admin access required", 403)
    return user


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
