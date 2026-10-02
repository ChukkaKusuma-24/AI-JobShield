"""OCR service using local Tesseract (Windows-aware)."""
from __future__ import annotations

import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

WINDOWS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]

INSTALL_INSTRUCTIONS = {
    "windows": (
        "1) Download & install Tesseract from "
        "https://github.com/UB-Mannheim/tesseract/wiki "
        "(default path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe). "
        "2) Set in project .env: "
        "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe "
        "3) Restart the backend."
    ),
    "macos": "brew install tesseract",
    "linux": "sudo apt-get install tesseract-ocr  (or equivalent for your distro)",
}


def resolve_tesseract_cmd() -> str | None:
    """Return a usable tesseract executable path, or None."""
    settings = get_settings()
    configured = (settings.TESSERACT_CMD or "").strip().strip('"')
    if configured:
        p = Path(configured)
        if p.is_file():
            return str(p)
        logger.warning("TESSERACT_CMD set but file not found: %s", configured)

    which = shutil.which("tesseract")
    if which:
        return which

    if os.name == "nt":
        for candidate in WINDOWS_CANDIDATES:
            if candidate and Path(candidate).is_file():
                return candidate
    return None


def configure_pytesseract() -> str | None:
    import pytesseract

    cmd = resolve_tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return cmd


def ocr_available() -> bool:
    try:
        import pytesseract
        from PIL import Image  # noqa: F401

        configure_pytesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception as exc:
        logger.info("OCR unavailable: %s", exc)
        return False


def extract_hints(text: str) -> dict[str, Any]:
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    urls = re.findall(r"https?://[^\s]+|www\.[^\s]+", text, flags=re.I)
    company = None
    for line in text.splitlines():
        m = re.search(r"company\s*[:\-]\s*(.+)", line, re.I)
        if m:
            company = m.group(1).strip()[:120]
            break
    title = None
    for line in text.splitlines():
        m = re.search(r"(?:job\s*title|position|role)\s*[:\-]\s*(.+)", line, re.I)
        if m:
            title = m.group(1).strip()[:120]
            break
    return {
        "emails": emails[:3],
        "urls": urls[:3],
        "company_name": company,
        "title": title,
    }


def _preprocess(img):
    """Grayscale, optional upscale, contrast-ish point transform, mild threshold."""
    processed = img.convert("L")
    w, h = processed.size
    # Upscale small screenshots for better OCR
    if max(w, h) < 1000:
        scale = 2
        processed = processed.resize((w * scale, h * scale))
    elif max(w, h) > 2200:
        ratio = 2200 / max(w, h)
        processed = processed.resize((int(w * ratio), int(h * ratio)))

    # Mild contrast stretch via point map, then threshold
    processed = processed.point(lambda x: min(255, max(0, int((x - 20) * 1.15))))
    processed = processed.point(lambda x: 0 if x < 150 else 255)
    return processed


def save_and_ocr(
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
) -> dict[str, Any]:
    settings = get_settings()
    if len(file_bytes) > settings.max_upload_bytes:
        raise ValueError(f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")

    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Only PNG, JPG, JPEG, WEBP images are allowed")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / safe_name

    from PIL import Image
    import io

    bio = io.BytesIO(file_bytes)
    img = Image.open(bio)
    img.verify()
    bio.seek(0)
    img = Image.open(bio)
    # Normalize mode for WEBP/RGBA
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    dest.write_bytes(file_bytes)

    cmd = configure_pytesseract()
    if not cmd or not ocr_available():
        return {
            "available": False,
            "filename": safe_name,
            "extracted_text": "",
            "confidence": None,
            "hints": {},
            "tesseract_cmd_tried": cmd or (settings.TESSERACT_CMD or None),
            "install_instructions": INSTALL_INSTRUCTIONS,
        }

    import pytesseract

    processed = _preprocess(img)

    try:
        text = pytesseract.image_to_string(processed)
        conf = None
        try:
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
            conf = round(sum(confs) / len(confs), 1) if confs else None
        except Exception:
            conf = None
    except Exception as exc:
        return {
            "available": False,
            "filename": safe_name,
            "extracted_text": "",
            "confidence": None,
            "hints": {},
            "error": str(exc),
            "tesseract_cmd_tried": cmd,
            "install_instructions": INSTALL_INSTRUCTIONS,
        }

    text = (text or "").strip()
    return {
        "available": True,
        "filename": safe_name,
        "extracted_text": text,
        "confidence": conf,
        "hints": extract_hints(text),
        "tesseract_cmd": cmd,
    }
