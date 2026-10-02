# AI JobShield — Sequence Diagrams

This document details the time-ordered interactions across the Client, Backend Gateway, Analytical Engines, and Database during core system workflows.

---

## 1. Sequence Diagram: Job Analysis & Evidence-Based Scoring

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Browser)
    participant UI as React SPA (AnalyzePage)
    participant API as FastAPI Gateway (/api/analyze)
    participant Auth as Auth & Token Verifier
    participant CV as Company Verifier
    participant RE as Rule Engine
    participant ML as ML Service (TF-IDF + SGD)
    participant Score as 5D Scoring Engine
    participant Explain as Explainability Builder
    participant DB as Relational Database (MySQL)

    User->>UI: Fills job form & clicks "Analyze"
    UI->>API: POST /api/analyze (Bearer JWT + Job Payload)
    API->>Auth: Verify JWT & extract user_id
    Auth-->>API: Validated CurrentUser (user_id)

    API->>CV: verify_company(company_name, email, url)
    CV-->>API: Company Status, Domain Consistency, Reasons

    API->>ML: predict(job_text)
    ML-->>API: Scam Probability, Top Influential Terms

    API->>RE: analyze_rules(job_text, company_status)
    RE-->>API: Red Flags, Positives, Bonus (Zeroed if critical flag)

    API->>Score: compute_trust_score(Company, Source, Quality, Scam, Contact)
    Note over Score: Apply Evidence-Based Caps:<br/>Critical Scam <= 35<br/>Impersonation <= 25<br/>Unverified <= 65
    Score-->>API: Trust Score, Risk Level, Dimension Breakdown

    API->>Explain: build_explanation(Score, Dimensions, Reasons, Evidence)
    Explain-->>API: Structured Natural Language Rationale

    API->>DB: INSERT into job_postings (title, company, description, user_id...)
    API->>DB: INSERT into analysis_results (trust_score, risk_level, breakdown...)
    API->>DB: COMMIT transaction
    DB-->>API: Success (analysis_id)

    API-->>UI: 200 OK (Full Analysis & Dimensions JSON)
    UI-->>User: Renders Trust Gauge, 5D Breakdown, and Red Flag Evidence
```

---

## 2. Sequence Diagram: OCR Screenshot Scanning Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Browser)
    participant UI as React SPA (OcrPage)
    participant API as FastAPI Gateway (/api/ocr/analyze)
    participant Gate as Job Content Gatekeeper
    participant OCR as Tesseract OCR Engine
    participant Analyzer as Analyzer Orchestrator
    participant DB as Relational Database (MySQL)

    User->>UI: Uploads job screenshot / chat image
    UI->>API: POST /api/ocr/analyze (Multipart FormData + JWT)
    API->>OCR: save_and_ocr(image_bytes)
    OCR-->>API: Extracted Text, Confidence Score, Metadata Hints

    API->>Gate: validate_job_related_text(text)
    alt Text is NOT job-related (Receipt, Meme, Code snippet)
        Gate-->>API: Rejected (Score < 20, Signals vs Anti-signals)
        API-->>UI: 422 Unprocessable Entity (User-friendly Gate Message)
        UI-->>User: Displays rejection banner explaining upload must be job-related
    else Text is verified job posting / recruiter message
        Gate-->>API: Validated (Job Signals Confirmed)
        API->>Analyzer: run_analysis(user_id, text, extracted_ocr_text=text)
        Analyzer-->>API: Completed Analysis Result
        API->>DB: INSERT into ocr_results (user_id, image_filename, text...)
        API->>DB: COMMIT transaction
        DB-->>API: Persisted (ocr_id, analysis_id)
        API-->>UI: 200 OK (Analysis JSON + Extracted OCR Text)
        UI-->>User: Renders full analysis with expandable OCR text view
    end
```
