# AI JobShield — Sequence Diagrams

This document details the time-ordered interactions across the Client Layer, API Gateway, Analytical Services, Database, and External Subsystems for all major workflows in **AI JobShield**.

---

## 1. Sequence Diagram: User Registration & Email OTP Verification

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker (Browser)
    participant UI as React Frontend (AuthPage)
    participant Gateway as FastAPI (/api/auth)
    participant Sec as Security / Bcrypt
    participant Mail as Email Service
    participant SMTP as External SMTP Server
    participant DB as Relational Database

    %% Step 1: Registration Request
    User->>UI: Enters name, email, password & clicks "Register"
    UI->>Gateway: POST /api/auth/register {name, email, password}
    Gateway->>Gateway: Validate email format & password strength (≥ 8 chars)
    Gateway->>DB: Check if email already registered
    DB-->>Gateway: Email available

    Gateway->>Sec: hash_password(password)
    Sec-->>Gateway: Bcrypt salted password hash
    Gateway->>DB: INSERT into users (name, email, password_hash, is_verified=False)
    DB-->>Gateway: Created user entity (user_id)

    %% Step 2: OTP Generation
    Gateway->>Mail: generate_otp() -> "654321"
    Mail->>Sec: hash_otp("654321") -> SHA-256 hash
    Sec-->>Mail: otp_hash
    Mail->>DB: INSERT into email_otps (user_id, otp_hash, purpose="verification", expires_at=now+15m)
    DB-->>Mail: OTP record saved

    %% Step 3: SMTP Delivery
    Mail->>SMTP: send_mail(to=email, subject="Verify Account", body="OTP: 654321")
    SMTP-->>Mail: 250 Message accepted for delivery
    Gateway-->>UI: 201 Created {requires_verification: true, email}
    UI-->>User: Renders OTP Input Modal

    %% Step 4: Verification Submission
    User->>UI: Enters 6-digit OTP code & clicks "Verify"
    UI->>Gateway: POST /api/auth/verify-email {email, otp="654321"}
    Gateway->>DB: Fetch user & active OTP record for user_id
    DB-->>Gateway: User entity & EmailOtp record

    Gateway->>Sec: verify_otp_hash("654321", stored_hash)
    Sec-->>Gateway: Valid OTP match
    Gateway->>DB: UPDATE users SET is_verified = True
    Gateway->>DB: DELETE FROM email_otps WHERE id = otp_id
    Gateway->>Sec: create_access_token(user_id, email, role)
    Sec-->>Gateway: Signed JWT Bearer token

    Gateway-->>UI: 200 OK {token, user: {id, name, email, role, is_verified: true}}
    UI->>UI: Save JWT to localStorage & update AuthContext
    UI-->>User: Redirect to User Dashboard
```

---

## 2. Sequence Diagram: User Login & JWT Authentication

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker (Browser)
    participant UI as React Frontend (AuthPage)
    participant Gateway as FastAPI (/api/auth/login)
    participant Sec as Security / Bcrypt
    participant DB as Relational Database

    User->>UI: Enters registered email & password
    UI->>Gateway: POST /api/auth/login {email, password}
    Gateway->>DB: SELECT * FROM users WHERE email = :email
    DB-->>Gateway: User record found

    Gateway->>Sec: verify_password(plain_password, user.password_hash)
    Sec-->>Gateway: Password Match Confirmed

    alt User is NOT verified (is_verified == False)
        Gateway-->>UI: 403 Forbidden {code: "EMAIL_NOT_VERIFIED", message: "Please verify email"}
        UI-->>User: Prompts user to complete OTP verification
    else User is verified
        Gateway->>Sec: create_access_token(sub=user.id, email=user.email, role=user.role)
        Sec-->>Gateway: Signed HMAC-SHA256 JWT Token
        Gateway-->>UI: 200 OK {token: "ey...", user: {id, name, email, role}}
        UI->>UI: Set active user session in AuthContext
        UI-->>User: Navigate to Dashboard with Welcome Toast
    end
```

---

## 3. Sequence Diagram: Manual Job Posting Analysis & 5D Scoring

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker
    participant UI as React Frontend (AnalyzePage)
    participant Gateway as FastAPI Router (/api/analyze)
    participant Auth as JWT Auth Dependency
    participant Orchestrator as Analyzer Service
    participant CV as Company Verifier Service
    participant URL as URL Analyzer Service
    participant Rules as Rule Engine
    participant ML as ML Service
    participant Score as 5D Scoring Engine
    participant Explain as Explainability Builder
    participant Dup as Duplicate Detection
    participant DB as Relational Database

    User->>UI: Fills Job Posting Form & clicks "Analyze Opportunity"
    UI->>Gateway: POST /api/analyze (Bearer JWT + Job Payload)
    Gateway->>Auth: get_current_user(token)
    Auth-->>Gateway: Validated User (user_id)

    Gateway->>Orchestrator: run_analysis(db, user_id, title, company_name, description, salary, email, url...)

    %% Component 1: URL & Company
    opt URL provided
        Orchestrator->>URL: analyze_url(url, company_name)
        URL-->>Orchestrator: URL risk level, score, indicators
    end

    Orchestrator->>CV: verify_company(db, company_name, email, url)
    CV-->>Orchestrator: Company Status (VERIFIED / PARTIAL / UNVERIFIED / IMPERSONATION_RISK)

    %% Component 2: ML & Rules
    Orchestrator->>ML: predict(job_text)
    ML-->>Orchestrator: Scam Probability, Top Influential Terms

    Orchestrator->>Rules: analyze_rules(title, company, description, salary, email, url, company_status)
    Rules-->>Orchestrator: Red Flags list, Positive Indicators list, Bonus points

    %% Component 3: 5D Scoring & Hard Caps
    Orchestrator->>Score: compute_trust_score(red_flags, bonus, ml_prob, company_res, url_res...)
    Note over Score: 1. Dim 1: Company Verification (25%)<br/>2. Dim 2: Source Credibility (20%)<br/>3. Dim 3: Job Quality (15%)<br/>4. Dim 4: Scam Detection (30%)<br/>5. Dim 5: Contact Consistency (10%)<br/>6. Apply Hard Caps (Impersonation<=25, Scam<=35, Unverified<=65)
    Score-->>Orchestrator: Trust Score (0-100), Risk Level (LOW/MED/HIGH), Score Breakdown

    %% Component 4: Explainability & Deduplication
    Orchestrator->>Explain: build_explanation(trust_score, risk_level, red_flags, positives, company_res, score_breakdown...)
    Explain-->>Orchestrator: Structured Markdown Rationale

    Orchestrator->>DB: INSERT into job_postings (user_id, title, company_name, description, salary, url, source="manual")
    DB-->>Orchestrator: Created posting (job_posting_id)

    Orchestrator->>Dup: find_duplicates(db, text, exclude_id=posting.id)
    Dup-->>Orchestrator: Duplicate matches list

    Orchestrator->>DB: INSERT into analysis_results (job_posting_id, user_id, trust_score, risk_level, red_flags, explanation, score_breakdown...)
    DB-->>Orchestrator: Created analysis (analysis_id)

    opt Near duplicates found
        Orchestrator->>DB: INSERT into duplicate_matches (analysis_result_id, matched_id, similarity)
    end

    Orchestrator->>DB: COMMIT transaction
    Orchestrator-->>Gateway: Serialized Analysis Payload
    Gateway-->>UI: 200 OK (Full Analysis JSON)
    UI-->>User: Renders Trust Gauge, 5-Dimension Bars, Red Flags & Recommendations
```

---

## 4. Sequence Diagram: OCR Screenshot Scanning & Relevance Gatekeeper

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker
    participant UI as React Frontend (OcrPage)
    participant Gateway as FastAPI Router (/api/ocr/analyze)
    participant OCR as OCR Service (Tesseract)
    participant Gate as Job Content Validator
    participant Orchestrator as Analyzer Service
    participant DB as Relational Database

    User->>UI: Drops screenshot of recruiter chat / job poster
    UI->>Gateway: POST /api/ocr/analyze (Multipart FormData [file] + Bearer JWT)

    Gateway->>OCR: save_and_ocr(file_bytes, filename, content_type)
    OCR->>OCR: Validate file format (.png, .jpg, .jpeg, .webp) & size (≤ 5MB)
    OCR->>OCR: Preprocess image (Grayscale, Resize, Point contrast threshold)
    OCR->>OCR: Execute Tesseract binary (image_to_string, image_to_data)
    OCR-->>Gateway: Extracted text, confidence score, extracted hints (email, url, title)

    Gateway->>Gate: validate_job_related_text(extracted_text)
    Note over Gate: Evaluate pattern weights:<br/>Strong (weight 3), Medium (weight 2), Weak (weight 1)<br/>Subtract Anti-patterns (Coding contests, Shopping carts)

    alt Extracted text is NOT job-related (Score < 8 or Anti-score ≥ 6)
        Gate-->>Gateway: Validation Failure: {valid: false, message: "Not job-related"}
        Gateway-->>UI: 422 Unprocessable Entity {error: "This image does not appear to contain job, recruitment, or resume content"}
        UI-->>User: Displays friendly rejection alert explaining upload requirements
    else Extracted text IS verified job/recruitment content
        Gate-->>Gateway: Validation Success: {valid: true, score, distinct_signals}
        Gateway->>Orchestrator: run_analysis(db, user_id, extracted_text, source="ocr")
        Orchestrator-->>Gateway: Completed Analysis Result
        Gateway->>DB: INSERT into ocr_results (user_id, image_filename, extracted_text, confidence, analysis_result_id)
        Gateway->>DB: COMMIT transaction
        DB-->>Gateway: Persisted OCR Record
        Gateway-->>UI: 200 OK {analysis, ocr: {text, confidence, hints}}
        UI-->>User: Renders Analysis Result with Expandable OCR Text Viewer
    end
```

---

## 5. Sequence Diagram: Browse Scan History & User Isolation

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker (user_id = 42)
    participant UI as React Frontend (HistoryPage)
    participant Gateway as FastAPI Router (/api/history)
    participant Auth as JWT Auth Dependency
    participant DB as Relational Database

    User->>UI: Navigates to History tab
    UI->>Gateway: GET /api/history?limit=10&offset=0&risk_level=ALL (Bearer JWT)
    Gateway->>Auth: Verify JWT
    Auth-->>Gateway: Current User (user_id = 42, role = "user")

    %% User Isolation Query
    Gateway->>DB: SELECT * FROM analysis_results WHERE user_id = 42 ORDER BY created_at DESC LIMIT 10 OFFSET 0
    DB-->>Gateway: List of user 42's analysis records only
    Gateway->>DB: SELECT COUNT(*) FROM analysis_results WHERE user_id = 42
    DB-->>Gateway: Total count (e.g. 15)

    Gateway-->>UI: 200 OK {items: [...], total: 15, limit: 10, offset: 0}
    UI-->>User: Displays paginated history table with risk badges and trust scores

    %% Attempting to view a specific item
    User->>UI: Clicks on Analysis #105
    UI->>Gateway: GET /api/history/105 (Bearer JWT)
    Gateway->>DB: SELECT * FROM analysis_results WHERE id = 105
    DB-->>Gateway: Record found (owner user_id = 42)

    alt Record belongs to user (or user is admin)
        Gateway-->>UI: 200 OK (Full Analysis Details)
        UI-->>User: Displays complete evaluation view
    else Record belongs to another user (user_id = 99)
        Gateway-->>UI: 404 Not Found {code: "NOT_FOUND", message: "Analysis not found"}
        UI-->>User: Shows error notification (Guarantees privacy)
    end
```

---

## 6. Sequence Diagram: Delete Analysis Record & Cascade Deletion

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker (user_id = 42)
    participant UI as React Frontend (HistoryPage)
    participant Gateway as FastAPI Router (/api/history/{id})
    participant Auth as JWT Auth Dependency
    participant DB as Relational Database

    User->>UI: Clicks "Delete" icon on Analysis #105
    UI-->>User: Prompts confirmation modal ("Are you sure?")
    User->>UI: Confirms deletion
    UI->>Gateway: DELETE /api/history/105 (Bearer JWT)
    Gateway->>Auth: Verify JWT
    Auth-->>Gateway: Current User (user_id = 42)

    Gateway->>DB: SELECT * FROM analysis_results WHERE id = 105
    DB-->>Gateway: Analysis entity found (user_id = 42, job_posting_id = 78)

    Gateway->>DB: DELETE FROM analysis_results WHERE id = 105
    Note over DB: SQLAlchemy cascade automatically deletes:<br/>- Linked duplicate_matches<br/>- Linked feedback records
    Gateway->>DB: DELETE FROM job_postings WHERE id = 78
    Gateway->>DB: COMMIT transaction
    DB-->>Gateway: Deletion confirmed

    Gateway-->>UI: 200 OK {message: "Analysis deleted successfully"}
    UI->>UI: Remove row from local state / refetch history
    UI-->>User: Displays success toast and updates table
```
