# Deterministic Rule Engine Audit: Analysis of All 14 Rules

## 1. Overview and Audit Objectives

This document provides a comprehensive audit of the 14 deterministic rules in AI-JobShield prior to implementing Step 5 contextual enhancements. 

The audit evaluates each rule across:
- **Detection logic** (regex patterns, syntactic thresholds, structural checks)
- **Evidence class** (`CRITICAL_EVIDENCE`, `NEGATIVE_EVIDENCE`, `POSITIVE_EVIDENCE`, `MISSING_EVIDENCE`)
- **Severity & penalty points**
- **Potential false positives** (legitimate job features incorrectly flagged)
- **Potential false negatives** (evasive scam phrasing that bypasses detection)
- **Cross-rule overlap & redundancy**
- **Multi-dimensional impacts** (Dimension 1–5 scoring interactions)
- **Contextual awareness** (differentiating job responsibilities from applicant-directed instructions)

---

## 2. Comprehensive Audit of All 14 Rules

### Rule 1: `fee_request`
- **Label**: Upfront fee / pay-to-join request
- **Severity**: `critical` | **Points**: 35 | **Evidence Class**: `CRITICAL_EVIDENCE`
- **Detection Logic**: 
  Matches regex patterns: `registration\s+fee`, `application\s+fee`, `training\s+fee`, `security\s+deposit`, `processing\s+fee`, `pay\s+to\s+(?:get|join|start)`, `fee\s+(?:to|for)\s+(?:join|register|apply)`, `joining\s+fee`.
- **Potential False Positives**:
  - Explicit negations: *"No application fee is charged by our company"*, *"We never request registration fees"*, *"Free application process"*.
  - Company benefits: *"Company covers all training fees and certification costs"*, *"Tuition fee reimbursement program"*.
  - Non-recruitment fees: *"Knowledge of billing processing fees in fintech applications"*.
- **Potential False Negatives**:
  - Evasive terminology: *"Refundable document verification charge"*, *"Onboarding kit courier fee of ₹850"*, *"Nominal seat reservation amount"*.
- **Overlaps**: Overlaps with `equipment_purchase` (when deposit is requested for hardware) and `money_transfer` (when fee is to be paid via UPI/crypto).
- **Multi-Dimensional Impact**: Triggering `fee_request` activates the `has_critical_scam` hard cap ($\le 35$) on the total trust score, collapses the Scam Detection dimension (Dimension 4), and strips all positive indicator bonuses.
- **Contextual Assessment**: **Lacks negation handling.** Must distinguish applicant-directed fee demands from employer-paid training and negative disclaimers ("no fee").

---

### Rule 2: `money_transfer`
- **Label**: Requests money, gift cards, or crypto
- **Severity**: `critical` | **Points**: 35 | **Evidence Class**: `CRITICAL_EVIDENCE`
- **Detection Logic**:
  Matches transactional patterns involving `gift cards`, `western union`, `crypto`, `bitcoin`, `ethereum`, `upi`, `money`, `funds`, `cash`, `deposit`, `transfer`.
- **Potential False Positives**:
  - Software & Engineering jobs: *"Building APIs for bank transfer processing"*, *"Integrating UPI payment gateway"*, *"Developing cryptocurrency exchange backend microservices"*, *"Managing corporate gift card rewards infrastructure"*.
  - Financial roles: *"Treasury management including wire transfers and bank reconciliations"*.
- **Potential False Negatives**:
  - Evasive transactional instructions: *"Purchase Amazon digital vouchers and send codes to recruiter"*, *"Wire funds via third-party escrow"*.
- **Overlaps**: Overlaps with `fee_request` (e.g., paying a fee via UPI).
- **Multi-Dimensional Impact**: Activates the `has_critical_scam` hard cap ($\le 35$), collapsing the trust score to High Risk.
- **Contextual Assessment**: **Previously a major false positive source (Case 15).** Requires strict applicant-directed syntax: `APPLICANT + ACTION + FINANCIAL OBJECT` (e.g., *"Send money to recruiter"*, *"Pay via UPI to start"*), while completely ignoring technical descriptions of financial systems.

---

### Rule 3: `equipment_purchase`
- **Label**: Requests payment for equipment / laptop / software / tools
- **Severity**: `critical` | **Points**: 35 | **Evidence Class**: `CRITICAL_EVIDENCE`
- **Detection Logic**:
  Matches phrases like `buy/purchase/pay for ... laptop/equipment/software/kit`, `laptop fee`, `equipment deposit/fee/charge`, `home office kit/setup fee`.
- **Potential False Positives**:
  - Employer procurement duties: *"Responsible for purchasing office equipment and software licenses for team"* (Procurement / IT Admin role).
  - Employer-provided benefits: *"Company will buy and provide all home office equipment including MacBook"*.
  - Negations: *"No equipment fee required; company provides all hardware"*.
- **Potential False Negatives**:
  - *"Mandatory security deposit required prior to dispatching company assets"*, *"Purchase our approved software bundle from vendor"*.
- **Overlaps**: Sub-type of `fee_request`.
- **Multi-Dimensional Impact**: Triggers hard cap ($\le 35$).
- **Contextual Assessment**: Must ensure the instruction demands the *applicant* pay for or buy equipment, rather than describing the company providing equipment or an IT admin's purchasing responsibilities.

---

### Rule 4: `company_impersonation`
- **Label**: Company impersonation detected (claimed brand with mismatched/free contact)
- **Severity**: `critical` | **Points**: 35 | **Evidence Class**: `CRITICAL_EVIDENCE`
- **Detection Logic**:
  Triggered when `company_status == "IMPERSONATION_RISK"` or when a verified enterprise identity is paired with a free webmail address (e.g., `tcs.recruitment@gmail.com`).
- **Potential False Positives**:
  - Very rare after Step 4 normalization. Could occur if a tiny unknown firm shares an acronym with a conglomerate unless registry matching is verified.
- **Potential False Negatives**:
  - Recruiter using an obscure custom domain that mimics the company name without containing company tokens.
- **Overlaps**: Overlaps with `free_email` and `email_domain_mismatch`.
- **Multi-Dimensional Impact**: Dominates Dimensions 1, 4, and 5; enforces the strongest guardrail cap ($\le 25$). Suppresses unearned positive legitimacy bonuses.
- **Contextual Assessment**: Correctly handled in Step 4 by suppressing secondary flags (`free_email`, `email_domain_mismatch`) when impersonation is triggered.

---

### Rule 5: `sensitive_info`
- **Label**: Requests sensitive personal/financial information
- **Severity**: `critical` | **Points**: 30 | **Evidence Class**: `CRITICAL_EVIDENCE`
- **Detection Logic**:
  Regex search for keywords: `aadhaar`, `aadhar`, `ssn`, `pan`, `passport`, `bank details/account/statement`, `otp`, `cvv`, `card number`, `debit card`, `credit card`.
- **Potential False Positives**:
  - Legitimate HR documentation: *"Selected candidates must present original Aadhaar and PAN card for verification during joining"*.
  - Travel requirements: *"Valid passport required for international travel"*.
  - Technical / API development: *"Integration with Aadhaar e-KYC APIs"*, *"PCI-DSS compliant credit card processing"*.
- **Potential False Negatives**:
  - Photos of ID cards: *"Submit selfie holding your government ID"*, *"Share net-banking login screenshot"*.
- **Overlaps**: None directly.
- **Multi-Dimensional Impact**: Enforces the critical scam cap ($\le 35$).
- **Contextual Assessment**: **Lacks distinction between credentials (OTP, CVV, PIN) and standard identity documents (Passport, PAN).** OTP/CVV/PIN requests are always critical fraud. Aadhaar/PAN/bank requests are suspicious only when solicited *upfront* before an interview or via unofficial channels (WhatsApp/Gmail).

---

### Rule 6: `unrealistic_salary`
- **Label**: Unrealistic salary for role/experience
- **Severity**: `high` | **Points**: 20 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Flags daily salary $\ge \text{INR } 3,000/\text{day}$ or monthly salary $\ge \text{INR } 1,50,000/\text{month}$ when matching entry/fresher/intern cues.
- **Potential False Positives**:
  - Legitimate high-paying tech internships (e.g., Google/Uber intern stipends of ₹1.5L–₹2L/month).
  - Senior roles mentioning "mentoring junior interns" where high salary belongs to the senior role.
- **Potential False Negatives**:
  - Hourly or weekly scam rates: *"Earn ₹25,000 per week for 2 hours work"*.
  - Percentage commission scams: *"Earn 20% commission on daily deposits"*.
- **Overlaps**: Often paired with `no_interview` and `urgency`.
- **Multi-Dimensional Impact**: Deducts 20 points from Scam Detection dimension (Dimension 4).
- **Contextual Assessment**: Needs cross-referencing with task complexity (e.g. typing, ad clicking vs engineering) and role seniority.

---

### Rule 7: `suspicious_contact`
- **Label**: Suspicious contact method (WhatsApp/Telegram-only)
- **Severity**: `high` | **Points**: 15 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Regex search for `whatsapp only`, `telegram only`, `contact on whatsapp`, `message via whatsapp/telegram`.
- **Potential False Positives**:
  - Legitimate enterprises offering WhatsApp for candidate queries alongside official email/website: *"For queries regarding your application, message our helpdesk on WhatsApp"*.
- **Potential False Negatives**:
  - Obfuscated handles: *"ping on wa +91..."*, *"DM on tg: @..."*.
- **Overlaps**: Interacts with Contact Consistency dimension (Dimension 5).
- **Multi-Dimensional Impact**: Deducts 15 points in Dimension 4; drives Dimension 5 score to 20.0.
- **Contextual Assessment**: WhatsApp/Telegram must **not** be treated as automatic fraud. When used as an *auxiliary* channel by a verified enterprise, it should carry low/no penalty. When used as the *exclusive* hiring channel by an unverified entity, it is a significant negative signal.

---

### Rule 8: `email_domain_mismatch`
- **Label**: Email domain does not match company name
- **Severity**: `high` | **Points**: 15 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Triggered when recruiter email domain does not match resolved company identity tokens or registered official domains.
- **Potential False Positives**:
  - Authorized third-party recruiting agencies hiring on behalf of clients (e.g., `careers@adecco.com` hiring for `Siemens`).
- **Potential False Negatives**:
  - Domains containing partial brand names but registered by scammers.
- **Overlaps**: Suppressed when `company_impersonation` fires.
- **Multi-Dimensional Impact**: Penalizes Dimension 4 (-15 pts) and Dimension 5 (Contact Consistency = 20.0).
- **Contextual Assessment**: Resolved cleanly in Step 4. Suppressed when official domains or verified acronyms match.

---

### Rule 9: `free_email`
- **Label**: Personal/free email used for claimed company
- **Severity**: `medium` | **Points**: 12 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Matches domain against `free_email_domains.json` (Gmail, Yahoo, Outlook, etc.) for non-impersonated entities.
- **Potential False Positives**:
  - Early-stage startups, sole proprietorships, individual tutors, domestic contractors.
- **Potential False Negatives**:
  - Temporary burner email domains not in the static list.
- **Overlaps**: Suppressed if `company_impersonation` fires.
- **Multi-Dimensional Impact**: Dimension 4 (-12 pts), Dimension 5 (Contact Consistency = 30.0).
- **Contextual Assessment**: Free email is not proof of fraud, but indicates lack of professional corporate infrastructure. Capping in Medium Risk ($40 - 65$) for unknown startups is appropriate.

---

### Rule 10: `no_interview`
- **Label**: No interview / guaranteed / instant selection
- **Severity**: `medium` | **Points**: 12 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Matches `no interview`, `no experience needed/required`, `guaranteed job/selection/placement`, `instant selection`, `direct joining`.
- **Potential False Positives**:
  - Genuine entry-level jobs: *"No prior experience needed; full training provided"*.
  - Academic courses with placement assistance: *"Guaranteed placement assistance upon graduation"*.
- **Potential False Negatives**:
  - *"Walk-in offer letter distribution without assessment"*.
- **Overlaps**: Often accompanies `vague_description` and `urgency`.
- **Multi-Dimensional Impact**: Deducts 12 points from Dimension 4.
- **Contextual Assessment**: Bare *"no experience needed"* is very common in legitimate retail/internship postings. The dangerous scam signal is *"no interview + guaranteed selection / direct joining"*.

---

### Rule 11: `urgency`
- **Label**: Urgency / pressure language
- **Severity**: `medium` | **Points**: 10 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Matches `within 24 hours`, `limited seats`, `immediately`, `final warning`, `hurry up`, `last chance`, `urgently hiring`, `apply now or`.
- **Potential False Positives**:
  - Standard hiring phrases: *"Immediate joiners preferred"*, *"Urgently hiring for critical production incident response team"*.
- **Potential False Negatives**:
  - High-pressure countdown timers or psychological panic language not in list.
- **Overlaps**: None directly.
- **Multi-Dimensional Impact**: Deducts 10 points from Dimension 4.
- **Contextual Assessment**: Pressure language like *"final warning"*, *"hurry up"*, *"within 24 hours or lose your slot"* is predatory. Legitimate corporate postings saying *"immediate joiners required"* should not be overly penalized.

---

### Rule 12: `vague_description`
- **Label**: Vague job description
- **Severity**: `medium` | **Points**: 10 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Triggered if description length < 80 characters OR neither responsibility cues nor qualification cues are found.
- **Potential False Positives**:
  - Concise legitimate postings (e.g. senior referrals, brief announcements directing to external portal).
- **Potential False Negatives**:
  - Lengthy generic copy-paste text describing company culture without actual job requirements.
- **Overlaps**: Deducts points in Dimension 3 (Job Description Quality) and Dimension 4.
- **Multi-Dimensional Impact**: -25 in Quality dimension, -10 in Scam dimension.
- **Contextual Assessment**: Must avoid double punishment. If Quality dimension already penalizes vague postings down to 15.0, Dimension 4 should only penalize if paired with suspicious contact or salary.

---

### Rule 13: `suspicious_url`
- **Label**: URL shows suspicious characteristics
- **Severity**: `medium` | **Points**: 12 (Override: 18) | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Triggered when `url_risk_level == "HIGH"` in `url_analyzer.py`.
- **Potential False Positives**:
  - Clean URLs that have high risk score due solely to tracking parameters or HTTP.
- **Potential False Negatives**:
  - Phishing sites disguised on clean cloud domains (e.g., `google-forms` scams).
- **Overlaps**: Direct overlap with Dimension 2 (Source / URL Credibility).
- **Multi-Dimensional Impact**: Dimension 2 evaluates URL risk directly ($100 - \text{risk score}$). Flagging `suspicious_url` in Dimension 4 penalizes the job a second time unless it involves active phishing or lookalike domains.
- **Contextual Assessment**: Dimension 4 should only penalize URLs when they represent active deception (e.g. `lookalike_domain`, credentials harvesting, punycode), rather than penalizing generic URL characteristics twice.

---

### Rule 14: `caps_exclaim`
- **Label**: Excessive caps / exclamation / poor writing cues
- **Severity**: `low` | **Points**: 5 | **Evidence Class**: `NEGATIVE_EVIDENCE`
- **Detection Logic**:
  Triggered when `caps_ratio > 0.35` or `exclamations >= 4`.
- **Potential False Positives**:
  - Technical descriptions dense with acronyms: *"AWS, GCP, CI/CD, SQL, REST APIs, HTML5, CSS3, JSON, TCP/IP, Docker, K8s"*.
- **Potential False Negatives**:
  - Sophisticated spear-phishing descriptions with polished grammar.
- **Overlaps**: Quality dimension (Dimension 3).
- **Multi-Dimensional Impact**: Deducts 15 in Dimension 3, deducts 5 in Dimension 4.
- **Contextual Assessment**: Should exclude standard capitalized technical acronyms from `caps_ratio` computation so tech-heavy descriptions are not penalized.

---

## 3. Cross-Rule Dependency & Double-Counting Matrix

| Signal / Fact | Primary Rule | Evidence Class | Dimension 1 (Company) | Dimension 2 (Source) | Dimension 3 (Quality) | Dimension 4 (Scam) | Dimension 5 (Contact) | Guardrail Cap |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Known Enterprise + Gmail** | `company_impersonation` | `CRITICAL` | 15.0 | - | - | 45.0 | 10.0 | **Cap $\le 25$** |
| **Known Enterprise + Lookalike URL** | `lookalike_domain` | `CRITICAL` | 15.0 | 5.0 | - | 32.0 | 20.0 | **Cap $\le 25$** |
| **Unknown Startup + Gmail** | `free_email` | `NEGATIVE` | 40.0 | - | - | 68.0 | 30.0 | **Cap $\le 65$** |
| **Applicant Fee Demanded** | `fee_request` | `CRITICAL` | - | - | - | 45.0 | - | **Cap $\le 35$** |
| **Equipment Purchase Demanded** | `equipment_purchase` | `CRITICAL` | - | - | - | 45.0 | - | **Cap $\le 35$** |
| **OTP / PIN / Card Requested** | `sensitive_info` | `CRITICAL` | - | - | - | 50.0 | - | **Cap $\le 35$** |
| **WhatsApp-Only Hiring** | `suspicious_contact` | `NEGATIVE` | - | - | - | 65.0 | 20.0 | None |
| **Auxiliary WhatsApp on Verified Enterprise** | Advisory Notice | `POSITIVE` | 95.0 | 90.0 | 90.0 | 95.0 | 95.0 | None |
| **Technical Fintech Mention (Bank/Crypto)** | Job Context | `POSITIVE` | 95.0 | 90.0 | 90.0 | 95.0 | 95.0 | None |

---

## 4. Action Plan for Step 5 Enhancements

1. **Context-Aware Fee Detection (`fee_request`)**:
   - Add negative assertion filter (`no application fee`, `never charges`, `free`).
   - Add employer-benefit filter (`company covers training fee`, `tuition reimbursement`).
   - Require applicant-directed payment cues (`candidate must pay`, `fee required before interview`).

2. **Context-Aware Financial Transaction Detection (`money_transfer`)**:
   - Disallow bare technology nouns (`crypto`, `bitcoin`, `bank transfer`, `gift cards`, `upi`) from triggering fraud flags.
   - Require `APPLICANT + ACTION + FINANCIAL OBJECT` syntax.

3. **Multi-Tiered Sensitive Information Detection (`sensitive_info`)**:
   - Tier 1 (Critical Extortion): `otp`, `pin`, `cvv`, `card number`, `netbanking password` $\rightarrow$ always critical.
   - Tier 2 (Premature Document Solicitation): `aadhaar`, `pan`, `bank account/statement` $\rightarrow$ flag only when directed to unverified channels (WhatsApp, Telegram, Gmail) or required *prior* to interview.
   - Tier 3 (Legitimate Context): Mentions of background verification via HR portals or passport for travel $\rightarrow$ no penalty.

4. **Context-Aware Contact Detection (`suspicious_contact`)**:
   - If company is `VERIFIED` and has official email/domain, auxiliary WhatsApp contact is downgraded from high severity to weak/no penalty.
   - If company is `UNVERIFIED` and contact is WhatsApp-only with no corporate channels $\rightarrow$ full negative flag.

5. **Context-Aware Urgency & No Interview (`urgency`, `no_interview`)**:
   - Differentiate `"immediate joiner preferred"` from `"final warning / 24 hours to secure placement"`.
   - Differentiate `"no prior experience needed"` (common legitimate phrasing) from `"no interview guaranteed selection"`.

6. **Acronym-Aware Caps Detection (`caps_exclaim`)**:
   - Filter recognized technical uppercase tokens (`AWS`, `SQL`, `API`, `REST`, `CI/CD`, etc.) before evaluating caps ratio.
