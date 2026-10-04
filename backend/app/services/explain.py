"""Template-based and structured natural language explanations."""
from __future__ import annotations

from typing import Any

DISCLAIMER = (
    "AI JobShield gives evidence-based security guidance, not a definitive legal verdict. Always verify through official channels."
)


def build_explanation(
    *,
    trust_score: int,
    risk_level: str,
    red_flags: list[dict],
    positive_indicators: list[dict],
    company_result: dict[str, Any] | None = None,
    url_result: dict[str, Any] | None = None,
    score_breakdown: dict[str, Any] | None = None,
    top_terms: list[dict] | None = None,
    ml_available: bool = False,
) -> str:
    """Build a transparent, human-readable structured explanation detailing:
    - Company Verification status & reasons
    - Critical Scam Evidence (if any)
    - Risk Factors (Negative Evidence)
    - Missing / Unverified Information
    - Positive Evidence of Legitimacy
    - Overall Trust & Risk Level
    """
    company_data = company_result or {}
    company_status = company_data.get("status", "UNVERIFIED")
    company_reasons = company_data.get("reasons", [])

    ev_breakdown = (score_breakdown or {}).get("evidence_breakdown", {})
    crit_ev = ev_breakdown.get("critical_evidence", [])
    neg_ev = ev_breakdown.get("negative_evidence", [])
    miss_ev = ev_breakdown.get("missing_evidence", [])
    pos_ev = ev_breakdown.get("positive_evidence", [])

    # If evidence_breakdown was not provided (e.g. legacy/mock calls), categorize directly
    if not ev_breakdown:
        crit_ev = [f for f in red_flags if f.get("severity") == "critical" or f.get("evidence_class") == "CRITICAL_EVIDENCE"]
        neg_ev = [f for f in red_flags if f not in crit_ev]
        pos_ev = [p for p in positive_indicators if p.get("id") != "no_fee"]

    lines: list[str] = []

    # Section 1: Company Verification
    lines.append(f"Company Verification: {company_status}")
    if company_reasons:
        lines.append("Reasons:")
        for r in company_reasons:
            lines.append(f"• {r}")
    else:
        if company_status == "VERIFIED":
            lines.append("Reasons:\n• Validated against official verified enterprise database and consistent contact records.")
        elif company_status == "UNVERIFIED":
            lines.append("Reasons:\n• No reliable independent company record found in database.\n• Recruiter email or domain could not be independently authenticated.")
        else:
            lines.append(f"Reasons:\n• Status assessed as {company_status} based on available signals.")

    # Section 2: Critical Scam Evidence
    if crit_ev:
        lines.append("\nCritical Scam Evidence:")
        for f in crit_ev:
            ev = f.get("evidence", "")
            if ev and ev != f.get("label"):
                lines.append(f"• [CRITICAL] {f.get('label')} (Evidence: \"{ev}\")")
            else:
                lines.append(f"• [CRITICAL] {f.get('label')}")

    # Section 3: Risk Factors (Negative Evidence)
    if neg_ev:
        lines.append("\nRisk Factors (Negative Evidence):")
        for f in neg_ev:
            ev = f.get("evidence", "")
            if ev and ev != f.get("label"):
                lines.append(f"• {f.get('label')} (Evidence: \"{ev}\")")
            else:
                lines.append(f"• {f.get('label')}")
    elif not crit_ev:
        lines.append("\nRisk Factors (Negative Evidence):\n• None detected")

    # Section 4: Missing / Unverified Information
    if miss_ev:
        lines.append("\nMissing / Unverified Information:")
        for m in miss_ev:
            desc = m.get("description")
            if desc:
                lines.append(f"• {m.get('label')}: {desc}")
            else:
                lines.append(f"• {m.get('label')}")

    # Section 5: Positive Evidence of Legitimacy
    if pos_ev:
        lines.append("\nPositive Evidence of Legitimacy:")
        for p in pos_ev:
            strength_str = f" [{p.get('strength', 'moderate').capitalize()}]" if p.get("strength") else ""
            lines.append(f"• {p.get('label')}{strength_str}")
    else:
        lines.append("\nPositive Evidence of Legitimacy:\n• None confirmed")

    # Section 6: Final Score Assessment
    if risk_level == "HIGH":
        verdict_str = "High Risk / Likely Scam"
    elif risk_level == "MEDIUM":
        verdict_str = "Medium Risk / Caution Advised"
    else:
        verdict_str = "Low Risk / Verified"

    cap_reason = (score_breakdown or {}).get("cap_reason")
    lines.append(f"\nFinal Score: {trust_score}/100 ({verdict_str})")
    if cap_reason:
        lines.append(f"Safety Constraint: {cap_reason}")

    if ml_available and top_terms:
        terms_str = ", ".join(t.get("term", "") for t in top_terms[:4] if t.get("term"))
        if terms_str:
            lines.append(f"ML Scam Pattern Indicators: {terms_str}")

    lines.append(f"\n{DISCLAIMER}")
    return "\n".join(lines)
