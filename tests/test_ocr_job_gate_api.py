"""Upload OCR sample images and print accept/reject outcomes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8000/api"
SAMPLES = ROOT / "tests" / "ocr_samples"

def test_ocr_job_gate_api():
    try:
        login = requests.post(
            f"{BASE}/auth/login",
            json={"email": "demo@jobshield.local", "password": "demo1234"},
            timeout=5,
        )
    except Exception:
        pytest.skip("Local test server at http://127.0.0.1:8000 is not running")

    if login.status_code != 200:
        pytest.skip("Login to local server failed, skipping live API OCR test")

    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    expect = {
        "A_codeforces.png": False,
        "B_shopping.png": False,
        "C_job.png": True,
        "D_recruiter.png": True,
        "E_resume.png": True,
    }

    failed = False
    for name, should_accept in expect.items():
        path = SAMPLES / name
        if not path.exists():
            continue
        with path.open("rb") as f:
            r = requests.post(
                f"{BASE}/ocr/analyze",
                headers=headers,
                files={"file": (name, f, "image/png")},
                timeout=120,
            )
        body = r.json()
        valid = body.get("valid")
        if valid is None and r.status_code == 200 and body.get("analysis"):
            valid = True
        if r.status_code == 422:
            valid = body.get("valid", False)

        ok = (valid is True) if should_accept else (valid is False and r.status_code == 422)
        if not ok:
            failed = True
    assert not failed, "OCR gate outcomes did not match expected"


if __name__ == "__main__":
    test_ocr_job_gate_api()
