"""Rule-based red-flag and positive-indicator engine with context-aware semantic evaluation."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings
from app.services.company_verifier import resolve_company_identity
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
    r"(?:buy|purchase|pay\s+for)\s+(?:a|an|the|your|their)?\s*(?:home\s+office\s+)?(?:laptop|workstation|computer|equipment|software|kit|device|hardware|tools|materials)",
    r"laptop\s+fee",
    r"workstation\s+(?:fee|deposit|cost|charge)",
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
    r"activation\s+fee",
    r"(?:pay|deposit)\s+(?:₹|rs\.?|inr|\$)\s*[\d,]+\s+(?:before|prior\s+to|to\s+confirm|to\s+join)",
]

DIRECTIVE_MONEY_PATTERNS = [
    r"(?:candidate|applicant|you|must|need\s+to|have\s+to|required\s+to|should)\s+(?:pay|send|transfer|deposit|wire)\s+(?:money|funds|cash|amount|payment|(?:₹|rs\.?|inr|\$)\s*[\d,]+)",
    r"\b(?:wire|transfer|send|pay|deposit)\s+(?:funds|amount|money|cash|(?:₹|rs\.?|inr|\$)\s*[\d,]+|[\d,]+\s*(?:dollars|usd|inr|rs))\b",
    r"(?:pay|send|transfer|deposit|wire)\s+(?:funds|amount|money|cash|(?:₹|rs\.?|inr|\$)\s*[\d,]+)\s+(?:to|into|via|towards)\s+(?:the\s+)?(?:recruiter|hr|manager|account|wallet|upi|phonepe|gpay|vendor|zelle)",
    r"(?:pay|transfer|send|wire)\s+[a-zA-Z0-9\$,\.\s]{0,25}\s*(?:via|through|using)\s+(?:western\s+union|crypto|bitcoin|ethereum|zelle)",
    r"wire\s+(?:funds|amount|money|cash|(?:₹|rs\.?|inr|\$)\s*[\d,]+)",
    r"(?:buy|purchase)\s+(?:a\s+)?(?:gift\s*cards?|vouchers?|crypto|bitcoin|ethereum)\s+(?:and\s+)?(?:send|forward|share|provide)\s+(?:the\s+)?(?:code|pin|details|screenshot)",
    r"deposit\s+(?:crypto|cryptocurrency|bitcoin|ethereum|funds)\s+(?:to|before|for|in\s+order\s+to)\s+(?:receive|start|activate|confirm|work)",
    r"(?:pay|transfer|send|wire)\s+(?:via|through|using)\s+(?:western\s+union|crypto|bitcoin|ethereum|zelle)",
    r"western\s+union\s+(?:transfer|payment)\s+(?:required|to|before)",
    r"(?:pay|transfer|send)\s+(?:via|through|using|to)\s+upi",
    r"upi\s+(?:transfer|payment|id)\s+(?:to|before|required|to\s+activate|to\s+confirm)",
]

CRITICAL_CREDENTIAL_PATTERNS = [
    r"\b(?:otp|cvv|netbanking\s+password|atm\s+pin|card\s+pin)\b",
    r"\b(?:send|share|provide|enter|submit)\s+(?:your\s+)?(?:password|pin|otp|cvv)\b",
    r"\b(?:debit|credit)\s+card\s+(?:number|details|cvv|pin)\b",
]

SOLICITED_IDENTITY_PATTERNS = [
    r"(?:send|email|whatsapp|submit|share|upload|provide|message)\s+(?:your|their|original\s+)*[a-zA-Z\s,]{0,30}(?:aadhaar|aadhar|pan|passport|bank\s+(?:account|details|statement)|debit\s+card)",
    r"(?:aadhaar|aadhar|pan|passport|bank\s+(?:account|details|statement)|debit\s+card)[a-zA-Z\s,]{0,30}(?:prior\s+to\s+interview|before\s+interview|to\s+(?:whatsapp|telegram|email|recruiter))",
]

PREDATORY_URGENCY_PATTERNS = [
    r"within\s+24\s+hours",
    r"limited\s+seats?",
    r"final\s+warning",
    r"hurry\s+up",
    r"last\s+chance",
    r"apply\s+now\s+or\s+(?:lose|cancel|regret)",
    r"offer\s+expires?\s+(?:today|tonight)",
]

STANDARD_URGENCY_PATTERNS = [
    r"urgent(?:ly)?\s+hir",
    r"\bimmediately\b",
    r"immediate\s+join",
]

NO_INTERVIEW_PATTERNS = [
    r"no\s+interview",
    r"guaranteed\s+(?:job|selection|placement)",
    r"instant\s+selection",
    r"direct\s+joining\b",
    r"direct\s+offer\s+letter",
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

UPPER_TECH_ACRONYMS = re.compile(
    r"\b(?:AWS|GCP|AZURE|CI/CD|CI|CD|SQL|REST|APIS?|HTML5?|CSS3?|JSON|HTTPS?|IT|HR|B\.?TECH|BE|MCA|BSC|MBA|TCS|HCL|WIPRO|UI/UX|UI|UX|SDK|PCI-DSS|PCI|DSS|TCP/IP|TCP|IP|DNS|SSL|TLS|AI|ML|LLM|GO|JAVA|C\+\+)\b"
)


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


def _find_fee_request(text: str) -> str | None:
    text_l = text.lower()
    for p in FEE_PATTERNS:
        for m in re.finditer(p, text_l):
            start = m.start()
            prefix = text_l[max(0, start - 80):start]
            last_boundary = max(
                prefix.rfind('.'), prefix.rfind(';'), prefix.rfind('\n'),
                prefix.rfind('but '), prefix.rfind('however ')
            )
            clause_prefix = prefix[last_boundary + 1:] if last_boundary != -1 else prefix
            if re.search(r"\b(?:no|never|without|zero|not\s+charge|not\s+require|not\s+ask|free\s+of|strictly\s+no)\b", clause_prefix):
                continue
            if re.search(r"\b(?:company|employer)\s+(?:covers?|pays?|sponsors?)\s+(?:all\s+)?", clause_prefix):
                continue
            suffix = text_l[m.end():min(len(text_l), m.end() + 50)]
            if re.search(r"^\s*(?:reimbursement|waiver|covered\s+by\s+company|not\s+required)", suffix):
                continue

            snippet_start = max(0, start - 20)
            snippet_end = min(len(text), m.end() + 40)
            return text[snippet_start:snippet_end].strip()
    return None


def _find_equipment_purchase(text: str) -> str | None:
    text_l = text.lower()
    for p in EQUIPMENT_PATTERNS:
        for m in re.finditer(p, text_l):
            start = m.start()
            prefix = text_l[max(0, start - 50):start]
            if re.search(r"\b(?:no|never|without|free|company\s+provides?|employer\s+provides?)\b", prefix):
                continue
            if re.search(r"\b(?:responsible\s+for|duties\s+include|role\s+involves)\s+(?:purchasing|procuring)\b", prefix):
                continue
            snippet_start = max(0, start - 20)
            snippet_end = min(len(text), m.end() + 40)
            return text[snippet_start:snippet_end].strip()
    return None


def _find_money_transfer(text: str) -> str | None:
    text_l = text.lower()
    for p in DIRECTIVE_MONEY_PATTERNS:
        m = re.search(p, text_l)
        if m:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 40)
            return text[start:end].strip()
    return None


def _find_sensitive_info(text: str) -> str | None:
    text_l = text.lower()
    # 1. Critical credentials (OTP, PIN, Password, Card numbers)
    for p in CRITICAL_CREDENTIAL_PATTERNS:
        m = re.search(p, text_l)
        if m:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 40)
            return text[start:end].strip()

    # 2. Solicited identity documents (Aadhaar, PAN, Bank statement)
    for p in SOLICITED_IDENTITY_PATTERNS:
        m = re.search(p, text_l)
        if m:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 40)
            return text[start:end].strip()

    return None


def _check_unrealistic_salary(title: str, description: str, salary: str | None) -> str | None:
    text_l = f"{title} {description} {salary or ''}".lower()
    is_senior = bool(re.search(r"\b(?:senior|lead|principal|architect|manager|director|head|vp|executive|expert|staff)\b|\b(?:[5-9]|\d{2})\+?\s*(?:years?|yrs?)\b", text_l))
    is_entry = bool(re.search(r"\b(?:intern|internship|fresher|freshers|entry[- ]level|no\s+experience|student|typing|data\s+entry|simple\s+typing|copy\s+paste|ad\s+click)\b", text_l))

    # Daily rate checks
    daily = re.search(r"(?:₹|rs\.?\s*|inr\s*)\s*([\d,]+)\s*(?:/|\s*per\s*)\s*day", text_l)
    earn_day = re.search(r"earn\s+(?:₹|rs\.?\s*)?\s*([\d,]+)\s*(?:/|\s*per\s*)?\s*day", text_l)
    for m in (daily, earn_day):
        if m:
            amt = int(m.group(1).replace(",", ""))
            if (is_entry and amt >= 2000) or (amt >= 8000 and not is_senior) or (amt >= 20000):
                return m.group(0)

    # Monthly rate checks
    monthly = re.search(r"(?:₹|rs\.?\s*|inr\s*)\s*([\d,]+)\s*(?:/|\s*per\s*)\s*month", text_l)
    earn_month = re.search(r"earn\s+(?:₹|rs\.?\s*)?\s*([\d,]+)\s*(?:/|\s*per\s*)\s*month", text_l)
    for m in (monthly, earn_month):
        if m:
            amt = int(m.group(1).replace(",", ""))
            if is_entry and amt >= 120000:
                return m.group(0)
            if not is_senior and amt >= 300000:
                return m.group(0)

    # Annual salary checks
    annual_lakh = re.search(r"(?:₹|rs\.?\s*|inr\s*)\s*([\d,]+)\s*(?:lakh|lakhs|lpa|per\s+annum)", text_l)
    if annual_lakh:
        amt = int(annual_lakh.group(1).replace(",", ""))
        if is_entry and amt >= 25:
            return annual_lakh.group(0)

    return None


def _find_suspicious_contact(text: str, company_status: str | None = None, is_official_url: bool = False) -> str | None:
    text_l = text.lower()
    exclusive_match = re.search(r"\b(?:whatsapp|telegram)\s+only\b", text_l)
    if exclusive_match:
        return exclusive_match.group(0)

    if company_status == "VERIFIED" and is_official_url:
        return None

    ev = _find_first(WHATSAPP_PATTERNS, text)
    if ev:
        return ev
    return None


def _find_urgency(text: str, has_other_scam_signals: bool = False) -> str | None:
    # 1. Predatory urgency always flags
    ev_pred = _find_first(PREDATORY_URGENCY_PATTERNS, text)
    if ev_pred:
        return ev_pred

    # 2. Standard urgency flags only when accompanied by other scam cues
    if has_other_scam_signals:
        ev_std = _find_first(STANDARD_URGENCY_PATTERNS, text)
        if ev_std:
            return ev_std

    return None


def _find_no_interview(text: str) -> str | None:
    return _find_first(NO_INTERVIEW_PATTERNS, text)


def _check_caps_exclaim(description: str) -> str | None:
    filtered_text = UPPER_TECH_ACRONYMS.sub("", description)
    caps_ratio = sum(1 for c in filtered_text if c.isupper()) / max(len(filtered_text), 1)
    bangs = description.count("!")
    if caps_ratio > 0.35 or bangs >= 4:
        return f"caps_ratio={caps_ratio:.2f}, exclamations={bangs}"
    return None


def _check_vague_description(description: str) -> str | None:
    desc_clean = description.strip()
    if len(desc_clean) < 80:
        return desc_clean[:80] + ("…" if len(desc_clean) > 80 else "")
    if not _find_first(RESPONSIBILITY_CUES, desc_clean) and not _find_first(QUAL_CUES, desc_clean):
        return desc_clean[:80] + ("…" if len(desc_clean) > 80 else "")
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
    free_domains = {d.lower() for d in _load_json_list("free_email_domains.json")}
    text = f"{title}\n{company_name}\n{description}\n{salary or ''}\n{email or ''}\n{url or ''}"
    text_l = text.lower()
    flags: list[dict] = []
    positives: list[dict] = []
    bonus = 0

    identity = resolve_company_identity(company_name)

    is_official_url = False
    if url and identity.is_known_entity and identity.official_domains:
        try:
            cand = url if "://" in url else "https://" + url
            clean_host = (urlparse(cand).hostname or "").lower().removeprefix("www.")
            is_official_url = any(clean_host == od or clean_host.endswith("." + od) for od in identity.official_domains)
        except Exception:
            pass

    # 1. Fee request
    fee_ev = _find_fee_request(text)
    if fee_ev:
        flags.append(_flag("fee_request", fee_ev))

    # 2. Equipment purchase
    equip_ev = _find_equipment_purchase(text)
    if equip_ev:
        flags.append(_flag("equipment_purchase", equip_ev))

    # 3. Money transfer
    money_ev = _find_money_transfer(text)
    if money_ev and not any(f["id"] == "fee_request" for f in flags):
        flags.append(_flag("money_transfer", money_ev))
    elif money_ev and any(f["id"] == "fee_request" for f in flags):
        if re.search(r"gift\s*card|crypto|bitcoin|western\s+union", text_l):
            flags.append(_flag("money_transfer", money_ev))

    # 4. Company impersonation
    if company_status == "IMPERSONATION_RISK":
        flags.append(_flag("company_impersonation", f"Recruiter contact ({email or 'N/A'}) mismatches verified company profile"))

    # 5. Sensitive info
    sens_ev = _find_sensitive_info(text)
    if sens_ev:
        flags.append(_flag("sensitive_info", sens_ev))

    # 6. Unrealistic salary
    unreal_sal = _check_unrealistic_salary(title, description, salary)
    if unreal_sal:
        flags.append(_flag("unrealistic_salary", unreal_sal))

    # 7. Suspicious contact
    contact_ev = _find_suspicious_contact(text, company_status=company_status, is_official_url=is_official_url)
    if contact_ev:
        flags.append(_flag("suspicious_contact", contact_ev))

    # 8. Email domain checks
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

    # 9. Urgency
    has_other_scam = any(f["severity"] == "critical" or f["id"] in ("unrealistic_salary", "suspicious_contact") for f in flags)
    urg_ev = _find_urgency(text, has_other_scam_signals=has_other_scam)
    if urg_ev:
        flags.append(_flag("urgency", urg_ev))

    # 10. No interview
    no_int_ev = _find_no_interview(text)
    if no_int_ev:
        flags.append(_flag("no_interview", no_int_ev))

    # 11. Vague description
    vague_ev = _check_vague_description(description)
    if vague_ev:
        flags.append(_flag("vague_description", vague_ev))

    # 12. Caps / exclamations
    caps_ev = _check_caps_exclaim(description)
    if caps_ev:
        flags.append(_flag("caps_exclaim", caps_ev))

    # 13. Suspicious URL
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
    has_impersonation = any(f.get("id") == "company_impersonation" for f in flags) or company_status == "IMPERSONATION_RISK"

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
