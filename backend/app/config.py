"""Application configuration from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directory layout:
# Path(__file__) is <root>/backend/app/config.py
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[2]


def _resolve_path(value: str) -> str:
    """Resolve relative filesystem paths against project root."""
    if not value:
        return value
    p = Path(value)
    if p.is_absolute():
        return str(p)
    return str((ROOT_DIR / p).resolve())


def _find_env_files() -> list[str]:
    """Find valid .env files across backend, root, and current working directory."""
    candidates = [
        BACKEND_DIR / ".env",
        ROOT_DIR / ".env",
        Path.cwd() / "backend" / ".env",
        Path.cwd() / ".env",
    ]
    seen: set[str] = set()
    found: list[str] = []
    for c in candidates:
        try:
            resolved = c.resolve()
            resolved_str = str(resolved)
            if resolved.is_file() and resolved_str not in seen:
                seen.add(resolved_str)
                found.append(resolved_str)
        except OSError:
            pass
    return found


ENV_FILES = _find_env_files()
PRIMARY_ENV_FILE = ENV_FILES[0] if ENV_FILES else str(BACKEND_DIR / ".env")

# Preload into os.environ with dotenv (respecting existing test overrides)
for _env_path in reversed(ENV_FILES):
    load_dotenv(dotenv_path=_env_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(reversed(ENV_FILES)) if ENV_FILES else str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = "dev-secret-change-me-ai-jobshield-local"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./database/jobshield.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    RULE_WEIGHT: float = 0.6
    ML_WEIGHT: float = 0.4

    UNREALISTIC_SALARY_INR: int = 80000
    UNREALISTIC_DAILY_INR: int = 2000
    MAX_UPLOAD_MB: int = 5

    ENABLE_ONLINE_LOOKUP: bool = False
    ONLINE_LOOKUP_TIMEOUT: int = 4

    TESSERACT_CMD: str = ""

    ML_MODEL_PATH: str = str(ROOT_DIR / "models" / "jobshield_model.joblib")
    EXPECTED_MODEL_SHA256: str = "636e26e42b5a4179a42f9e9161dd7692d4f63146f1475659021605b9676bf1a2"
    VERIFY_MODEL_INTEGRITY: bool = True
    ML_ALTERNATIVE: str = "logistic"
    DEMO_DATA_PATH: str = str(ROOT_DIR / "data" / "demo_training_data.csv")

    UPLOAD_DIR: str = str(ROOT_DIR / "uploads")
    DATA_DIR: str = str(ROOT_DIR / "data")
    MODELS_DIR: str = str(ROOT_DIR / "models")

    # Email / OTP verification (configure in .env — never hard-code secrets)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "AI JobShield <noreply@jobshield.local>"
    SMTP_USE_TLS: bool = True
    # When true and SMTP is unset, OTP is logged for automated tests only (not for Gmail).
    SMTP_CONSOLE_FALLBACK: bool = False
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SEC: int = 60

    @property
    def jwt_secret(self) -> str:
        secret = (self.JWT_SECRET or "").strip()
        if secret:
            return secret
        return self.SECRET_KEY.strip()

    @property
    def smtp_user(self) -> str:
        user = (self.SMTP_USER or "").strip()
        if user:
            return user
        return (self.SMTP_USERNAME or "").strip()

    @model_validator(mode="after")
    def clean_and_sync_smtp(self) -> "Settings":
        # Clean quotes and whitespace
        if self.SMTP_HOST:
            self.SMTP_HOST = self.SMTP_HOST.strip().strip("'\"")
        if self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USER.strip().strip("'\"")
        if self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USERNAME.strip().strip("'\"")
        if self.SMTP_PASSWORD:
            self.SMTP_PASSWORD = self.SMTP_PASSWORD.strip().strip("'\"")
        if self.SMTP_FROM:
            self.SMTP_FROM = self.SMTP_FROM.strip().strip("'\"")

        # Synchronize SMTP_USER and SMTP_USERNAME
        if self.SMTP_USER and not self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USER
        elif self.SMTP_USERNAME and not self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USERNAME

        # Normalize SMTP_FROM
        effective_user = self.SMTP_USER or self.SMTP_USERNAME
        if effective_user:
            placeholders = ("replace_with", "your.address@", "noreply@jobshield.local", "example.com")
            if not self.SMTP_FROM or any(p in self.SMTP_FROM.lower() for p in placeholders):
                self.SMTP_FROM = f"AI JobShield <{effective_user}>"

        return self

    @model_validator(mode="after")
    def resolve_relative_paths(self) -> "Settings":
        # SQLite URLs like sqlite:///./database/jobshield.db
        if self.DATABASE_URL.startswith("sqlite:///"):
            raw = self.DATABASE_URL[len("sqlite:///") :]
            if raw and not Path(raw).is_absolute():
                self.DATABASE_URL = f"sqlite:///{(ROOT_DIR / raw).resolve().as_posix()}"

        self.ML_MODEL_PATH = _resolve_path(self.ML_MODEL_PATH)
        self.DEMO_DATA_PATH = _resolve_path(self.DEMO_DATA_PATH)
        self.UPLOAD_DIR = _resolve_path(self.UPLOAD_DIR)
        self.DATA_DIR = _resolve_path(self.DATA_DIR)
        self.MODELS_DIR = _resolve_path(self.MODELS_DIR)
        return self

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    """Clear cached settings and reload."""
    get_settings.cache_clear()
    return get_settings()
