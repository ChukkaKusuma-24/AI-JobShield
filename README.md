# AI JobShield — Intelligent Recruitment Scam Detection & Credibility Analysis Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![PyTest](https://img.shields.io/badge/Tests-20%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<p align="center">
  <strong>An end-to-end cybersecurity and machine learning platform that protects job seekers by detecting deceptive recruitment postings, fraudulent task schemes, brand impersonation, and upfront fee solicitation.</strong>
</p>

</div>

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [Proposed Solution](#-proposed-solution)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Application Workflow](#-application-workflow)
- [Database Schema & ER Model](#-database-schema--er-model)
- [REST API Documentation](#-rest-api-documentation)
- [Authentication & Security Flow](#-authentication--security-flow)
- [OCR Screenshot Processing Pipeline](#-ocr-screenshot-processing-pipeline)
- [Evidence-Based Credibility Scoring](#-evidence-based-credibility-scoring)
- [Scam & Red Flag Detection Engine](#-scam--red-flag-detection-engine)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Setup Guide](#-installation--setup-guide)
- [Environment Configuration](#-environment-configuration)
- [Automated Testing Suite](#-automated-testing-suite)
- [Screenshots & UI Showcase](#-screenshots--ui-showcase)
- [Future Enhancements](#-future-enhancements)
- [Author & License](#-author--license)

---

## 🎯 Project Overview

**AI JobShield** is a full-stack, enterprise-grade recruitment safety and analysis platform. Combining deterministic cybersecurity heuristics, Natural Language Processing (NLP), Optical Character Recognition (OCR), and multi-dimensional credibility scoring, AI JobShield thoroughly investigates online job descriptions, recruiter contacts, company domains, and mobile screenshot transcripts to shield candidates from employment fraud.

---

## ⚠️ Problem Statement

Employment and internship fraud has increased dramatically across professional platforms (LinkedIn, Telegram, WhatsApp, job boards). Fraudulent actors routinely exploit job seekers through:

1. **Brand Impersonation**: Claiming affiliation with established enterprises (e.g., Infosys, TCS, Google) while using personal webmail (`@gmail.com`) or lookalike domains.
2. **Financial Exploitation**: Demanding "registration fees," "training deposits," "laptop security charges," or equipment purchases before onboarding.
3. **Identity & Data Theft**: Soliciting sensitive documents (Aadhaar, PAN cards, bank credentials, OTPs) prior to any legitimate interview process.
4. **Deceptive Guarantees & Pressure**: Promising guaranteed income (e.g., "₹5,000/day for data entry"), "no interview direct joining," and extreme urgency ("limited seats within 24 hours").

Existing job platforms often rely on passive community reporting or basic keyword filters, failing to detect sophisticated brand impersonation or multi-channel recruitment tactics.

---

## 💡 Proposed Solution

AI JobShield implements a proactive, multi-layered defensive pipeline that treats **evidence as the foundation of trust**:

* **Never Trust Blind Names**: Known enterprise names are never whitelisted. A posting claiming to be from Infosys using a `@gmail.com` address is instantly classified as an **Impersonation Risk** and capped at high risk.
* **Evidence-Based Scrutiny for Unknown Companies**: Unverified organizations without corroborating public records are marked as **Unverified** with credibility hard-capped at moderate levels, rather than falsely classified as legitimate or automatically marked as scams.
* **5-Dimensional Weighted Scoring**: Aggregates Company Verification (25%), Source/URL Credibility (20%), Job Posting Quality (15%), Scam Detection (30%), and Contact/Domain Consistency (10%).
* **Complete Database Persistence**: Analyses are strictly scoped to the authenticated user and permanently recorded in a relational database (MySQL/SQLite).
* **Local OCR Integration**: Enables candidate screenshot analysis without sending sensitive personal resume details to third-party paid APIs.

---

## ✨ Key Features

* 🔐 **Secure Production Authentication**: Complete sign-up, login, and password reset flows with Bcrypt salt hashing, JWT tokens, and 6-digit email OTPs sent via Google Gmail SMTP.
* 🛡️ **Multi-Dimensional Job Analysis**: Evaluates job title, company name, text description, salary, recruiter email, and application URL across 5 independent risk dimensions.
* 📸 **OCR Job Scanner**: Tesseract-powered optical recognition pipeline extracts text from screenshots, resumes, or chat logs, accompanied by a job-relevance gatekeeper.
* 🏢 **Enterprise Company Verification**: Verifies employers against a curated corporate registry, enforcing strict domain consistency and alerting on recruiter webmail impersonation.
* 🚩 **Deterministic Red Flag Engine**: Analyzes 14 critical scam signals, identifying upfront fees, equipment deposits, sensitive ID solicitations, and WhatsApp-only communication.
* 🤖 **Machine Learning Classifier**: Scikit-Learn TF-IDF vectorizer paired with a calibrated linear classifier evaluates semantic scam probabilities and extracts influential vocabulary tokens.
* 📊 **Persistent User Scan History**: Filterable, paginated history surviving page reloads, logouts, and restarts, featuring complete user isolation and single-record deletion.
* 📈 **Interactive Security Dashboard**: Aggregated real-time metrics, risk distribution donut charts, and 14-day scanning activity histograms.
* 👤 **User Profile & Security Workspace**: Identity inspection showing registration timestamp, verified account badge, aggregate risk summary, and security standards overview.

---

## 🏛️ System Architecture

AI JobShield follows a clean, decoupled multi-tier architectural pattern:

```mermaid
graph TD
    subgraph Client ["Client Presentation Layer (React 18 + Vite)"]
        UI["Tailwind CSS UI & Component Views"]
        AuthContext["AuthContext (JWT & LocalStorage Session)"]
        ClientAPI["Axios API Client (client.js)"]
        UI --> AuthContext --> ClientAPI
    end

    subgraph Gateway ["Application Gateway (FastAPI ASGI)"]
        RouterAuth["Auth Router (/api/auth)"]
        RouterAnalyze["Analyze Router (/api/analyze)"]
        RouterOCR["OCR Router (/api/ocr)"]
        RouterHistory["History Router (/api/history)"]
        RouterDash["Dashboard Router (/api/dashboard)"]
    end

    ClientAPI -->|REST API over HTTP/CORS| Gateway

    subgraph AnalyticalEngines ["Intelligence & Analytical Pipeline"]
        TesseractOCR["Tesseract OCR Engine"]
        JobContentGate["Content Relevance Gatekeeper"]
        CompanyVerifier["Company Registry & Domain Matcher"]
        RuleEngine["Deterministic Scam Rule Engine"]
        MLClassifier["TF-IDF + SGD Logistic Classifier"]
        ScoringEngine["5-Dimensional Weighted Scoring Engine"]
        ExplainEngine["Explainability & Rationale Builder"]
    end

    RouterOCR --> TesseractOCR --> JobContentGate --> RouterAnalyze
    RouterAnalyze --> CompanyVerifier
    RouterAnalyze --> RuleEngine
    RouterAnalyze --> MLClassifier
    RouterAnalyze --> ScoringEngine
    RouterAnalyze --> ExplainEngine

    subgraph Persistence ["Persistence Layer"]
        MySQL[("MySQL 8.0 / SQLite Database")]
        CuratedJSON[("Verified Enterprise Registry (JSON)")]
        ModelJoblib[("Serialized ML Model (.joblib)")]
    end

    CompanyVerifier --> CuratedJSON
    MLClassifier --> ModelJoblib
    Gateway --> MySQL
    AnalyticalEngines --> MySQL
```

> Detailed architecture diagrams and narratives are available in [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md) and [docs/architecture/component-diagram.md](docs/architecture/component-diagram.md).

---

## 🔄 Application Workflow

```mermaid
flowchart TD
    Start([User visits AI JobShield]) --> AuthCheck{Authenticated?}
    AuthCheck -- No --> AuthPage[Register / Sign In with Email OTP]
    AuthPage --> AuthCheck
    AuthCheck -- Yes --> Dashboard[User Dashboard]

    Dashboard --> InputMethod{Select Ingestion Method}
    InputMethod -- Manual Entry --> JobForm[Enter Job Title, Company, Description, Email, URL]
    InputMethod -- Image Upload --> OCRUpload[Upload Screenshot of Job or Chat]

    OCRUpload --> OCRProcess[Extract Text via Tesseract]
    OCRProcess --> GateValidation{Job Related?}
    GateValidation -- No --> GateReject[Reject: Not Job Related]
    GateReject --> OCRUpload
    GateValidation -- Yes --> ExecuteAnalysis

    JobForm --> ExecuteAnalysis[Execute Analysis Pipeline]

    subgraph Pipeline ["Analytical & Scoring Pipeline"]
        ExecuteAnalysis --> CheckCompany[1. Company Verification & Domain Match]
        CheckCompany --> CheckRules[2. Detect Red Flags: Fees, Urgency, WhatsApp]
        CheckRules --> PredictML[3. ML Scam Probability Inference]
        PredictML --> Compute5D[4. 5-Dimensional Weighted Trust Calculation]
        Compute5D --> ApplyCaps[5. Enforce Evidence-Based Security Caps]
        ApplyCaps --> BuildRationale[6. Generate Natural Language Explanation]
    end

    Pipeline --> SaveDB[(Save to Database: job_postings & analysis_results)]
    SaveDB --> ShowResult[Display ResultPage with Trust Gauge & Breakdown]
    ShowResult --> HistoryView[Persisted in User History]
```

> Full sequence and activity diagrams are documented in [docs/diagrams/sequence.md](docs/diagrams/sequence.md) and [docs/diagrams/activity.md](docs/diagrams/activity.md).

---

## 🗄️ Database Schema & ER Model

AI JobShield uses SQLAlchemy 2.0 ORM with relational integrity constraints and database indexes:

```mermaid
erDiagram
    USERS ||--o{ JOB_POSTINGS : "creates"
    USERS ||--o{ ANALYSIS_RESULTS : "owns"
    USERS ||--o{ OCR_RESULTS : "uploads"
    USERS ||--o{ EMAIL_OTPS : "has"
    JOB_POSTINGS ||--|| ANALYSIS_RESULTS : "analyzed_in"
    ANALYSIS_RESULTS ||--o| OCR_RESULTS : "linked_to"
    ANALYSIS_RESULTS ||--o{ DUPLICATE_MATCHES : "triggers"
    ANALYSIS_RESULTS ||--o{ FEEDBACK : "receives"

    USERS {
        int id PK
        string name
        string email UK "Indexed"
        string password_hash "Bcrypt"
        boolean is_verified
        datetime created_at "Indexed"
    }

    JOB_POSTINGS {
        int id PK
        int user_id FK "Indexed"
        string title
        string company_name
        text description
        string salary
        string email
        string url
        string source
        datetime created_at "Indexed"
    }

    ANALYSIS_RESULTS {
        int id PK
        int job_posting_id FK
        int user_id FK "Indexed"
        int trust_score "0-100"
        string risk_level "LOW | MEDIUM | HIGH"
        text red_flags "JSON"
        text positive_indicators "JSON"
        text explanation "Markdown"
        text company_verification "JSON"
        text score_breakdown "JSON"
        text extracted_ocr_text "Nullable"
        datetime created_at "Indexed"
    }
```

> Full entity specifications, field descriptions, and foreign key rules are documented in [docs/diagrams/er-diagram.md](docs/diagrams/er-diagram.md).

---

## 📡 REST API Documentation

All secured endpoints require the header `Authorization: Bearer <JWT_TOKEN>`.

### Authentication Endpoints
* `POST /api/auth/register` — Registers new account, hashes password, triggers email OTP.
* `POST /api/auth/verify-email` — Validates 6-digit OTP, verifies account, issues JWT token.
* `POST /api/auth/login` — Verifies credentials, enforces OTP verification, returns JWT token.
* `POST /api/auth/resend-otp` — Resends a fresh verification OTP (enforces 60-second rate-limiting).
* `POST /api/auth/forgot-password` — Sends password reset code to registered user.
* `POST /api/auth/reset-password` — Validates reset OTP and updates password.
* `GET /api/auth/me` — Returns current authenticated user profile (`id`, `name`, `email`, `role`, `created_at`).

### Core Analysis & OCR Endpoints
* `POST /api/analyze` — Analyzes job parameters, computes 5-dimensional score, commits record to database.
* `POST /api/ocr/analyze` — Multipart image upload (`PNG/JPG/WEBP`), runs Tesseract OCR, validates relevance, and persists analysis.

### History & Workspace Endpoints
* `GET /api/history` — Retrieves paginated, user-scoped scan history (`page`, `limit`, `risk_level` filter).
* `GET /api/history/{id}` — Retrieves full analysis breakdown for a single previous scan.
* `DELETE /api/history/{id}` — Permanently deletes an analysis record belonging to the authenticated user.
* `GET /api/dashboard` — Returns real-time aggregate statistics, risk distributions, and 14-day history.
* `POST /api/company/verify` — Standalone endpoint for enterprise validation and domain mismatch detection.
* `POST /api/url/analyze` — Standalone endpoint for local URL heuristic evaluation.

---

## 🔒 Authentication & Security Flow

1. **Password Hashing**: User passwords are encrypted with bcrypt utilizing automatic salting; passwords are never logged or stored in plaintext.
2. **Email Verification with OTP**: Upon registration, an unverified account is created and a time-limited (10-minute) 6-digit numerical OTP is dispatched via Google Gmail SMTP.
3. **Session Management**: Authenticated requests require an HMAC-SHA256 signed JSON Web Token (JWT) expiring after 24 hours.
4. **Data Isolation**: The user ID is strictly extracted from the validated JWT token by backend dependencies (`CurrentUser`). Frontend-supplied user IDs are never trusted.
5. **Rate-Limiting Protection**: Sliding-window rate limiters prevent brute-force attacks on login and verification endpoints.

---

## 🔍 OCR Screenshot Processing Pipeline

```
┌─────────────────┐     ┌───────────────┐     ┌───────────────────────┐
│ Upload Image    │ ──> │ Tesseract OCR │ ──> │ Job Content Validator │
│ (PNG/JPG ≤5 MB) │     │ Engine        │     │ (Gatekeeper)          │
└─────────────────┘     └───────────────┘     └───────────────────────┘
                                                          │
                                         ┌────────────────┴───────────────┐
                                         ▼                                ▼
                                  [Not Job Related]              [Valid Job Posting]
                                  422 Gate Error                 Proceed to 5D Engine
```

1. **Upload & Preprocessing**: Images are validated for supported format (`image/png`, `image/jpeg`, `image/webp`) and size (≤ 5 MB).
2. **Text Extraction**: Tesseract OCR extracts character streams, structural lines, and confidence ratings.
3. **Relevance Gatekeeper (`job_content_validator.py`)**: Checks text against job signals (roles, salaries, requirements) versus anti-signals (grocery receipts, memes, code snippets). Non-job images are gracefully rejected with a helpful user prompt.
4. **Database Archival**: The extracted text is preserved directly in the `analysis_results` table under `extracted_ocr_text` for complete historical auditability.

---

## ⚖️ Evidence-Based Credibility Scoring

The scoring system replaces simplistic name whitelists with a transparent **5-dimensional weighted framework**:

$$\text{Raw Score} = 0.25 \times \text{Company} + 0.20 \times \text{Source} + 0.15 \times \text{Quality} + 0.30 \times \text{Scam} + 0.10 \times \text{Contact}$$

| Dimension | Weight | Evaluation Criteria |
| :--- | :---: | :--- |
| **1. Company Verification** | **25%** | Cross-referenced against verified enterprise records (`data/verified_companies.json`) and database registries. Checks corporate domain consistency. |
| **2. Source / URL Credibility** | **20%** | Validates HTTPS protocol, checks for URL shorteners, punycode attacks, IP hosts, and mismatch between URL domain and company name. |
| **3. Job Posting Quality** | **15%** | Measures clarity of responsibilities, explicit qualifications, realistic compensation, and selection process details. Deducts for vague text. |
| **4. Scam & Red Flag Detection** | **30%** | Deterministic detection of upfront fees, equipment deposits, crypto/gift card requests, sensitive ID solicitations, and WhatsApp-only recruitment. |
| **5. Contact & Domain Consistency** | **10%** | Validates corporate domain alignment (`@infosys.com`) versus personal/free email providers (`@gmail.com`). |

### Safety Guardrails & Evidence-Based Caps
* 🚨 **Critical Scam Indicator Triggered**: When fees, equipment payments, or sensitive financial data are requested, Trust Score is strictly capped at **≤ 35** (**HIGH RISK / LIKELY SCAM**). Positive bonuses cannot cancel serious red flags.
* 🚨 **Company Impersonation Risk**: When a known brand (e.g., Infosys) is paired with a free or mismatched email (`@gmail.com`), Trust Score is capped at **≤ 25** (**HIGH RISK**).
* 🛡️ **Unverified Company**: When an unknown company has no independent public record, lack of evidence is never treated as positive proof; Trust Score is capped at **≤ 65** (**MEDIUM RISK**).
* 🛡️ **Partially Verified Company**: When a recognized company lacks official contact links, Trust Score is capped at **≤ 75**.

---

## 🚩 Scam & Red Flag Detection Engine

| Risk Indicator | Severity | Penalty | Target Signals |
| :--- | :---: | :---: | :--- |
| **`fee_request`** | **Critical** | 35 pts | "registration fee", "application fee", "training fee", "security deposit", "pay to join" |
| **`money_transfer`** | **Critical** | 35 pts | "gift card", "western union", "crypto", "bitcoin", "upi payment", "send money" |
| **`equipment_purchase`** | **Critical** | 35 pts | "purchase laptop", "buy equipment", "laptop deposit", "home office kit fee" |
| **`company_impersonation`** | **Critical** | 35 pts | Claimed enterprise name using free webmail (`@gmail.com`, `@yahoo.com`) |
| **`sensitive_info`** | **Critical** | 30 pts | Solicits Aadhaar, PAN, SSN, passport, bank account details, or OTPs prior to interview |
| **`unrealistic_salary`** | **High** | 20 pts | Daily earnings exceeding ₹2,000/day or entry-level monthly salary exceeding ₹80,000/mo |
| **`suspicious_contact`** | **High** | 15 pts | "WhatsApp only", "Telegram only", "message on WhatsApp", no formal corporate channel |
| **`email_domain_mismatch`** | **High** | 15 pts | Email domain shares no naming tokens with claimed company entity |
| **`free_email`** | **Medium** | 12 pts | Company recruiter using free email provider for corporate recruitment |
| **`no_interview`** | **Medium** | 12 pts | "No interview needed", "guaranteed job", "instant selection", "direct joining" |
| **`urgency`** | **Medium** | 10 pts | "Within 24 hours", "limited seats", "hurry up", "urgent hiring", "apply now or miss out" |
| **`vague_description`** | **Medium** | 10 pts | Under 80 characters, missing job duties, or lacking minimum qualifications |
| **`caps_exclaim`** | **Low** | 5 pts | Excessive uppercase letters (>35%) or multiple exclamation marks (≥4) |

---

## 💻 Technology Stack

### Frontend
* **Core**: React 18 (SPA), JavaScript (ES2022+), HTML5, CSS3
* **Build System**: Vite 5 / Rolldown
* **Styling**: Tailwind CSS with custom design tokens
* **Routing**: React Router v6
* **Data Visualization**: Recharts (Pie/Donut charts, Bar histograms), SVG Trust Gauge
* **HTTP Client**: Axios with unified interceptors

### Backend & AI
* **Framework**: FastAPI (Asynchronous Python 3.10+)
* **ASGI Server**: Uvicorn with AnyIO event loop
* **ORM**: SQLAlchemy 2.0 with connection pooling
* **Relational Database**: MySQL 8.0 (Production) / SQLite (Testing)
* **OCR**: Tesseract OCR via `pytesseract`
* **Machine Learning**: Scikit-Learn (TF-IDF vectorizer, SGDClassifier / Logistic Regression)
* **Authentication**: PyJWT (HMAC-SHA256) & Passlib / Bcrypt
* **Email / SMTP**: Python `smtplib` with TLS over Google Gmail SMTP

---

## 📂 Project Directory Structure

```
AI-JobShield/
├── backend/                        # FastAPI application root
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory & CORS configuration
│   │   ├── config.py               # Pydantic BaseSettings environment loader
│   │   ├── database.py             # Database engine, session maker, schema compatibility
│   │   ├── models.py               # SQLAlchemy ORM entity models
│   │   ├── deps.py                 # Dependency injection: DbSession & CurrentUser
│   │   ├── routers/                # REST API router endpoints
│   │   │   ├── auth.py             # Register, Login, Verify Email OTP, Forgot Password
│   │   │   ├── analyze.py          # Job posting analysis orchestration
│   │   │   ├── ocr.py              # Screenshot upload & Tesseract OCR processing
│   │   │   ├── history.py          # User-scoped history CRUD & deletion
│   │   │   ├── dashboard.py        # Aggregate metrics & risk distributions
│   │   │   ├── company.py          # Company registry & verification endpoints
│   │   │   ├── url.py              # URL heuristic evaluation endpoints
│   │   │   ├── reports.py          # Scam community reporting
│   │   │   └── feedback.py         # Prediction feedback logging
│   │   └── services/               # Core business & analytical logic
│   │       ├── analyzer.py         # Full pipeline coordinator
│   │       ├── company_verifier.py # Evidence-based company & domain verification
│   │       ├── rules.py            # Rule engine with 14 red-flag patterns
│   │       ├── scoring.py          # 5-dimensional weighted scoring & safety caps
│   │       ├── explain.py          # Structured markdown rationale builder
│   │       ├── ml_service.py       # Scikit-Learn TF-IDF model inference
│   │       ├── ocr_service.py      # Tesseract image OCR & hint extraction
│   │       ├── job_content_validator.py # OCR job relevance gatekeeper
│   │       ├── url_analyzer.py     # Local URL security heuristics
│   │       ├── duplicate.py        # Duplicate posting detection
│   │       └── email_service.py    # Gmail SMTP OTP delivery with console fallback
│   ├── requirements.txt            # Python dependencies
│   └── seed.py                     # Database initialization & demo seed script
│
├── frontend/                       # React SPA root
│   ├── src/
│   │   ├── main.jsx                # Application root mount
│   │   ├── App.jsx                 # Route definitions & protected route guards
│   │   ├── api/
│   │   │   └── client.js           # Axios API client with auth interceptors
│   │   ├── components/             # Reusable UI components
│   │   │   ├── Navbar.jsx          # Header navigation with profile link & auth state
│   │   │   ├── TrustGauge.jsx      # Interactive SVG trust rating gauge
│   │   │   ├── AnalysisResultView.jsx # 5D breakdown, red flags, stored details, OCR viewer
│   │   │   ├── FeedbackWidget.jsx  # Accuracy feedback submission
│   │   │   └── ProtectedRoute.jsx  # Route authorization guard
│   │   ├── context/
│   │   │   └── AuthContext.jsx     # Authentication context & session persistence
│   │   ├── pages/                  # Page route components
│   │   │   ├── Landing.jsx         # Public landing page
│   │   │   ├── AuthPage.jsx        # Login, registration & email OTP verification
│   │   │   ├── Dashboard.jsx       # Security metrics & recent analysis feed
│   │   │   ├── AnalyzePage.jsx     # Manual job posting analysis form
│   │   │   ├── OcrPage.jsx         # Image screenshot OCR upload & processing
│   │   │   ├── ResultPage.jsx      # Analysis result view (fetches from DB)
│   │   │   ├── HistoryPage.jsx     # Paginated analysis history with delete actions
│   │   │   ├── ProfilePage.jsx     # User profile, security summary & stats
│   │   │   ├── CompanyPage.jsx     # Standalone company verification lookup
│   │   │   ├── UrlPage.jsx         # Standalone URL security inspector
│   │   │   └── ReportsPage.jsx     # Community scam report submission
│   │   └── utils/
│   │       └── helpers.js          # Severity styling helpers & mock sample loaders
│   ├── package.json                # Frontend dependencies
│   └── vite.config.js              # Vite bundler configuration
│
├── data/                           # Curated security datasets
│   ├── verified_companies.json     # Recognized enterprise registry & official domains
│   ├── free_email_domains.json     # List of public webmail providers
│   └── suspicious_tlds.json        # High-risk top-level domains
│
├── docs/                           # Comprehensive project documentation
│   ├── architecture/
│   │   ├── system-architecture.md  # Multi-tier architecture specification
│   │   ├── component-diagram.md    # Internal component modularity
│   │   └── deployment-architecture.md # Runtime & deployment topology
│   ├── diagrams/
│   │   ├── use-case.md             # Use case diagram & actor specifications
│   │   ├── dfd.md                  # Level 0 and Level 1 Data Flow Diagrams
│   │   ├── er-diagram.md           # Entity-relationship diagram & data dictionary
│   │   ├── sequence.md             # Time-ordered interaction sequence diagrams
│   │   ├── activity.md             # Job analysis activity & state diagram
│   │   └── workflow.md             # End-to-end user flowchart
│   └── screenshots/
│       └── README.md               # Visual UI tour & screenshot catalogue
│
├── models/                         # Serialized ML assets
│   ├── jobshield_model.joblib      # Pre-trained TF-IDF + SGDClassifier pipeline
│   └── confusion_matrix.png        # Model evaluation performance chart
│
├── tests/                          # Automated test suite
│   ├── test_api.py                 # Core API endpoints & auth tests
│   ├── test_history_and_scoring.py # History persistence, user isolation & Cases A–F
│   ├── test_job_content_validator.py # OCR gatekeeper test cases
│   └── test_ocr_job_gate_api.py    # OCR API integration tests
│
├── .env.example                    # Template environment variables (no secrets)
├── .gitignore                      # Git exclusion rules (prevents secret leaks)
└── README.md                       # Master project documentation
```

---

## 🚀 Installation & Setup Guide

### Prerequisites
* **Python**: v3.10 or higher
* **Node.js**: v18.0 or higher
* **MySQL**: v8.0 or higher (or SQLite, which requires zero configuration)
* **Tesseract OCR**: Optional for OCR screenshot scanning ([Tesseract Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki))

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/ChukkaKusuma-24/AI-JobShield.git
cd AI-JobShield
```

---

### Step 2: Configure Environment Variables
Create your local `.env` file from the provided template:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `copy .env.example .env`)*

Configure your database and Gmail SMTP credentials in `.env`:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/ai_jobshield
# Or use SQLite without installing MySQL:
# DATABASE_URL=sqlite:///./database/jobshield.db

SMTP_USER=your.gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

---

### Step 3: Backend Setup & Database Migration
```bash
# Create and activate Python virtual environment
python -m venv backend/venv

# Windows
backend\venv\Scripts\activate
# macOS/Linux
# source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run initial seed data
python backend/seed.py

# Start FastAPI server
cd backend
uvicorn app.main:app --reload --port 8000
```
Backend API interactive Swagger documentation will be available at: **`http://localhost:8000/docs`**

---

### Step 4: Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser to access AI JobShield.

---

## ⚙️ Environment Configuration

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy database connection URI | `mysql+pymysql://root:pass@localhost:3306/ai_jobshield` |
| `SECRET_KEY` | Secret key used for signing session tokens | Random cryptographic string |
| `JWT_SECRET` | Secret key used for HMAC-SHA256 JWT tokens | Random cryptographic string |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `1440` (24 hours) |
| `SMTP_HOST` | Outgoing SMTP mail server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Gmail address for OTP delivery | `your.address@gmail.com` |
| `SMTP_PASSWORD` | 16-character Google App Password | `xxxx xxxx xxxx xxxx` |
| `SMTP_CONSOLE_FALLBACK` | Print OTP to console if SMTP is unconfigured | `false` (set `true` in test runs) |
| `TESSERACT_CMD` | Full path to Tesseract OCR executable | `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `VITE_API_BASE` | Frontend base URL for backend API | `http://127.0.0.1:8000/api` |

---

## 🧪 Automated Testing Suite

AI JobShield features a rigorous automated test suite executing across SQLite and MySQL test fixtures:

```bash
# Run the complete test suite
pytest tests -v
```

### Verified Test Cases
1. **User History Lifecycle & Data Isolation**:
   * Registers User 1 → Confirms empty history.
   * Analyzes Job 1 → Confirms all fields stored in DB.
   * Analyzes Job 2 → Confirms reverse chronological order.
   * Simulates browser refresh, logout, and re-login → History persists intact from DB.
   * Registers User 2 → Confirms User 2 has empty history and receives `403 Forbidden` attempting to access or delete User 1's records.
   * User 1 deletes Job 1 → Confirms successful deletion.
2. **Scoring Case A (Well-known company + legitimate job)**:
   * Entity: Infosys | Email: `careers@infosys.com`
   * **Result**: `VERIFIED`, Trust Score: **96/100 (LOW RISK)**.
3. **Scoring Case B (Unknown company + normal job)**:
   * Entity: Krypton Web Solutions | Email: `hiring@kryptonwebsolutions.io`
   * **Result**: `UNVERIFIED`, Trust Score: **60/100 (MEDIUM RISK)**. Capped at ≤ 65; clearly marked as unverified.
4. **Scoring Case C (Unknown company + registration fee request)**:
   * Description: Demands ₹1,499 registration fee via WhatsApp.
   * **Result**: Trust Score: **18/100 (HIGH RISK / LIKELY SCAM)**. Critical fee cap applied.
5. **Scoring Case D (Known brand + suspicious email impersonation)**:
   * Entity: Infosys | Email: `infosys.campus.recruiter@gmail.com`
   * **Result**: `IMPERSONATION_RISK`, Trust Score: **18/100 (HIGH RISK)**. Impersonation cap applied.
6. **Scoring Case E (Known brand + suspicious payment request)**:
   * Entity: Infosys | Description: Demands ₹5,000 laptop security deposit.
   * **Result**: Trust Score: **34/100 (HIGH RISK)**. Verified company name does not override critical scam flag.
7. **Scoring Case F (Legitimate company + incomplete evidence)**:
   * Entity: Wipro | No recruiter email or careers URL provided.
   * **Result**: `PARTIALLY VERIFIED`, Trust Score: **68/100 (MEDIUM RISK)**.

---

## 📸 Screenshots & UI Showcase

Visual assets and page tours are documented in [docs/screenshots/README.md](docs/screenshots/README.md):

* 📊 **Security Dashboard**: Live scan counters, Recharts risk distributions, and recent analyses table.
* 🔎 **Analysis Engine**: Parameterized input with pre-loaded legit and scam samples.
* 📷 **OCR Scanner**: Drag-and-drop file ingestion, processing spinner, and job relevance gatekeeper.
* 🛡️ **Multi-Dimensional Result View**: Dynamic SVG Trust Gauge, 5-dimension progress cards, direct quote evidence, and expandable raw OCR text viewer.
* 📜 **Analysis History**: Paginated history table with risk filtering and safe record deletion.
* 👤 **User Profile**: Account verification status, member date, and personal risk breakdown.

---

## 🔮 Future Enhancements

* 🌐 **Browser Extension**: A lightweight Chrome extension to analyze job listings directly on LinkedIn, Indeed, and Internshala with a single click.
* 🤖 **Multi-Modal Deep Learning**: Incorporate multi-modal vision-language models (e.g., Gemini Flash) to analyze image layouts, fake corporate logos, and manipulated offer letters.
* 📱 **Mobile Application**: Native React Native / Flutter cross-platform client for instant camera scanning of printed job flyers and physical recruitment banners.
* 🤝 **Community Blacklist Consensus**: Decentralized, peer-reviewed voting mechanisms on community scam reports with automated registrar abuse reporting.

---

## 👤 Author & License

* **Developer**: Chukka Kusuma ([@ChukkaKusuma-24](https://github.com/ChukkaKusuma-24))
* **License**: This project is licensed under the [MIT License](LICENSE).
* **Disclaimer**: *AI JobShield provides risk-scoring guidance and pattern detection based on available evidence, not an absolute legal verdict. Always verify job opportunities through official corporate channels.*
