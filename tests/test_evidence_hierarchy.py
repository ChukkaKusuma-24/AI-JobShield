from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_evidence_suite.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-jobshield-evidence"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, explain, ml_service, rules, scoring, url_analyzer
from app.services.evidence import EvidenceClass, classify_positive_signal, classify_rule_signal

init_db()


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def ml_model():
    ml_service.load_model()
    return ml_service


# =====================================================================
# Unit Tests for Evidence Classes
# =====================================================================

def test_evidence_classification_helpers():
    """Verify that rule signals and positive signals map to correct evidence classes."""
    # Critical flags
    assert classify_rule_signal("fee_request", "critical") == EvidenceClass.CRITICAL
    assert classify_rule_signal("money_transfer", "critical") == EvidenceClass.CRITICAL
    assert classify_rule_signal("equipment_purchase", "critical") == EvidenceClass.CRITICAL
    assert classify_rule_signal("company_impersonation", "critical") == EvidenceClass.CRITICAL
    assert classify_rule_signal("sensitive_info", "critical") == EvidenceClass.CRITICAL

    # Negative flags
    assert classify_rule_signal("suspicious_contact", "high") == EvidenceClass.NEGATIVE
    assert classify_rule_signal("free_email", "medium") == EvidenceClass.NEGATIVE
    assert classify_rule_signal("email_domain_mismatch", "high") == EvidenceClass.NEGATIVE
    assert classify_rule_signal("urgency", "medium") == EvidenceClass.NEGATIVE
    assert classify_rule_signal("vague_description", "medium") == EvidenceClass.NEGATIVE

    # Positive signals
    ev_class, strength = classify_positive_signal("official_email")
    assert ev_class == EvidenceClass.POSITIVE
    assert strength == "strong"

    ev_class, strength = classify_positive_signal("company_verified")
    assert ev_class == EvidenceClass.POSITIVE
    assert strength == "strong"

    # Neutral absence of negative pattern
    ev_class, strength = classify_positive_signal("no_fee")
    assert ev_class == EvidenceClass.MISSING
    assert strength == "neutral"


# =====================================================================
# Cases A - O: 15 Benchmark Verification Tests
# =====================================================================

def test_case_a_genuine_tcs(db_session, ml_model):
    """Case A: Genuine verified TCS. Acronym issue preserved until Step 4/5."""
    company_name = "Tata Consultancy Services"
    email = "careers@tcs.com"
    url = "https://www.tcs.com/careers"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Senior Systems Engineer",
        company_name=company_name,
        description="Responsibilities include microservices architecture. Qualifications: 3+ years Java. Selection process includes technical interview.",
        salary="₹8,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert score_res["risk_level"] == "LOW"
    assert score_res["trust_score"] >= 75


def test_case_b_genuine_infosys(db_session, ml_model):
    """Case B: Genuine verified Infosys with official contact and URL."""
    company_name = "Infosys"
    email = "careers@infosys.com"
    url = "https://www.infosys.com/careers"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Lead Java Developer",
        company_name=company_name,
        description="Key responsibilities include backend services. Qualifications: 5+ years Java and Spring Boot. Interview process involves coding test and HR round.",
        salary="₹15,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert comp_res["status"] == "VERIFIED"
    assert score_res["risk_level"] == "LOW"
    assert score_res["trust_score"] >= 90
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["company_verification"]["evidence_class"] == "POSITIVE_EVIDENCE"
    assert dims["contact_consistency"]["evidence_class"] == "POSITIVE_EVIDENCE"


def test_case_c_genuine_unknown_startup(db_session, ml_model):
    """Case C: Genuine unknown startup. Must not be classified as a scam."""
    company_name = "Lumina Quantum Systems"
    email = "talent@luminaquantum.tech"
    url = "https://www.luminaquantum.tech/jobs"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Full Stack Engineer",
        company_name=company_name,
        description="Responsibilities include React UI and FastAPI. Qualifications: 2+ years experience. Interview process includes screening call and virtual interview.",
        salary="₹12,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert comp_res["status"] == "UNVERIFIED"
    assert score_res["risk_level"] == "MEDIUM"
    assert 50 <= score_res["trust_score"] <= 65
    assert not any(f.get("severity") == "critical" for f in flags)


def test_case_d_tcs_using_gmail_no_double_counting(db_session, ml_model):
    """Case D: TCS using Gmail. Hard cap <= 25, no double-counting with free_email/email_domain_mismatch."""
    company_name = "Tata Consultancy Services"
    email = "recruiter@gmail.com"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=None)
    flags, positives, bonus = rules.analyze_rules(
        title="Associate Consultant",
        company_name=company_name,
        description="Responsibilities include client consulting. Qualifications: B.Tech. Interview process included.",
        salary="₹6,00,000 per annum",
        email=email,
        url=None,
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=None, positive_indicators=positives, email=email
    )
    assert comp_res["status"] == "IMPERSONATION_RISK"
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"
    flag_ids = [f["id"] for f in flags]
    assert "company_impersonation" in flag_ids
    # Assert double counting was prevented
    assert "free_email" not in flag_ids
    assert "email_domain_mismatch" not in flag_ids


def test_case_e_tcs_lookalike_domain(db_session, ml_model):
    """Case E: Known enterprise name with lookalike phishing domain."""
    company_name = "Tata Consultancy Services"
    email = "recruiter@tcs-hiring-portal.top"
    url = "http://tcs-careers-verify.top/apply"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Customer Support Executive",
        company_name=company_name,
        description="Responsibilities involve client support. Qualifications: Any graduate. Immediate document submission required.",
        salary="₹35,000 per month",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"


def test_case_f_registration_fee_scam(db_session, ml_model):
    """Case F: Explicit upfront registration fee. Must trigger critical cap <= 35."""
    company_name = "Quick Earn Data Solutions"
    flags, positives, bonus = rules.analyze_rules(
        title="Data Entry Clerk",
        company_name=company_name,
        description="Earn Rs 4000 per day. No experience needed. Note: Candidates must pay a mandatory registration fee of ₹1,499 via UPI before account activation.",
        salary="₹4,000 per day",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False)
    assert any(f["id"] == "fee_request" and f["evidence_class"] == "CRITICAL_EVIDENCE" for f in flags)
    assert score_res["trust_score"] <= 35
    assert score_res["risk_level"] == "HIGH"


def test_case_g_equipment_deposit_scam(db_session, ml_model):
    """Case G: Equipment purchase / deposit requirement."""
    flags, positives, bonus = rules.analyze_rules(
        title="Remote Administrative Assistant",
        company_name="Global Virtual Workspace",
        description="Candidates are required to pay for home office equipment and purchase a mandatory security deposit kit of ₹8,500 prior to laptop dispatch.",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False)
    assert any(f["id"] in ("equipment_purchase", "fee_request") and f["evidence_class"] == "CRITICAL_EVIDENCE" for f in flags)
    assert score_res["trust_score"] <= 35
    assert score_res["risk_level"] == "HIGH"


def test_case_h_whatsapp_only_recruitment(db_session, ml_model):
    """Case H: WhatsApp-only recruitment is NEGATIVE_EVIDENCE (warning), not critical scam cap."""
    flags, positives, bonus = rules.analyze_rules(
        title="Digital Marketing Associate",
        company_name="Apex Media Services",
        description=(
            "Duties include managing social media campaigns, preparing marketing collateral, and analyzing engagement metrics. "
            "Qualifications: Bachelor's degree in marketing or communications, knowledge of Canva and social platforms. "
            "To apply, contact on WhatsApp only at +91-9876543210. No phone calls or emails will be entertained. "
            "Message via WhatsApp to schedule your instant interview."
        ),
        salary="₹25,000 - ₹30,000 per month",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False, positive_indicators=positives)
    assert any(f["id"] == "suspicious_contact" and f["evidence_class"] == "NEGATIVE_EVIDENCE" for f in flags)
    assert not any(f.get("severity") == "critical" for f in flags)
    assert score_res["risk_level"] == "MEDIUM"
    assert 45 <= score_res["trust_score"] <= 65


def test_case_i_telegram_only_recruitment(db_session, ml_model):
    """Case I: Telegram-only recruitment is NEGATIVE_EVIDENCE, not critical scam."""
    flags, positives, bonus = rules.analyze_rules(
        title="Blockchain Research Analyst",
        company_name="Crypto Alpha Labs",
        description=(
            "Key responsibilities include monitoring decentralized protocol yields, preparing market summary notes, "
            "and researching tokenomics. Qualifications: Familiarity with crypto exchanges, basic financial acumen. "
            "All communication and project coordination is conducted via Telegram only. "
            "Interested applicants must message on Telegram @cryptoalpha_hr for onboarding tasks and interview details."
        ),
        salary="₹50,000 per month",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False, positive_indicators=positives)
    assert any(f["id"] == "suspicious_contact" and f["evidence_class"] == "NEGATIVE_EVIDENCE" for f in flags)
    assert not any(f["id"] == "money_transfer" for f in flags)
    assert score_res["risk_level"] == "MEDIUM"
    assert 45 <= score_res["trust_score"] <= 65


def test_case_j_unrealistic_salary(db_session, ml_model):
    """Case J: Unrealistic salary with urgent pressure cues."""
    flags, positives, bonus = rules.analyze_rules(
        title="Fresher Typist",
        company_name="Swift Careers",
        description="Guaranteed placement for freshers with no experience needed. Simple typing. Earn ₹5000 per day. Apply within 24 hours.",
        salary="₹5,000 per day",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False)
    assert any(f["id"] == "unrealistic_salary" for f in flags)
    assert score_res["trust_score"] <= 40
    assert score_res["risk_level"] == "HIGH"


def test_case_k_sensitive_info_request(db_session, ml_model):
    """Case K: Request for Aadhaar, PAN, bank statement and debit card details."""
    flags, positives, bonus = rules.analyze_rules(
        title="Verification Assistant",
        company_name="Verification Bureau",
        description="Applicants must email their original Aadhaar card, PAN card, bank account statement, and debit card details prior to interview.",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False)
    assert any(f["id"] == "sensitive_info" and f["evidence_class"] == "CRITICAL_EVIDENCE" for f in flags)
    assert score_res["trust_score"] <= 35
    assert score_res["risk_level"] == "HIGH"


def test_case_l_multiple_critical_signals(db_session, ml_model):
    """Case L: Job with fee request, Aadhaar/bank request, and guaranteed placement."""
    flags, positives, bonus = rules.analyze_rules(
        title="Data Assistant",
        company_name="Fast Track Employment",
        description="No interview needed, guaranteed placement. Must pay application fee of ₹2,500 via UPI. Submit your Aadhaar and bank details for payroll.",
    )
    score_res = scoring.compute_trust_score(flags, bonus, None, False)
    crit_flags = [f for f in flags if f.get("severity") == "critical"]
    assert len(crit_flags) >= 2
    assert score_res["trust_score"] <= 35
    assert score_res["risk_level"] == "HIGH"


def test_case_m_legitimate_incomplete_posting(db_session, ml_model):
    """Case M: Known enterprise without URL or email. Must receive MISSING_EVIDENCE and stay in Medium Risk."""
    company_name = "Wipro"
    comp_res = company_verifier.verify_company(db_session, company_name, email=None, website=None)
    flags, positives, bonus = rules.analyze_rules(
        title="Project Engineer",
        company_name=company_name,
        description="Wipro is hiring Project Engineers. Responsibilities include automated testing frameworks. Qualifications: B.E./B.Tech.",
        email=None,
        url=None,
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=None, positive_indicators=positives, email=None
    )
    assert comp_res["status"] == "PARTIALLY VERIFIED"
    assert score_res["risk_level"] == "MEDIUM"
    assert 55 <= score_res["trust_score"] <= 70
    breakdown = score_res["score_breakdown"]["evidence_breakdown"]
    missing_ids = [m["id"] for m in breakdown["missing_evidence"]]
    assert "missing_url" in missing_ids
    assert "missing_email" in missing_ids


def test_case_n_legitimate_job_with_whatsapp_auxiliary(db_session, ml_model):
    """Case N: Official enterprise posting with auxiliary WhatsApp contact remains Low Risk."""
    company_name = "Reliance Jio"
    email = "careers@jio.com"
    url = "https://careers.jio.com"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Senior Network Engineer",
        company_name=company_name,
        description="Reliance Jio Infocomm is hiring. Key responsibilities include radio network optimization. Qualifications: Degree in Telecom. Candidates may also reach out on WhatsApp at +91-9123456789.",
        salary="₹16,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert score_res["risk_level"] == "LOW"
    assert score_res["trust_score"] >= 80


def test_case_o_legitimate_payment_context_job(db_session, ml_model):
    """Case O: Legitimate fintech engineering posting must NOT trigger money_transfer scam flag."""
    company_name = "HCLTech"
    email = "careers@hcltech.com"
    url = "https://www.hcltech.com/careers"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Fintech Backend Engineer - Payment Systems",
        company_name=company_name,
        description=(
            "HCLTech is seeking a Senior Backend Engineer for our Banking practice. "
            "You will be responsible for integrating payment gateway protocols, building secure bank transfer APIs, "
            "processing automated gift cards redemption, and managing merchant settlement reconciliation workflows. "
            "Qualifications: Bachelor's degree in CS, 5+ years of experience with distributed payment systems. "
            "Selection process includes technical coding round and HR interview."
        ),
        salary="₹18,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert not any(f["id"] == "money_transfer" for f in flags)
    assert not any(f.get("severity") == "critical" for f in flags)
    assert score_res["risk_level"] == "LOW"
    assert score_res["trust_score"] >= 90


# =====================================================================
# Cases P - W: Edge Cases for Evidence Distinction & Hierarchy
# =====================================================================

def test_case_p_unknown_company_no_url():
    """Case P: Unknown company + no URL. Source credibility is MISSING_EVIDENCE, not suspicious."""
    score_res = scoring.compute_trust_score([], 0, None, False, url_result=None)
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["source_credibility"]["evidence_class"] == "MISSING_EVIDENCE"
    assert dims["source_credibility"]["score"] == 35.0


def test_case_q_unknown_company_no_email():
    """Case Q: Unknown company + no email. Contact consistency is MISSING_EVIDENCE, not suspicious."""
    score_res = scoring.compute_trust_score([], 0, None, False, email=None)
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["contact_consistency"]["evidence_class"] == "MISSING_EVIDENCE"
    assert dims["contact_consistency"]["score"] == 35.0


def test_case_r_known_company_no_url(db_session):
    """Case R: Known company + no URL. Source dimension is MISSING_EVIDENCE."""
    comp_res = company_verifier.verify_company(db_session, "Infosys", email="careers@infosys.com", website=None)
    score_res = scoring.compute_trust_score(
        [], 0, None, False,
        company_result=comp_res, url_result=None, email="careers@infosys.com"
    )
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["source_credibility"]["evidence_class"] == "MISSING_EVIDENCE"
    assert dims["source_credibility"]["score"] == 35.0


def test_case_s_known_company_no_email(db_session):
    """Case S: Known company + no email. Partially verified cap at 70 prevents unearned Low Risk."""
    comp_res = company_verifier.verify_company(db_session, "Infosys", email=None, website=None)
    score_res = scoring.compute_trust_score(
        [], 0, None, False,
        company_result=comp_res, url_result=None, email=None
    )
    assert comp_res["status"] == "PARTIALLY VERIFIED"
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["contact_consistency"]["evidence_class"] == "MISSING_EVIDENCE"
    assert dims["contact_consistency"]["score"] == 35.0
    assert score_res["trust_score"] <= 70


def test_case_t_known_company_official_email(db_session):
    """Case T: Known company + official email. Contact dimension is POSITIVE_EVIDENCE with score 95."""
    comp_res = company_verifier.verify_company(db_session, "Infosys", email="careers@infosys.com", website=None)
    flags, positives, bonus = rules.analyze_rules(
        title="Developer", company_name="Infosys", description="Job details", email="careers@infosys.com"
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, positive_indicators=positives, email="careers@infosys.com"
    )
    assert comp_res["status"] == "VERIFIED"
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["contact_consistency"]["evidence_class"] == "POSITIVE_EVIDENCE"
    assert dims["contact_consistency"]["score"] == 95.0


def test_case_u_known_company_mismatched_email(db_session):
    """Case U: Known company + mismatched email triggers IMPERSONATION_RISK and cap <= 25."""
    comp_res = company_verifier.verify_company(db_session, "Infosys", email="recruiter@fake-infosys-jobs.com", website=None)
    flags, positives, bonus = rules.analyze_rules(
        title="Developer", company_name="Infosys", description="Job details",
        email="recruiter@fake-infosys-jobs.com", company_status=comp_res.get("status")
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, email="recruiter@fake-infosys-jobs.com"
    )
    assert comp_res["status"] == "IMPERSONATION_RISK"
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"


def test_case_v_known_company_official_url():
    """Case V: Known company + official URL is POSITIVE_EVIDENCE with score 90."""
    url_res = url_analyzer.analyze_url("https://www.infosys.com/careers", "Infosys")
    score_res = scoring.compute_trust_score([], 0, None, False, url_result=url_res)
    dims = score_res["score_breakdown"]["dimensions"]
    assert dims["source_credibility"]["evidence_class"] == "POSITIVE_EVIDENCE"
    assert dims["source_credibility"]["score"] == 90.0


def test_case_w_known_company_lookalike_url():
    """Case W: Known company + lookalike URL flags suspicious_url with points 18."""
    url = "http://infosys-careers-jobs-2026.xyz/verify"
    url_res = url_analyzer.analyze_url(url, "Infosys")
    assert url_res.get("risk_level") == "HIGH"
    flags, positives, bonus = rules.analyze_rules(
        title="Developer", company_name="Infosys", description="Job details",
        url=url, url_risk_level=url_res.get("risk_level")
    )
    assert any(f["id"] == "suspicious_url" and f["points"] == 18 for f in flags)


def test_explanation_structure_evidence_categories(db_session):
    """Test that build_explanation renders the four distinct evidence categories in human-readable form."""
    comp_res = company_verifier.verify_company(db_session, "Unknown Corp", email=None, website=None)
    flags = [
        {"id": "fee_request", "label": "Upfront fee request", "severity": "critical", "evidence_class": "CRITICAL_EVIDENCE", "evidence": "pay 500"},
        {"id": "urgency", "label": "Urgency language", "severity": "medium", "evidence_class": "NEGATIVE_EVIDENCE", "evidence": "apply now"},
    ]
    positives = [
        {"id": "detailed_responsibilities", "label": "Detailed responsibilities listed", "evidence_class": "POSITIVE_EVIDENCE", "strength": "moderate"},
    ]
    score_res = scoring.compute_trust_score(
        flags, 0, None, False,
        company_result=comp_res, url_result=None, positive_indicators=positives, email=None
    )
    explanation = explain.build_explanation(
        trust_score=score_res["trust_score"],
        risk_level=score_res["risk_level"],
        red_flags=flags,
        positive_indicators=positives,
        company_result=comp_res,
        url_result=None,
        score_breakdown=score_res["score_breakdown"],
    )
    assert "Company Verification: UNVERIFIED" in explanation
    assert "Critical Scam Evidence:" in explanation
    assert "Risk Factors (Negative Evidence):" in explanation
    assert "Missing / Unverified Information:" in explanation
    assert "Positive Evidence of Legitimacy:" in explanation
    assert "Final Score:" in explanation
