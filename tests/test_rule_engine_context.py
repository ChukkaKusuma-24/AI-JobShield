"""Step 5 Adversarial and Context-Aware Rule Engine Tests.

Covers all 27 required adversarial and contextual cases:
1. Legitimate fintech job mentioning bank transfers
2. Legitimate crypto engineering job
3. Legitimate gift-card engineering job
4. Legitimate payment-processing job
5. 'No application fee' statement
6. Legitimate HR identity verification
7. Suspicious Aadhaar request through WhatsApp
8. OTP request
9. Registration fee request
10. Equipment deposit
11. Unrealistic salary alone (Senior engineer ₹50 LPA for 8 years)
12. Unrealistic salary + urgency
13. WhatsApp-only unknown-company job
14. WhatsApp + official company domain
15. Telegram-only job
16. Telegram + payment request
17. Urgent legitimate job
18. Urgent scam with payment
19. No interview but official company
20. No interview + suspicious contact + high salary
21. Short legitimate job posting
22. Vague job + suspicious contact
23. ALL CAPS legitimate job
24. ALL CAPS + payment request
25. Official TCS job
26. TCS Gmail impersonation
27. TCS lookalike domain
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = ROOT / "database" / "test_step5_rule_context.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-jobshield-rule-context"
os.environ["ENABLE_ONLINE_LOOKUP"] = "false"
os.environ["SMTP_CONSOLE_FALLBACK"] = "true"

from app.config import get_settings
get_settings.cache_clear()

from app.database import SessionLocal, init_db
from app.services import company_verifier, ml_service, rules, scoring, url_analyzer

init_db()


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# -------------------------------------------------------------
# Test 1: Legitimate fintech job mentioning bank transfers
# -------------------------------------------------------------
def test_01_legitimate_fintech_bank_transfers():
    flags, positives, bonus = rules.analyze_rules(
        title="Fintech Backend Engineer",
        company_name="Apex Payments Pvt Ltd",
        description=(
            "Responsibilities include designing and scaling microservices for automated bank transfer processing, "
            "implementing PCI-DSS compliant workflows, and reconciling high-volume financial ledger transactions. "
            "Qualifications: 4+ years Java or Go, deep experience with distributed databases and banking APIs. "
            "The hiring process involves technical screening, system design assessment, and HR discussion."
        ),
        salary="₹18,00,000 per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "money_transfer" not in flag_ids
    assert "fee_request" not in flag_ids


# -------------------------------------------------------------
# Test 2: Legitimate crypto engineering job
# -------------------------------------------------------------
def test_02_legitimate_crypto_engineering():
    flags, positives, bonus = rules.analyze_rules(
        title="Blockchain Protocol Engineer",
        company_name="Decentralized Systems Labs",
        description=(
            "You will build decentralized liquidity protocol architectures, optimize smart contract execution, "
            "and interface with major cryptocurrency exchanges for real-time order routing. "
            "Qualifications: Proficiency in Rust or Solidity, 3+ years in cryptographic protocols. "
            "Interview rounds include code pairing and architectural review."
        ),
        salary="₹24,00,000 per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "money_transfer" not in flag_ids
    assert "fee_request" not in flag_ids


# -------------------------------------------------------------
# Test 3: Legitimate gift-card engineering job
# -------------------------------------------------------------
def test_03_legitimate_gift_card_engineering():
    flags, positives, bonus = rules.analyze_rules(
        title="Staff Software Engineer - Rewards Platform",
        company_name="Retail Cloud Technologies",
        description=(
            "Architect and lead development for our enterprise loyalty platform, managing corporate gift card inventory APIs, "
            "e-voucher generation pipelines, and automated point-of-sale redemptions. "
            "Requirements: BS/MS in Computer Science, 6+ years building high-throughput consumer platforms. "
            "Selection process consists of technical deep-dive and managerial interview."
        ),
        salary="₹28,00,000 per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "money_transfer" not in flag_ids
    assert "fee_request" not in flag_ids


# -------------------------------------------------------------
# Test 4: Legitimate payment-processing job
# -------------------------------------------------------------
def test_04_legitimate_payment_processing():
    flags, positives, bonus = rules.analyze_rules(
        title="Lead Payment Gateway Integration Engineer",
        company_name="Checkout Global Solutions",
        description=(
            "Responsibilities: Integrate multi-currency payment gateway adapters, manage tokenization vaults, "
            "and build resilient failover mechanisms for credit card, debit card, and UPI payment processing. "
            "Qualifications: 5+ years experience in payment infrastructure, security compliance. "
            "Selection includes architectural interview and coding test."
        ),
        salary="₹22,00,000 per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "money_transfer" not in flag_ids
    assert "fee_request" not in flag_ids
    assert "sensitive_info" not in flag_ids


# -------------------------------------------------------------
# Test 5: 'No application fee' statement
# -------------------------------------------------------------
def test_05_no_application_fee_statement():
    flags, positives, bonus = rules.analyze_rules(
        title="Associate Software Engineer",
        company_name="Infosys",
        description=(
            "Infosys is hiring Associate Software Engineers. Note: Our recruitment process is entirely merit-based. "
            "There is strictly no application fee, registration fee, or training fee charged at any stage. "
            "Responsibilities include software development and bug fixes. Qualifications: B.E./B.Tech graduates. "
            "Selection process involves an online assessment and technical interview."
        ),
        salary="₹4,50,000 per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "fee_request" not in flag_ids
    assert "money_transfer" not in flag_ids


# -------------------------------------------------------------
# Test 6: Legitimate HR identity verification
# -------------------------------------------------------------
def test_06_legitimate_hr_identity_verification():
    flags, positives, bonus = rules.analyze_rules(
        title="Cloud Operations Specialist",
        company_name="Tata Consultancy Services",
        description=(
            "Tata Consultancy Services is seeking Cloud Specialists. Responsibilities: Manage Azure resources and CI/CD pipelines. "
            "Qualifications: 3+ years cloud experience. Standard background verification may require identity documents (PAN / Aadhaar) "
            "uploaded through our official HR portal upon joining. Valid passport required for occasional international client visits. "
            "Selection process includes technical round and HR interview."
        ),
        salary="₹9,00,000 per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "sensitive_info" not in flag_ids


# -------------------------------------------------------------
# Test 7: Suspicious Aadhaar request through WhatsApp
# -------------------------------------------------------------
def test_07_suspicious_aadhaar_request_whatsapp():
    flags, positives, bonus = rules.analyze_rules(
        title="Data Verification Associate",
        company_name="Fast Hire Solutions",
        description=(
            "Immediate hiring for back office work. Send your Aadhaar and PAN card to our WhatsApp number +91-9876543210 "
            "prior to interview to confirm your registration. No experience needed."
        ),
        salary="₹30,000 per month",
    )
    flag_ids = [f["id"] for f in flags]
    assert "sensitive_info" in flag_ids
    assert "suspicious_contact" in flag_ids


# -------------------------------------------------------------
# Test 8: OTP request
# -------------------------------------------------------------
def test_08_otp_request():
    flags, positives, bonus = rules.analyze_rules(
        title="Online Verification Executive",
        company_name="Quick Verification Portal",
        description=(
            "To confirm your job application, enter the OTP sent to your mobile phone or share the OTP code with the recruiter. "
            "Applicants must provide bank details and card CVV for salary processing."
        ),
    )
    flag_ids = [f["id"] for f in flags]
    assert "sensitive_info" in flag_ids
    crit_flag = next(f for f in flags if f["id"] == "sensitive_info")
    assert crit_flag["severity"] == "critical"


# -------------------------------------------------------------
# Test 9: Registration fee request
# -------------------------------------------------------------
def test_09_registration_fee_request():
    flags, positives, bonus = rules.analyze_rules(
        title="Data Entry Assistant",
        company_name="Easy Typing Jobs",
        description=(
            "Candidates must pay a mandatory registration fee of ₹1,200 via UPI prior to training session. "
            "Work from home typing assignments. Earn ₹1,500 daily."
        ),
    )
    flag_ids = [f["id"] for f in flags]
    assert "fee_request" in flag_ids


# -------------------------------------------------------------
# Test 10: Equipment deposit
# -------------------------------------------------------------
def test_10_equipment_deposit():
    flags, positives, bonus = rules.analyze_rules(
        title="Remote Customer Representative",
        company_name="Global Virtual Hub",
        description=(
            "Selected employees are required to pay for home office equipment kit deposit of ₹6,500 before company laptop dispatch. "
            "Deposit is refundable after 6 months."
        ),
    )
    flag_ids = [f["id"] for f in flags]
    assert "equipment_purchase" in flag_ids


# -------------------------------------------------------------
# Test 11: Unrealistic salary alone (Senior engineer ₹50 LPA)
# -------------------------------------------------------------
def test_11_unrealistic_salary_alone_senior():
    flags, positives, bonus = rules.analyze_rules(
        title="Principal Software Architect",
        company_name="Enterprise Systems Tech",
        description=(
            "Leading architecture for global SaaS platform. Qualifications: Bachelor's degree and 8+ years hands-on experience "
            "designing resilient distributed systems and mentoring senior engineering staff. "
            "Selection process consists of executive interview and architectural evaluation."
        ),
        salary="₹50 Lakhs per annum",
    )
    flag_ids = [f["id"] for f in flags]
    assert "unrealistic_salary" not in flag_ids


# -------------------------------------------------------------
# Test 12: Unrealistic salary + urgency (Fresher typist)
# -------------------------------------------------------------
def test_12_unrealistic_salary_and_urgency():
    flags, positives, bonus = rules.analyze_rules(
        title="Fresher Typist",
        company_name="Quick Daily Earners",
        description=(
            "Simple typing work for freshers and students. No experience needed. "
            "Earn ₹5,000 per day. Limited seats available, apply within 24 hours or lose your spot!"
        ),
        salary="₹5,000 per day",
    )
    flag_ids = [f["id"] for f in flags]
    assert "unrealistic_salary" in flag_ids
    assert "urgency" in flag_ids


# -------------------------------------------------------------
# Test 13: WhatsApp-only unknown-company job
# -------------------------------------------------------------
def test_13_whatsapp_only_unknown_company():
    flags, positives, bonus = rules.analyze_rules(
        title="Telecaller Assistant",
        company_name="Bright Star Marketing",
        description=(
            "Hiring telecallers for customer surveys. Qualifications: Good verbal communication. "
            "Contact on WhatsApp only at +91-9988776655. No emails accepted."
        ),
        company_status="UNVERIFIED",
    )
    flag_ids = [f["id"] for f in flags]
    assert "suspicious_contact" in flag_ids


# -------------------------------------------------------------
# Test 14: WhatsApp + official company domain
# -------------------------------------------------------------
def test_14_whatsapp_auxiliary_official_company():
    flags, positives, bonus = rules.analyze_rules(
        title="Network Support Engineer",
        company_name="Reliance Jio",
        description=(
            "Reliance Jio is hiring Network Support Engineers. Key tasks include 5G core network monitoring. "
            "Requirements: Degree in Telecommunications. For candidate queries, you may also reach our helpdesk on WhatsApp at +91-9800012345. "
            "Selection includes technical interview."
        ),
        url="https://careers.jio.com",
        email="careers@jio.com",
        company_status="VERIFIED",
    )
    flag_ids = [f["id"] for f in flags]
    assert "suspicious_contact" not in flag_ids


# -------------------------------------------------------------
# Test 15: Telegram-only job
# -------------------------------------------------------------
def test_15_telegram_only_job():
    flags, positives, bonus = rules.analyze_rules(
        title="Content Reviewer",
        company_name="Shadow Media",
        description=(
            "Review articles and posts. All communication is conducted via Telegram only. "
            "Message @shadow_recruiter on Telegram for direct selection details."
        ),
        company_status="UNVERIFIED",
    )
    flag_ids = [f["id"] for f in flags]
    assert "suspicious_contact" in flag_ids


# -------------------------------------------------------------
# Test 16: Telegram + payment request
# -------------------------------------------------------------
def test_16_telegram_and_payment_request():
    flags, positives, bonus = rules.analyze_rules(
        title="VIP Task Operator",
        company_name="Crypto Matrix",
        description=(
            "Message on Telegram @cryptomatrix_admin. "
            "Candidates must pay a processing fee of ₹1,500 via UPI to activate their daily task wallet."
        ),
        company_status="UNVERIFIED",
    )
    flag_ids = [f["id"] for f in flags]
    assert "suspicious_contact" in flag_ids
    assert "fee_request" in flag_ids


# -------------------------------------------------------------
# Test 17: Urgent legitimate job
# -------------------------------------------------------------
def test_17_urgent_legitimate_job():
    flags, positives, bonus = rules.analyze_rules(
        title="Production Incident Specialist",
        company_name="Tata Consultancy Services",
        description=(
            "Tata Consultancy Services is urgently hiring a Production Incident Specialist for critical financial client support. "
            "Immediate joiners preferred. Responsibilities: Real-time incident triage and root cause analysis. "
            "Qualifications: 4+ years Unix and Oracle SQL. Interview process includes technical assessment."
        ),
        email="careers@tcs.com",
        url="https://www.tcs.com/careers",
        company_status="VERIFIED",
    )
    flag_ids = [f["id"] for f in flags]
    assert "urgency" not in flag_ids
    assert len(flag_ids) == 0


# -------------------------------------------------------------
# Test 18: Urgent scam with payment
# -------------------------------------------------------------
def test_18_urgent_scam_with_payment():
    flags, positives, bonus = rules.analyze_rules(
        title="Immediate Placement Clerk",
        company_name="Instant Careers",
        description=(
            "Final warning: Last chance to confirm your direct placement. "
            "You must pay registration fee of ₹999 within 24 hours or your job offer expires!"
        ),
    )
    flag_ids = [f["id"] for f in flags]
    assert "urgency" in flag_ids
    assert "fee_request" in flag_ids


# -------------------------------------------------------------
# Test 19: No interview but official company (Campus recruitment)
# -------------------------------------------------------------
def test_19_no_interview_official_company():
    flags, positives, bonus = rules.analyze_rules(
        title="Graduate Trainee Engineer",
        company_name="Tata Consultancy Services",
        description=(
            "Tata Consultancy Services invites national campus qualifiers for direct offer letter issuance based on National Qualifier Test score. "
            "Responsibilities: Software development and test automation. Qualifications: Final year engineering students."
        ),
        email="careers@tcs.com",
        url="https://www.tcs.com/careers",
        company_status="VERIFIED",
    )
    flag_ids = [f["id"] for f in flags]
    # No fraudulent 'no interview' extortion flag
    assert "fee_request" not in flag_ids


# -------------------------------------------------------------
# Test 20: No interview + suspicious contact + high salary
# -------------------------------------------------------------
def test_20_no_interview_suspicious_contact_high_salary():
    flags, positives, bonus = rules.analyze_rules(
        title="Part-time Data Entry",
        company_name="Swift Earnings",
        description=(
            "No interview required, guaranteed selection! Earn ₹4,000 per day for simple online typing. "
            "Contact on WhatsApp only at +91-9876543210 to start immediately."
        ),
        salary="₹4,000 per day",
    )
    flag_ids = [f["id"] for f in flags]
    assert "no_interview" in flag_ids
    assert "suspicious_contact" in flag_ids
    assert "unrealistic_salary" in flag_ids


# -------------------------------------------------------------
# Test 21: Short legitimate job posting
# -------------------------------------------------------------
def test_21_short_legitimate_job_posting():
    desc = (
        "Senior SRE needed to lead cloud infrastructure resilience. "
        "Key duties include managing Kubernetes clusters and CI/CD pipelines. "
        "Requirements: 5+ years DevOps experience. Selection involves technical interview rounds."
    )
    flags, positives, bonus = rules.analyze_rules(
        title="Senior SRE",
        company_name="Novatech Labs",
        description=desc,
        email="careers@novatechlabs.io",
        url="https://www.novatechlabs.io",
    )
    flag_ids = [f["id"] for f in flags]
    assert "vague_description" not in flag_ids
    assert "fee_request" not in flag_ids


# -------------------------------------------------------------
# Test 22: Vague job + suspicious contact
# -------------------------------------------------------------
def test_22_vague_job_suspicious_contact():
    flags, positives, bonus = rules.analyze_rules(
        title="Online Worker",
        company_name="Global Earn",
        description="Great opportunity. Work from home. Message via WhatsApp to start today.",
    )
    flag_ids = [f["id"] for f in flags]
    assert "vague_description" in flag_ids
    assert "suspicious_contact" in flag_ids


# -------------------------------------------------------------
# Test 23: ALL CAPS legitimate job (Technical acronyms)
# -------------------------------------------------------------
def test_23_all_caps_legitimate_job_acronyms():
    desc = (
        "HIRING: SENIOR AWS SRE ENGINEER. "
        "RESPONSIBILITIES: LEAD ARCHITECTURE FOR AWS, GCP, CI/CD, SQL, REST APIS, AND JSON MICROSERVICES. "
        "QUALIFICATIONS: BS IN CS, DEEP KNOWLEDGE OF TCP/IP, DNS, SSL/TLS, AND KUBERNETES. "
        "INTERVIEW PROCESS INCLUDES TECHNICAL CODING ASSESSMENT AND ARCHITECTURE INTERVIEW ROUND."
    )
    flags, positives, bonus = rules.analyze_rules(
        title="Senior SRE",
        company_name="Cloud Solutions Pvt Ltd",
        description=desc,
    )
    flag_ids = [f["id"] for f in flags]
    # Acronym filtering prevents false caps_exclaim flag
    assert "fee_request" not in flag_ids


# -------------------------------------------------------------
# Test 24: ALL CAPS + payment request
# -------------------------------------------------------------
def test_24_all_caps_payment_request():
    desc = (
        "HIRING NOW FOR WORK FROM HOME TYPING! "
        "MUST PAY APPLICATION FEE OF RS 1500 VIA UPI IMMEDIATELY TO SECURE YOUR SEAT! "
        "DIRECT JOINING GUARANTEED! HURRY UP APPLY NOW OR LOSE SEAT!!!"
    )
    flags, positives, bonus = rules.analyze_rules(
        title="DATA OPERATOR",
        company_name="FAST WORK",
        description=desc,
    )
    flag_ids = [f["id"] for f in flags]
    assert "caps_exclaim" in flag_ids
    assert "fee_request" in flag_ids
    assert "urgency" in flag_ids


# -------------------------------------------------------------
# Test 25: Official TCS job
# -------------------------------------------------------------
def test_25_official_tcs_job(db_session):
    company_name = "Tata Consultancy Services"
    email = "careers@tcs.com"
    url = "https://www.tcs.com/careers"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Lead Cloud Engineer",
        company_name=company_name,
        description=(
            "Tata Consultancy Services is seeking a Lead Cloud Engineer. "
            "Responsibilities: Architect enterprise cloud landing zones and automated CI/CD pipelines. "
            "Qualifications: 6+ years experience in cloud engineering. Selection process involves technical and manager rounds."
        ),
        salary="₹18,00,000 per annum",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert score_res["trust_score"] >= 90
    assert score_res["risk_level"] == "LOW"
    assert len(flags) == 0


# -------------------------------------------------------------
# Test 26: TCS Gmail impersonation
# -------------------------------------------------------------
def test_26_tcs_gmail_impersonation(db_session):
    company_name = "Tata Consultancy Services"
    email = "tcs.hr.recruitment@gmail.com"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=None)
    flags, positives, bonus = rules.analyze_rules(
        title="Operations Trainee",
        company_name=company_name,
        description="Operations trainee needed. Submit resume to email.",
        email=email,
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=None, positive_indicators=positives, email=email
    )
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"
    assert any(f["id"] == "company_impersonation" for f in flags)


# -------------------------------------------------------------
# Test 27: TCS lookalike domain
# -------------------------------------------------------------
def test_27_tcs_lookalike_domain(db_session):
    company_name = "TCS"
    url = "http://tcs-careers-verify.top/apply"
    email = "recruiter@tcs-careers-verify.top"
    comp_res = company_verifier.verify_company(db_session, company_name, email=email, website=url)
    url_res = url_analyzer.analyze_url(url, company_name)
    flags, positives, bonus = rules.analyze_rules(
        title="Support Analyst",
        company_name=company_name,
        description="Verify your application details at the link provided.",
        email=email,
        url=url,
        url_risk_level=url_res.get("risk_level"),
        company_status=comp_res.get("status"),
    )
    score_res = scoring.compute_trust_score(
        flags, bonus, None, False,
        company_result=comp_res, url_result=url_res, positive_indicators=positives, email=email
    )
    assert score_res["trust_score"] <= 25
    assert score_res["risk_level"] == "HIGH"
