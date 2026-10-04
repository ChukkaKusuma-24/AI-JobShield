"""Step 4 Company Identity, Acronym, and Domain Verification Tests.

Covers Cases A through K:
- Case A: Tata Consultancy Services + careers@tcs.com (official email, no mismatch)
- Case B: Tata Consultancy Services + https://www.tcs.com/careers (official URL, no mismatch)
- Case C: TCS + official domain (acronym resolution, matches canonical enterprise)
- Case D: TCS + Gmail (known enterprise + free webmail = impersonation risk)
- Case E: TCS + lookalike domain (imitation attempt flagged as lookalike + high risk)
- Case F: Genuine Infosys (official domain verified, positive indicators)
- Case G: Genuine unknown startup + Gmail (unverified, NOT enterprise impersonation)
- Case H: Genuine unknown startup + missing email (missing evidence handled properly)
- Case I: Known company + missing email (known company with incomplete contact capped <= 70)
- Case J: Known company + unrelated domain (mismatched domain flagged)
- Case K: Company verifier score propagation (verifier score reaches scoring engine)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_step4_company_identity.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-jobshield-company-identity"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, rules, scoring, url_analyzer
from app.services.company_verifier import (
    generate_acronym,
    normalize_company_name,
    resolve_company_identity,
    verify_company,
)

init_db()


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# -------------------------------------------------------------
# Unit Tests for Normalization and Acronym Resolution
# -------------------------------------------------------------

def test_normalization_and_acronym_generation():
    assert normalize_company_name("Tata Consultancy Services Limited") == "tata consultancy services"
    assert normalize_company_name("Infosys Pvt. Ltd.") == "infosys"
    assert normalize_company_name("Wipro Technologies Corp") == "wipro technologies"
    assert generate_acronym("Tata Consultancy Services") == "tcs"


def test_resolve_company_identity_tcs_and_full_name():
    id_full = resolve_company_identity("Tata Consultancy Services")
    id_acronym = resolve_company_identity("TCS")

    assert id_full.is_known_entity is True
    assert id_acronym.is_known_entity is True
    assert id_full.canonical_name == "Tata Consultancy Services"
    assert id_acronym.canonical_name == "Tata Consultancy Services"
    assert "tcs.com" in id_full.official_domains
    assert "tcs.com" in id_acronym.official_domains
    assert "tcs" in id_full.tokens
    assert "tcs" in id_acronym.tokens


# -------------------------------------------------------------
# Case A: Tata Consultancy Services + careers@tcs.com
# -------------------------------------------------------------

def test_case_a_tcs_full_name_official_email(db_session):
    company_name = "Tata Consultancy Services"
    email = "careers@tcs.com"
    url = "https://www.tcs.com/careers"

    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Senior Software Engineer",
        company_name=company_name,
        description=(
            "Tata Consultancy Services is hiring a Senior Software Engineer. "
            "Responsibilities include microservices design, Java development, and agile delivery. "
            "Qualifications: Bachelor's degree and 4+ years software development experience. "
            "Selection process includes technical screening and manager interview."
        ),
        salary="INR 12,00,000 - 16,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=email,
    )

    # 1. Company verification must recognize official domain
    assert comp_res["status"] == "VERIFIED"
    assert comp_res["is_known_entity"] is True

    # 2. No false email_domain_mismatch
    red_flag_ids = [f["id"] for f in flags]
    assert "email_domain_mismatch" not in red_flag_ids
    assert "company_impersonation" not in red_flag_ids
    assert "free_email" not in red_flag_ids

    # 3. Positive official email indicator awarded
    pos_ids = [p["id"] for p in positives]
    assert "official_email" in pos_ids

    # 4. Final score should be High Credibility / Low Risk (>= 80)
    assert score_res["trust_score"] >= 80
    assert score_res["risk_level"] == "LOW"


# -------------------------------------------------------------
# Case B: Tata Consultancy Services + https://www.tcs.com/careers
# -------------------------------------------------------------

def test_case_b_tcs_full_name_official_url():
    url_res = url_analyzer.analyze_url("https://www.tcs.com/careers", "Tata Consultancy Services")

    # Recognizes official domain
    indicator_ids = [i["id"] for i in url_res["indicators"]]
    assert "official_domain" in indicator_ids
    assert "company_mismatch" not in indicator_ids
    assert "lookalike_domain" not in indicator_ids
    assert url_res["risk_level"] == "LOW"
    assert url_res["risk_score"] == 0


# -------------------------------------------------------------
# Case C: TCS (Acronym) + official domain
# -------------------------------------------------------------

def test_case_c_tcs_acronym_resolution(db_session):
    company_name = "TCS"
    email = "recruitment@tcs.com"
    url = "https://www.tcs.com/careers"

    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Systems Engineer",
        company_name=company_name,
        description=(
            "TCS is looking for Systems Engineers to join our global engineering team. "
            "Responsibilities include implementing cloud infrastructure and monitoring distributed systems. "
            "Requirements: Degree in Engineering, hands-on knowledge of Linux and AWS. "
            "The selection process entails a written cognitive test and technical evaluation."
        ),
        salary="INR 8,00,000 - 12,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=email,
    )

    # Acronym 'TCS' resolves to canonical Tata Consultancy Services
    assert comp_res["status"] == "VERIFIED"
    assert comp_res["matched_entity"] == "Tata Consultancy Services"
    assert comp_res["is_known_entity"] is True

    # No false mismatch
    red_flag_ids = [f["id"] for f in flags]
    assert "email_domain_mismatch" not in red_flag_ids
    assert "company_impersonation" not in red_flag_ids

    # High credibility
    assert score_res["trust_score"] >= 80
    assert score_res["risk_level"] == "LOW"


# -------------------------------------------------------------
# Case D: TCS + Gmail (Enterprise Impersonation)
# -------------------------------------------------------------

def test_case_d_tcs_using_gmail_impersonation(db_session):
    company_name = "TCS"
    email = "tcs.recruitment.india@gmail.com"

    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=None)
    url_res = url_analyzer.analyze_url("", company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Process Associate",
        company_name=company_name,
        description=(
            "Immediate hiring for Process Associates at TCS. "
            "Candidates will handle international voice and non-voice client queries. "
            "Requirements: Any graduate with good English communication skills. "
            "Send resume directly to recruiter."
        ),
        salary="INR 25,000 per month",
        email=email,
        url=None,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=email,
    )

    # Resolved to known entity but flagged as impersonation risk
    assert comp_res["is_known_entity"] is True
    assert comp_res["status"] == "IMPERSONATION_RISK"
    assert comp_res["impersonation_detected"] is True

    # Must NOT receive official email credit
    pos_ids = [p["id"] for p in positives]
    assert "official_email" not in pos_ids

    # Hard guardrail cap <= 25 applies
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"


# -------------------------------------------------------------
# Case E: TCS + Lookalike Domain
# -------------------------------------------------------------

def test_case_e_tcs_lookalike_domain(db_session):
    url_res = url_analyzer.analyze_url(
        "http://tcs-careers-jobs-2026.xyz/verify",
        "TCS",
    )

    # Lookalike domain and company mismatch flagged with high risk
    indicator_ids = [i["id"] for i in url_res["indicators"]]
    assert "lookalike_domain" in indicator_ids
    assert "company_mismatch" in indicator_ids
    assert "official_domain" not in indicator_ids
    assert url_res["risk_level"] == "HIGH"
    assert url_res["risk_score"] >= 50

    # Pipeline integration
    comp_res = company_verifier.verify_company(
        db_session,
        "TCS",
        email="recruiter@tcs-careers-jobs-2026.xyz",
        website="http://tcs-careers-jobs-2026.xyz/verify",
    )
    flags, positives, bonus = rules.analyze_rules(
        title="Associate Analyst",
        company_name="TCS",
        description=(
            "Job opportunity at TCS. Click verify link to confirm your application details. "
            "Requirements: Basic computer skills and analytical aptitude."
        ),
        email="recruiter@tcs-careers-jobs-2026.xyz",
        url="http://tcs-careers-jobs-2026.xyz/verify",
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email="recruiter@tcs-careers-jobs-2026.xyz",
    )
    assert score_res["risk_level"] == "HIGH"
    assert score_res["trust_score"] <= 35


# -------------------------------------------------------------
# Case F: Genuine Infosys
# -------------------------------------------------------------

def test_case_f_genuine_infosys(db_session):
    company_name = "Infosys"
    email = "careers@infosys.com"
    url = "https://www.infosys.com/careers"

    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Technology Lead",
        company_name=company_name,
        description=(
            "Infosys is seeking an experienced Technology Lead. "
            "You will lead architecture discussions, guide agile development teams, and develop cloud-native applications. "
            "Qualifications: BE/BTech/MCA with 6+ years experience in Java, Microservices, and Cloud. "
            "Selection process comprises technical interview rounds and client presentation."
        ),
        salary="INR 14,00,000 - 18,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=email,
    )

    assert comp_res["status"] == "VERIFIED"
    assert comp_res["matched_entity"] == "Infosys"
    assert "email_domain_mismatch" not in [f["id"] for f in flags]
    assert "official_email" in [p["id"] for p in positives]
    assert score_res["trust_score"] >= 80
    assert score_res["risk_level"] == "LOW"


# -------------------------------------------------------------
# Case G: Genuine Unknown Startup + Gmail
# -------------------------------------------------------------

def test_case_g_genuine_unknown_startup_gmail(db_session):
    company_name = "PixelCraft Studios"
    email = "pixelcraft.founder@gmail.com"

    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=None)
    url_res = url_analyzer.analyze_url("", company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Junior Frontend Developer",
        company_name=company_name,
        description=(
            "PixelCraft Studios is an early-stage creative technology studio looking for a Junior Frontend Developer. "
            "Responsibilities: Build responsive interactive components using React and Tailwind CSS, integrate REST APIs. "
            "Requirements: Good understanding of JavaScript (ES6+), HTML5, CSS3, and React. Portfolio or GitHub projects required. "
            "Interview process includes portfolio review and a practical coding interview."
        ),
        salary="INR 4,50,000 - 6,00,000 per annum",
        email=email,
        url=None,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=email,
    )

    # Startup is unverified, NOT impersonation
    assert comp_res["status"] == "UNVERIFIED"
    assert comp_res["is_known_entity"] is False
    assert comp_res["impersonation_detected"] is False

    red_flag_ids = [f["id"] for f in flags]
    assert "company_impersonation" not in red_flag_ids
    assert "free_email" in red_flag_ids

    # Unverified startup with Gmail capped sensibly in Medium Risk, NOT collapsed to scam (score >= 40 and <= 65)
    assert 40 <= score_res["trust_score"] <= 65
    assert score_res["risk_level"] == "MEDIUM"


# -------------------------------------------------------------
# Case H: Genuine Unknown Startup + Missing Email
# -------------------------------------------------------------

def test_case_h_unknown_startup_missing_email(db_session):
    company_name = "Novatech Labs"
    url = "https://www.novatechlabs.io"

    comp_res = company_verifier.verify_company(db_session, company_name, email=None, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Full Stack Engineer",
        company_name=company_name,
        description=(
            "Novatech Labs is developing next-gen analytics software. "
            "Responsibilities include building frontend dashboards and scalable Python backend services. "
            "Qualifications: 2+ years of full stack experience with Python and React. "
            "Interview process includes technical screening and system design discussion."
        ),
        salary="INR 9,00,000 - 13,00,000 per annum",
        email=None,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=None,
    )

    assert comp_res["status"] == "UNVERIFIED"
    assert score_res["score_breakdown"]["dimensions"]["contact_consistency"]["evidence_class"] == "MISSING_EVIDENCE"
    assert score_res["trust_score"] <= 65
    assert score_res["risk_level"] == "MEDIUM"


# -------------------------------------------------------------
# Case I: Known Company + Missing Email
# -------------------------------------------------------------

def test_case_i_known_company_missing_email(db_session):
    company_name = "Tata Consultancy Services"

    comp_res = company_verifier.verify_company(db_session, company_name, email=None, website=None)
    url_res = url_analyzer.analyze_url("", company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Data Engineer",
        company_name=company_name,
        description=(
            "Tata Consultancy Services is seeking a Data Engineer. "
            "You will build data pipelines using PySpark and SQL, and deploy workflows on Azure. "
            "Requirements: Degree in Computer Science with 3+ years in data engineering. "
            "Hiring process involves technical evaluation and manager round."
        ),
        salary="INR 10,00,000 - 14,00,000 per annum",
        email=None,
        url=None,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=None,
    )

    # Known company without contact email is partially verified
    assert comp_res["status"] == "PARTIALLY VERIFIED"
    assert comp_res["is_known_entity"] is True
    # Contact consistency is missing evidence
    assert score_res["score_breakdown"]["dimensions"]["contact_consistency"]["evidence_class"] == "MISSING_EVIDENCE"
    # Score capped appropriately at <= 70 (Medium Risk)
    assert score_res["trust_score"] <= 70
    assert score_res["risk_level"] == "MEDIUM"


# -------------------------------------------------------------
# Case J: Known Company + Unrelated Domain
# -------------------------------------------------------------

def test_case_j_known_company_unrelated_domain(db_session):
    company_name = "Tata Consultancy Services"
    email = "hr-tcs@quickjob-recruiters-hub.org"
    url = "https://www.quickjob-recruiters-hub.org/apply"

    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="HR Coordinator",
        company_name=company_name,
        description=(
            "TCS is recruiting HR Coordinators for our enterprise operations. "
            "Manage candidate documentation and onboarding logistics. "
            "Apply via our third-party recruitment partner."
        ),
        salary="INR 30,000 per month",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        None,
        False,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=email,
    )

    # Domain mismatch detected for verified enterprise
    assert comp_res["status"] == "IMPERSONATION_RISK"
    red_flag_ids = [f["id"] for f in flags]
    assert "email_domain_mismatch" in red_flag_ids or "company_impersonation" in red_flag_ids
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"


# -------------------------------------------------------------
# Case K: Company Verifier Score Propagation Test
# -------------------------------------------------------------

def test_case_k_company_verifier_score_propagation():
    # Test that verify_company returns both 'score' and 'company_score'
    ver_res = verify_company(None, "Tata Consultancy Services", email="careers@tcs.com", website="https://www.tcs.com")
    assert "score" in ver_res
    assert "company_score" in ver_res
    assert ver_res["score"] == 95
    assert ver_res["company_score"] == 95

    # Test that compute_trust_score reads company_score and score directly
    score_res = scoring.compute_trust_score(
        red_flags=[],
        positive_bonus=10,
        ml_scam_probability=0.05,
        ml_available=True,
        company_result={"status": "PARTIALLY VERIFIED", "company_score": 58, "checks": []},
        url_result={"url": "https://example.com", "valid": True, "risk_level": "LOW", "indicators": []},
        positive_indicators=[{"id": "detailed_responsibilities", "evidence_class": "POSITIVE_EVIDENCE"}],
    )
    # The score should reflect company dimension = 58.0, not hardcoded 65.0
    assert score_res["score_breakdown"]["dimensions"]["company_verification"]["score"] == 58.0
