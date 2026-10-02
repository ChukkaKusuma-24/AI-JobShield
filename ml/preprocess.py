"""Shared text preprocessing for training and inference."""
from __future__ import annotations

import re


_HTML_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MONEY_RE = re.compile(
    r"(?:₹|rs\.?\s*|inr\s*|\$|usd\s*)\s*[\d,]+(?:\.\d+)?(?:\s*(?:k|lakh|lakhs|lpa|per\s*month|/month|/day|pm))?",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"\b\d{4,}\b")
_WS_RE = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    if not text:
        return ""
    t = text.lower()
    t = _HTML_RE.sub(" ", t)
    t = _URL_RE.sub(" <URL> ", t)
    t = _EMAIL_RE.sub(" <EMAIL> ", t)
    t = _MONEY_RE.sub(" <MONEY> ", t)
    t = _NUMBER_RE.sub(" <NUM> ", t)
    # Keep useful punctuation cues (! ? $ ₹)
    t = re.sub(r"[^\w\s<>!?\-]", " ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t
