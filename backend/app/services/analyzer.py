"""Orchestrates full job posting analysis."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import AnalysisResult, DuplicateMatch, JobPosting
from app.services import company_verifier, duplicate, explain, ml_service, rules, scoring, url_analyzer


def run_analysis(
    db: Session,
    user_id: int,
    *,
    title: str,
    company_name: str,
    description: str,
    salary: str | None = None,
    email: str | None = None,
    url: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    source: str = "manual",
    extracted_ocr_text: str | None = None,
) -> dict[str, Any]:
    url_result = None
    if url:
        url_result = url_analyzer.analyze_url(url, company_name)
        if not url_result.get("valid"):
            # Still continue analysis but keep the url analysis result
            pass

    company_result = company_verifier.verify_company(
        db, company_name, email=email, website=url
    )

    ml = ml_service.predict(f"{title} {company_name} {description} {salary or ''}")

    red_flags, positives, bonus = rules.analyze_rules(
        title=title,
        company_name=company_name,
        description=description,
        salary=salary,
        email=email,
        url=url,
        job_type=job_type,
        url_risk_level=(url_result or {}).get("risk_level"),
        company_status=company_result.get("status"),
    )

    score = scoring.compute_trust_score(
        red_flags,
        bonus,
        ml.get("scam_probability"),
        ml.get("available", False),
        company_result=company_result,
        url_result=url_result,
        positive_indicators=positives,
        source=source,
        email=email,
    )

    explanation = explain.build_explanation(
        trust_score=score["trust_score"],
        risk_level=score["risk_level"],
        red_flags=red_flags,
        positive_indicators=positives,
        company_result=company_result,
        url_result=url_result,
        score_breakdown=score["score_breakdown"],
        top_terms=ml.get("top_terms"),
        ml_available=ml.get("available", False),
    )

    posting = JobPosting(
        user_id=user_id,
        title=title,
        company_name=company_name,
        description=description,
        salary=salary,
        email=email,
        url=url,
        location=location,
        job_type=job_type,
        source=source,
    )
    db.add(posting)
    db.flush()

    dup = duplicate.find_duplicates(
        db,
        f"{title} {company_name} {description}",
        exclude_job_posting_id=posting.id,
    )

    analysis = AnalysisResult(
        job_posting_id=posting.id,
        user_id=user_id,
        trust_score=score["trust_score"],
        risk_level=score["risk_level"],
        ml_scam_probability=ml.get("scam_probability"),
        rule_risk_points=score["rule_risk_points"],
        red_flags=json.dumps(red_flags),
        positive_indicators=json.dumps(positives),
        explanation=explanation,
        company_verification=json.dumps(company_result),
        url_analysis=json.dumps(url_result or {}),
        duplicate_result=json.dumps(dup),
        score_breakdown=json.dumps(score["score_breakdown"]),
        extracted_ocr_text=extracted_ocr_text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.flush()

    for m in dup.get("matches", []):
        db.add(
            DuplicateMatch(
                analysis_result_id=analysis.id,
                matched_source_type=m["source_type"],
                matched_id=m["matched_id"],
                similarity=m["similarity_percent"] / 100.0,
            )
        )
    db.commit()
    db.refresh(analysis)

    return serialize_analysis(analysis, posting, ml)


def serialize_analysis(
    analysis: AnalysisResult,
    posting: JobPosting | None = None,
    ml: dict | None = None,
) -> dict[str, Any]:
    if posting is None:
        posting = analysis.job_posting

    ml_prob = analysis.ml_scam_probability
    ml_block = ml or {
        "available": ml_prob is not None,
        "scam_probability": ml_prob,
        "top_terms": [],
    }

    return {
        "analysis_id": analysis.id,
        "id": analysis.id,
        "user_id": analysis.user_id,
        "job_posting_id": analysis.job_posting_id,
        "trust_score": analysis.trust_score,
        "risk_level": analysis.risk_level,
        "ml": {
            "available": bool(ml_block.get("available")),
            "scam_probability": ml_block.get("scam_probability"),
            "top_terms": ml_block.get("top_terms") or [],
        },
        "red_flags": json.loads(analysis.red_flags or "[]"),
        "positive_indicators": json.loads(analysis.positive_indicators or "[]"),
        "explanation": analysis.explanation,
        "score_breakdown": json.loads(analysis.score_breakdown or "{}"),
        "company_verification": json.loads(analysis.company_verification or "{}"),
        "url_analysis": json.loads(analysis.url_analysis or "{}"),
        "duplicate_result": json.loads(analysis.duplicate_result or "{}"),
        "extracted_ocr_text": analysis.extracted_ocr_text,
        "disclaimer": explain.DISCLAIMER,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "title": posting.title if posting else None,
        "company_name": posting.company_name if posting else None,
        "description": posting.description if posting else None,
        "salary": posting.salary if posting else None,
        "email": posting.email if posting else None,
        "url": posting.url if posting else None,
        "location": posting.location if posting else None,
        "job_type": posting.job_type if posting else None,
        "source": posting.source if posting else None,
    }
