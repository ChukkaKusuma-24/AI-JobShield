# AI JobShield — Entity-Relationship (ER) Diagram

This document specifies the database schema, relational cardinalities, foreign key constraints, and indexing strategies implemented in **AI JobShield**.

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ EMAIL_OTPS : "has"
    USERS ||--o{ JOB_POSTINGS : "creates"
    USERS ||--o{ ANALYSIS_RESULTS : "owns"
    USERS ||--o{ OCR_RESULTS : "uploads"
    USERS ||--o{ SCAM_REPORTS : "submits"
    USERS ||--o{ FEEDBACK : "provides"

    JOB_POSTINGS ||--|| ANALYSIS_RESULTS : "analyzed_in"
    ANALYSIS_RESULTS ||--o| OCR_RESULTS : "derived_from"
    ANALYSIS_RESULTS ||--o{ DUPLICATE_MATCHES : "triggers"
    ANALYSIS_RESULTS ||--o{ FEEDBACK : "receives"

    USERS {
        int id PK "Auto-increment"
        string name "User full name"
        string email UK "Unique, Indexed"
        string password_hash "Bcrypt salted hash"
        string role "user | admin"
        boolean is_verified "Email OTP verified"
        datetime created_at "Indexed"
        datetime updated_at "Auto-updated"
    }

    EMAIL_OTPS {
        int id PK "Auto-increment"
        int user_id FK "Cascade delete"
        string otp_hash "SHA256 salted hash"
        string purpose "verification | reset"
        datetime expires_at "Expiration timestamp"
        int attempts "Brute-force counter"
        datetime created_at ""
    }

    JOB_POSTINGS {
        int id PK "Auto-increment"
        int user_id FK "Owner User ID, Indexed"
        string title "Job Title"
        string company_name "Target Company"
        text description "Full description text"
        string salary "Salary range / terms"
        string email "Recruiter contact email"
        string url "Job posting / website URL"
        string location "Geographic location"
        string job_type "Full-time / Part-time / etc"
        string source "manual | ocr | import"
        datetime created_at "Indexed"
    }

    ANALYSIS_RESULTS {
        int id PK "Auto-increment"
        int job_posting_id FK "1:1 with JobPosting"
        int user_id FK "Owner User ID, Indexed"
        int trust_score "Computed score (0 - 100)"
        string risk_level "LOW | MEDIUM | HIGH"
        float ml_scam_probability "0.0 - 1.0"
        float rule_risk_points "Cumulative red flag penalty"
        text red_flags "JSON array of detected flags"
        text positive_indicators "JSON array of positives"
        text explanation "Structured Markdown rationale"
        text company_verification "JSON verification object"
        text url_analysis "JSON heuristic findings"
        text duplicate_result "JSON near-duplicate matches"
        text score_breakdown "JSON 5-dimension breakdown"
        text extracted_ocr_text "Raw OCR text if scanned"
        datetime created_at "Indexed"
    }

    OCR_RESULTS {
        int id PK "Auto-increment"
        int user_id FK "Owner User ID"
        string image_filename "Stored file path"
        text extracted_text "Raw Tesseract output"
        boolean ocr_available "Engine status"
        float confidence "OCR confidence score"
        int analysis_result_id FK "Nullable FK"
        datetime created_at ""
    }

    COMPANIES {
        int id PK "Auto-increment"
        string name "Company Name, Indexed"
        string domain "Corporate Domain"
        string verification_status "VERIFIED | PARTIALLY VERIFIED | UNVERIFIED"
        datetime last_checked_at ""
        text notes "Audit summary"
    }

    DUPLICATE_MATCHES {
        int id PK "Auto-increment"
        int analysis_result_id FK "Cascade delete"
        string matched_source_type "history | report"
        int matched_id "Foreign record ID"
        float similarity "0.0 - 1.0"
        datetime created_at ""
    }

    FEEDBACK {
        int id PK "Auto-increment"
        int analysis_result_id FK "Cascade delete"
        int user_id FK "Reviewing User ID"
        string label "correct | incorrect | unsure"
        text comment "User feedback remarks"
        datetime created_at ""
    }

    SCAM_REPORTS {
        int id PK "Auto-increment"
        int user_id FK "Reporting User ID"
        string company_name "Reported Company"
        string job_title "Reported Title"
        string platform "Where spotted"
        text description "Report narrative"
        string evidence_url "Proof URL"
        string status "pending | reviewed | dismissed"
        datetime created_at ""
    }
```

---

## 2. Relational Integrity & Performance Optimizations

1. **Foreign Key Constraints**:
   * All child tables (`job_postings`, `analysis_results`, `email_otps`, `ocr_results`, `scam_reports`, `feedbacks`) enforce foreign key relationships referencing `users(id)`.
   * When an `AnalysisResult` is deleted, related records in `duplicate_matches` and `feedback` are automatically removed via `cascade="all, delete-orphan"`.
2. **Database Indexing**:
   * `users.email`: Unique index enabling sub-millisecond authentication lookups.
   * `analysis_results.user_id`: Index enabling fast user-scoped query filtering (`WHERE user_id = :id`).
   * `analysis_results.created_at`: Index enabling efficient descending sorting for paginated history retrieval.
   * `job_postings.user_id` & `job_postings.created_at`: Indexes enabling rapid analytical joins.
