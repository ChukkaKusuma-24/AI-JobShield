"""Shared text preprocessing for training and inference."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_HTML_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MONEY_RE = re.compile(
    r"(?:₹|rs\.?\s*|inr\s*|\$|usd\s*)\s*[\d,]+(?:\.\d+)?(?:\s*(?:k|lakh|lakhs|lpa|per\s*month|/month|/day|pm))?",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(
    r"(?:\+?91[-.\s]*)?[6-9]\d{3}[-.\s]*\d{6}\b|"
    r"(?:\+?91[-.\s]*)?[6-9]\d{4}[-.\s]*\d{5}\b|"
    r"(?:\+?91[-.\s]*)?[6-9]\d{9}\b|"
    r"(?:\+?\d{1,3}[-.\s]*)?\(?\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b"
)
_NUMBER_RE = re.compile(r"\b\d{4,}\b")
_WS_RE = re.compile(r"\s+")

# Build known company list for entity masking
_COMPANIES: set[str] = {
    # Tech & IT Services
    "Tata Consultancy Services", "TCS", "Infosys", "Wipro", "HCL Technologies",
    "HCL Tech", "HCL", "Tech Mahindra", "Cognizant", "Accenture", "Capgemini",
    "IBM India", "IBM", "Larsen & Toubro Infotech", "LTI", "L&T", "Mindtree",
    "Zoho Corporation", "Zoho", "Freshworks", "Razorpay", "PhonePe", "Paytm",
    "Flipkart", "Amazon India", "Amazon", "Microsoft India", "Microsoft",
    "Google India", "Google", "Meta", "Apple", "Swiggy", "Zomato",
    "Jio Platforms", "Reliance Jio", "Reliance Industries", "Reliance", "Jio",
    "Airtel Digital", "Bharti Airtel", "Airtel", "Cred", "Zerodha", "Polygon",
    # Known scam and synthetic entities
    "Apex Solutions", "Apex Global Services", "Global Opportunity Hub",
    "Quick Cash Careers", "Prime Earn Online", "Dream Job Express",
    "Instant Hire India", "BrightPath Services", "BrightPath Careers",
    "FastJobs India", "Prime Talent Group", "Digital Dynamics",
    "NextGen Infotech", "Starlight Media", "Vertex Global", "Universal Staffing",
    "Elite Systems", "Zenith Corp", "Vanguard Technologies", "Alpha Star Innovations",
    "Horizon Ventures", "QuickJobsIndia", "QuickHire India",
}

# Dynamically load from data/verified_companies.json if available
try:
    _verified_file = ROOT / "data" / "verified_companies.json"
    if _verified_file.exists():
        with open(_verified_file, "r", encoding="utf-8") as _f:
            _v_data = json.load(_f)
            if isinstance(_v_data, list):
                for _item in _v_data:
                    if _item.get("name"):
                        _COMPANIES.add(_item["name"])
                    for _alias in _item.get("aliases", []):
                        _COMPANIES.add(_alias)
except Exception:
    pass

_SORTED_COMPANIES = sorted(_COMPANIES, key=len, reverse=True)
_COMPANY_RE = re.compile(r"\b(?:" + "|".join(map(re.escape, _SORTED_COMPANIES)) + r")\b", re.IGNORECASE)


def preprocess_text(text: str, company_name: str | None = None) -> str:
    """Universal entity-masking and text preprocessing.
    
    Transforms raw input text by masking entities (<URL>, <EMAIL>, <MONEY>,
    <PHONE>, <COMPANY>, <NUM>) while strictly preserving semantic and intent cues.
    Used identically during training, validation, testing, and live inference.
    """
    if not text:
        return ""

    t = text

    # 1. HTML tags removal
    t = _HTML_RE.sub(" ", t)

    # 2. URL masking
    t = _URL_RE.sub(" <URL> ", t)

    # 3. Email masking
    t = _EMAIL_RE.sub(" <EMAIL> ", t)

    # 4. Monetary value masking
    t = _MONEY_RE.sub(" <MONEY> ", t)

    # 5. Phone number masking
    t = _PHONE_RE.sub(" <PHONE> ", t)

    # 6. Specific user/input company name masking (if provided)
    if company_name and company_name.strip():
        t = re.sub(r"\b" + re.escape(company_name.strip()) + r"\b", " <COMPANY> ", t, flags=re.IGNORECASE)

    # 7. Known company names and aliases masking
    t = _COMPANY_RE.sub(" <COMPANY> ", t)

    # 8. Remaining large integers (4+ digits)
    t = _NUMBER_RE.sub(" <NUM> ", t)

    # 9. Keep useful punctuation cues (! ? $ ₹ -) and entity tokens (< >)
    t = re.sub(r"[^\w\s<>!?\-]", " ", t)

    # 10. Collapse whitespace and lowercase
    t = _WS_RE.sub(" ", t).strip()
    return t.lower()
