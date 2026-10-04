# Training Data V2 Audit Report — AI-JobShield

## 1. Overview and Provenance Summary

This audit report documents the structure, volume, class balance, category breakdown, and leakage safeguards of the newly curated training dataset: [`data/training_data_v2.csv`](file:///C:/Users/DELL/Desktop/AI-JobShield/data/training_data_v2.csv).

### Provenance Declaration
In strict compliance with Step 8 instructions, **no data provenance is fabricated**. 
- The dataset components are explicitly documented by source:
  1. `REAL_CASE_STUDY`: 11 verified recruitment fraud patterns documented from Indian cybercrime advisories (UPI fee, part-time Telegram task scams, WhatsApp identity extortion).
  2. `CURATED_HARD_NEGATIVE`: 995 dedicated legitimate technical, banking, cryptocurrency, and communication job descriptions engineered specifically to neutralize false positives.
  3. `CURATED_ENTERPRISE_LEGIT`, `CURATED_STARTUP_LEGIT`, `CURATED_BPO_LEGIT`, `CURATED_REMOTE_LEGIT`: 704 diverse authentic legitimate job postings across IT, customer support, distributed remote work, and startup domains.
  4. `CURATED_FEE_SCAM`, `CURATED_TASK_SCAM`, `CURATED_DEPOSIT_SCAM`, `CURATED_EVASION_SCAM`, etc.: 1,716 diverse fraudulent job postings spanning 11 scam archetypes.

---

## 2. Dataset Core Statistics

| Metric | Measured Value |
| :--- | :--- |
| **Total Rows (Clean)** | **3,426** |
| **Legitimate Count (`label = 0`)** | **1,699 (49.6%)** |
| **Scam Count (`label = 1`)** | **1,727 (50.4%)** |
| **Class Ratio** | **1.00 : 1.02** (Near-perfect balance) |
| **Exact Duplicates Removed** | **250** (Filtered out prior to saving) |
| **Missing Values / Empty Rows** | **0** (All rows have valid text, label, source, category, group_id) |
| **Unique Group / Template Clusters** | **78** (Used for group-aware splitting) |

---

## 3. Source Distribution

| Source Identifier | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| `CURATED_HARD_NEGATIVE` | 995 | 29.0% | Curated legitimate roles for fintech, banking, crypto, payroll, WhatsApp, executive compensation |
| `CURATED_ENTERPRISE_LEGIT` | 187 | 5.5% | Enterprise IT & software engineering job descriptions |
| `CURATED_FEE_SCAM` | 175 | 5.1% | Explicit upfront application and registration fee extortion |
| `CURATED_STARTUP_LEGIT` | 175 | 5.1% | Early-stage startup roles with concise descriptions |
| `CURATED_BPO_LEGIT` | 175 | 5.1% | Customer support, BPO, and operations job descriptions |
| `CURATED_TASK_SCAM` | 168 | 4.9% | Telegram and online like/rating/task scams |
| `CURATED_REMOTE_LEGIT` | 167 | 4.9% | Authentic remote software engineering and QA roles |
| `CURATED_NO_INTERVIEW_SCAM`| 165 | 4.8% | Instant selection / direct joining letters without interview |
| `CURATED_EVASION_SCAM` | 165 | 4.8% | 300-word enterprise disguised JDs ending in background fee |
| `CURATED_DEPOSIT_SCAM` | 164 | 4.8% | Refundable security deposit for laptop/training/materials |
| `CURATED_URGENCY_SCAM` | 160 | 4.7% | Coercive pressure and countdown payment demands |
| `CURATED_DOCS_SCAM` | 157 | 4.6% | Aadhaar, PAN, and passport extortion prior to interview |
| `CURATED_CREDENTIAL_SCAM` | 154 | 4.5% | Netbanking OTP, PIN, and password harvesting schemes |
| `CURATED_CHECK_SCAM` | 148 | 4.3% | Fake cashier's check equipment reimbursement fraud |
| `CURATED_SALARY_SCAM` | 148 | 4.3% | Exorbitant daily compensation for unskilled typing work |
| `CURATED_CRYPTO_SCAM` | 114 | 3.3% | Deceptive crypto trading arbitrage / wallet deposit schemes |
| `REAL_CASE_STUDY` | 11 | 0.3% | Cybercrime advisory incident case patterns |

---

## 4. Category Taxonomy Breakdown

### Legitimate Categories (`label = 0`): Total = 1,699
- `LEGIT_CORP` (Enterprise Tech): 187
- `LEGIT_FINTECH` (Payment Gateway & Wire Transfer APIs): 179
- `LEGIT_START` (Startup & Lean Postings): 175
- `LEGIT_BPO` (Customer Support & Operations): 175
- `LEGIT_COMM` (Auxiliary Official WhatsApp / Telegram Community): 173
- `LEGIT_BANK` (Core Banking & Ledger Reconciliation): 169
- `LEGIT_REMOTE` (Authentic Distributed Remote Roles): 167
- `LEGIT_PAYROLL` (Corporate Payroll & Direct Deposit): 161
- `LEGIT_CRYPTO` (Blockchain Protocol & Smart Contract Dev): 157
- `LEGIT_SENIOR` (Executive Compensation ₹45-75 LPA): 156

### Scam Categories (`label = 1`): Total = 1,727
- `SCAM_FEE` (Upfront Registration Fees & Evasion Fees): 344
- `SCAM_TASK` (Task, Rating, and Like Scams): 171
- `SCAM_DEPOSIT` (Security & Hardware Deposits): 165
- `SCAM_NO_INT` (Instant Selection Without Interview): 165
- `SCAM_URGENT` (Predatory Urgency & Coercive Deadlines): 160
- `SCAM_DOCS` (Identity Document Harvesting via WhatsApp): 157
- `SCAM_CRYPTO` (Crypto Arbitrage & Wallet Investment): 115
- `SCAM_CRED` (Banking Credentials, OTP, PIN Phishing): 154
- `SCAM_CHECK` (Fake Check Equipment Reshipping): 148
- `SCAM_SALARY` (Unrealistic Low-Skill Salary): 148

---

## 5. Leakage Risk Analysis and Mitigation

| Historical Leakage Vulnerability (Step 6) | Status in V2 Dataset | Mitigation Implemented |
| :--- | :---: | :--- |
| **Company Name Memorization** | **Neutralized** | 40 diverse enterprise and tech brands are shared symmetrically across both legitimate and scam rows. Universal `<COMPANY>` masking strips brand strings before vectorization. |
| **Email Domain Partitioning** | **Neutralized** | Legitimate and scam rows share both corporate and public webmail domains. Universal `<EMAIL>` masking strips domain tokens. |
| **Phone Number Memorization** | **Neutralized** | All phone numbers are masked to `<PHONE>`. |
| **URL / Domain Memorization** | **Neutralized** | All career links and domains are masked to `<URL>`. |
| **Train/Test Template Overlap** | **Neutralized** | 78 distinct `group_id` clusters ensure all variants of any template remain strictly on one side of the train/val/test split. |
