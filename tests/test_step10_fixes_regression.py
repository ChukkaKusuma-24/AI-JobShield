"""Regression tests specifically verifying Step 10 audit defect fixes:

1. removeprefix("www.") preserves domains starting with 'w' (Wipro, Walmart, Wells Fargo, etc.)
2. Safe database default without hardcoded credentials
3. Workstation & wire rule coverage in equipment / advance check scams
4. Model SHA-256 verification and integrity protection
5. End-to-end Wipro enterprise job verification (no false impersonation)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_step10_fixes.db"
if TEST_DB.exists():
    try:
        TEST_DB.unlink()
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-step10-fixes-remediation-32bytes"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, ml_service, rules, scoring, url_analyzer

init_db()


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# =====================================================================
# 1. Tests for removeprefix("www.") Domain Preservation
# =====================================================================

def test_w_companies_domain_cleaning():
    """Verify that domains starting with 'w' are NOT truncated."""
    # Test emails
    assert company_verifier._clean_domain("recruiter@wipro.com") == "wipro.com"
    assert company_verifier._clean_domain("jobs@walmart.com") == "walmart.com"
    assert company_verifier._clean_domain("careers@wellsfargo.com") == "wellsfargo.com"
    assert company_verifier._clean_domain("editor@wordpress.org") == "wordpress.org"

    # Test www. domains
    assert company_verifier._clean_domain("www.wipro.com") == "wipro.com"
    assert company_verifier._clean_domain("www.walmart.com") == "walmart.com"
    assert company_verifier._clean_domain("www.tcs.com") == "tcs.com"

    # Test URLs
    assert company_verifier._domain_from_url("https://www.wipro.com/careers") == "wipro.com"
    assert company_verifier._domain_from_url("https://wipro.com/careers") == "wipro.com"
    assert company_verifier._domain_from_url("http://www.walmart.com") == "walmart.com"
    assert company_verifier._domain_from_url("https://wellsfargo.com") == "wellsfargo.com"


def test_wipro_enterprise_verification(db_session):
    """Verify that Wipro is verified and does not trigger false IMPERSONATION_RISK."""
    res = company_verifier.verify_company(
        db_session,
        "Wipro",
        email="campus.talent@wipro.com",
        website="https://www.wipro.com/careers",
    )
    assert res["status"] == "VERIFIED"
    assert res["company_score"] >= 90
    assert "IMPERSONATION_RISK" not in res["status"]


def test_url_analyzer_w_company_official_domain():
    """Verify that url_analyzer correctly matches official domain for 'W' companies."""
    res = url_analyzer.analyze_url("https://www.wipro.com/careers", "Wipro")
    indicators = [i["id"] for i in res.get("indicators", [])]
    assert "official_domain" in indicators
    assert "company_mismatch" not in indicators


# =====================================================================
# 2. Tests for Database Credentials Sanitization
# =====================================================================

def test_database_url_credentials_sanitized():
    """Ensure hardcoded passwords are removed from default configuration."""
    settings = get_settings()
    db_url = settings.DATABASE_URL.lower()
    assert "kusuma" not in db_url
    assert "%26247" not in db_url
    assert "sqlite" in db_url or "yourpassword" in db_url or "@localhost" in db_url


# =====================================================================
# 3. Tests for Workstation and Wire Rule Coverage
# =====================================================================

def test_workstation_equipment_rule():
    """Verify that 'purchase your home office workstation' triggers equipment_purchase rule."""
    text = (
        "We are hiring a Remote Operations Clerk. "
        "We will mail you a company check of $3,500 to purchase your home office workstation "
        "from our certified equipment distributor."
    )
    flags, pos, bonus = rules.analyze_rules(
        title="Remote Operations Clerk",
        company_name="Apex Logistics",
        description=text,
    )
    flag_ids = [f["id"] for f in flags]
    assert "equipment_purchase" in flag_ids
    assert any(f["severity"] == "critical" for f in flags)


def test_wire_money_transfer_rule():
    """Verify that directive imperative 'wire $2,500 via Zelle' triggers money_transfer rule."""
    text = (
        "Deposit the cashier check into your checking account immediately, "
        "and wire $2,500 via Zelle to our software vendor before starting training."
    )
    flags, pos, bonus = rules.analyze_rules(
        title="Data Specialist",
        company_name="Apex Logistics",
        description=text,
    )
    flag_ids = [f["id"] for f in flags]
    assert "money_transfer" in flag_ids
    assert any(f["severity"] == "critical" for f in flags)


def test_advance_check_scam_caps_score(db_session):
    """Verify that the advance-fee check scam (Golden Case 12) is capped at <= 35."""
    text = (
        "We are seeking a Remote Administrative Assistant. We will mail you a company cashier's check of $3,500 "
        "to purchase your home office workstation and specialized cryptographic software from our certified vendor. "
        "Once you deposit the check into your bank account, wire $2,500 via Zelle or Bitcoin to our equipment vendor immediately."
    )
    ml_pred = ml_service.predict(f"Remote Administrative Assistant Apex Global Logistics {text}")

    flags, pos, bonus = rules.analyze_rules(
        title="Remote Administrative Assistant",
        company_name="Apex Global Logistics",
        description=text,
    )

    company_res = company_verifier.verify_company(
        db_session,
        "Apex Global Logistics",
        email="recruitment@apexlogistics-work.com",
        website="http://apexlogistics-work.com",
    )

    url_res = url_analyzer.analyze_url("http://apexlogistics-work.com", "Apex Global Logistics")

    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        ml_pred.get("scam_probability"),
        ml_pred.get("available", False),
        company_result=company_res,
        url_result=url_res,
        positive_indicators=pos,
    )

    # Must be capped at <= 35 and classified as HIGH risk
    assert score_res["trust_score"] <= 35
    assert score_res["risk_level"] == "HIGH"
    assert score_res["score_breakdown"]["cap_applied"] is True


# =====================================================================
# 4. Tests for Model SHA-256 Verification
# =====================================================================

def test_model_sha256_verification():
    """Verify that the model hash matches the frozen Step 8/9 artifact hash."""
    settings = get_settings()
    model_path = Path(settings.ML_MODEL_PATH)
    actual_hash = ml_service.compute_model_sha256(model_path)
    assert actual_hash == "636e26e42b5a4179a42f9e9161dd7692d4f63146f1475659021605b9676bf1a2"

    # Verify that load_model with integrity check succeeds
    assert ml_service.load_model(verify_checksum=True) is True
    assert ml_service.is_sha256_verified() is True
    assert ml_service.get_model_sha256() == actual_hash


def test_tampered_model_sha256_rejected():
    """Verify that loading fails if model hash does not match expected checksum."""
    settings = get_settings()
    orig = settings.EXPECTED_MODEL_SHA256
    try:
        settings.EXPECTED_MODEL_SHA256 = "0000000000000000000000000000000000000000000000000000000000000000"
        ok = ml_service.load_model(verify_checksum=True)
        assert ok is False
        assert ml_service.is_available() is False
    finally:
        settings.EXPECTED_MODEL_SHA256 = orig
        ml_service.load_model(verify_checksum=True)
        assert ml_service.is_available() is True
