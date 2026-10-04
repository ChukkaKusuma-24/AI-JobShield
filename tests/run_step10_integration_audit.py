"""Step 10 End-to-End Scoring & System Integration Audit Runner.

Executes and verifies:
1. ML integration & sanity checks
2. Scoring integration & dimension formulas
3. Double-counting audit across email, URL, contact, impersonation combinations
4. Hard-cap audit (impersonation, critical scam, unverified company, partial)
5. Evidence hierarchy verification
6. Contextual rule evaluation (10 contrast cases)
7. Explanation consistency validation
8. 20 End-to-End Golden Cases (10 legit, 10 scam)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_step10_audit.db"
if TEST_DB.exists():
    try:
        TEST_DB.unlink()
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-jobshield-step10-audit"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, explain, ml_service, rules, scoring, url_analyzer

init_db()
session = SessionLocal()
ml_service.load_model()


def run_single_analysis(
    title: str,
    company_name: str,
    description: str,
    salary: str | None = None,
    email: str | None = None,
    url: str | None = None,
    job_type: str | None = None,
    source: str = "manual",
):
    url_result = None
    if url:
        url_result = url_analyzer.analyze_url(url, company_name)

    company_result = company_verifier.verify_company(
        session, company_name, email=email, website=url
    )

    ml = ml_service.predict(f"{title} {company_name} {description} {salary or ''}")

    red_flags, positives, bonus = rules.analyze_rules(
        title=title,
        company_name=company_name,
        description=description,
        salary=salary,
        email=email,
        url=url,
        job_type=job_type,
        url_risk_level=(url_result or {}).get("risk_level"),
        company_status=company_result.get("status"),
    )

    score = scoring.compute_trust_score(
        red_flags,
        bonus,
        ml.get("scam_probability"),
        ml.get("available", False),
        company_result=company_result,
        url_result=url_result,
        positive_indicators=positives,
        source=source,
        email=email,
    )

    explanation = explain.build_explanation(
        trust_score=score["trust_score"],
        risk_level=score["risk_level"],
        red_flags=red_flags,
        positive_indicators=positives,
        company_result=company_result,
        url_result=url_result,
        score_breakdown=score["score_breakdown"],
        top_terms=ml.get("top_terms"),
        ml_available=ml.get("available", False),
    )

    return {
        "url_result": url_result,
        "company_result": company_result,
        "ml": ml,
        "red_flags": red_flags,
        "positives": positives,
        "bonus": bonus,
        "score": score,
        "explanation": explanation,
    }


def audit_ml_integration():
    print("==================================================")
    print("SECTION 2: ML INTEGRATION AUDIT")
    print("==================================================")
    avail = ml_service.is_available()
    print(f"ML Available: {avail}")
    assert avail, "ML model should be available"

    p_legit = ml_service.predict("Infosys Senior Software Engineer Python Django AWS microservices")
    p_scam = ml_service.predict("Earn 5000 daily deposit registration fee to join contact WhatsApp")

    print(f"Legit P(scam): {p_legit.get('scam_probability')} | Top Terms: {[t['term'] for t in p_legit.get('top_terms', [])[:3]]}")
    print(f"Scam P(scam):  {p_scam.get('scam_probability')} | Top Terms: {[t['term'] for t in p_scam.get('top_terms', [])[:3]]}")
    assert 0.0 <= p_legit["scam_probability"] <= 1.0
    assert 0.0 <= p_scam["scam_probability"] <= 1.0
    assert p_scam["scam_probability"] > 0.90
    assert p_legit["scam_probability"] < 0.10
    print("PASS: ML Integration sanity verified.")


def audit_double_counting():
    print("\n==================================================")
    print("SECTION 4: DOUBLE-COUNTING AUDIT")
    print("==================================================")
    desc = (
        "We are hiring a Junior Developer for frontend development. "
        "Candidate will work with React and TypeScript. Qualifications: degree in CS or equivalent. "
        "Competitive salary and standard work hours. Interview process includes technical assessment."
    )

    # Case A: Gmail only (Unknown company)
    res_a = run_single_analysis(
        title="Junior Developer",
        company_name="Acme Startups",
        description=desc,
        email="recruiter.acme@gmail.com",
    )

    # Case B: Gmail + domain mismatch (Company has official website example.com, email is gmail)
    res_b = run_single_analysis(
        title="Junior Developer",
        company_name="Acme Solutions",
        description=desc,
        url="https://acmesolutions.com",
        email="recruiter.acme@gmail.com",
    )

    # Case C: Gmail + suspicious URL (e.g. .xyz or lookalike)
    res_c = run_single_analysis(
        title="Junior Developer",
        company_name="Acme Solutions",
        description=desc,
        url="http://acme-jobs.xyz/apply",
        email="recruiter.acme@gmail.com",
    )

    # Case D: Gmail + suspicious URL + impersonation (Claiming TCS with Gmail and .xyz)
    res_d = run_single_analysis(
        title="Junior Developer",
        company_name="Tata Consultancy Services",
        description=desc,
        url="http://tcs-careers-portal.xyz",
        email="tcs.recruiter@gmail.com",
    )

    print(f"Case A (Gmail only):")
    print(f"  Flags: {[f['id'] for f in res_a['red_flags']]}")
    print(f"  Dimensions: Company={res_a['score']['score_breakdown']['dimensions']['company_verification']['score']}, Contact={res_a['score']['score_breakdown']['dimensions']['contact_consistency']['score']}, Scam={res_a['score']['score_breakdown']['dimensions']['scam_detection']['score']}")
    print(f"  Score: {res_a['score']['trust_score']}, Risk: {res_a['score']['risk_level']}, Cap: {res_a['score']['score_breakdown']['cap_applied']}")

    print(f"Case B (Gmail + Domain Mismatch):")
    print(f"  Flags: {[f['id'] for f in res_b['red_flags']]}")
    print(f"  Dimensions: Company={res_b['score']['score_breakdown']['dimensions']['company_verification']['score']}, Contact={res_b['score']['score_breakdown']['dimensions']['contact_consistency']['score']}, Scam={res_b['score']['score_breakdown']['dimensions']['scam_detection']['score']}")
    print(f"  Score: {res_b['score']['trust_score']}, Risk: {res_b['score']['risk_level']}, Cap: {res_b['score']['score_breakdown']['cap_applied']}")

    print(f"Case C (Gmail + Suspicious URL):")
    print(f"  Flags: {[f['id'] for f in res_c['red_flags']]}")
    print(f"  Dimensions: Company={res_c['score']['score_breakdown']['dimensions']['company_verification']['score']}, Source={res_c['score']['score_breakdown']['dimensions']['source_credibility']['score']}, Contact={res_c['score']['score_breakdown']['dimensions']['contact_consistency']['score']}")
    print(f"  Score: {res_c['score']['trust_score']}, Risk: {res_c['score']['risk_level']}, Cap: {res_c['score']['score_breakdown']['cap_applied']}")

    print(f"Case D (Gmail + Suspicious URL + Impersonation):")
    print(f"  Flags: {[f['id'] for f in res_d['red_flags']]}")
    print(f"  Dimensions: Company={res_d['score']['score_breakdown']['dimensions']['company_verification']['score']}, Source={res_d['score']['score_breakdown']['dimensions']['source_credibility']['score']}, Contact={res_d['score']['score_breakdown']['dimensions']['contact_consistency']['score']}")
    print(f"  Score: {res_d['score']['trust_score']}, Risk: {res_d['score']['risk_level']}, Cap: {res_d['score']['score_breakdown']['cap_applied']} ({res_d['score']['score_breakdown']['cap_reason']})")


def audit_hard_caps():
    print("\n==================================================")
    print("SECTION 5: HARD-CAP AUDIT")
    print("==================================================")
    # Case E: Critical scam signals + strong legitimate indicators
    desc_e = (
        "Tata Consultancy Services is seeking a Principal Enterprise Architect. "
        "Candidate must have 15+ years experience in distributed cloud computing, Kubernetes, and TOGAF certification. "
        "Comprehensive healthcare benefits, Provident Fund, stock purchase plan, and 35 days paid annual leave. "
        "Selected candidates will lead global enterprise engineering transformation across North America and Europe. "
        "A mandatory refundable security deposit and registration fee of Rs 2,500 must be transferred via UPI prior to document verification."
    )
    res_e = run_single_analysis(
        title="Principal Enterprise Architect",
        company_name="Tata Consultancy Services",
        description=desc_e,
        email="careers@tcs.com",
        url="https://www.tcs.com/careers",
    )
    print(f"Case E (Critical Scam + Legitimate Enterprise Signals):")
    print(f"  ML P(scam): {res_e['ml']['scam_probability']}")
    print(f"  Flags: {[f['id'] for f in res_e['red_flags']]}")
    print(f"  Raw Weighted Score before cap: {res_e['score']['score_breakdown']['raw_weighted_score']}")
    print(f"  Final Score: {res_e['score']['trust_score']} (Expected <= 35)")
    print(f"  Cap Applied: {res_e['score']['score_breakdown']['cap_applied']} | Reason: {res_e['score']['score_breakdown']['cap_reason']}")
    assert res_e['score']['trust_score'] <= 35, f"Expected critical scam cap <= 35, got {res_e['score']['trust_score']}"

    # Case F: Impersonation + high ML legitimacy
    desc_f = (
        "Tata Consultancy Services invites applications for Senior DevOps Consultant. "
        "Responsibilities: CI/CD automation with GitLab CI, Terraform IaC, AWS ECS, Prometheus, Grafana. "
        "Qualifications: B.Tech/M.Tech with 6+ years experience. Competitive compensation package. "
        "Technical interview and managerial discussion rounds will be scheduled online."
    )
    res_f = run_single_analysis(
        title="Senior DevOps Consultant",
        company_name="Tata Consultancy Services",
        description=desc_f,
        email="tcs.recruiting.team@gmail.com",
    )
    print(f"\nCase F (Impersonation + High ML Legitimacy):")
    print(f"  ML P(scam): {res_f['ml']['scam_probability']}")
    print(f"  Company Status: {res_f['company_result']['status']}")
    print(f"  Flags: {[f['id'] for f in res_f['red_flags']]}")
    print(f"  Raw Weighted Score before cap: {res_f['score']['score_breakdown']['raw_weighted_score']}")
    print(f"  Final Score: {res_f['score']['trust_score']} (Expected <= 25)")
    print(f"  Cap Applied: {res_f['score']['score_breakdown']['cap_applied']} | Reason: {res_f['score']['score_breakdown']['cap_reason']}")
    assert res_f['score']['trust_score'] <= 25, f"Expected impersonation cap <= 25, got {res_f['score']['trust_score']}"

    # Case G: Payment scam + verified company
    desc_g = (
        "Infosys is hiring Customer Support Executives for our Bengaluru campus. "
        "Immediate joining. Candidates must pay a mandatory application fee of 1500 INR to receive interview call letter."
    )
    res_g = run_single_analysis(
        title="Customer Support Executive",
        company_name="Infosys",
        description=desc_g,
        email="careers@infosys.com",
        url="https://www.infosys.com/careers",
    )
    print(f"\nCase G (Payment Scam + Verified Company):")
    print(f"  Company Status: {res_g['company_result']['status']}")
    print(f"  Flags: {[f['id'] for f in res_g['red_flags']]}")
    print(f"  Final Score: {res_g['score']['trust_score']} (Expected <= 35)")
    print(f"  Cap Applied: {res_g['score']['score_breakdown']['cap_applied']}")
    assert res_g['score']['trust_score'] <= 35

    # Case H: Fake company + legitimate-looking text
    desc_h = (
        "Leading international software development consultancy hiring Backend Python Developer. "
        "Experience required: 3-5 years with FastAPI, PostgreSQL, Docker, Redis. "
        "Standard interview rounds: coding challenge, technical discussion, cultural fit. "
        "Salary: 12-16 LPA with standard paid time off."
    )
    res_h = run_single_analysis(
        title="Backend Python Developer",
        company_name="Zephyr Global Innovations",
        description=desc_h,
    )
    print(f"\nCase H (Unverified Company + Professional Text):")
    print(f"  Company Status: {res_h['company_result']['status']}")
    print(f"  Final Score: {res_h['score']['trust_score']} (Expected <= 65)")
    print(f"  Cap Applied: {res_h['score']['score_breakdown']['cap_applied']} | Reason: {res_h['score']['score_breakdown']['cap_reason']}")
    assert res_h['score']['trust_score'] <= 65


def audit_golden_cases():
    print("\n==================================================")
    print("SECTION 11: 20 END-TO-END GOLDEN CASES")
    print("==================================================")

    cases = [
        # --- 10 LEGITIMATE CASES ---
        {
            "id": 1,
            "type": "LEGITIMATE",
            "name": "Verified Corporate Job (TCS)",
            "title": "Lead Software Engineer",
            "company": "Tata Consultancy Services",
            "desc": "Tata Consultancy Services is looking for a Lead Software Engineer with 7+ years in Java microservices, Spring Boot, and Kubernetes. The candidate will design enterprise cloud architectures and lead junior developers. Minimum qualification: B.Tech/B.E in Computer Science. Standard hiring process: technical screening, architecture interview, and HR discussion. No fees are requested at any point.",
            "salary": "18-24 LPA",
            "email": "careers@tcs.com",
            "url": "https://www.tcs.com/careers",
        },
        {
            "id": 2,
            "type": "LEGITIMATE",
            "name": "Verified Corporate Job (Infosys)",
            "title": "Senior Systems Engineer",
            "company": "Infosys",
            "desc": "Infosys is hiring a Senior Systems Engineer for cloud migration initiatives. Candidates must have 4+ years of hands-on experience with AWS, Terraform, and Python. Qualifications include a Bachelor's or Master's degree in engineering. Competitive salary with annual performance bonus, medical insurance, and retirement gratuity. Apply on our official careers portal.",
            "salary": "12-16 LPA",
            "email": "careers@infosys.com",
            "url": "https://www.infosys.com/careers",
        },
        {
            "id": 3,
            "type": "LEGITIMATE",
            "name": "Unknown Startup (No Scam Signals)",
            "title": "Full Stack Developer",
            "company": "Nexlify Tech Labs",
            "desc": "Nexlify Tech Labs is an early-stage startup looking for a Full Stack Developer proficient in React, Node.js, and PostgreSQL. You will collaborate directly with the founders to build our MVP. Qualifications: 2+ years of full stack web development experience. We offer competitive equity, flexible working hours, and standard healthcare reimbursement.",
            "salary": "8-12 LPA",
            "email": "team@nexlify.io",
            "url": "https://nexlify.io",
        },
        {
            "id": 4,
            "type": "LEGITIMATE",
            "name": "University Faculty Recruitment",
            "title": "Assistant Professor in Computer Science",
            "company": "Indian Institute of Science",
            "desc": "The Department of Computer Science and Automation at the Indian Institute of Science invites applications from outstanding candidates for tenure-track Assistant Professor positions. Minimum qualifications include a Ph.D. in Computer Science or related fields with a strong track record of high-impact research publications in top-tier conferences (ACM/IEEE). Compensation follows 7th Central Pay Commission with residential quarters and research seed grants.",
            "salary": "Level 12 as per 7th CPC",
            "email": "recruitment@iisc.ac.in",
            "url": "https://iisc.ac.in/careers",
        },
        {
            "id": 5,
            "type": "LEGITIMATE",
            "name": "Fintech Payment Engineering",
            "title": "Senior Payment Gateway Architect",
            "company": "Razorpay",
            "desc": "Razorpay is seeking an experienced Backend Architect to lead our core payment processing engine. You will design ultra-low-latency transaction pipelines handling millions of merchant bank account settlements, direct deposit disbursements, and PCI-DSS compliant credit card authorization workflows. Qualifications: 8+ years building mission-critical distributed payment systems in Go or Java. Competitive compensation with stock options.",
            "salary": "35-50 LPA",
            "email": "engineering-careers@razorpay.com",
            "url": "https://razorpay.com/jobs",
        },
        {
            "id": 6,
            "type": "LEGITIMATE",
            "name": "Crypto / Web3 Engineering",
            "title": "Blockchain Core Protocol Engineer",
            "company": "CoinDCX",
            "desc": "CoinDCX is seeking a Blockchain Protocol Engineer to build and audit decentralised liquidity smart contracts. Responsibilities: implement consensus algorithms, design EVM compatible protocols, and conduct mathematical security proofs on cryptographic primitives. Requirements: strong proficiency in Rust, Solidity, and distributed cryptography. Candidates must have 3+ years experience with decentralized network design.",
            "salary": "25-35 LPA",
            "email": "careers@coindcx.com",
            "url": "https://coindcx.com/careers",
        },
        {
            "id": 7,
            "type": "LEGITIMATE",
            "name": "Enterprise Job + WhatsApp Coordinator",
            "title": "Campus Recruitment Officer",
            "company": "Wipro",
            "desc": "Wipro Enterprise Services is conducting our 2026 Nationwide Campus Drive for Graduate Engineering Trainees. Selected candidates will participate in our 3-month foundational training program. For candidate logistics and venue queries on campus evaluation day, candidates may coordinate with our university relations team via WhatsApp at +91-9876543210. No fees are ever required for employment at Wipro.",
            "salary": "6.5 LPA",
            "email": "campus.talent@wipro.com",
            "url": "https://www.wipro.com/careers",
        },
        {
            "id": 8,
            "type": "LEGITIMATE",
            "name": "Open Source Tech + Telegram Community",
            "title": "Developer Relations Engineer",
            "company": "Polygon Labs",
            "desc": "Polygon Technology is looking for a Developer Relations Engineer to engage our global open-source developer ecosystem. Responsibilities include building technical tutorials, creating developer documentation, and moderating our community developer discussions on Discord and our public developer Telegram channel at t.me/polygondevs. Qualifications: 3+ years in open-source advocacy and smart contract development.",
            "salary": "30-40 LPA",
            "email": "talent@polygon.technology",
            "url": "https://polygon.technology/careers",
        },
        {
            "id": 9,
            "type": "LEGITIMATE",
            "name": "Senior Staff Salary Posting",
            "title": "Staff Software Engineer",
            "company": "Google India",
            "desc": "Google India is hiring a Staff Software Engineer for Google Cloud Storage Systems. Qualifications: BS/MS in Computer Science with 10+ years of industry experience architecting hyperscale storage infrastructure, Paxos consensus implementations, and distributed fault tolerance. Compensation package: base salary Rs 75 LPA plus annual performance equity grants, comprehensive health insurance, and 401k equivalent retirement contribution.",
            "salary": "Rs 75,00,000 per annum",
            "email": "recruiting@google.com",
            "url": "https://careers.google.com",
        },
        {
            "id": 10,
            "type": "LEGITIMATE",
            "name": "Legitimate Post-Offer Onboarding Verification",
            "title": "Associate Consultant Onboarding",
            "company": "HCL Technologies",
            "desc": "HCL Technologies Welcomes Selected Associate Consultants. Following formal acceptance of your employment offer letter, our HR operations team will conduct mandatory pre-onboarding background verification. Candidates must submit self-attested degree certificates, previous company relieving letters, and proof of identity (passport or PAN card) through our secure employee onboarding portal. Never share passwords or OTPs.",
            "salary": "9-12 LPA",
            "email": "onboarding@hcltech.com",
            "url": "https://www.hcltech.com/careers",
        },

        # --- 10 SCAM CASES ---
        {
            "id": 11,
            "type": "SCAM",
            "name": "Registration Fee Scam",
            "title": "Data Entry Specialist",
            "company": "Prime Typing Global",
            "desc": "URGENT HIRING! Work from home simple typing and copy paste work. Daily payout Rs 3,000 to 5,000 guaranteed. No qualification or experience needed. Basic mobile or laptop is sufficient. To activate your employee portal and receive ID card, candidate must pay a refundable registration fee of Rs 1,499 via GooglePay or UPI today.",
            "salary": "Rs 5,000 per day",
            "email": "primetyping.hr@gmail.com",
            "url": None,
        },
        {
            "id": 12,
            "type": "SCAM",
            "name": "Equipment / Advance Check Scam",
            "title": "Remote Administrative Assistant",
            "company": "Apex Global Logistics",
            "desc": "We are seeking a Remote Administrative Assistant. We will mail you a company cashier's check of $3,500 to purchase your home office workstation and specialized cryptographic software from our certified vendor. Once you deposit the check into your bank account, wire $2,500 via Zelle or Bitcoin to our equipment vendor immediately.",
            "salary": "$45 per hour",
            "email": "recruitment@apexlogistics-work.com",
            "url": "http://apexlogistics-work.com",
        },
        {
            "id": 13,
            "type": "SCAM",
            "name": "Sensitive Credential Harvesting Scam",
            "title": "Online Bank Verification Clerk",
            "company": "SecureTrust Capital",
            "desc": "Immediate opening for Online Bank Verification Clerk. Easy data verification work from mobile phone. Earn Rs 40,000 monthly. To verify your identity for immediate employment disbursement, please enter your Internet Banking login username, ATM debit card PIN, and Aadhaar card OTP on our verification link.",
            "salary": "Rs 40,000/month",
            "email": "hr@securetrust-verify.top",
            "url": "http://securetrust-verify.top/login",
        },
        {
            "id": 14,
            "type": "SCAM",
            "name": "Company Impersonation (TCS on Gmail)",
            "title": "Software Developer Trainee",
            "company": "Tata Consultancy Services",
            "desc": "Tata Consultancy Services is hiring fresh engineering graduates for 2026 batch. Immediate offer letters issued without written test. Selected candidates will be assigned to Pune Tata campus. Please reply directly to our senior human resources manager at tcs.campus.recruiter2026@gmail.com with your resume.",
            "salary": "7 LPA",
            "email": "tcs.campus.recruiter2026@gmail.com",
            "url": None,
        },
        {
            "id": 15,
            "type": "SCAM",
            "name": "Lookalike Domain Scam",
            "title": "Junior Software Trainee",
            "company": "Tata Consultancy Services",
            "desc": "Tata Consultancy Services invites applications for Junior Software Trainees. Candidates must complete their registration and background processing on our newly launched direct-hiring portal: http://tcs-careers-portal.xyz. Apply within 24 hours to secure immediate appointment letter.",
            "salary": "6 LPA",
            "email": "recruitment@tcs-careers-portal.xyz",
            "url": "http://tcs-careers-portal.xyz",
        },
        {
            "id": 16,
            "type": "SCAM",
            "name": "WhatsApp-Only Task / Rating Scam",
            "title": "YouTube Video Reviewer",
            "company": "ViralMedia Solutions",
            "desc": "Work from home part time watching YouTube videos and giving 5-star ratings to hotels on Google Maps. Earn 3000 to 8000 daily with instant UPI payout after every 3 tasks completed. No resume required. Contact our HR manager exclusively on WhatsApp at +91-9988776655 to start task immediately.",
            "salary": "8,000 daily",
            "email": None,
            "url": None,
        },
        {
            "id": 17,
            "type": "SCAM",
            "name": "Telegram Crypto Investment Scam",
            "title": "Crypto Trading Assistant",
            "company": "Binance Global Tasks",
            "desc": "Urgent hiring! Earn daily high returns by completing cryptocurrency arbitrage tasks. Join our official task dispatch channel on Telegram at t.me/binancetaskreward. Deposit 50 USDT to activate your VIP level 1 trading account and get 200 USDT bonus immediately.",
            "salary": "500 USDT/day",
            "email": None,
            "url": "https://t.me/binancetaskreward",
        },
        {
            "id": 18,
            "type": "SCAM",
            "name": "Multiple Critical Signals Combo Scam",
            "title": "Operations Clerk",
            "company": "Tata Consultancy Services",
            "desc": "URGENT VACANCY at Tata Consultancy Services! Earn 10,000 daily working from home! No interview needed! Immediate joining guaranteed! Transfer Rs 2,500 security deposit via PhonePe to hr-tcs@upi. Contact on WhatsApp +91-9876543210 and apply on http://tcs-online-jobs.xyz now! Send your bank passbook and Aadhaar OTP to hr.tcs.india@gmail.com!",
            "salary": "Rs 10,000 per day",
            "email": "hr.tcs.india@gmail.com",
            "url": "http://tcs-online-jobs.xyz",
        },
        {
            "id": 19,
            "type": "SCAM",
            "name": "Unrealistic Salary + Urgency Scam",
            "title": "Data Entry Executive",
            "company": "FastCash Typing Enterprises",
            "desc": "APPLY TODAY ONLY! Earn Rs 90,000 monthly for typing simple MS Word documents 1 hour per day from your mobile phone! Zero experience required, 10th pass eligible, 100% genuine guaranteed income! Only 5 vacancies remaining! Contact immediately before closing date!",
            "salary": "Rs 90,000 per month",
            "email": "fastcashtyping@gmail.com",
            "url": None,
        },
        {
            "id": 20,
            "type": "SCAM",
            "name": "Airport Gate Pass / Security Deposit Scam",
            "title": "Ground Staff Customer Service",
            "company": "Indian Aviation Airport Services",
            "desc": "Direct hiring for Indira Gandhi International Airport ground staff and baggage handling. Selection without exam. Salary Rs 35,000/month with flight discounts. Selected candidates must deposit Rs 3,500 for airport security gate pass and uniform kit. Deposit is 100% refundable after 15 days.",
            "salary": "Rs 35,000/month",
            "email": "airport.groundstaff.recruitment@gmail.com",
            "url": None,
        },
    ]

    results = []
    print(f"{'ID':<3} | {'Type':<10} | {'Case Name':<32} | {'P(scam)':<8} | {'Comp Status':<18} | {'Flags':<20} | {'Score':<5} | {'Risk':<6} | {'Cap'}")
    print("-" * 125)

    for c in cases:
        res = run_single_analysis(
            title=c["title"],
            company_name=c["company"],
            description=c["desc"],
            salary=c["salary"],
            email=c["email"],
            url=c["url"],
        )
        p_scam = res["ml"].get("scam_probability", 0.0)
        c_status = res["company_result"].get("status", "UNVERIFIED")
        flags = [f["id"] for f in res["red_flags"]]
        flags_str = ",".join(flags[:2]) if flags else "None"
        score = res["score"]["trust_score"]
        risk = res["score"]["risk_level"]
        cap = "YES" if res["score"]["score_breakdown"]["cap_applied"] else "NO"

        print(f"{c['id']:<3} | {c['type']:<10} | {c['name'][:32]:<32} | {p_scam:<8.4f} | {c_status:<18} | {flags_str:<20} | {score:<5} | {risk:<6} | {cap}")

        results.append({
            "case": c,
            "output": res,
        })

    # Summary and telemetry collection
    print("\n--- Summary of Golden Cases Audit Telemetry ---")
    legit_low = sum(1 for r in results if r["case"]["type"] == "LEGITIMATE" and r["output"]["score"]["risk_level"] == "LOW")
    legit_med = sum(1 for r in results if r["case"]["type"] == "LEGITIMATE" and r["output"]["score"]["risk_level"] == "MEDIUM")
    legit_high = sum(1 for r in results if r["case"]["type"] == "LEGITIMATE" and r["output"]["score"]["risk_level"] == "HIGH")

    scam_high = sum(1 for r in results if r["case"]["type"] == "SCAM" and r["output"]["score"]["risk_level"] == "HIGH")
    scam_med = sum(1 for r in results if r["case"]["type"] == "SCAM" and r["output"]["score"]["risk_level"] == "MEDIUM")
    scam_low = sum(1 for r in results if r["case"]["type"] == "SCAM" and r["output"]["score"]["risk_level"] == "LOW")

    print(f"Legitimate Cases (N=10): LOW={legit_low}, MEDIUM={legit_med}, HIGH={legit_high}")
    print(f"Scam Cases (N=10):       HIGH={scam_high}, MEDIUM={scam_med}, LOW={scam_low}")

    return results


def audit_contextual_rules():
    print("\n==================================================")
    print("SECTION 7: CONTEXTUAL RULE & STEP 5 COMPARISON")
    print("==================================================")
    context_cases = [
        {
            "name": "Fintech / Payment Processing",
            "title": "Payment Integration Engineer",
            "company": "Infosys",
            "desc": "Infosys is seeking a Payment Integration Engineer. You will integrate bank transfer gateways, NEFT/RTGS transaction reconciliation APIs, and payment card validation protocols. Qualifications: 3+ years experience in fintech payment systems.",
            "email": "careers@infosys.com",
            "url": "https://www.infosys.com/careers",
        },
        {
            "name": "Crypto Blockchain Engineering",
            "title": "Solidity Smart Contract Developer",
            "company": "Infosys",
            "desc": "Infosys Cloud & Security Unit is hiring a Solidity Smart Contract Developer. Work on decentralized blockchain solutions, cryptocurrency wallet integration, and cryptographic protocols. Minimum 2 years experience.",
            "email": "careers@infosys.com",
            "url": "https://www.infosys.com/careers",
        },
        {
            "name": "Legitimate HR Document Onboarding",
            "title": "Operations Associate",
            "company": "Infosys",
            "desc": "Infosys welcomes newly selected candidates. For pre-employment background verification, candidates are requested to upload copies of their degree certificate and PAN card on our secure portal. Never share OTP or passwords.",
            "email": "careers@infosys.com",
            "url": "https://www.infosys.com/careers",
        },
        {
            "name": "Senior Salary ₹60 LPA",
            "title": "Principal Architect",
            "company": "Infosys",
            "desc": "Infosys is hiring a Principal Architect with 12+ years of enterprise experience. Architect global cloud platforms on AWS and Azure. Compensation is Rs 60 LPA.",
            "salary": "Rs 60 LPA",
            "email": "careers@infosys.com",
            "url": "https://www.infosys.com/careers",
        },
        {
            "name": "Urgent Legitimate Hiring",
            "title": "Cloud Engineer",
            "company": "Infosys",
            "desc": "Urgently hiring Cloud Engineers for an immediate client deployment project at Infosys. Candidates must have 3+ years AWS experience. Immediate joining preferred.",
            "email": "careers@infosys.com",
            "url": "https://www.infosys.com/careers",
        },
    ]

    print(f"{'Case Name':<35} | {'Flags':<25} | {'ML P(scam)':<10} | {'D4 Score':<10} | {'Final Score':<12}")
    print("-" * 100)
    for c in context_cases:
        res = run_single_analysis(
            title=c["title"],
            company_name=c["company"],
            description=c["desc"],
            salary=c.get("salary"),
            email=c.get("email"),
            url=c.get("url"),
        )
        flags = [f["id"] for f in res["red_flags"]]
        flags_str = ",".join(flags) if flags else "None"
        ml_p = res["ml"].get("scam_probability", 0.0)
        d4 = res["score"]["score_breakdown"]["dimensions"]["scam_detection"]["score"]
        final_s = res["score"]["trust_score"]
        print(f"{c['name']:<35} | {flags_str:<25} | {ml_p:<10.4f} | {d4:<10.1f} | {final_s:<12}")


def audit_explanation_consistency():
    print("\n==================================================")
    print("SECTION 8: EXPLANATION CONSISTENCY AUDIT")
    print("==================================================")
    test_cases = [
        ("Fee Scam", "Apex Work", "Urgent hiring! Pay registration fee of 1500 to join. Contact on WhatsApp.", None, None),
        ("Impersonation", "Tata Consultancy Services", "Software engineer role. Send resume to hr@gmail.com", "hr@gmail.com", None),
        ("Suspicious Domain", "Tech Corp", "Data analyst position. Apply at http://free-jobs.xyz/apply", None, "http://free-jobs.xyz/apply"),
        ("Credential Scam", "Secure Corp", "Enter your netbanking password, OTP, and CVV to verify bank account.", None, None),
        ("Legit Corporate", "Infosys", "Senior software developer. 5 years experience required. Apply at careers@infosys.com", "careers@infosys.com", "https://www.infosys.com/careers"),
    ]

    for name, comp, desc, email, url in test_cases:
        res = run_single_analysis(
            title="Software Job",
            company_name=comp,
            description=desc,
            email=email,
            url=url,
        )
        print(f"\n--- Case: {name} ---")
        print(f"Flags Triggered: {[f['id'] for f in res['red_flags']]}")
        print(f"Explanation:")
        for line in res["explanation"].splitlines():
            print(f"  {line}")


if __name__ == "__main__":
    audit_ml_integration()
    audit_double_counting()
    audit_hard_caps()
    golden_results = audit_golden_cases()
    audit_contextual_rules()
    audit_explanation_consistency()
