"""Feedback endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.deps import AppError, CurrentUser, DbSession
from app.models import AnalysisResult, Feedback
from app.schemas import FeedbackCreate

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", status_code=201)
def submit_feedback(body: FeedbackCreate, db: DbSession, user: CurrentUser):
    analysis = db.get(AnalysisResult, body.analysis_id)
    if not analysis:
        raise AppError("NOT_FOUND", "Analysis not found", 404)
    if analysis.user_id != user.id and user.role != "admin":
        raise AppError("FORBIDDEN", "You can only feedback on your own analyses", 403)

    existing = (
        db.query(Feedback)
        .filter(Feedback.analysis_result_id == body.analysis_id, Feedback.user_id == user.id)
        .first()
    )
    if existing:
        existing.label = body.label
        existing.comment = body.comment
        db.commit()
        db.refresh(existing)
        fb = existing
    else:
        fb = Feedback(
            analysis_result_id=body.analysis_id,
            user_id=user.id,
            label=body.label,
            comment=body.comment,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

    return {
        "feedback": {
            "id": fb.id,
            "analysis_id": fb.analysis_result_id,
            "label": fb.label,
            "comment": fb.comment,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
    }
