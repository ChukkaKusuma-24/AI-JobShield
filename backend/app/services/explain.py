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
    - Risk Factors (Red flags)
    - Positive Factors
    - Overall Trust & Risk Level
    """
    company_data = company_result or {}
    company_status = company_data.get("status", "UNVERIFIED")
    company_reasons = company_data.get("reasons", [])

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

    # Section 2: Risk Factors
    if red_flags:
        lines.append("\nRisk Factors:")
        for f in red_flags:
            ev = f.get("evidence", "")
            if ev and ev != f.get("label"):
                lines.append(f"• {f.get('label')} (Evidence: \"{ev}\")")
            else:
                lines.append(f"• {f.get('label')}")
    else:
        lines.append("\nRisk Factors:\n• None detected")

    # Section 3: Positive Factors
    if positive_indicators:
        lines.append("\nPositive Factors:")
        for p in positive_indicators:
            lines.append(f"• {p.get('label')}")
    else:
        lines.append("\nPositive Factors:\n• None recorded")

    # Section 4: Final Score Assessment
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
