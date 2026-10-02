"""Company verification – evidence-based local heuristics + verified enterprise registry."""
from __future__ import annotations

import json
import re
import socket
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Company


def _free_domains() -> set[str]:
    path = Path(get_settings().DATA_DIR) / "free_email_domains.json"
    if path.exists():
        try:
            return {d.lower() for d in json.loads(path.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com", "icloud.com"}


def _load_verified_registry() -> list[dict]:
    path = Path(get_settings().DATA_DIR) / "verified_companies.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _tokens(name: str) -> set[str]:
    stop = {"pvt", "ltd", "limited", "inc", "llc", "the", "and", "of", "company", "co", "corp", "private", "solutions", "technologies", "services"}
    return {t for t in re.findall(r"[a-z0-9]+", name.lower()) if t not in stop and len(t) > 2}


def _domain_from_url(website: str | None) -> str | None:
    if not website:
        return None
    w = website.strip()
    if not re.match(r"^https?://", w, re.I):
        w = "https://" + w
    try:
        host = urlparse(w).hostname
        if host:
            return host.lower().lstrip("www.")
        return None
    except Exception:
        return None


def _clean_domain(domain_or_email: str | None) -> str | None:
    if not domain_or_email:
        return None
    val = domain_or_email.strip().lower()
    if "@" in val:
        val = val.split("@")[-1]
    val = val.lstrip("www.")
    return val


def find_verified_company_match(name: str) -> dict | None:
    """Find matching verified company record from registry if reliable match exists."""
    clean_name = (name or "").strip().lower()
    if not clean_name:
        return None

    registry = _load_verified_registry()
    name_tokens = _tokens(clean_name)

    # 1. Exact match on name
    for comp in registry:
        if comp["name"].lower() == clean_name:
            return comp

    # 2. Match on aliases
    for comp in registry:
        aliases = [a.lower() for a in comp.get("aliases", [])]
        if clean_name in aliases:
            return comp

    # 3. High similarity or token subset for multi-word
    for comp in registry:
        comp_name = comp["name"].lower()
        comp_tokens = _tokens(comp_name)
        if name_tokens and comp_tokens:
            if name_tokens == comp_tokens:
                return comp
            # E.g. "Infosys Technologies Ltd" vs "Infosys"
            if len(comp_tokens) == 1 and comp_tokens.issubset(name_tokens):
                return comp
            if len(name_tokens) == 1 and name_tokens.issubset(comp_tokens):
                return comp

    return None


def verify_company(
    db: Session,
    company_name: str,
    email: str | None = None,
    website: str | None = None,
) -> dict[str, Any]:
    """
    Evidence-based multi-dimensional company verification.
    Distinguishes:
      - VERIFIED: Recognized entity with matching official domain / channels
      - PARTIALLY VERIFIED: Consistent signals but incomplete independent verification
      - UNVERIFIED: Unknown company with insufficient verifiable data
      - IMPERSONATION_RISK: Known company name used with personal email or mismatched domain
    """
    settings = get_settings()
    free = _free_domains()
    checks: list[dict] = []
    reasons: list[str] = []
    risk_factors: list[str] = []
    positive_factors: list[str] = []

    name = (company_name or "").strip()
    name_toks = _tokens(name)

    email_domain = _clean_domain(email)
    web_domain = _domain_from_url(website)

    matched_record = find_verified_company_match(name)
    if not matched_record and db:
        db_comp = db.query(Company).filter(Company.name.ilike(name)).first()
        if db_comp and db_comp.verification_status == "VERIFIED":
            matched_record = {
                "name": db_comp.name,
                "official_domains": [db_comp.domain] if db_comp.domain else [],
                "source": "db_registry",
            }

    impersonation_detected = False
    company_score = 40  # Baseline for unverified

    # Case 1: Company matches a verified enterprise record
    if matched_record:
        official_name = matched_record["name"]
        official_domains = [d.lower() for d in matched_record.get("official_domains", [])]

        checks.append({
            "name": "registry_match",
            "passed": True,
            "detail": f"Company matched established registry record for '{official_name}'",
        })

        if email_domain:
            is_free = email_domain in free
            domain_matches_official = any(email_domain == od or email_domain.endswith("." + od) for od in official_domains)

            if domain_matches_official:
                checks.append({
                    "name": "official_email_domain",
                    "passed": True,
                    "detail": f"Email domain '@{email_domain}' directly matches official domain for {official_name}",
                })
                positive_factors.append(f"Official recruiter email verified (@{email_domain})")
                positive_factors.append(f"Company verified in independent registry ({official_name})")
                status = "VERIFIED"
                confidence = "Verified / High Confidence"
                company_score = 95
                summary = f"Verified enterprise record: '{official_name}'. Official email domain matches."
                reasons.append(f"Company record found in verified enterprise registry ({official_name}).")
                reasons.append(f"Recruiter email domain directly matches official company domain (@{email_domain}).")

            elif is_free:
                # Critical Impersonation Warning: Known enterprise with @gmail.com
                impersonation_detected = True
                checks.append({
                    "name": "official_email_domain",
                    "passed": False,
                    "detail": f"Impersonation alert: Claimed '{official_name}' but recruiter is using a free email provider (@{email_domain})",
                })
                risk_factors.append(f"High risk: Claimed to be {official_name}, but using a free email (@{email_domain})")
                status = "IMPERSONATION_RISK"
                confidence = "High Risk / Impersonation"
                company_score = 15
                summary = f"Impersonation Risk: Posting claims to be '{official_name}', but recruitment contact is using a personal/free email (@{email_domain})."
                reasons.append(f"CRITICAL: Claimed company is recognized enterprise ('{official_name}'), but recruiter is using a free/personal email (@{email_domain}).")
                reasons.append(f"Legitimate {official_name} recruitment is conducted strictly through official corporate domains, never free webmail.")

            else:
                # Recruiter email domain does not match official domain
                impersonation_detected = True
                checks.append({
                    "name": "official_email_domain",
                    "passed": False,
                    "detail": f"Domain mismatch: Recruiter email domain '@{email_domain}' does not match official domain ({', '.join(official_domains)})",
                })
                risk_factors.append(f"Domain mismatch: Recruiter email (@{email_domain}) does not match official {official_name} domain")
                status = "IMPERSONATION_RISK"
                confidence = "High Risk / Impersonation"
                company_score = 15
                summary = f"Impersonation Risk: Recruiter email domain '@{email_domain}' does not match official {official_name} domain."
                reasons.append(f"Domain mismatch: Recruiter email domain (@{email_domain}) does not match official corporate domain ({', '.join(official_domains)}).")

        elif web_domain:
            domain_matches_official = any(web_domain == od or web_domain.endswith("." + od) for od in official_domains)
            if domain_matches_official:
                checks.append({
                    "name": "official_website_domain",
                    "passed": True,
                    "detail": f"Website domain '{web_domain}' matches official domain for {official_name}",
                })
                positive_factors.append(f"Official company website verified ({web_domain})")
                status = "VERIFIED"
                confidence = "Verified / High Confidence"
                company_score = 90
                summary = f"Verified enterprise record: '{official_name}'. Official website confirmed."
                reasons.append(f"Official corporate website domain confirmed ({web_domain}).")
            else:
                checks.append({
                    "name": "official_website_domain",
                    "passed": False,
                    "detail": f"Website domain '{web_domain}' differs from official domain ({', '.join(official_domains)})",
                })
                status = "PARTIALLY VERIFIED"
                confidence = "Partially Verified"
                company_score = 55
                summary = f"Company '{official_name}' matched, but provided website '{web_domain}' differs from known corporate domain."
                reasons.append(f"Provided website '{web_domain}' does not directly match official registry domain.")

        else:
            # Known company, but NO email and NO URL provided in posting -> Incomplete evidence
            status = "PARTIALLY VERIFIED"
            confidence = "Partially Verified"
            company_score = 65
            summary = f"Company name matches recognized enterprise '{official_name}', but posting provides no official contact email or careers URL to verify authenticity."
            reasons.append(f"Company name matches recognized enterprise record ({official_name}).")
            reasons.append("Posting lacks official corporate email or careers link to verify authenticity.")
            positive_factors.append(f"Identifiable enterprise name ({official_name})")

    # Case 2: Unknown company (not in verified registry)
    else:
        checks.append({
            "name": "registry_match",
            "passed": False,
            "detail": f"No independent registry record found for company '{name}'",
        })

        status = "UNVERIFIED"
        confidence = "Unverified"
        reasons.append(f"No reliable independent company record found for '{name}'.")

        if email_domain:
            is_free = email_domain in free
            if is_free:
                company_score = 30
                summary = f"Company '{name}' could not be verified. Recruiter is using a personal/free email (@{email_domain})."
                reasons.append(f"Recruitment contact uses personal/free email provider (@{email_domain}).")
                risk_factors.append(f"Personal email (@{email_domain}) used for company recruitment")
            else:
                company_score = 45
                summary = f"Company '{name}' could not be independently verified. Custom domain (@{email_domain}) provided."
                reasons.append(f"Recruiter email uses custom domain (@{email_domain}), but company has no independent registry record.")
        elif web_domain:
            company_score = 45
            summary = f"Company '{name}' could not be independently verified. Website ({web_domain}) provided."
            reasons.append(f"Website domain ({web_domain}) provided, but company has no independent registry record.")
        else:
            company_score = 40
            summary = (
                f"Company '{name}' could not be independently verified. "
                "Lack of verification does not mean the company is a scam, but requires cautious review."
            )
            reasons.append("Recruiter email domain could not be verified.")
            reasons.append("Job source/website could not be independently verified.")

    # Upsert company record in database
    try:
        domain = web_domain or email_domain
        existing = db.query(Company).filter(Company.name.ilike(name)).first()
        now = datetime.now(timezone.utc)
        if existing:
            if domain:
                existing.domain = domain
            existing.verification_status = status
            existing.last_checked_at = now
            existing.notes = summary[:500]
        else:
            db.add(
                Company(
                    name=name,
                    domain=domain,
                    verification_status=status,
                    last_checked_at=now,
                    notes=summary[:500],
                )
            )
        db.commit()
    except Exception:
        db.rollback()

    return {
        "status": status,
        "confidence_level": confidence,
        "score": company_score,
        "is_known_entity": bool(matched_record),
        "matched_entity": matched_record["name"] if matched_record else None,
        "impersonation_detected": impersonation_detected,
        "checks": checks,
        "reasons": reasons,
        "risk_factors": risk_factors,
        "positive_factors": positive_factors,
        "summary": summary,
    }
