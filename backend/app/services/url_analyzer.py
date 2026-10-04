"""Local heuristic URL analyzer – no network fetching."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings

SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "rebrand.ly",
    "cutt.ly",
    "rb.gy",
}
SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "secure",
    "payment",
    "bonus",
    "free",
    "claim",
    "account",
    "update",
    "confirm",
    "wallet",
    "prize",
]


def _suspicious_tlds() -> set[str]:
    path = Path(get_settings().DATA_DIR) / "suspicious_tlds.json"
    if path.exists():
        return {t.lower().lstrip(".") for t in json.loads(path.read_text(encoding="utf-8"))}
    return {"tk", "ml", "xyz", "top"}


def _normalize_company(name: str) -> set[str]:
    stop = {"pvt", "ltd", "limited", "inc", "llc", "the", "and", "of", "company", "co"}
    return {t for t in re.findall(r"[a-z0-9]+", name.lower()) if t not in stop and len(t) > 2}


def analyze_url(url: str, company_name: str | None = None) -> dict[str, Any]:
    raw = (url or "").strip()
    if not raw:
        return {
            "url": raw,
            "valid": False,
            "indicators": [],
            "risk_level": "HIGH",
            "risk_score": 100,
            "explanation": "URL is empty or invalid.",
        }

    candidate = raw if re.match(r"^https?://", raw, re.I) else "http://" + raw
    try:
        parsed = urlparse(candidate)
    except Exception:
        return {
            "url": raw,
            "valid": False,
            "indicators": [{"id": "parse_error", "label": "Could not parse URL", "severity": "high"}],
            "risk_level": "HIGH",
            "risk_score": 90,
            "explanation": "The provided string could not be parsed as a URL.",
        }

    host = (parsed.hostname or "").lower()
    if not host or "." not in host:
        return {
            "url": raw,
            "valid": False,
            "indicators": [{"id": "no_host", "label": "Missing or invalid hostname", "severity": "high"}],
            "risk_level": "HIGH",
            "risk_score": 90,
            "explanation": "URL is missing a valid hostname.",
        }

    indicators: list[dict] = []
    score = 0

    if len(raw) > 100:
        indicators.append({"id": "long_url", "label": "Unusually long URL", "severity": "low"})
        score += 8

    if "@" in raw:
        indicators.append({"id": "at_sign", "label": "Contains '@' character", "severity": "high"})
        score += 25

    if re.search(r"https?://\d{1,3}(?:\.\d{1,3}){3}", candidate):
        indicators.append({"id": "ip_host", "label": "Uses IP address as host", "severity": "high"})
        score += 30

    labels = host.split(".")
    if len(labels) >= 4:
        indicators.append({"id": "subdomains", "label": "Excessive subdomains", "severity": "medium"})
        score += 15

    hyphen_digits = len(re.findall(r"[-0-9]", host))
    if hyphen_digits >= 6:
        indicators.append(
            {"id": "hyphen_digits", "label": "Many hyphens/digits in domain", "severity": "medium"}
        )
        score += 12

    path_q = (parsed.path or "") + (parsed.query or "")
    for kw in SUSPICIOUS_KEYWORDS:
        if kw in candidate.lower():
            indicators.append(
                {"id": f"kw_{kw}", "label": f"Contains suspicious keyword '{kw}'", "severity": "medium"}
            )
            score += 8
            break

    if host in SHORTENERS or any(host.endswith("." + s) for s in SHORTENERS):
        indicators.append({"id": "shortener", "label": "URL shortener domain", "severity": "medium"})
        score += 18

    if parsed.scheme == "http":
        indicators.append({"id": "http", "label": "Uses HTTP instead of HTTPS", "severity": "medium"})
        score += 12

    tld = labels[-1] if labels else ""
    if tld in _suspicious_tlds():
        indicators.append(
            {"id": "tld", "label": f"Suspicious/free TLD '.{tld}'", "severity": "high"}
        )
        score += 22

    if "xn--" in host:
        indicators.append({"id": "punycode", "label": "Punycode / IDN domain", "severity": "high"})
        score += 25

    if re.search(r"[^\x00-\x7f]", host):
        indicators.append(
            {"id": "lookalike", "label": "Non-ASCII / lookalike characters in host", "severity": "high"}
        )
        score += 25

    if company_name:
        from app.services.company_verifier import resolve_company_identity
        identity = resolve_company_identity(company_name)
        clean_host = host.lower().removeprefix("www.")

        is_official = False
        if identity.is_known_entity and identity.official_domains:
            is_official = any(clean_host == od or clean_host.endswith("." + od) for od in identity.official_domains)

        if is_official:
            indicators.append({
                "id": "official_domain",
                "label": f"Matches verified official corporate domain ({clean_host})",
                "severity": "low",
            })
        elif identity.is_known_entity:
            # Company is a recognized enterprise, but URL is NOT on their registered official domain
            host_toks = set(re.findall(r"[a-z0-9]+", host.replace(".", " ")))
            if identity.tokens & host_toks:
                indicators.append({
                    "id": "lookalike_domain",
                    "label": f"Lookalike domain attempting to imitate {identity.canonical_name}",
                    "severity": "high",
                })
                indicators.append({
                    "id": "company_mismatch",
                    "label": f"Domain '{clean_host}' is not a registered official domain for {identity.canonical_name}",
                    "severity": "high",
                })
                score += 30
            else:
                indicators.append({
                    "id": "company_mismatch",
                    "label": f"Domain does not match verified official domain for {identity.canonical_name}",
                    "severity": "medium",
                })
                score += 15
        else:
            host_toks = set(re.findall(r"[a-z0-9]+", host.replace(".", " ")))
            if identity.tokens and not (identity.tokens & host_toks):
                indicators.append({
                    "id": "company_mismatch",
                    "label": "Domain does not resemble company name",
                    "severity": "medium",
                })
                score += 15

    score = min(score, 100)
    if score >= 50:
        risk_level = "HIGH"
    elif score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if indicators:
        explanation = (
            "This URL shows suspicious characteristics based on local heuristics "
            f"(risk score {score}). This does not prove the link is malicious—verify carefully."
        )
    else:
        explanation = (
            "No strong local heuristic red flags were found for this URL. "
            "Absence of flags does not guarantee safety."
        )

    return {
        "url": raw,
        "valid": True,
        "indicators": indicators,
        "risk_level": risk_level,
        "risk_score": score,
        "explanation": explanation,
    }
