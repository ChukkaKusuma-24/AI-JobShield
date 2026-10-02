"""Seed demo users, companies, scam reports, and ~12 analyses for the dashboard."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running as `python backend/seed.py` from project root
BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal, init_db
from app.models import AnalysisResult, Company, EmailOtp, JobPosting, ScamReport, User
from app.security import hash_otp, hash_password, otp_expiry
from app.services.duplicate import invalidate_cache

SEED_MARKER = "SEED_DEMO"

SEED_50_USERS = [
    # 40 Verified Users
    ("Aarav Sharma", "aarav.sharma@jobshield.demo", True, "user"),
    ("Priya Patel", "priya.patel@jobshield.demo", True, "user"),
    ("Rohan Verma", "rohan.verma@jobshield.demo", True, "user"),
    ("Ananya Iyer", "ananya.iyer@jobshield.demo", True, "user"),
    ("Vikram Malhotra", "vikram.malhotra@jobshield.demo", True, "user"),
    ("Sneha Reddy", "sneha.reddy@jobshield.demo", True, "user"),
    ("Kavya Nair", "kavya.nair@jobshield.demo", True, "user"),
    ("Aditya Joshi", "aditya.joshi@jobshield.demo", True, "user"),
    ("Ishaan Gupta", "ishaan.gupta@jobshield.demo", True, "user"),
    ("Rhea Kapoor", "rhea.kapoor@jobshield.demo", True, "user"),
    ("John Smith", "john.smith@jobshield.demo", True, "user"),
    ("Emily Johnson", "emily.johnson@jobshield.demo", True, "user"),
    ("Michael Brown", "michael.brown@jobshield.demo", True, "user"),
    ("Sarah Davis", "sarah.davis@jobshield.demo", True, "user"),
    ("David Wilson", "david.wilson@jobshield.demo", True, "user"),
    ("Jessica Taylor", "jessica.taylor@jobshield.demo", True, "user"),
    ("James Anderson", "james.anderson@jobshield.demo", True, "user"),
    ("Sophia Thomas", "sophia.thomas@jobshield.demo", True, "user"),
    ("Daniel Martinez", "daniel.martinez@jobshield.demo", True, "user"),
    ("Olivia White", "olivia.white@jobshield.demo", True, "user"),
    ("Lucas Garcia", "lucas.garcia@jobshield.demo", True, "user"),
    ("Emma Robinson", "emma.robinson@jobshield.demo", True, "user"),
    ("Alexander Clark", "alexander.clark@jobshield.demo", True, "user"),
    ("Mia Rodriguez", "mia.rodriguez@jobshield.demo", True, "user"),
    ("Ethan Lewis", "ethan.lewis@jobshield.demo", True, "user"),
    ("Isabella Lee", "isabella.lee@jobshield.demo", True, "user"),
    ("Liam Walker", "liam.walker@jobshield.demo", True, "user"),
    ("Ava Hall", "ava.hall@jobshield.demo", True, "user"),
    ("Noah Allen", "noah.allen@jobshield.demo", True, "user"),
    ("Charlotte Young", "charlotte.young@jobshield.demo", True, "user"),
    ("Benjamin Hernandez", "benjamin.hernandez@jobshield.demo", True, "user"),
    ("Amelia King", "amelia.king@jobshield.demo", True, "user"),
    ("Mason Wright", "mason.wright@jobshield.demo", True, "user"),
    ("Harper Lopez", "harper.lopez@jobshield.demo", True, "user"),
    ("Elijah Hill", "elijah.hill@jobshield.demo", True, "user"),
    ("Evelyn Scott", "evelyn.scott@jobshield.demo", True, "user"),
    ("Oliver Green", "oliver.green@jobshield.demo", True, "user"),
    ("Abigail Adams", "abigail.adams@jobshield.demo", True, "user"),
    ("Mateo Baker", "mateo.baker@jobshield.demo", True, "user"),
    ("Ella Gonzalez", "ella.gonzalez@jobshield.demo", True, "user"),
    # 10 Unverified Users (for testing verification flow)
    ("Tanya Sen", "tanya.sen@jobshield.demo", False, "user"),
    ("Karan Mehta", "karan.mehta@jobshield.demo", False, "user"),
    ("Simran Gill", "simran.gill@jobshield.demo", False, "user"),
    ("Devansh Saxena", "devansh.saxena@jobshield.demo", False, "user"),
    ("Meera Choudhury", "meera.choudhury@jobshield.demo", False, "user"),
    ("Chloe Campbell", "chloe.campbell@jobshield.demo", False, "user"),
    ("Henry Mitchell", "henry.mitchell@jobshield.demo", False, "user"),
    ("Grace Roberts", "grace.roberts@jobshield.demo", False, "user"),
    ("Jack Carter", "jack.carter@jobshield.demo", False, "user"),
    ("Lily Phillips", "lily.phillips@jobshield.demo", False, "user"),
]


def _flags(*ids: str) -> list[dict]:
    catalog = {
        "fee_request": {
            "id": "fee_request",
            "label": "Upfront fee / pay-to-join request",
            "severity": "critical",
            "points": 35,
            "evidence": "registration fee",
        },
        "suspicious_contact": {
            "id": "suspicious_contact",
            "label": "Suspicious contact method (WhatsApp/Telegram-only)",
            "severity": "high",
            "points": 15,
            "evidence": "WhatsApp only",
        },
        "free_email": {
            "id": "free_email",
            "label": "Personal/free email used for claimed company",
            "severity": "medium",
            "points": 12,
            "evidence": "@gmail.com",
        },
        "urgency": {
            "id": "urgency",
            "label": "Urgency / pressure language",
            "severity": "medium",
            "points": 10,
            "evidence": "apply within 24 hours",
        },
        "vague_description": {
            "id": "vague_description",
            "label": "Vague job description",
            "severity": "medium",
            "points": 10,
            "evidence": "short posting",
        },
    }
    return [catalog[i] for i in ids if i in catalog]


def _positives(*ids: str) -> list[dict]:
    catalog = {
        "detailed_responsibilities": {
            "id": "detailed_responsibilities",
            "label": "Detailed responsibilities listed",
        },
        "qualifications": {"id": "qualifications", "label": "Qualifications / skills listed"},
        "official_email": {
            "id": "official_email",
            "label": "Official-looking company-domain email",
        },
        "https_url": {"id": "https_url", "label": "HTTPS URL provided"},
        "interview_process": {
            "id": "interview_process",
            "label": "Interview / selection process mentioned",
        },
        "no_fee": {"id": "no_fee", "label": "No fee / money request detected"},
    }
    return [catalog[i] for i in ids if i in catalog]


# day_offset: days ago from today (0 = today). Varied so the 14-day chart has real counts.
DEMO_ANALYSES = [
    {
        "key": "technova-swe",
        "title": "Software Engineer",
        "company_name": "TechNova Solutions",
        "description": (
            "We are hiring a Software Engineer at TechNova Solutions. Responsibilities include "
            "designing APIs, writing tests, and collaborating with product. Qualifications: CS degree, "
            "Python/JavaScript. Interview: OA, technical, HR. Apply via careers@technovasolutions.com "
            "or https://www.technovasolutions.com/careers. No fees."
        ),
        "salary": "8-12 LPA",
        "email": "careers@technovasolutions.com",
        "url": "https://www.technovasolutions.com/careers",
        "location": "Bengaluru",
        "job_type": "Full-time",
        "day_offset": 1,
        "trust_score": 86,
        "risk_level": "LOW",
        "ml_prob": 0.12,
        "rule_risk": 10,
        "flags": [],
        "positives": [
            "detailed_responsibilities",
            "qualifications",
            "official_email",
            "https_url",
            "interview_process",
            "no_fee",
        ],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": (
            "This posting received a relatively higher trust score (86/100). "
            "No strong rule-based red flags were triggered. Positive signals noted: "
            "detailed responsibilities, official email, interview process."
        ),
    },
    {
        "key": "cloudbridge-fe",
        "title": "Frontend Developer",
        "company_name": "CloudBridge Systems",
        "description": (
            "CloudBridge Systems seeks a Frontend Developer. You will build React UIs, improve "
            "accessibility, and ship features with designers. Requirements: HTML/CSS/JS, React. "
            "Salary 6-9 LPA. Selection via portfolio review and interview. "
            "jobs@cloudbridgesystems.com — https://www.cloudbridgesystems.com/jobs"
        ),
        "salary": "6-9 LPA",
        "email": "jobs@cloudbridgesystems.com",
        "url": "https://www.cloudbridgesystems.com/jobs",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "day_offset": 2,
        "trust_score": 82,
        "risk_level": "LOW",
        "ml_prob": 0.18,
        "rule_risk": 12,
        "flags": [],
        "positives": [
            "detailed_responsibilities",
            "qualifications",
            "official_email",
            "https_url",
            "no_fee",
        ],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Relatively higher trust score with clear responsibilities and official contact channels.",
    },
    {
        "key": "datasphere-da",
        "title": "Data Analyst",
        "company_name": "DataSphere Labs",
        "description": (
            "DataSphere Labs is hiring a Data Analyst. Duties: dashboards, SQL reporting, stakeholder "
            "updates. Qualifications: SQL, Excel, statistics basics. CTC 5-8 LPA. Multi-round interview. "
            "talent@dataspherelabs.com https://www.dataspherelabs.com/careers"
        ),
        "salary": "5-8 LPA",
        "email": "talent@dataspherelabs.com",
        "url": "https://www.dataspherelabs.com/careers",
        "location": "Pune",
        "job_type": "Full-time",
        "day_offset": 3,
        "trust_score": 79,
        "risk_level": "LOW",
        "ml_prob": 0.22,
        "rule_risk": 15,
        "flags": [],
        "positives": ["detailed_responsibilities", "qualifications", "official_email", "https_url"],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Low-risk posting with structured JD and company-domain email.",
    },
    {
        "key": "nextgen-py",
        "title": "Python Developer",
        "company_name": "NextGen Technologies",
        "description": (
            "Opening for Python Developer at NextGen Technologies. Role involves backend services, "
            "automation scripts, and code reviews. Must-have: Python, Git. Package 7-10 LPA. "
            "Process: written test + interview. hiring@nextgentech.example "
            "https://www.nextgentech.example/careers"
        ),
        "salary": "7-10 LPA",
        "email": "hiring@nextgentech.example",
        "url": "https://www.nextgentech.example/careers",
        "location": "Chennai",
        "job_type": "Full-time",
        "day_offset": 4,
        "trust_score": 74,
        "risk_level": "LOW",
        "ml_prob": 0.28,
        "rule_risk": 18,
        "flags": [],
        "positives": ["detailed_responsibilities", "qualifications", "https_url", "interview_process"],
        "company_status": "UNABLE TO VERIFY",
        "url_risk": "LOW",
        "explanation": "Mostly consistent local signals; company could not be fully verified online.",
    },
    {
        "key": "visionworks-ml",
        "title": "ML Intern",
        "company_name": "VisionWorks",
        "description": (
            "Internship opportunity – ML Intern with VisionWorks. Learn real projects, attend weekly "
            "reviews. Stipend 15000/month. Eligibility: 3rd/4th year students. Selection through form "
            "and interview. internship@visionworks.ai https://www.visionworks.ai/internships. No fees."
        ),
        "salary": "15000/month",
        "email": "internship@visionworks.ai",
        "url": "https://www.visionworks.ai/internships",
        "location": "Remote",
        "job_type": "Internship",
        "day_offset": 5,
        "trust_score": 77,
        "risk_level": "LOW",
        "ml_prob": 0.20,
        "rule_risk": 14,
        "flags": [],
        "positives": ["interview_process", "official_email", "https_url", "no_fee"],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Internship posting looks structured with stipend and interview process.",
    },
    {
        "key": "codecraft-be",
        "title": "Backend Developer",
        "company_name": "CodeCraft Labs",
        "description": (
            "Join CodeCraft Labs as Backend Developer. Own modules end-to-end, write tests, document APIs. "
            "Requirements: degree, 0-2 years, Git. Package 6-10 LPA. OA → technical → HR. "
            "recruit@codecraftlabs.com https://www.codecraftlabs.com/careers"
        ),
        "salary": "6-10 LPA",
        "email": "recruit@codecraftlabs.com",
        "url": "https://www.codecraftlabs.com/careers",
        "location": "Noida",
        "job_type": "Full-time",
        "day_offset": 6,
        "trust_score": 81,
        "risk_level": "LOW",
        "ml_prob": 0.16,
        "rule_risk": 11,
        "flags": [],
        "positives": [
            "detailed_responsibilities",
            "qualifications",
            "official_email",
            "https_url",
            "interview_process",
        ],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Clear responsibilities and transparent selection process.",
    },
    {
        "key": "appmatrix-java",
        "title": "Java Developer",
        "company_name": "AppMatrix",
        "description": (
            "AppMatrix hiring Java Developer in Mumbai. Duties: spring services, mentoring juniors. "
            "Competitive salary 8-14 LPA. Interview schedule after shortlisting. "
            "careers@appmatrix.com https://www.appmatrix.com/jobs"
        ),
        "salary": "8-14 LPA",
        "email": "careers@appmatrix.com",
        "url": "https://www.appmatrix.com/jobs",
        "location": "Mumbai",
        "job_type": "Full-time",
        "day_offset": 7,
        "trust_score": 72,
        "risk_level": "LOW",
        "ml_prob": 0.25,
        "rule_risk": 20,
        "flags": [],
        "positives": ["official_email", "https_url", "interview_process"],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Generally consistent signals with official domain email.",
    },
    {
        "key": "digitalcore-web",
        "title": "Web Developer",
        "company_name": "DigitalCore",
        "description": (
            "DigitalCore looking for Web Developer. Some details listed but contact is hr.digitalcore@gmail.com "
            "and posting says apply within 24 hours for limited seats. Salary mentioned as competitive. "
            "Website http://digitalcore-jobs.info/apply"
        ),
        "salary": "Competitive",
        "email": "hr.digitalcore@gmail.com",
        "url": "http://digitalcore-jobs.info/apply",
        "location": "Remote",
        "job_type": "Contract",
        "day_offset": 8,
        "trust_score": 48,
        "risk_level": "MEDIUM",
        "ml_prob": 0.55,
        "rule_risk": 45,
        "flags": ["free_email", "urgency"],
        "positives": [],
        "company_status": "NOT VERIFIED",
        "url_risk": "MEDIUM",
        "explanation": (
            "Medium-risk score mainly because of free email for claimed company and urgency language."
        ),
    },
    {
        "key": "infrastack-devops",
        "title": "DevOps Intern",
        "company_name": "InfraStack",
        "description": (
            "DevOps Intern at InfraStack. Assist with CI pipelines and cloud basics under mentorship. "
            "Stipend 12000/month. Student eligibility. Selection via interview. "
            "interns@infrastack.io https://www.infrastack.io/careers"
        ),
        "salary": "12000/month",
        "email": "interns@infrastack.io",
        "url": "https://www.infrastack.io/careers",
        "location": "Bengaluru",
        "job_type": "Internship",
        "day_offset": 9,
        "trust_score": 75,
        "risk_level": "LOW",
        "ml_prob": 0.21,
        "rule_risk": 16,
        "flags": [],
        "positives": ["interview_process", "https_url", "no_fee"],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Internship looks plausible with mentorship and interview selection.",
    },
    {
        "key": "futuresoft-intern",
        "title": "Software Intern",
        "company_name": "FutureSoft",
        "description": (
            "Software Intern with FutureSoft. Learn real projects, weekly reviews, final presentation. "
            "Stipend 10000 per month. 3rd/4th year students. Application form + interview. "
            "internship@futuresoft.dev https://www.futuresoft.dev/intern. No fees required."
        ),
        "salary": "10000/month",
        "email": "internship@futuresoft.dev",
        "url": "https://www.futuresoft.dev/intern",
        "location": "Hyderabad",
        "job_type": "Internship",
        "day_offset": 10,
        "trust_score": 78,
        "risk_level": "LOW",
        "ml_prob": 0.19,
        "rule_risk": 13,
        "flags": [],
        "positives": ["interview_process", "https_url", "no_fee", "official_email"],
        "company_status": "PARTIALLY VERIFIED",
        "url_risk": "LOW",
        "explanation": "Structured internship with no fee requests.",
    },
    {
        "key": "quickcash-wfh",
        "title": "Work From Home Data Entry",
        "company_name": "Quick Cash Careers",
        "description": (
            "URGENT hiring! Work from home and earn 5000/day. No interview needed. "
            "Pay registration fee of 1499 via UPI to join. Contact on WhatsApp only. "
            "Guaranteed job for freshers. Limited seats apply within 24 hours."
        ),
        "salary": "5000/day",
        "email": "hr1@gmail.com",
        "url": "http://quick-cash-jobs.xyz/apply",
        "location": "Remote",
        "job_type": "Part-time",
        "day_offset": 0,
        "trust_score": 22,
        "risk_level": "HIGH",
        "ml_prob": 0.91,
        "rule_risk": 78,
        "flags": ["fee_request", "suspicious_contact", "free_email", "urgency"],
        "positives": [],
        "company_status": "NOT VERIFIED",
        "url_risk": "HIGH",
        "explanation": (
            "High-risk score mainly because it requests an upfront registration fee and "
            "uses WhatsApp-only contact with a free email domain."
        ),
    },
    {
        "key": "primeearn-crypto",
        "title": "Crypto Trading Internship",
        "company_name": "Prime Earn Online",
        "description": (
            "Crypto trading internship – guaranteed profits 25000/month. "
            "Invest 2999 to get started. Contact via Telegram only. No experience needed."
        ),
        "salary": "25000/month",
        "email": "primehr@yahoo.com",
        "url": "http://bit.ly/fake-crypto-intern",
        "location": "Remote",
        "job_type": "Internship",
        "day_offset": 3,
        "trust_score": 25,
        "risk_level": "HIGH",
        "ml_prob": 0.88,
        "rule_risk": 72,
        "flags": ["fee_request", "suspicious_contact", "free_email"],
        "positives": [],
        "company_status": "NOT VERIFIED",
        "url_risk": "HIGH",
        "explanation": "High risk due to investment ask and Telegram-only contact.",
    },
    {
        "key": "dreamjob-mkt",
        "title": "Marketing Intern",
        "company_name": "Dream Job Express",
        "description": (
            "Guaranteed internship. Instant selection, no experience required. "
            "Transfer security deposit 999 to start training. Email HR at hr99@gmail.com."
        ),
        "salary": "Not stated",
        "email": "hr99@gmail.com",
        "url": None,
        "location": "Remote",
        "job_type": "Internship",
        "day_offset": 11,
        "trust_score": 28,
        "risk_level": "HIGH",
        "ml_prob": 0.84,
        "rule_risk": 70,
        "flags": ["fee_request", "free_email", "vague_description"],
        "positives": [],
        "company_status": "NOT VERIFIED",
        "url_risk": None,
        "explanation": "High risk: security deposit and free email with vague description.",
    },
    {
        "key": "oppohub-support",
        "title": "Customer Support Executive",
        "company_name": "Global Opportunity Hub",
        "description": (
            "Hiring support staff. Easy work from home. Message on WhatsApp for joining. "
            "Send Aadhaar for verification. Limited seats!!!!"
        ),
        "salary": "Earn daily",
        "email": "support.hub@outlook.com",
        "url": "http://opp-hub.top/join",
        "location": "Work from home",
        "job_type": "Part-time",
        "day_offset": 12,
        "trust_score": 35,
        "risk_level": "HIGH",
        "ml_prob": 0.79,
        "rule_risk": 60,
        "flags": ["suspicious_contact", "free_email", "urgency", "vague_description"],
        "positives": [],
        "company_status": "NOT VERIFIED",
        "url_risk": "HIGH",
        "explanation": "High risk from WhatsApp-only contact, urgency, and vague JD.",
    },
]


DEMO_COMPANIES = [
    ("TechNova Solutions", "technovasolutions.com", "PARTIALLY VERIFIED"),
    ("CloudBridge Systems", "cloudbridgesystems.com", "PARTIALLY VERIFIED"),
    ("DataSphere Labs", "dataspherelabs.com", "PARTIALLY VERIFIED"),
    ("VisionWorks", "visionworks.ai", "PARTIALLY VERIFIED"),
    ("CodeCraft Labs", "codecraftlabs.com", "PARTIALLY VERIFIED"),
    ("AppMatrix", "appmatrix.com", "PARTIALLY VERIFIED"),
    ("InfraStack", "infrastack.io", "PARTIALLY VERIFIED"),
    ("FutureSoft", "futuresoft.dev", "PARTIALLY VERIFIED"),
    ("Quick Cash Careers", None, "NOT VERIFIED"),
    ("Prime Earn Online", None, "NOT VERIFIED"),
    ("Dream Job Express", None, "NOT VERIFIED"),
    ("Global Opportunity Hub", None, "NOT VERIFIED"),
]


def _clear_demo_analyses(db, demo_user_id: int) -> None:
    """Remove previous seed analyses/postings for the demo user (idempotent reseed)."""
    existing = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == demo_user_id, JobPosting.source == SEED_MARKER)
        .all()
    )
    for jp in existing:
        for ar in db.query(AnalysisResult).filter(AnalysisResult.job_posting_id == jp.id).all():
            db.delete(ar)
        db.delete(jp)
    db.flush()


def seed():
    init_db()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@jobshield.local").first()
        if not admin:
            admin = User(
                name="Admin Demo",
                email="admin@jobshield.local",
                password_hash=hash_password("admin1234"),
                role="admin",
                is_verified=True,
            )
            db.add(admin)
        else:
            admin.is_verified = True
            admin.role = "admin"

        demo = db.query(User).filter(User.email == "demo@jobshield.local").first()
        if not demo:
            demo = User(
                name="Demo Student",
                email="demo@jobshield.local",
                password_hash=hash_password("demo1234"),
                role="user",
                is_verified=True,
            )
            db.add(demo)
        else:
            demo.is_verified = True
        db.commit()
        db.refresh(admin)
        db.refresh(demo)

        # Seed 50 realistic users (40 verified, 10 unverified)
        default_seed_pw_hash = hash_password("TestPass123!")
        default_otp_hash = hash_otp("123456")
        expiry = otp_expiry()

        for name, email, verified, role in SEED_50_USERS:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    name=name,
                    email=email,
                    password_hash=default_seed_pw_hash,
                    role=role,
                    is_verified=verified,
                )
                db.add(u)
                db.flush()
            else:
                u.name = name
                u.is_verified = verified
                u.role = role

            if not verified:
                # Add or update OTP record for testing verification
                otp_rec = (
                    db.query(EmailOtp)
                    .filter(EmailOtp.user_id == u.id, EmailOtp.purpose == "verification")
                    .first()
                )
                if not otp_rec:
                    otp_rec = EmailOtp(
                        user_id=u.id,
                        otp_hash=default_otp_hash,
                        purpose="verification",
                        expires_at=expiry,
                        attempts=0,
                    )
                    db.add(otp_rec)
                else:
                    otp_rec.otp_hash = default_otp_hash
                    otp_rec.expires_at = expiry
                    otp_rec.attempts = 0

        db.commit()

        now = datetime.now(timezone.utc)

        for name, domain, status in DEMO_COMPANIES:
            row = db.query(Company).filter(Company.name == name).first()
            if not row:
                db.add(
                    Company(
                        name=name,
                        domain=domain,
                        verification_status=status,
                        last_checked_at=now,
                        notes=f"{SEED_MARKER} company record",
                    )
                )
            else:
                row.domain = domain or row.domain
                row.verification_status = status
                row.last_checked_at = now
        db.flush()

        # Scam reports (detect by title+company)
        samples = [
            {
                "job_title": "Work From Home Data Entry",
                "company_name": "Quick Cash Careers",
                "description": DEMO_ANALYSES[10]["description"],
                "url": "http://quick-cash-jobs.xyz/apply",
                "reason": "Asked for registration fee over WhatsApp",
            },
            {
                "job_title": "Crypto Trading Internship",
                "company_name": "Prime Earn Online",
                "description": DEMO_ANALYSES[11]["description"],
                "url": "http://bit.ly/fake-crypto-intern",
                "reason": "Asked for investment and Telegram-only contact",
            },
            {
                "job_title": "Marketing Intern",
                "company_name": "Dream Job Express",
                "description": DEMO_ANALYSES[12]["description"],
                "reason": "Security deposit requested before joining",
            },
            {
                "job_title": "Customer Support Executive",
                "company_name": "Global Opportunity Hub",
                "description": DEMO_ANALYSES[13]["description"],
                "url": "http://opp-hub.top/join",
                "reason": "Asked for Aadhaar over WhatsApp",
            },
        ]
        for s in samples:
            exists = (
                db.query(ScamReport)
                .filter(
                    ScamReport.job_title == s["job_title"],
                    ScamReport.company_name == s["company_name"],
                )
                .first()
            )
            if not exists:
                db.add(
                    ScamReport(
                        user_id=admin.id,
                        job_title=s["job_title"],
                        company_name=s["company_name"],
                        description=s["description"],
                        url=s.get("url"),
                        reason=s["reason"],
                        status="reviewed",
                    )
                )

        _clear_demo_analyses(db, demo.id)

        for item in DEMO_ANALYSES:
            created = now - timedelta(days=item["day_offset"], hours=item["day_offset"] % 5)
            company = db.query(Company).filter(Company.name == item["company_name"]).first()
            posting = JobPosting(
                user_id=demo.id,
                title=item["title"],
                company_id=company.id if company else None,
                company_name=item["company_name"],
                description=item["description"],
                salary=item.get("salary"),
                email=item.get("email"),
                url=item.get("url"),
                location=item.get("location"),
                job_type=item.get("job_type"),
                source=SEED_MARKER,
                created_at=created,
            )
            db.add(posting)
            db.flush()

            flags = _flags(*item.get("flags", []))
            positives = _positives(*item.get("positives", []))
            breakdown = {
                "trust_score": item["trust_score"],
                "risk_level": item["risk_level"],
                "raw_rule_points": sum(f["points"] for f in flags),
                "positive_bonus": min(5 * len(positives), 25),
                "rule_risk": item["rule_risk"],
                "ml_available": True,
                "ml_scam_probability": item["ml_prob"],
                "seed": SEED_MARKER,
                "seed_key": item["key"],
            }
            url_analysis = {}
            if item.get("url"):
                url_analysis = {
                    "url": item["url"],
                    "valid": True,
                    "risk_level": item.get("url_risk") or "LOW",
                    "risk_score": 10 if item.get("url_risk") == "LOW" else 55,
                    "indicators": [],
                    "explanation": "Seeded URL heuristic snapshot.",
                }

            db.add(
                AnalysisResult(
                    job_posting_id=posting.id,
                    user_id=demo.id,
                    trust_score=item["trust_score"],
                    risk_level=item["risk_level"],
                    ml_scam_probability=item["ml_prob"],
                    rule_risk_points=float(item["rule_risk"]),
                    red_flags=json.dumps(flags),
                    positive_indicators=json.dumps(positives),
                    explanation=item["explanation"]
                    + " AI JobShield gives guidance, not a verdict. Always verify through official channels.",
                    company_verification=json.dumps(
                        {
                            "status": item["company_status"],
                            "summary": f"Seeded status: {item['company_status']}",
                            "checks": [],
                            "online_lookup_performed": False,
                        }
                    ),
                    url_analysis=json.dumps(url_analysis),
                    duplicate_result=json.dumps({"is_duplicate": False, "matches": []}),
                    score_breakdown=json.dumps(breakdown),
                    created_at=created,
                )
            )

        db.commit()
        invalidate_cache()
        print("Seed complete.")
        print(f"  Demo analyses : {len(DEMO_ANALYSES)} (source={SEED_MARKER})")
        print(f"  Companies     : {len(DEMO_COMPANIES)}")
        print(f"  Scam reports  : {len(samples)}")
        print("  Demo user     : demo@jobshield.local / demo1234")
        print("  Admin user    : admin@jobshield.local / admin1234")
        print("  Re-run safely : clears previous SEED_DEMO analyses for demo user, then inserts again.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
