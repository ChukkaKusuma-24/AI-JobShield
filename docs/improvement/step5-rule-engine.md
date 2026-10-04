# Step 5: Rule Engine Quality, Context, and Double-Counting Audit

## 1. Executive Summary

In Step 5, we audited and re-engineered the 14 deterministic rules in AI-JobShield to incorporate **context-aware semantic evaluation**, distinguish **job responsibilities from applicant-directed instructions**, and eliminate residual multi-dimensional double-counting.

Prior to Step 5:
1. Innocent statements such as *"There is strictly no application fee"* triggered `fee_request` (35 pts, Critical) due to naive substring matches.
2. Technical descriptions in engineering roles (e.g., *"developing APIs for bank transfer processing"*, *"integrating crypto exchanges"*, *"managing gift card infrastructure"*) risked triggering extortion rules (`money_transfer`).
3. Standard HR identity documentation requests upon hire (*"Aadhaar and PAN required for background verification through official portal"*) were conflated with upfront extortion or credential phishing (`sensitive_info`).
4. High salaries for legitimate principal/staff engineers (e.g., ₹50 LPA for 8+ years experience) were vulnerable to false `unrealistic_salary` penalties.
5. Technical postings packed with uppercase acronyms (AWS, GCP, SQL, CI/CD, REST APIs) triggered `caps_exclaim`.

Following Step 5 enhancements:
- All 14 rules now distinguish **affirmative applicant-directed instructions** from technical domain discussions and negative assertions.
- **72 tests pass** across all four test suites (7 history/scoring + 25 evidence hierarchy + 13 company identity + 27 adversarial rule context tests) with **0 failures**.
- Across the controlled 15-case benchmark, all legitimate jobs score in the **Low Risk** category (87–93) or appropriate **Medium Risk** (58–65 for unverified startups), while all fraudulent/scam postings are strictly contained in **High Risk** (25–35) or **Medium Risk** (50–51 for unverified messaging-only jobs).

---

## 2. Summary of Changes Made to the Rule Engine

### A. Context-Aware Applicant-Directed Fee Detection (`fee_request`)
- **Clause-Level Negation Handling**: Scans the preceding clause bounded by sentence terminators (`.`, `;`, `\n`) or contrastive conjunctions (`but`, `however`) for negative qualifiers (`no`, `never`, `without`, `zero`, `free of`, `strictly no`).
- **Employer Coverage Recognition**: Ignores fee words when preceded by employer benefit cues (`company covers`, `employer pays`, `tuition reimbursement`).
- **Applicant-Directed Requirement**: Affirmatively targets instructions where the applicant/candidate is told to pay, deposit, or transfer money before joining or interview.

### B. Applicant-Directed Financial Action vs Technical Job Duties (`money_transfer`)
- **Action Verb + Financial Object Syntax**: Enforces `APPLICANT + ACTION + FINANCIAL OBJECT` grammar (e.g., *"pay the recruiter"*, *"send ₹1,500 via UPI"*, *"deposit cryptocurrency to receive salary"*, *"buy gift cards and send codes"*).
- **Technical Suppression**: Ignores bare technology nouns (`crypto`, `bitcoin`, `bank transfer`, `gift cards`, `upi`) when describing software architecture, payment gateways, APIs, or reconciliation protocols.

### C. Tiered Sensitive Information Evaluation (`sensitive_info`)
- **Tier 1 (Always Critical Extortion)**: Immediate detection of credential harvesting: `otp`, `pin`, `cvv`, `netbanking password`, `card pin`, `debit/credit card number`.
- **Tier 2 (Solicited Identity Documents)**: Targets requests instructing applicants to send, email, or message their original `Aadhaar`, `PAN`, `passport`, or `bank statement` directly to recruiters, via WhatsApp/Telegram, or prior to interview.
- **Legitimate HR Onboarding Excluded**: Legitimate mentions of identity verification through company HR portals upon joining or passport requirements for international travel are explicitly preserved without penalty.

### D. Seniority-Aware Salary Realism (`unrealistic_salary`)
- **Role Seniority Differentiation**: Checks whether the posting is for a senior/lead/architect role with 5+ to 10+ years experience versus entry-level, fresher, or low-skill manual tasks (typing, data entry, copy-pasting, ad-clicking).
- **Legitimate Executive Compensation**: ₹50 Lakhs/year for a Principal Architect with 8+ years experience is recognized as standard market compensation and not penalized.
- **Entry-Level Scam Detection**: ₹5,000/day or ₹1,50,000/month or ₹25 LPA for entry-level/fresher/typing is flagged as `unrealistic_salary`.

### E. Contextual Messaging Platform Handling (`suspicious_contact`)
- **Auxiliary vs Exclusive Channels**: Distinguishes companies that offer WhatsApp as an auxiliary candidate helpdesk alongside official corporate emails/websites from unverified entities that recruit exclusively through WhatsApp or Telegram.
- **Verified Enterprise Protection**: For verified enterprises with official domains (e.g., Reliance Jio at `careers@jio.com`), auxiliary WhatsApp mentions do not trigger high-severity penalties.

### F. Predatory Pressure vs Normal Urgency (`urgency`)
- **Predatory Pressure Language**: Always flags predatory tactics (*"final warning"*, *"hurry up"*, *"last chance"*, *"within 24 hours or lose seat"*).
- **Standard Corporate Timelines**: Standard phrasing (*"urgently hiring"*, *"immediate joiners preferred"*) is only flagged when accompanied by independent red flags (payment requests, sensitive info, or unrealistic salary).

### G. Uncoupling "No Experience" from "No Interview" (`no_interview`)
- **Removed False Positive**: Removed `r"no\s+experience\s+(?:needed|required)"` from `NO_INTERVIEW_PATTERNS`.
- **Targeted Scam Indicator**: Focuses strictly on `no interview`, `guaranteed selection/placement`, `instant selection`, and `direct joining letter`.

### H. Acronym-Aware Capitalization Evaluation (`caps_exclaim`)
- **Technical Acronym Filter**: Strips recognized uppercase industry acronyms (`AWS`, `GCP`, `AZURE`, `CI/CD`, `SQL`, `REST`, `API`, `HTML5`, `CSS3`, `JSON`, `HTTP`, `HTTPS`, `IT`, `HR`, `BTECH`, `MCA`, `TCS`, `HCL`, `WIPRO`, `SDK`, `PCI-DSS`, `TCP/IP`, `DNS`, `SSL`, `TLS`, `AI`, `ML`, `LLM`, `GO`) before calculating the `caps_ratio`.

---

## 3. Underlying Evidence to Scoring Dimension Mapping

To prevent double-counting across the 5 dimensions, signals are strictly routed to their primary dimension:

```
Underlying Evidence Signal            Primary Rule               Class       Affected Dimensions
---------------------------------------------------------------------------------------------------------
Official Corporate Domain             official_domain            POSITIVE    D1 (Company), D2 (Source), D5 (Contact)
Known Enterprise + Free Webmail       company_impersonation      CRITICAL    D1 (Company), D4 (Scam), D5 (Contact) [Cap <= 25]
Lookalike / Phishing Host             lookalike_domain           CRITICAL    D2 (Source), D4 (Scam) [Cap <= 25]
Applicant Registration Fee Demanded   fee_request                CRITICAL    D4 (Scam) [Cap <= 35]
Equipment Kit Purchase Demanded       equipment_purchase         CRITICAL    D4 (Scam) [Cap <= 35]
Applicant Directed to Wire / UPI      money_transfer             CRITICAL    D4 (Scam) [Cap <= 35]
Recruiter Solicits OTP / Card CVV     sensitive_info             CRITICAL    D4 (Scam) [Cap <= 35]
Aadhaar / PAN Demanded on WhatsApp    sensitive_info             CRITICAL    D4 (Scam) [Cap <= 35]
Telegram / WhatsApp-Only Hiring       suspicious_contact         NEGATIVE    D4 (Scam: -15), D5 (Contact: 20.0)
Entry Typist Earning ₹5,000/day       unrealistic_salary         NEGATIVE    D4 (Scam: -20)
Guaranteed Placement Direct Joining   no_interview               NEGATIVE    D4 (Scam: -12)
Predatory 24h Panic Pressure          urgency                    NEGATIVE    D4 (Scam: -10)
Short Uninformative Description       vague_description          NEGATIVE    D3 (Quality: -25), D4 (Scam: -10)
All-Caps Screaming Text (Excl. Acr.)  caps_exclaim               NEGATIVE    D3 (Quality: -15), D4 (Scam: -5)
```

---

## 4. Benchmark Progression Across All 5 Steps

Below is the side-by-side progression of all 15 benchmark cases across the project lifecycle:

| ID | Case Name | Category | Step 2 Baseline | Step 3 Evidence | Step 4 Identity | Step 5 Context | Net Delta (S2 $\rightarrow$ S5) | Final Risk Level | Key Mechanism |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **Genuine verified TCS** | Legitimate | 77 | 76 | 92 | **92** | **+15** | **LOW** | Full enterprise match; zero false flags; positive official email (+6) and URL. |
| **2** | **Genuine verified Infosys** | Legitimate | 93 | 92 | 93 | **93** | 0 | **LOW** | Enterprise verified; official corporate domain. |
| **3** | **Genuine unknown startup** | Legitimate | 63 | 58 | 65 | **65** | +2 | **MEDIUM** | Unverified registry match; positive domain matching (+4); capped at 65. |
| **4** | **TCS using Gmail** | Fraudulent | 25 | 25 | 25 | **25** | 0 | **HIGH** | `company_impersonation` (`CRITICAL`); hard cap $\le 25$. |
| **5** | **TCS lookalike domain** | Fraudulent | 25 | 25 | 25 | **25** | 0 | **HIGH** | `lookalike_domain` + `company_impersonation`; hard cap $\le 25$. |
| **6** | **Registration fee scam** | Fraudulent | 34 | 31 | 25 | **27** | -7 | **HIGH** | `fee_request` (`CRITICAL`) + `unrealistic_salary`, hard cap $\le 35$. |
| **7** | **Equipment/deposit scam** | Fraudulent | 35 | 35 | 25 | **25** | -10 | **HIGH** | `equipment_purchase` + `fee_request`, hard cap $\le 35$. |
| **8** | **WhatsApp-only recruitment** | Fraudulent | 59 | 51 | 50 | **50** | -9 | **MEDIUM** | `suspicious_contact` (`NEGATIVE`), no crude scam words. |
| **9** | **Telegram-only recruitment** | Fraudulent | 35 | 51 | 51 | **51** | +16 | **MEDIUM** | `suspicious_contact` (`NEGATIVE`), false crypto extortion cleared. |
| **10** | **Unrealistic salary scam** | Fraudulent | 45 | 34 | 31 | **31** | -14 | **HIGH** | `unrealistic_salary` + `urgency` (`NEGATIVE`), missing evidence base. |
| **11** | **Sensitive info request** | Fraudulent | 35 | 35 | 35 | **35** | 0 | **HIGH** | `sensitive_info` (`CRITICAL`), Aadhaar/PAN solicitation, cap $\le 35$. |
| **12** | **Multiple critical signals** | Fraudulent | 27 | 27 | 26 | **26** | -1 | **HIGH** | Multiple critical flags, hard cap $\le 35$. |
| **13** | **Legitimate incomplete posting** | Legitimate | 73 | 63 | 60 | **60** | -13 | **MEDIUM** | Wipro without URL/email; partially verified cap $\le 70$. |
| **14** | **Legitimate job + WhatsApp** | Legitimate | 92 | 90 | 89 | **89** | -3 | **LOW** | Official Jio channels verified; auxiliary contact handled gracefully. |
| **15** | **Legitimate payment-context job** | Legitimate | 35 | 92 | 87 | **87** | **+52** | **LOW** | HCLTech official domain; fintech keywords recognized as technical duties. |

---

## 5. False Positives and False Negatives Fixed

### False Positives Fixed:
1. **Negated Fee Statements**: Phrases like *"Strictly no application fee, registration fee, or training fee charged at any stage"* no longer trigger `fee_request`.
2. **Fintech / Payment Engineering Duties**: Postings mentioning *"bank transfer APIs"*, *"crypto exchanges"*, *"gift card platform"*, or *"UPI payment integration"* no longer trigger `money_transfer`.
3. **Legitimate HR Identity Onboarding**: Requirements stating *"Aadhaar and PAN required for background verification through official HR portal upon joining"* no longer trigger `sensitive_info`.
4. **Legitimate Travel Requirements**: *"Valid passport required for international travel"* no longer triggers `sensitive_info`.
5. **High Market Salaries for Senior Staff**: Executive/Principal roles offering ₹50 LPA for 8+ years experience no longer trigger `unrealistic_salary`.
6. **Auxiliary WhatsApp Support on Verified Enterprises**: Enterprise postings mentioning a WhatsApp helpdesk alongside corporate emails/sites no longer receive high-severity penalties.
7. **Normal Corporate Timelines**: Phrases like *"urgently hiring"* or *"immediate joiners preferred"* no longer trigger `urgency` unless combined with predatory pressure or extortion.
8. **Entry-Level "No Experience Required"**: Postings offering entry-level jobs with *"no experience needed"* are no longer falsely flagged as `no_interview`.
9. **Technical Capitalization**: Descriptions containing uppercase acronyms (AWS, GCP, CI/CD, SQL, REST APIs, JSON) no longer trigger `caps_exclaim`.

### False Negatives Fixed:
1. **Multi-Document Solicitation**: Requests demanding *"Submit your Aadhaar and bank details for payroll"* now cleanly trigger `sensitive_info`.
2. **Predatory Pressure Tactics**: Language like *"final warning"*, *"hurry up"*, *"within 24 hours or lose your placement"* reliably triggers `urgency`.
3. **Telegram/WhatsApp-Only Unverified Recruiters**: Exclusive messaging-only hiring with no official corporate domain is reliably flagged as `suspicious_contact`.
4. **Credential Harvesting**: Requests for `OTP`, `PIN`, `CVV`, or `netbanking password` reliably trigger `sensitive_info` with critical severity.

---

## 6. Complete Test Suite Results (72 Tests)

A total of **72 tests** across four test suites were executed, passing with **100% success rate**:

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\DELL\Desktop\AI-JobShield
collected 72 items

tests/test_history_and_scoring.py (7 tests) ........................... PASSED [ 10%]
tests/test_evidence_hierarchy.py (25 tests) ........................... PASSED [ 44%]
tests/test_company_identity.py (13 tests) ............................. PASSED [ 62%]
tests/test_rule_engine_context.py (27 tests):
  test_01_legitimate_fintech_bank_transfers ............................ PASSED [ 63%]
  test_02_legitimate_crypto_engineering ............................... PASSED [ 65%]
  test_03_legitimate_gift_card_engineering ............................ PASSED [ 66%]
  test_04_legitimate_payment_processing ................................ PASSED [ 68%]
  test_05_no_application_fee_statement ................................ PASSED [ 69%]
  test_06_legitimate_hr_identity_verification .......................... PASSED [ 70%]
  test_07_suspicious_aadhaar_request_whatsapp .......................... PASSED [ 72%]
  test_08_otp_request .................................................. PASSED [ 73%]
  test_09_registration_fee_request ..................................... PASSED [ 75%]
  test_10_equipment_deposit ............................................ PASSED [ 76%]
  test_11_unrealistic_salary_alone_senior .............................. PASSED [ 77%]
  test_12_unrealistic_salary_and_urgency ............................... PASSED [ 79%]
  test_13_whatsapp_only_unknown_company ................................ PASSED [ 80%]
  test_14_whatsapp_auxiliary_official_company .......................... PASSED [ 81%]
  test_15_telegram_only_job ............................................ PASSED [ 83%]
  test_16_telegram_and_payment_request ................................. PASSED [ 84%]
  test_17_urgent_legitimate_job ........................................ PASSED [ 86%]
  test_18_urgent_scam_with_payment ..................................... PASSED [ 87%]
  test_19_no_interview_official_company ................................ PASSED [ 88%]
  test_20_no_interview_suspicious_contact_high_salary .................. PASSED [ 90%]
  test_21_short_legitimate_job_posting ................................. PASSED [ 91%]
  test_22_vague_job_suspicious_contact ................................. PASSED [ 93%]
  test_23_all_caps_legitimate_job_acronyms ............................. PASSED [ 94%]
  test_24_all_caps_payment_request ..................................... PASSED [ 95%]
  test_25_official_tcs_job ............................................. PASSED [ 97%]
  test_26_tcs_gmail_impersonation ...................................... PASSED [ 98%]
  test_27_tcs_lookalike_domain ......................................... PASSED [100%]

======================= 72 passed, 9 warnings in 11.46s =======================
```

---

## 7. Remaining Limitations

1. **Complex Compound Negations**:
   Very convoluted multi-sentence negations (e.g. *"Unlike traditional agencies that collect fees, our firm operates on a retainer model funded by the corporate client"*) rely on keyword proximity rather than deep dependency parsing.
2. **Multilingual Phrasing (Hinglish)**:
   Scam phrases written in informal transliterated Hinglish (*"registration charge pay karna padega"*, *"paise bhejo"*) require specialized multilingual token expansion.
3. **ML Feature Coupling**:
   The TF-IDF ML model was intentionally not retrained in Step 5 (per user constraints) and continues to output raw predictions based on unigram/bigram tokens.
