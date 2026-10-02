"""Scam report endpoints."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Query, Request

from app.config import get_settings
from app.deps import AppError, CurrentUser, DbSession
from app.models import ScamReport
from app.schemas import ReportCreate
from app.services.duplicate import invalidate_cache

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _save_report(db, user, *, job_title, company_name, description, reason, url=None, screenshot_path=None):
    if len(job_title.strip()) < 2 or len(company_name.strip()) < 2:
        raise AppError("VALIDATION_ERROR", "Title and company are required", 400)
    if len(description.strip()) < 10:
        raise AppError("VALIDATION_ERROR", "Description must be at least 10 characters", 400)
    if len(reason.strip()) < 5:
        raise AppError("VALIDATION_ERROR", "Reason must be at least 5 characters", 400)

    report = ScamReport(
        user_id=user.id,
        job_title=job_title.strip(),
        company_name=company_name.strip(),
        description=description.strip(),
        url=(url or "").strip() or None,
        reason=reason.strip(),
        screenshot_path=screenshot_path,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    invalidate_cache()
    return {
        "report": {
            "id": report.id,
            "job_title": report.job_title,
            "company_name": report.company_name,
            "description": report.description,
            "url": report.url,
            "reason": report.reason,
            "screenshot_path": report.screenshot_path if report.user_id == user.id else None,
            "report_date": report.report_date.isoformat() if report.report_date else None,
            "status": report.status,
        }
    }


@router.post("", status_code=201)
async def create_report(request: Request, db: DbSession, user: CurrentUser):
    """Accept multipart/form-data or JSON body."""
    content_type = (request.headers.get("content-type") or "").lower()

    if "application/json" in content_type:
        raw = await request.json()
        try:
            body = ReportCreate.model_validate(raw)
        except Exception as exc:
            raise AppError("VALIDATION_ERROR", str(exc), 422) from exc
        return _save_report(
            db,
            user,
            job_title=body.job_title,
            company_name=body.company_name,
            description=body.description,
            reason=body.reason,
            url=body.url,
        )

    form = await request.form()
    job_title = str(form.get("job_title") or "")
    company_name = str(form.get("company_name") or "")
    description = str(form.get("description") or "")
    reason = str(form.get("reason") or "")
    url_val = form.get("url")
    url = str(url_val) if url_val else None
    screenshot = form.get("screenshot")

    screenshot_path = None
    if screenshot is not None and hasattr(screenshot, "filename") and screenshot.filename:
        settings = get_settings()
        raw_bytes = await screenshot.read()
        if len(raw_bytes) > settings.max_upload_bytes:
            raise AppError("FILE_TOO_LARGE", f"Screenshot exceeds {settings.MAX_UPLOAD_MB} MB", 413)
        ext = Path(screenshot.filename).suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise AppError("UNSUPPORTED_MEDIA", "Screenshot must be PNG/JPG/WEBP", 415)
        name = f"report_{uuid.uuid4().hex}{ext}"
        dest = Path(settings.UPLOAD_DIR) / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw_bytes)
        screenshot_path = name

    return _save_report(
        db,
        user,
        job_title=job_title,
        company_name=company_name,
        description=description,
        reason=reason,
        url=url,
        screenshot_path=screenshot_path,
    )


@router.get("")
def list_reports(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    q = db.query(ScamReport).order_by(ScamReport.report_date.desc())
    total = q.count()
    rows = q.offset((page - 1) * limit).limit(limit).all()
    items = []
    for r in rows:
        desc = r.description
        if len(desc) > 200:
            desc = desc[:200] + "…"
        items.append(
            {
                "id": r.id,
                "job_title": r.job_title,
                "company_name": r.company_name,
                "description": desc,
                "url": r.url,
                "reason": r.reason,
                "screenshot_available": bool(
                    r.screenshot_path and (r.user_id == user.id or user.role == "admin")
                ),
                "report_date": r.report_date.isoformat() if r.report_date else None,
                "status": r.status,
            }
        )
    return {"items": items, "total": total}


@router.patch("/{report_id}/reviewed")
def mark_reviewed(report_id: int, db: DbSession, user: CurrentUser):
    if user.role != "admin":
        raise AppError("FORBIDDEN", "Admin access required", 403)
    report = db.get(ScamReport, report_id)
    if not report:
        raise AppError("NOT_FOUND", "Report not found", 404)
    report.status = "reviewed"
    db.commit()
    return {"report": {"id": report.id, "status": report.status}}
