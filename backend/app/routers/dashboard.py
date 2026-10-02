"""Dashboard stats endpoint."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func

from app.deps import CurrentUser, DbSession
from app.models import AnalysisResult, Company, JobPosting, ScamReport

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: DbSession, user: CurrentUser):
    # Global-ish stats for demo (scoped lightly); analyses filtered to current user for privacy on recent
    total_analyses = db.query(AnalysisResult).filter(AnalysisResult.user_id == user.id).count()
    high = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user.id, AnalysisResult.risk_level == "HIGH")
        .count()
    )
    medium = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user.id, AnalysisResult.risk_level == "MEDIUM")
        .count()
    )
    low = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user.id, AnalysisResult.risk_level == "LOW")
        .count()
    )
    total_reports = db.query(ScamReport).count()
    companies_checked = db.query(Company).count()

    recent = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user.id)
        .order_by(AnalysisResult.created_at.desc())
        .limit(8)
        .all()
    )
    recent_analyses = []
    for a in recent:
        posting = a.job_posting
        recent_analyses.append(
            {
                "analysis_id": a.id,
                "title": posting.title if posting else None,
                "company_name": posting.company_name if posting else None,
                "trust_score": a.trust_score,
                "risk_level": a.risk_level,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )

    risk_distribution = [
        {"name": "HIGH", "value": high},
        {"name": "MEDIUM", "value": medium},
        {"name": "LOW", "value": low},
    ]

    # Analyses per day (last 14 days)
    since = datetime.now(timezone.utc) - timedelta(days=13)
    rows = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user.id, AnalysisResult.created_at >= since)
        .all()
    )
    by_day: dict[str, int] = defaultdict(int)
    for a in rows:
        if a.created_at:
            day = a.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
            by_day[day] += 1
    analyses_per_day = []
    for i in range(14):
        d = (since + timedelta(days=i)).strftime("%Y-%m-%d")
        analyses_per_day.append({"date": d, "count": by_day.get(d, 0)})

    return {
        "total_analyses": total_analyses,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "total_reports": total_reports,
        "companies_checked": companies_checked,
        "recent_analyses": recent_analyses,
        "risk_distribution": risk_distribution,
        "analyses_per_day": analyses_per_day,
    }
