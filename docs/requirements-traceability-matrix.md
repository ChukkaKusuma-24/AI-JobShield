# Requirements Traceability Matrix (RTM)
## AI JobShield — Intelligent Recruitment Scam Detection & Credibility Analysis Platform

This document tracks the bidirectional traceability between **Software Requirements (SRS)**, architectural modules, REST API endpoints, database entities, automated test cases, and their verification statuses in **AI JobShield**.

---

## 1. Traceability Matrix

| Requirement ID | Feature Description | Architectural Module / Service | API Endpoint | Database Entity | Test Case ID | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **REQ-AUTH-01** | User Registration with complexity validation | `app/routers/auth.py`, `app/schemas.py` | `POST /api/auth/register` | `users` | **TC-AUTH-01**, **TC-AUTH-02** | **VERIFIED** |
| **REQ-AUTH-02** | Bcrypt password hashing (salted) | `app/security.py` | `POST /api/auth/register` | `users.password_hash` | **TC-AUTH-01** | **VERIFIED** |
| **REQ-AUTH-03** | 6-Digit Email OTP generation & SMTP dispatch | `app/services/email_service.py` | `POST /api/auth/register` | `email_otps` | **TC-AUTH-01**, **TC-AUTH-05** | **VERIFIED** |
| **REQ-AUTH-04** | Email verification enforcement gate | `app/routers/auth.py`, `app/deps.py` | `POST /api/auth/login` | `users.is_verified` | **TC-AUTH-04** | **VERIFIED** |
| **REQ-AUTH-05** | OTP validation, account activation & JWT issuance | `app/routers/auth.py`, `app/security.py` | `POST /api/auth/verify-email` | `users`, `email_otps` | **TC-AUTH-05**, **TC-AUTH-06** | **VERIFIED** |
| **REQ-AUTH-06** | OTP resend with rate-limit cooldown | `app/services/email_service.py` | `POST /api/auth/resend-otp` | `email_otps` | **TC-AUTH-05** | **VERIFIED** |
| **REQ-AUTH-07** | Authenticate user & issue signed JWT Bearer token | `app/routers/auth.py`, `app/security.py` | `POST /api/auth/login` | `users` | **TC-AUTH-07**, **TC-AUTH-08** | **VERIFIED** |
| **REQ-AUTH-08** | Password reset flow via OTP validation | `app/routers/auth.py`, `app/services/email_service.py` | `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` | `users`, `email_otps` | **TC-AUTH-09** | **VERIFIED** |
| **REQ-AUTH-09** | Protected route authorization with Bearer token | `app/deps.py` | `GET /api/auth/me`, All protected APIs | `users` | **TC-AUTH-10** | **VERIFIED** |
| **REQ-ING-01** | Manual job opportunity form input validation | `app/routers/analyze.py`, `app/schemas.py` | `POST /api/analyze` | `job_postings` | **TC-SCORE-01**, **TC-SCORE-02** | **VERIFIED** |
| **REQ-ING-02** | Minimum description length validation (≥ 30 chars) | `app/schemas.py` | `POST /api/analyze` | `job_postings.description` | **TC-SCORE-02** | **VERIFIED** |
| **REQ-OCR-01** | Screenshot upload & MIME/size validation (≤ 5MB) | `app/services/ocr_service.py` | `POST /api/ocr/analyze` | `ocr_results`, `uploads/` | **TC-OCR-06** | **VERIFIED** |
| **REQ-OCR-02** | Image preprocessing & Tesseract text extraction | `app/services/ocr_service.py` | `POST /api/ocr/analyze` | `ocr_results` | **TC-OCR-06** | **VERIFIED** |
| **REQ-OCR-03** | Job relevance gatekeeper (reject non-job images) | `app/services/job_content_validator.py` | `POST /api/ocr/analyze` | None (rejected early) | **TC-OCR-01**, **TC-OCR-02**, **TC-OCR-05** | **VERIFIED** |
| **REQ-OCR-04** | Contact & company hint extraction from OCR text | `app/services/ocr_service.py` | `POST /api/ocr/analyze` | `ocr_results` | **TC-OCR-03**, **TC-OCR-04** | **VERIFIED** |
| **REQ-VER-01** | Curated enterprise registry lookup & alias match | `app/services/company_verifier.py` | `POST /api/company/verify`, `POST /api/analyze` | `companies`, `verified_companies.json` | **TC-COMP-01** | **VERIFIED** |
| **REQ-VER-02** | Brand impersonation detection (free email mismatch)| `app/services/company_verifier.py` | `POST /api/analyze` | `companies` | **TC-COMP-02**, **TC-SCORE-04** | **VERIFIED** |
| **REQ-VER-03** | Local URL security heuristic inspection | `app/services/url_analyzer.py` | `POST /api/url/analyze`, `POST /api/analyze` | `analysis_results.url_analysis` | **TC-URL-01**, **TC-URL-02**, **TC-URL-03** | **VERIFIED** |
| **REQ-RUL-01** | 14 Deterministic red flag pattern detection | `app/services/rules.py` | `POST /api/analyze` | `analysis_results.red_flags` | **TC-SCORE-03**, **TC-SCORE-05** | **VERIFIED** |
| **REQ-RUL-02** | Positive legitimacy indicators & bonus points | `app/services/rules.py` | `POST /api/analyze` | `analysis_results.positive_indicators` | **TC-SCORE-01** | **VERIFIED** |
| **REQ-ML-01** | TF-IDF text vectorization & SGD Logistic inference | `app/services/ml_service.py` | `POST /api/analyze` | `models/jobshield_model.joblib` | **TC-SCORE-01**, **TC-SCORE-03** | **VERIFIED** |
| **REQ-ML-02** | Top influential vocabulary extraction for explainability | `app/services/ml_service.py` | `POST /api/analyze` | `analysis_results.score_breakdown` | **TC-SCORE-01** | **VERIFIED** |
| **REQ-SCR-01** | 5-Dimensional weighted credibility score calculation | `app/services/scoring.py` | `POST /api/analyze` | `analysis_results.trust_score` | **TC-SCORE-01**, **TC-SCORE-02** | **VERIFIED** |
| **REQ-SCR-02** | Impersonation risk safety cap (Trust Score ≤ 25) | `app/services/scoring.py` | `POST /api/analyze` | `analysis_results.trust_score` | **TC-SCORE-04** | **VERIFIED** |
| **REQ-SCR-03** | Critical scam safety cap (Trust Score ≤ 35) | `app/services/scoring.py` | `POST /api/analyze` | `analysis_results.trust_score` | **TC-SCORE-03**, **TC-SCORE-05** | **VERIFIED** |
| **REQ-SCR-04** | Unverified company evidence cap (Trust Score ≤ 65)| `app/services/scoring.py` | `POST /api/analyze` | `analysis_results.trust_score` | **TC-SCORE-02** | **VERIFIED** |
| **REQ-SCR-05** | Structured natural language explainability report | `app/services/explain.py` | `POST /api/analyze` | `analysis_results.explanation` | **TC-SCORE-01**, **TC-SCORE-03** | **VERIFIED** |
| **REQ-HST-01** | Persistent scan history storage linked to user | `app/services/analyzer.py` | `POST /api/analyze` | `analysis_results`, `job_postings` | **TC-HIST-01** | **VERIFIED** |
| **REQ-HST-02** | Paginated reverse-chronological history retrieval | `app/routers/history.py` | `GET /api/history` | `analysis_results` | **TC-HIST-02** | **VERIFIED** |
| **REQ-HST-03** | Strict multi-tenant user data isolation | `app/routers/history.py` | `GET /api/history`, `GET /api/history/{id}` | `analysis_results.user_id` | **TC-HIST-03**, **TC-HIST-04** | **VERIFIED** |
| **REQ-HST-04** | Record deletion with cascade purge | `app/routers/history.py` | `DELETE /api/history/{id}` | `analysis_results`, `job_postings` | **TC-HIST-05** | **VERIFIED** |
| **REQ-DSH-01** | Security dashboard metrics & 14-day activity chart | `app/routers/dashboard.py` | `GET /api/dashboard` | `analysis_results` | **TC-DSH-01** | **VERIFIED** |
| **REQ-COM-01** | Community scam reporting submission | `app/routers/reports.py` | `POST /api/reports` | `scam_reports` | **TC-REP-01** | **VERIFIED** |
| **REQ-FDB-01** | Analysis accuracy feedback collection | `app/routers/feedback.py` | `POST /api/feedback` | `feedback` | **TC-FDB-01** | **VERIFIED** |

---

## 2. Traceability Summary

* **Total Tracked Requirements**: 34 functional and security criteria.
* **Test Case Coverage**: 100% of functional requirements mapped to executable test scenarios.
* **Verification Outcome**: All 34 requirements verified against the automated test suite (`pytest`) and database constraints.
