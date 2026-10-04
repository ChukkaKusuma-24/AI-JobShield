"""Run 15 controlled benchmark cases for Step 4."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "step4_benchmark.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "benchmark-step4-key"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, ml_service, rules, scoring, url_analyzer

init_db()
ml_service.load_model()
db = SessionLocal()

BENCHMARK_CASES = [
    {
        "id": 1,
        "name": "Genuine verified TCS",
        "category": "Legitimate",
        "company_name": "Tata Consultancy Services",
        "title": "Senior Systems Engineer",
        "description": "Responsibilities include microservices architecture, cloud deployment, and system maintenance. Qualifications: 3+ years Java and Spring Boot experience. Selection process includes technical interview and HR discussion.",
        "salary": "₹8,00,000 per annum",
        "email": "careers@tcs.com",
        "url": "https://www.tcs.com/careers",
    },
    {
        "id": 2,
        "name": "Genuine verified Infosys",
        "category": "Legitimate",
        "company_name": "Infosys",
        "title": "Lead Java Developer",
        "description": "Key responsibilities include backend services, microservices, and agile delivery. Qualifications: 5+ years Java and Spring Boot. Interview process involves coding test and HR round.",
        "salary": "₹15,00,000 per annum",
        "email": "careers@infosys.com",
        "url": "https://www.infosys.com/careers",
    },
    {
        "id": 3,
        "name": "Genuine unknown startup",
        "category": "Legitimate",
        "company_name": "Lumina Quantum Systems",
        "title": "Full Stack Engineer",
        "description": "Responsibilities include React UI and FastAPI. Qualifications: 2+ years experience. Interview process includes screening call and virtual interview.",
        "salary": "₹12,00,000 per annum",
        "email": "talent@luminaquantum.tech",
        "url": "https://www.luminaquantum.tech/jobs",
    },
    {
        "id": 4,
        "name": "TCS using Gmail",
        "category": "Fraudulent",
        "company_name": "Tata Consultancy Services",
        "title": "Associate Consultant",
        "description": "Responsibilities include client consulting. Qualifications: B.Tech. Interview process included. Send resume to recruiter email.",
        "salary": "₹6,00,000 per annum",
        "email": "recruiter@gmail.com",
        "url": None,
    },
    {
        "id": 5,
        "name": "TCS lookalike domain",
        "category": "Fraudulent",
        "company_name": "Tata Consultancy Services",
        "title": "Customer Support Executive",
        "description": "Responsibilities involve client support. Qualifications: Any graduate. Immediate document submission required via portal.",
        "salary": "₹35,000 per month",
        "email": "recruiter@tcs-hiring-portal.top",
        "url": "http://tcs-careers-verify.top/apply",
    },
    {
        "id": 6,
        "name": "Registration fee scam",
        "category": "Fraudulent",
        "company_name": "Quick Earn Data Solutions",
        "title": "Data Entry Clerk",
        "description": "Earn Rs 4000 per day. No experience needed. Note: Candidates must pay a mandatory registration fee of ₹1,499 via UPI before account activation.",
        "salary": "₹4,00,000 per day",
        "email": None,
        "url": None,
    },
    {
        "id": 7,
        "name": "Equipment/deposit scam",
        "category": "Fraudulent",
        "company_name": "Global Virtual Workspace",
        "title": "Remote Administrative Assistant",
        "description": "Candidates are required to pay for home office equipment and purchase a mandatory security deposit kit of ₹8,500 prior to laptop dispatch.",
        "salary": None,
        "email": None,
        "url": None,
    },
    {
        "id": 8,
        "name": "WhatsApp-only recruitment",
        "category": "Fraudulent",
        "company_name": "Apex Media Services",
        "title": "Digital Marketing Associate",
        "description": "Duties include managing social media campaigns, preparing marketing collateral, and analyzing engagement metrics. Qualifications: Bachelor's degree in marketing or communications, knowledge of Canva and social platforms. To apply, contact on WhatsApp only at +91-9876543210. No phone calls or emails will be entertained. Message via WhatsApp to schedule your instant interview.",
        "salary": "₹25,000 - ₹30,000 per month",
        "email": None,
        "url": None,
    },
    {
        "id": 9,
        "name": "Telegram-only recruitment",
        "category": "Fraudulent",
        "company_name": "Crypto Alpha Labs",
        "title": "Blockchain Research Analyst",
        "description": "Key responsibilities include monitoring decentralized protocol yields, preparing market summary notes, and researching tokenomics. Qualifications: Familiarity with crypto exchanges, basic financial acumen. All communication and project coordination is conducted via Telegram only. Interested applicants must message on Telegram @cryptoalpha_hr for onboarding tasks and interview details.",
        "salary": "₹50,000 per month",
        "email": None,
        "url": None,
    },
    {
        "id": 10,
        "name": "Unrealistic salary scam",
        "category": "Fraudulent",
        "company_name": "Swift Careers",
        "title": "Fresher Typist",
        "description": "Guaranteed placement for freshers with no experience needed. Simple typing. Earn ₹5000 per day. Apply within 24 hours.",
        "salary": "₹5,000 per day",
        "email": None,
        "url": None,
    },
    {
        "id": 11,
        "name": "Sensitive info request",
        "category": "Fraudulent",
        "company_name": "Verification Bureau",
        "title": "Verification Assistant",
        "description": "Applicants must email their original Aadhaar card, PAN card, bank account statement, and debit card details prior to interview.",
        "salary": None,
        "email": None,
        "url": None,
    },
    {
        "id": 12,
        "name": "Multiple critical signals",
        "category": "Fraudulent",
        "company_name": "Fast Track Employment",
        "title": "Data Assistant",
        "description": "No interview needed, guaranteed placement. Must pay application fee of ₹2,500 via UPI. Submit your Aadhaar and bank details for payroll.",
        "salary": None,
        "email": None,
        "url": None,
    },
    {
        "id": 13,
        "name": "Legitimate incomplete posting",
        "category": "Legitimate",
        "company_name": "Wipro",
        "title": "Project Engineer",
        "description": "Wipro is hiring Project Engineers. Responsibilities include automated testing frameworks. Qualifications: B.E./B.Tech.",
        "salary": None,
        "email": None,
        "url": None,
    },
    {
        "id": 14,
        "name": "Legitimate job + WhatsApp",
        "category": "Legitimate",
        "company_name": "Reliance Jio",
        "title": "Senior Network Engineer",
        "description": "Reliance Jio Infocomm is hiring. Key responsibilities include radio network optimization. Qualifications: Degree in Telecom. Candidates may also reach out on WhatsApp at +91-9123456789.",
        "salary": "₹16,00,000 per annum",
        "email": "careers@jio.com",
        "url": "https://careers.jio.com",
    },
    {
        "id": 15,
        "name": "Legitimate payment-context job",
        "category": "Legitimate",
        "company_name": "HCLTech",
        "title": "Payment Gateway Engineer",
        "description": "HCLTech is looking for senior engineers experienced in integrating payment gateway protocols, building secure bank transfer APIs, processing automated gift cards redemption systems, and handling crypto custody microservices for our financial services clients. Qualifications: 5+ years backend engineering in Java/Go, deep knowledge of PCI-DSS compliance and financial ledger consistency.",
        "salary": "₹22,00,000 per annum",
        "email": "careers@hcltech.com",
        "url": "https://www.hcltech.com/careers",
    },
]

results = []
print(f"{'ID':<3} | {'Case Name':<32} | {'Category':<11} | {'Comp Status':<18} | {'Flags':<25} | {'Score':<5} | {'Risk':<6}")
print("-" * 115)

for c in BENCHMARK_CASES:
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

    ml = ml_service.predict(f"{c['title']} {c['company_name']} {c['description']} {c['salary'] or ''}")

    score_res = scoring.compute_trust_score(
        flags,
        bonus,
        ml.get("scam_probability"),
        ml.get("available", False),
        company_result=comp_res,
        url_result=url_res,
        positive_indicators=positives,
        email=c["email"],
    )

    flag_names = ",".join(f["id"] for f in flags) or "None"
    print(f"{c['id']:<3} | {c['name']:<32} | {c['category']:<11} | {comp_res.get('status', 'N/A'):<18} | {flag_names[:25]:<25} | {score_res['trust_score']:<5} | {score_res['risk_level']:<6}")
    results.append({
        "id": c["id"],
        "name": c["name"],
        "category": c["category"],
        "company_status": comp_res.get("status"),
        "flags": [f["id"] for f in flags],
        "positives": [p["id"] for p in positives],
        "trust_score": score_res["trust_score"],
        "risk_level": score_res["risk_level"],
        "breakdown": score_res["score_breakdown"],
    })

db.close()
