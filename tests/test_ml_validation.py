"""Unit tests for ML model audit and validation (Step 6)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT / "ml") not in sys.path:
    sys.path.insert(0, str(ROOT / "ml"))

from app.services import ml_service, scoring
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.calibration import CalibratedClassifierCV


@pytest.fixture(autouse=True)
def ensure_ml_loaded():
    """Ensure ML model is loaded before tests and restore state after."""
    orig_pipe = ml_service._state.get("pipeline")
    orig_avail = ml_service._state.get("available")
    ml_service.load_model()
    yield
    ml_service._state["pipeline"] = orig_pipe
    ml_service._state["available"] = orig_avail


def test_model_loading_and_pipeline_integrity():
    """Test model loading and that pipeline contains tfidf and clf steps."""
    loaded = ml_service.load_model()
    assert loaded is True
    assert ml_service.is_available() is True
    pipe = ml_service._state["pipeline"]
    assert pipe is not None
    assert "tfidf" in pipe.named_steps
    assert "clf" in pipe.named_steps


def test_tfidf_vectorizer_configuration():
    """Test TF-IDF vectorizer configuration and hyperparameter settings."""
    pipe = ml_service._state["pipeline"]
    vec = pipe.named_steps["tfidf"]
    assert isinstance(vec, TfidfVectorizer)
    assert vec.ngram_range == (1, 2)
    assert vec.min_df == 2
    assert vec.sublinear_tf is True


def test_classifier_configuration():
    """Test classifier configuration and hyperparameter settings."""
    pipe = ml_service._state["pipeline"]
    clf = pipe.named_steps["clf"]
    if isinstance(clf, CalibratedClassifierCV):
        base = clf.estimator if hasattr(clf, "estimator") and clf.estimator is not None else clf.calibrated_classifiers_[0].estimator
    else:
        base = clf
    assert isinstance(base, LogisticRegression)
    assert base.class_weight == "balanced"
    assert base.penalty in ("l2", "deprecated", None)
    assert base.C == 1.0


def test_probability_output_bounds():
    """Test probability outputs are floats clamped strictly in [0.0, 1.0]."""
    res = ml_service.predict("Software Engineer at Infosys with Java experience")
    assert res["available"] is True
    p = res["scam_probability"]
    assert isinstance(p, float)
    assert 0.0 <= p <= 1.0


def test_known_legitimate_text_probability():
    """Test standard corporate legitimate text produces p_scam < 0.40."""
    legit_text = (
        "Infosys is hiring a Senior Software Engineer. Responsibilities include building "
        "scalable microservices with Python and cloud infrastructure. Qualifications: Bachelor "
        "degree in Computer Science, 5+ years experience. Competitive compensation package."
    )
    res = ml_service.predict(legit_text)
    assert res["available"] is True
    assert res["scam_probability"] is not None
    assert res["scam_probability"] < 0.40


def test_known_scam_text_probability():
    """Test overt scam text with registration fee produces p_scam > 0.60."""
    scam_text = (
        "Earn 5000 daily working from home! Data entry typing job. No skills needed. "
        "Guaranteed daily payout. Pay registration fee of Rs 1000 for activation software kit. "
        "Contact immediately on WhatsApp."
    )
    res = ml_service.predict(scam_text)
    assert res["available"] is True
    assert res["scam_probability"] is not None
    assert res["scam_probability"] > 0.60


def test_empty_input_handling():
    """Test empty string and whitespace input handling without crashing."""
    res_empty = ml_service.predict("")
    assert res_empty["available"] is True
    assert res_empty["scam_probability"] is not None
    assert 0.0 <= res_empty["scam_probability"] <= 1.0

    res_ws = ml_service.predict("   \n\t  ")
    assert res_ws["available"] is True
    assert res_ws["scam_probability"] is not None
    assert 0.0 <= res_ws["scam_probability"] <= 1.0


def test_very_long_input_handling():
    """Test very long input text (5000+ words) executes cleanly without crashing."""
    long_doc = "Responsibilities include enterprise architecture and distributed systems. " * 500
    res = ml_service.predict(long_doc)
    assert res["available"] is True
    assert res["scam_probability"] is not None
    assert 0.0 <= res["scam_probability"] <= 1.0


def test_special_characters_and_unicode():
    """Test input with emojis, currency symbols (₹, $, €), and non-ASCII text."""
    unicode_text = (
        "🚀 Hiring Remote Developer! Salary: ₹15,00,000 - ₹20,00,000 / year (or $30,000 USD). "
        "Apply via official career portal: https://company.com/jobs?id=4920&ref=linkedin! "
        "Tech stack: Python 3.12, Docker 🐳, Kubernetes ☸️."
    )
    res = ml_service.predict(unicode_text)
    assert res["available"] is True
    assert res["scam_probability"] is not None
    assert 0.0 <= res["scam_probability"] <= 1.0


def test_ml_output_never_overrides_critical_rule_flags():
    """Test that ML probability cannot override critical rule guardrails or hard caps."""
    # Even if ML scam probability is 0.0 (ML thinks text is 100% legitimate),
    # a critical red flag (fee_request) MUST cap trust score at <= 35.
    critical_flags = [
        {
            "id": "fee_request",
            "label": "Registration Fee Required",
            "points": 50,
            "severity": "critical",
            "evidence_class": "CRITICAL_EVIDENCE",
            "evidence": "Candidate asked to pay Rs 1000",
        }
    ]
    score_with_optimistic_ml = scoring.compute_trust_score(
        red_flags=critical_flags,
        positive_bonus=0,
        ml_scam_probability=0.0,  # Extreme false negative ML prediction
        ml_available=True,
        company_result={"status": "UNVERIFIED"},
    )
    assert score_with_optimistic_ml["trust_score"] <= 35
    assert score_with_optimistic_ml["risk_level"] == "HIGH"
    assert score_with_optimistic_ml["score_breakdown"]["cap_applied"] is True

    # Similarly, company impersonation risk MUST cap trust score at <= 25
    impersonation_flags = [
        {
            "id": "company_impersonation",
            "label": "Company Impersonation",
            "points": 45,
            "severity": "critical",
            "evidence_class": "CRITICAL_EVIDENCE",
            "evidence": "Claiming TCS from gmail.com",
        }
    ]
    score_with_impersonation = scoring.compute_trust_score(
        red_flags=impersonation_flags,
        positive_bonus=0,
        ml_scam_probability=0.0,
        ml_available=True,
        company_result={"status": "IMPERSONATION_RISK"},
    )
    assert score_with_impersonation["trust_score"] <= 25
    assert score_with_impersonation["risk_level"] == "HIGH"


def test_ml_service_graceful_degradation_when_unavailable():
    """Test graceful degradation when ML model is unavailable."""
    # Simulate model unavailability
    ml_service._state["available"] = False
    ml_service._state["pipeline"] = None

    assert ml_service.is_available() is False
    res = ml_service.predict("Senior Engineer role")
    assert res["available"] is False
    assert res["scam_probability"] is None
    assert res["top_terms"] == []

    # Scoring engine must continue working seamlessly with ml_available=False
    flags = [
        {
            "id": "vague_description",
            "label": "Vague Description",
            "points": 10,
            "severity": "low",
            "evidence_class": "NEGATIVE_EVIDENCE",
        }
    ]
    score_result = scoring.compute_trust_score(
        red_flags=flags,
        positive_bonus=10,
        ml_scam_probability=None,
        ml_available=False,
        company_result={"status": "VERIFIED"},
    )
    assert score_result["trust_score"] > 0
    scam_dim = score_result["score_breakdown"]["dimensions"]["scam_detection"]
    assert scam_dim["score"] == 90.0  # 100.0 - 10.0 purely from rules


def test_top_contributing_terms_extraction():
    """Test extraction of top contributing TF-IDF terms."""
    text = "Earn quick cash guaranteed registration fee WhatsApp"
    res = ml_service.predict(text)
    assert "top_terms" in res
    terms = res["top_terms"]
    assert isinstance(terms, list)
    assert len(terms) > 0
    for item in terms:
        assert "term" in item
        assert "weight" in item
        assert isinstance(item["term"], str)
        assert isinstance(item["weight"], float)


def test_hard_negative_fintech_payment_operations():
    """Test that legitimate fintech payment engineering posting receives low scam probability."""
    fintech_text = (
        "Razorpay is hiring a Backend Engineer for Payment Operations in Bengaluru. "
        "You will design high-throughput REST APIs for wire transfers, instant bank account "
        "verification, credit card gateway processing, and automated merchant settlements. "
        "Qualifications: Bachelor in CS, 4+ years Java/Python experience, PCI-DSS compliance. "
        "Salary: 25-35 LPA with health benefits. Apply at https://razorpay.com/careers."
    )
    res = ml_service.predict(fintech_text)
    assert res["available"] is True
    assert res["scam_probability"] < 0.20


def test_hard_negative_blockchain_crypto_protocol():
    """Test that legitimate blockchain protocol engineering posting receives low scam probability."""
    crypto_text = (
        "Polygon Labs is seeking a Protocol Developer. The role involves designing smart contracts, "
        "securing decentralized crypto wallet custody solutions, analyzing consensus mechanisms, "
        "and testing token disbursement smart contracts on testnet. Compensation: 30-50 LPA."
    )
    res = ml_service.predict(crypto_text)
    assert res["available"] is True
    assert res["scam_probability"] < 0.20


def test_hard_negative_telegram_developer_community():
    """Test that legitimate open source role mentioning Telegram community receives low scam probability."""
    comm_text = (
        "Developer Community Manager at Infosys. Manage global developer relations, "
        "organize webinars, and engage with open source developers across GitHub and our "
        "official Telegram developer group @InfosysDevs. Salary: 12-18 LPA. Apply at careers@infosys.com."
    )
    res = ml_service.predict(comm_text)
    assert res["available"] is True
    assert res["scam_probability"] < 0.20


def test_diluted_scam_with_fee_tail():
    """Test that fee extortion buried in a long legitimate-sounding enterprise JD is caught."""
    diluted_scam = (
        "Senior Software Engineer at Google. Responsibilities include building scalable distributed systems, "
        "microservices architecture, and cloud data pipelines. Qualifications: BS in Computer Science, "
        "5+ years experience. Selected candidates must pay a mandatory Rs 2,500 background screening processing "
        "fee to our accredited third-party verification partner prior to final interview."
    )
    res = ml_service.predict(diluted_scam)
    assert res["available"] is True
    assert res["scam_probability"] >= 0.50


def test_refundable_security_deposit_scam():
    """Test that refundable security deposit scam is detected."""
    deposit_scam = (
        "Work from home Administrative Assistant at Apex Solutions. We will send you a corporate laptop. "
        "Candidates must pay a 100% refundable security deposit of Rs 3,500 before courier dispatch. "
        "Deposit refunded with your first month salary. Contact on WhatsApp."
    )
    res = ml_service.predict(deposit_scam)
    assert res["available"] is True
    assert res["scam_probability"] >= 0.60
