"""AI JobShield FastAPI application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.database import init_db
from app.deps import AppError
from app.routers import (
    analyze,
    auth,
    company,
    dashboard,
    feedback,
    history,
    ocr,
    reports,
    url,
)
from app.services import ml_service, ocr_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jobshield")

settings = get_settings()
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ok = ml_service.load_model()
    logger.info("ML available: %s | OCR available: %s", ok, ocr_service.ocr_available())
    from app.config import ENV_FILES, get_settings
    from app.services.email_service import smtp_configured, smtp_status

    current_settings = get_settings()
    env_paths = ", ".join(ENV_FILES) if ENV_FILES else "none"
    logger.info(
        "SMTP Diagnostics: .env path(s)=[%s] | SMTP_HOST loaded: %s | SMTP_USER loaded: %s | SMTP_PASSWORD loaded: %s",
        env_paths,
        "yes" if bool(current_settings.SMTP_HOST) else "no",
        "yes" if bool(current_settings.smtp_user) else "no",
        "yes" if bool(current_settings.SMTP_PASSWORD) else "no",
    )

    if smtp_configured():
        logger.info(
            "Email OTP: SMTP configured successfully (Host: %s:%s, User: %s, From: %s)",
            current_settings.SMTP_HOST,
            current_settings.SMTP_PORT,
            current_settings.smtp_user,
            current_settings.SMTP_FROM,
        )
    else:
        logger.warning(
            "Email OTP: SMTP is not configured in .env. Real email delivery will be inactive until SMTP_HOST, SMTP_USER, and SMTP_PASSWORD are provided."
        )
    yield


app = FastAPI(
    title="AI JobShield API",
    description="Local Intelligent Fake Job & Internship Detection System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every API request so auth/email flows are visible in the terminal."""
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


def error_body(code: str, message: str, details=None):
    return {"error": {"code": code, "message": message, "details": details or []}}


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.details),
    )


def _jsonable_errors(errors: list) -> list:
    """Make pydantic/fastapi error dicts JSON-serializable."""
    out = []
    for err in errors:
        item = {}
        for k, v in err.items():
            if isinstance(v, BaseException):
                item[k] = str(v)
            elif isinstance(v, dict):
                item[k] = {
                    kk: (str(vv) if isinstance(vv, BaseException) else vv) for kk, vv in v.items()
                }
            else:
                item[k] = v
        out.append(item)
    return out


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_body(
            "VALIDATION_ERROR", "Invalid request", details=_jsonable_errors(exc.errors())
        ),
    )


@app.exception_handler(ValidationError)
async def pydantic_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=error_body(
            "VALIDATION_ERROR", "Invalid data", details=_jsonable_errors(exc.errors())
        ),
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "An unexpected error occurred"),
    )


@app.get("/api/health")
def health():
    from app.services.email_service import smtp_status

    return {
        "status": "ok",
        "ml_available": ml_service.is_available(),
        "ocr_available": ocr_service.ocr_available(),
        "online_lookup_enabled": settings.ENABLE_ONLINE_LOOKUP,
        "email": smtp_status(),
    }


app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(ocr.router)
app.include_router(url.router)
app.include_router(company.router)
app.include_router(reports.router)
app.include_router(feedback.router)
app.include_router(history.router)
app.include_router(dashboard.router)
