"""Job analysis endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas import AnalyzeRequest
from app.services.analyzer import run_analysis

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze")
def analyze(body: AnalyzeRequest, db: DbSession, user: CurrentUser):
    return run_analysis(
        db,
        user.id,
        title=body.title,
        company_name=body.company_name,
        description=body.description,
        salary=body.salary,
        email=body.email,
        url=body.url,
        location=body.location,
        job_type=body.job_type,
        source="manual",
    )
