"""Generate a synthetic DEMO training dataset for AI JobShield."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAM_TEMPLATES = [
    "URGENT hiring! Work from home and earn {salary}/day. No interview needed. Pay registration fee of {fee} via UPI to join. Contact on WhatsApp {phone} only.",
    "Guaranteed internship at {company}. Instant selection, no experience required. Transfer security deposit {fee} to start training. Email HR at {email}.",
    "Earn {salary} per month from home typing jobs. Limited seats! Apply within 24 hours. Send Aadhaar and PAN copy to {email}. Telegram only: {phone}.",
    "Congratulations you are selected for {role} at {company}. Pay processing fee {fee} in gift cards to confirm. No interview. Message on WhatsApp.",
    "Part-time online job. Easy money {salary}/day. Send bank details and OTP to verify account. Contact {email}. Final warning – seats filling fast!!!",
    "Freelance data entry. Earn {salary} weekly. Pay training fee {fee} first. Company email: {email}. Apply immediately or lose opportunity.",
    "Crypto trading internship – guaranteed profits {salary}/month. Invest {fee} to get started. Contact via Telegram only. No experience needed.",
    "{company} is hiring {role}. Registration fee required before joining. WhatsApp HR {phone}. Earn from home without interview.",
    "Work online as {role}. Unrealistic pay {salary}/day. Share passport and bank account details for onboarding. Email {email}.",
    "Urgent: government scheme job. Pay application fee {fee}. Selection guaranteed. Contact personal Gmail {email}. Limited time offer!!!",
]

LEGIT_TEMPLATES = [
    "We are hiring a {role} at {company}. Responsibilities include collaborating with the product team, writing clean code, and participating in code reviews. Qualifications: degree in CS or related field, knowledge of Python/JavaScript. Salary range {salary} LPA based on experience. Interview process: online assessment, technical round, HR round. Apply via careers@{domain} or visit https://www.{domain}/careers.",
    "{company} seeks an intern for {role}. You will assist with documentation, testing, and learning industry practices under mentorship. Stipend {salary}/month. Required: currently enrolled student, basic communication skills. Selection via resume shortlist and interview. Official email: hr@{domain}. Location: {location}.",
    "Opening for {role} at {company}. Key responsibilities: customer support, ticket handling, and process improvement. Qualifications: graduation, good English, CRM familiarity preferred. CTC {salary} LPA. Multi-round interview including manager discussion. Apply at https://careers.{domain}/jobs. Contact: talent@{domain}.",
    "{company} is looking for a {role}. Role involves data analysis, reporting, and stakeholder communication. Requirements: SQL, Excel, statistics basics. Competitive salary {salary} LPA with benefits. Process: written test + interview. Website: https://www.{domain}. Email: jobs@{domain}. Location {location}.",
    "Full-time {role} position at {company}. Responsibilities include designing features, mentoring juniors, and shipping releases. Must-have skills: relevant experience, problem solving. Compensation {salary} LPA + benefits. Structured interviews: coding, system design, culture fit. Apply through https://www.{domain}/careers. HR: recruit@{domain}.",
    "Internship opportunity – {role} with {company}. Learn real projects, attend weekly reviews, submit a final presentation. Stipend {salary} per month. Eligibility: 3rd/4th year students. Selection through application form and interview. Contact internship@{domain}. No fees required at any stage.",
    "{company} hiring {role} in {location}. Duties: market research, presentation prep, coordination with sales. Qualifications listed on JD. Salary band {salary} LPA. Interview schedule shared after shortlisting. Official domain email careers@{domain}. HTTPS careers page available.",
    "Join {company} as {role}. You will own modules end-to-end, write tests, and document APIs. Requirements: degree, 0-2 years experience, Git proficiency. Package {salary} LPA. Transparent selection: OA → technical → HR. Email: hiring@{domain}. Visit https://www.{domain}.",
]

COMPANIES_LEGIT = [
    ("Infosys", "infosys.com"),
    ("Tata Consultancy Services", "tcs.com"),
    ("Wipro", "wipro.com"),
    ("Accenture", "accenture.com"),
    ("Zoho", "zoho.com"),
    ("Freshworks", "freshworks.com"),
    ("Mindtree", "mindtree.com"),
    ("Capgemini", "capgemini.com"),
]
COMPANIES_SCAM = [
    ("Global Opportunity Hub", "gmail.com"),
    ("Quick Cash Careers", "yahoo.com"),
    ("Prime Earn Online", "outlook.com"),
    ("Dream Job Express", "hotmail.com"),
    ("Instant Hire India", "gmail.com"),
]
ROLES = [
    "Software Engineer",
    "Data Analyst Intern",
    "Marketing Intern",
    "Customer Support Executive",
    "Backend Developer",
    "HR Assistant",
    "Business Analyst",
    "QA Tester",
]
LOCATIONS = ["Bengaluru", "Hyderabad", "Pune", "Chennai", "Remote", "Mumbai", "Noida"]


def _row(text: str, label: int) -> dict:
    return {"text": text, "label": label, "source": "DEMO_SYNTHETIC"}


def generate(n: int = 400, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    half = n // 2

    for i in range(half):
        company, domain = rng.choice(COMPANIES_SCAM)
        role = rng.choice(ROLES)
        salary = rng.choice(["5000", "8000", "15000", "25000", "50000"])
        fee = rng.choice(["999", "1499", "2999", "4999", "500"])
        phone = f"+91{rng.randint(7000000000, 9999999999)}"
        email = f"hr{rng.randint(1,99)}@{domain}"
        tpl = rng.choice(SCAM_TEMPLATES)
        text = tpl.format(
            company=company, role=role, salary=salary, fee=fee, phone=phone, email=email
        )
        rows.append(_row(text, 1))

    for i in range(n - half):
        company, domain = rng.choice(COMPANIES_LEGIT)
        role = rng.choice(ROLES)
        salary = rng.choice(["3-5", "4-6", "6-10", "8-12", "10-15", "15000", "20000"])
        location = rng.choice(LOCATIONS)
        tpl = rng.choice(LEGIT_TEMPLATES)
        text = tpl.format(
            company=company,
            domain=domain,
            role=role,
            salary=salary,
            location=location,
        )
        rows.append(_row(text, 0))

    rng.shuffle(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate DEMO synthetic training data")
    parser.add_argument("--out", default=str(ROOT / "data" / "demo_training_data.csv"))
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = generate(args.n, args.seed)

    with out.open("w", newline="", encoding="utf-8") as f:
        f.write("# DEMO SYNTHETIC DATASET – for local mini-project training only.\n")
        f.write("# Metrics from this data do NOT represent real-world performance.\n")
        f.write("# Columns: text,label,source  (label: 1=suspicious, 0=legitimate)\n")
        writer = csv.DictWriter(f, fieldnames=["text", "label", "source"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
