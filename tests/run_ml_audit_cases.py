"""Run ML evaluation on the 15 benchmark cases independently from rules."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "ml"))

TEST_DB = ROOT / "database" / "test_ml_audit.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "ml-audit-secret-key"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, ml_service, rules, scoring, url_analyzer
import tests.run_benchmark_step4 as bench

init_db()
ml_service.load_model()
db = SessionLocal()

cases = bench.BENCHMARK_CASES

print(f"{'ID':<3} | {'Case Name':<31} | {'P(scam)':<8} | {'P(legit)':<8} | {'ML Pred':<7} | {'ML Score':<8} | {'Rule D4':<8} | {'D4 (Blend)':<10} | {'Trust Score':<11}")
print("-" * 115)

results = []

for c in cases:
    text = f"{c['title']} {c['company_name']} {c['description']} {c['salary'] or ''}"
    pred_res = ml_service.predict(text)
    p_scam = pred_res["scam_probability"]
    p_legit = round(1.0 - p_scam, 4) if p_scam is not None else None
    ml_pred = 1 if p_scam >= 0.5 else 0
    ml_dim_score = round(100.0 - (p_scam * 100.0), 2)

    comp_res = company_verifier.verify_company(db, c["company_name"], email=c["email"], website=c["url"])
    url_res = url_analyzer.analyze_url(c["url"], c["company_name"]) if c["url"] else None
    flags, positives, bonus = rules.analyze_rules(
        title=c["title"],
        company_name=c["company_name"],
        description=c["description"],
        salary=c["salary"],
        email=c["email"],
        url=c["url"],
        url_risk_level=(url_res or {}).get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        p_scam,
        True,
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=c["email"],
    )
    d4_blend = score_res["score_breakdown"]["dimensions"]["scam_detection"]["score"]

    raw_pts = sum(f.get("points", 0) for f in flags)
    has_pos_legit = (
        comp_res.get("status") == "VERIFIED"
        or any(p.get("id") == "official_email" for p in positives)
        or (
            url_res
            and url_res.get("risk_level") == "LOW"
            and not any(i.get("id") in ("company_mismatch", "lookalike_domain") for i in url_res.get("indicators", []))
            and comp_res.get("status") in ("VERIFIED", "PARTIALLY VERIFIED")
        )
    )
    scam_base = 100.0 if has_pos_legit else 80.0
    rule_d4 = max(0.0, scam_base - raw_pts)

    print(f"{c['id']:<3} | {c['name']:<31} | {p_scam:<8.4f} | {p_legit:<8.4f} | {ml_pred:<7} | {ml_dim_score:<8.2f} | {rule_d4:<8.1f} | {d4_blend:<10.2f} | {score_res['trust_score']:<11}")
    results.append({
        "id": c["id"],
        "name": c["name"],
        "p_scam": p_scam,
        "p_legit": p_legit,
        "ml_pred": ml_pred,
        "ml_score": ml_dim_score,
        "rule_d4": rule_d4,
        "d4_blend": d4_blend,
        "trust_score": score_res["trust_score"],
        "top_terms": pred_res.get("top_terms", []),
    })

db.close()
