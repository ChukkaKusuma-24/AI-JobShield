# Machine Learning Dataset Design Specification — AI-JobShield

## 1. Executive Summary

This document defines the architectural and operational specification for the target training dataset of AI-JobShield. It addresses the vulnerabilities identified during the Step 6 audit:
- 100% synthetic reliance on only 18 fixed templates
- Company name and email domain target leakage
- High false positive rate on legitimate fintech and payment roles
- High false negative rate (42.9% miss rate) on diluted scams and modern task scams
- Severe probability uncalibration (Brier score = 0.2185 on realistic cases)

---

## 2. Dataset Architecture & Target Scale

### 2.1 Target Scale
- **Total Samples**: **3,000 – 4,000 balanced samples**
  - **Class 0 (Legitimate)**: ~1,800 samples (50–55%)
  - **Class 1 (Scam / Fraudulent)**: ~1,600 samples (45–50%)

### 2.2 Data Sourcing Strategy
The target dataset must be constructed by fusing three distinct, validated sources:

1. **EMSCAD Real-World Open Corpus (Curated Subset)**:
   - Employment Scam Aegean Dataset (contains 17,880 real-world job postings).
   - Extract 800 verified fraudulent job postings across industries (administrative, data entry, customer care, sales).
   - Extract 1,000 verified authentic job postings across technical, commercial, and operational domains.
2. **Indian & Global Recruitment Scam Case Studies (Verified Real-World)**:
   - 400 verified recruitment scam incident postings collected from cybercrime advisories, recruitment fraud warnings, and reported job scam patterns (UPI deposit scams, Aadhaar/PAN extortion, Telegram task scams, fake interview letters from major IT services brands).
3. **Hard-Negative & Adversarial Domain Synthesis**:
   - 400 specialized legitimate postings (fintech, banking APIs, cryptocurrency/blockchain protocols, gift card operations, legitimate HR WhatsApp/campus coordination, and high-salary executive roles).
   - 400 modern evasion scam postings (keyword-diluted enterprise scams, refundable workstation deposits, task scams).

---

## 3. Class Taxonomy and Labeling Policy

### 3.1 Binary Label Definitions
- **`label = 0` (Legitimate)**:
  An authentic job posting or employment communication where the employer offers genuine employment, does not solicit upfront payments or banking credentials, does not assign deceptive task schemes, and conducts normal recruitment evaluations.
- **`label = 1` (Fraudulent / Scam)**:
  Any job posting, message, or offer designed to extort money from the applicant, steal credentials/identity documents, conduct task fraud, or deceive the candidate for unlawful gain.

### 3.2 Granular Category Taxonomy

#### SCAM Categories (`label = 1`):
| Category Code | Name | Description | Key Characteristic |
| :--- | :--- | :--- | :--- |
| `SCAM_FEE` | Registration / Application Fee | Requires applicant to pay before joining or interview | "Pay Rs 1,500 registration fee" |
| `SCAM_DEPOSIT` | Security / Equipment Deposit | Demands refundable deposit for laptop/training/materials | "Mandatory security deposit of Rs 3,500" |
| `SCAM_CHECK` | Fake Check / Vendor Scam | Mails corporate check and instructs applicant to wire funds | "Deposit our check and wire vendor fees" |
| `SCAM_TASK` | Task / Commission Scam | Pays daily commission for clicking links, YouTube likes | "Earn daily by completing 10 tasks on portal" |
| `SCAM_CRYPTO` | Crypto Investment Scam | Demands crypto deposit to start trading or receive salary | "Deposit USDT to activate corporate trading wallet" |
| `SCAM_NO_INT` | Instant Selection Scam | Guarantees placement or sends direct offer without interview | "Instant selection, direct joining letter" |
| `SCAM_CRED` | Credential Harvesting | Requests banking passwords, PIN, CVV, or OTP | "Send OTP to verify your account" |
| `SCAM_DOCS` | Identity Harvesting | Demands Aadhaar/PAN/Passport copy via WhatsApp before interview | "Send Aadhaar and PAN copy to WhatsApp HR" |
| `SCAM_SALARY` | Unrealistic Low-Skill Salary | Exorbitant daily or monthly payout for zero-skill work | "Rs 5,000/day for online data entry typing" |
| `SCAM_URGENT` | Predatory Urgency | Coercive deadlines accompanied by financial demands | "Final warning: pay within 2 hours or lose seat" |

#### LEGITIMATE Categories (`label = 0`):
| Category Code | Name | Description | Key Characteristic |
| :--- | :--- | :--- | :--- |
| `LEGIT_CORP` | Enterprise Tech & Engineering | Standard software, cloud, data, and QA roles | Multi-round interviews, CS degree, benefits |
| `LEGIT_START` | Early-Stage Startup Roles | Lean, brief, or informal descriptions | Fast-paced, equity options, modern tech stack |
| `LEGIT_BPO` | Customer Support & Operations | Legitimate customer service, BPO, operations | Shift allowances, CRM tools, voice/non-voice |
| `LEGIT_REMOTE` | Legitimate Remote Work | Authentic distributed software or design roles | Async communication, flexible hours, competitive pay |
| `LEGIT_FINTECH` | Payment Infrastructure & Fintech | Engineering roles building payment systems | "Develop APIs for bank transfers, credit card gateways" |
| `LEGIT_BANK` | Banking & Financial Operations | Account management, loan processing, auditing | "Reconcile customer bank accounts and ledger entries" |
| `LEGIT_CRYPTO` | Blockchain & Web3 Engineering | Smart contract and protocol developers | "Build decentralized custody wallets on testnet" |
| `LEGIT_PAYROLL` | Standard HR Payroll Mentions | Mentions bank accounts in legitimate payroll context | "Monthly compensation deposited to employee bank account" |
| `LEGIT_COMM` | Auxiliary Official Messaging | Legitimate use of WhatsApp for interview coordination | "Recruitment team may share interview venue via WhatsApp" |
| `LEGIT_SENIOR` | High Senior/Executive Salary | High compensation justified by senior experience | "Principal Architect CTC ₹50-70 LPA (8+ years exp)" |

### 3.3 Disambiguation Matrix
To ensure contextual understanding over naive keyword triggering:

| Phrase / Context | Target Label | Rationale |
| :--- | :---: | :--- |
| *"Candidate must have experience building bank transfer APIs"* | `0` | Technical responsibility, not extortion. |
| *"Transfer Rs 1,000 to our bank account for onboarding"* | `1` | Applicant-directed financial extortion. |
| *"Salary will be credited directly to your bank account"* | `0` | Standard payroll explanation. |
| *"Send your Aadhaar card and bank account details for verification"* | `1` | Premature credential/identity solicitation. |
| *"Experience in crypto exchanges or smart contract protocols"* | `0` | Technical role qualification. |
| *"Deposit $100 in USDT to receive task commissions"* | `1` | Crypto task scam. |
| *"Join our official WhatsApp group for interview directions"* | `0` | Auxiliary logistical communication. |
| *"No interview. Contact HR on WhatsApp only to start working"* | `1` | Exclusive messaging channel + no interview scam. |
| *"There is strictly no registration fee at any stage"* | `0` | Affirmative anti-scam notice. |
| *"Pay mandatory registration fee of Rs 500"* | `1` | Explicit fee extortion. |

---

## 4. Entity Masking & Leakage Prevention Specification

### 4.1 Root Cause of Current Contamination
In the baseline model, specific company names (`Infosys`, `TCS`, `Wipro`) were exclusively assigned to legitimate rows, while artificial names (`Quick Cash Careers`, `Global Opportunity Hub`) were exclusively assigned to scam rows. As a result, the linear model memorized company tokens rather than recruitment patterns.

### 4.2 Universal Entity Masking Rules
Before TF-IDF vectorization, both training data and live inference text must pass through the identical entity normalization:

1. **Company Name Masking (`<COMPANY>`)**:
   - Any company name present in the company registry (`verified_companies.json`) or passed via the `company_name` input field is replaced with `<COMPANY>`.
   - In training text, entity recognizers / token replacement map known organization names to `<COMPANY>`.
2. **Email Address Masking (`<EMAIL>`)**:
   - Standard regex `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` replaced with `<EMAIL>`.
   - Domain strings are intentionally stripped from text so the ML model cannot memorize email domains (email domain risk is handled by deterministic rules).
3. **URL Masking (`<URL>`)**:
   - All `http://`, `https://`, and `www.` patterns replaced with `<URL>`.
4. **Phone Number Masking (`<PHONE>`)**:
   - Indian (+91) and international phone patterns (10-12 digits) replaced with `<PHONE>`.
5. **Monetary Value Masking (`<MONEY>`)**:
   - Currency expressions (`₹`, `Rs.`, `INR`, `$`, `USD`, `LPA`, `per month`) normalized to `<MONEY>`.
6. **Large Integer Masking (`<NUM>`)**:
   - Arbitrary multi-digit numbers replaced with `<NUM>`.

### 4.3 What Remains Unmasked
- Semantic action verbs: `pay`, `wire`, `deposit`, `transfer`, `reimburse`, `credit`, `earn`, `apply`, `build`, `design`.
- Role nouns: `engineer`, `intern`, `operator`, `specialist`, `lead`, `architect`, `assistant`.
- Channel indicators: `whatsapp`, `telegram`, `email`, `portal`, `sms`.
- Process descriptors: `interview`, `assessment`, `round`, `selection`, `guaranteed`, `immediate`, `urgent`.

---

## 5. Leakage-Resistant Dataset Splitting

### 5.1 Splitting Rules
1. **Deduplication Prior to Splitting**: Exact duplicates and near-duplicates (>90% character similarity) must be removed before partitioning.
2. **Group-Aware Partitioning**:
   - Samples from the same source origin or template family must NEVER be split across train and test.
   - All variations of a single template must reside exclusively in either the Train split or the Test split.
3. **Split Distribution**:
   - **Training Set (70%)**: Used for fitting TF-IDF vocabulary and classifier parameters.
   - **Validation Set (15%)**: Strictly isolated; used for hyperparameter tuning, n-gram selection, and probability calibration.
   - **Test Set (15%)**: Completely untouched holdout for final unbiased evaluation.
4. **Reproducibility**: Random seed fixed to `42`.

---

## 6. Hard-Negative Archetypes

To permanently cure false positives on technical and financial postings, the training dataset must include at least **350 hard-negative legitimate samples** distributed across seven archetypes:

1. **Fintech Payment Processing**: Software engineers building payment gateways, transaction processors, and clearinghouse integrations.
2. **Banking Account Reconciliations**: Operations analysts reconciling customer accounts, bank ledgers, and credit card processing.
3. **Cryptocurrency & Web3 Protocols**: Protocol developers designing smart contracts, wallet custody solutions, and consensus algorithms.
4. **Gift Card & Loyalty Programs**: Operations managers handling retail gift cards, loyalty vouchers, and promotional reward distribution.
5. **Auxiliary HR Messaging**: Verified corporate recruiters offering WhatsApp Business contact for campus recruitment drives or interview venue coordination.
6. **Developer Communities**: Open-source maintainers linking official Telegram or Discord developer discussion channels.
7. **Senior Executive Compensation**: Principal architects and engineering leaders earning ₹40-75 LPA.

By training on these affirmative samples with `label = 0`, the model learns that words like `bank`, `account`, `payment`, `crypto`, and `whatsapp` do NOT constitute scam indicators when used in technical or professional contexts.
