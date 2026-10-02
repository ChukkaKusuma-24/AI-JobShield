# AI JobShield — Activity Diagram

This document illustrates the operational activity flow of the job opportunity evaluation process, showing decisions, branching, and state transitions.

---

## Activity Flow Diagram

```mermaid
stateDiagram-v2
    [*] --> IngestionChoice: User initiates analysis

    state IngestionChoice <<choice>>
    IngestionChoice --> ManualInput: Manual Job Parameters
    IngestionChoice --> UploadImage: Screenshot Upload

    state UploadImage {
        [*] --> RunOCR: Preprocess & Call Tesseract
        RunOCR --> ContentGate: Evaluate Extracted Text
        state GateCheck <<choice>>
        ContentGate --> GateCheck: Score against Job Vocabulary
        GateCheck --> RejectUpload: Score < 20 / Anti-signals dominant
        GateCheck --> AcceptUpload: Relevant Job Content Validated
    }

    RejectUpload --> [*]: Display rejection feedback

    ManualInput --> ExtractFeatures
    AcceptUpload --> ExtractFeatures: Populate text & metadata hints

    state ExtractFeatures {
        [*] --> VerifyCompany: Check Curated Registry & DB
        VerifyCompany --> CheckDomainConsistency: Compare recruiter email domain with corporate registry
        CheckDomainConsistency --> RunRuleEngine: Execute 14 Red Flag & Positive Rules
        RunRuleEngine --> RunMLClassifier: Extract TF-IDF features & infer probability
    }

    ExtractFeatures --> Calculate5Dimensions

    state Calculate5Dimensions {
        [*] --> Dim1: Company Verification (25%)
        [*] --> Dim2: Source & URL Credibility (20%)
        [*] --> Dim3: Job Posting Quality (15%)
        [*] --> Dim4: Scam & Red Flag Detection (30%)
        [*] --> Dim5: Contact Domain Consistency (10%)
    }

    Calculate5Dimensions --> EvaluateHardCaps

    state EvaluateHardCaps <<choice>>
    EvaluateHardCaps --> ImpersonationCap: Known enterprise with free email?
    EvaluateHardCaps --> ScamCap: Fee, money request, or sensitive ID request?
    EvaluateHardCaps --> UnverifiedCap: Unknown company with no verification record?
    EvaluateHardCaps --> NormalWeighted: Clean verified signals

    ImpersonationCap --> AssignFinalScore: Cap Trust Score <= 25 (High Risk)
    ScamCap --> AssignFinalScore: Cap Trust Score <= 35 (High Risk)
    UnverifiedCap --> AssignFinalScore: Cap Trust Score <= 65 (Medium Risk)
    NormalWeighted --> AssignFinalScore: Uncapped Trust Score (0-100)

    AssignFinalScore --> GenerateRationale: Synthesize structured Markdown explanation
    GenerateRationale --> DatabaseTransaction: Persist JobPosting & AnalysisResult
    DatabaseTransaction --> RenderResult: Render interactive TrustGauge & Dimension breakdown
    RenderResult --> [*]: Saved to permanent user history
```
