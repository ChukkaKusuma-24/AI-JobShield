# AI JobShield — Use Case Diagram

This document defines the primary actors, functional use cases, and access boundaries within **AI JobShield**.

---

## 1. Use Case Diagram

```mermaid
graph LR
    %% Actors
    User((Authenticated Job Seeker / User))
    Guest((Unauthenticated Visitor))
    Admin((System Administrator))

    %% Boundary
    subgraph AI_JobShield_Platform ["AI JobShield Platform Boundary"]
        %% Public Use Cases
        UC_Register["Register Account"]
        UC_VerifyEmail["Verify Email (OTP)"]
        UC_Login["Sign In / Authenticate"]
        UC_ForgotPassword["Reset Password via OTP"]
        UC_ViewLanding["Explore Platform & About"]

        %% Core Analysis Use Cases
        UC_ManualAnalyze["Analyze Job Opportunity"]
        UC_UploadOCR["Scan Job Screenshot / OCR"]
        UC_ViewResult["Inspect Trust Score & Dimensions"]
        UC_ExamineRedFlags["Review Detected Scam Evidence"]
        UC_VerifyCompany["Run Standalone Company Verification"]
        UC_VerifyURL["Run Standalone URL Heuristics"]

        %% User Workspace Use Cases
        UC_ViewDashboard["View Real-Time Security Dashboard"]
        UC_ViewHistory["Browse Personal Analysis History"]
        UC_DeleteHistory["Delete Analysis Record"]
        UC_SubmitReport["Submit Scam Report"]
        UC_SubmitFeedback["Provide Analysis Accuracy Feedback"]
        UC_ViewProfile["View User Profile & Stats"]
        UC_Logout["Sign Out / Invalidate Token"]

        %% Admin Use Cases
        UC_ManageReports["Review Community Scam Reports"]
        UC_ManageCompanies["Update Curated Enterprise Registry"]
    end

    %% Guest Associations
    Guest --> UC_ViewLanding
    Guest --> UC_Register
    Guest --> UC_VerifyEmail
    Guest --> UC_Login
    Guest --> UC_ForgotPassword

    %% User Associations
    User --> UC_ViewDashboard
    User --> UC_ManualAnalyze
    User --> UC_UploadOCR
    User --> UC_ViewResult
    User --> UC_ExamineRedFlags
    User --> UC_VerifyCompany
    User --> UC_VerifyURL
    User --> UC_ViewHistory
    User --> UC_DeleteHistory
    User --> UC_SubmitReport
    User --> UC_SubmitFeedback
    User --> UC_ViewProfile
    User --> UC_Logout

    %% Admin Associations
    Admin --> UC_ManageReports
    Admin --> UC_ManageCompanies
    Admin --> UC_ViewDashboard

    %% Includes & Extends
    UC_ManualAnalyze -.->|<<include>>| UC_ViewResult
    UC_UploadOCR -.->|<<include>>| UC_ViewResult
    UC_ViewResult -.->|<<extend>>| UC_ExamineRedFlags
    UC_ViewResult -.->|<<extend>>| UC_SubmitFeedback
    UC_ViewResult -.->|<<extend>>| UC_SubmitReport
```

---

## 2. Use Case Descriptions

| Use Case | Primary Actor | Pre-Conditions | Post-Conditions |
| :--- | :--- | :--- | :--- |
| **Analyze Job Opportunity** | Authenticated User | Valid JWT Bearer token, minimum 30 characters of job text | Analysis saved to database, multi-dimensional trust score rendered. |
| **Scan Job Screenshot (OCR)** | Authenticated User | Valid image file (PNG/JPG/WEBP, ≤ 5 MB) | Image text extracted, validated for relevance, analyzed, and linked to user history. |
| **Browse Analysis History** | Authenticated User | User logged in | Paginated list of user's past scans retrieved from database. |
| **Delete Analysis Record** | Authenticated User | User owns the target analysis record | Record and linked job posting safely deleted; cannot affect other users. |
| **View Profile** | Authenticated User | User logged in | Name, email, registration date, and aggregate scan breakdown rendered without exposing password. |
| **Company Verification** | Authenticated User | Company name entered | Registry matched status, domain consistency, and impersonation risk displayed. |
