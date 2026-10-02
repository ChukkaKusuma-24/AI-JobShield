"""SQLAlchemy engine and session setup."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

logger = logging.getLogger("jobshield")
settings = get_settings()

# Engine configuration
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
if is_sqlite:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # MySQL / other production RDBMS
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


@event.listens_for(engine, "connect")
def configure_connection(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_schema_compatibility() -> None:
    """Ensure is_verified, updated_at, extracted_ocr_text, and performance indexes exist."""
    try:
        with engine.begin() as conn:
            if settings.DATABASE_URL.startswith("sqlite"):
                # Users table migrations
                rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                if rows:
                    existing = {row[1] for row in rows}
                    alterations = [
                        ("is_verified", "ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 1"),
                        ("updated_at", "ALTER TABLE users ADD COLUMN updated_at DATETIME"),
                    ]
                    for col, ddl in alterations:
                        if col not in existing:
                            conn.execute(text(ddl))
                            logger.info("Migrated SQLite users.%s", col)

                # Analysis results table migrations
                ar_rows = conn.execute(text("PRAGMA table_info(analysis_results)")).fetchall()
                if ar_rows:
                    ar_existing = {row[1] for row in ar_rows}
                    if "extracted_ocr_text" not in ar_existing:
                        conn.execute(text("ALTER TABLE analysis_results ADD COLUMN extracted_ocr_text TEXT"))
                        logger.info("Migrated SQLite analysis_results.extracted_ocr_text")
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_results_user_id ON analysis_results (user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analysis_results_created_at ON analysis_results (created_at)"))

            elif "mysql" in settings.DATABASE_URL:
                # Check columns in users table
                rows = conn.execute(
                    text(
                        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'"
                    )
                ).fetchall()
                if rows:
                    existing = {row[0] for row in rows}
                    if "is_verified" not in existing:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_verified TINYINT(1) NOT NULL DEFAULT 0"))
                        logger.info("Migrated MySQL users.is_verified")
                    if "updated_at" not in existing:
                        conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME NULL"))
                        logger.info("Migrated MySQL users.updated_at")

                # Check columns in analysis_results table
                ar_rows = conn.execute(
                    text(
                        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'analysis_results'"
                    )
                ).fetchall()
                if ar_rows:
                    ar_existing = {row[0] for row in ar_rows}
                    if "extracted_ocr_text" not in ar_existing:
                        conn.execute(text("ALTER TABLE analysis_results ADD COLUMN extracted_ocr_text TEXT NULL"))
                        logger.info("Migrated MySQL analysis_results.extracted_ocr_text")

                # Ensure indexes exist on analysis_results
                try:
                    idx_rows = conn.execute(
                        text(
                            "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS "
                            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'analysis_results'"
                        )
                    ).fetchall()
                    indexes = {row[0] for row in idx_rows}
                    if "ix_analysis_results_user_id" not in indexes:
                        conn.execute(text("CREATE INDEX ix_analysis_results_user_id ON analysis_results (user_id)"))
                    if "ix_analysis_results_created_at" not in indexes:
                        conn.execute(text("CREATE INDEX ix_analysis_results_created_at ON analysis_results (created_at)"))
                except Exception as idx_err:
                    logger.debug("MySQL index verification notice: %s", idx_err)

    except Exception as exc:
        logger.warning("Schema compatibility check notice: %s", exc)


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_schema_compatibility()
