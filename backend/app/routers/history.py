"""Analysis history endpoints."""
from __future__ import annotations

import json
from fastapi import APIRouter, Query

from app.deps import AppError, CurrentUser, DbSession
from app.models import AnalysisResult, JobPosting
from app.services.analyzer import serialize_analysis

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def list_history(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    risk_level: str | None = Query(None),
):
    q = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user.id)
        .order_by(AnalysisResult.created_at.desc())
    )
    if risk_level:
        q = q.filter(AnalysisResult.risk_level == risk_level.upper())
    total = q.count()
    rows = q.offset((page - 1) * limit).limit(limit).all()
    items = []
    for a in rows:
        posting = a.job_posting or db.get(JobPosting, a.job_posting_id)
        items.append(
            {
                "analysis_id": a.id,
                "id": a.id,
                "user_id": a.user_id,
                "job_posting_id": a.job_posting_id,
                "title": posting.title if posting else None,
                "company_name": posting.company_name if posting else None,
                "description": posting.description if posting else None,
                "salary": posting.salary if posting else None,
                "email": posting.email if posting else None,
                "url": posting.url if posting else None,
                "source": posting.source if posting else None,
                "extracted_ocr_text": a.extracted_ocr_text,
                "trust_score": a.trust_score,
                "risk_level": a.risk_level,
                "red_flags": json.loads(a.red_flags or "[]"),
                "positive_indicators": json.loads(a.positive_indicators or "[]"),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )
    return {"items": items, "total": total}


@router.get("/{analysis_id}")
def get_history_item(analysis_id: int, db: DbSession, user: CurrentUser):
    analysis = db.get(AnalysisResult, analysis_id)
    if not analysis:
        raise AppError("NOT_FOUND", "Analysis not found", 404)
    if analysis.user_id != user.id and user.role != "admin":
        raise AppError("FORBIDDEN", "Not allowed to view this analysis", 403)
    return serialize_analysis(analysis)


@router.delete("/{analysis_id}")
def delete_history_item(analysis_id: int, db: DbSession, user: CurrentUser):
    analysis = db.get(AnalysisResult, analysis_id)
    if not analysis:
        raise AppError("NOT_FOUND", "Analysis not found", 404)
    if analysis.user_id != user.id and user.role != "admin":
        raise AppError("FORBIDDEN", "Not allowed to delete this analysis", 403)

    if analysis.ocr_result:
        analysis.ocr_result.analysis_result_id = None

    posting = analysis.job_posting
    db.delete(analysis)
    if posting:
        db.delete(posting)
    db.commit()
    return {"status": "ok", "message": "Analysis deleted successfully", "analysis_id": analysis_id}
