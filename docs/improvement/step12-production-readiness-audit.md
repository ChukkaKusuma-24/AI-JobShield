# Step 12: Production Readiness & Complete User Workflow Audit Report

**Date**: 2026-10-03  
**System**: AI JobShield — Intelligent Fake Job & Internship Detection Platform  
**Audit Scope**: End-to-End User Workflow, API Contracts, 5D Evidence Scoring, ML Pipeline, OCR Content Gate, URL Analyzer, Company Verification, Multi-Tenant Database Isolation, Security & Input Abuse, Performance Benchmarks, 20 Golden Cases, and Clean-Environment Evaluation.  
**System State**: FROZEN (ML Model, 5D Weights, Decision Thresholds, Safety Caps).

---

## 1. Executive Summary

The AI JobShield platform was audited for production readiness, robustness, security integrity, and end-to-end user workflows following the completion of Step 9 (Independent Red-Team Validation), Step 10 (System Integration Audit), and Step 11 (Security & Correctness Remediation).

### Key Audit Metrics
- **Regression Suite**: 110 passed, 1 skipped (OCR local engine skipped when Tesseract CLI binary is absent on host), 0 failed.
- **Independent ML Red-Team (N = 64)**:
  - Accuracy: **98.44%**
  - Scam Recall: **100.00%**
  - Precision: **96.97%**
  - False Negatives: **0**
  - False Positives: **1**
  - Brier Score: **0.0166**
  - Training Contamination: **0.00%** (100% unseen test distribution)
- **Golden End-to-End Test Suite (N = 20)**:
  - Legitimate Cases (N = 10): 4 LOW Risk, 6 MEDIUM Risk (startups, academic, and web3 capped at $\le 65$ by Evidence Hierarchy), 0 HIGH Risk (**0% False Positives**).
  - Fraudulent Cases (N = 10): 9 HIGH Risk, 1 MEDIUM Risk (Telegram crypto task investment scam, score 45), 0 LOW Risk (**0% False Negatives**).
- **Security Vectors Tested**: 10 attack classes evaluated (SQL Injection, Stored/Reflected XSS, Command Injection, SSRF, Path Traversal, Unsafe File Upload, Oversized Requests, Unauthenticated Access, Cross-Tenant History Tampering, Model Tampering). Zero vulnerabilities exploited.
- **Latency Benchmarks**:
  - Standard analysis: **30.84 ms**
  - Average repeated analysis: **50.06 ms**
  - Stress analysis (15,000-character description): **59.09 ms** (well within the $< 250\text{ ms}$ real-time budget).
- **Readiness Verdict**: The backend detection, scoring, database, and auth pipeline are production-ready. Minor deployment-phase operational items (Vite production build target, JWT secret length warning, root requirements.txt) have been cataloged with clear remediation guidance.

---

## 2. Complete User Workflow Trace

The operational lifecycle of an analysis request was audited across 17 distinct stages from initial user interaction to database persistence and historical retrieval:

```mermaid
flowchart TD
    A[1. User enters job posting in Web UI] --> B[2. Frontend Client Validation]
    B --> C[3. HTTP POST /api/analyze with JWT]
    C --> D[4. FastAPI Route Handler]
    D --> E[5. Pydantic Request Validation]
    E --> F[6. Orchestrator: run_analysis]
    F --> G[7. URL Analyzer]
    F --> H[8. Company Verifier]
    F --> I[9. Context-Aware Rule Engine]
    F --> J[10. ML Service Model Inference]
    G & H & I & J --> K[11. 5D Evidence Trust Scoring Engine]
    K --> L[12. Natural Language Explanation Builder]
    K --> M[13. Duplicate Job Postings Detector]
    L & M --> N[14. Atomic Database Persistence]
    N --> O[15. JSON Response Serialization]
    O --> P[16. React UI Rendering]
    N --> Q[17. History & Multi-Tenant Retrieval]
```

### Stage-by-Stage Trace Matrix

| Stage | Component | Input | Output | Transformation / Logic | Failure Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. UI Entry** | `AnalyzePage.jsx` | User form inputs | Form state object | Real-time input handling, character counters | Client disables submit if mandatory fields empty |
| **2. Client Validation** | `AnalyzePage.jsx` | Form state | Validated payload | Checks required `title`, `company_name`, `description` | Displays inline warning banner |
| **3. API Request** | `client.js` | Payload + JWT | HTTP Request | Adds `Authorization: Bearer <token>` header, POST to `/api/analyze` | Returns network error toast |
| **4. Route Handler** | `analyze.py` | FastAPI Request | Validated Dependency | Injects DB session (`get_db`) and authenticated User (`get_current_user`) | HTTP 401 if token invalid/missing |
| **5. Schema Validation** | `AnalyzeJobRequest` | Raw JSON | Pydantic model instance | Enforces lengths (desc 30–20,000, title $\le 200$, comp $\le 200$) | HTTP 422 with structured error JSON |
| **6. Orchestrator** | `analyzer.py` | Model fields | Coordinated pipeline | Passes inputs to URL analyzer, company verifier, ML, rules | Caught by global 500 handler |
| **7. URL Analysis** | `url_analyzer.py` | URL string, company | `url_result` dict | Parses URL, checks TLD risk, lookalikes, IP hosts, scheme normalization | Returns `valid=False`, safe fallback |
| **8. Company Verifier** | `company_verifier.py` | Company name, email, URL | `company_result` dict | Normalizes name, checks enterprise registry, matches email domain | Falls back to `UNVERIFIED` (score 45) |
| **9. Rule Engine** | `rules.py` | Job text & metadata | `red_flags`, `positives`, `bonus` | Evaluates contextual regex rules (fee, impersonation, urgency) | Returns empty flags on error |
| **10. ML Inference** | `ml_service.py` | Combined job text | `ml_result` dict | Checks SHA-256 hash, vectorizes text, predicts scam probability | Returns `available=False` gracefully |
| **11. 5D Scoring** | `scoring.py` | D1–D5 signals, ML prob | `trust_score`, `risk_level`, breakdown | Computes weighted sum, evaluates evidence caps ($\le 25, \le 35, \le 65$) | Bounds score strictly to $[0, 100]$ |
| **12. Explanation** | `explain.py` | Flags, breakdown, status | Formatted Markdown text | Categorizes into Critical, Risk Factors, Missing, Positive | Returns default template explanation |
| **13. Duplicate Check** | `duplicate_detector.py` | Description text | `duplicate_result` dict | Trigram similarity against existing postings | Non-blocking; returns empty matches |
| **14. DB Persistence** | `database.py` | Result objects | DB Row IDs | Commits `JobPosting`, `AnalysisResult`, `DuplicateMatch` | Rolls back transaction on DB error |
| **15. Serialization** | `analyzer.py` | ORM instances | JSON dict | Maps ORM columns to API response contract | 500 error if serialization fails |
| **16. UI Render** | `AnalysisResultView.jsx` | API Response JSON | React DOM | Renders SVG Trust Gauge, 5 progress bars, flag chips, explanation | Renders error card if data corrupt |
| **17. History Audit** | `history.py` | User ID, pagination | History List / Item | Enforces multi-tenant ownership filter (`user_id == current_user.id`) | HTTP 403 Forbidden on foreign access |

---

## 3. Frontend → Backend Contract Audit

The API contracts between React Axios calls and FastAPI Pydantic definitions were audited for field alignment, null tolerance, and schema compliance.

### Contract Audit Results

| Test Scenario | Payload Characteristics | Expected HTTP | Actual HTTP | Result |
| :--- | :--- | :---: | :---: | :---: |
| **Normal Request** | All fields valid, corporate email & URL | `200 OK` | `200 OK` | **PASS** |
| **Minimal Request** | Only `title`, `company_name`, `description` (no optional fields) | `200 OK` | `200 OK` | **PASS** |
| **Incomplete Request** | Description length = 15 characters (minimum is 30) | `422 Unprocessable` | `422 Unprocessable` | **PASS** |
| **Malformed Request** | Empty string title (`title: ""`) | `422 Unprocessable` | `422 Unprocessable` | **PASS** |
| **Missing Company** | Company omitted completely from JSON payload | `422 Unprocessable` | `422 Unprocessable` | **PASS** |
| **Max Length Request** | Description length = 19,500 characters | `200 OK` | `200 OK` | **PASS** |
| **Oversized Request** | Description length = 20,500 characters ($> 20,000$) | `422 Unprocessable` | `422 Unprocessable` | **PASS** |
| **Null Optional Fields** | `salary: null`, `email: null`, `url: null` | `200 OK` | `200 OK` | **PASS** |
| **Empty Optional Fields** | `salary: ""`, `email: ""`, `url: ""` | `200 OK` | `200 OK` | **PASS** |

### Response Schema Field Parity
- **Guaranteed Keys Present**: `analysis_id`, `id`, `user_id`, `job_posting_id`, `trust_score`, `risk_level`, `ml` (`available`, `scam_probability`, `top_terms`), `red_flags`, `positive_indicators`, `explanation`, `score_breakdown` (`dimensions`, `cap_applied`, `cap_reason`), `company_verification`, `url_analysis`, `duplicate_result`, `extracted_ocr_text`, `disclaimer`, `created_at`.
- **Zero Field Discards**: All job metadata fields (`title`, `company_name`, `description`, `salary`, `email`, `url`, `location`, `job_type`, `source`) are preserved across database persistence and response serialization.

---

## 4. Analysis Pipeline Results (Workflow Categories A through M)

Thirteen representative job categories were evaluated end-to-end through the complete pipeline:

| Cat | Workflow Description | $P(\text{scam})$ | Flags Triggered | D1 | D2 | D3 | D4 | D5 | Score | Risk | Cap Applied |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | Verified Corporate Job (TCS) | 0.0001 | `vague_description` | 95 | 90 | 15 | 93 | 95 | **81** | **LOW** | NO |
| **B** | Unknown Startup (Aether Labs) | 0.0008 | `vague_description` | 45 | 60 | 15 | 93 | 95 | **63** | **MEDIUM** | NO (Score $\le 65$) |
| **C** | University / Academic (IISc) | 0.6208 | `vague_description` | 45 | 60 | 15 | 74 | 95 | **57** | **MEDIUM** | NO (Score $\le 65$) |
| **D** | Fintech Engineering (Infosys) | 0.0029 | `vague_description` | 95 | 90 | 15 | 93 | 95 | **81** | **LOW** | NO |
| **E** | Crypto / Blockchain (Infosys) | 0.3951 | `vague_description` | 95 | 90 | 15 | 81 | 95 | **78** | **LOW** | NO |
| **F** | Legitimate WhatsApp Coord (Wipro) | 0.0954 | `vague_description` | 95 | 90 | 15 | 90 | 95 | **81** | **LOW** | NO |
| **G** | Legitimate Telegram Dev (Infosys) | 0.3119 | `vague_description` | 95 | 90 | 15 | 84 | 95 | **79** | **LOW** | NO |
| **H** | Registration Fee Scam (QuickCash) | 1.0000 | `fee_request`, `free_email` | 30 | 35 | 15 | 16 | 30 | **25** | **HIGH** | YES (Cap $\le 35$) |
| **I** | Equipment / Deposit Scam (Global) | 1.0000 | `equipment_purchase`, `money_transfer` | 45 | 90 | 15 | 7 | 95 | **35** | **HIGH** | YES (Cap $\le 35$) |
| **J** | Credential Harvesting Scam (TrustBank) | 1.0000 | `sensitive_info`, `email_domain_mismatch` | 45 | 43 | 15 | 5 | 20 | **26** | **HIGH** | YES (Cap $\le 35$) |
| **K** | Company Impersonation (TCS on Gmail) | 0.9384 | `company_impersonation`, `vague_description` | 15 | 35 | 15 | 26 | 10 | **22** | **HIGH** | YES (Cap $\le 25$) |
| **L** | Suspicious Domain Scam (TCS .xyz) | 0.2638 | `company_impersonation`, `urgency` | 15 | 36 | 15 | 27 | 10 | **22** | **HIGH** | YES (Cap $\le 25$) |
| **M** | Multiple Critical Signals Combo | 1.0000 | `fee_request`, `company_impersonation` | 15 | 36 | 15 | 0 | 10 | **14** | **HIGH** | YES (Cap $\le 25$) |

---

## 5. Database & History Multi-Tenant Audit

### Persistence Integrity
- Analyses are persisted atomically across `job_postings`, `analysis_results`, and `duplicate_matches`.
- **Value Parity Check**:
  - Live API `trust_score` = Persisted DB `trust_score` (Verified exact match).
  - Live API `risk_level` = Persisted DB `risk_level` (Verified exact match).
  - ML scam probability, explanation text, and 5D breakdowns are preserved in full JSON fidelity.
  - Timestamps are UTC ISO-8601 formatted and valid.

### Multi-Tenant Isolation
- Tested cross-user isolation with two distinct registered users (`audit.tester@jobshield.local` and `user2@jobshield.local`):
  1. User 1 submits an analysis $\to$ stored under `user_id = 1`.
  2. User 2 queries `/api/history` $\to$ User 1's analysis is strictly omitted (**PASS**).
  3. User 2 directly requests `GET /api/history/{user_1_analysis_id}` $\to$ Returns **HTTP 403 Forbidden** (**PASS**).
  4. User 2 attempts `DELETE /api/history/{user_1_analysis_id}` $\to$ Returns **HTTP 403 Forbidden** (**PASS**).
  5. User 1 deletes their own analysis $\to$ Returns **HTTP 200 OK**; subsequent retrieval returns **HTTP 404 Not Found** (**PASS**).

---

## 6. OCR Gate & Content Validation Audit

The OCR pipeline protects backend resources from non-job processing via `validate_job_related_text()`.

### Content Validation Gate Tests
1. **Legitimate Job Posting Text**:
   - Sample: *"We are hiring a Full-time Senior Backend Engineer at Infosys. Key responsibilities include designing scalable Python APIs..."*
   - Result: `valid = True`, job signal score = 27 (11 distinct signals), anti-signal score = 0 (**ACCEPTED**).
2. **Competitive Programming Contest Submission (Codeforces)**:
   - Sample: *"Codeforces Round 950 (Div. 2). Problem B: Permutation Game. Verdict: Accepted on test 14 using C++20..."*
   - Result: `valid = False`, job signal score = 0, anti-signal score = 34 (**REJECTED**).
3. **E-Commerce Shopping Cart / Receipt**:
   - Sample: *"Order Summary: Order ID #987654. Total amount $149.99. Items: Wireless Headphones. Proceed to checkout..."*
   - Result: `valid = False`, job signal score = 0, anti-signal score = 11 (**REJECTED**).

### File Upload Constraints
- File size limit: 5 MB (`MAX_UPLOAD_MB`). Payloads exceeding 5 MB are rejected with HTTP 400.
- Allowed MIME types: `image/png`, `image/jpeg`, `image/jpg`, `image/webp`. Executables and shell scripts are rejected.
- Graceful Degradation: When Tesseract CLI binary is absent from host, the OCR endpoint returns a structured error message (`Tesseract OCR engine is not installed or configured`) rather than an unhandled 500 crash.

---

## 7. URL Analysis Workflow Audit

| Test URL | Context Company | Expected Risk | Classified Risk | Normalized Host / Behavior | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `https://www.infosys.com/careers` | Infosys | `LOW` | `LOW` | `infosys.com/careers` (Official domain) | **PASS** |
| `https://www.iisc.ac.in/faculty` | IISc | `LOW` | `LOW` | `iisc.ac.in/faculty` (Academic domain) | **PASS** |
| `http://urgent-hiring-now.xyz` | Acme Tech | `MEDIUM`/`HIGH` | `MEDIUM` | Suspicious TLD (.xyz) flag raised | **PASS** |
| `http://tcs-careers-portal.xyz` | TCS | `HIGH` | `HIGH` | Lookalike domain detected | **PASS** |
| `http://user:pass@example.com:8080/apply` | Acme Tech | `HIGH` | `HIGH` | Embedded credentials & non-standard port | **PASS** |
| `infosys.com/careers` | Infosys | `LOW` | `LOW` | Scheme-less URL normalized with `https://` | **PASS** |
| `https://example.com/careers/jobs/...` ($>100$ chars) | Acme Tech | Safe Parse | `LOW` | Extremely long URL parsed without catastrophic backtrack | **PASS** |
| `http://192.168.1.100/apply` | Acme Tech | `HIGH` | `HIGH` | Raw IP host flagged as high risk | **PASS** |

---

## 8. Company Verification & 'W' Domain Preservation Audit

Verified the Step 11 remediation replacing `lstrip("www.")` with `removeprefix("www.")`:

| Target Company | Recruiter Email | Website URL | Verification Status | Score | Preservation Check |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Wipro** | `campus@wipro.com` | `https://www.wipro.com/careers` | `VERIFIED` | 95 | Preserved `wipro.com` (not stripped to `ipro.com`) |
| **Wipro** | `recruiter@gmail.com` | None | `IMPERSONATION_RISK` | 15 | Flagged impersonation on free email |
| **Walmart** | `careers@walmart.com` | `https://www.walmart.com` | `UNVERIFIED` | 45 | Preserved `walmart.com` (not stripped to `almart.com`) |
| **Wells Fargo** | `talent@wellsfargo.com` | `https://wellsfargo.com` | `UNVERIFIED` | 45 | Preserved `wellsfargo.com` (not stripped to `ellsfargo.com`) |
| **T.C.S. Pvt. Ltd.** | `careers@tcs.com` | `https://www.tcs.com` | `VERIFIED` | 95 | Normalized punctuation & suffix to Tata Consultancy Services |

---

## 9. Security Audit & Input Abuse (10 Attack Vectors)

Ten critical attack classes were audited with benign test payloads:

1. **SQL Injection**:
   - Payloads: `title: "Dev'; DROP TABLE job_postings; --"` and `company_name: "Acme' UNION SELECT * FROM users --"`.
   - Result: Handled cleanly by SQLAlchemy parameterized queries. Stored safely as literal text. Database tables intact.
2. **Cross-Site Scripting (XSS)**:
   - Payloads: `title: "<script>alert('xss')</script>"` and `description: "<img src=x onerror=alert('xss')>"`.
   - Result: Inputs stored as raw text without execution. React frontend JSX safely auto-escapes string content during DOM interpolation.
3. **Command Injection**:
   - Payload: `salary: "; calc.exe | whoami"`.
   - Result: Backend does not invoke subshells on user input. Handled purely as string data.
4. **Server-Side Request Forgery (SSRF)**:
   - Payload: `url: "http://169.254.169.254/latest/meta-data/"`.
   - Result: URL analyzer does not make outbound HTTP requests to user-supplied targets. No internal network addresses queried.
5. **Path Traversal & Unsafe Uploads**:
   - File uploads in OCR and Reports routes use secure UUID filename generation and constrain file storage to `uploads/`. Path traversal sequences (`../`) in uploaded filenames are discarded.
6. **Oversized Payloads & DoS**:
   - Payload: Description $> 20,000$ characters.
   - Result: Blocked immediately at FastAPI Pydantic validation with HTTP 422 before reaching rule engine or ML tokenizer.
7. **Unauthenticated Access**:
   - Endpoints `/api/analyze` and `/api/history` strictly enforce JWT authentication. Requests without `Authorization` header yield HTTP 401 Unauthorized.
8. **Broken Object-Level Authorization (BOLA)**:
   - Cross-tenant requests to `/api/history/{id}` return HTTP 403 Forbidden.
9. **Information Leakage / Stack Traces**:
   - FastAPI exception handlers trap all unhandled exceptions, log the stack trace internally, and return a sanitized `{"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}` response (HTTP 500) to clients.
10. **Model Deserialization & Tampering**:
    - Machine learning model loads only after verifying SHA-256 hash against `EXPECTED_MODEL_SHA256` (`636e26e4...`). Tampered or replaced model binaries are rejected with `RuntimeError` before deserialization.

---

## 10. Secrets & Configuration Audit

- **Database Credentials**: Verified that hardcoded database credentials were removed from `backend/app/config.py` in Step 11. Default database URL is `sqlite:///./database/jobshield.db`.
- **Git Tracking**: Verified that `.env` is absent from git tracking and listed in `.gitignore`. Only `.env.example` is committed.
- **Model Checksum**: Enforced in `config.py` via `EXPECTED_MODEL_SHA256`.
- **SMTP Configuration**: Fallback console logging (`SMTP_CONSOLE_FALLBACK`) defaults to `false` in production settings and is enabled only during automated testing.

---

## 11. CORS & API Security

- **CORS Middleware**: Implemented via FastAPI `CORSMiddleware`.
- **Configured Origins**: Loaded from `CORS_ORIGINS` environment variable (defaults to `http://localhost:5173,http://127.0.0.1:5173`).
- **Production Note**: In production deployment, `CORS_ORIGINS` must be explicitly populated with the production domain name to prevent cross-origin requests from untrusted origins.

---

## 12. Error Handling & Graceful Degradation

- **Validation Failure**: Returns structured 422 JSON:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid request",
      "details": [...]
    }
  }
  ```
- **ML Failure Mode**: If `models/jobshield_model.joblib` is missing or unreadable, `ml_service.predict()` returns `{"available": False, "scam_probability": None}`. Scoring engine falls back to deterministic rule scoring without interrupting the user.
- **OCR Failure Mode**: If Tesseract is not installed, OCR route returns HTTP 400 with actionable error text.
- **Unhandled Exceptions**: Caught by `unhandled_handler`, logged to logger, returning sanitized HTTP 500 without leaking stack traces.

---

## 13. Performance & Latency Benchmarks

Tested on local workstation (Python 3.12, Windows 11):

| Operation | Characteristic | Measured Latency | Budget / SLA | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Normal Analysis** | Standard job text, verified company | **30.84 ms** | $< 250\text{ ms}$ | **PASS** |
| **Repeated Analysis (N=5)** | Consecutive requests with duplicate check | **50.06 ms** avg | $< 250\text{ ms}$ | **PASS** |
| **Large Description** | 15,000 characters description stress | **59.09 ms** | $< 500\text{ ms}$ | **PASS** |
| **Model In-Memory Cache** | Single initial load during lifespan | **0.00 ms** per request | $< 5\text{ ms}$ | **PASS** |

---

## 14. Deployment Readiness

- **Backend**:
  - Python requirements specified in `backend/requirements.txt`.
  - Database schema initialized automatically during lifespan startup (`init_db()`).
  - Model integrity verified during startup.
- **Frontend**:
  - React application configured with Vite (`frontend/package.json`).
  - API base URL driven by `VITE_API_BASE`.
  - Production build executed via `npm run build` targeting `dist/`.
- **Identified Deployment Prerequisites**:
  - Run `npm install` inside `frontend/` before executing build.
  - Set `SECRET_KEY` and `JWT_SECRET` to $\ge 32$ characters in production `.env`.
  - Install Tesseract-OCR binary on host system if OCR scanning is enabled.

---

## 15. Frontend Production Audit

- **Environment Config**: `frontend/src/api/client.js` uses `import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'`.
- **Mock Data**: Verified zero mock data or hardcoded score values in production components.
- **Loading & Empty States**:
  - `ResultPage.jsx` renders loading spinner during fetch, error panel on 404/403.
  - `HistoryPage.jsx` renders empty-state banner when no records exist.
- **Reactive UI**: Analysis results seamlessly propagate to `AnalysisResultView.jsx` without requiring page reload.

---

## 16. Golden End-to-End Cases (20 Cases Table & Telemetry)

Twenty complete end-to-end golden test cases were evaluated through the entire system:

| ID | Case Type | Case Name | $P(\text{scam})$ | Company Status | Primary Flags | Score | Risk | Cap Applied |
| :---: | :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| **1** | LEGIT | Verified Corporate Job (TCS) | 0.0000 | `VERIFIED` | None | **92** | **LOW** | NO |
| **2** | LEGIT | Verified Corporate Job (Infosys) | 0.0000 | `VERIFIED` | None | **91** | **LOW** | NO |
| **3** | LEGIT | Unknown Startup (No Scam Signals) | 0.0000 | `UNVERIFIED` | None | **65** | **MEDIUM** | YES ($\le 65$) |
| **4** | LEGIT | University Faculty Recruitment | 0.4117 | `UNVERIFIED` | None | **65** | **MEDIUM** | YES ($\le 65$) |
| **5** | LEGIT | Fintech Payment Engineering | 0.0000 | `UNVERIFIED` | None | **65** | **MEDIUM** | YES ($\le 65$) |
| **6** | LEGIT | Crypto / Web3 Engineering | 0.0002 | `UNVERIFIED` | None | **65** | **MEDIUM** | YES ($\le 65$) |
| **7** | LEGIT | Enterprise Job + WhatsApp Coord | 0.0337 | `VERIFIED` | `vague_description` | **83** | **LOW** | NO |
| **8** | LEGIT | Open Source Tech + Telegram Comm | 0.0019 | `UNVERIFIED` | None | **65** | **MEDIUM** | YES ($\le 65$) |
| **9** | LEGIT | Senior Staff Salary Posting | 0.0000 | `VERIFIED` | None | **91** | **LOW** | NO |
| **10** | LEGIT | Legitimate Post-Offer Onboarding | 0.9993 | `VERIFIED` | `vague_description` | **74** | **MEDIUM** | NO |
| **11** | SCAM | Registration Fee Scam | 1.0000 | `UNVERIFIED` | `fee_request`, `unrealistic_salary` | **26** | **HIGH** | YES ($\le 35$) |
| **12** | SCAM | Equipment / Advance Check Scam | 1.0000 | `UNVERIFIED` | `equipment_purchase`, `money_transfer` | **35** | **HIGH** | YES ($\le 35$) |
| **13** | SCAM | Sensitive Credential Harvesting | 1.0000 | `UNVERIFIED` | `sensitive_info`, `vague_description` | **35** | **HIGH** | YES ($\le 35$) |
| **14** | SCAM | Company Impersonation (TCS on Gmail) | 0.9530 | `IMPERSONATION_RISK` | `company_impersonation`, `vague_desc` | **23** | **HIGH** | YES ($\le 25$) |
| **15** | SCAM | Lookalike Domain Scam | 0.9976 | `IMPERSONATION_RISK` | `company_impersonation`, `urgency` | **17** | **HIGH** | YES ($\le 25$) |
| **16** | SCAM | WhatsApp-Only Task / Rating Scam | 1.0000 | `UNVERIFIED` | `vague_description` | **39** | **HIGH** | NO |
| **17** | SCAM | Telegram Crypto Investment Scam | 0.9999 | `UNVERIFIED` | `vague_description` | **45** | **MEDIUM** | NO |
| **18** | SCAM | Multiple Critical Signals Combo Scam | 1.0000 | `IMPERSONATION_RISK` | `money_transfer`, `company_impersonation` | **14** | **HIGH** | YES ($\le 25$) |
| **19** | SCAM | Unrealistic Salary + Urgency Scam | 1.0000 | `UNVERIFIED` | `free_email`, `vague_description` | **31** | **HIGH** | NO |
| **20** | SCAM | Airport Gate Pass / Security Deposit | 0.9999 | `UNVERIFIED` | `money_transfer`, `free_email` | **26** | **HIGH** | YES ($\le 35$) |

### Telemetry Summary
- **Legitimate Postings (N = 10)**: 4 LOW, 6 MEDIUM, 0 HIGH. **Zero False Positives.**
- **Scam Postings (N = 10)**: 9 HIGH, 1 MEDIUM, 0 LOW. **Zero False Negatives.**

---

## 17. Regression Test Results

The full regression test battery was executed:

1. **Pytest Regression Suite**: **110 passed, 1 skipped**, 0 failed (16.21s).
   - Skipped test: `tests/test_ocr_job_gate_api.py` (marked to skip gracefully when local Tesseract binary is uninstalled).
2. **Step 9 Independent Red-Team Suite**: **64 challenge cases** evaluated.
   - Accuracy: **98.44%**
   - Recall: **100.00%**
   - Precision: **96.97%**
   - False Negatives: **0**
   - False Positives: **1**
   - Brier Score: **0.0166**
3. **Step 10 Remediation Regression Tests** (`tests/test_step10_fixes_regression.py`): **9/9 passed**.
   - Verified `removeprefix("www.")` domain normalization.
   - Verified `wipro.com` preservation in URL analyzer and company verifier.
   - Verified sanitization of DB credentials in `config.py`.
   - Verified `workstation` equipment rule and `wire` money transfer rule.
   - Verified model SHA-256 verification and tampered model rejection.

---

## 18. Clean-Environment Evaluation

- **Backend Dependencies**: `backend/requirements.txt` specifies all required libraries (FastAPI, Uvicorn, SQLAlchemy, Scikit-learn, Joblib, PyJWT, Pydantic, etc.). Verified compatible with standard Python 3.12 installations.
- **Frontend Dependencies**: `frontend/package.json` contains valid dependency graph (React 18, Vite, Axios, TailwindCSS). Verified clean lockfile resolution via `npm install --package-lock-only`.
- **Database Provisioning**: Self-contained SQLite initialization on first startup (`init_db()`), eliminating external database setup friction for evaluation.
- **Model Checksum Check**: Self-verifying SHA-256 pipeline ensures runtime integrity without external network calls.

---

## 19. Findings & Recommendations

All findings from the audit are cataloged strictly under the five designated severities (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`):

### Summary Table

| Finding ID | Severity | Affected Component | Summary |
| :---: | :---: | :--- | :--- |
| **SEC-12-01** | `MEDIUM` | `frontend/` build workflow | `node_modules` not pre-installed on clean clones; requires `npm install` before build |
| **SEC-12-02** | `LOW` | `backend/app/auth.py` / tests | PyJWT Insecure Key Length Warning during test execution when key $<32$ bytes |
| **SEC-12-03** | `LOW` | Root workspace layout | Missing root `requirements.txt` redirecting to `backend/requirements.txt` |
| **SEC-12-04** | `INFO` | `frontend/src/api/client.js` | Production deployment requires setting `VITE_API_BASE` and backend `CORS_ORIGINS` |
| **SEC-12-05** | `INFO` | `backend/app/services/ocr_service.py` | Local OCR execution requires external OS-level Tesseract installation |

---

### Detailed Findings

#### Finding SEC-12-01
- **Severity**: `MEDIUM`
- **Affected Component**: `frontend/`
- **Evidence**: Running `npm run build` directly on a fresh workspace clone fails with `'vite' is not recognized as an internal or external command`.
- **Reproduction**: Clone repository into a new directory and execute `npm run build` in `frontend/` without prior `npm install`.
- **Impact**: Automated build/CI scripts that expect `npm run build` to succeed immediately will fail.
- **Recommended Remediation**: Document `cd frontend && npm install && npm run build` in the deployment instructions and Dockerfile / CI workflow.

#### Finding SEC-12-02
- **Severity**: `LOW`
- **Affected Component**: `backend/app/auth.py` and test harnesses
- **Evidence**: PyJWT issues warning during test runs: `InsecureKeyLengthWarning: The HMAC key is 28 bytes long, which is below the minimum recommended length of 32 bytes for SHA256. See RFC 7518 Section 3.2`.
- **Reproduction**: Run `pytest tests/test_api.py`.
- **Impact**: While tests pass, short keys reduce cryptographic entropy.
- **Recommended Remediation**: Ensure test harnesses and `.env.example` specify keys of 32 or more bytes (e.g. 64-character hex strings).

#### Finding SEC-12-03
- **Severity**: `LOW`
- **Affected Component**: Root directory
- **Evidence**: Python dependencies are defined in `backend/requirements.txt`. There is no root-level `requirements.txt`.
- **Reproduction**: Inspect root directory files; running `pip install -r requirements.txt` at root fails with file not found.
- **Impact**: PaaS deployment tools (e.g., Heroku, Render, Railway) that look for a root-level `requirements.txt` by default may fail during automated buildpack detection unless configured with build context `backend/`.
- **Recommended Remediation**: Add a root `requirements.txt` containing `-r backend/requirements.txt`.

#### Finding SEC-12-04
- **Severity**: `INFO`
- **Affected Component**: `frontend/src/api/client.js` & `backend/app/config.py`
- **Evidence**: Frontend defaults to `http://127.0.0.1:8000/api` when `VITE_API_BASE` is unset. Backend defaults CORS to `http://localhost:5173,http://127.0.0.1:5173`.
- **Reproduction**: Deploy frontend build to a public domain without setting environment variables; API calls route to localhost.
- **Impact**: Expected behavior for development; requires production environment variable configuration for staging/production environments.
- **Recommended Remediation**: Set `VITE_API_BASE` and `CORS_ORIGINS` in production environment manifests.

#### Finding SEC-12-05
- **Severity**: `INFO`
- **Affected Component**: `backend/app/services/ocr_service.py`
- **Evidence**: `test_ocr_job_gate_api` is skipped when Tesseract is not installed on the host.
- **Reproduction**: Run tests on a machine without `tesseract.exe` installed.
- **Impact**: OCR image text extraction is unavailable without the external system binary, though the system degrades gracefully without crashing.
- **Recommended Remediation**: Include `apt-get install -y tesseract-ocr` or Windows installer links in setup documentation.

---

## 20. Strict Stop Condition Adherence

This audit was conducted strictly as a **READ-ONLY EVALUATION**:
- No ML model weights or hyper-parameters were modified.
- No model retraining was executed.
- No scoring formulas, 5D weights, or safety caps were changed.
- No risk thresholds were altered.
- No frontend components were redesigned.
- No discovered issues were automatically patched.

All findings have been documented, verified, and presented for review.
