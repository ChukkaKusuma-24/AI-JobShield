"""Duplicate detection via TF-IDF + cosine similarity."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models import JobPosting, ScamReport

_cache: dict[str, Any] = {"version": 0, "vectorizer": None, "matrix": None, "meta": []}


def _corpus_version(db: Session) -> int:
    jp = db.query(JobPosting).count()
    sr = db.query(ScamReport).count()
    return jp + sr * 1000


def _refresh(db: Session) -> None:
    docs: list[str] = []
    meta: list[dict] = []

    for jp in db.query(JobPosting).order_by(JobPosting.id.desc()).limit(500).all():
        docs.append(f"{jp.title} {jp.company_name} {jp.description}")
        meta.append(
            {
                "source_type": "job_posting",
                "matched_id": jp.id,
                "title": jp.title,
                "company": jp.company_name,
                "snippet": jp.description[:160],
                "date": jp.created_at.isoformat() if jp.created_at else None,
            }
        )

    for sr in db.query(ScamReport).order_by(ScamReport.id.desc()).limit(500).all():
        docs.append(f"{sr.job_title} {sr.company_name} {sr.description}")
        meta.append(
            {
                "source_type": "scam_report",
                "matched_id": sr.id,
                "title": sr.job_title,
                "company": sr.company_name,
                "snippet": sr.description[:160],
                "date": sr.report_date.isoformat() if sr.report_date else None,
            }
        )

    if not docs:
        _cache.update({"version": _corpus_version(db), "vectorizer": None, "matrix": None, "meta": []})
        return

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")
    matrix = vectorizer.fit_transform(docs)
    _cache.update(
        {
            "version": _corpus_version(db),
            "vectorizer": vectorizer,
            "matrix": matrix,
            "meta": meta,
        }
    )


def find_duplicates(
    db: Session,
    text: str,
    *,
    exclude_job_posting_id: int | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    version = _corpus_version(db)
    if _cache["vectorizer"] is None or _cache["version"] != version:
        _refresh(db)

    if _cache["vectorizer"] is None or _cache["matrix"] is None or not text.strip():
        return {"is_duplicate": False, "matches": []}

    vec = _cache["vectorizer"].transform([text])
    sims = cosine_similarity(vec, _cache["matrix"]).flatten()
    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)

    matches: list[dict] = []
    for idx, sim in ranked:
        if sim < 0.75:
            break
        meta = _cache["meta"][idx]
        if (
            exclude_job_posting_id
            and meta["source_type"] == "job_posting"
            and meta["matched_id"] == exclude_job_posting_id
        ):
            continue
        label = (
            "Near-identical to previous posting"
            if sim >= 0.90
            else "Possible duplicate detected"
        )
        matches.append(
            {
                "similarity_percent": round(float(sim) * 100, 1),
                "source_type": meta["source_type"],
                "matched_id": meta["matched_id"],
                "title": meta["title"],
                "company": meta["company"],
                "snippet": meta["snippet"],
                "date": meta["date"],
                "label": label,
            }
        )
        if len(matches) >= top_k:
            break

    return {"is_duplicate": len(matches) > 0, "matches": matches}


def invalidate_cache() -> None:
    _cache["version"] = -1
