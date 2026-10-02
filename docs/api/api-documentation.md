# AI JobShield — API Documentation

This document provides formal REST API specifications for all endpoints implemented in **AI JobShield**, detailing HTTP methods, URL endpoints, authentication requirements, request parameters, response structures, and status codes.

---

## 1. API Endpoints Overview

| Category | Method | Endpoint | Description | Authentication |
| :--- | :---: | :--- | :--- | :---: |
| **System Health** | `GET` | `/api/health` | Service status, ML/OCR readiness, SMTP state | Public |
| **Authentication** | `POST` | `/api/auth/register` | Register new user & dispatch 6-digit Email OTP | Public |
| **Authentication** | `POST` | `/api/auth/verify-email` | Confirm OTP, mark verified & return JWT | Public |
| **Authentication** | `POST` | `/api/auth/resend-otp` | Dispatch a new verification code to email | Public |
| **Authentication** | `POST` | `/api/auth/login` | Authenticate credentials & return JWT | Public |
| **Authentication** | `POST` | `/api/auth/forgot-password` | Generate and email password reset OTP | Public |
| **Authentication** | `POST` | `/api/auth/reset-password` | Validate reset OTP and update password | Public |
| **Authentication** | `GET` | `/api/auth/me` | Fetch profile of currently authenticated user | Bearer JWT |
| **Job Analysis** | `POST` | `/api/analyze` | Perform full 5D credibility analysis on job posting | Bearer JWT |
| **OCR Processing**| `POST` | `/api/ocr/analyze` | Preprocess screenshot, run OCR & validate gate | Bearer JWT |
| **OCR Processing**| `GET` | `/api/ocr/my-uploads` | List user's historical OCR uploaded artifacts | Bearer JWT |
| **Company Verification** | `POST` | `/api/company/verify` | Standalone company registry & domain lookup | Optional / Public |
| **URL Security** | `POST` | `/api/url/analyze` | Standalone local heuristic URL security inspection | Optional / Public |
| **Analysis History** | `GET` | `/api/history` | Paginated, filterable user scan history | Bearer JWT |
| **Analysis History** | `GET` | `/api/history/{analysis_id}` | Fetch detailed evaluation of specific past scan | Bearer JWT |
| **Analysis History** | `DELETE`| `/api/history/{analysis_id}` | Permanently delete analysis record & cascades | Bearer JWT |
| **Dashboard** | `GET` | `/api/dashboard` | Aggregated security metrics & 14-day timeline | Bearer JWT |
| **Scam Reports** | `POST` | `/api/reports` | Submit community fraudulent job report | Optional / Public |
| **Scam Reports** | `GET` | `/api/reports` | List community reported scams with filters | Optional / Public |
| **Feedback** | `POST` | `/api/feedback` | Submit analysis accuracy feedback | Bearer JWT |

---

## 2. Detailed Endpoint Specifications

### A. System Health

#### `GET /api/health`
Checks backend readiness, local ML pipeline availability, Tesseract OCR binary status, and SMTP email service configuration.

* **Authentication**: None (Public)
* **Response `200 OK`**:
```json
{
  "status": "ok",
  "ml_available": true,
  "ocr_available": true,
  "online_lookup_enabled": false,
  "email": {
    "smtp_configured": true,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_from": "no-reply@jobshield.local"
  }
}
```

---

### B. Authentication APIs (`/api/auth`)

#### `POST /api/auth/register`
Creates an unverified user account, hashes password via Bcrypt, and sends a 6-digit OTP code to the provided email address.

* **Authentication**: None (Public)
* **Request Body**:
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "password": "SecurePassword123!"
}
```
* **Response `201 Created`**:
```json
{
  "requires_verification": true,
  "email": "jane.doe@example.com",
  "message": "Verification code sent. Check your email to complete registration."
}
```
* **Error Responses**:
  * `400 Bad Request`: Email already registered.
  * `422 Unprocessable Entity`: Password must be ≥ 8 chars with letters and numbers/special characters.

---

#### `POST /api/auth/verify-email`
Verifies the submitted 6-digit OTP, marks the user account as verified (`is_verified = True`), and issues a signed JWT Bearer token.

* **Authentication**: None (Public)
* **Request Body**:
```json
{
  "email": "jane.doe@example.com",
  "otp": "123456"
}
```
* **Response `200 OK`**:
```json
{
  "user": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "role": "user",
    "is_verified": true,
    "email_verified": true
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
* **Error Responses**:
  * `400 Bad Request`: Invalid or expired verification code.
  * `404 Not Found`: User not found.

---

#### `POST /api/auth/login`
Authenticates user credentials and returns a signed JWT Bearer token.

* **Authentication**: None (Public)
* **Request Body**:
```json
{
  "email": "jane.doe@example.com",
  "password": "SecurePassword123!"
}
```
* **Response `200 OK`**:
```json
{
  "user": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "role": "user",
    "is_verified": true,
    "email_verified": true
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
* **Error Responses**:
  * `401 Unauthorized`: Invalid email or password.
  * `403 Forbidden`: Account email is unverified.

---

#### `GET /api/auth/me`
Retrieves the profile of the currently authenticated session user.

* **Authentication**: `Bearer <token>` (JWT)
* **Response `200 OK`**:
```json
{
  "user": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "role": "user",
    "is_verified": true,
    "email_verified": true
  }
}
```
* **Error Responses**:
  * `401 Unauthorized`: Missing, expired, or invalid JWT Bearer token.

---

### C. Job Analysis APIs (`/api`)

#### `POST /api/analyze`
Executes comprehensive multi-engine job credibility analysis, evaluating company verification, URL security, deterministic red flags, and ML scam likelihood. Persists results and returns full dimensional breakdown.

* **Authentication**: `Bearer <token>` (JWT)
* **Request Body**:
```json
{
  "title": "Software Engineer",
  "company_name": "TechNova Solutions",
  "description": "We are hiring a Software Engineer. Responsibilities include building scalable APIs with Python. No upfront fees.",
  "salary": "8-12 LPA",
  "email": "careers@technovasolutions.com",
  "url": "https://www.technovasolutions.com/careers",
  "location": "Bengaluru",
  "job_type": "Full-time"
}
```
* **Response `200 OK`**:
```json
{
  "analysis_id": 101,
  "id": 101,
  "user_id": 1,
  "job_posting_id": 55,
  "trust_score": 86,
  "risk_level": "LOW",
  "ml": {
    "available": true,
    "scam_probability": 0.12,
    "top_terms": [
      { "term": "apis", "weight": -0.42 },
      { "term": "scalable", "weight": -0.35 }
    ]
  },
  "red_flags": [],
  "positive_indicators": [
    { "id": "detailed_responsibilities", "label": "Detailed responsibilities listed" },
    { "id": "official_email", "label": "Official-looking company-domain email" }
  ],
  "score_breakdown": {
    "dimensions": {
      "company_verification": { "score": 90.0, "weight": 0.25, "label": "Company Verification" },
      "source_credibility": { "score": 90.0, "weight": 0.20, "label": "Source & URL Credibility" },
      "job_posting_quality": { "score": 75.0, "weight": 0.15, "label": "Job Posting Quality" },
      "scam_detection": { "score": 96.4, "weight": 0.30, "label": "Scam & Red Flag Detection" },
      "contact_consistency": { "score": 95.0, "weight": 0.10, "label": "Contact & Domain Consistency" }
    },
    "raw_weighted_score": 89.2,
    "cap_applied": false,
    "trust_score": 86,
    "risk_level": "LOW"
  },
  "company_verification": {
    "status": "PARTIALLY VERIFIED",
    "confidence_level": "Partially Verified",
    "score": 65
  },
  "url_analysis": {
    "valid": true,
    "risk_level": "LOW",
    "risk_score": 0
  },
  "duplicate_result": {
    "is_duplicate": false,
    "matches": []
  },
  "explanation": "This posting received a high credibility trust score (86/100). No critical red flags were triggered.",
  "disclaimer": "AI JobShield provides risk analysis based on available signals, not legal certainty.",
  "created_at": "2026-10-02T14:30:00Z"
}
```
* **Error Responses**:
  * `422 Unprocessable Entity`: Job description too short (< 30 characters).

---

### D. OCR Processing APIs (`/api/ocr`)

#### `POST /api/ocr/analyze`
Accepts a screenshot or photo of a job posting, executes Tesseract OCR, validates the text against the relevance gatekeeper, and optionally triggers full analysis.

* **Authentication**: `Bearer <token>` (JWT)
* **Request Header**: `Content-Type: multipart/form-data`
* **Form Parameters**:
  * `file`: Binary image file (PNG, JPG, JPEG, WEBP ≤ 5 MB).
  * `auto_analyze`: Boolean string (`"true"` or `"false"`).
  * `title`: Optional override title.
  * `company_name`: Optional override company name.
* **Response `200 OK` (Relevance Gate Passed)**:
```json
{
  "ocr": {
    "available": true,
    "filename": "d41d8cd98f00b204e9800998ecf8427e.png",
    "extracted_text": "We are hiring Backend Developer at Acme Corp. CTC 8 LPA...",
    "confidence": 88.5,
    "hints": {
      "emails": ["jobs@acme.com"],
      "urls": ["https://acme.com/apply"],
      "company_name": "Acme Corp",
      "title": "Backend Developer"
    }
  },
  "validation": {
    "valid": true,
    "score": 15,
    "distinct_signals": 5,
    "anti_score": 0
  },
  "analysis": { ... }
}
```
* **Response `422 Unprocessable Entity` (Relevance Gate Rejected)**:
```json
{
  "error": {
    "code": "OCR_NOT_JOB_RELATED",
    "message": "This doesn't appear to be a job or recruitment-related document. Please upload a job posting, recruiter message, or resume.",
    "details": []
  }
}
```

---

### E. Analysis History APIs (`/api/history`)

#### `GET /api/history`
Returns a paginated list of past analyses performed by the authenticated user.

* **Authentication**: `Bearer <token>` (JWT)
* **Query Parameters**:
  * `limit`: Integer, default `10` (max 100).
  * `offset`: Integer, default `0`.
  * `search`: String, optional keyword search across title, company, description.
  * `risk_level`: String, optional filter (`"ALL"`, `"LOW"`, `"MEDIUM"`, `"HIGH"`).
* **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": 101,
      "job_posting_id": 55,
      "title": "Software Engineer",
      "company_name": "TechNova Solutions",
      "trust_score": 86,
      "risk_level": "LOW",
      "ml_scam_probability": 0.12,
      "created_at": "2026-10-02T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

#### `DELETE /api/history/{analysis_id}`
Permanently deletes an analysis record belonging to the authenticated user. Cascades removal to duplicate matches and feedback entries.

* **Authentication**: `Bearer <token>` (JWT)
* **Response `200 OK`**:
```json
{
  "message": "Analysis deleted successfully"
}
```
* **Error Responses**:
  * `404 Not Found`: Analysis record not found or belongs to another user.

---

### F. Dashboard APIs (`/api`)

#### `GET /api/dashboard`
Fetches aggregate analytical metrics, risk tier distributions, recent activity, and a 14-day scan history timeline.

* **Authentication**: `Bearer <token>` (JWT)
* **Response `200 OK`**:
```json
{
  "total_analyses": 14,
  "average_trust_score": 68.4,
  "risk_distribution": {
    "low": 9,
    "medium": 1,
    "high": 4
  },
  "recent_analyses": [ ... ],
  "timeline_14_days": [
    { "date": "2026-09-20", "count": 2, "avg_score": 75 },
    { "date": "2026-09-21", "count": 1, "avg_score": 82 }
  ],
  "is_admin_view": false
}
```

---

### G. Feedback & Scam Reports APIs

#### `POST /api/feedback`
Submits user feedback regarding the accuracy of an analysis result.

* **Authentication**: `Bearer <token>` (JWT)
* **Request Body**:
```json
{
  "analysis_id": 101,
  "label": "correct",
  "comment": "Analysis accurately flagged personal email."
}
```
* **Response `201 Created`**:
```json
{
  "id": 1,
  "analysis_result_id": 101,
  "label": "correct",
  "comment": "Analysis accurately flagged personal email."
}
```

---

#### `POST /api/reports`
Submits a public or authenticated report of fraudulent recruitment activity to the community warning pool.

* **Authentication**: Optional / Public
* **Request Body**:
```json
{
  "job_title": "Data Entry Specialist",
  "company_name": "Quick Cash Careers",
  "description": "Demanded registration fee via UPI.",
  "url": "http://quick-cash-jobs.xyz/apply",
  "reason": "Fee fraud"
}
```
* **Response `201 Created`**:
```json
{
  "id": 5,
  "status": "pending",
  "message": "Scam report recorded. Thank you for protecting the community."
}
```
