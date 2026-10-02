"""Auth routes: register, email OTP verify, login, forgot/reset password, me."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings
from app.deps import (
    AppError,
    CurrentUser,
    DbSession,
    check_login_rate_limit,
    check_otp_resend_rate_limit,
    clear_otp_resend_rate_limit,
)
from app.models import EmailOtp, User, utcnow
from app.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    MessageResponse,
    RegisterPendingResponse,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    UserOut,
    VerifyEmailRequest,
)
from app.security import (
    create_access_token,
    generate_otp,
    hash_otp,
    hash_password,
    otp_expiry,
    verify_otp,
    verify_password,
)
from app.services.email_service import (
    send_password_reset_otp,
    send_verification_otp,
    smtp_configured,
)

logger = logging.getLogger("jobshield.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_token(user: User) -> AuthResponse:
    token = create_access_token(user.id, {"role": user.role, "email": user.email})
    return AuthResponse(user=UserOut.model_validate(user), token=token)


def _get_active_otp(db: DbSession, user_id: int, purpose: str = "verification") -> EmailOtp | None:
    return (
        db.query(EmailOtp)
        .filter(EmailOtp.user_id == user_id, EmailOtp.purpose == purpose)
        .first()
    )


def _assign_and_send_otp(db: DbSession, user: User, *, purpose: str = "verification", context: str) -> None:
    otp = generate_otp(6)
    hashed = hash_otp(otp)
    expiry = otp_expiry()

    record = _get_active_otp(db, user.id, purpose=purpose)
    if record:
        record.otp_hash = hashed
        record.expires_at = expiry
        record.attempts = 0
        record.updated_at = utcnow()
    else:
        record = EmailOtp(
            user_id=user.id,
            otp_hash=hashed,
            purpose=purpose,
            expires_at=expiry,
            attempts=0,
        )
        db.add(record)
    db.flush()

    logger.info("OTP generated for user %s (purpose=%s, context=%s, expires=%s)", user.email, purpose, context, expiry.isoformat())

    try:
        if purpose == "password_reset":
            send_password_reset_otp(user.email, otp, name=user.name)
        else:
            send_verification_otp(user.email, otp, name=user.name)
    except Exception as exc:
        logger.error("Failed to send OTP email to %s (%s): %s", user.email, context, exc)
        raise AppError(
            "EMAIL_SEND_FAILED",
            str(exc) if str(exc) else "Could not send verification email. Check SMTP settings in .env.",
            503,
        ) from exc


def _otp_is_expired(otp_record: EmailOtp) -> bool:
    if not otp_record or not otp_record.expires_at:
        return True
    expires = otp_record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires


@router.post("/register", response_model=RegisterPendingResponse, status_code=201)
def register(body: RegisterRequest, db: DbSession):
    logger.info("Register request for %s", body.email)
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        if existing.is_verified:
            raise AppError("EMAIL_TAKEN", "An account with this email already exists", 400)
        # Unverified account: update credentials and resend verification OTP
        existing.name = body.name
        existing.password_hash = hash_password(body.password)
        existing.updated_at = utcnow()
        try:
            _assign_and_send_otp(db, existing, purpose="verification", context="register-retry")
        except AppError:
            db.rollback()
            raise
        db.commit()
        clear_otp_resend_rate_limit(existing.email)
        logger.info("Register retry: OTP re-sent to unverified account %s", existing.email)
        return RegisterPendingResponse(email=existing.email)

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role="user",
        is_verified=False,
    )
    db.add(user)
    db.flush()
    try:
        _assign_and_send_otp(db, user, purpose="verification", context="register")
    except AppError:
        db.rollback()
        raise
    db.commit()
    clear_otp_resend_rate_limit(user.email)
    logger.info("Register complete for %s — awaiting email verification", user.email)
    return RegisterPendingResponse(email=user.email)


@router.post("/verify-email", response_model=AuthResponse)
def verify_email(body: VerifyEmailRequest, db: DbSession):
    logger.info("Verify-email request for %s", body.email)
    settings = get_settings()
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise AppError("INVALID_OTP", "Invalid or expired verification code", 400)
    if user.is_verified:
        logger.info("Verify-email: %s already verified", user.email)
        return _issue_token(user)

    otp_record = _get_active_otp(db, user.id, purpose="verification")
    if not otp_record or _otp_is_expired(otp_record):
        if otp_record:
            db.delete(otp_record)
            db.commit()
        logger.warning("Verify-email: expired or missing OTP for %s", user.email)
        raise AppError(
            "OTP_EXPIRED",
            "Verification code expired. Request a new code.",
            400,
        )

    if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
        db.delete(otp_record)
        db.commit()
        logger.warning("Verify-email: OTP locked for %s", user.email)
        raise AppError(
            "OTP_LOCKED",
            "Too many invalid attempts. Request a new verification code.",
            400,
        )

    if not verify_otp(body.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        otp_record.updated_at = utcnow()
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - otp_record.attempts
        logger.warning("Verify-email: invalid OTP for %s (%s attempt(s) left)", user.email, remaining)
        raise AppError(
            "INVALID_OTP",
            f"Invalid verification code. {remaining} attempt(s) remaining.",
            400,
        )

    user.is_verified = True
    user.updated_at = utcnow()
    db.delete(otp_record)
    db.commit()
    db.refresh(user)
    logger.info("Verify-email: %s verified successfully", user.email)
    return _issue_token(user)


@router.post("/resend-otp", response_model=MessageResponse)
def resend_otp(body: ResendOtpRequest, db: DbSession):
    logger.info("Resend-OTP request for %s", body.email)
    if not check_otp_resend_rate_limit(body.email):
        logger.warning("Resend-OTP rate-limited for %s", body.email)
        raise AppError(
            "RATE_LIMIT",
            "Please wait before requesting another verification code.",
            429,
        )
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        logger.warning("Resend-OTP: no account found for %s", body.email)
        return MessageResponse(message="If an unverified account exists, a new code was sent.")
    if user.is_verified:
        logger.info("Resend-OTP: %s already verified", body.email)
        return MessageResponse(message="This email is already verified. You can sign in.")

    try:
        _assign_and_send_otp(db, user, purpose="verification", context="resend")
    except AppError:
        db.rollback()
        raise
    db.commit()
    logger.info("Resend-OTP: new code sent to %s", user.email)
    return MessageResponse(message="A new verification code has been sent to your email.")


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: DbSession):
    if not check_login_rate_limit(body.email):
        raise AppError("RATE_LIMIT", "Too many login attempts. Try again shortly.", 429)
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password", 401)
    if not user.is_verified:
        raise AppError(
            "EMAIL_NOT_VERIFIED",
            "Please verify your email with the OTP sent to your inbox before signing in.",
            403,
        )
    return _issue_token(user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: DbSession):
    logger.info("Forgot-password request for %s", body.email)
    if not check_otp_resend_rate_limit(body.email):
        raise AppError("RATE_LIMIT", "Please wait before requesting another code.", 429)

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.is_verified:
        # Generic response for security to avoid account enumeration
        return MessageResponse(message="If a verified account exists for this email, a password reset code was sent.")

    try:
        _assign_and_send_otp(db, user, purpose="password_reset", context="forgot-password")
    except AppError:
        db.rollback()
        raise
    db.commit()
    logger.info("Forgot-password: reset code sent to %s", user.email)
    return MessageResponse(message="A 6-digit password reset code has been sent to your email.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: DbSession):
    logger.info("Reset-password request for %s", body.email)
    settings = get_settings()
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise AppError("INVALID_OTP", "Invalid or expired reset code", 400)

    otp_record = _get_active_otp(db, user.id, purpose="password_reset")
    if not otp_record or _otp_is_expired(otp_record):
        if otp_record:
            db.delete(otp_record)
            db.commit()
        raise AppError("OTP_EXPIRED", "Password reset code expired. Please request a new one.", 400)

    if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
        db.delete(otp_record)
        db.commit()
        raise AppError("OTP_LOCKED", "Too many invalid attempts. Please request a new code.", 400)

    if not verify_otp(body.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        otp_record.updated_at = utcnow()
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - otp_record.attempts
        raise AppError("INVALID_OTP", f"Invalid code. {remaining} attempt(s) remaining.", 400)

    # Valid OTP: update password securely with bcrypt
    user.password_hash = hash_password(body.new_password)
    user.updated_at = utcnow()
    db.delete(otp_record)
    db.commit()
    logger.info("Password successfully reset for %s", user.email)
    return MessageResponse(message="Your password has been reset successfully. You can now sign in.")


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser):
    return MeResponse(user=UserOut.model_validate(user))
