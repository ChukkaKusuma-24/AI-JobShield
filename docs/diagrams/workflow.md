# AI JobShield — End-to-End Application Workflow

This document traces the complete user journey through **AI JobShield**, from onboarding to analysis, review, and historical tracking.

---

## Complete User Journey Flowchart

```mermaid
flowchart TD
    Start([User Visits AI JobShield]) --> CheckAuth{Is User Authenticated?}

    %% Public Path
    CheckAuth -- No --> Landing[Landing Page & Platform Overview]
    Landing --> AuthChoice{Action?}
    AuthChoice -- Register --> RegisterForm[Register with Name, Email & Password]
    RegisterForm --> SendOTP[System sends 6-digit OTP to Email]
    SendOTP --> VerifyOTPForm[Enter OTP Code]
    VerifyOTPForm -- Success --> IssueJWT[Issue Secure JWT Bearer Token]
    VerifyOTPForm -- Fail --> ResendOTP[Request New OTP]
    ResendOTP --> VerifyOTPForm

    AuthChoice -- Sign In --> LoginForm[Enter Email & Password]
    LoginForm --> IssueJWT

    %% Authenticated Path
    CheckAuth -- Yes --> IssueJWT
    IssueJWT --> Dashboard[User Security Dashboard]

    Dashboard --> ActionChoice{Select Navigation Action}

    %% Option 1: Manual Analysis
    ActionChoice -- Analyze Job --> InputJobForm[Enter Title, Company, Description, Salary, Contact, URL]
    InputJobForm --> ExecutePipeline[Backend Analysis Pipeline]

    %% Option 2: OCR Scanning
    ActionChoice -- Scan Screenshot --> UploadScreenshot[Upload Screenshot / Recruiter Chat Image]
    UploadScreenshot --> TesseractOCR[Extract Text via Tesseract OCR]
    TesseractOCR --> ContentGateCheck{Is Content Job-Related?}
    ContentGateCheck -- No --> GateReject[Display Friendly Rejection Message]
    GateReject --> UploadScreenshot
    ContentGateCheck -- Yes --> ExecutePipeline

    %% Pipeline Execution
    subgraph Pipeline ["AI JobShield Analytical Engine"]
        ExecutePipeline --> VerifyEmployer[1. Verify Company against Enterprise Registry]
        VerifyEmployer --> DetectImpersonation[Check for Email / Domain Mismatches]
        DetectImpersonation --> DetectRedFlags[2. Run Rule Engine for Upfront Fees, Urgency, WhatsApp]
        DetectRedFlags --> MLClassify[3. Run TF-IDF + SGD Classifier for Scam Probability]
        MLClassify --> Compute5D[4. Calculate 5-Dimension Weighted Credibility Rating]
        Compute5D --> ApplyCaps[5. Enforce Evidence-Based Security Caps]
        ApplyCaps --> GenerateExplanation[6. Generate Explainable Natural Language Report]
    end

    Pipeline --> CommitDB[(Persist JobPosting & AnalysisResult in Database)]
    CommitDB --> DisplayResult[Display ResultPage with Trust Gauge & 5D Breakdown]

    DisplayResult --> PostResultAction{Post-Analysis Actions}
    PostResultAction -- Review History --> HistoryPage[Analysis History with Filters & Pagination]
    PostResultAction -- Submit Report --> ReportScam[Submit Official Scam Community Report]
    PostResultAction -- Feedback --> SubmitFeedback[Submit Prediction Accuracy Feedback]
    PostResultAction -- Analyze Another --> InputJobForm

    %% History & Workspace Actions
    ActionChoice -- View History --> HistoryPage
    HistoryPage --> OpenPastAnalysis[Inspect Previous Analysis Result]
    HistoryPage --> DeleteRecord[Permanently Delete Record]

    ActionChoice -- User Profile --> ProfilePage[View Profile, Member Date, Aggregate Scan Stats]
    ActionChoice -- Sign Out --> Logout[Clear Session Token & Return to Landing Page]
    Logout --> Landing
```
