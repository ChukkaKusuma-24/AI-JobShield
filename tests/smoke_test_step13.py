"""Step 13 Application Smoke Test."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_smoke_step13.db"
if TEST_DB.exists():
    try:
        TEST_DB.unlink()
    except Exception:
        pass

os.environ["SECRET_KEY"] = "smoke-test-secret-key-jobshield-32bytes-min!!"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.models import AnalysisResult, JobPosting, User
from app.main import app
from fastapi.testclient import TestClient

init_db()
print("==================================================")
print("STEP 13: APPLICATION SMOKE TEST")
print("==================================================")

with TestClient(app) as client:
    # 1. Backend starts & API responds to health check
    r_health = client.get("/api/health")
    print(f"1. API Health Check: status={r_health.status_code}, data={r_health.json()}")
    assert r_health.status_code == 200
    assert r_health.json()["ml_available"] is True, "ML model must be available via lifespan"

# 2. Frontend dist build verification
dist_index = ROOT / "frontend" / "dist" / "index.html"
print(f"2. Frontend dist/index.html: exists={dist_index.exists()} (size={dist_index.stat().st_size} bytes)")
assert dist_index.exists() and dist_index.stat().st_size > 0

# 3. User registration & JWT auth
r_reg = client.post("/api/auth/register", json={"name": "Smoke User", "email": "smoke@jobshield.local", "password": "Password123!"})
assert r_reg.status_code == 201

s = SessionLocal()
u = s.query(User).filter(User.email == "smoke@jobshield.local").first()
assert u is not None
u.is_verified = True
u.email_verified = True
s.commit()
s.close()

r_login = client.post("/api/auth/login", json={"email": "smoke@jobshield.local", "password": "Password123!"})
assert r_login.status_code == 200
token = r_login.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"3. User Authentication: login status=200, JWT token acquired")

# 4. Legitimate analysis works
legit_payload = {
    "title": "Senior Systems Architect",
    "company_name": "Tata Consultancy Services",
    "description": "Designing scalable distributed cloud architectures and Java microservices. Minimum 8 years experience required.",
    "email": "careers@tcs.com",
    "url": "https://www.tcs.com/careers"
}
r_legit = client.post("/api/analyze", json=legit_payload, headers=headers)
assert r_legit.status_code == 200
legit_data = r_legit.json()
print(f"4. Legitimate Job Analysis: score={legit_data['trust_score']}, risk={legit_data['risk_level']}")
assert legit_data["trust_score"] >= 75
assert legit_data["risk_level"] == "LOW"

# 5. Obvious scam analysis works
scam_payload = {
    "title": "Work from Home Typist",
    "company_name": "Tata Consultancy Services",
    "description": "Direct joining without interview! Earn 5000 daily! Pay mandatory registration fee of 1500 via UPI to activate portal.",
    "email": "tcs.hr.recruitment@gmail.com",
    "url": "http://tcs-jobs-quick.xyz"
}
r_scam = client.post("/api/analyze", json=scam_payload, headers=headers)
assert r_scam.status_code == 200
scam_data = r_scam.json()
print(f"5. Obvious Scam Analysis: score={scam_data['trust_score']}, risk={scam_data['risk_level']}")
assert scam_data["trust_score"] <= 25
assert scam_data["risk_level"] == "HIGH"

# 6. History persistence works
r_hist = client.get(f"/api/history/{legit_data['analysis_id']}", headers=headers)
assert r_hist.status_code == 200
hist_data = r_hist.json()
print(f"6. History Persistence: retrieved_id={hist_data['analysis_id']}, score={hist_data['trust_score']}, risk={hist_data['risk_level']}")
assert hist_data["trust_score"] == legit_data["trust_score"]
assert hist_data["risk_level"] == legit_data["risk_level"]

print("\nPASS: ALL 6 SMOKE TEST CHECKS COMPLETED SUCCESSFULLY.")
