"""Build training_data_v2.csv with multi-category diversity and provenance tracking."""
from __future__ import annotations

import csv
import hashlib
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "data" / "training_data_v2.csv"

# Random seed for strict reproducibility
SEED = 42
rng = random.Random(SEED)

# ----------------------------------------------------------------------
# Entity Pools for Substitution
# ----------------------------------------------------------------------
COMPANIES = [
    "Tata Consultancy Services", "Infosys", "Wipro", "HCL Tech", "Tech Mahindra",
    "Cognizant", "Accenture", "Capgemini", "IBM India", "Larsen & Toubro Infotech",
    "Zoho Corporation", "Freshworks", "Razorpay", "PhonePe", "Paytm",
    "Flipkart", "Amazon India", "Microsoft India", "Google India", "Swiggy",
    "Zomato", "Jio Platforms", "Airtel Digital", "Cred", "Zerodha",
    "Apex Solutions", "Global Connect", "QuickHire India", "BrightPath Services",
    "Prime Talent Group", "Digital Dynamics", "NextGen Infotech", "Starlight Media",
    "Vertex Global", "Universal Staffing", "Elite Systems", "Zenith Corp",
    "Vanguard Technologies", "Alpha Star Innovations", "Horizon Ventures",
]

DOMAINS = [
    "tcs.com", "infosys.com", "wipro.com", "hcl.com", "techmahindra.com",
    "cognizant.com", "accenture.com", "capgemini.com", "ibm.com", "zoho.com",
    "freshworks.com", "razorpay.com", "phonepe.com", "flipkart.com", "amazon.com",
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com",
    "protonmail.com", "careers-portal.net", "quickjob.co", "recruitment-hub.top",
]

LOCATIONS = [
    "Bengaluru", "Hyderabad", "Pune", "Chennai", "Mumbai", "Noida", "Gurugram",
    "Kolkata", "Ahmedabad", "Kochi", "Coimbatore", "Chandigarh", "Jaipur", "Remote",
    "Hybrid (Bengaluru)", "Hybrid (Pune)", "Remote (India)",
]

# ----------------------------------------------------------------------
# SCAM GENERATORS (By Step 7 Taxonomy)
# ----------------------------------------------------------------------

SCAM_SPECS = [
    # 1. SCAM_FEE: Registration / Application Fee
    {
        "category": "SCAM_FEE",
        "source": "CURATED_FEE_SCAM",
        "group_prefix": "scam_fee",
        "templates": [
            "Urgent hiring for {role} at {company}. Work from home and earn {salary}. Immediate joining guaranteed. A non-refundable application fee of {fee} is required to process your candidate registration. Pay via UPI or Google Pay to activate your candidate profile. Send payment receipt to {email} or WhatsApp {phone}.",
            "{company} invites applications for {role} in {location}. Selected candidates must pay a mandatory registration fee of {fee} for document verification and interview scheduling. Payment must be made prior to technical screening. Contact HR at {email}.",
            "Hiring freshers and experienced candidates for {role}. 100% placement guaranteed without examination. Candidates need to deposit {fee} processing charge towards examination enrollment. Apply via {email} or call {phone}.",
            "Direct recruitment drive by {company} for {role}. Package: {salary}. To confirm your interview slot, transfer registration fee of {fee} to our recruitment partner account. Contact recruitment team at {email}.",
            "Immediate vacancy: {role}. Earn {salary} working part-time. No interview required. Pay an onboarding enrollment fee of {fee} to receive your starter employment kit. Message HR on WhatsApp {phone}.",
        ],
        "roles": ["Data Entry Operator", "Back Office Executive", "Online Form Filler", "HR Assistant", "Customer Support Executive", "Junior Computer Operator", "Accounts Clerk"],
        "salaries": ["₹25,000 - ₹35,000 per month", "₹4,000 per week", "₹1,500 daily", "₹5 Lakhs per annum"],
        "fees": ["₹750", "₹1,200", "₹1,500", "₹2,499", "₹3,000", "₹950"],
    },

    # 2. SCAM_DEPOSIT: Security / Equipment Deposit
    {
        "category": "SCAM_DEPOSIT",
        "source": "CURATED_DEPOSIT_SCAM",
        "group_prefix": "scam_deposit",
        "templates": [
            "{company} is hiring remote {role}. We provide a corporate laptop, monitor, and high-speed Wi-Fi setup. Selected candidates must pay a 100% refundable security deposit of {fee} before courier dispatch of IT equipment. Deposit will be reimbursed with your first month salary. Contact logistics at {email}.",
            "Work from home opportunity for {role} at {company}. Due to company policy, a refundable hardware collateral deposit of {fee} is required for company asset allocation. Send proof of transfer to {email}.",
            "Selected for remote {role} at {company}. Candidate must submit an initial training and software tool security deposit of {fee}. The deposit guarantees your workstation setup and will be credited back upon completion of 14-day training. WhatsApp {phone}.",
            "Executive Trainee - {role} position. Candidates are required to make a refundable security deposit of {fee} towards background screening and asset tracking. Forward transaction ID to {email}.",
        ],
        "roles": ["Remote Administrative Assistant", "Software Quality Tester", "Content Moderator", "Junior Python Developer", "Customer Operations Representative"],
        "salaries": ["₹30,000 - ₹45,000 per month", "₹6,00,000 per annum", "₹35,000 per month"],
        "fees": ["₹3,500", "₹4,999", "₹5,500", "₹8,000", "₹2,500"],
    },

    # 3. SCAM_CHECK: Fake Check / Equipment Vendor Reimbursement
    {
        "category": "SCAM_CHECK",
        "source": "CURATED_CHECK_SCAM",
        "group_prefix": "scam_check",
        "templates": [
            "We are pleased to offer you the position of {role} at {company}. You will receive a corporate advance check of {salary} to purchase your home office equipment from our approved vendor. You must deposit the check in your personal bank account and wire {fee} to our vendor immediately for equipment dispatch.",
            "Remote {role} position. Our finance department will send you an electronic check for office setup. Once cleared, you will wire payment to our verified equipment supplier. Send bank details and mailing address to {email}.",
            "Offer letter confirmed for {role}. A corporate equipment check has been issued to you. Please deposit the check and transfer {fee} via wire transfer or money order to our certified IT hardware logistics partner. Contact HR: {email}.",
        ],
        "roles": ["Virtual Executive Assistant", "Remote Project Coordinator", "Data Analyst", "Operations Specialist"],
        "salaries": ["$2,500", "$3,800", "₹1,50,000", "$4,200"],
        "fees": ["$1,800", "$2,200", "₹85,000", "$3,000"],
    },

    # 4. SCAM_TASK: Task / Commission / Like-and-Earn
    {
        "category": "SCAM_TASK",
        "source": "CURATED_TASK_SCAM",
        "group_prefix": "scam_task",
        "templates": [
            "Part-time online job! Earn {salary} daily simply by rating hotels, reviewing Google maps, and liking YouTube videos. Work 1-2 hours from mobile. Daily payout directly to your UPI/bank. Contact our recruitment manager on Telegram @{telegram_user} to start your first task today!",
            "Earn extra income from home! Complete simple online product rating tasks and earn {salary} commission per day. Immediate withdrawal. No technical experience required. Join our official Telegram task group @{telegram_user} now.",
            "Freelance Digital Promoter: Earn {salary} daily for liking posts and subscribing to channels. Payout credited every evening. Sign up now on Telegram {phone} to receive your daily task assignments.",
            "Part-time movie review and app testing job. Earn {salary} for reviewing 15 applications daily. Immediate payment on task completion. Reach coordinator on WhatsApp {phone} or Telegram @{telegram_user}.",
        ],
        "roles": ["Digital Media Rater", "Online Task Associate", "Social Media Promoter", "App Reviewer", "Product Feedback Specialist"],
        "salaries": ["₹2,000 - ₹5,000", "₹3,500", "₹1,500 - ₹4,000", "₹5,000"],
        "fees": ["0"],
    },

    # 5. SCAM_CRYPTO: Crypto Investment / Wallet Task Scam
    {
        "category": "SCAM_CRYPTO",
        "source": "CURATED_CRYPTO_SCAM",
        "group_prefix": "scam_crypto",
        "templates": [
            "Crypto Arbitrage Operations Intern at {company}. Work from home managing automated crypto trading tasks. Earn {salary} daily. To activate your merchant trading account, deposit {fee} in USDT to your assigned company smart contract wallet. Guaranteed 20% daily return. Contact via Telegram @{telegram_user}.",
            "Digital Asset Optimization Specialist: Execute simulated buy/sell orders on our decentralized exchange portal. Deposit {fee} in cryptocurrency as initial liquidity collateral to start receiving high-yield commissions. Message on Telegram.",
            "Crypto Trading Assistant: Earn {salary} per week. Candidates must connect personal Web3 wallet and transfer an initial gas verification fee of {fee} to receive automated trading allocations. Join Telegram channel @{telegram_user}.",
        ],
        "roles": ["Crypto Operations Intern", "Digital Asset Trader", "Web3 Task Specialist", "Blockchain Operations Assistant"],
        "salaries": ["$200 - $500 daily", "₹8,000 daily", "₹50,000 weekly"],
        "fees": ["100 USDT", "250 USDT", "₹5,000", "$150 in ETH"],
    },

    # 6. SCAM_NO_INT: Direct Offer / Instant Selection Without Interview
    {
        "category": "SCAM_NO_INT",
        "source": "CURATED_NO_INTERVIEW_SCAM",
        "group_prefix": "scam_no_int",
        "templates": [
            "Congratulations! Your resume has been shortlisted and you are directly selected for the post of {role} at {company}. Salary: {salary}. No interview required. Direct appointment letter will be issued upon payment of documentation charges {fee}. Contact HR on WhatsApp {phone}.",
            "Direct selection notification from {company}. You have been appointed as {role} based on your job portal profile. No written test or interview. Pay document verification charge of {fee} to download your official joining letter. Email: {email}.",
            "Urgent recruitment: Direct joining for {role} at {company}. Zero interview rounds, immediate joining tomorrow. Candidates must transfer {fee} gate pass fee before reporting. Reach out on WhatsApp {phone}.",
        ],
        "roles": ["Computer Operator", "Junior Accountant", "Administrative Clerk", "Store Incharge", "Billing Executive"],
        "salaries": ["₹35,000 per month", "₹4.5 LPA", "₹28,000 per month"],
        "fees": ["₹1,850", "₹2,200", "₹3,100", "₹1,500"],
    },

    # 7. SCAM_CRED: Credential Phishing (OTP, PIN, Password)
    {
        "category": "SCAM_CRED",
        "source": "CURATED_CREDENTIAL_SCAM",
        "group_prefix": "scam_cred",
        "templates": [
            "Dear candidate, to activate your payroll direct deposit for {role} at {company}, our verification bot will send an OTP to your registered mobile number. Please share the 6-digit OTP and your netbanking password with our HR representative at {email} to verify your bank account.",
            "Employment verification alert: To process your appointment letter for {role}, confirm your bank account ownership by providing your debit card CVV and ATM PIN for pre-authorization. Email details to {email}.",
            "Candidate onboarding portal setup: Please provide your online banking login credentials or forward the OTP received on your mobile to complete candidate identity authentication. Send via WhatsApp {phone}.",
        ],
        "roles": ["Accounts Assistant", "Payroll Clerk", "Finance Executive", "Backend Associate"],
        "salaries": ["₹30,000 per month", "₹4 LPA"],
        "fees": ["0"],
    },

    # 8. SCAM_DOCS: Identity Harvesting via WhatsApp before interview
    {
        "category": "SCAM_DOCS",
        "source": "CURATED_DOCS_SCAM",
        "group_prefix": "scam_docs",
        "templates": [
            "{company} is hiring {role}. Before scheduling your interview, you must immediately send clear color photos of your original Aadhaar card, PAN card, and 6 months bank account statements via WhatsApp to {phone}. Failure to submit documents will result in cancellation of candidature.",
            "Immediate vacancy for {role}. To qualify for selection, email high-resolution scans of your passport, driver's license, and cancelled cheque to {email}. Do not apply if you cannot provide identity proofs immediately.",
            "Direct hiring drive: Send front and back photos of your Aadhaar card and PAN card along with personal selfie to WhatsApp number {phone} for instant interview pass issuance.",
        ],
        "roles": ["HR Assistant", "Data Entry Specialist", "Telecaller", "Field Sales Executive"],
        "salaries": ["₹20,000 - ₹30,000 per month", "₹3.5 LPA"],
        "fees": ["0"],
    },

    # 9. SCAM_SALARY: Unrealistic Low-Skill Salary
    {
        "category": "SCAM_SALARY",
        "source": "CURATED_SALARY_SCAM",
        "group_prefix": "scam_salary",
        "templates": [
            "Huge opening! Earn {salary} simply by copying and pasting text into Word documents. No qualification needed, anyone can do it. Housewives, students, and freshers welcome. Guaranteed daily payment. Contact immediately on WhatsApp {phone}.",
            "Online SMS sending and captcha typing job. Earn {salary} working just 2 hours from home. No experience, no interview. Payout transferred daily to Google Pay / PhonePe. Message on WhatsApp {phone}.",
            "Earn {salary} monthly for simple handwriting and page typing work. Materials will be sent to your home address. Registration open for limited candidates only. Email {email}.",
        ],
        "roles": ["Data Entry Operator", "SMS Sending Executive", "Captcha Solver", "Form Filling Specialist", "Typing Assistant"],
        "salaries": ["₹5,000 - ₹10,000 daily", "₹1,50,000 per month", "₹8,000 per day", "₹25,000 weekly"],
        "fees": ["0"],
    },

    # 10. SCAM_URGENT: Coercive Urgency & Pressure
    {
        "category": "SCAM_URGENT",
        "source": "CURATED_URGENCY_SCAM",
        "group_prefix": "scam_urgent",
        "templates": [
            "FINAL WARNING: Your application for {role} at {company} will be permanently cancelled within 2 hours unless you pay the security clearance fee of {fee}. Only 2 seats remaining! Transfer payment immediately to UPI id hr-verify@upi and message on WhatsApp {phone}.",
            "URGENT NOTICE: Last chance to claim your appointment letter for {role}. Pay mandatory verification charge {fee} before 6:00 PM today or your vacancy will be reallocated to waitlisted candidates. Contact {email}.",
            "Immediate action required! Selection confirmed for {role}. Pay processing fee of {fee} within 30 minutes to reserve your joining date. Delay will result in immediate disqualification. Call {phone}.",
        ],
        "roles": ["Operations Assistant", "Customer Support Associate", "Billing Executive", "Office Coordinator"],
        "salaries": ["₹30,000 per month", "₹4 LPA"],
        "fees": ["₹1,499", "₹2,500", "₹999", "₹3,500"],
    },

    # 11. SCAM_EVASION: Diluted Enterprise Scam (Realistic JD with Fee Tail)
    {
        "category": "SCAM_FEE",
        "source": "CURATED_EVASION_SCAM",
        "group_prefix": "scam_evasion",
        "templates": [
            "{company} is seeking an experienced {role} in {location}. Responsibilities: Architect enterprise distributed applications, participate in code reviews, optimize database queries, and ensure adherence to agile principles. Qualifications: Bachelor's degree in Computer Science, 4+ years of hands-on experience with modern frameworks, microservices architecture, and CI/CD pipelines. Competitive compensation: {salary} with health insurance and retirement plans. Note: Selected candidates must pay a mandatory third-party candidate background proctoring fee of {fee} prior to technical interview scheduling. Submit fee receipt to {email}.",
            "Exciting career opportunity at {company} for {role}. We are looking for an analytical professional to lead cross-functional product initiatives. Requirements include Bachelor/Master degree, 3+ years experience in business analysis, SQL, and agile methodologies. Compensation: {salary}. As part of company onboarding governance, candidates are required to deposit a refundable asset tracking fee of {fee} for workstation logistics. Apply via {email}.",
            "{company} announces its annual graduate intake for {role}. Selection rounds: Round 1 Online Aptitude, Round 2 Technical Assessment, Round 3 Management Discussion. Eligibility: B.Tech / MCA graduates with minimum 65% aggregate. To activate your proctored assessment portal slot, an examination administration charge of {fee} must be transferred to our accredited testing vendor. Email payment confirmation to {email}.",
        ],
        "roles": ["Senior Software Engineer", "Business Systems Analyst", "DevOps Cloud Engineer", "Graduate Technical Trainee"],
        "salaries": ["₹14 - ₹20 LPA", "₹10 - ₹16 LPA", "₹7 LPA", "₹18 LPA"],
        "fees": ["₹1,250", "₹2,500", "₹950", "₹3,000"],
    },
]

# ----------------------------------------------------------------------
# LEGITIMATE GENERATORS (By Step 7 Taxonomy & Hard Negatives)
# ----------------------------------------------------------------------

LEGIT_SPECS = [
    # 1. LEGIT_CORP: Enterprise IT & Software Engineering
    {
        "category": "LEGIT_CORP",
        "source": "CURATED_ENTERPRISE_LEGIT",
        "group_prefix": "legit_corp",
        "templates": [
            "{company} is hiring a {role} in {location}. Key responsibilities include designing scalable cloud backend services, writing robust automated unit and integration tests, and collaborating with cross-functional product teams. Qualifications: Bachelor's degree in Computer Science or related field, 3-6 years of experience with Python, Go, or Java, strong knowledge of distributed systems, and Git workflow. Compensation: {salary} plus comprehensive medical insurance, annual performance bonus, and retirement savings. Selection process involves an online coding assessment, two technical rounds, and an HR discussion. Apply via our official careers portal https://www.{domain}/careers or send CV to careers@{domain}.",
            "Opportunity for {role} at {company}. Responsibilities: Maintain enterprise web applications, optimize REST API response times, and participate in daily agile standups. Required skills: Bachelor of Engineering, proficiency in React, TypeScript, and Node.js, and solid debugging skills. CTC: {salary} based on experience. Interview schedule: Technical screening followed by architecture interview and director round. Submit profile through https://careers.{domain}/jobs.",
            "Join {company} as {role}. You will own feature delivery from conception to deployment on AWS cloud infrastructure. Requirements: 2-5 years software engineering experience, Docker, Kubernetes, CI/CD pipelines, and relational database design. Salary band: {salary} with employee stock options. Send resume to talent-acquisition@{domain}.",
            "{company} is looking for a talented {role} to join our engineering division in {location}. You will design high-throughput data processing workflows, ensure system reliability, and mentor junior engineers. Requirements: B.Tech/M.Tech in CS or IT, 5+ years experience. Compensation: {salary}. Selection is purely merit-based through technical coding evaluations. Apply at https://www.{domain}/careers.",
        ],
        "roles": ["Senior Backend Developer", "Full Stack Engineer", "Cloud Infrastructure Engineer", "DevOps Engineer", "Frontend Software Engineer", "Site Reliability Engineer"],
        "salaries": ["12-18 LPA", "15-22 LPA", "18-28 LPA", "8-14 LPA", "20-30 LPA"],
    },

    # 2. LEGIT_START: Early-Stage Startup Roles (Lean / Brief JDs)
    {
        "category": "LEGIT_START",
        "source": "CURATED_STARTUP_LEGIT",
        "group_prefix": "legit_start",
        "templates": [
            "We are a fast-growing venture-backed startup seeking a {role} in {location}. We build developer productivity tools. You will work directly with the founders to ship rapid iterations. Must have strong fundamentals in Python or Go, ability to work independently, and passion for product craftsmanship. Competitive salary {salary} plus generous equity. Send your GitHub and resume to founders@{domain}.",
            "Hiring a {role} to build our early product. Remote friendly. We care about shipping fast, clean architecture, and customer focus. Experience with React, Node, and PostgreSQL preferred. Compensation: {salary}. Let's chat: jobs@{domain}.",
            "Early-stage fintech startup looking for a {role}. You'll own our core mobile experience. Requirements: 2+ years Flutter/React Native experience. Salary: {salary} + 0.5% equity. Apply directly at careers@{domain}.",
        ],
        "roles": ["Founding Engineer", "Full Stack Developer", "Mobile Engineer", "Product Designer", "Growth Engineer"],
        "salaries": ["10-18 LPA", "15-25 LPA", "8-15 LPA", "Competitive + Equity"],
    },

    # 3. LEGIT_BPO: Customer Support & Operations
    {
        "category": "LEGIT_BPO",
        "source": "CURATED_BPO_LEGIT",
        "group_prefix": "legit_bpo",
        "templates": [
            "{company} is hiring a {role} in {location}. Responsibilities include addressing customer queries via email, phone, and chat, resolving escalation tickets, and maintaining high customer satisfaction metrics. Qualifications: Any graduate degree, excellent English communication skills, and customer service orientation. Rotational shifts with company transport provided. Salary: {salary} with shift allowances and medical coverage. Interview rounds: Voice assessment, HR interview, and operations manager discussion. Apply at https://www.{domain}/careers.",
            "Opening for {role} at {company}. Responsibilities: Provide technical support for enterprise SaaS clients, diagnose software issues, and log bug reports. Requirements: Graduation in any stream, 1-3 years BPO/customer service experience. Compensation: {salary}. Walk-in or email resume to hr@{domain}.",
        ],
        "roles": ["Customer Support Representative", "Technical Support Associate", "Client Success Specialist", "Operations Executive"],
        "salaries": ["3.5 - 5.5 LPA", "4.0 - 6.0 LPA", "₹25,000 - ₹35,000 per month"],
    },

    # 4. LEGIT_REMOTE: Authentic Remote Work
    {
        "category": "LEGIT_REMOTE",
        "source": "CURATED_REMOTE_LEGIT",
        "group_prefix": "legit_remote",
        "templates": [
            "{company} is looking for a Remote {role}. We operate as a 100% distributed team across India. You will design scalable web microservices, participate in asynchronous code reviews, and write technical specifications. Requirements: 3+ years backend development experience, self-motivated with strong written communication skills. Compensation: {salary} with home office setup stipend and health coverage. Hiring process: Take-home coding exercise followed by video technical interview. Apply at https://www.{domain}/careers.",
            "Fully remote opening for {role} at {company}. Work flexible hours from anywhere. Responsibilities: Manage automated testing suites and CI/CD pipelines. Qualifications: BS in Computer Science, experience with Cypress and Playwright. Package: {salary}. Send CV to remote-jobs@{domain}.",
        ],
        "roles": ["Remote Backend Developer", "Remote QA Automation Engineer", "Remote Technical Writer", "Remote Data Analyst"],
        "salaries": ["10-16 LPA", "14-22 LPA", "8-12 LPA"],
    },

    # 5. HARD NEGATIVE: LEGIT_FINTECH (Payment Gateway & Wire Transfers)
    {
        "category": "LEGIT_FINTECH",
        "source": "CURATED_HARD_NEGATIVE",
        "group_prefix": "hard_neg_fintech",
        "templates": [
            "{company} is hiring a {role} in {location}. You will design and implement mission-critical payment gateway systems, process millions of daily credit card transactions, integrate instant bank transfer APIs via IMPS/NEFT, and build automated reconciliation pipelines. Qualifications: Bachelor's in CS, 4+ years of backend Java/Python experience, in-depth understanding of PCI-DSS compliance, banking APIs, and financial transaction settlement protocols. Salary compensation: {salary} with performance incentives. Multi-round technical interview: System design, coding evaluation, and hiring manager round. Apply via official portal https://www.{domain}/careers.",
            "Exciting opening for {role} at {company}. The candidate will engineer secure payment infrastructure, manage bank account verification workflows, optimize payment processing routing algorithms, and prevent transaction fraud across multi-currency payment rails. Requirements: Strong experience in distributed systems, REST APIs, and core banking integration. Package: {salary}. Apply at careers@{domain}.",
            "{company} Payment Solutions division is looking for a {role}. Responsibilities: Develop secure microservices for wire transfers, automated merchant settlements, and wallet credit disbursements. Must have 3+ years experience in payment services or fintech. CTC: {salary}. Official domain application: https://www.{domain}.",
            "Senior Backend Engineer - Payments at {company}. Build high-throughput financial transaction engines handling bank transfers, card payments, and UPI payment rails. Experience with idempotency, distributed databases, and high availability required. Compensation: {salary}. Contact: payments-hiring@{domain}.",
        ],
        "roles": ["Payment Operations Engineer", "Fintech Backend Developer", "Payment Gateway Architect", "Financial Transaction Systems Lead"],
        "salaries": ["18-28 LPA", "22-35 LPA", "25-40 LPA", "16-24 LPA"],
    },

    # 6. HARD NEGATIVE: LEGIT_BANK (Banking Operations & Account Reconciliation)
    {
        "category": "LEGIT_BANK",
        "source": "CURATED_HARD_NEGATIVE",
        "group_prefix": "hard_neg_bank",
        "templates": [
            "{company} is seeking an experienced {role} in {location}. Key responsibilities: Reconcile daily customer bank account balances, investigate transaction discrepancies, audit general ledgers, and manage automated clearinghouse entries. Requirements: Degree in Finance, Commerce, or Accounting, 3+ years banking operations experience, and thorough knowledge of banking reconciliation software. Compensation: {salary} plus banking benefits. Application process: Written aptitude test followed by technical accounting interview. Submit profile to banking-careers@{domain}.",
            "Opening for {role} in our Corporate Banking division at {company}. The role involves auditing corporate customer bank accounts, validating credit facilities, processing wire transfers for institutional clients, and generating compliance reports. Qualifications: MBA Finance or CA Inter, 2-5 years experience. Salary band: {salary}. Official portal: https://www.{domain}/careers.",
            "Financial Operations Analyst at {company}. Responsible for daily bank account reconciliations, monitoring payment settlements, resolving merchant chargebacks, and ensuring compliance with regulatory accounting guidelines. Package: {salary}. Apply at careers@{domain}.",
        ],
        "roles": ["Banking Operations Analyst", "Account Reconciliation Specialist", "Corporate Banking Associate", "Senior Financial Auditor"],
        "salaries": ["6-10 LPA", "8-14 LPA", "7-12 LPA"],
    },

    # 7. HARD NEGATIVE: LEGIT_CRYPTO (Blockchain & Web3 Protocol Engineering)
    {
        "category": "LEGIT_CRYPTO",
        "source": "CURATED_HARD_NEGATIVE",
        "group_prefix": "hard_neg_crypto",
        "templates": [
            "{company} is looking for a {role} to build institutional blockchain infrastructure. You will design smart contracts in Solidity, develop cryptographic wallet custody protocols, audit decentralized protocol security, and test token settlement smart contracts on Ethereum testnets. Requirements: Bachelor's degree in Computer Science, solid cryptography fundamentals, and 2+ years of hands-on Web3 experience. Compensation: {salary} + token allocations. Interviews: Technical architecture round and live coding test. Apply at https://www.{domain}/careers.",
            "Web3 Infrastructure Lead at {company}. Build high-throughput blockchain indexing engines and secure multi-signature crypto wallet custody solutions. Experience with distributed consensus algorithms, Rust, and Go required. Salary: {salary}. Send GitHub and resume to protocol-jobs@{domain}.",
            "{company} Labs is hiring a {role}. Responsibilities: Audit smart contracts, optimize decentralized exchange algorithms, and integrate blockchain APIs. Competitive package: {salary}. Submit application at careers@{domain}.",
        ],
        "roles": ["Blockchain Protocol Engineer", "Smart Contract Developer", "Web3 Security Engineer", "Crypto Infrastructure Architect"],
        "salaries": ["25-45 LPA", "30-50 LPA", "20-35 LPA"],
    },

    # 8. HARD NEGATIVE: LEGIT_PAYROLL (Standard Payroll & Bank Account Credits)
    {
        "category": "LEGIT_PAYROLL",
        "source": "CURATED_HARD_NEGATIVE",
        "group_prefix": "hard_neg_payroll",
        "templates": [
            "{company} is hiring a {role} in {location}. The specialist will manage monthly payroll processing for 5,000+ employees, ensure accurate salary disbursements credited directly to employee bank accounts, administer Provident Fund and ESI deductions, and handle statutory tax filings. Requirements: 3-5 years corporate payroll experience with SAP HR or Workday. Salary: {salary}. Selection via interview rounds. Apply to hr-operations@{domain}.",
            "HR Operations & Payroll Lead at {company}. Oversee end-to-end employee compensation workflows, bank account salary transfers, bonus distribution, and payroll audit compliance. Qualifications: MBA HR or equivalent, 5+ years experience. Compensation: {salary}. Submit resume at https://www.{domain}/careers.",
            "Compensation & Benefits Analyst at {company}. Responsibilities include auditing monthly payroll registers, managing employee bank account updates for direct deposit, and preparing annual compensation reports. Salary: {salary}. Apply at careers@{domain}.",
        ],
        "roles": ["Payroll Operations Specialist", "Compensation & Benefits Lead", "HR Payroll Executive", "Corporate Compensation Analyst"],
        "salaries": ["7-11 LPA", "10-15 LPA", "6-9 LPA"],
    },

    # 9. HARD NEGATIVE: LEGIT_COMM (Auxiliary WhatsApp/Telegram for Logistics)
    {
        "category": "LEGIT_COMM",
        "source": "CURATED_HARD_NEGATIVE",
        "group_prefix": "hard_neg_comm",
        "templates": [
            "{company} is conducting campus recruitment for {role} across engineering colleges. Eligible candidates will receive written assessment links via official email. For venue directions, interview slot updates, and logistical coordination, our campus recruitment team has also established a verified WhatsApp Business helpdesk at {phone}. Note: All formal offers and appointments are issued exclusively through official corporate email careers@{domain}. CTC: {salary}. Register at https://www.{domain}/campus.",
            "{company} hiring drive for {role} in {location}. Candidates can track their interview schedule on our career portal https://www.{domain}/careers or join our official WhatsApp announcement group {phone} for physical venue directions on the day of the drive. No fees are charged at any stage. Salary package: {salary}.",
            "Developer Community Manager at {company}. Manage our global open-source developer relations, organize technical webinars, and engage with developers across GitHub, Discord, and our official Telegram developer community channel @{telegram_user}. Salary: {salary}. Apply via jobs@{domain}.",
        ],
        "roles": ["Campus Recruitment Candidate", "Graduate Engineer Trainee", "Developer Relations Specialist", "Technical Talent Coordinator"],
        "salaries": ["5-8 LPA", "6-10 LPA", "12-18 LPA"],
    },

    # 10. HARD NEGATIVE: LEGIT_SENIOR (Executive Senior Compensation)
    {
        "category": "LEGIT_SENIOR",
        "source": "CURATED_HARD_NEGATIVE",
        "group_prefix": "hard_neg_senior",
        "templates": [
            "{company} is seeking an exceptional {role} to lead our global cloud architecture. The candidate will define multi-region distributed system strategy, mentor 50+ senior engineers, and collaborate with executive leadership. Requirements: Bachelor/Master in CS, 10-15 years of industry experience, track record of architecting petabyte-scale distributed systems. Compensation package: {salary} plus significant equity grants. Rigorous executive interviews: Architecture deep-dive and board interview. Apply at https://www.{domain}/careers.",
            "Director of Software Engineering at {company}. Lead enterprise microservices transformation, oversee engineering budgets, and drive engineering excellence across multiple global business units. Qualifications: 12+ years experience in technical leadership. Compensation: {salary} + executive bonus. Contact: executive-search@{domain}.",
            "Principal Distributed Systems Architect at {company}. Lead next-generation storage and computing platforms. Required: 8+ years distributed systems expertise. Compensation: {salary}. Submit profile via https://www.{domain}/leadership.",
        ],
        "roles": ["Principal Software Architect", "Director of Engineering", "Chief Technology Officer", "Vice President of Engineering"],
        "salaries": ["45-70 LPA", "50-80 LPA", "60-90 LPA", "₹75 Lakhs per annum"],
    },
]

# ----------------------------------------------------------------------
# REAL-WORLD DOCUMENTED CASE STUDY PATTERNS (Indian Cybercrime Advisories)
# ----------------------------------------------------------------------
REAL_CASE_STUDIES = [
    # UPI Fee Scams
    ("URGENT: Tata Consultancy Services direct hiring for Data Entry Operator. Work from home. Monthly salary ₹35,000. Selected without interview. Transfer registration charge ₹1,499 via UPI to verify your candidature. Send screenshot to WhatsApp +919876543210.", 1, "REAL_CASE_STUDY", "SCAM_FEE", "real_case_upi_1"),
    ("Infosys Technologies HR drive: You are shortlisted for Back Office Executive role. Package ₹4.2 LPA. Pay document processing fee ₹1,850 via PhonePe/GPay to secure your employee ID card. Offer expires in 2 hours. WhatsApp +919812345678.", 1, "REAL_CASE_STUDY", "SCAM_FEE", "real_case_upi_2"),
    ("Wipro BPO recruitment. Part-time form filling. Earn ₹1,500 daily. Pay refundable software activation fee ₹999 to start work. Contact hr.wipro@gmail.com.", 1, "REAL_CASE_STUDY", "SCAM_FEE", "real_case_upi_3"),
    ("Direct selection letter from Reliance Jio. Selected as Customer Care Assistant. Monthly salary ₹28,000. Send ₹2,500 gate pass and medical clearance fee to bank account before joining date.", 1, "REAL_CASE_STUDY", "SCAM_FEE", "real_case_upi_4"),
    ("HCL Technologies: Direct joining without interview for Computer Operator. Pay security deposit ₹3,000 for training kit. Contact WhatsApp +919988776655.", 1, "REAL_CASE_STUDY", "SCAM_DEPOSIT", "real_case_deposit_1"),

    # Telegram Task Scams
    ("Part-time job offer: Earn ₹3,000 to ₹5,000 per day by rating hotels and restaurants on Google Maps. Complete 20 tasks daily. Instant payout to bank account. Join our official Telegram group @IndiaJobTasks now.", 1, "REAL_CASE_STUDY", "SCAM_TASK", "real_case_task_1"),
    ("YouTube Video Liking Job: Work from home. Earn ₹50 for every video liked. 30 videos per day = ₹1,500 daily income. Payment guaranteed via UPI every evening. Message coordinator on Telegram @EarnFastIndia.", 1, "REAL_CASE_STUDY", "SCAM_TASK", "real_case_task_2"),
    ("Amazon product review job: Earn handsome commission daily by boosting product ratings on merchant portal. Recharge wallet with ₹1,000 to receive high-tier tasks. Contact Telegram @AmazonTaskManager.", 1, "REAL_CASE_STUDY", "SCAM_TASK", "real_case_task_3"),
    ("Crypto task investment: Earn 30% daily return by depositing USDT into our trading smart contract pool. Instant withdrawals. Connect with our financial mentor on Telegram @CryptoCareerIndia.", 1, "REAL_CASE_STUDY", "SCAM_CRYPTO", "real_case_crypto_1"),

    # Identity Extortion
    ("Urgent hiring for Amazon packing and scanning jobs. Earn ₹25,000/month. No interview. Send clear photo of Aadhaar card, PAN card, and bank passbook to WhatsApp +919123456780 to receive your joining letter today.", 1, "REAL_CASE_STUDY", "SCAM_DOCS", "real_case_docs_1"),
    ("Flipkart delivery and data entry vacancies. Send front and back photos of your Aadhaar card and live selfie on WhatsApp +919876501234 for instant job allocation.", 1, "REAL_CASE_STUDY", "SCAM_DOCS", "real_case_docs_2"),
]


def generate_dataset() -> list[dict]:
    """Generate balanced, leakage-resistant dataset with metadata."""
    rows: list[dict] = []

    # 1. Real Case Studies
    for text, label, source, category, group_id in REAL_CASE_STUDIES:
        rows.append({
            "text": text,
            "label": label,
            "source": source,
            "category": category,
            "group_id": group_id,
        })

    # 2. SCAM Categories (~1,650 samples across 11 categories)
    target_scam_per_spec = 150
    for spec in SCAM_SPECS:
        cat = spec["category"]
        src = spec["source"]
        prefix = spec["group_prefix"]
        templates = spec["templates"]
        roles = spec["roles"]
        salaries = spec["salaries"]
        fees = spec.get("fees", ["₹1,500"])

        for t_idx, tpl in enumerate(templates):
            group_id = f"{prefix}_tpl{t_idx}"
            samples_for_tpl = target_scam_per_spec // len(templates) + 5
            for s_idx in range(samples_for_tpl):
                company = rng.choice(COMPANIES)
                domain = rng.choice(DOMAINS)
                role = rng.choice(roles)
                salary = rng.choice(salaries)
                fee = rng.choice(fees)
                location = rng.choice(LOCATIONS)
                phone = f"+91{rng.randint(7000000000, 9999999999)}"
                email = f"recruitment@{domain}" if "gmail" not in domain else f"hr.{role.lower().replace(' ', '')}{rng.randint(10,99)}@{domain}"
                tg_user = f"Hire_{company.split()[0]}_{rng.randint(100,999)}"

                text = tpl.format(
                    company=company,
                    domain=domain,
                    role=role,
                    salary=salary,
                    fee=fee,
                    location=location,
                    phone=phone,
                    email=email,
                    telegram_user=tg_user,
                )
                rows.append({
                    "text": text,
                    "label": 1,
                    "source": src,
                    "category": cat,
                    "group_id": group_id,
                })

    # 3. LEGITIMATE Categories (~1,700 samples across 10 categories)
    target_legit_per_spec = 170
    for spec in LEGIT_SPECS:
        cat = spec["category"]
        src = spec["source"]
        prefix = spec["group_prefix"]
        templates = spec["templates"]
        roles = spec["roles"]
        salaries = spec["salaries"]

        for t_idx, tpl in enumerate(templates):
            group_id = f"{prefix}_tpl{t_idx}"
            samples_for_tpl = target_legit_per_spec // len(templates) + 5
            for s_idx in range(samples_for_tpl):
                company = rng.choice(COMPANIES)
                domain = f"{company.lower().split()[0]}.com"
                role = rng.choice(roles)
                salary = rng.choice(salaries)
                location = rng.choice(LOCATIONS)
                phone = f"+91 {rng.randint(7000, 9999)} {rng.randint(100000, 999999)}"
                email = f"careers@{domain}"
                tg_user = f"{company.lower().split()[0]}_devs"

                text = tpl.format(
                    company=company,
                    domain=domain,
                    role=role,
                    salary=salary,
                    location=location,
                    phone=phone,
                    email=email,
                    telegram_user=tg_user,
                )
                rows.append({
                    "text": text,
                    "label": 0,
                    "source": src,
                    "category": cat,
                    "group_id": group_id,
                })

    return rows


def build_and_save():
    raw_rows = generate_dataset()
    print(f"Generated raw rows: {len(raw_rows)}")

    # Deduplication based on normalized text hash
    seen_hashes = set()
    clean_rows = []
    duplicates = 0

    for r in raw_rows:
        text = r["text"].strip()
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if h in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(h)
        clean_rows.append(r)

    print(f"Exact duplicates removed: {duplicates}")
    print(f"Clean rows: {len(clean_rows)}")

    # Save to CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "source", "category", "group_id"])
        writer.writeheader()
        writer.writerows(clean_rows)

    print(f"Saved dataset to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_and_save()
