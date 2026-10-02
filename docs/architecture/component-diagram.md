# AI JobShield — Component Diagram

This document illustrates the internal component modularity of **AI JobShield**, highlighting the separation of concerns across presentation, routing, business logic, security rules, and data access.

---

## Component Modularity Diagram

```mermaid
graph TB
    subgraph UIComponents ["Frontend Components (React)"]
        Navbar["Navbar.jsx"]
        AuthView["AuthPage.jsx"]
        DashView["Dashboard.jsx"]
        AnalyzeView["AnalyzePage.jsx"]
        OcrView["OcrPage.jsx"]
        ResultView["ResultPage.jsx"]
        HistoryView["HistoryPage.jsx"]
        ProfileView["ProfilePage.jsx"]
        TrustGauge["TrustGauge.jsx"]
        ResultCard["AnalysisResultView.jsx"]

        ResultView --> ResultCard
        OcrView --> ResultCard
        ResultCard --> TrustGauge
    end

    subgraph APIClientModule ["Frontend API Client"]
        AxiosClient["client.js (Axios Instance)"]
        AuthInterceptor["JWT Bearer Interceptor"]
        ErrorInterceptor["Unified Error Handler"]

        AxiosClient --> AuthInterceptor
        AxiosClient --> ErrorInterceptor
    end

    UIComponents --> AxiosClient

    subgraph BackendRouters ["Backend API Routers (FastAPI)"]
        AuthRouter["routers/auth.py"]
        AnalyzeRouter["routers/analyze.py"]
        OcrRouter["routers/ocr.py"]
        HistoryRouter["routers/history.py"]
        CompanyRouter["routers/company.py"]
        UrlRouter["routers/url.py"]
        DashRouter["routers/dashboard.py"]
    end

    AxiosClient --> BackendRouters

    subgraph ServiceModules ["Core Business Logic & Analytical Services"]
        AnalyzerOrchestrator["services/analyzer.py"]
        CompanyVerificationService["services/company_verifier.py"]
        RuleEngineService["services/rules.py"]
        MLInferenceService["services/ml_service.py"]
        ScoringService["services/scoring.py"]
        ExplanationService["services/explain.py"]
        OcrServiceEngine["services/ocr_service.py"]
        JobContentValidator["services/job_content_validator.py"]
        UrlAnalyzerHeuristics["services/url_analyzer.py"]
        DuplicateService["services/duplicate.py"]
        EmailService["services/email_service.py"]
    end

    AnalyzeRouter --> AnalyzerOrchestrator
    OcrRouter --> OcrServiceEngine
    OcrRouter --> JobContentValidator
    OcrRouter --> AnalyzerOrchestrator
    HistoryRouter --> AnalyzerOrchestrator
    AuthRouter --> EmailService

    AnalyzerOrchestrator --> CompanyVerificationService
    AnalyzerOrchestrator --> RuleEngineService
    AnalyzerOrchestrator --> MLInferenceService
    AnalyzerOrchestrator --> ScoringService
    AnalyzerOrchestrator --> ExplanationService
    AnalyzerOrchestrator --> DuplicateService
    AnalyzerOrchestrator --> UrlAnalyzerHeuristics

    subgraph DatabaseLayer ["Data Access & Models (SQLAlchemy ORM)"]
        DBModels["models.py (User, JobPosting, AnalysisResult, OcrResult, etc.)"]
        DBSession["database.py (Engine, SessionLocal, Compatibility Migrator)"]
    end

    AnalyzerOrchestrator --> DBModels
    HistoryRouter --> DBModels
    AuthRouter --> DBModels
    DashRouter --> DBModels
    CompanyVerificationService --> DBModels
    DBModels --> DBSession
```

---

## Component Interfaces & Data Responsibilities

| Component | Responsibility | Inputs | Outputs |
| :--- | :--- | :--- | :--- |
| **`analyzer.py`** | Coordinates posting validation, heuristic analysis, score calculation, and persistent storage. | Raw job parameters, `user_id`, DB session | Normalized `AnalysisResult` dictionary |
| **`company_verifier.py`** | Verifies employer identity against curated registries; detects corporate impersonation. | Company name, recruiter email, website URL | Status (`VERIFIED`, `UNVERIFIED`, `IMPERSONATION_RISK`), reasons, dimension score |
| **`rules.py`** | Deterministic keyword and regex rule execution detecting scam indicators. | Job text, salary, email, URL | Red flag list, positive indicator list, bonus points |
| **`ml_service.py`** | Evaluates job postings with a trained Scikit-Learn TF-IDF classifier. | Concatenated job text | Scam probability (0.0 to 1.0), top influential terms |
| **`scoring.py`** | Transparent 5-dimensional weighted trust rating bounded by evidence-based caps. | Dimension outputs, flags, positives, ML probability | Final Trust Score (0–100), Risk Level (`LOW`, `MEDIUM`, `HIGH`), score breakdown |
| **`explain.py`** | Builds human-readable structured explanations with transparent reasons. | Trust score, risk level, flags, positives, cap reasons | Multi-section structured markdown text |
| **`ocr_service.py`** | Image preprocessing and text extraction via Tesseract OCR. | Image bytes, filename, content type | Extracted text, confidence rating, metadata hints |
