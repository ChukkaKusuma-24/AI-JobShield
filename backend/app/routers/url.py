"""URL analysis endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.deps import AppError, CurrentUser
from app.schemas import UrlAnalyzeRequest
from app.services.url_analyzer import analyze_url

router = APIRouter(prefix="/api/url", tags=["url"])


@router.post("/analyze")
def url_analyze(body: UrlAnalyzeRequest, user: CurrentUser):
    result = analyze_url(body.url, body.company_name)
    if not result.get("valid"):
        raise AppError("INVALID_URL", result.get("explanation") or "Invalid URL", 400, details=[result])
    return result
