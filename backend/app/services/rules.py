"""Rule-based red-flag and positive-indicator engine."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.evidence import classify_positive_signal, classify_rule_signal

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
    r"(?:buy|purchase|pay\s+for)\s+(?:a\s+)?(?:home\s+office\s+)?(?:laptop|equipment|software|kit|device|hardware|tools|materials)",
    r"laptop\s+fee",
    r"equipment\s+(?:fee|deposit|cost|charge)",
    r"home\s+office\s+(?:kit|setup)\s+(?:fee|deposit|cost|charge)",
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
    r"(?:pay|send|transfer|deposit|purchase|buy|invest|redeem\s+for\s+cash)\s+(?:via|with|through|using|in)?\s*(?:a\s+)?(?:gift\s*cards?|western\s+union|crypto|bitcoin|ethereum|upi)",
    r"(?:gift\s*cards?|western\s+union|crypto|bitcoin|ethereum|upi)\s+(?:payment|transfer|deposit|investment)",
    r"(?:pay|send|transfer)\s+(?:money|funds|cash|payment|deposit|₹|rs)",
    r"transfer\s+(?:funds|amount|₹|rs)\s+(?:to|via|into)",
    r"western\s+union",
    r"upi\s+(?:payment|transfer|id)",
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
    ev_class = classify_rule_signal(rule_id, meta["severity"]).value
    return {
        "id": rule_id,
        "label": meta["label"],
        "severity": meta["severity"],
        "evidence_class": ev_class,
        "points": points_override if points_override is not None else meta["points"],
        "evidence": evidence[:200],
    }


def _positive(signal_id: str, label: str) -> dict:
    ev_class, strength = classify_positive_signal(signal_id)
    return {
        "id": signal_id,
        "label": label,
        "evidence_class": ev_class.value,
        "strength": strength,
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

    from app.services.company_verifier import resolve_company_identity
    identity = resolve_company_identity(company_name)

    has_impersonation = (
        company_status == "IMPERSONATION_RISK"
        or any(f["id"] == "company_impersonation" for f in flags)
    )
    if email and "@" in email:
        domain = email.split("@")[-1].lower().strip()
        is_free = domain in free_domains
        is_official = (
            identity.is_known_entity
            and bool(identity.official_domains)
            and any(domain == od or domain.endswith("." + od) for od in identity.official_domains)
        )

        if not has_impersonation:
            if is_official:
                pass  # Official verified enterprise email domain
            elif is_free:
                if identity.is_known_entity:
                    flags.append(
                        _flag(
                            "company_impersonation",
                            f"Recruiter using personal email ({email}) for verified enterprise {identity.canonical_name}",
                        )
                    )
                else:
                    flags.append(_flag("free_email", email))
            else:
                # Custom domain
                if identity.is_known_entity:
                    flags.append(_flag("email_domain_mismatch", f"{email} vs {identity.canonical_name}"))
                else:
                    company_toks = identity.tokens or _company_tokens(company_name)
                    domain_toks = set(re.findall(r"[a-z0-9]+", domain.replace(".", " ")))
                    domain_root = domain.split(".")[0]
                    has_match = (
                        bool(company_toks & domain_toks)
                        or any(t in domain_root for t in company_toks if len(t) >= 3)
                    )
                    if company_toks and not has_match:
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

    if url_risk_level == "HIGH":
        flags.append(_flag("suspicious_url", f"URL risk level: {url_risk_level}", 18))

    # Deduplicate by id (keep highest points)
    by_id: dict[str, dict] = {}
    for f in flags:
        if f["id"] not in by_id or f["points"] > by_id[f["id"]]["points"]:
            by_id[f["id"]] = f
    flags = list(by_id.values())

    # Positive indicators
    has_critical = any(f.get("severity") == "critical" for f in flags)

    if _find_first(RESPONSIBILITY_CUES, description):
        positives.append(_positive("detailed_responsibilities", "Detailed responsibilities listed"))
        bonus += 5
    if _find_first(QUAL_CUES, description):
        positives.append(_positive("qualifications", "Qualifications / skills listed"))
        bonus += 5
    if email and "@" in email and not has_impersonation:
        domain = email.split("@")[-1].lower().strip()
        is_free = domain in free_domains
        is_official = (
            identity.is_known_entity
            and bool(identity.official_domains)
            and any(domain == od or domain.endswith("." + od) for od in identity.official_domains)
        )
        if is_official:
            positives.append(_positive("official_email", f"Official company email verified (@{domain})"))
            bonus += 6
        elif not is_free:
            company_toks = identity.tokens or _company_tokens(company_name)
            domain_toks = set(re.findall(r"[a-z0-9]+", domain.replace(".", " ")))
            domain_root = domain.split(".")[0]
            has_match = (
                bool(company_toks & domain_toks)
                or any(t in domain_root for t in company_toks if len(t) >= 3)
            )
            if has_match:
                positives.append(_positive("official_email", f"Company-matching domain email (@{domain})"))
                bonus += 4
    if url and url.lower().startswith("https://"):
        positives.append(_positive("https_url", "HTTPS URL provided"))
        bonus += 3
    if _find_first(INTERVIEW_CUES, description):
        positives.append(_positive("interview_process", "Interview / selection process mentioned"))
        bonus += 5
    if salary and re.search(r"\d", salary) and not any(f["id"] == "unrealistic_salary" for f in flags):
        positives.append(_positive("realistic_salary", "Salary information looks plausible"))
        bonus += 3
    if company_status in ("VERIFIED", "PARTIALLY VERIFIED"):
        positives.append(_positive("company_verified", f"Company status: {company_status}"))
        bonus += 5 if company_status == "VERIFIED" else 2
    if not any(f["id"] in ("fee_request", "money_transfer", "equipment_purchase") for f in flags):
        positives.append(_positive("no_fee", "No upfront fee request detected"))
        # Neutral absence of negative evidence; grants no positive trust bonus

    # Critical scam indicators must never be cancelled out by positive signals
    if has_critical:
        bonus = 0
    else:
        bonus = min(bonus, POSITIVE_MAX_BONUS)

    return flags, positives, bonus
