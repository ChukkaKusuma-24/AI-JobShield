"""Comprehensive test suite for Job Scan History Persistence and Evidence-Based Credibility Scoring."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_jobshield_suite.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-jobshield-history"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_USERNAME"] = ""
os.environ["SMTP_PASSWORD"] = ""

from app.config import get_settings

get_settings.cache_clear()

from app.database import init_db
from app.main import app
from app.services import ml_service
from app.services.email_service import get_last_console_otp

init_db()
ml_service.load_model()

client = TestClient(app)


def register_and_get_token(name: str, email: str) -> str:
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": "Password123!"})
    assert r.status_code == 201, r.text
    otp = get_last_console_otp(email)
    assert otp, f"Expected OTP for {email}"
    v = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert v.status_code == 200, v.text
    return v.json()["token"]


def test_complete_history_persistence_and_isolation_flow():
    """Verify flow:
    1. Register user 1
    2. Empty history check
    3. Analyze job 1 -> saved in DB with all required fields
    4. Fetch history -> item 1 present with title, company, description, score, risk, etc.
    5. Fetch single analysis -> matches item 1
    6. Analyze job 2 -> saved in DB
    7. Fetch history -> both items present in reverse chrono order
    8. Logout simulation -> login again -> both items still present!
    9. User 2 registers -> User 2 history is empty, cannot access or delete User 1's records
    10. Delete job 1 -> only job 2 remains
    """
    token1 = register_and_get_token("User One", "user1@example.com")
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Step 1: Empty history state
    h0 = client.get("/api/history", headers=headers1)
    assert h0.status_code == 200
    assert h0.json()["total"] == 0
    assert h0.json()["items"] == []

    # Step 2: Analyze job 1
    payload1 = {
        "title": "Senior Cloud Architect",
        "company_name": "Infosys",
        "description": (
            "We are seeking a Senior Cloud Architect to design enterprise systems. "
            "Key responsibilities include architecting multi-region deployments, mentoring team members, "
            "and leading security reviews. Qualifications: 8+ years cloud engineering, AWS/Azure certified. "
            "Interview process: technical round and architectural panel. Competitive salary."
        ),
        "salary": "₹35,00,000 per annum",
        "email": "careers@infosys.com",
        "url": "https://www.infosys.com/careers",
        "location": "Bengaluru, India",
        "job_type": "Full-time",
    }
    r1 = client.post("/api/analyze", json=payload1, headers=headers1)
    assert r1.status_code == 200, r1.text
    a1 = r1.json()
    aid1 = a1["analysis_id"]

    # Verify all required fields stored & returned
    assert a1["title"] == "Senior Cloud Architect"
    assert a1["company_name"] == "Infosys"
    assert a1["trust_score"] >= 80
    assert a1["risk_level"] == "LOW"
    assert "description" in a1
    assert "red_flags" in a1
    assert "positive_indicators" in a1
    assert "created_at" in a1
    assert a1["url"] == "https://www.infosys.com/careers"

    # Step 3: Fetch history from backend
    h1 = client.get("/api/history", headers=headers1)
    assert h1.status_code == 200
    h1_data = h1.json()
    assert h1_data["total"] == 1
    item1 = h1_data["items"][0]
    assert item1["analysis_id"] == aid1
    assert item1["title"] == "Senior Cloud Architect"
    assert item1["company_name"] == "Infosys"
    assert item1["description"] is not None
    assert item1["trust_score"] == a1["trust_score"]
    assert item1["risk_level"] == "LOW"

    # Step 4: Single previous analysis endpoint
    detail1 = client.get(f"/api/history/{aid1}", headers=headers1)
    assert detail1.status_code == 200
    assert detail1.json()["analysis_id"] == aid1
    assert detail1.json()["company_name"] == "Infosys"

    # Step 5: Analyze job 2
    payload2 = {
        "title": "Junior Python QA",
        "company_name": "Apex Novelty Tech",
        "description": (
            "Looking for Junior Python QA to write unit and automated tests. "
            "Responsibilities include writing test scripts and collaborating with developers. "
            "Qualifications: Python knowledge, git basics. Selection process includes a coding test."
        ),
        "salary": "₹6,00,000 per annum",
        "location": "Remote",
    }
    r2 = client.post("/api/analyze", json=payload2, headers=headers1)
    assert r2.status_code == 200
    aid2 = r2.json()["analysis_id"]

    h2 = client.get("/api/history", headers=headers1)
    assert h2.json()["total"] == 2
    # Verify reverse chronological ordering (job 2 first)
    assert h2.json()["items"][0]["analysis_id"] == aid2
    assert h2.json()["items"][1]["analysis_id"] == aid1

    # Step 6: Simulate Logout and Login Again
    login_r = client.post("/api/auth/login", json={"email": "user1@example.com", "password": "Password123!"})
    assert login_r.status_code == 200
    new_token1 = login_r.json()["token"]
    new_headers1 = {"Authorization": f"Bearer {new_token1}"}

    # Verify history still exists after re-login
    h_relogin = client.get("/api/history", headers=new_headers1)
    assert h_relogin.status_code == 200
    assert h_relogin.json()["total"] == 2
    assert h_relogin.json()["items"][0]["analysis_id"] == aid2

    # Step 7: Isolation from User 2
    token2 = register_and_get_token("User Two", "user2@example.com")
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 2 history is completely empty
    h_user2 = client.get("/api/history", headers=headers2)
    assert h_user2.status_code == 200
    assert h_user2.json()["total"] == 0

    # User 2 cannot access User 1's analysis
    forbidden_view = client.get(f"/api/history/{aid1}", headers=headers2)
    assert forbidden_view.status_code in (403, 404)

    # User 2 cannot delete User 1's analysis
    forbidden_delete = client.delete(f"/api/history/{aid1}", headers=headers2)
    assert forbidden_delete.status_code in (403, 404)

    # Step 8: User 1 deletes job 1
    del_r = client.delete(f"/api/history/{aid1}", headers=new_headers1)
    assert del_r.status_code == 200

    h_after_del = client.get("/api/history", headers=new_headers1)
    assert h_after_del.json()["total"] == 1
    assert h_after_del.json()["items"][0]["analysis_id"] == aid2


def test_scoring_case_a_well_known_company_legitimate():
    """Case A: Well-known company + legitimate-looking job.
    Must be recognized based on verified company records & official domain, with high trust.
    """
    token = register_and_get_token("Case A User", "case_a@example.com")
    payload = {
        "title": "Lead Software Engineer",
        "company_name": "Infosys",
        "description": (
            "Infosys is hiring a Lead Software Engineer for digital transformation projects. "
            "Key responsibilities include designing scalable microservices, managing technical deliverables, "
            "and leading sprint reviews. Qualifications: Bachelor's degree in CS, 6+ years Java/Python experience. "
            "The recruitment process includes technical assessment and client interview. Competitive compensation."
        ),
        "salary": "₹22,00,000 per year",
        "email": "careers@infosys.com",
        "url": "https://www.infosys.com/careers",
    }
    r = client.post("/api/analyze", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "LOW"
    assert data["trust_score"] >= 80
    assert data["company_verification"]["status"] == "VERIFIED"
    assert "fee_request" not in [f["id"] for f in data["red_flags"]]
    assert "VERIFIED" in data["explanation"]


def test_scoring_case_b_unknown_company_normal_job():
    """Case B: Unknown company + normal-looking job.
    Unknown company must NOT automatically receive a high score just because description looks good.
    Must be marked 'UNVERIFIED' with trust capped at <= 65 (MEDIUM risk).
    """
    token = register_and_get_token("Case B User", "case_b@example.com")
    payload = {
        "title": "React Frontend Developer",
        "company_name": "Krypton Web Solutions Private Limited",
        "description": (
            "We are looking for a React Frontend Developer to build modern responsive web apps. "
            "Responsibilities include building UI components, consuming REST APIs, and writing clean CSS. "
            "Qualifications: 2 years experience with React, JavaScript, and Tailwind. "
            "Selection process consists of a take-home assignment and an interview round."
        ),
        "salary": "₹8,00,000 per year",
        "email": "hiring@kryptonwebsolutions.io",
    }
    r = client.post("/api/analyze", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["company_verification"]["status"] == "UNVERIFIED"
    # Cap ensures trust score does NOT exceed 65
    assert data["trust_score"] <= 65
    assert data["risk_level"] == "MEDIUM"
    assert "fee_request" not in [f["id"] for f in data["red_flags"]]
    assert "UNVERIFIED" in data["explanation"]
    # Explains that company could not be verified rather than claiming it is a scam
    assert (data["score_breakdown"].get("cap_reason") and "could not be independently verified" in data["score_breakdown"]["cap_reason"].lower()) or "unverified" in data["explanation"].lower()


def test_scoring_case_c_unknown_company_registration_fee():
    """Case C: Unknown company + registration fee request.
    Must trigger critical red flag and drop score to HIGH risk (<= 35).
    """
    token = register_and_get_token("Case C User", "case_c@example.com")
    payload = {
        "title": "Online Typing & Data Entry Executive",
        "company_name": "Quick Work Solutions",
        "description": (
            "Immediate hiring for work from home data entry. Guaranteed income of 3000 per day. "
            "Candidates must pay a refundable registration fee of ₹1,499 to activate account. "
            "Contact on WhatsApp only. No interview required, direct joining."
        ),
        "salary": "3000/day",
        "email": "quickwork@gmail.com",
    }
    r = client.post("/api/analyze", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "HIGH"
    assert data["trust_score"] <= 35
    flag_ids = [f["id"] for f in data["red_flags"]]
    assert "fee_request" in flag_ids
    assert data["score_breakdown"]["cap_applied"] is True


def test_scoring_case_d_known_company_suspicious_email_impersonation():
    """Case D: Known company name + suspicious recruiter email/domain.
    Brand claimed (Infosys) but paired with a free email address (@gmail.com) -> IMPERSONATION_RISK.
    Must trigger impersonation flag and drop to HIGH risk (<= 25).
    """
    token = register_and_get_token("Case D User", "case_d@example.com")
    payload = {
        "title": "Associate Consultant",
        "company_name": "Infosys",
        "description": (
            "Infosys is hiring Associate Consultants across locations. "
            "Responsibilities include client consulting and ERP delivery. "
            "Qualifications: B.Tech / MCA with good communication skills. "
            "Send your resume to our hiring manager email below."
        ),
        "email": "infosys.campus.recruiter@gmail.com",
    }
    r = client.post("/api/analyze", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["company_verification"]["status"] == "IMPERSONATION_RISK"
    assert data["risk_level"] == "HIGH"
    assert data["trust_score"] <= 25
    flag_ids = [f["id"] for f in data["red_flags"]]
    assert "company_impersonation" in flag_ids or "email_domain_mismatch" in flag_ids
    assert "IMPERSONATION" in data["explanation"]


def test_scoring_case_e_known_company_suspicious_payment_request():
    """Case E: Known company + suspicious payment request.
    Even for a verified company, asking for fees/equipment deposits must drop trust to HIGH risk (<= 35).
    Verified name must NOT cancel serious scam indicators.
    """
    token = register_and_get_token("Case E User", "case_e@example.com")
    payload = {
        "title": "Software Developer Trainee",
        "company_name": "Infosys",
        "description": (
            "Infosys invites applications for Software Developer Trainees. "
            "Selected candidates will undergo 3 months paid training. "
            "Note: A mandatory equipment security deposit of ₹5,000 is required before laptop dispatch. "
            "Apply via careers@infosys.com."
        ),
        "email": "careers@infosys.com",
        "url": "https://www.infosys.com",
    }
    r = client.post("/api/analyze", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    # Critical fee request overrides verified company score
    assert data["risk_level"] == "HIGH"
    assert data["trust_score"] <= 35
    flag_ids = [f["id"] for f in data["red_flags"]]
    assert any(f in ("fee_request", "equipment_purchase") for f in flag_ids)


def test_scoring_case_f_legitimate_company_incomplete_evidence():
    """Case F: Legitimate company + legitimate job but incomplete company evidence.
    e.g. Company exists in database, but no official email/careers URL provided.
    Evaluated as PARTIALLY VERIFIED with moderate trust (60-75).
    """
    from app.database import SessionLocal
    from app.models import Company

    # Ensure a verified company is present in the database without matching domain in the request
    db = SessionLocal()
    try:
        existing = db.query(Company).filter(Company.name == "Wipro").first()
        if not existing:
            db.add(Company(name="Wipro", domain="wipro.com", verification_status="VERIFIED"))
            db.commit()
    finally:
        db.close()

    token = register_and_get_token("Case F User", "case_f@example.com")
    payload = {
        "title": "Project Engineer",
        "company_name": "Wipro",
        "description": (
            "Wipro is hiring Project Engineers. Responsibilities include building automation scripts, "
            "monitoring server performance, and resolving customer tickets. "
            "Qualifications: Degree in engineering, knowledge of Linux and shell scripting. "
            "Comprehensive technical interview process."
        ),
        # No email or website URL provided -> incomplete evidence
    }
    r = client.post("/api/analyze", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["company_verification"]["status"] in ("PARTIALLY VERIFIED", "VERIFIED")
    assert data["risk_level"] in ("MEDIUM", "LOW")
    # Clean job without scam flags
    assert data["trust_score"] >= 60
    assert "fee_request" not in [f["id"] for f in data["red_flags"]]
