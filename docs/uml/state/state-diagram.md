# AI JobShield — State Machine Diagrams

This document models the dynamic state transitions, triggers, guard conditions, and lifecycles for entities with state-dependent behavior in **AI JobShield**.

---

## 1. Job Opportunity Analysis & Risk Lifecycle

This state machine models how an ingested job posting traverses through preprocessing, gate validation, concurrent evaluation, risk categorization, and archival.

```mermaid
stateDiagram-v2
    [*] --> Ingested: User submits job text or screenshot

    state Ingested {
        [*] --> ParameterExtraction: Form text received
        [*] --> ImagePreprocessing: Screenshot image received
        ImagePreprocessing --> OCRTextExtracted: Tesseract optical scan complete
        OCRTextExtracted --> RelevanceValidation: Run job_content_validator.py
    }

    RelevanceValidation --> RejectedNonJob: Validation failed (score < 8 or anti-score ≥ 6)
    RejectedNonJob --> [*]: 422 Unprocessable Entity (Rejection alert)

    RelevanceValidation --> AnalysisPipeline: Validated job / recruiter content
    ParameterExtraction --> AnalysisPipeline: Validated form parameters

    state AnalysisPipeline {
        [*] --> CompanyLookup: Cross-check registry
        [*] --> URLSecurityCheck: Inspect link heuristics
        [*] --> RuleEvaluation: Scan for 14 scam patterns
        [*] --> MLInference: Calculate TF-IDF scam probability

        CompanyLookup --> DimensionCalculation
        URLSecurityCheck --> DimensionCalculation
        RuleEvaluation --> DimensionCalculation
        MLInference --> DimensionCalculation

        DimensionCalculation --> SafetyCapEvaluation: Aggregate 5 weighted dimensions
    }

    AnalysisPipeline --> RiskClassification: Enforce evidence-based caps

    state RiskClassification {
        [*] --> EvaluateScore
        EvaluateScore --> LowRisk: Trust Score ≥ 75
        EvaluateScore --> MediumRisk: 45 ≤ Trust Score < 75
        EvaluateScore --> HighRisk: Trust Score < 45
    }

    LowRisk --> Persisted: Generate clean rationale
    MediumRisk --> Persisted: Generate cautionary warnings
    HighRisk --> Persisted: Generate critical scam alerts

    state Persisted {
        [*] --> SavedInDatabase: Commit JobPosting & AnalysisResult
        SavedInDatabase --> UserWorkspace: Available in History & Dashboard
    }

    UserWorkspace --> Deleted: User initiates deletion
    Deleted --> [*]: Cascade purge from database
```

---

## 2. User Account & Authentication Lifecycle

```mermaid
stateDiagram-v2
    [*] --> UnverifiedRegistration: User submits signup form

    UnverifiedRegistration --> PendingEmailVerification: 6-digit OTP generated & mailed via SMTP

    state PendingEmailVerification {
        [*] --> AwaitingInput: 15-minute countdown active
        AwaitingInput --> InvalidCodeEntered: User submits incorrect OTP
        InvalidCodeEntered --> AwaitingInput: attempts < 5
        InvalidCodeEntered --> LockedOut: attempts ≥ 5 (Brute-force lockout)
        AwaitingInput --> ResendRequested: User clicks "Resend OTP"
        ResendRequested --> AwaitingInput: New OTP dispatched & timer reset
    }

    AwaitingInput --> VerifiedActive: Correct OTP submitted
    LockedOut --> UnverifiedRegistration: Cooldown period elapses / Admin reset

    state VerifiedActive {
        [*] --> Unauthenticated: Logged out
        Unauthenticated --> AuthenticatedSession: Successful login with valid password
        AuthenticatedSession --> TokenExpired: JWT TTL expires (24 hours)
        TokenExpired --> Unauthenticated: Requires re-login
        AuthenticatedSession --> Unauthenticated: User clicks "Sign Out"
    }

    Unauthenticated --> PasswordResetPending: User requests forgot-password OTP
    PasswordResetPending --> VerifiedActive: Valid reset OTP & new password supplied
```

---

## 3. Company Verification State Machine

```mermaid
stateDiagram-v2
    [*] --> Unchecked: Company name supplied in posting

    Unchecked --> RegistryLookup: Query verified_companies.json & DB

    state RegistryLookup <<choice>>
    RegistryLookup --> KnownEnterprise: Exact match on name or verified aliases
    RegistryLookup --> UnknownCompany: No matching independent record

    state KnownEnterprise {
        [*] --> CheckContactDomain
        CheckContactDomain --> OfficialDomainMatch: Recruiter email matches official corporate domain
        CheckContactDomain --> PersonalEmailDetected: Recruiter uses free webmail (@gmail, @yahoo)
        CheckContactDomain --> DomainMismatchDetected: Recruiter domain differs from corporate domain
        CheckContactDomain --> IncompleteEvidence: No email or URL supplied in posting
    }

    state UnknownCompany {
        [*] --> CheckEmailDomain
        CheckEmailDomain --> CustomDomainProvided: Unknown company with custom @domain.com
        CheckEmailDomain --> FreeEmailProvided: Unknown company with @gmail.com
        CheckEmailDomain --> NoContactProvided: No contact information
    }

    %% Terminal States
    OfficialDomainMatch --> VERIFIED: High Confidence (Company Score: 95)
    IncompleteEvidence --> PARTIALLY_VERIFIED: Recognizable brand without verified channels (Score: 65)
    CustomDomainProvided --> UNVERIFIED: No independent registry record (Score: 45)
    NoContactProvided --> UNVERIFIED: Incomplete verifiable evidence (Score: 40)
    FreeEmailProvided --> UNVERIFIED: Personal email for unverified business (Score: 30)
    PersonalEmailDetected --> IMPERSONATION_RISK: Critical brand impersonation alert (Score: 15)
    DomainMismatchDetected --> IMPERSONATION_RISK: Domain spoofing alert (Score: 15)

    VERIFIED --> [*]
    PARTIALLY_VERIFIED --> [*]
    UNVERIFIED --> [*]
    IMPERSONATION_RISK --> [*]
```

---

## 4. Community Scam Report Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Submitted: Candidate encounters fraudulent posting & submits report

    Submitted --> PendingReview: Stored with status="pending"

    state PendingReview {
        [*] --> InQueue: Visible in security admin queue
        InQueue --> UnderInvestigation: Administrator reviews attached screenshots & URL
    }

    UnderInvestigation --> Reviewed: Administrator confirms fraudulent indicators
    UnderInvestigation --> Dismissed: Administrator determines submission is invalid / spam

    Reviewed --> Resolved: Added to known scam repository / duplicate detection corpus
    Dismissed --> [*]: Report archived as dismissed
    Resolved --> [*]: Permanent entry in scam intelligence corpus
```
