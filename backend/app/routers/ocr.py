"""OCR analyze endpoint."""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.deps import AppError, CurrentUser, DbSession
from app.models import OcrResult
from app.services import ocr_service
from app.services.analyzer import run_analysis
from app.services.job_content_validator import USER_FACING_MESSAGE, validate_job_related_text

logger = logging.getLogger("jobshield.ocr")

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/analyze")
async def ocr_analyze(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    company_name: str | None = Form(None),
    email: str | None = Form(None),
    url: str | None = Form(None),
    title: str | None = Form(None),
    text_override: str | None = Form(None),
):
    raw = await file.read()
    try:
        result = ocr_service.save_and_ocr(raw, file.filename or "upload.png", file.content_type)
    except ValueError as exc:
        msg = str(exc)
        code = "VALIDATION_ERROR"
        status = 400
        if "MB" in msg:
            code, status = "FILE_TOO_LARGE", 413
        elif "Only PNG" in msg:
            code, status = "UNSUPPORTED_MEDIA", 415
        raise AppError(code, msg, status)

    if not result.get("available"):
        raise AppError(
            "OCR_UNAVAILABLE",
            "Tesseract OCR is not available on this machine. Install Tesseract and set TESSERACT_CMD, then restart the backend.",
            503,
            details=[result.get("install_instructions", ocr_service.INSTALL_INSTRUCTIONS)],
        )

    ocr_text = (result.get("extracted_text") or "").strip()
    logger.info(
        "OCR completed filename=%s chars=%s confidence=%s",
        result.get("filename"),
        len(ocr_text),
        result.get("confidence"),
    )

    text = (text_override or ocr_text).strip()
    if len(text) < 30:
        raise AppError(
            "OCR_TEXT_TOO_SHORT",
            "Extracted text is empty or too short. Try a clearer image or paste the text manually on the Analyze page.",
            400,
            details=[{"valid": False, "extracted_text": text}],
        )

    # Validate job/recruitment/resume relevance BEFORE analysis pipeline
    validation = validate_job_related_text(text)
    logger.info(
        "OCR validation score=%s valid=%s signals=%s",
        validation["score"],
        validation["valid"],
        [s["id"] for s in validation["signals"]],
    )

    if not validation["valid"]:
        logger.info("OCR rejected: not job-related")
        return JSONResponse(
            status_code=422,
            content={
                "valid": False,
                "message": validation["message"],
                "extracted_text": text,
                "score": validation["score"],
                "signals": validation["signals"],
                "anti_signals": validation["anti_signals"],
                "error": {
                    "code": "NOT_JOB_RELATED",
                    "message": USER_FACING_MESSAGE,
                    "details": [
                        {
                            "valid": False,
                            "extracted_text": text,
                            "score": validation["score"],
                            "signals": validation["signals"],
                            "anti_signals": validation["anti_signals"],
                        }
                    ],
                },
            },
        )

    hints = result.get("hints") or {}
    final_title = title or hints.get("title") or "OCR Job Posting"
    final_company = company_name or hints.get("company_name") or "Unknown Company"
    final_email = email or (hints.get("emails") or [None])[0]
    final_url = url or (hints.get("urls") or [None])[0]

    analysis = run_analysis(
        db,
        user.id,
        title=final_title,
        company_name=final_company,
        description=text,
        email=final_email,
        url=final_url,
        source="ocr",
        extracted_ocr_text=text,
    )

    ocr_row = OcrResult(
        user_id=user.id,
        image_filename=result["filename"],
        extracted_text=text,
        ocr_available=True,
        confidence=result.get("confidence"),
        analysis_result_id=analysis["analysis_id"],
    )
    db.add(ocr_row)
    db.commit()
    db.refresh(ocr_row)

    logger.info("OCR accepted and analysis saved analysis_id=%s", analysis["analysis_id"])

    return {
        "valid": True,
        "extracted_text": text,
        "validation": {
            "score": validation["score"],
            "signals": validation["signals"],
        },
        "ocr": {
            "ocr_id": ocr_row.id,
            "extracted_text": text,
            "hints": hints,
            "confidence": result.get("confidence"),
        },
        "analysis": analysis,
    }


@router.get("/my-uploads")
def list_my_ocr_uploads(db: DbSession, user: CurrentUser):
    """Retrieve resume / document uploads belonging strictly to the logged-in user."""
    rows = (
        db.query(OcrResult)
        .filter(OcrResult.user_id == user.id)
        .order_by(OcrResult.created_at.desc())
        .limit(30)
        .all()
    )
    return {
        "uploads": [
            {
                "id": r.id,
                "filename": r.image_filename,
                "confidence": r.confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "analysis_id": r.analysis_result_id,
            }
            for r in rows
        ]
    }
