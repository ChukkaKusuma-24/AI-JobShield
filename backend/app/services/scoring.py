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
    email: str | None = None,
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
    raw_score = company_data.get("company_score")
    if raw_score is None:
        raw_score = company_data.get("score")
    if raw_score is not None:
        company_dim_score = float(raw_score)
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

    if company_status == "VERIFIED":
        company_ev_class = "POSITIVE_EVIDENCE"
    elif company_status == "IMPERSONATION_RISK":
        company_ev_class = "CRITICAL_EVIDENCE"
    elif company_status == "PARTIALLY VERIFIED":
        company_ev_class = "MISSING_EVIDENCE"
    else:
        company_ev_class = "MISSING_EVIDENCE"

    # -------------------------------------------------------------
    # Dimension 2: Source / URL Credibility (20%)
    # -------------------------------------------------------------
    url_data = url_result or {}
    has_url = bool(url_data.get("url"))
    if has_url:
        if not url_data.get("valid", True):
            source_dim_score = 15.0
            source_ev_class = "CRITICAL_EVIDENCE" if url_data.get("risk_level") == "HIGH" else "NEGATIVE_EVIDENCE"
        else:
            url_risk = url_data.get("risk_level", "MEDIUM")
            url_risk_score = url_data.get("risk_score", 0)
            if url_risk == "LOW":
                # Check if mismatch flag exists
                indicators = url_data.get("indicators", [])
                if any(i.get("id") == "company_mismatch" for i in indicators):
                    source_dim_score = 60.0
                    source_ev_class = "NEGATIVE_EVIDENCE"
                else:
                    source_dim_score = 90.0
                    source_ev_class = "POSITIVE_EVIDENCE"
            elif url_risk == "MEDIUM":
                source_dim_score = 45.0
                source_ev_class = "NEGATIVE_EVIDENCE"
            else:
                source_dim_score = max(5.0, 100.0 - float(url_risk_score))
                source_ev_class = "CRITICAL_EVIDENCE" if url_risk == "HIGH" else "NEGATIVE_EVIDENCE"
    else:
        # No URL provided: missing evidence (unverified source channel, NOT suspicious, NOT positive)
        source_dim_score = 35.0
        source_ev_class = "MISSING_EVIDENCE"
    source_dim_score = clamp(source_dim_score, 0.0, 100.0)

    # -------------------------------------------------------------
    # Dimension 3: Job Description Quality (15%)
    # -------------------------------------------------------------
    # Baseline for neutral unverified job description starts at 40.0 (MISSING evidence of quality)
    quality_dim_score = 40.0
    if any(p.get("id") == "detailed_responsibilities" for p in positives):
        quality_dim_score += 15.0
    if any(p.get("id") == "qualifications" for p in positives):
        quality_dim_score += 15.0
    if any(p.get("id") == "interview_process" for p in positives):
        quality_dim_score += 10.0
    if any(p.get("id") == "realistic_salary" for p in positives):
        quality_dim_score += 10.0

    if any(f.get("id") == "vague_description" for f in red_flags):
        quality_dim_score -= 25.0
    if any(f.get("id") == "caps_exclaim" for f in red_flags):
        quality_dim_score -= 15.0
    quality_dim_score = clamp(quality_dim_score, 15.0, 95.0)

    quality_ev_class = "POSITIVE_EVIDENCE" if quality_dim_score >= 70.0 else "MISSING_EVIDENCE" if quality_dim_score >= 35.0 else "NEGATIVE_EVIDENCE"

    # -------------------------------------------------------------
    # Dimension 4: Scam / Red Flag Detection (30%)
    # -------------------------------------------------------------
    raw_points = sum(f.get("points", 0) for f in red_flags)

    # Distinguish POSITIVE_EVIDENCE_OF_LEGITIMACY from NO_NEGATIVE_EVIDENCE_DETECTED
    has_impersonation_flag = (
        company_status == "IMPERSONATION_RISK"
        or any(f.get("id") == "company_impersonation" for f in red_flags)
        or any(i.get("id") == "lookalike_domain" for i in url_data.get("indicators", []))
    )
    has_positive_legitimacy = (
        not has_impersonation_flag
        and (
            company_status == "VERIFIED"
            or any(p.get("id") == "official_email" for p in positives)
            or (
                has_url
                and url_data.get("risk_level") == "LOW"
                and not any(i.get("id") in ("company_mismatch", "lookalike_domain") for i in url_data.get("indicators", []))
                and company_status in ("VERIFIED", "PARTIALLY VERIFIED")
            )
        )
    )

    if has_positive_legitimacy:
        scam_base = 100.0
        scam_ev_state = "POSITIVE_EVIDENCE_OF_LEGITIMACY"
    else:
        # Absence of crude scam keywords is NOT proof of legitimacy; base at 80.0
        scam_base = 80.0
        scam_ev_state = "NO_NEGATIVE_EVIDENCE_DETECTED"

    rule_scam_score = clamp(scam_base - raw_points, 0.0, 100.0)

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
    has_contact = bool(
        (email and email.strip())
        or any(c.get("name") == "official_email_domain" for c in company_data.get("checks", []))
        or any(f.get("id") in ("free_email", "email_domain_mismatch", "suspicious_contact") for f in red_flags)
        or any(p.get("id") == "official_email" for p in positives)
    )

    if company_status == "IMPERSONATION_RISK" or any(f.get("id") == "company_impersonation" for f in red_flags):
        contact_dim_score = 10.0
        contact_ev_class = "CRITICAL_EVIDENCE"
    elif any(f.get("id") == "email_domain_mismatch" for f in red_flags):
        contact_dim_score = 20.0
        contact_ev_class = "NEGATIVE_EVIDENCE"
    elif any(f.get("id") == "free_email" for f in red_flags):
        contact_dim_score = 30.0
        contact_ev_class = "NEGATIVE_EVIDENCE"
    elif any(f.get("id") == "suspicious_contact" for f in red_flags):
        contact_dim_score = 20.0
        contact_ev_class = "NEGATIVE_EVIDENCE"
    elif any(p.get("id") == "official_email" for p in positives):
        contact_dim_score = 95.0
        contact_ev_class = "POSITIVE_EVIDENCE"
    elif has_contact:
        contact_dim_score = 65.0
        contact_ev_class = "POSITIVE_EVIDENCE"
    else:
        # No email / contact provided: missing evidence (unverified contact, NOT suspicious)
        contact_dim_score = 35.0
        contact_ev_class = "MISSING_EVIDENCE"
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
        or f.get("evidence_class") == "CRITICAL_EVIDENCE"
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
        if trust_score > 70:
            trust_score = 70
            cap_applied = True
            cap_reason = "Company is partially verified; unconfirmed contact channels cap score to Medium Risk."

    trust_score = int(clamp(trust_score, 0, 100))

    # Risk level classification
    if trust_score >= 75:
        risk_level = "LOW"
    elif trust_score >= 45:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # Build structured evidence breakdown
    pos_ev_list = []
    for p in positives:
        if p.get("evidence_class") == "POSITIVE_EVIDENCE" or p.get("id") != "no_fee":
            pos_ev_list.append({
                "id": p.get("id"),
                "label": p.get("label"),
                "strength": p.get("strength", "moderate"),
                "evidence_class": "POSITIVE_EVIDENCE",
            })

    miss_ev_list = []
    if not has_url:
        miss_ev_list.append({
            "id": "missing_url",
            "label": "No job posting URL provided",
            "dimension": "source_credibility",
            "description": "Source authenticity could not be independently verified.",
            "evidence_class": "MISSING_EVIDENCE",
        })
    if not has_contact:
        miss_ev_list.append({
            "id": "missing_email",
            "label": "No recruiter email provided",
            "dimension": "contact_consistency",
            "description": "Recruiter contact authenticity could not be independently verified.",
            "evidence_class": "MISSING_EVIDENCE",
        })
    if is_unverified_company:
        miss_ev_list.append({
            "id": "unverified_company",
            "label": "Company not in verified enterprise registry",
            "dimension": "company_verification",
            "description": "Company identity requires independent verification.",
            "evidence_class": "MISSING_EVIDENCE",
        })
    if any(p.get("id") == "no_fee" for p in positives):
        miss_ev_list.append({
            "id": "no_fee",
            "label": "No upfront fee request detected",
            "dimension": "scam_detection",
            "description": "Absence of fee request noted; does not constitute affirmative proof of legitimacy.",
            "evidence_class": "MISSING_EVIDENCE",
        })

    neg_ev_list = []
    crit_ev_list = []
    for f in red_flags:
        item = {
            "id": f.get("id"),
            "label": f.get("label"),
            "points": f.get("points"),
            "severity": f.get("severity"),
            "evidence": f.get("evidence", ""),
            "evidence_class": f.get("evidence_class", "NEGATIVE_EVIDENCE"),
        }
        if f.get("severity") == "critical" or f.get("evidence_class") == "CRITICAL_EVIDENCE":
            crit_ev_list.append(item)
        else:
            neg_ev_list.append(item)

    evidence_breakdown = {
        "positive_evidence": pos_ev_list,
        "missing_evidence": miss_ev_list,
        "negative_evidence": neg_ev_list,
        "critical_evidence": crit_ev_list,
        "scam_evidence_state": scam_ev_state,
    }

    breakdown = {
        "dimensions": {
            "company_verification": {
                "score": round(company_dim_score, 1),
                "weight": w_company,
                "status": company_status,
                "evidence_class": company_ev_class,
                "label": "Company Verification",
            },
            "source_credibility": {
                "score": round(source_dim_score, 1),
                "weight": w_source,
                "evidence_class": source_ev_class,
                "label": "Source & URL Credibility",
            },
            "job_posting_quality": {
                "score": round(quality_dim_score, 1),
                "weight": w_quality,
                "evidence_class": quality_ev_class,
                "label": "Job Posting Quality",
            },
            "scam_detection": {
                "score": round(scam_dim_score, 1),
                "weight": w_scam,
                "evidence_class": scam_ev_state,
                "label": "Scam & Red Flag Detection",
            },
            "contact_consistency": {
                "score": round(contact_dim_score, 1),
                "weight": w_contact,
                "evidence_class": contact_ev_class,
                "label": "Contact & Domain Consistency",
            },
        },
        "raw_weighted_score": round(raw_weighted, 1),
        "red_flag_points": [
            {
                "id": f.get("id", ""),
                "label": f.get("label", ""),
                "points": f.get("points", 0),
                "severity": f.get("severity", "medium"),
                "evidence_class": f.get("evidence_class", "NEGATIVE_EVIDENCE"),
            }
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
        "evidence_breakdown": evidence_breakdown,
    }

    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "rule_risk_points": raw_points,
        "score_breakdown": breakdown,
    }
