"""Backend API tests for AI JobShield."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Use a temp SQLite DB for tests
TEST_DB = ROOT / "database" / "test_jobshield.db"
if TEST_DB.exists():
    TEST_DB.unlink()

import os

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-jobshield"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_USERNAME"] = ""
os.environ["SMTP_PASSWORD"] = ""

from app.config import get_settings

get_settings.cache_clear()

from app.database import Base, engine, init_db
from app.main import app
from app.services import ml_service

init_db()
ml_service.load_model()

client = TestClient(app)


@pytest.fixture
def auth_headers():
    from app.services.email_service import get_last_console_otp

    email = "tester@example.com"
    r = client.post(
        "/api/auth/register",
        json={"name": "Tester", "email": email, "password": "password123"},
    )
    if r.status_code == 201:
        otp = get_last_console_otp(email)
        assert otp, "Expected console OTP when SMTP is not configured"
        v = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
        assert v.status_code == 200, v.text
        token = v.json()["token"]
    else:
        # Already registered from a prior test in this session
        r = client.post("/api/auth/login", json={"email": email, "password": "password123"})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "ml_available" in body
    assert "ocr_available" in body


def test_register_validation():
    r = client.post(
        "/api/auth/register",
        json={"name": "A", "email": "bad", "password": "short"},
    )
    assert r.status_code in (400, 422)


def test_email_otp_verification_flow():
    from app.database import SessionLocal
    from app.models import User
    from app.services.email_service import get_last_console_otp

    email = "otp-user@example.com"
    r = client.post(
        "/api/auth/register",
        json={"name": "OTP User", "email": email, "password": "password123"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["requires_verification"] is True
    assert "token" not in body

    # Unverified users cannot log in
    denied = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"

    otp = get_last_console_otp(email)
    assert otp and otp.isdigit()

    # OTP stored hashed in EmailOtp, not plaintext
    from app.models import EmailOtp

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.is_verified is False
        otp_rec = db.query(EmailOtp).filter(EmailOtp.user_id == user.id, EmailOtp.purpose == "verification").first()
        assert otp_rec is not None
        assert otp_rec.otp_hash is not None
        assert otp_rec.otp_hash != otp
        assert not user.password_hash.startswith("password")
    finally:
        db.close()

    bad = client.post("/api/auth/verify-email", json={"email": email, "otp": "000000"})
    assert bad.status_code == 400

    ok = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert ok.status_code == 200
    assert ok.json()["token"]
    assert ok.json()["user"]["is_verified"] is True

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user.is_verified is True
        otp_rec = db.query(EmailOtp).filter(EmailOtp.user_id == user.id, EmailOtp.purpose == "verification").first()
        assert otp_rec is None
    finally:
        db.close()

    # Already verified accounts can sign in; old OTP is no longer stored
    login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200


def test_forgot_and_reset_password_flow():
    from app.services.email_service import get_last_console_otp

    email = "reset-tester@example.com"
    # Register and verify account first
    reg = client.post(
        "/api/auth/register",
        json={"name": "Reset Tester", "email": email, "password": "password123"},
    )
    assert reg.status_code == 201
    reg_otp = get_last_console_otp(email)
    assert reg_otp
    ver = client.post("/api/auth/verify-email", json={"email": email, "otp": reg_otp})
    assert ver.status_code == 200

    # Request password reset code
    r = client.post("/api/auth/forgot-password", json={"email": email})
    assert r.status_code == 200

    otp = get_last_console_otp(email)
    assert otp and otp.isdigit()

    # Reset password with valid code and strong password
    new_pw = "NewSecurePass2026!"
    r2 = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp": otp, "new_password": new_pw},
    )
    assert r2.status_code == 200

    # Old password fails
    old_login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert old_login.status_code == 401

    # New password succeeds
    new_login = client.post("/api/auth/login", json={"email": email, "password": new_pw})
    assert new_login.status_code == 200
    assert "token" in new_login.json()


def test_protected_route_rejects_unauthenticated():
    r = client.get("/api/dashboard")
    assert r.status_code == 401

    r2 = client.get("/api/dashboard", headers={"Authorization": "Bearer invalid.token.value"})
    assert r2.status_code == 401


def test_analyze_scam_like(auth_headers):
    payload = {
        "title": "Work From Home Data Entry Instant",
        "company_name": "Quick Cash Careers",
        "description": (
            "URGENT hiring! Work from home and earn 5000/day. No interview needed. "
            "Pay registration fee of 1499 via UPI to join. Contact on WhatsApp only. "
            "Guaranteed job for freshers. Limited seats apply within 24 hours."
        ),
        "salary": "5000/day",
        "email": "hr1@gmail.com",
        "url": "http://quick-cash-jobs.xyz/apply",
        "job_type": "Part-time",
    }
    r = client.post("/api/analyze", json=payload, headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "trust_score" in data
    assert data["risk_level"] in ("HIGH", "MEDIUM", "LOW")
    assert "red_flags" in data
    assert "disclaimer" in data
    assert "FAKE" not in data.get("explanation", "").upper().split()
    assert "REAL" not in (data.get("explanation") or "")
    # Fee request should trigger critical-ish score
    assert data["trust_score"] <= 70
    assert any(f["id"] == "fee_request" for f in data["red_flags"])


def test_analyze_short_description(auth_headers):
    r = client.post(
        "/api/analyze",
        json={
            "title": "Job",
            "company_name": "Acme",
            "description": "too short",
        },
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_url_analyze(auth_headers):
    r = client.post(
        "/api/url/analyze",
        json={"url": "http://login-verify-bonus.tk/claim", "company_name": "Infosys"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert "suspicious" in body["explanation"].lower() or body["risk_score"] >= 0


def test_company_verify(auth_headers):
    r = client.post(
        "/api/company/verify",
        json={
            "company_name": "Infosys",
            "email": "careers@infosys.com",
            "website": "https://www.infosys.com",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in (
        "VERIFIED",
        "PARTIALLY VERIFIED",
        "NOT VERIFIED",
        "UNABLE TO VERIFY",
    )


def test_history_and_feedback(auth_headers):
    payload = {
        "title": "Backend Developer",
        "company_name": "Zoho",
        "description": (
            "We are hiring a Backend Developer at Zoho. Responsibilities include designing APIs, "
            "writing tests, and documenting services. Qualifications: CS degree, Python experience. "
            "Interview process includes technical and HR rounds. Apply via careers@zoho.com."
        ),
        "email": "careers@zoho.com",
        "url": "https://www.zoho.com/careers",
    }
    r = client.post("/api/analyze", json=payload, headers=auth_headers)
    assert r.status_code == 200
    aid = r.json()["analysis_id"]

    h = client.get("/api/history", headers=auth_headers)
    assert h.status_code == 200
    assert h.json()["total"] >= 1

    detail = client.get(f"/api/history/{aid}", headers=auth_headers)
    assert detail.status_code == 200

    fb = client.post(
        "/api/feedback",
        json={"analysis_id": aid, "label": "correct", "comment": "looks fine"},
        headers=auth_headers,
    )
    assert fb.status_code == 201


def test_dashboard(auth_headers):
    r = client.get("/api/dashboard", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "total_analyses" in body
    assert "risk_distribution" in body
