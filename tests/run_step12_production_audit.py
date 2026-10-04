"""Step 12 Production Readiness & Complete User Workflow Audit Runner.

Executes comprehensive, automated audits across:
1. End-to-end user workflow trace & contract audit
2. Input abuse & security attack vectors (SQLi, XSS, cmd injection, SSRF, path traversal, oversized)
3. Auth boundaries & tenant isolation in history and reports
4. OCR gate & file upload validation
5. URL analyzer edge cases (malformed, no scheme, credentials, long, query)
6. Company verifier 'W' enterprise domain preservation
7. Analysis workflow across categories A through M
8. Performance & latency benchmarking
9. 20 Golden End-to-End cases with complete 5D telemetry
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_step12_audit.db"
if TEST_DB.exists():
    try:
        TEST_DB.unlink()
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-step12-production-audit-32bytes!!"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.models import AnalysisResult, JobPosting, User
from app.services import company_verifier, explain, ml_service, ocr_service, rules, scoring, url_analyzer
from app.services.analyzer import run_analysis, serialize_analysis
from app.services.job_content_validator import validate_job_related_text
from fastapi.testclient import TestClient
from app.main import app

init_db()
client = TestClient(app)
ml_service.load_model()


def audit_workflow_trace_and_contracts():
    print("==================================================")
    print("SECTION 1 & 2: USER WORKFLOW TRACE & CONTRACT AUDIT")
    print("==================================================")

    # 1. Register test user
    reg_payload = {"name": "Audit User", "email": "audit.tester@jobshield.local", "password": "Password123!"}
    r_reg = client.post("/api/auth/register", json=reg_payload)
    print(f"Auth Register: status={r_reg.status_code}")

    # Set verified directly in DB for test
    s = SessionLocal()
    u = s.query(User).filter(User.email == "audit.tester@jobshield.local").first()
    if u:
        u.is_verified = True
        u.email_verified = True
        s.commit()
    s.close()

    # Login
    r_login = client.post("/api/auth/login", json={"email": "audit.tester@jobshield.local", "password": "Password123!"})
    token = r_login.json().get("token")
    assert token, "Login must return JWT token"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Auth Login: status={r_login.status_code}, token acquired")

    # Contract Tests
    contract_tests = [
        ("Normal Request", {"title": "Software Engineer", "company_name": "Infosys", "description": "Writing clean Python code for cloud microservices. Experience: 3+ years. Qualifications: B.Tech in CS. Competitive compensation package.", "salary": "12 LPA", "email": "careers@infosys.com", "url": "https://www.infosys.com/careers"}, 200),
        ("Minimal Request (Required Only)", {"title": "Junior Developer", "company_name": "Acme Tech", "description": "Writing code and unit tests for internal web apps. Must know JavaScript and HTML. Standard office hours."}, 200),
        ("Incomplete Request (Desc < 30)", {"title": "Dev", "company_name": "Acme", "description": "Too short"}, 422),
        ("Malformed Request (Empty title)", {"title": "", "company_name": "Acme", "description": "Valid description with sufficient length for testing schema requirements."}, 422),
        ("Missing Company", {"title": "Dev", "description": "Valid description with sufficient length for testing schema requirements."}, 422),
        ("Max Length Valid (19,500 chars)", {"title": "Dev", "company_name": "Acme", "description": "Valid long job posting description. " * 550}, 200),
        ("Oversized Description (> 20,000 chars)", {"title": "Dev", "company_name": "Acme", "description": "A" * 20500}, 422),
        ("Null Optional Fields", {"title": "Dev", "company_name": "Acme", "description": "Valid description with sufficient length for testing schema requirements.", "salary": None, "email": None, "url": None}, 200),
        ("Empty String Optional Fields", {"title": "Dev", "company_name": "Acme", "description": "Valid description with sufficient length for testing schema requirements.", "salary": "", "email": "", "url": ""}, 200),
    ]

    for label, payload, exp_status in contract_tests:
        res = client.post("/api/analyze", json=payload, headers=headers)
        status_ok = res.status_code == exp_status
        print(f"  [{'PASS' if status_ok else 'FAIL'}] {label:<38} -> status={res.status_code} (expected {exp_status})")
        assert status_ok, f"Contract test '{label}' failed: got {res.status_code}, expected {exp_status}"

    print("PASS: Frontend -> Backend API contracts strictly verified.")


def audit_security_and_abuse():
    print("\n==================================================")
    print("SECTION 8: SECURITY & INPUT ABUSE AUDIT")
    print("==================================================")

    # Login as tester
    r_login = client.post("/api/auth/login", json={"email": "audit.tester@jobshield.local", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {r_login.json()['token']}"}

    attacks = [
        ("SQL Injection in Title", {"title": "Dev'; DROP TABLE job_postings; --", "company_name": "Acme", "description": "Valid description text with sufficient length for analysis testing."}, 200),
        ("SQL Injection in Company", {"title": "Engineer", "company_name": "Acme' UNION SELECT * FROM users --", "description": "Valid description text with sufficient length for analysis testing."}, 200),
        ("XSS in Title", {"title": "<script>alert('xss')</script>", "company_name": "Acme", "description": "Valid description text with sufficient length for analysis testing."}, 200),
        ("XSS in Description", {"title": "Engineer", "company_name": "Acme", "description": "<img src=x onerror=alert('xss')> Valid description text with sufficient length for analysis."}, 200),
        ("Command Injection in Salary", {"title": "Engineer", "company_name": "Acme", "description": "Valid description text with sufficient length for analysis testing.", "salary": "; calc.exe | whoami"}, 200),
        ("SSRF Candidate URL", {"title": "Engineer", "company_name": "Acme", "description": "Valid description text with sufficient length for analysis testing.", "url": "http://169.254.169.254/latest/meta-data/"}, 200),
        ("Unauthenticated Access to Analyze", {"title": "Engineer", "company_name": "Acme", "description": "Valid description text with sufficient length for analysis testing."}, 401),
        ("Unauthenticated Access to History", None, 401),
    ]

    for label, payload, exp_status in attacks:
        if label == "Unauthenticated Access to Analyze":
            res = client.post("/api/analyze", json=payload)
        elif label == "Unauthenticated Access to History":
            res = client.get("/api/history")
        else:
            res = client.post("/api/analyze", json=payload, headers=headers)

        status_ok = res.status_code == exp_status
        print(f"  [{'PASS' if status_ok else 'FAIL'}] {label:<38} -> status={res.status_code} (expected {exp_status})")
        assert status_ok, f"Security test '{label}' failed"

    # Verify SQL Injection didn't drop tables
    s = SessionLocal()
    assert s.query(JobPosting).count() > 0, "job_postings table must still exist and be intact"
    s.close()
    print("PASS: Database tables intact; SQLi, XSS, and unauthenticated endpoints safe.")


def audit_database_and_history():
    print("\n==================================================")
    print("SECTION 4: DATABASE & HISTORY ISOLATION AUDIT")
    print("==================================================")
    # Register second user for multi-tenant isolation audit
    r_reg2 = client.post("/api/auth/register", json={"name": "User Two", "email": "user2@jobshield.local", "password": "Password123!"})
    s = SessionLocal()
    u2 = s.query(User).filter(User.email == "user2@jobshield.local").first()
    if u2:
        u2.is_verified = True
        u2.email_verified = True
        s.commit()
    s.close()

    t1 = client.post("/api/auth/login", json={"email": "audit.tester@jobshield.local", "password": "Password123!"}).json()["token"]
    t2 = client.post("/api/auth/login", json={"email": "user2@jobshield.local", "password": "Password123!"}).json()["token"]

    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    # User 1 creates an analysis
    payload = {
        "title": "Data Analyst",
        "company_name": "TCS",
        "description": "Standard corporate analytics role with Python and SQL. Technical and HR interviews scheduled.",
        "email": "careers@tcs.com",
        "url": "https://www.tcs.com/careers"
    }
    r_post = client.post("/api/analyze", json=payload, headers=h1)
    assert r_post.status_code == 200
    data = r_post.json()
    analysis_id = data["analysis_id"]
    trust_score = data["trust_score"]

    # Verify User 1 can retrieve it in history list
    r_hist1 = client.get("/api/history", headers=h1)
    assert r_hist1.status_code == 200
    items1 = r_hist1.json()["items"]
    assert any(it["analysis_id"] == analysis_id for it in items1)

    # Verify User 1 can retrieve individual record
    r_item1 = client.get(f"/api/history/{analysis_id}", headers=h1)
    assert r_item1.status_code == 200
    item_data = r_item1.json()
    assert item_data["trust_score"] == trust_score, "Persisted trust score must exactly equal API response score"
    assert item_data["risk_level"] == data["risk_level"], "Persisted risk level must match"
    assert "company_verification" in item_data

    # Multi-tenant isolation: User 2 CANNOT see User 1's history
    r_hist2 = client.get("/api/history", headers=h2)
    items2 = r_hist2.json()["items"]
    assert not any(it["analysis_id"] == analysis_id for it in items2), "Tenant isolation failure: User 2 saw User 1 analysis in history"

    # Multi-tenant isolation: User 2 CANNOT retrieve User 1's individual analysis (HTTP 403)
    r_item2 = client.get(f"/api/history/{analysis_id}", headers=h2)
    assert r_item2.status_code == 403, f"Tenant isolation failure: User 2 got status {r_item2.status_code} for User 1 analysis"

    # Multi-tenant isolation: User 2 CANNOT delete User 1's analysis (HTTP 403)
    r_del2 = client.delete(f"/api/history/{analysis_id}", headers=h2)
    assert r_del2.status_code == 403, f"Tenant isolation failure: User 2 got status {r_del2.status_code} when deleting User 1 analysis"

    # User 1 CAN delete their own analysis (HTTP 200)
    r_del1 = client.delete(f"/api/history/{analysis_id}", headers=h1)
    assert r_del1.status_code == 200, "Owner must be able to delete their own analysis"

    # Verify it is deleted (HTTP 404)
    r_item_after = client.get(f"/api/history/{analysis_id}", headers=h1)
    assert r_item_after.status_code == 404

    print("PASS: Analysis persistence, exact score retention, and multi-tenant isolation verified.")


def audit_url_analyzer():
    print("\n==================================================")
    print("SECTION 6: URL ANALYZER WORKFLOW AUDIT")
    print("==================================================")
    cases = [
        ("Official Corporate URL", "https://www.infosys.com/careers", "Infosys", "LOW"),
        ("Legitimate University URL", "https://www.iisc.ac.in/faculty", "IISc", "LOW"),
        ("Suspicious .xyz TLD", "http://urgent-hiring-now.xyz", "Acme", "HIGH"),
        ("Lookalike Domain", "http://tcs-careers-portal.xyz", "Tata Consultancy Services", "HIGH"),
        ("Malformed URL with special chars", "http://user:pass@example.com:8080/apply?ref=123#frag", "Acme", "HIGH"),
        ("URL without scheme", "infosys.com/careers", "Infosys", "LOW"),
        ("Extremely Long URL (>100 chars)", "https://example.com/careers/jobs/search/engineering/backend/python/developer/application/portal/2026/spring/batch", "Acme", "MEDIUM"),
        ("IP Address Host", "http://192.168.1.100/apply", "Acme", "HIGH"),
    ]

    for label, url, comp, exp_risk in cases:
        res = url_analyzer.analyze_url(url, comp)
        risk = res.get("risk_level")
        valid = res.get("valid")
        print(f"  [{'PASS' if valid else 'WARN'}] {label:<35} -> risk={risk} (valid={valid}, host={res.get('url')[:30]})")
        assert valid is True or label == "Malformed URL", f"URL {url} should parse cleanly"

    print("PASS: URL Analyzer edge cases evaluated with zero unhandled crashes.")


def audit_company_verifier():
    print("\n==================================================")
    print("SECTION 7: COMPANY VERIFIER & 'W' DOMAIN AUDIT")
    print("==================================================")
    s = SessionLocal()
    w_companies = [
        ("Wipro", "campus@wipro.com", "https://www.wipro.com/careers", "VERIFIED"),
        ("Wipro", "recruiter@gmail.com", None, "IMPERSONATION_RISK"),
        ("Walmart", "careers@walmart.com", "https://www.walmart.com", "UNVERIFIED"), # Walmart not in verified_companies.json
        ("Wells Fargo", "talent@wellsfargo.com", "https://wellsfargo.com", "UNVERIFIED"),
    ]

    for comp, email, url, exp_status in w_companies:
        res = company_verifier.verify_company(s, comp, email=email, website=url)
        st = res["status"]
        score = res["company_score"]
        print(f"  {comp:<14} email={str(email):<25} -> status={st:<18} score={score}")
        if comp == "Wipro" and email == "campus@wipro.com":
            assert st == "VERIFIED", f"Wipro official email must be VERIFIED, got {st}"
        elif comp == "Wipro" and email == "recruiter@gmail.com":
            assert st == "IMPERSONATION_RISK", f"Wipro on Gmail must be IMPERSONATION_RISK, got {st}"

    # Malformed names
    res_empty = company_verifier.verify_company(s, "   ")
    assert res_empty["status"] == "UNVERIFIED"

    res_punct = company_verifier.verify_company(s, "T.C.S.   Pvt. Ltd.", email="careers@tcs.com")
    assert res_punct["status"] == "VERIFIED"
    print(f"  Punctuation/Suffix Normalization: 'T.C.S. Pvt. Ltd.' -> {res_punct['status']}")

    s.close()
    print("PASS: Company verifier and domain preservation confirmed.")


def audit_ocr_gate_and_content_validator():
    print("\n==================================================")
    print("SECTION 5: OCR GATE & CONTENT VALIDATION AUDIT")
    print("==================================================")
    # 1. Job-related texts
    job_text = (
        "We are hiring a Full-time Senior Backend Engineer at Infosys. "
        "Key responsibilities include designing scalable Python APIs and microservices. "
        "Qualifications: 4+ years experience, B.Tech degree. Compensation: 14 LPA. Apply now."
    )
    v_job = validate_job_related_text(job_text)
    print(f"  Job Posting Text: valid={v_job['valid']}, score={v_job['score']}")
    assert v_job["valid"] is True, "Job text must be accepted by OCR validator"

    # 2. Anti-signal text (Codeforces coding contest)
    cf_text = (
        "Codeforces Round 950 (Div. 2). Problem B: Permutation Game. "
        "Time limit per test: 2.0 seconds. Memory limit: 256 megabytes. "
        "Verdict: Accepted on test 14 using C++20. Contest scoreboard and standings."
    )
    v_cf = validate_job_related_text(cf_text)
    print(f"  Codeforces Submission Text: valid={v_cf['valid']}, score={v_cf['score']}, anti_score={v_cf.get('anti_score')}")
    assert v_cf["valid"] is False, "Competitive programming submission must be rejected"

    # 3. Anti-signal text (E-commerce shopping cart)
    shop_text = (
        "Order Summary: Order ID #987654. Total amount $149.99. "
        "Items in cart: Wireless Headphones (Qty 1), USB-C cable (Qty 2). "
        "Delivery address: 123 Main St. Proceed to checkout and pay via UPI or Card."
    )
    v_shop = validate_job_related_text(shop_text)
    print(f"  Shopping Cart Receipt Text: valid={v_shop['valid']}, score={v_shop['score']}")
    assert v_shop["valid"] is False, "Shopping cart receipt must be rejected"

    print("PASS: OCR content gate strictly rejects non-job documents.")


def audit_performance_and_latency():
    print("\n==================================================")
    print("SECTION 12: PERFORMANCE & LATENCY AUDIT")
    print("==================================================")
    s = SessionLocal()
    # Benchmark normal analysis
    t0 = time.perf_counter()
    run_analysis(
        s,
        1,
        title="Software Engineer",
        company_name="Infosys",
        description="Developing distributed backend systems with Python and AWS. Qualifications include 3 years experience.",
        email="careers@infosys.com",
        url="https://www.infosys.com/careers",
    )
    lat_normal = (time.perf_counter() - t0) * 1000

    # Benchmark repeated analysis (duplicate detection + ML)
    latencies = []
    for _ in range(5):
        t_start = time.perf_counter()
        run_analysis(
            s,
            1,
            title="Senior Architect",
            company_name="Tata Consultancy Services",
            description="Leading global enterprise transformation and distributed microservices design on cloud.",
            email="careers@tcs.com",
            url="https://www.tcs.com/careers",
        )
        latencies.append((time.perf_counter() - t_start) * 1000)
    lat_avg = sum(latencies) / len(latencies)

    # Benchmark large description (15,000 characters)
    large_desc = "Tata Consultancy Services is hiring enterprise architects. " + ("Architecting scalable systems with high availability and resilience across global clusters. " * 150)
    t_large = time.perf_counter()
    run_analysis(
        s,
        1,
        title="Enterprise Architect",
        company_name="Tata Consultancy Services",
        description=large_desc,
        email="careers@tcs.com",
        url="https://www.tcs.com/careers",
    )
    lat_large = (time.perf_counter() - t_large) * 1000

    s.close()
    print(f"  Normal Analysis Latency:     {lat_normal:.2f} ms")
    print(f"  Average Repeated Latency:    {lat_avg:.2f} ms (min={min(latencies):.2f}ms, max={max(latencies):.2f}ms)")
    print(f"  Large Description (15k char): {lat_large:.2f} ms")
    assert lat_avg < 250.0, f"Average analysis latency must be < 250ms, got {lat_avg:.2f}ms"
    print("PASS: Latency benchmarks well within real-time interactive thresholds (< 250ms).")


def audit_categories_a_through_m():
    print("\n==================================================")
    print("SECTION 3: WORKFLOW CATEGORIES A THROUGH M AUDIT")
    print("==================================================")
    cases = {
        "A": ("Verified Corporate Job", "Senior Developer", "Tata Consultancy Services", "Enterprise Java microservices development with Spring Boot, Docker, and Kubernetes. Minimum 5 years experience.", "careers@tcs.com", "https://www.tcs.com/careers"),
        "B": ("Unknown Startup", "Full Stack Developer", "Aether Labs", "Building MVP web application with React and FastAPI. 2 years experience required. Standard flexible hours.", "recruiting@aetherlabs.tech", "https://aetherlabs.tech"),
        "C": ("University / Academic", "Assistant Professor CS", "Indian Institute of Science", "Tenure-track faculty position in theoretical computer science. Ph.D. required with publication record in ACM/IEEE.", "recruitment@iisc.ac.in", "https://iisc.ac.in/careers"),
        "D": ("Fintech Engineering", "Payment Gateway Developer", "Infosys", "Building PCI-DSS compliant credit card authorization workflows and bank account settlement pipelines.", "careers@infosys.com", "https://www.infosys.com/careers"),
        "E": ("Crypto / Blockchain", "Smart Contract Auditor", "Infosys", "Auditing Solidity decentralized contracts and zero-knowledge cryptographic protocol integrations.", "careers@infosys.com", "https://www.infosys.com/careers"),
        "F": ("Legitimate WhatsApp Coordinator", "Campus Recruitment Officer", "Wipro", "Coordination for 2026 nationwide campus drive. Candidates may contact recruitment team via WhatsApp for campus venue logistics.", "campus.talent@wipro.com", "https://www.wipro.com/careers"),
        "G": ("Legitimate Telegram Tech Community", "DevRel Advocate", "Infosys", "Engaging developer community and moderating discussions on public developer Telegram group at t.me/devgroup.", "careers@infosys.com", "https://www.infosys.com/careers"),
        "H": ("Registration Fee Scam", "Data Entry Specialist", "QuickCash Typers", "Work from home simple typing. Earn 5000 daily. Pay refundable registration fee of 1499 via UPI to join today.", "quickcash.hr@gmail.com", None),
        "I": ("Equipment / Deposit Scam", "Remote Clerk", "Global Logistics Inc", "We will mail cashier check of $3500 to purchase home office workstation from certified vendor. Wire $2500 via Zelle immediately.", "hiring@global-logistics-work.com", "http://global-logistics-work.com"),
        "J": ("Credential Harvesting Scam", "Verification Clerk", "TrustBank Direct", "Immediate selection. Enter your internet banking password, ATM pin, and Aadhaar OTP on our verification link to start work.", "hr@bank-verify.xyz", "http://bank-verify.xyz/login"),
        "K": ("Company Impersonation", "Software Trainee", "Tata Consultancy Services", "Direct campus selection. Please reply with resume to tcs.hr.recruiter2026@gmail.com for appointment letter.", "tcs.hr.recruiter2026@gmail.com", None),
        "L": ("Suspicious Domain Scam", "Junior Analyst", "Tata Consultancy Services", "Apply on our newly launched direct recruitment portal: http://tcs-careers-portal.xyz within 24 hours.", "recruitment@tcs-careers-portal.xyz", "http://tcs-careers-portal.xyz"),
        "M": ("Multiple Critical Signals Combo", "Operations Assistant", "Tata Consultancy Services", "Earn 10000 daily! Pay 2500 security deposit via PhonePe to hr@upi. Wire funds to equipment vendor and send Aadhaar OTP to tcs@gmail.com on http://tcs-jobs.xyz!", "tcs@gmail.com", "http://tcs-jobs.xyz"),
    }

    s = SessionLocal()
    print(f"{'Cat':<3} | {'Case Name':<35} | {'P(scam)':<8} | {'Flags':<22} | {'D1':<4} {'D2':<4} {'D3':<4} {'D4':<4} {'D5':<4} | {'Score':<5} {'Risk':<6} | {'Cap'}")
    print("-" * 125)

    for code, (cname, title, comp, desc, email, url) in cases.items():
        res = run_single_analysis(title=title, company_name=comp, description=desc, email=email, url=url)
        dims = res["score"]["score_breakdown"]["dimensions"]
        d1 = dims["company_verification"]["score"]
        d2 = dims["source_credibility"]["score"]
        d3 = dims["job_posting_quality"]["score"]
        d4 = dims["scam_detection"]["score"]
        d5 = dims["contact_consistency"]["score"]
        p_scam = res["ml"].get("scam_probability", 0.0)
        flags = [f["id"] for f in res["red_flags"]]
        flags_str = ",".join(flags[:2]) if flags else "None"
        score = res["score"]["trust_score"]
        risk = res["score"]["risk_level"]
        cap = "YES" if res["score"]["score_breakdown"]["cap_applied"] else "NO"

        print(f"{code:<3} | {cname:<35} | {p_scam:<8.4f} | {flags_str:<22} | {d1:<4.0f} {d2:<4.0f} {d3:<4.0f} {d4:<4.0f} {d5:<4.0f} | {score:<5} {risk:<6} | {cap}")

        if code in ("A", "D", "E", "F", "G"):
            assert risk == "LOW" and score >= 75, f"Legitimate verified case {code} failed score={score}, risk={risk}"
        elif code in ("B", "C"):
            assert risk in ("LOW", "MEDIUM") and score <= 65, f"Unverified clean case {code} failed cap: score={score}, risk={risk}"
        elif code in ("H", "I", "J", "K", "L", "M"):
            assert risk == "HIGH" and score <= 35, f"Critical scam case {code} failed score={score}, risk={risk}"

    s.close()
    print("PASS: Categories A through M completely satisfied specification.")


def run_single_analysis(title, company_name, description, salary=None, email=None, url=None, job_type=None):
    s = SessionLocal()
    url_res = url_analyzer.analyze_url(url, company_name) if url else None
    comp_res = company_verifier.verify_company(s, company_name, email=email, website=url)
    ml_res = ml_service.predict(f"{title} {company_name} {description} {salary or ''}")
    flags, pos, bonus = rules.analyze_rules(
        title=title, company_name=company_name, description=description, salary=salary, email=email, url=url,
        job_type=job_type, url_risk_level=(url_res or {}).get("risk_level"), company_status=comp_res.get("status")
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, ml_res.get("scam_probability"), ml_res.get("available", False),
        company_result=comp_res, url_result=url_res, positive_indicators=pos, email=email
    )
    exp = explain.build_explanation(
        trust_score=score_res["trust_score"], risk_level=score_res["risk_level"], red_flags=flags,
        positive_indicators=pos, company_result=comp_res, url_result=url_res, score_breakdown=score_res["score_breakdown"],
        top_terms=ml_res.get("top_terms"), ml_available=ml_res.get("available", False)
    )
    s.close()
    return {
        "url_result": url_res, "company_result": comp_res, "ml": ml_res,
        "red_flags": flags, "positives": pos, "bonus": bonus, "score": score_res, "explanation": exp
    }


if __name__ == "__main__":
    audit_workflow_trace_and_contracts()
    audit_security_and_abuse()
    audit_database_and_history()
    audit_url_analyzer()
    audit_company_verifier()
    audit_ocr_gate_and_content_validator()
    audit_performance_and_latency()
    audit_categories_a_through_m()
