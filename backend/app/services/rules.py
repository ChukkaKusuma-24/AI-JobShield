"""Rule-based red-flag and positive-indicator engine."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config import get_settings

# Tunable weights – single place for faculty demos
RULE_WEIGHTS: dict[str, dict[str, Any]] = {
    "fee_request": {"severity": "critical", "points": 35, "label": "Upfront fee / pay-to-join request"},
    "money_transfer": {"severity": "critical", "points": 35, "label": "Requests money, gift cards, or crypto"},
    "equipment_purchase": {"severity": "critical", "points": 35, "label": "Requests payment for equipment / laptop / software / tools"},
    "company_impersonation": {"severity": "critical", "points": 35, "label": "Company impersonation detected (claimed brand with mismatched/free contact)"},
    "sensitive_info": {"severity": "critical", "points": 30, "label": "Requests sensitive personal/financial information"},
    "unrealistic_salary": {"severity": "high", "points": 20, "label": "Unrealistic salary for role/experience"},
    "suspicious_contact": {"severity": "high", "points": 15, "label": "Suspicious contact method (WhatsApp/Telegram-only)"},
    "free_email": {"severity": "medium", "points": 12, "label": "Personal/free email used for claimed company"},
    "email_domain_mismatch": {"severity": "high", "points": 15, "label": "Email domain does not match company name"},
    "urgency": {"severity": "medium", "points": 10, "label": "Urgency / pressure language"},
    "no_interview": {"severity": "medium", "points": 12, "label": "No interview / guaranteed / instant selection"},
    "vague_description": {"severity": "medium", "points": 10, "label": "Vague job description"},
    "caps_exclaim": {"severity": "low", "points": 5, "label": "Excessive caps / exclamation / poor writing cues"},
    "suspicious_url": {"severity": "medium", "points": 12, "label": "URL shows suspicious characteristics"},
}

POSITIVE_MAX_BONUS = 25

EQUIPMENT_PATTERNS = [
    r"(?:buy|purchase|pay\s+for)\s+(?:a\s+)?(?:laptop|equipment|software|kit|device|hardware|tools|materials)",
    r"laptop\s+fee",
    r"equipment\s+(?:fee|deposit|cost|charge)",
    r"home\s+office\s+(?:kit|setup)\s+fee",
]
FEE_PATTERNS = [
    r"registration\s+fee",
    r"application\s+fee",
    r"training\s+fee",
    r"security\s+deposit",
    r"processing\s+fee",
    r"pay\s+to\s+(?:get|join|start)",
    r"fee\s+(?:to|for)\s+(?:join|register|apply)",
    r"joining\s+fee",
]
MONEY_PATTERNS = [
    r"gift\s*cards?",
    r"western\s+union",
    r"bank\s+transfer",
    r"\bcrypto\b",
    r"\bbitcoin\b",
    r"\bethereum\b",
    r"upi\s+(?:payment|transfer|id)",
    r"send\s+(?:money|payment|₹|rs)",
]
SENSITIVE_PATTERNS = [
    r"\baadhaar\b",
    r"\baadhar\b",
    r"\bssn\b",
    r"\bpan\s*(?:card)?\b",
    r"\bpassport\b",
    r"bank\s+(?:details|account|statement)",
    r"\botp\b",
    r"card\s+number",
    r"cvv",
    r"debit\s+card",
    r"credit\s+card",
]
URGENCY_PATTERNS = [
    r"within\s+24\s+hours",
    r"limited\s+seats?",
    r"\bimmediately\b",
    r"final\s+warning",
    r"hurry\s+up",
    r"last\s+chance",
    r"urgent(?:ly)?\s+hir",
    r"apply\s+now\s+or",
]
NO_INTERVIEW_PATTERNS = [
    r"no\s+interview",
    r"no\s+experience\s+(?:needed|required)",
    r"guaranteed\s+(?:job|selection|placement)",
    r"instant\s+selection",
    r"direct\s+joining",
]
WHATSAPP_PATTERNS = [
    r"whatsapp\s+only",
    r"telegram\s+only",
    r"contact\s+(?:on|via)\s+whatsapp",
    r"message\s+(?:on|via)\s+(?:whatsapp|telegram)",
    r"whatsapp\s*(?:me|hr|number)",
]

RESPONSIBILITY_CUES = [
    r"responsibilit",
    r"you will",
    r"duties",
    r"key\s+tasks",
    r"role\s+involves",
]
QUAL_CUES = [
    r"qualifications?",
    r"requirements?",
    r"must[- ]have",
    r"skills?\s+required",
    r"eligibility",
]
INTERVIEW_CUES = [
    r"interview",
    r"selection\s+process",
    r"assessment",
    r"technical\s+round",
    r"hr\s+round",
]


def _load_json_list(name: str) -> list:
    path = Path(get_settings().DATA_DIR) / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _find_first(patterns: list[str], text: str) -> str | None:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 40)
            return text[start:end].strip()
    return None


def _flag(rule_id: str, evidence: str, points_override: int | None = None) -> dict:
    meta = RULE_WEIGHTS[rule_id]
    return {
        "id": rule_id,
        "label": meta["label"],
        "severity": meta["severity"],
        "points": points_override if points_override is not None else meta["points"],
        "evidence": evidence[:200],
    }


def _company_tokens(name: str) -> set[str]:
    stop = {"pvt", "ltd", "limited", "inc", "llc", "the", "and", "of", "company", "co", "corp"}
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    return {t for t in tokens if t not in stop and len(t) > 2}


def analyze_rules(
    *,
    title: str,
    company_name: str,
    description: str,
    salary: str | None = None,
    email: str | None = None,
    url: str | None = None,
    job_type: str | None = None,
    url_risk_level: str | None = None,
    company_status: str | None = None,
) -> tuple[list[dict], list[dict], int]:
    """Return (red_flags, positive_indicators, positive_bonus_points)."""
    settings = get_settings()
    free_domains = {d.lower() for d in _load_json_list("free_email_domains.json")}
    text = f"{title}\n{company_name}\n{description}\n{salary or ''}\n{email or ''}\n{url or ''}"
    text_l = text.lower()
    flags: list[dict] = []
    positives: list[dict] = []
    bonus = 0

    ev = _find_first(FEE_PATTERNS, text)
    if ev:
        flags.append(_flag("fee_request", ev))

    ev = _find_first(EQUIPMENT_PATTERNS, text)
    if ev:
        flags.append(_flag("equipment_purchase", ev))

    ev = _find_first(MONEY_PATTERNS, text)
    if ev and not any(f["id"] == "fee_request" for f in flags):
        flags.append(_flag("money_transfer", ev))
    elif ev and any(f["id"] == "fee_request" for f in flags):
        # still add if distinct money channel language
        if re.search(r"gift\s*card|crypto|bitcoin|western\s+union", text_l):
            flags.append(_flag("money_transfer", ev))

    if company_status == "IMPERSONATION_RISK":
        flags.append(_flag("company_impersonation", f"Recruiter contact ({email or 'N/A'}) mismatches verified company profile"))

    ev = _find_first(SENSITIVE_PATTERNS, text)
    if ev:
        flags.append(_flag("sensitive_info", ev))

    # Unrealistic salary heuristics
    salary_blob = f"{salary or ''} {description}".lower()
    daily = re.search(r"(?:₹|rs\.?\s*|inr\s*)\s*([\d,]+)\s*(?:/|\s*per\s*)\s*day", salary_blob)
    monthly_high = re.search(
        r"(?:₹|rs\.?\s*|inr\s*)\s*([\d,]+)\s*(?:/|\s*per\s*)\s*month", salary_blob
    )
    earn_day = re.search(r"earn\s+(?:₹|rs\.?\s*)?\s*([\d,]+)\s*(?:/|\s*per\s*)?\s*day", salary_blob)
    entry = bool(
        re.search(r"intern|fresher|entry[- ]level|no\s+experience|student", text_l)
    )
    amount = None
    for m in (daily, earn_day):
        if m:
            amount = int(m.group(1).replace(",", ""))
            if amount >= settings.UNREALISTIC_DAILY_INR:
                flags.append(
                    _flag(
                        "unrealistic_salary",
                        m.group(0),
                    )
                )
                break
    if amount is None and monthly_high and entry:
        amt = int(monthly_high.group(1).replace(",", ""))
        if amt >= settings.UNREALISTIC_SALARY_INR:
            flags.append(_flag("unrealistic_salary", monthly_high.group(0)))

    ev = _find_first(WHATSAPP_PATTERNS, text)
    if ev:
        flags.append(_flag("suspicious_contact", ev))

    if email and "@" in email:
        domain = email.split("@")[-1].lower().strip()
        if domain in free_domains:
            flags.append(_flag("free_email", email))
        company_toks = _company_tokens(company_name)
        domain_toks = set(re.findall(r"[a-z0-9]+", domain.replace(".", " ")))
        if company_toks and not (company_toks & domain_toks) and domain not in free_domains:
            # domain doesn't share tokens with company
            flags.append(_flag("email_domain_mismatch", f"{email} vs {company_name}"))
        elif company_toks and domain in free_domains:
            flags.append(_flag("email_domain_mismatch", f"{email} vs {company_name}"))

    ev = _find_first(URGENCY_PATTERNS, text)
    if ev:
        flags.append(_flag("urgency", ev))

    ev = _find_first(NO_INTERVIEW_PATTERNS, text)
    if ev:
        flags.append(_flag("no_interview", ev))

    if len(description.strip()) < 80 or (
        not _find_first(RESPONSIBILITY_CUES, description)
        and not _find_first(QUAL_CUES, description)
    ):
        flags.append(
            _flag(
                "vague_description",
                description[:80] + ("…" if len(description) > 80 else ""),
            )
        )

    caps_ratio = sum(1 for c in description if c.isupper()) / max(len(description), 1)
    bangs = description.count("!")
    if caps_ratio > 0.35 or bangs >= 4:
        flags.append(
            _flag(
                "caps_exclaim",
                f"caps_ratio={caps_ratio:.2f}, exclamations={bangs}",
            )
        )

    if url_risk_level in ("MEDIUM", "HIGH"):
        pts = 18 if url_risk_level == "HIGH" else RULE_WEIGHTS["suspicious_url"]["points"]
        flags.append(_flag("suspicious_url", f"URL risk level: {url_risk_level}", pts))

    # Deduplicate by id (keep highest points)
    by_id: dict[str, dict] = {}
    for f in flags:
        if f["id"] not in by_id or f["points"] > by_id[f["id"]]["points"]:
            by_id[f["id"]] = f
    flags = list(by_id.values())

    # Positive indicators
    has_critical = any(f.get("severity") == "critical" for f in flags)

    if _find_first(RESPONSIBILITY_CUES, description):
        positives.append({"id": "detailed_responsibilities", "label": "Detailed responsibilities listed"})
        bonus += 5
    if _find_first(QUAL_CUES, description):
        positives.append({"id": "qualifications", "label": "Qualifications / skills listed"})
        bonus += 5
    if email and "@" in email:
        domain = email.split("@")[-1].lower()
        if domain not in free_domains and (_company_tokens(company_name) & set(
            re.findall(r"[a-z0-9]+", domain.replace(".", " "))
        )):
            positives.append({"id": "official_email", "label": "Official-looking company-domain email"})
            bonus += 6
    if url and url.lower().startswith("https://"):
        positives.append({"id": "https_url", "label": "HTTPS URL provided"})
        bonus += 3
    if _find_first(INTERVIEW_CUES, description):
        positives.append({"id": "interview_process", "label": "Interview / selection process mentioned"})
        bonus += 5
    if salary and re.search(r"\d", salary) and not any(f["id"] == "unrealistic_salary" for f in flags):
        positives.append({"id": "realistic_salary", "label": "Salary information looks plausible"})
        bonus += 3
    if company_status in ("VERIFIED", "PARTIALLY VERIFIED"):
        positives.append({"id": "company_verified", "label": f"Company status: {company_status}"})
        bonus += 5 if company_status == "VERIFIED" else 2
    if not any(f["id"] in ("fee_request", "money_transfer", "equipment_purchase") for f in flags):
        positives.append({"id": "no_fee", "label": "No upfront fee request detected"})
        bonus += 4

    # Critical scam indicators must never be cancelled out by positive signals
    if has_critical:
        bonus = 0
    else:
        bonus = min(bonus, POSITIVE_MAX_BONUS)

    return flags, positives, bonus
