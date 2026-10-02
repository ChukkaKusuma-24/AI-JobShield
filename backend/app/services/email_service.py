"""SMTP email delivery for verification and password reset OTPs. Credentials come from .env only."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger("jobshield.email")

# Used only during automated tests when SMTP_CONSOLE_FALLBACK=true.
_last_console_otps: dict[str, str] = {}


def smtp_configured() -> bool:
    """True only when host + username/user + password look like real credentials."""
    settings = get_settings()
    host = (settings.SMTP_HOST or "").strip()
    user = settings.smtp_user.strip()
    password = (settings.SMTP_PASSWORD or "").strip()
    if not (host and user and password):
        return False
    # Reject unedited .env placeholders so we fail early with a clear message
    placeholders = ("replace_with", "your.address@", "your-16-char", "example.com")
    blob = f"{user} {password}".lower()
    if any(p in blob for p in placeholders):
        return False
    return True


def smtp_status() -> dict:
    settings = get_settings()
    return {
        "smtp_configured": smtp_configured(),
        "smtp_host": (settings.SMTP_HOST or "").strip() or None,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user_set": bool(settings.smtp_user.strip()),
        "smtp_password_set": bool((settings.SMTP_PASSWORD or "").strip()),
        "smtp_from": settings.SMTP_FROM,
        "console_fallback": bool(settings.SMTP_CONSOLE_FALLBACK),
    }


def get_last_console_otp(email: str) -> str | None:
    """Return the last OTP logged for an email (test suite only)."""
    return _last_console_otps.get(email.strip().lower())


def clear_console_otps() -> None:
    _last_console_otps.clear()


def _send_smtp_message(to_email: str, subject: str, text_content: str, html_content: str) -> None:
    settings = get_settings()
    to_email = to_email.strip().lower()

    if not smtp_configured():
        if settings.SMTP_CONSOLE_FALLBACK:
            # Used strictly in automated unit/integration test runs
            logger.info("SMTP_CONSOLE_FALLBACK active for %s (test runner)", to_email)
            return

        missing = []
        host = (settings.SMTP_HOST or "").strip()
        user = settings.smtp_user.strip()
        password = (settings.SMTP_PASSWORD or "").strip()
        if not host:
            missing.append("SMTP_HOST")
        if not user or "replace_with" in user.lower() or "your.address@" in user.lower():
            missing.append("SMTP_USER (e.g. your Gmail address)")
        if not password or "replace_with" in password.lower() or "your-16-char" in password.lower():
            missing.append("SMTP_PASSWORD (e.g. 16-character Google App Password)")
        msg = (
            "SMTP is not configured with real credentials. Please configure: "
            + ", ".join(missing)
            + " in .env. Guide: https://myaccount.google.com/apppasswords"
        )
        logger.error("Email send failed: %s", msg)
        raise RuntimeError(msg)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    user = settings.smtp_user.strip()
    host = settings.SMTP_HOST.strip()
    port = settings.SMTP_PORT

    try:
        logger.info("Connecting to SMTP server at %s:%s (TLS=%s)...", host, port, settings.SMTP_USE_TLS)
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            logger.info("Authenticating with SMTP server as %s ...", user)
            server.login(user, settings.SMTP_PASSWORD.strip())
            server.send_message(msg)
        logger.info("Email delivered successfully to %s", to_email)
    except smtplib.SMTPAuthenticationError as exc:
        err_msg = (
            f"Gmail SMTP authentication failed (code {exc.smtp_code}). "
            "Please verify that your Gmail address and 16-character Google App Password in .env are correct. "
            "Guide: https://myaccount.google.com/apppasswords"
        )
        logger.error("Gmail SMTP authentication failed: %s", exc)
        raise RuntimeError(err_msg) from exc
    except (smtplib.SMTPConnectError, TimeoutError, OSError) as exc:
        err_msg = (
            f"Could not connect to SMTP server at {host}:{port}. "
            f"Network connection error: {exc}"
        )
        logger.error("SMTP Connection Error: %s", exc)
        raise RuntimeError(err_msg) from exc
    except smtplib.SMTPException as exc:
        logger.error("SMTP Error sending email to %s: %s", to_email, exc)
        raise RuntimeError(f"SMTP email delivery error: {exc}") from exc
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        raise


def send_verification_otp(to_email: str, otp: str, name: str | None = None) -> None:
    """Send real 6-digit email verification code via SMTP."""
    settings = get_settings()
    minutes = settings.OTP_EXPIRE_MINUTES
    greeting = f"Hi {name}," if name else "Hello,"
    subject = "Your AI JobShield Verification Code"

    text_body = (
        f"{greeting}\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code will expire in {minutes} minutes.\n"
        f"Please enter this code on AI JobShield to verify your email address.\n\n"
        f"If you did not request this, please ignore this email.\n"
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
    .card {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .badge {{ display: inline-block; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #2563eb; background: #eff6ff; padding: 12px 24px; border-radius: 8px; border: 1px solid #bfdbfe; margin: 20px 0; }}
    .footer {{ margin-top: 24px; font-size: 12px; color: #64748b; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <h2 style="margin-top:0; color:#0f172a;">AI JobShield Verification</h2>
    <p>{greeting}</p>
    <p>Thank you for registering with AI JobShield. Please use the following 6-digit verification code to activate your account:</p>
    <div style="text-align: center;">
      <div class="badge">{otp}</div>
    </div>
    <p style="font-size: 14px; color: #475569;">This code is valid for <strong>{minutes} minutes</strong> and can only be used once.</p>
    <div class="footer">
      <hr style="border:none; border-top:1px solid #e2e8f0; margin-bottom:16px;" />
      <p>If you did not create an account on AI JobShield, you can safely ignore this email.</p>
      <p>&copy; AI JobShield &mdash; Local Intelligent Fake Job &amp; Internship Detection</p>
    </div>
  </div>
</body>
</html>"""

    if settings.SMTP_CONSOLE_FALLBACK and not smtp_configured():
        _last_console_otps[to_email.strip().lower()] = otp

    _send_smtp_message(to_email, subject, text_body, html_body)


def send_password_reset_otp(to_email: str, otp: str, name: str | None = None) -> None:
    """Send 6-digit password reset code via SMTP."""
    settings = get_settings()
    minutes = settings.OTP_EXPIRE_MINUTES
    greeting = f"Hi {name}," if name else "Hello,"
    subject = "AI JobShield Password Reset Code"

    text_body = (
        f"{greeting}\n\n"
        f"Your password reset code is: {otp}\n\n"
        f"This code will expire in {minutes} minutes.\n"
        f"Enter this code on AI JobShield along with your new password to reset your account credentials.\n\n"
        f"If you did not request a password reset, please secure your account immediately.\n"
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
    .card {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .badge {{ display: inline-block; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #dc2626; background: #fef2f2; padding: 12px 24px; border-radius: 8px; border: 1px solid #fecaca; margin: 20px 0; }}
    .footer {{ margin-top: 24px; font-size: 12px; color: #64748b; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <h2 style="margin-top:0; color:#0f172a;">Password Reset Request</h2>
    <p>{greeting}</p>
    <p>We received a request to reset the password for your AI JobShield account. Use the code below to proceed:</p>
    <div style="text-align: center;">
      <div class="badge">{otp}</div>
    </div>
    <p style="font-size: 14px; color: #475569;">This code expires in <strong>{minutes} minutes</strong>.</p>
    <div class="footer">
      <hr style="border:none; border-top:1px solid #e2e8f0; margin-bottom:16px;" />
      <p>If you did not make this request, please ignore this email or review your security.</p>
      <p>&copy; AI JobShield</p>
    </div>
  </div>
</body>
</html>"""

    if settings.SMTP_CONSOLE_FALLBACK and not smtp_configured():
        _last_console_otps[to_email.strip().lower()] = otp

    _send_smtp_message(to_email, subject, text_body, html_body)
