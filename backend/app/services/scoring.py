"""Evidence-based multi-dimensional trust score computation."""
from __future__ import annotations

from typing import Any

from app.config import get_settings


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_trust_score(
    red_flags: list[dict],
    positive_bonus: int,
    ml_scam_probability: float | None,
    ml_available: bool,
    *,
    company_result: dict[str, Any] | None = None,
    url_result: dict[str, Any] | None = None,
    positive_indicators: list[dict] | None = None,
    source: str = "manual",
) -> dict[str, Any]:
    """Compute transparent weighted credibility score across 5 dimensions:
    1. Company Verification (25%)
    2. Job / Source Credibility (20%)
    3. Job Posting Quality (15%)
    4. Scam / Red Flag Detection (30%)
    5. Contact / Domain Consistency (10%)
    """
    settings = get_settings()
    positives = positive_indicators or []

    # -------------------------------------------------------------
    # Dimension 1: Company Verification (25%)
    # -------------------------------------------------------------
    company_data = company_result or {}
    company_status = company_data.get("status", "UNVERIFIED")
    if "company_score" in company_data and company_data["company_score"] is not None:
        company_dim_score = float(company_data["company_score"])
    else:
        if company_status == "VERIFIED":
            company_dim_score = 95.0
        elif company_status == "PARTIALLY VERIFIED":
            company_dim_score = 65.0
        elif company_status == "IMPERSONATION_RISK":
            company_dim_score = 10.0
        else:
            company_dim_score = 40.0
    company_dim_score = clamp(company_dim_score, 0.0, 100.0)

    # -------------------------------------------------------------
    # Dimension 2: Source / URL Credibility (20%)
    # -------------------------------------------------------------
    url_data = url_result or {}
    has_url = bool(url_data.get("url"))
    if has_url:
        if not url_data.get("valid", True):
            source_dim_score = 15.0
        else:
            url_risk = url_data.get("risk_level", "MEDIUM")
            url_risk_score = url_data.get("risk_score", 0)
            if url_risk == "LOW":
                # Check if mismatch flag exists
                indicators = url_data.get("indicators", [])
                if any(i.get("id") == "company_mismatch" for i in indicators):
                    source_dim_score = 60.0
                else:
                    source_dim_score = 90.0
            elif url_risk == "MEDIUM":
                source_dim_score = 45.0
            else:
                source_dim_score = max(5.0, 100.0 - float(url_risk_score))
    else:
        # No URL provided: neutral unverified source (neither positive nor malicious)
        source_dim_score = 50.0
    source_dim_score = clamp(source_dim_score, 0.0, 100.0)

    # -------------------------------------------------------------
    # Dimension 3: Job Description Quality (15%)
    # -------------------------------------------------------------
    quality_dim_score = 60.0
    if any(p.get("id") == "detailed_responsibilities" for p in positives):
        quality_dim_score += 15.0
    if any(p.get("id") == "qualifications" for p in positives):
        quality_dim_score += 15.0
    if any(p.get("id") == "interview_process" for p in positives):
        quality_dim_score += 10.0
    if any(p.get("id") == "realistic_salary" for p in positives):
        quality_dim_score += 10.0

    if any(f.get("id") == "vague_description" for f in red_flags):
        quality_dim_score -= 35.0
    if any(f.get("id") == "caps_exclaim" for f in red_flags):
        quality_dim_score -= 15.0
    quality_dim_score = clamp(quality_dim_score, 15.0, 95.0)

    # -------------------------------------------------------------
    # Dimension 4: Scam / Red Flag Detection (30%)
    # -------------------------------------------------------------
    raw_points = sum(f.get("points", 0) for f in red_flags)
    rule_scam_score = clamp(100.0 - raw_points, 0.0, 100.0)

    used_ml = False
    if ml_available and ml_scam_probability is not None:
        ml_risk = ml_scam_probability * 100.0
        ml_scam_score = clamp(100.0 - ml_risk, 0.0, 100.0)
        # 70% rule-based / 30% ML blend
        scam_dim_score = 0.70 * rule_scam_score + 0.30 * ml_scam_score
        used_ml = True
    else:
        scam_dim_score = rule_scam_score
        ml_risk = None
    scam_dim_score = clamp(scam_dim_score, 0.0, 100.0)

    # -------------------------------------------------------------
    # Dimension 5: Contact / Domain Consistency (10%)
    # -------------------------------------------------------------
    if company_status == "IMPERSONATION_RISK" or any(f.get("id") == "company_impersonation" for f in red_flags):
        contact_dim_score = 10.0
    elif any(f.get("id") == "email_domain_mismatch" for f in red_flags):
        contact_dim_score = 20.0
    elif any(f.get("id") == "free_email" for f in red_flags):
        contact_dim_score = 30.0
    elif any(f.get("id") == "suspicious_contact" for f in red_flags):
        contact_dim_score = 20.0
    elif any(p.get("id") == "official_email" for p in positives):
        contact_dim_score = 95.0
    else:
        # Neutral if contact info not explicitly verified
        contact_dim_score = 50.0
    contact_dim_score = clamp(contact_dim_score, 0.0, 100.0)

    # -------------------------------------------------------------
    # Weighted Score Aggregation
    # -------------------------------------------------------------
    w_company = 0.25
    w_source = 0.20
    w_quality = 0.15
    w_scam = 0.30
    w_contact = 0.10

    raw_weighted = (
        w_company * company_dim_score
        + w_source * source_dim_score
        + w_quality * quality_dim_score
        + w_scam * scam_dim_score
        + w_contact * contact_dim_score
    )

    trust_score = int(round(raw_weighted))

    # -------------------------------------------------------------
    # Evidence-Based Guardrails & Hard Caps
    # -------------------------------------------------------------
    has_critical_scam = any(
        f.get("severity") == "critical"
        or f.get("id") in ("fee_request", "money_transfer", "equipment_purchase", "sensitive_info")
        for f in red_flags
    )
    has_impersonation = (
        company_status == "IMPERSONATION_RISK"
        or any(f.get("id") == "company_impersonation" for f in red_flags)
    )
    is_unverified_company = company_status == "UNVERIFIED" or company_status is None
    is_partially_verified = company_status == "PARTIALLY VERIFIED"

    cap_applied = False
    cap_reason = None

    if has_impersonation:
        trust_score = min(trust_score, 25)
        cap_applied = True
        cap_reason = "Impersonation risk detected: company claimed name does not match recruiter contact."
    elif has_critical_scam:
        trust_score = min(trust_score, 35)
        cap_applied = True
        cap_reason = "Critical scam indicator present (upfront fee, money request, or sensitive data solicitation)."
    elif is_unverified_company:
        if trust_score > 65:
            trust_score = 65
            cap_applied = True
            cap_reason = "Company is unverified; lack of verifiable evidence caps maximum credibility score."
    elif is_partially_verified:
        if trust_score > 75:
            trust_score = 75
            cap_applied = True
            cap_reason = "Company is partially verified; moderate trust cap applied."

    trust_score = int(clamp(trust_score, 0, 100))

    # Risk level classification
    if trust_score >= 75:
        risk_level = "LOW"
    elif trust_score >= 45:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    breakdown = {
        "dimensions": {
            "company_verification": {
                "score": round(company_dim_score, 1),
                "weight": w_company,
                "status": company_status,
                "label": "Company Verification",
            },
            "source_credibility": {
                "score": round(source_dim_score, 1),
                "weight": w_source,
                "label": "Source & URL Credibility",
            },
            "job_posting_quality": {
                "score": round(quality_dim_score, 1),
                "weight": w_quality,
                "label": "Job Posting Quality",
            },
            "scam_detection": {
                "score": round(scam_dim_score, 1),
                "weight": w_scam,
                "label": "Scam & Red Flag Detection",
            },
            "contact_consistency": {
                "score": round(contact_dim_score, 1),
                "weight": w_contact,
                "label": "Contact & Domain Consistency",
            },
        },
        "raw_weighted_score": round(raw_weighted, 1),
        "red_flag_points": [
            {"id": f["id"], "label": f["label"], "points": f["points"], "severity": f["severity"]}
            for f in red_flags
        ],
        "raw_rule_points": raw_points,
        "positive_bonus": positive_bonus,
        "ml_available": used_ml,
        "ml_scam_probability": ml_scam_probability,
        "ml_risk": round(ml_risk, 2) if ml_risk is not None else None,
        "cap_applied": cap_applied,
        "cap_reason": cap_reason,
        "trust_score": trust_score,
        "risk_level": risk_level,
        "formula": "25% Company + 20% Source + 15% Quality + 30% Scam Detection + 10% Contact Consistency; bounded by evidence-based caps",
    }

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "rule_risk_points": raw_points,
        "score_breakdown": breakdown,
    }
