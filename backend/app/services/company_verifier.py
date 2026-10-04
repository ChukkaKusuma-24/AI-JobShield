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


def normalize_company_name(name: str) -> str:
    """Normalize company name by stripping legal suffixes and standardizing punctuation."""
    if not name:
        return ""
    val = name.strip().lower()
    val = re.sub(r"[\.,\-_/&]+", " ", val)
    suffixes = [
        r"\bpvt\s+ltd\b", r"\bprivate\s+limited\b", r"\bltd\b", r"\blimited\b",
        r"\binc\b", r"\bincorporated\b", r"\bllc\b", r"\bcorp\b", r"\bcorporation\b",
        r"\bco\b", r"\bcompany\b",
    ]
    for s in suffixes:
        val = re.sub(s, "", val)
    return re.sub(r"\s+", " ", val).strip()


def generate_acronym(name: str) -> str | None:
    """Generate canonical acronym from company name tokens (e.g. 'Tata Consultancy Services' -> 'tcs')."""
    if not name:
        return None
    stop = {"pvt", "ltd", "limited", "inc", "llc", "the", "and", "of", "co", "corp", "company", "private"}
    words = [w for w in re.findall(r"[a-zA-Z0-9]+", name) if w.lower() not in stop]
    if len(words) >= 2:
        return "".join(w[0].lower() for w in words)
    return None


class CompanyIdentity:
    """Represents resolved, normalized company identity across legal names, aliases, and official domains."""
    def __init__(
        self,
        raw_name: str,
        canonical_name: str,
        is_known_entity: bool,
        verification_status: str,
        official_domains: list[str],
        careers_urls: list[str],
        aliases: list[str],
        acronym: str | None,
        tokens: set[str],
    ):
        self.raw_name = raw_name
        self.canonical_name = canonical_name
        self.is_known_entity = is_known_entity
        self.verification_status = verification_status
        self.official_domains = official_domains
        self.careers_urls = careers_urls
        self.aliases = aliases
        self.acronym = acronym
        self.tokens = tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_name": self.raw_name,
            "canonical_name": self.canonical_name,
            "is_known_entity": self.is_known_entity,
            "verification_status": self.verification_status,
            "official_domains": self.official_domains,
            "careers_urls": self.careers_urls,
            "aliases": self.aliases,
            "acronym": self.acronym,
        }


def find_verified_company_match(name: str) -> dict | None:
    """Find matching verified company record from registry if reliable match exists."""
    clean_name = (name or "").strip().lower()
    if not clean_name:
        return None

    registry = _load_verified_registry()
    name_norm = normalize_company_name(clean_name)
    name_tokens = _tokens(clean_name)
    name_acronym = generate_acronym(clean_name)

    # 1. Exact match on name or normalized legal name
    for comp in registry:
        c_name = comp["name"].lower()
        if c_name == clean_name or normalize_company_name(c_name) == name_norm:
            return comp

    # 2. Match on aliases
    for comp in registry:
        aliases = [a.lower() for a in comp.get("aliases", [])]
        if clean_name in aliases or name_norm in aliases:
            return comp

    # 3. Match on acronyms
    for comp in registry:
        comp_acronym = generate_acronym(comp["name"])
        if comp_acronym and (clean_name == comp_acronym or name_norm == comp_acronym):
            return comp
        if name_acronym and name_acronym in [a.lower() for a in comp.get("aliases", [])]:
            return comp

    # 4. Token subset for multi-word
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


def resolve_company_identity(company_name: str, db: Session | None = None) -> CompanyIdentity:
    """Resolve raw company name into normalized CompanyIdentity using registry and database."""
    name = (company_name or "").strip()
    if not name:
        return CompanyIdentity(
            raw_name="",
            canonical_name="Unknown",
            is_known_entity=False,
            verification_status="UNVERIFIED",
            official_domains=[],
            careers_urls=[],
            aliases=[],
            acronym=None,
            tokens=set(),
        )

    matched = find_verified_company_match(name)
    if not matched and db:
        try:
            db_comp = db.query(Company).filter(Company.name.ilike(name)).first()
            if db_comp and db_comp.verification_status == "VERIFIED":
                matched = {
                    "name": db_comp.name,
                    "official_domains": [db_comp.domain] if db_comp.domain else [],
                    "status": "VERIFIED",
                    "source": "db_registry",
                }
        except Exception:
            pass

    if matched:
        canonical_name = matched["name"]
        aliases = [a.lower() for a in matched.get("aliases", [])]
        official_domains = [d.lower() for d in matched.get("official_domains", [])]
        careers_urls = matched.get("careers_urls", [])
        status = matched.get("status", "VERIFIED")
        acronym = generate_acronym(canonical_name)
        if not acronym and aliases:
            for a in aliases:
                if 2 <= len(a) <= 5 and a.isalnum():
                    acronym = a
                    break

        toks = set(_tokens(canonical_name)) | set(_tokens(name))
        for a in aliases:
            toks.update(_tokens(a))
            if 2 <= len(a) <= 5:
                toks.add(a)
        if acronym:
            toks.add(acronym)
        for od in official_domains:
            domain_root = od.split(".")[0]
            if len(domain_root) >= 2:
                toks.add(domain_root)

        return CompanyIdentity(
            raw_name=name,
            canonical_name=canonical_name,
            is_known_entity=True,
            verification_status=status,
            official_domains=official_domains,
            careers_urls=careers_urls,
            aliases=aliases,
            acronym=acronym,
            tokens=toks,
        )
    else:
        acronym = generate_acronym(name)
        toks = set(_tokens(name))
        if acronym:
            toks.add(acronym)
        return CompanyIdentity(
            raw_name=name,
            canonical_name=name,
            is_known_entity=False,
            verification_status="UNVERIFIED",
            official_domains=[],
            careers_urls=[],
            aliases=[],
            acronym=acronym,
            tokens=toks,
        )


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

    identity = resolve_company_identity(name, db)
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

        email_check_passed = False
        web_check_passed = False

        if email_domain:
            is_free = email_domain in free
            domain_matches_official = any(email_domain == od or email_domain.endswith("." + od) for od in official_domains)

            if domain_matches_official:
                email_check_passed = True
                checks.append({
                    "name": "official_email_domain",
                    "passed": True,
                    "detail": f"Email domain '@{email_domain}' directly matches official domain for {official_name}",
                })
                positive_factors.append(f"Official recruiter email verified (@{email_domain})")
                positive_factors.append(f"Company verified in independent registry ({official_name})")
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
                reasons.append(f"Domain mismatch: Recruiter email domain (@{email_domain}) does not match official corporate domain ({', '.join(official_domains)}).")

        if web_domain:
            domain_matches_official = any(web_domain == od or web_domain.endswith("." + od) for od in official_domains)
            if domain_matches_official:
                web_check_passed = True
                checks.append({
                    "name": "official_website_domain",
                    "passed": True,
                    "detail": f"Website domain '{web_domain}' matches official domain for {official_name}",
                })
                positive_factors.append(f"Official company website verified ({web_domain})")
                reasons.append(f"Official corporate website domain confirmed ({web_domain}).")
            else:
                checks.append({
                    "name": "official_website_domain",
                    "passed": False,
                    "detail": f"Website domain '{web_domain}' differs from official domain ({', '.join(official_domains)})",
                })
                risk_factors.append(f"Provided website '{web_domain}' differs from official {official_name} domain")
                reasons.append(f"Provided website '{web_domain}' does not directly match official registry domain.")

        # Determine overall status and score
        if impersonation_detected:
            status = "IMPERSONATION_RISK"
            confidence = "High Risk / Impersonation"
            company_score = 15
            summary = f"Impersonation Risk: Posting claims to be '{official_name}', but recruitment contact mismatches verified company profile."
        elif email_check_passed and web_check_passed:
            status = "VERIFIED"
            confidence = "Verified / High Confidence"
            company_score = 95
            summary = f"Verified enterprise record: '{official_name}'. Official email and website confirmed."
        elif email_check_passed and web_domain and not web_check_passed:
            status = "PARTIALLY VERIFIED"
            confidence = "Partially Verified"
            company_score = 60
            summary = f"Company '{official_name}' matched official email domain, but provided website '{web_domain}' differs from known corporate domain."
        elif email_check_passed:
            status = "VERIFIED"
            confidence = "Verified / High Confidence"
            company_score = 95
            summary = f"Verified enterprise record: '{official_name}'. Official email domain matches."
        elif web_check_passed:
            status = "VERIFIED"
            confidence = "Verified / High Confidence"
            company_score = 90
            summary = f"Verified enterprise record: '{official_name}'. Official website confirmed."
        elif web_domain and not web_check_passed:
            status = "PARTIALLY VERIFIED"
            confidence = "Partially Verified"
            company_score = 55
            summary = f"Company '{official_name}' matched, but provided website '{web_domain}' differs from known corporate domain."
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
    if db is not None:
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
        "company_score": company_score,
        "is_known_entity": bool(matched_record),
        "matched_entity": matched_record["name"] if matched_record else None,
        "impersonation_detected": impersonation_detected,
        "checks": checks,
        "reasons": reasons,
        "risk_factors": risk_factors,
        "positive_factors": positive_factors,
        "summary": summary,
        "identity": identity.to_dict(),
    }
