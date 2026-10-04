"""Formal Evidence Hierarchy for AI JobShield.

Defines the four core evidence classes:
1. POSITIVE_EVIDENCE: Direct, verifiable proof of legitimacy or safe practice.
2. MISSING_EVIDENCE: Unprovided or unverified data that cannot be independently confirmed.
3. NEGATIVE_EVIDENCE: Non-critical warning indicators of suspicious, high-pressure, or deceptive patterns.
4. CRITICAL_EVIDENCE: Severe disqualifying scam indicators requiring immediate hard score caps.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class EvidenceClass(str, Enum):
    POSITIVE = "POSITIVE_EVIDENCE"
    MISSING = "MISSING_EVIDENCE"
    NEGATIVE = "NEGATIVE_EVIDENCE"
    CRITICAL = "CRITICAL_EVIDENCE"


def classify_rule_signal(rule_id: str, severity: str) -> EvidenceClass:
    """Classify a detected rule flag into the formal evidence hierarchy."""
    if severity == "critical" or rule_id in (
        "fee_request",
        "money_transfer",
        "equipment_purchase",
        "company_impersonation",
        "sensitive_info",
    ):
        return EvidenceClass.CRITICAL
    return EvidenceClass.NEGATIVE


def classify_positive_signal(signal_id: str) -> tuple[EvidenceClass, str]:
    """Classify a positive indicator and return (evidence_class, strength).
    
    Absence of negative patterns (e.g. no_fee) is classified as MISSING_EVIDENCE /
    neutral absence of harm, NOT positive proof of legitimacy.
    """
    if signal_id == "no_fee":
        return EvidenceClass.MISSING, "neutral"
    if signal_id in ("official_email", "company_verified"):
        return EvidenceClass.POSITIVE, "strong"
    if signal_id in ("detailed_responsibilities", "qualifications", "interview_process"):
        return EvidenceClass.POSITIVE, "moderate"
    return EvidenceClass.POSITIVE, "weak"
