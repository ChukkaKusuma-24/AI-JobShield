# STEP 10 — END-TO-END SCORING & SYSTEM INTEGRATION AUDIT

**Audit Date**: October 3, 2026  
**Status**: COMPLETE (Read-Only Audit)  
**System State**: FROZEN (No code, model, weights, or scoring modifications made)  
**Model SHA256**: `636E26E42B5A4179A42F9E9161DD7692D4F63146F1475659021605B9676BF1A2`  

---

## 1. Architecture Trace

Every incoming job analysis request executes deterministically through an end-to-end 12-stage pipeline:

```
[1. HTTP Request] POST /api/analyze (JSON payload: title, company_name, description, salary, email, url, location, job_type)
        │
        ▼
[2. FastAPI Router & Schema Validation] (Pydantic AnalyzeRequest enforces field length bounds, trims strings, strips whitespace)
        │
        ▼
[3. Analyzer Orchestrator] run_analysis() in backend/app/services/analyzer.py
        │
        ├──► [4. URL Heuristic Analyzer] url_analyzer.analyze_url()
        │      • Validates URL syntax and extracts hostname (offline, no network fetching)
        │      • Checks suspicious TLDs (.xyz, .top, etc.), IP hostnames, credential keywords, and lookalike patterns
        │      • Computes URL risk_level (LOW, MEDIUM, HIGH) and risk_score
        │
        ├──► [5. Company Identity & Registry Verifier] company_verifier.verify_company()
        │      • Resolves aliases, acronyms (e.g., "Tata Consultancy Services" <-> "TCS"), and legal suffixes
        │      • Checks verified enterprise registry (verified_companies.json) and local database
        │      • Checks email domain and website domain against official enterprise domains
        │      • Assigns company status: VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, or IMPERSONATION_RISK
        │
        ├──► [6. Machine Learning Classifier] ml_service.predict()
        │      • Text preprocessing: entities masked to `<COMPANY>`, `<EMAIL>`, `<URL>`, `<PHONE>`, `<MONEY>`, `<NUM>`
        │      • Feature extraction: TF-IDF unigrams & bigrams (max_features=5000, sublinear_tf=True)
        │      • Calibrated probability estimation: Logistic Regression with CalibratedClassifierCV
        │      • Extracts top contributing n-gram terms with model feature weights
        │
        ├──► [7. Context-Aware Rule Engine] rules.analyze_rules()
        │      • Evaluates 14 deterministic rules with linguistic boundary context
        │      • Context awareness disables false alarms for fintech payments, crypto, HR onboarding, and high salaries
        │      • Outputs: red_flags, positive_indicators, positive_bonus
        │
        ├──► [8. Evidence-Based 5D Trust Engine] scoring.compute_trust_score()
        │      • D1: Company Verification (25% weight)
        │      • D2: Source Credibility (20% weight)
        │      • D3: Job Posting Quality (15% weight)
        │      • D4: Scam Detection (30% weight: 70% Rule Penalty Score + 30% ML Score)
        │      • D5: Contact Consistency (10% weight)
        │      • Evaluates Evidence Hierarchy (Positive, Missing, Negative, Critical)
        │      • Enforces Hard Safety Caps: Impersonation (≤25), Critical Scam (≤35), Unverified Company (≤65)
        │
        ├──► [9. Natural Language Explainer] explain.build_explanation()
        │      • Synthesizes structured markdown explanation from verified evidence and active flags
        │      • Lists critical scam evidence, negative risks, missing unverified items, and positive signals
        │      • Appends ML pattern indicators and mandatory consumer security disclaimer
        │
        ├──► [10. Duplicate Detection Engine] duplicate.find_duplicates()
        │      • Computes TF-IDF cosine similarity against historical postings and user scam reports
        │
        ├──► [11. Database Persistence] SQLAlchemy Session
        │      • Persists JobPosting entity
        │      • Persists AnalysisResult entity with serialized JSON breakdown and timestamps
        │      • Persists DuplicateMatch associations
        │      • Commits transaction atomically
        │
        ▼
[12. API Serialization & Response] serialize_analysis()
        │
        ▼
[Frontend Consumption] React 18 UI renders TrustGauge, 5D breakdown cards, Evidence list, and Explanations
```

---

## 2. ML Integration

### 2.1 Model Artifact Verification
- **Production Artifact**: `models/jobshield_model.joblib` and `backend/models/jobshield_model.joblib` are verified identical.
- **Artifact SHA256**: `636E26E42B5A4179A42F9E9161DD7692D4F63146F1475659021605B9676BF1A2`.
- **Model Path Resolution**: Deterministic via `backend/app/config.py` using `ROOT_DIR / "models" / "jobshield_model.joblib"`.
- **Stale Model Audit**: No legacy or conflicting model artifacts exist in the repository.

### 2.2 Inference Telemetry
- `ml_service.is_available()` returns `True`.
- `scam_probability` is strictly bounded within $[0.0, 1.0]$.
- **Legitimate corporate sample**: $P(\text{scam}) = 0.0178$ ($1.78\%$). Top negative-weight (legitimizing) terms: `senior software` (-0.112), `software engineer` (-0.019), `company` (-0.029).
- **Blatant scam sample**: $P(\text{scam}) = 1.0000$ ($100.0\%$). Top positive-weight (scam) terms: `fee` (+0.2575), `deposit` (+0.1875), `contact` (+0.1504), `whatsapp` (+0.1422), `urgent` (+0.1228).
- **Top Terms Integration**: The `CalibratedClassifierCV` wrapper cleanly delegates to the underlying estimator's linear coefficients (`clf.coef_[0]`), preserving `top_terms` generation without throwing runtime exceptions.

---

## 3. Scoring Integration

### 3.1 Mathematical Formulation
The trust scoring engine strictly adheres to the 5-dimensional evidence-based specification:

$$\text{Raw Trust Score} = 0.25 \times D_1 + 0.20 \times D_2 + 0.15 \times D_3 + 0.30 \times D_4 + 0.10 \times D_5$$

Where:
- **$D_1$ (Company Verification, 25%)**: Evaluates enterprise registry matches, official domains, and corporate standing.
- **$D_2$ (Source & URL Credibility, 20%)**: Evaluates URL structural safety, TLD risk, and domain matching.
- **$D_3$ (Job Posting Quality, 15%)**: Evaluates presence of responsibilities, qualifications, realistic compensation, and structural clarity.
- **$D_4$ (Scam Detection, 30%)**:
  $$D_4 = 0.70 \times \text{Rule Penalty Score} + 0.30 \times \text{ML Score}$$
  $$\text{ML Score} = (1.0 - P(\text{scam})) \times 100.0$$
  $$\text{Rule Penalty Score} = \text{clamp}(\text{Base} - \sum \text{Rule Points}, 0.0, 100.0)$$
  - Base is $100.0$ if positive enterprise legitimacy is confirmed.
  - Base is $80.0$ if no negative evidence is detected but positive legitimacy is missing.
- **$D_5$ (Contact & Domain Consistency, 10%)**: Evaluates alignment between recruiter contact channel and employer domain.

### 3.2 Verification of Weights
The weights remain frozen:
- Company Verification: $25\%$
- Source Credibility: $20\%$
- Job Quality: $15\%$
- Scam Detection: $30\%$
- Contact Consistency: $10\%$
$$\sum \text{Weights} = 0.25 + 0.20 + 0.15 + 0.30 + 0.10 = 1.00 \quad (100\%)$$

---

## 4. Double-Counting Audit

An empirical audit was executed across combinations of free email, domain mismatch, suspicious URL, and impersonation:

| Test Case | Inputs | Triggered Flags | Dimension Scores | Final Score | Cap Applied |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Case A** | Unknown company + Gmail | `free_email` | $D_1=30, D_2=35, D_3=60, D_4=77.6, D_5=30$ | **51** (MEDIUM) | No |
| **Case B** | Website abc.com + Gmail | `free_email` | $D_1=30, D_2=90, D_3=60, D_4=77.6, D_5=30$ | **56** (MEDIUM) | No |
| **Case C** | Suspicious URL (.xyz) + Gmail | `free_email` | $D_1=30, D_2=45, D_3=60, D_4=77.6, D_5=30$ | **53** (MEDIUM) | No |
| **Case D** | TCS + Suspicious URL + Gmail | `company_impersonation`, `suspicious_url` | $D_1=15, D_2=36, D_3=60, D_4=40.5, D_5=10$ | **25** (HIGH) | Yes (Impersonation Cap) |

### 4.1 Double-Counting Findings
1. **Free Email vs. Impersonation De-duplication**: In `rules.py` line 443, when `company_status == "IMPERSONATION_RISK"`, the rule engine explicitly suppresses the `free_email` flag. This prevents stacking duplicate penalties for the same personal email address.
2. **Dimension Independence**: Free email reduces $D_5$ (Contact Consistency) to $30.0$ and applies a mild 12-point rule penalty in $D_4$. The penalties do not cascade into $D_2$ or $D_3$.
3. **Hard Cap Bounding**: Even when multiple signals coincide (Gmail + domain mismatch + suspicious URL), the hard cap mechanism acts as a ceiling rather than an additive decrement, preventing scores from falling below zero or double-penalizing the user.

---

## 5. Hard-Cap Audit

The four primary safety caps were tested against adversarial edge cases:

| Case | Scenario | Raw Weighted Score | Final Score | Cap Status & Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Case E** | Critical scam fee + verified enterprise text | 73.4 | **35** | **CAP APPLIED**: Critical scam indicator present (upfront fee request) |
| **Case F** | Brand impersonation + high ML legitimacy | 41.7 | **25** | **CAP APPLIED**: Impersonation risk detected (free email for corporate brand) |
| **Case G** | Payment scam + verified company | 68.2 | **35** | **CAP APPLIED**: Critical scam indicator present |
| **Case H** | Unverified company + highly polished text | 48.0 | **48** | Unverified cap ceiling ($\le 65$) respected; score is within bounds |

### 5.1 Hard-Cap Findings
- **Protection Verified**: High ML legitimacy ($P(\text{scam}) < 0.05$) is strictly subordinate to deterministic safety caps. When upfront fees or brand impersonation are detected, the trust score is forcibly capped at $\le 35$ or $\le 25$, regardless of how polished or convincing the job description text appears.

---

## 6. Evidence Hierarchy Findings

The four evidence classes established in Step 3 were validated:

1. **`POSITIVE_EVIDENCE`**:
   - Requires affirmative, independently verifiable data (e.g., registry match, matching official corporate domain, corporate email).
   - Grants full dimension scores ($D_1 \ge 90, D_5 \ge 95$).
2. **`MISSING_EVIDENCE`**:
   - Absence of an email, URL, or company registration is treated as missing information, NOT malicious fraud.
   - For an unprovided URL, $D_2$ is assigned a neutral score of $35.0$ and flagged as `MISSING_EVIDENCE`. It does not trigger negative red flags.
   - For an unprovided recruiter email, $D_5$ is assigned $35.0$ and flagged as `MISSING_EVIDENCE`.
   - The absence of crude scam keywords sets the $D_4$ base to $80.0$ (`NO_NEGATIVE_EVIDENCE_DETECTED`), preventing unknown startups from receiving false $100/100$ scores merely because they lacked obvious scam words.
3. **`NEGATIVE_EVIDENCE`**:
   - Suspicious signals (personal email for unknown company, urgency phrasing, vague text) apply proportional point deductions without triggering catastrophic score collapse.
4. **`CRITICAL_EVIDENCE`**:
   - Brand impersonation, upfront fee demands, equipment advance-fee checks, and credential harvesting trigger hard caps ($\le 25$ or $\le 35$) and zero out positive bonus points.

---

## 7. Rule / ML Interaction & Contextual Rule Testing

Comparison across the contextual scenarios evaluated in Step 5:

| Case Scenario | Rule Flags | ML $P(\text{scam})$ | Dimension 4 Score | Final Trust Score | Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fintech / Payment Processing** | None | $0.0000$ | 100.0 | **92** | LOW |
| **Crypto Blockchain Engineering** | None | $0.0507$ | 91.5 | **81** | LOW |
| **Senior Salary (₹60 LPA)** | None | $0.0009$ | 93.0 | **83** | LOW |
| **Urgent Legitimate Hiring** | None | $0.5972$ | 82.1 | **84** | LOW |
| **Legitimate HR Onboarding** | `sensitive_info` | $0.9998$ | 42.0 | **35** | HIGH |

### 7.1 Rule/ML Synergy Observations
- **Fintech & Crypto Resilience**: Legitimate engineering postings discussing payment gateways, bank transfers, and crypto smart contracts trigger zero false rule flags, and the ML model predicts $P(\text{scam}) \le 0.05$. Both systems synergistically output Low Risk scores ($81$–$92$).
- **Urgent Hiring**: The contextual rule engine correctly ignored "urgently hiring" in the corporate context. The ML model was mildly uncertain ($P(\text{scam}) = 0.5972$), but the 70/30 blend and strong verified enterprise standing preserved an $84$ Low Risk rating.
- **Onboarding Boundary Sensitivity**: When text explicitly enumerates sensitive documents (passport, PAN card) without strong surrounding context, both the rule engine and ML model trigger, dropping the score to $35$.

---

## 8. Explanation Consistency

Generated explanations were audited against triggered rule signals and evidence classes:

| Test Case | Triggered Flags | Rendered Explanations | Hallucinated Signals? |
| :--- | :--- | :--- | :--- |
| **Fee Scam** | `fee_request`, `suspicious_contact`, `urgency` | Accurately quotes upfront fee text and WhatsApp contact | **None** |
| **Impersonation** | `company_impersonation` | Explicitly states: "Claimed company is recognized enterprise ('Tata Consultancy Services'), but recruiter is using a free/personal email (@gmail.com)" | **None** |
| **Suspicious Domain** | `suspicious_url` | Accurately identifies high-risk URL domain `.xyz` | **None** |
| **Credential Scam** | `sensitive_info` | Quotes netbanking password, OTP, and CVV request | **None** |
| **Legit Corporate** | None | Highlights verified registry record, matching domain, and HTTPS website | **None** |

**Verdict**: Explanations strictly map 1:1 to triggered evidence and rules. No hallucinated rules or fake claims appear.

---

## 9. API / Database Integration

### 9.1 FastAPI Routers & Schemas
- `AnalyzeRequest` in `backend/app/schemas.py` validates `title` ($\ge 2$ chars), `company_name` ($\ge 2$ chars), and `description` ($\ge 30$ chars).
- Trailing and leading whitespace are cleaned by Pydantic field validators.
- Request payload fields directly and completely map to `analyzer.run_analysis()` parameters.

### 9.2 Database Persistence
- `JobPosting` and `AnalysisResult` tables are populated correctly via SQLAlchemy ORM.
- The `AnalysisResult` stores:
  - `trust_score` (Integer)
  - `risk_level` (String: LOW, MEDIUM, HIGH)
  - `ml_scam_probability` (Float)
  - `rule_risk_points` (Integer)
  - `red_flags` (JSON string)
  - `score_breakdown` (JSON string containing full 5D telemetry and cap metadata)
- Deserialization in `serialize_analysis()` preserves exact scores, risks, and probabilities without floating-point truncation or rounding shifts.

---

## 10. Frontend Findings

### 10.1 Architecture & Contract Compliance
- **API Endpoint**: `frontend/src/api/client.js` targets `POST /api/analyze` with an Axios client using `import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'`.
- **Payload Shape**: `AnalyzePage.jsx` transmits `{ title, company_name, description, salary, email, url, location, job_type }`, matching the backend schema exactly.
- **Score Rendering**: `AnalysisResultView.jsx` directly binds `data.trust_score` and `data.risk_level` to the `TrustGauge` component. No hardcoded or mock scores exist in UI components.
- **Dimension Breakdown**: Renders all 5 dimensions ($D_1$–$D_5$) dynamically with weights, scores, and status badges.
- **Evidence Cap Notification**: The frontend actively inspects `score_breakdown.cap_applied` and displays an explicit banner: `🛡️ Evidence Cap Applied: {breakdown.cap_reason}`.

---

## 11. End-to-End Golden-Case Results (20 Cases)

A controlled benchmark of 20 golden cases (10 legitimate, 10 fraudulent) was evaluated end-to-end:

| ID | Category | Case Name | ML $P(\text{scam})$ | Company Status | Primary Flags | Score | Risk Level | Safety Cap |
| :---: | :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: |
| **1** | Legitimate | Verified Corporate Job (TCS) | $0.0000$ | VERIFIED | None | **92** | LOW | No |
| **2** | Legitimate | Verified Corporate Job (Infosys) | $0.0000$ | VERIFIED | None | **91** | LOW | No |
| **3** | Legitimate | Unknown Startup (Clean JD) | $0.0000$ | UNVERIFIED | None | **65** | MEDIUM | Yes (Unverified Cap) |
| **4** | Legitimate | University Faculty Recruitment | $0.4117$ | UNVERIFIED | None | **65** | MEDIUM | Yes (Unverified Cap) |
| **5** | Legitimate | Fintech Payment Engineering | $0.0000$ | UNVERIFIED | None | **65** | MEDIUM | Yes (Unverified Cap) |
| **6** | Legitimate | Crypto / Web3 Protocol Engineer | $0.0002$ | UNVERIFIED | None | **65** | MEDIUM | Yes (Unverified Cap) |
| **7** | Legitimate | Enterprise Job + WhatsApp Coord. | $0.0337$ | IMPERSONATION_RISK* | `company_impersonation`* | **25** | HIGH* | Yes (Bug #1)* |
| **8** | Legitimate | Open Source Tech + Telegram | $0.0019$ | UNVERIFIED | None | **65** | MEDIUM | Yes (Unverified Cap) |
| **9** | Legitimate | Senior Staff Salary Posting (Google) | $0.0000$ | VERIFIED | None | **91** | LOW | No |
| **10** | Legitimate | Post-Offer Onboarding Verification | $0.9993$ | VERIFIED | `vague_description` | **74** | MEDIUM | No |
| **11** | Scam | Upfront Registration Fee | $1.0000$ | UNVERIFIED | `fee_request`, `unrealistic_salary` | **26** | HIGH | Yes (Critical Cap) |
| **12** | Scam | Equipment / Advance Check Scam | $1.0000$ | UNVERIFIED | `vague_description` | **52** | MEDIUM | No |
| **13** | Scam | Sensitive Credential Harvesting | $1.0000$ | UNVERIFIED | `sensitive_info` | **35** | HIGH | Yes (Critical Cap) |
| **14** | Scam | Brand Impersonation (TCS on Gmail) | $0.9530$ | IMPERSONATION_RISK | `company_impersonation` | **23** | HIGH | Yes (Impersonation Cap) |
| **15** | Scam | Lookalike Domain Scam (.xyz) | $0.9976$ | IMPERSONATION_RISK | `company_impersonation`, `urgency` | **17** | HIGH | Yes (Impersonation Cap) |
| **16** | Scam | WhatsApp-Only Rating Task Scam | $1.0000$ | UNVERIFIED | `vague_description` | **39** | HIGH | No |
| **17** | Scam | Telegram Crypto Investment Scam | $0.9999$ | UNVERIFIED | `vague_description` | **45** | MEDIUM | No |
| **18** | Scam | Multiple Critical Signals Combo | $1.0000$ | IMPERSONATION_RISK | `company_impersonation`, `sensitive_info` | **14** | HIGH | Yes (Impersonation Cap) |
| **19** | Scam | Unrealistic Salary + Urgency Scam | $1.0000$ | UNVERIFIED | `free_email` | **31** | HIGH | No |
| **20** | Scam | Airport Gate Pass Deposit Scam | $0.9999$ | UNVERIFIED | `money_transfer`, `free_email` | **26** | HIGH | Yes (Critical Cap) |

*\*Note on Case 7: Flagged as impersonation due to the `lstrip("www.")` domain parsing defect documented in Section 14.*

---

## 12. Security Audit

A comprehensive security audit across 10 vectors revealed the following posture:

| Vector | Status | Evidence & Code Path | Severity |
| :--- | :--- | :--- | :--- |
| **1. Unsafe User Input** | **PASS** | Strict Pydantic models with `strip()` and length constraints in `backend/app/schemas.py`. | INFO |
| **2. SQL Injection** | **PASS** | 100% parameterized SQLAlchemy ORM queries (`query.filter()`). Zero raw SQL execution or concatenation. | INFO |
| **3. Cross-Site Scripting (XSS)** | **PASS** | React JSX auto-escapes all rendered values. Zero instances of `dangerouslySetInnerHTML` across `frontend/src`. | INFO |
| **4. Command Injection** | **PASS** | No `os.system` or `subprocess.Popen(..., shell=True)`. `pytesseract` takes array arguments. | INFO |
| **5. Unsafe URL Fetching (SSRF)** | **PASS** | `url_analyzer.py` performs 100% offline regex parsing without outbound HTTP network connections. | INFO |
| **6. Path Traversal** | **PASS** | Uploaded files in `ocr.py` and `reports.py` use `uuid.uuid4().hex` filenames; user-supplied paths are discarded. | INFO |
| **7. Hardcoded Secrets in Config** | **DEFECT** | `backend/app/config.py` contains default fallback MySQL credentials (`root:kusuma%23%26247`). | **HIGH** |
| **8. Debug Information Leakage** | **PASS** | Global exception handler catches unhandled exceptions and returns generic `INTERNAL_ERROR` without stack traces. | INFO |
| **9. Unrestricted File Upload** | **PASS** | Enforces 5 MB size ceiling, MIME/extension allowlists, and `PIL.Image.open().verify()` image validation. | INFO |
| **10. Unsafe Model Deserialization** | **DEFECT** | `joblib.load()` executes unauthenticated Python pickle deserialization without cryptographic SHA256 integrity verification. | **MEDIUM** |

---

## 13. Regression Results

All regression suites were executed:
- **Pytest Regression Suite (89 Tests)**:
  - `tests/test_history_and_scoring.py`: 7 passed
  - `tests/test_evidence_hierarchy.py`: 25 passed
  - `tests/test_company_identity.py`: 13 passed
  - `tests/test_rule_engine_context.py`: 27 passed
  - `tests/test_ml_validation.py`: 17 passed
  - **Total**: **89 passed, 0 failed** in 9.94s.
- **Step 9 Red-Team Evaluation (64 Cases)**:
  - Accuracy: $98.44\%$
  - Scam Recall: $100.00\%$
  - Scam Precision: $96.97\%$
  - False Negatives: $0$
  - False Positives: $1$ (Academic faculty post)
  - Brier Score: $0.0166$
- **15-Case Baseline Benchmark**: Zero regressions observed.

---

## 14. Critical Issues

### Issue 1: `lstrip("www.")` Domain Truncation Bug
- **Severity**: **CRITICAL**
- **Affected Files**:
  - `backend/app/services/company_verifier.py` (lines 53, 65)
  - `backend/app/services/rules.py` (line 369)
  - `backend/app/services/url_analyzer.py` (line 152)
- **Root Cause**:
  Python's `str.lstrip("www.")` treats the argument as a set of characters (`{'w', '.'}`), NOT as a prefix string. When stripping domains that begin with the letter `w`, it strips leading `w` characters:
  - `"wipro.com".lstrip("www.")` $\rightarrow$ `"ipro.com"`
  - `"walmart.com".lstrip("www.")` $\rightarrow$ `"almart.com"`
  - `"wellsfargo.com".lstrip("www.")` $\rightarrow$ `"ellsfargo.com"`
  - `"wordpress.org".lstrip("www.")` $\rightarrow$ `"ordpress.org"`
- **Consequence**:
  Legitimate recruitment emails and websites from verified enterprises starting with `w` fail domain matching. The verifier flags legitimate enterprise postings as `IMPERSONATION_RISK`, crashing trust scores from $90+$ down to $25$.

### Issue 2: Hardcoded Production Database Credentials in `config.py`
- **Severity**: **HIGH**
- **Affected File**: `backend/app/config.py` (line 70)
- **Root Cause**:
  `DATABASE_URL: str = "mysql+pymysql://root:kusuma%23%26247@localhost:3306/ai_jobshield"` exposes hardcoded database credentials in default configuration files tracked in git.
- **Consequence**:
  Security credential exposure and automated secret scanner alerts.

---

## 15. Non-Critical Issues

### Issue 3: Incomplete Keyword Synonyms in Advance-Fee Equipment Scam Rule
- **Severity**: **MEDIUM**
- **Affected File**: `backend/app/services/rules.py` (lines 34–64)
- **Root Cause**:
  The equipment and money transfer regex patterns match specific nouns (`laptop`, `equipment`, `software`, `kit`) and verbs (`pay`, `send`, `transfer`, `deposit`), but omit common advance-fee scam terms such as `workstation` and `wire`.
- **Consequence**:
  Scams instructing candidates to "purchase your home office workstation" and "wire $2,500 via Zelle" are caught at $1.0000$ by the ML model, but bypass the deterministic critical rule, preventing the $\le 35$ hard cap from engaging (resulting in score 52 instead of $\le 35$).

### Issue 4: Missing `import pytest` in Standalone Integration Test
- **Severity**: **LOW**
- **Affected File**: `tests/test_ocr_job_gate_api.py` (line 22)
- **Root Cause**:
  `test_ocr_job_gate_api.py` attempts `pytest.skip(...)` when a live backend server is not running on port 8000, but fails with `NameError: name 'pytest' is not defined` because `pytest` was not imported.

### Issue 5: Unverified Joblib Model Loading
- **Severity**: **LOW**
- **Affected File**: `backend/app/services/ml_service.py` (line 71)
- **Root Cause**:
  `joblib.load()` performs unauthenticated pickle deserialization without pre-verifying the file's SHA256 checksum against an expected hash manifest.

---

## 16. Recommended Fixes (For Subsequent Execution Steps)

> **IMPORTANT**: In accordance with the Step 10 stop condition, none of these fixes have been implemented in this step. They are documented here for subsequent implementation:

1. **Fix Domain Prefix Stripping**:
   Replace all instances of `.lstrip("www.")` with `.removeprefix("www.")` (Python 3.9+) or `re.sub(r"^www\.", "", ...)` in `company_verifier.py`, `rules.py`, and `url_analyzer.py`.
2. **Sanitize Default Database Configuration**:
   Change `DATABASE_URL` default in `backend/app/config.py` to an unprivileged generic default (e.g. `sqlite:///./jobshield.db` or `mysql+pymysql://user:password@localhost:3306/ai_jobshield`) and load actual credentials strictly from environment variables.
3. **Expand Scam Lexicon Synonyms**:
   Add `workstation` to `EQUIPMENT_PATTERNS` and `wire` to `DIRECTIVE_MONEY_PATTERNS` in `backend/app/services/rules.py`.
4. **Add Import to Test Script**:
   Add `import pytest` to `tests/test_ocr_job_gate_api.py`.
5. **Model Checksum Verification**:
   Add an optional SHA256 check before `joblib.load()` in `ml_service.py` to guarantee model artifact integrity.

---

## 17. Audit Conclusion & Baseline State

- Step 10 Read-Only System Integration Audit completed with zero production code modified during the audit phase.
- All 89 baseline regression tests passed with zero regressions.
- The pipeline was systematically audited and defects documented.

---

## 18. Post-Audit Targeted Defect Resolutions & Verification

Following user authorization, the 5 identified defects were surgically resolved without altering ML weights, 5D trust weights, caps, or scoring thresholds:

### 18.1 Implemented Fixes
1. **Domain Prefix Stripping Fix**:
   - Replaced all 4 instances of `.lstrip("www.")` with `.removeprefix("www.")` in:
     - `backend/app/services/company_verifier.py` (lines 53, 65)
     - `backend/app/services/rules.py` (line 369)
     - `backend/app/services/url_analyzer.py` (line 152)
   - Verified that enterprise domains starting with `w` (Wipro, Walmart, Wells Fargo, etc.) are perfectly preserved.
2. **Database Configuration Sanitization**:
   - Removed plaintext credentials from default configuration in `backend/app/config.py`.
   - Set default `DATABASE_URL` to local SQLite (`sqlite:///./database/jobshield.db`), allowing password-less local operations out of the box while maintaining `.env` override capability for production MySQL.
3. **Advance-Fee Equipment Scam Lexicon Coverage**:
   - Added `workstation` and `computer` to `EQUIPMENT_PATTERNS` in `backend/app/services/rules.py`.
   - Added `wire` and payment app directives (`zelle`, `wire transfer`) to `DIRECTIVE_MONEY_PATTERNS`.
4. **Pytest Import in Gate API Test**:
   - Added `import pytest` to `tests/test_ocr_job_gate_api.py`.
5. **Model SHA-256 Cryptographic Integrity Verification**:
   - Implemented `compute_model_sha256()` and integrity validation in `backend/app/services/ml_service.py`.
   - The model artifact hash (`636e26e42b5a4179a42f9e9161dd7692d4f63146f1475659021605b9676bf1a2`) is verified prior to deserialization; tampered artifacts are immediately rejected and logged.

### 18.2 Verification & Regression Results
- **Dedicated Step 10 Fixes Regression Suite (`tests/test_step10_fixes_regression.py`)**:
  - 9 tests covering `removeprefix` domain cleaning, Wipro verification, DB sanitization, workstation/wire rules, advance check cap, model SHA-256 verification, and tampering rejection.
  - **9 / 9 passed (100%)**.
- **Full Pytest Regression Suite**:
  - **98 / 98 passed (100%)** (89 baseline + 9 new regression tests).
- **Step 9 Red-Team Evaluation (64 Cases)**:
  - Accuracy: $98.44\%$, Scam Recall: $100.00\%$, False Negatives: $0$.
- **Affected Golden Cases Resolved**:
  - **Case 7 (Wipro Enterprise + WhatsApp Coordinator)**: Score improved from 25 (HIGH) to **83 (LOW Risk)**; Company Status: **VERIFIED**; zero false impersonation alarms.
  - **Case 12 (Advance Check Workstation Scam)**: Score improved from 52 (MEDIUM) to **35 (HIGH Risk)**; triggers `equipment_purchase` and `money_transfer`; critical scam cap applied.

