"""Deterministic job/recruitment/resume content validation for OCR text."""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jobshield.ocr_validate")

# Strong multi-word / high-value signals (weight 3)
STRONG_PATTERNS: list[tuple[str, str]] = [
    (r"\bwe are hiring\b", "we_are_hiring"),
    (r"\bnow hiring\b", "now_hiring"),
    (r"\bjob (?:posting|description|opening|opportunity|vacancy|role)\b", "job_posting"),
    (r"\b(?:full[- ]time|part[- ]time|contract)\s+(?:job|role|position)\b", "employment_type_role"),
    (r"\b(?:internship|intern(?:ship)?\s+opportunity)\b", "internship"),
    (r"\b(?:software|backend|frontend|java|python|web|data)\s+(?:engineer|developer|analyst|intern)\b", "tech_role"),
    (r"\b(?:work experience|professional experience|employment history)\b", "work_experience"),
    (r"\b(?:required skills|key responsibilities|job responsibilities|qualifications)\b", "jd_sections"),
    (r"\b(?:apply now|apply (?:via|at|through)|send (?:your )?(?:cv|resume))\b", "apply_cta"),
    (r"\b(?:curriculum vitae|\bcv\b|\bresume\b)\b", "resume_cv"),
    (r"\b(?:salary|compensation|ctc|stipend)\b", "compensation"),
    (r"\b(?:lpa|per annum|/month|/yr)\b", "pay_unit"),
    (r"\b(?:recruiter|talent acquisition|hiring manager|hr\s*(?:team|manager)?)\b", "recruiter"),
    (r"\b(?:interview process|technical round|hr round|selection process)\b", "interview"),
    (r"\b(?:career opportunity|careers page|join our team)\b", "career"),
    (r"\b(?:candidate|applicant)\b", "candidate"),
    (r"\b(?:job application|application deadline)\b", "application"),
    (r"\b(?:years? of experience|\d+\+?\s*yrs?\b)", "yoe"),
]

# Medium single signals (weight 2) — still need multiple hits overall
MEDIUM_PATTERNS: list[tuple[str, str]] = [
    (r"\bhiring\b", "hiring"),
    (r"\brecruit(?:ment|ing)?\b", "recruitment"),
    (r"\bemployment\b", "employment"),
    (r"\bvacancy|vacancies\b", "vacancy"),
    (r"\bposition\b", "position"),
    (r"\bopportunity\b", "opportunity"),
    (r"\bskills?\b", "skills"),
    (r"\bexperience\b", "experience"),
    (r"\beducation\b", "education"),
    (r"\bprojects?\b", "projects"),
    (r"\bintern\b", "intern"),
    (r"\bjob\b", "job"),
    (r"\bcareer\b", "career_word"),
    (r"\bsalary\b", "salary_word"),
    (r"\binterview\b", "interview_word"),
    (r"\bcompany\b", "company"),
    (r"\bresponsibilities\b", "responsibilities"),
    (r"\bqualifications?\b", "qualifications"),
    (r"\beligibility\b", "eligibility"),
    (r"\bonboarding\b", "onboarding"),
    (r"\bnotice period\b", "notice_period"),
    (r"\bremote\b", "remote"),
    (r"\bwfh\b|\bwork from home\b", "wfh"),
]

# Weak signals (weight 1) — alone must NOT accept
WEAK_PATTERNS: list[tuple[str, str]] = [
    (r"\bemail\b|@", "email_mention"),
    (r"\bphone\b|\bmobile\b|\bwhatsapp\b", "contact"),
    (r"https?://", "url"),
    (r"\bapply\b", "apply_word"),
    (r"\bteam\b", "team"),
    (r"\brole\b", "role"),
]

# Anti-signals: coding contests, shopping, etc. (subtract / gate)
ANTI_PATTERNS: list[tuple[str, str, int]] = [
    (r"\bcodeforces\b", "codeforces", 8),
    (r"\bleetcode\b|\bhackerrank\b|\batcoder\b|\bcodechef\b", "oj_platform", 8),
    (r"\bcontest\b", "contest", 4),
    (r"\bproblemset\b|\bproblem\s*[a-z0-9]\b|\btestcase\b|\btest case\b", "problemset", 5),
    (r"\baccepted\b|\bwrong answer\b|\btime limit\b|\bmemory limit\b|\bruntime error\b|\bverdict\b", "oj_verdict", 6),
    (r"\bc\+\+20\b|\bpython3\b|\bjava\s*17\b|\bcompilation error\b", "oj_lang", 3),
    (r"\bstanding[s]?\b|\brating\b|\bdiv\.?\s*[12]\b", "contest_meta", 4),
    (r"\bcart\b|\bcheckout\b|\border\s+(?:id|summary|total)\b|\bdelivery\b|\badd to cart\b", "shopping", 8),
    (r"\bpayment\b|\bupi\b|\bgpay\b|\bpaypal\b", "payment_ui", 3),
    (r"\binstagram\b|\bstories?\b|\breels?\b|\blikes?\b|\bfollowers?\b", "social", 5),
    (r"\bweather\b|\bforecast\b|\bhumidity\b", "weather", 5),
    (r"\bscoreboard\b|\bleaderboard\b", "scoreboard", 4),
]

MIN_SCORE = 8
MIN_DISTINCT_SIGNALS = 3
# If anti_score is high and job score is weak, force reject
ANTI_FORCE_REJECT = 6

REJECT_MESSAGE = (
    "This image does not appear to contain job, recruitment, resume, or employment-related content."
)
USER_FACING_MESSAGE = (
    "This doesn't appear to be a job or recruitment-related document. "
    "Please upload a job posting, recruiter message, resume/CV, or similar document."
)


def _find_matches(patterns: list[tuple[str, str]], text: str, weight: int) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for pattern, signal_id in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({"id": signal_id, "weight": weight, "pattern": pattern})
    return hits


def validate_job_related_text(text: str) -> dict[str, Any]:
    """
    Score extracted OCR text for job/recruitment/resume relevance.

    Returns:
      valid, score, signals, anti_signals, message
    """
    raw = (text or "").strip()
    lowered = raw.lower()

    strong = _find_matches(STRONG_PATTERNS, lowered, 3)
    medium = _find_matches(MEDIUM_PATTERNS, lowered, 2)
    weak = _find_matches(WEAK_PATTERNS, lowered, 1)

    # Deduplicate by signal id (keep highest weight)
    by_id: dict[str, dict[str, Any]] = {}
    for hit in strong + medium + weak:
        prev = by_id.get(hit["id"])
        if not prev or hit["weight"] > prev["weight"]:
            by_id[hit["id"]] = hit
    signals = list(by_id.values())
    score = sum(s["weight"] for s in signals)
    distinct = len(signals)

    anti_hits: list[dict[str, Any]] = []
    anti_score = 0
    for pattern, signal_id, weight in ANTI_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            anti_hits.append({"id": signal_id, "weight": weight})
            anti_score += weight

    # Strong anti-content without enough job evidence → reject
    force_anti = anti_score >= ANTI_FORCE_REJECT and score < (MIN_SCORE + 4)

    valid = (
        score >= MIN_SCORE
        and distinct >= MIN_DISTINCT_SIGNALS
        and not force_anti
        and len(raw) >= 30
    )

    # Extra gate: weak-only (email/url/company alone) must fail — already covered by MIN_SCORE
    # and requiring distinct signals from stronger categories when possible:
    strong_or_medium = [s for s in signals if s["weight"] >= 2]
    if valid and len(strong_or_medium) < 2:
        valid = False

    result = {
        "valid": valid,
        "score": score,
        "min_score": MIN_SCORE,
        "distinct_signals": distinct,
        "min_distinct_signals": MIN_DISTINCT_SIGNALS,
        "signals": [{"id": s["id"], "weight": s["weight"]} for s in signals],
        "anti_signals": anti_hits,
        "anti_score": anti_score,
        "message": REJECT_MESSAGE if not valid else "Content appears job/recruitment/resume related.",
        "user_message": USER_FACING_MESSAGE if not valid else "",
    }

    logger.info(
        "OCR content validation: valid=%s score=%s distinct=%s signals=%s anti_score=%s anti=%s",
        valid,
        score,
        distinct,
        [s["id"] for s in signals],
        anti_score,
        [a["id"] for a in anti_hits],
    )
    return result
