# AI JobShield Scoring System: Baseline Benchmark Results

**Date:** 2026-10-03  
**Status:** Reproducible Baseline Report (Read-Only Execution of Unmodified Production Code)  
**Execution Environment:** Python 3.12, SQLite (`database/baseline_benchmark.db`), Scikit-Learn 1.9.0 with active pre-trained model `models/jobshield_model.joblib`.  

---

## 1. Test Methodology

### Objective
Establish an empirical, reproducible baseline of the existing AI JobShield scoring engine across 15 standardized test scenarios representing genuine corporate jobs, startups, deceptive scams, contact-channel variations, and edge cases.

### Rules of Engagement
- **Zero Production Modifications:** No source code in `backend/app` or `models/` was changed.
- **Identical Pipeline:** Each case was processed through the identical pipeline used by `/api/analyze`:
  1. `company_verifier.verify_company(db, company, email, url)`
  2. `url_analyzer.analyze_url(url, company)`
  3. `ml_service.predict(text)`
  4. `rules.analyze_rules(...)`
  5. `scoring.compute_trust_score(...)`
  6. `explain.build_explanation(...)`
- **Signal Taxonomy:** Every signal observed during evaluation is classified into one of four rigorous evidentiary classes:
  - **POSITIVE EVIDENCE:** Verifiable indicators of legitimacy (e.g. verified registry record, official corporate domain match, structured JD).
  - **NEGATIVE EVIDENCE:** Non-critical warning indicators of risk (e.g. urgency words, non-interview guarantees, suspicious URL attributes).
  - **MISSING EVIDENCE:** Omission of verifiable data (e.g. missing website URL, missing recruiter email, unverified brand).
  - **CRITICAL EVIDENCE:** Severe disqualifying indicators requiring hard caps (e.g. upfront fee, gift card/crypto transfer, Aadhaar/bank data solicitation, brand impersonation).

---

## 2. Complete Test-Case Summary Table

| ID | Case Name | Category | Company Status | URL Status | ML Prob | Raw Wtd | Cap Applied | Final Score | Risk Level |
|---|---|---|---|---|---|---|---|---|---|
| **1** | Genuine verified TCS | Legitimate | VERIFIED | LOW (mismatch) | 19.0% | 77.1 | None | **77** | **LOW** |
| **2** | Genuine verified Infosys | Legitimate | VERIFIED | LOW | 27.6% | 93.0 | None | **93** | **LOW** |
| **3** | Genuine unknown startup | Legitimate | UNVERIFIED | LOW (mismatch) | 28.5% | 62.5 | None | **63** | **MEDIUM** |
| **4** | TCS using Gmail | Fraudulent | IMPERSONATION_RISK | NO_URL | 33.1% | 41.8 | Cap 25 | **25** | **HIGH** |
| **5** | TCS lookalike domain | Fraudulent | IMPERSONATION_RISK | HIGH | 30.0% | 39.4 | Cap 25 | **25** | **HIGH** |
| **6** | Registration fee scam | Fraudulent | UNVERIFIED | MEDIUM | 84.5% | 33.6 | Cap 35 | **34** | **HIGH** |
| **7** | Equipment/deposit scam | Fraudulent | UNVERIFIED | LOW (mismatch) | 52.0% | 53.1 | Cap 35 | **35** | **HIGH** |
| **8** | WhatsApp-only recruitment | Fraudulent | UNVERIFIED | NO_URL | 50.9% | 58.5 | None | **59** | **MEDIUM** |
| **9** | Telegram-only recruitment | Fraudulent | UNVERIFIED | NO_URL | 49.9% | 51.3 | Cap 35 | **35** | **HIGH** |
| **10** | Unrealistic salary scam | Fraudulent | UNVERIFIED | NO_URL | 74.0% | 44.6 | None | **45** | **MEDIUM** |
| **11** | Sensitive information request | Fraudulent | UNVERIFIED | NO_URL | 51.2% | 52.2 | Cap 35 | **35** | **HIGH** |
| **12** | Multiple critical scam signals | Fraudulent | UNVERIFIED | MEDIUM | 89.8% | 27.2 | Cap 35 | **27** | **HIGH** |
| **13** | Legitimate incomplete posting | Legitimate | PARTIALLY VERIFIED | NO_URL | 32.0% | 72.6 | None | **73** | **MEDIUM** |
| **14** | Legitimate job w/ WhatsApp | Legitimate | VERIFIED | LOW | 34.6% | 92.4 | None | **92** | **LOW** |
| **15** | Legitimate payment-context job | Legitimate | VERIFIED | LOW | 33.5% | 85.1 | Cap 35 | **35** | **HIGH** |

### Benchmark Aggregate Statistics

$$\begin{aligned}
\text{Legitimate Cases (6 cases):} \quad &\text{Range: } [35, 93], \quad \text{Average Score: } \mathbf{72.17} \\
\text{Fraudulent Cases (9 cases):} \quad &\text{Range: } [25, 59], \quad \text{Average Score: } \mathbf{35.56} \\
\text{Score Overlap Region:} \quad &[\mathbf{35}, \mathbf{59}] \quad (\text{Catastrophic overlap: scams score above legitimate jobs})
\end{aligned}$$

---

## 3. Per-Case Scoring Breakdown

### Case 1: Genuine Verified TCS
- **Input:** Company: `Tata Consultancy Services` | Email: `careers@tcs.com` | URL: `https://www.tcs.com/careers`
- **Company Verification:** `status = VERIFIED`, internal score = 95.
- **URL Status:** `LOW` risk (score 15), URL flags: `company_mismatch` [NEGATIVE EVIDENCE].
- **Rule Flags:** `email_domain_mismatch` (15 pts, high severity) [NEGATIVE EVIDENCE].
- **Positive Indicators:** `detailed_responsibilities`, `qualifications`, `https_url`, `interview_process`, `realistic_salary`, `company_verified`, `no_fee` [POSITIVE EVIDENCE].
- **5-Dimensional Scores:**
  - Company (25%): **95.0** (contributes 23.75)
  - Source (20%): **60.0** (slashed from 90.0 due to `company_mismatch`) (contributes 12.00)
  - Quality (15%): **95.0** (contributes 14.25)
  - Scam Detection (30%): **83.8** (15 rule pts deducted, ML risk 19.03) (contributes 25.14)
  - Contact Consistency (10%): **20.0** (slashed from 95.0 due to `email_domain_mismatch`) (contributes 2.00)
- **Raw Weighted Score:** 77.1 $\to$ **Final Trust Score: 77 (LOW Risk)**.
- **Evidentiary Diagnosis:** Acronym mismatch bug in `rules.py` and `url_analyzer.py` robs genuine TCS of **18 points**.

### Case 2: Genuine Verified Infosys
- **Input:** Company: `Infosys` | Email: `careers@infosys.com` | URL: `https://www.infosys.com/careers`
- **Company Verification:** `status = VERIFIED`, internal score = 95.
- **URL Status:** `LOW` risk (score 0), no flags.
- **Rule Flags:** None.
- **Positive Indicators:** `detailed_responsibilities`, `qualifications`, `official_email`, `https_url`, `interview_process`, `realistic_salary`, `company_verified`, `no_fee` [POSITIVE EVIDENCE].
- **5-Dimensional Scores:** Company: 95.0 | Source: 90.0 | Quality: 95.0 | Scam: 91.7 | Contact: 95.0.
- **Raw Weighted Score:** 93.0 $\to$ **Final Trust Score: 93 (LOW Risk)**.
- **Evidentiary Diagnosis:** Company tokens (`{"infosys"}`) match domain tokens (`{"infosys"}`), producing expected clean tier-1 enterprise evaluation.

### Case 3: Genuine Unknown Startup
- **Input:** Company: `Lumina Quantum Systems` | Email: `talent@luminaquantum.tech` | URL: `https://www.luminaquantum.tech/jobs`
- **Company Verification:** `status = UNVERIFIED`, internal score = 45.
- **URL Status:** `LOW` risk (score 15), URL flags: `company_mismatch` [NEGATIVE EVIDENCE].
- **Rule Flags:** `email_domain_mismatch` (15 pts) [NEGATIVE EVIDENCE].
- **Positive Indicators:** `detailed_responsibilities`, `qualifications`, `https_url`, `interview_process`, `realistic_salary`, `no_fee` [POSITIVE EVIDENCE].
- **5-Dimensional Scores:** Company: 40.0 | Source: 60.0 | Quality: 95.0 | Scam: 81.0 | Contact: 20.0.
- **Raw Weighted Score:** 62.5 $\to$ **Final Trust Score: 63 (MEDIUM Risk)**.
- **Evidentiary Diagnosis:** `_company_tokens` produced `{"lumina", "quantum"}` while domain had single token `{"luminaquantum"}`. Inability to recognize compound domain names causes unwarranted mismatch flags.

### Case 4: TCS Using Gmail
- **Input:** Company: `Tata Consultancy Services` | Email: `recruiter@gmail.com` | URL: None
- **Company Verification:** `status = IMPERSONATION_RISK`, internal score = 15 [CRITICAL EVIDENCE].
- **URL Status:** `NO_URL_PROVIDED` [MISSING EVIDENCE].
- **Rule Flags:** `company_impersonation` (35 pts, critical) [CRITICAL EVIDENCE], `free_email` (12 pts) [NEGATIVE EVIDENCE], `email_domain_mismatch` (15 pts) [NEGATIVE EVIDENCE].
- **5-Dimensional Scores:** Company: 10.0 | Source: 50.0 | Quality: 95.0 | Scam: 46.7 | Contact: 10.0.
- **Raw Weighted Score:** 41.8 $\to$ **Applied Cap: Impersonation Cap (25) $\to$ Final Trust Score: 25 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Critical guardrail worked as intended. Noticeable multi-counting of free email signal (62 penalty points).

### Case 5: TCS Lookalike Domain
- **Input:** Company: `Tata Consultancy Services` | Email: `recruiter@tcs-hiring-portal.top` | URL: `http://tcs-careers-verify.top/apply`
- **Company Verification:** `status = IMPERSONATION_RISK`, internal score = 15 [CRITICAL EVIDENCE].
- **URL Status:** `HIGH` risk (score 67), URL flags: `kw_verify`, `http`, `tld`, `company_mismatch` [NEGATIVE EVIDENCE].
- **Rule Flags:** `company_impersonation` (35 pts, critical), `email_domain_mismatch` (15 pts), `suspicious_url` (18 pts).
- **5-Dimensional Scores:** Company: 10.0 | Source: 43.0 | Quality: 95.0 | Scam: 43.4 | Contact: 10.0.
- **Raw Weighted Score:** 39.4 $\to$ **Applied Cap: Impersonation Cap (25) $\to$ Final Trust Score: 25 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Correctly caught by impersonation guardrail and suspicious TLD heuristics.

### Case 6: Registration Fee Scam
- **Input:** Company: `Quick Earn Data Solutions` | Email: `hr@quickearnjobs.info` | URL: `http://quickearnjobs.info/register`
- **Company Verification:** `status = UNVERIFIED` [MISSING EVIDENCE].
- **Rule Flags:** `fee_request` (35 pts, critical) [CRITICAL EVIDENCE], `unrealistic_salary` (20 pts), `email_domain_mismatch` (15 pts), `urgency` (10 pts), `no_interview` (12 pts), `suspicious_url` (12 pts).
- **ML Probability:** 84.5% scam risk [NEGATIVE EVIDENCE].
- **5-Dimensional Scores:** Company: 40.0 | Source: 45.0 | Quality: 75.0 | Scam: 4.7 | Contact: 20.0.
- **Raw Weighted Score:** 33.6 $\to$ **Applied Cap: Critical Scam Cap (35) $\to$ Final Trust Score: 34 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Correctly classified as HIGH risk through multiple rule signals and ML.

### Case 7: Equipment / Deposit Scam
- **Input:** Company: `Global Virtual Workspace` | Email: `onboarding@globalvirtualworkspace.com` | URL: `https://globalvirtualworkspace.com/careers`
- **Company Verification:** `status = UNVERIFIED` [MISSING EVIDENCE].
- **Rule Flags:** `fee_request` (35 pts, critical) [CRITICAL EVIDENCE], `email_domain_mismatch` (15 pts).
- **5-Dimensional Scores:** Company: 40.0 | Source: 60.0 | Quality: 95.0 | Scam: 49.4 | Contact: 20.0.
- **Raw Weighted Score:** 53.1 $\to$ **Applied Cap: Critical Scam Cap (35) $\to$ Final Trust Score: 35 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Raw weighted score was 53.1 (Medium Risk). Only saved from being classified as Medium Risk by the hard cap of 35.

### Case 8: WhatsApp-Only Recruitment
- **Input:** Company: `Apex Media Services` | Email: None | URL: None | "Contact on WhatsApp only at +91-9876543210"
- **Company Verification:** `status = UNVERIFIED` [MISSING EVIDENCE].
- **Rule Flags:** `suspicious_contact` (15 pts, high severity) [NEGATIVE EVIDENCE].
- **Positive Indicators:** `detailed_responsibilities`, `qualifications`, `interview_process`, `realistic_salary`, `no_fee` [POSITIVE EVIDENCE].
- **5-Dimensional Scores:** Company: 40.0 | Source: 50.0 (blank baseline) | Quality: 95.0 | Scam: 74.2 | Contact: 20.0.
- **Raw Weighted Score:** 58.5 $\to$ **Applied Cap: None $\to$ Final Trust Score: 59 (MEDIUM Risk)**.
- **Evidentiary Diagnosis (MAJOR FALSE NEGATIVE):** `suspicious_contact` is only High severity (15 pts), not Critical. Missing URL and missing email receive neutral 50 baselines. Resulting score of **59 is higher than legitimate HCLTech (35)!**

### Case 9: Telegram-Only Recruitment
- **Input:** Company: `Crypto Alpha Labs` | Email: None | URL: None | "Conducted via Telegram only"
- **Company Verification:** `status = UNVERIFIED` [MISSING EVIDENCE].
- **Rule Flags:** `money_transfer` (35 pts, critical) [CRITICAL EVIDENCE], `suspicious_contact` (15 pts).
- **5-Dimensional Scores:** Company: 40.0 | Source: 50.0 | Quality: 95.0 | Scam: 50.0 | Contact: 20.0.
- **Raw Weighted Score:** 51.3 $\to$ **Applied Cap: Critical Scam Cap (35) $\to$ Final Trust Score: 35 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Note that `money_transfer` was triggered accidentally because the company name contained "Crypto". Had the company been named "Alpha Analytics", `money_transfer` would not have triggered, and the score would have risen to **59/100 (Medium Risk)** like Case 8.

### Case 10: Unrealistic Salary Scam
- **Input:** Company: `Apex Swift Career Solutions` | Email: `jobs@swiftcareer.com` | URL: None | "Earn ₹5000 per day from home with immediate payment daily. No experience needed."
- **Company Verification:** `status = UNVERIFIED` [MISSING EVIDENCE].
- **Rule Flags:** `unrealistic_salary` (20 pts), `email_domain_mismatch` (15 pts), `urgency` (10 pts), `no_interview` (12 pts).
- **5-Dimensional Scores:** Company: 40.0 | Source: 50.0 | Quality: 75.0 | Scam: 37.9 | Contact: 20.0.
- **Raw Weighted Score:** 44.6 $\to$ **Applied Cap: None $\to$ Final Trust Score: 45 (MEDIUM Risk)**.
- **Evidentiary Diagnosis (CRITICAL DEFECT):** Despite being an obvious ₹5,000/day work-from-home typing scam, it received **45/100 (MEDIUM Risk)** because `unrealistic_salary`, `urgency`, and `no_interview` are not marked as critical signals and do not trigger a safety cap.

### Case 11: Sensitive Information Request
- **Input:** Company: `National Verification Bureau` | Email: `verification@natverify-desk.org` | URL: None | "Email Aadhaar card, PAN card, bank account statement, and debit card details"
- **Company Verification:** `status = UNVERIFIED` [MISSING EVIDENCE].
- **Rule Flags:** `sensitive_info` (30 pts, critical) [CRITICAL EVIDENCE], `email_domain_mismatch` (15 pts).
- **5-Dimensional Scores:** Company: 40.0 | Source: 50.0 | Quality: 95.0 | Scam: 53.1 | Contact: 20.0.
- **Raw Weighted Score:** 52.2 $\to$ **Applied Cap: Critical Scam Cap (35) $\to$ Final Trust Score: 35 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Correctly capped by `sensitive_info` critical rule.

### Case 12: Multiple Critical Scam Signals
- **Input:** Company: `Fast Track Global Employment` | Email: `fasttrackjobs@gmail.com` | URL: `http://fasttrack-jobs.xyz/pay`
- **Rule Flags:** 11 flags triggered (`fee_request`, `money_transfer`, `sensitive_info`, `unrealistic_salary`, `suspicious_contact`, `free_email`, `email_domain_mismatch`, `urgency`, `no_interview`, `vague_description`, `suspicious_url`) totaling 206 rule risk points.
- **ML Probability:** 89.8% scam risk.
- **5-Dimensional Scores:** Company: 40.0 | Source: 45.0 | Quality: 35.0 | Scam: 3.1 | Contact: 20.0.
- **Raw Weighted Score:** 27.2 $\to$ **Applied Cap: Critical Scam Cap (35) $\to$ Final Trust Score: 27 (HIGH Risk)**.
- **Evidentiary Diagnosis:** Correctly classified as deep HIGH risk.

### Case 13: Legitimate Incomplete Posting
- **Input:** Company: `Wipro` | Email: None | URL: None | Professional Engineering JD
- **Company Verification:** `status = PARTIALLY VERIFIED`, internal score = 65.
- **Rule Flags:** None.
- **5-Dimensional Scores:** Company: 65.0 | Source: 50.0 | Quality: 95.0 | Scam: 90.4 | Contact: 50.0.
- **Raw Weighted Score:** 72.6 $\to$ **Applied Cap: None $\to$ Final Trust Score: 73 (MEDIUM Risk)**.
- **Evidentiary Diagnosis:** Correctly placed in Medium Risk (73), bounded below genuine complete postings (Infosys 93, Jio 92).

### Case 14: Legitimate Job with WhatsApp Contact
- **Input:** Company: `Reliance Jio` | Email: `careers@jio.com` | URL: `https://careers.jio.com` | Contains "recruiter desk on WhatsApp for queries"
- **Company Verification:** `status = VERIFIED`, internal score = 95.
- **Rule Flags:** None (does not match `WHATSAPP_PATTERNS` because it is not "WhatsApp only").
- **5-Dimensional Scores:** Company: 95.0 | Source: 90.0 | Quality: 95.0 | Scam: 89.6 | Contact: 95.0.
- **Raw Weighted Score:** 92.4 $\to$ **Applied Cap: None $\to$ Final Trust Score: 92 (LOW Risk)**.
- **Evidentiary Diagnosis:** Handled correctly. Auxiliary WhatsApp mentions do not trigger false penalties when official channels exist.

### Case 15: Legitimate Payment-Context Job
- **Input:** Company: `HCLTech` | Email: `careers@hcltech.com` | URL: `https://www.hcltech.com/careers`
- **Description:** Senior Backend Engineer working on "payment gateway protocols, secure bank transfer APIs, automated gift cards redemption".
- **Company Verification:** `status = VERIFIED`, internal score = 95.
- **Rule Flags:** `money_transfer` (35 pts, critical) [FALSE POSITIVE CRITICAL EVIDENCE].
- **5-Dimensional Scores:** Company: 95.0 | Source: 90.0 | Quality: 95.0 | Scam: 65.5 | Contact: 95.0.
- **Raw Weighted Score:** 85.1 $\to$ **Applied Cap: Critical Scam Cap (35) $\to$ Final Trust Score: 35 (HIGH Risk)**.
- **Evidentiary Diagnosis (DISASTROUS FALSE POSITIVE):** A legitimate verified posting from a Fortune Global 500 company is branded as a **High Risk Scam (35/100)** because the job description discusses fintech engineering duties containing the keyword "gift cards".

---

## 4. Current False Positives (Legitimate Jobs Incorrectly Flagged / Slashed)

1. **Case 15 (HCLTech Fintech Engineer):**
   - **Triggered:** `money_transfer` (Critical, 35 pts).
   - **Cause:** Regex pattern `r"gift\s*cards?"` matched the engineering requirement `"processing automated gift cards redemption"`.
   - **Impact:** Crashed a 95-rated posting to **35/100 (HIGH RISK / SCAM)**.
2. **Case 1 (Tata Consultancy Services):**
   - **Triggered:** `email_domain_mismatch` (15 pts) and `company_mismatch` (15 pts).
   - **Cause:** Naive alphanumeric token overlap between `"Tata Consultancy Services"` and `tcs.com`.
   - **Impact:** Slashed score from **~95 down to 77/100**.
3. **Case 3 (Lumina Quantum Systems):**
   - **Triggered:** `email_domain_mismatch` (15 pts) and `company_mismatch` (15 pts).
   - **Cause:** `_company_tokens` tokenizes to `{"lumina", "quantum"}` while domain token is concatenated `{"luminaquantum"}`.
   - **Impact:** Penalized clean startup posting down to **63/100 (MEDIUM Risk)**.

---

## 5. Current False Negatives (Fraudulent Jobs Receiving Tolerant Scores)

1. **Case 8 (WhatsApp-Only Recruitment):**
   - **Score Received:** **59 / 100 (MEDIUM Risk)**.
   - **Cause:** `suspicious_contact` is non-critical (15 pts). With missing URL and email receiving 50 baselines, the raw score stays well above High Risk.
2. **Case 10 (Unrealistic Salary ₹5,000/day Work-From-Home Scam):**
   - **Score Received:** **45 / 100 (MEDIUM Risk)**.
   - **Cause:** `unrealistic_salary` (20 pts), `urgency` (10 pts), and `no_interview` (12 pts) do not trigger any safety cap. Score lands at 45, avoiding High Risk.

---

## 6. Cases Where Missing Evidence Receives Positive / Neutral Credit

1. **Case 8 & 9 (Missing URL & Email):**
   - Received **50.0/100** in Source Credibility and **50.0/100** in Contact Consistency simply by leaving fields empty.
2. **Case 10 (Missing URL):**
   - Received **50.0/100** in Source Credibility, providing an unearned $+10.0$ points to a typing scam.
3. **Case 13 (Missing Credentials for Known Enterprise):**
   - Received `PARTIALLY VERIFIED` (**65.0/100** in Dimension 1) solely for reciting the company name "Wipro".

---

## 7. Cases Where the Same Signal is Double-Counted

1. **Case 4 (TCS with Gmail):**
   - Free email is penalized as `free_email` (-12 pts), `email_domain_mismatch` (-15 pts), and `company_impersonation` (-35 pts).
2. **Case 5 (TCS Lookalike URL):**
   - URL is penalized in `url_analyzer.py` (reducing Dimension 2 to 43.0), and penalized again in `rules.py` as `suspicious_url` (-18 pts in Dimension 4).
3. **Cases 1, 3, 5, 6, 7, 10, 11, 12 (Domain Mismatch):**
   - Flags `email_domain_mismatch` in rules (-15 pts), slashes Dimension 5 to 20.0, and often triggers `company_mismatch` in URL analyzer (-6.0 weighted pts).

---

## 8. Cases Where Legitimate Evidence is Incorrectly Penalized

1. **Case 1 (TCS):** Official recruitment address `careers@tcs.com` penalized by 15 rule points and Dimension 5 drop to 20.0.
2. **Case 1 (TCS):** Official portal `https://www.tcs.com/careers` penalized by Dimension 2 drop to 60.0.
3. **Case 15 (HCLTech):** Job duty mentions of payment protocols penalized as financial extortion.

---

## 9. Cases Where Critical Evidence is Correctly Capped

1. **Case 4 (TCS with Gmail):** Correctly capped at **25** (Impersonation Cap).
2. **Case 5 (TCS Lookalike Domain):** Correctly capped at **25** (Impersonation Cap).
3. **Case 6 (Registration Fee Scam):** Correctly capped at **34** (Critical Scam Cap).
4. **Case 7 (Equipment Deposit Scam):** Correctly capped at **35** (Critical Scam Cap).
5. **Case 11 (Sensitive Information Solicitation):** Correctly capped at **35** (Critical Scam Cap).
6. **Case 12 (Multi-Vector Scam):** Correctly capped at **27** (Critical Scam Cap).

---

## 10. Summary of Architectural Limitations

1. **Context-Free Keyword Matching:** Regex engines in `rules.py` cannot distinguish between job duties (*"develop payment gateway and bank transfer APIs"*) and fraudulent requests (*"pay via bank transfer"*).
2. **Naive Acronym / Token Incompatibility:** No registry lookup or abbreviation mapping in `rules.py` and `url_analyzer.py`.
3. **Missing-Data Inflation Floor:** Missing URLs and missing emails receive neutral 50.0 baselines, giving unverified postings an automatic head start.
4. **Permissive Non-Critical Rules:** WhatsApp-only recruitment (59) and ₹5,000/day typing scams (45) escape High Risk because their flags lack critical cap enforcement.
5. **Score Inversion:** The current scoring engine yields a higher trust score to a WhatsApp-only recruitment scam (**59/100**) than to an authentic fintech posting from HCLTech (**35/100**).

---
*End of Baseline Report. Production source code remains unmodified.*
