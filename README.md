# AI JobShield — Intelligent Recruitment Scam Detection & Credibility Analysis Platform

<div align="center">

![Academic Project](https://img.shields.io/badge/Project-Software%20Engineering%20Capstone-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Tests](https://img.shields.io/badge/Test%20Suite-110%20Cases%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<p align="center">
  <strong>An end-to-end cybersecurity and machine learning platform that protects job seekers by detecting deceptive recruitment postings, fraudulent task schemes, brand impersonation, and upfront fee solicitation.</strong>
</p>

[SRS Document](docs/SRS.md) • [Traceability Matrix](docs/requirements-traceability-matrix.md) • [System Architecture](docs/architecture/system-architecture.md) • [UML Diagrams](docs/uml/use-case/use-case-diagram.md) • [DFD Diagrams](docs/dfd/dfd-diagrams.md) • [API Reference](docs/api/api-documentation.md) • [Test Cases](docs/testing/test-cases.md)

</div>

---

## 📑 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Project Objectives](#-project-objectives)
3. [Proposed Solution](#-proposed-solution)
4. [Key Features](#-key-features)
5. [System Users / Actors](#-system-users--actors)
6. [System Architecture](#-system-architecture)
7. [Technology Stack](#-technology-stack)
8. [Database Design](#-database-design)
9. [UML Diagrams](#-uml-diagrams)
10. [Data Flow Diagrams (DFD)](#-data-flow-diagrams-dfd)
11. [Application Workflow](#-application-workflow)
12. [Authentication & Security](#-authentication--security)
13. [OCR Processing Pipeline](#-ocr-processing-pipeline)
14. [AI / Machine Learning Analysis](#-ai--machine-learning-analysis)
15. [Credibility & Risk Scoring Methodology](#-credibility--risk-scoring-methodology)
16. [Scam & Red Flag Detection Engine](#-scam--red-flag-detection-engine)
17. [REST API Documentation](#-rest-api-documentation)
18. [Project Structure](#-project-structure)
19. [Installation & Setup](#-installation--setup)
20. [Environment Variables](#-environment-variables)
21. [Demo & Seed Accounts](#-demo--seed-accounts)
22. [Automated Testing Suite](#-automated-testing-suite)
23. [UI Screenshots](#-ui-screenshots)
24. [Future Enhancements](#-future-enhancements)
25. [License & Author](#-license--author)

---

## ⚠️ Problem Statement

Employment fraud has escalated dramatically across modern hiring channels (LinkedIn, Telegram, WhatsApp, unsolicited SMS, and online job boards). Malicious actors exploit job seekers—particularly students, fresh graduates, and career transitioners—through sophisticated deceptive strategies:

1. **Brand Impersonation**: Fraudsters falsely claim corporate affiliations with established IT and multinational brands (e.g., Infosys, TCS, Google, Amazon) while contacting candidates from free public webmail (`@gmail.com`, `@yahoo.com`) or lookalike typo-squatted domains.
2. **Upfront Financial Exploitation**: Deceptive offers demand payment for "registration fees," "mandatory training modules," "laptop/equipment security deposits," or "background screening charges" prior to employment.
3. **Data Harvesting & Identity Theft**: Fraudulent postings solicit Aadhaar, PAN card scans, bank account credentials, or mobile verification OTPs under the pretext of onboarding documentation before any interview takes place.
4. **Task & Crypto Scams**: Deceptive listings advertise unrealistic compensation (e.g., *"₹5,000/day for YouTube video liking or data entry"*) requiring users to complete tasks and deposit cryptocurrency or cash to release "earnings."
5. **Urgency & Interview-Free Direct Joining**: High-pressure tactics (*"Direct selection without interview"*, *"Join within 24 hours"*), pushing victims into rash financial decisions.

Existing job boards often employ passive keyword flags or rely on delayed manual reports after victims have already lost money. **AI JobShield** addresses this void through automated, proactive, multi-signal credibility verification.

---

## 🎯 Project Objectives

* **Proactive Scam Prevention**: Provide job seekers with an immediate risk assessment before they engage, reply, or transfer funds to prospective recruiters.
* **Evidence-Based Trust Verification**: Replace naive name-matching with an evidence-based framework where brand names are verified against authentic corporate registries, official domain records, and strict email consistency checks.
* **Multi-Modal Analysis**: Support both structured text input and direct mobile screenshot ingestion via local Optical Character Recognition (OCR) with an intelligent job relevance gatekeeper.
* **Hybrid Intelligence Engine**: Combine 14 deterministic cybersecurity heuristic rules with calibrated Natural Language Processing (TF-IDF + SGD Logistic Regression) and 5-dimensional weighted risk scoring.
* **Safety Guardrails & Hard Caps**: Enforce rigorous security caps so positive indicators cannot mask critical danger signals (e.g., upfront payment requests cap trust score at $\le 35$).
* **Complete User Isolation & Auditability**: Ensure all scans are securely persisted in a relational database scoped to authenticated user accounts, supporting paginated history, audit trails, and aggregate dashboard insights.

---

## 💡 Proposed Solution

**AI JobShield** delivers an enterprise-grade recruitment safety and credibility analysis platform:

```
[Job Input / Screenshot] ──> [Gatekeeper & OCR] ──> [5-Dimension Evaluation] ──> [Evidence Caps] ──> [Guarded Trust Score]
```

* **Never Trust Blind Names**: Claiming a reputable company name does not grant trust. An application claiming to represent *Infosys* using an `@gmail.com` address is instantly classified as an **Impersonation Risk** and capped at $\le 25$ (High Risk).
* **Objective Handling of Unknown Organizations**: Unverified organizations without public records are classified as **Unverified** with credibility capped at $\le 65$ (Medium Risk) rather than falsely certified as safe or unfairly flagged as outright scams.
* **5-Dimensional Weighted Scoring**: Aggregates Company Verification (25%), Source/URL Credibility (20%), Job Posting Quality (15%), Scam Detection (30%), and Contact/Domain Consistency (10%).
* **Explainable Rationale**: Generates transparent natural language breakdowns, direct quote extractions of suspicious text, and actionable safety recommendations.
* **Zero External Data Leakage**: Optical character recognition is processed locally via Tesseract, preventing candidate resumes or personal chats from being leaked to third-party commercial APIs.

---

## ✨ Key Features

| Capability | Module / Component | Detailed Implementation |
| :--- | :--- | :--- |
| **User Registration & Login** | `auth.py` / `AuthPage.jsx` | Bcrypt password hashing, session tokens, and account profile management. |
| **Email OTP Verification** | `email_service.py` | 6-digit numeric OTP with 10-minute expiry dispatched via Google Gmail SMTP (console fallback for testing). |
| **JWT Authentication** | `deps.py` / `client.js` | HMAC-SHA256 signed bearer tokens with 24-hour lifetime and automatic Axios request interceptors. |
| **Multi-Param Job Analysis** | `analyze.py` / `analyzer.py` | Evaluates job title, company name, description, salary, recruiter email, and application URL. |
| **Enterprise Verification** | `company_verifier.py` | Validates against `data/verified_companies.json` and database registries; alerts on domain mismatch and recruiter webmail. |
| **Deterministic Red Flag Engine** | `rules.py` | 14 rule patterns detecting upfront fees, equipment deposits, sensitive ID solicitations, and WhatsApp-only channels. |
| **Machine Learning Analysis** | `ml_service.py` | Scikit-Learn TF-IDF vectorizer + SGDClassifier inferring statistical scam probability and extracting influential terms. |
| **OCR Screenshot Scanner** | `ocr.py` / `ocr_service.py` | Ingests mobile screenshots (`PNG/JPG/WEBP`), runs Tesseract OCR, and extracts structural contact information. |
| **Job Content Gatekeeper** | `job_content_validator.py` | Pre-analysis filter rejecting non-job images (memes, food receipts, random code) with HTTP 422 before analytical processing. |
| **5-Dimensional Credibility Scoring** | `scoring.py` | Weighted composite score with 4 safety caps (impersonation, fee requests, unverified company, partial info). |
| **Persistent User History** | `history.py` / `HistoryPage.jsx`| Relational database storage strictly scoped to authenticated user with pagination, risk filters, and record deletion. |
| **Interactive Dashboard** | `dashboard.py` / `Dashboard.jsx`| Real-time KPIs, scan volume counters, Recharts risk distribution charts, and 14-day activity timelines. |
| **User Profile & Security** | `ProfilePage.jsx` | Shows account verification status, registration date, aggregate risk breakdown, and platform security standards. |
| **URL Security Inspection** | `url_analyzer.py` / `UrlPage.jsx`| Evaluates HTTPS, domain shorteners, punycode attacks, raw IP hosts, and domain-company alignment. |
| **Community Scam Reports** | `reports.py` / `ReportsPage.jsx` | User-reported recruitment fraud logging with platform, contact, and evidence tracking. |

---

## 👥 System Users / Actors

AI JobShield distinguishes between explicit human actors and automated system components:

1. **Job Seeker / Candidate (Primary End User)**:
   * Registers, verifies email via OTP, and logs in securely.
   * Enters job descriptions or uploads recruitment screenshots/flyers.
   * Reviews detailed credibility scores, red-flag quotes, and safety advice.
   * Manages personal scan history and submits scam reports.
2. **Security Administrator (System Administrator)**:
   * Pre-seeded administrative role (`role="admin"`) for inspecting system health, verified company directories, and global platform usage.
3. **AI / Analytical Engine (Internal Automated Actor)**:
   * Orchestrates the 5-dimensional evaluation, invokes deterministic rules, runs ML inference, and generates markdown rationale.
4. **Tesseract OCR Subsystem (Internal Automated Actor)**:
   * Performs optical text recognition on uploaded images and feeds normalized text into the content gatekeeper.
5. **Database System (Persistence Actor)**:
   * MySQL 8.0 / SQLite database enforcing schema validation, foreign keys, user isolation, and indexing.
6. **Email / SMTP Relay Service (External Actor)**:
   * Google Gmail SMTP relay delivering time-limited verification OTP codes to candidate inboxes.

---

## 🏛️ System Architecture

AI JobShield is engineered as a clean, decoupled 4-tier architecture following modern software engineering principles:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PRESENTATION TIER (React 18 + Vite)                  │
│  LandingPage │ AuthPage │ Dashboard │ AnalyzePage │ OcrPage │ History  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / REST (Axios Interceptors)
┌───────────────────────────────────▼────────────────────────────────────┐
│                    API GATEWAY TIER (FastAPI ASGI)                     │
│  /api/auth  │  /api/analyze  │  /api/ocr  │  /api/history  │ /dashboard │
│  Security: Bcrypt Salt Hashing │ JWT Bearer Middleware │ CORS Handler │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Internal Service Invocation
┌───────────────────────────────────▼────────────────────────────────────┐
│                  ANALYTICAL & INTELLIGENCE ENGINES                     │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────┐ │
│  │ Tesseract OCR Service │ │ Content Gatekeeper    │ │ Company Verif │ │
│  └───────────────────────┘ └───────────────────────┘ └───────────────┘ │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────┐ │
│  │ 14-Rule Scam Engine   │ │ TF-IDF ML Classifier  │ │ 5D Trust Calc │ │
│  └───────────────────────┘ └───────────────────────┘ └───────────────┘ │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Relational Persistence & Assets
┌───────────────────────────────────▼────────────────────────────────────┐
│                       DATA & STORAGE PERSISTENCE                       │
│  MySQL 8.0 / SQLite (Users, Jobs, Analyses, OTRs, Reports, Matches)    │
│  verified_companies.json │ jobshield_model.joblib │ High-Risk TLDs     │
└────────────────────────────────────────────────────────────────────────┘
```

> For full architectural decomposition, component boundaries, and hardware topologies, see **[System Architecture Documentation](docs/architecture/system-architecture.md)** and **[Deployment Architecture](docs/uml/deployment/deployment-diagram.md)**.

---

## 💻 Technology Stack

| Layer | Technology | Version | Purpose in AI JobShield |
| :--- | :--- | :---: | :--- |
| **Frontend Framework** | React.js | 18.2.0 | Reactive Single-Page Application (SPA) user interface. |
| **Build Tooling** | Vite | 5.0.0+ | Hot Module Replacement (HMR) and optimized ES module bundling. |
| **Styling & Design** | Tailwind CSS | 3.4.0 | Responsive design system, dark-mode styling, and custom tokens. |
| **Client-Side Routing** | React Router DOM | 6.20.0 | Declarative client-side routing and protected route wrappers. |
| **Data Visualization** | Recharts | 2.10.0 | Interactive donut charts for risk distribution and scan histograms. |
| **HTTP Client** | Axios | 1.6.0 | REST communication with automatic JWT Authorization header injection. |
| **Backend Framework** | FastAPI | 0.104.1 | High-performance asynchronous Python web framework (ASGI). |
| **Application Server** | Uvicorn | 0.24.0 | Production-grade ASGI web server with worker clustering. |
| **ORM & Persistence** | SQLAlchemy | 2.0.23 | Declarative database object-relational mapping and connection pooling. |
| **Database Engine** | MySQL | 8.0 | Primary relational persistence for users, jobs, results, and OTPs. |
| **Lightweight Database** | SQLite | 3.x | Zero-configuration testing and embedded local development database. |
| **Database Driver** | PyMySQL | 1.1.0 | Pure Python MySQL client driver. |
| **Optical Character Recognition** | Tesseract OCR / pytesseract | 5.3+ / 0.3.10 | Local optical text extraction from uploaded job screenshots. |
| **Machine Learning** | Scikit-Learn | 1.3.2 | TF-IDF text vectorization and calibrated SGD Logistic Classifier. |
| **Array & Model Storage** | NumPy & Joblib | 1.26.2 / 1.3.2 | Numerical arrays and serialized `.joblib` model asset persistence. |
| **Authentication & Hash** | PyJWT & Passlib (Bcrypt) | 2.8.0 / 1.7.4 | Cryptographic password hashing and HMAC-SHA256 JWT tokens. |
| **Email Delivery** | Python smtplib / ssl | Built-in | TLS-encrypted Google Gmail SMTP communication for 6-digit OTP delivery. |
| **Validation & Schemas** | Pydantic | 2.5.2 | Strict request/response payload typing and configuration parsing. |
| **Automated Testing** | PyTest & HTTPX | 7.4.3 / 0.25.2 | Comprehensive unit, integration, and API test automation suite. |

---

## 🗄️ Database Design

The relational persistence tier maintains referential integrity, automatic cascade behaviors, and index optimizations:

| Entity / Table | Primary Key | Foreign Keys | Key Attributes & Responsibilities |
| :--- | :--- | :--- | :--- |
| **`users`** | `id` (INT) | None | `name`, `email` (UNIQUE, indexed), `password_hash`, `role`, `is_verified`, `created_at`. Enforces identity and credential storage. |
| **`email_otps`** | `id` (INT) | `user_id` $\rightarrow$ `users.id` | `otp_code`, `purpose` (`VERIFY_EMAIL`, `RESET_PASSWORD`), `expires_at`, `is_used`, `created_at`. |
| **`job_postings`** | `id` (INT) | `user_id` $\rightarrow$ `users.id` | `title`, `company_name`, `description`, `salary`, `email`, `url`, `source`, `created_at`. Raw input record. |
| **`analysis_results`** | `id` (INT) | `job_posting_id`, `user_id` | `trust_score` (0–100), `risk_level` (`LOW`, `MEDIUM`, `HIGH`), `red_flags` (JSON), `positive_indicators` (JSON), `score_breakdown` (JSON), `company_verification` (JSON), `extracted_ocr_text`, `explanation` (Markdown). |
| **`ocr_results`** | `id` (INT) | `user_id` $\rightarrow$ `users.id` | `filename`, `file_hash`, `raw_text`, `processed_text`, `confidence_score`, `created_at`. Stores OCR extraction telemetry. |
| **`companies`** | `id` (INT) | None | `name` (UNIQUE), `domain`, `is_verified`, `risk_level`, `industry`, `careers_url`, `notes`. Dynamic database enterprise registry. |
| **`scam_reports`** | `id` (INT) | `user_id` $\rightarrow$ `users.id` | `company_name`, `job_title`, `scam_type`, `description`, `contact_info`, `platform`, `evidence_url`. Community threat reporting. |
| **`feedbacks`** | `id` (INT) | `analysis_result_id`, `user_id`| `is_accurate`, `user_comment`, `corrected_risk_level`, `created_at`. User evaluation feedback loop. |
| **`duplicate_matches`** | `id` (INT) | `analysis_result_id` | `similarity_score`, `original_analysis_id`, `match_type`. Prevents redundant duplicate analyses. |

### Database Relationship Summary
* A **User** has zero-to-many **JobPostings**, **AnalysisResults**, **OcrResults**, **EmailOTPs**, and **ScamReports**.
* Each **JobPosting** corresponds to exactly one **AnalysisResult** (1:1 operational pair).
* Deleting a user or analysis result propagates via foreign key cascade rules to related feedback and duplicate entries.

> View complete relational schemas, data dictionary, indexing rules, and Mermaid ER models in **[Entity-Relationship Documentation](docs/database/er-diagram.md)**.

---

## 📐 UML Diagrams

Following standard software engineering specifications, complete UML coverage is documented and linked below:

| Diagram | Description | Documentation Link |
| :--- | :--- | :---: |
| **Use Case Diagram** | Details system actors (Candidate, Admin, OCR, SMTP) and all 15 discrete system use cases. | **[View Use Case Diagram](docs/uml/use-case/use-case-diagram.md)** |
| **Class Diagram** | Visualizes domain entities, Pydantic schemas, and analytical service classes with method signatures. | **[View Class Diagram](docs/uml/class/class-diagram.md)** |
| **Sequence Diagrams** | Step-by-step sequence traces for User Registration & OTP, Login, Manual Analysis, and OCR Analysis. | **[View Sequence Diagrams](docs/uml/sequence/sequence-diagrams.md)** |
| **Communication Diagram** | Component collaboration and message numbering across Presentation, Gateway, Engine, and DB tiers. | **[View Communication Diagram](docs/uml/communication/communication-diagram.md)** |
| **Activity Diagram** | Complete decision logic workflow from job ingestion through OCR gate, scoring, caps, and persistence. | **[View Activity Diagram](docs/uml/activity/activity-diagram.md)** |
| **State Diagram** | Finite state machine modeling user account lifecycle and analysis risk state transitions. | **[View State Diagram](docs/uml/state/state-diagram.md)** |
| **Component Diagram** | Structural wiring of backend modules, external Tesseract binaries, SMTP relays, and databases. | **[View Component Diagram](docs/uml/component/component-diagram.md)** |
| **Deployment Diagram** | Execution architecture across client browsers, FastAPI ASGI servers, local Tesseract, and MySQL. | **[View Deployment Diagram](docs/uml/deployment/deployment-diagram.md)** |

---

## 🔄 Data Flow Diagrams (DFD)

Structured functional data flow models depict system boundaries, major transformational processes, and data repositories:

| Level | Scope & Description | Documentation Link |
| :--- | :--- | :---: |
| **Context Level DFD (Level 0)** | Defines the overall system boundary, external entities (Job Seeker, Admin, Gmail SMTP, Tesseract OCR), and primary data flows. | **[View Context DFD](docs/dfd/dfd-diagrams.md#context-level-dfd-level-0)** |
| **Level-1 DFD** | Decomposes AI JobShield into 7 core processes (Authentication, OCR Ingestion, Company Verification, Rule Detection, ML Inference, Scoring, History Management) and 5 data stores. | **[View Level-1 DFD](docs/dfd/dfd-diagrams.md#level-1-dfd-major-system-processes)** |
| **Level-2 DFD (Job Analysis)** | Deep-dive decomposition of Process 4.0 (*Job Analysis & Risk Evaluation*), detailing data normalization, rule checking, ML scoring, safety capping, and explanation synthesis. | **[View Level-2 DFD](docs/dfd/dfd-diagrams.md#level-2-dfd-process-40-job-analysis--risk-evaluation)** |

---

## 🔁 Application Workflow

The end-to-end execution workflow transitions a candidate from ingestion to transparent security insight:

```
[User Visits AI JobShield]
         │
         ▼
[Registration / Login] ──(Requires OTP)──> [Gmail SMTP dispatches 6-digit OTP]
         │ (JWT Issued)
         ▼
[User Dashboard Workspace]
         │
         ├──► [Method A: Manual Parameter Entry] ──────────┐
         │                                                 │
         └──► [Method B: Upload Screenshot]                │
                     │                                     │
                     ▼                                     │
              [Tesseract OCR Engine]                       │
                     │                                     │
                     ▼                                     │
              [Content Gatekeeper]                         │
                     │ (Pass: Job-related text)            │
                     ▼                                     ▼
         ┌────────────────────────────────────────────────────────┐
         │             CORE 5-DIMENSIONAL ANALYSIS                │
         │  1. Company Verification (Domain & Registry match)     │
         │  2. URL / Source Analysis (HTTPS, shortener check)     │
         │  3. Job Description Quality (Length, clarity)          │
         │  4. Deterministic Red Flag Detection (14 rules)        │
         │  5. Machine Learning Scam Inference (TF-IDF + SGD)     │
         │  6. Contact Consistency (Recruiter email vs domain)    │
         └──────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
         [Enforce Evidence-Based Safety Caps (Impersonation / Fees)]
                                    │
                                    ▼
         [Generate Natural Language Explanation & Direct Quotes]
                                    │
                                    ▼
         [Persist Record to Database (job_postings & analysis_results)]
                                    │
                                    ▼
         [Display ResultPage: SVG Gauge, 5D Cards & Action Advice]
                                    │
                                    ▼
         [Archived in Paginated User Scan History (Isolated per User)]
```

> For exhaustive step-by-step descriptions and edge case workflows, refer to the **[Application Workflow Specification](docs/architecture/application-workflow.md)**.

---

## 🔒 Authentication & Security

AI JobShield implements comprehensive multi-layer defensive security controls:

* **Password Protection**: Passwords are cryptographically salted and hashed using **Bcrypt** (`passlib[bcrypt]`), guaranteeing resistance against dictionary and rainbow table attacks.
* **Email Verification (OTP)**: Registration generates a 6-digit numeric OTP with a strict **10-minute expiry window** and single-use flag. Unverified accounts cannot authenticate or access analytical endpoints.
* **Stateless JWT Tokens**: Authenticated sessions utilize HMAC-SHA256 signed JSON Web Tokens (`PyJWT`) with a 24-hour expiration time (`exp`) and subject claim (`sub=user_id`).
* **Strict User Isolation**: Every database query for history, individual scan details, or deletion enforces `filter(AnalysisResult.user_id == current_user.id)`. Requests targeting another user's scan immediately return `403 Forbidden` or `404 Not Found`.
* **Zero Secret Commitment**: All secrets (JWT keys, database passwords, SMTP credentials) are managed strictly via environment variables loaded via Pydantic `BaseSettings`. No secrets exist in version control.
* **Anti-Abuse Rate-Limiting**: Verification and OTP dispatch endpoints enforce sliding-window cooldowns (minimum 60 seconds between resends) to mitigate mail relay abuse.

---

## 👁️ OCR Processing Pipeline

The Optical Character Recognition subsystem allows candidates to scan recruitment flyers, email screenshots, WhatsApp forwards, and mobile job boards:

```
┌─────────────────┐     ┌───────────────┐     ┌───────────────────────┐
│ Upload Image    │ ──> │ Tesseract OCR │ ──> │ Job Content Validator │
│ (PNG/JPG ≤5 MB) │     │ Engine        │     │ (Gatekeeper)          │
└─────────────────┘     └───────────────┘     └───────────────────────┘
                                                           │
                                          ┌────────────────┴───────────────┐
                                          ▼                                ▼
                                   [Not Job Related]              [Valid Job Posting]
                                   HTTP 422 Rejection             Proceed to 5D Engine
```

1. **Payload Preprocessing**: Incoming files are validated for supported MIME types (`image/png`, `image/jpeg`, `image/webp`) and capped at a maximum of 5 MB.
2. **Text Extraction (`ocr_service.py`)**: Tesseract OCR extracts character streams, line structures, and raw text confidence values.
3. **Relevance Gatekeeper (`job_content_validator.py`)**: Before invoking analytical engines, the extracted text is checked against recruitment vocabulary (roles, salaries, requirements) versus anti-signals (grocery receipts, memes, source code, medical prescriptions). Irrelevant images are gracefully rejected with a helpful prompt, preventing database clutter.
4. **Historical Archival**: The extracted text is archived directly in `analysis_results.extracted_ocr_text` for complete historical auditability.

---

## 🤖 AI / Machine Learning Analysis

AI JobShield employs a calibrated, deterministic Natural Language Processing pipeline:

* **Dataset & Training**: Pre-trained on 400 labeled recruitment text samples representing legitimate enterprise postings and verified fraud patterns (task scams, fee requests, phishing).
* **Text Preprocessing & Vectorization**: Uses Scikit-Learn `TfidfVectorizer` (sublinear TF scaling, English stop-word removal, 1-to-2 n-gram tokenization).
* **Classifier Model**: Calibrated `SGDClassifier` configured with log-loss (Logistic Regression) generating statistical scam probability $P(\text{scam})$.
* **Influential Feature Extraction**: Inspects model coefficients to highlight high-weight fraud signals (e.g., *"registration"*, *"deposit"*, *"telegram"*, *"urgently"*, *"daily income"*).
* **Hybrid Scoring Integration**: To prevent ML hallucinations or edge-case false positives, the ML prediction is strictly blended with deterministic heuristic checks:
  $$\text{Scam Dimension} = 0.70 \times \text{Rule Penalty Score} + 0.30 \times (1 - P(\text{scam})) \times 100$$
* **Honest Scope Disclaimer**: The system does **not** rely on slow, ungrounded Large Language Models (LLMs) or commercial generative APIs; it is built on deterministic cybersecurity heuristics and statistical machine learning designed for predictable, explainable outcomes.

---

## ⚖️ Credibility & Risk Scoring Methodology

AI JobShield replaces arbitrary binary verdicts with a transparent **5-Dimensional Weighted Scoring Engine**:

$$\text{Raw Trust Score} = 0.25 \times S_{\text{company}} + 0.20 \times S_{\text{source}} + 0.15 \times S_{\text{quality}} + 0.30 \times S_{\text{scam}} + 0.10 \times S_{\text{contact}}$$

| Dimension | Weight | Evaluation Criteria |
| :--- | :---: | :--- |
| **1. Company Verification** | **25%** | Cross-references company against `data/verified_companies.json` and database registries. Checks domain alignment and past reputation. |
| **2. Source / URL Credibility** | **20%** | Validates HTTPS protocol, checks for URL shorteners, punycode attacks, raw IP addresses, and brand-domain mismatch. |
| **3. Job Posting Quality** | **15%** | Evaluates description length (>80 chars), clarity of responsibilities, stated qualifications, and realistic compensation terms. |
| **4. Scam & Red Flag Detection** | **30%** | Deterministic detection of upfront fees, equipment charges, crypto payments, sensitive ID harvesting, and WhatsApp-only channels. |
| **5. Contact & Domain Consistency** | **10%** | Verifies official corporate domain alignment (`@infosys.com`) versus personal/free email services (`@gmail.com`). |

### Hard Security Caps & Guardrails
To prevent positive traits (e.g., long description or good grammar) from masking dangerous scam signals, the system enforces **evidence-based hard caps**:

```
                              ┌───────────────────────────────────────────────┐
                              │            Raw Trust Score (0-100)            │
                              └──────────────────────┬────────────────────────┘
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │ Does Impersonation Trigger?  │──Yes──► Cap at ≤ 25 (HIGH RISK)
                                      └──────────────┬───────────────┘
                                                     │ No
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │ Does Critical Scam Trigger?  │──Yes──► Cap at ≤ 35 (HIGH RISK)
                                      └──────────────┬───────────────┘
                                                     │ No
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │ Is Company Unverified?       │──Yes──► Cap at ≤ 65 (MEDIUM RISK)
                                      └──────────────┬───────────────┘
                                                     │ No
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │ Is Company Partially Known?  │──Yes──► Cap at ≤ 75 (MEDIUM RISK)
                                      └──────────────┬───────────────┘
                                                     │ No
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │  Final Trust Score Applied   │
                                      └──────────────────────────────┘
```

* 🟢 **LOW RISK (80 – 100)**: Legitimate company, verified official domain, professional email, zero scam indicators.
* 🟡 **MEDIUM RISK (50 – 79)**: Unverified startup, partial contact details, missing corporate website; requires candidate diligence.
* 🔴 **HIGH RISK (0 – 49)**: Brand impersonation, upfront fee requests, equipment deposits, or sensitive ID harvesting detected.

---

## 🚩 Scam & Red Flag Detection Engine

AI JobShield incorporates 14 deterministic rule indicators with calibrated severity points:

| Indicator Code | Severity Level | Deduction | Targeted Signals & Keywords |
| :--- | :---: | :---: | :--- |
| **`fee_request`** | **Critical** | 35 pts | *"registration fee"*, *"application fee"*, *"training fee"*, *"security deposit"*, *"pay to join"* |
| **`money_transfer`** | **Critical** | 35 pts | *"gift card"*, *"western union"*, *"crypto"*, *"bitcoin"*, *"upi transfer"*, *"send money"* |
| **`equipment_purchase`** | **Critical** | 35 pts | *"purchase laptop"*, *"buy equipment"*, *"laptop deposit"*, *"home office kit fee"* |
| **`company_impersonation`** | **Critical** | 35 pts | Claimed enterprise entity paired with free public webmail (`@gmail.com`, `@yahoo.com`) |
| **`sensitive_info`** | **Critical** | 30 pts | Solicits Aadhaar, PAN card, passport scan, bank account number, or OTP before interview |
| **`unrealistic_salary`** | **High** | 20 pts | Daily earnings exceeding ₹2,000/day or entry-level salary exceeding ₹80,000/month |
| **`suspicious_contact`** | **High** | 15 pts | *"WhatsApp only"*, *"Telegram only"*, *"contact on Telegram"*, no formal corporate channel |
| **`email_domain_mismatch`** | **High** | 15 pts | Recruiter email domain shares zero naming tokens with claimed company entity |
| **`free_email`** | **Medium** | 12 pts | Recruiter uses free webmail provider for official corporate hiring |
| **`no_interview`** | **Medium** | 12 pts | *"No interview needed"*, *"direct selection"*, *"instant joining"*, *"guaranteed placement"* |
| **`urgency`** | **Medium** | 10 pts | *"Within 24 hours"*, *"limited seats"*, *"hurry up"*, *"apply now or offer expires"* |
| **`vague_description`** | **Medium** | 10 pts | Text under 80 characters, missing job duties, or lacking minimum qualifications |
| **`suspicious_url`** | **Medium** | 12 pts | Uses URL shorteners (bit.ly), punycode domains, or high-risk top-level domains (.tk, .xyz) |
| **`caps_exclaim`** | **Low** | 5 pts | Excessive uppercase letters (>35% text) or multiple consecutive exclamation marks (≥4) |

---

## 📡 REST API Documentation

All secured endpoints require the HTTP header: `Authorization: Bearer <JWT_TOKEN>`.

### Authentication Endpoints
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Registers account, hashes password, dispatches 6-digit email OTP. | No |
| `POST` | `/api/auth/verify-email` | Validates 6-digit OTP, verifies account, returns JWT bearer token. | No |
| `POST` | `/api/auth/login` | Validates credentials, verifies OTP status, returns JWT bearer token. | No |
| `POST` | `/api/auth/resend-otp` | Re-dispatches a fresh verification OTP with 60-second rate-limiting. | No |
| `POST` | `/api/auth/forgot-password`| Sends a 6-digit password reset OTP to registered user email. | No |
| `POST` | `/api/auth/reset-password` | Verifies reset OTP code and updates user password hash. | No |
| `GET` | `/api/auth/me` | Returns authenticated user profile (`id`, `name`, `email`, `role`, `is_verified`).| **Yes** |

### Core Job Analysis & OCR Endpoints
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/analyze` | Executes 5D analysis on structured job parameters and commits to DB. | **Yes** |
| `POST` | `/api/ocr/analyze` | Ingests image (`PNG/JPG`), runs Tesseract OCR, validates gate, and saves to DB. | **Yes** |

### History & Workspace Endpoints
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/history` | Fetches paginated, user-scoped scan history (`page`, `limit`, `risk_level`). | **Yes** |
| `GET` | `/api/history/{id}` | Retrieves full 5-dimension breakdown and explanation for a specific scan. | **Yes** |
| `DELETE`| `/api/history/{id}` | Permanently deletes an analysis record belonging to the authenticated user. | **Yes** |
| `GET` | `/api/dashboard` | Returns real-time platform statistics, risk distributions, and 14-day history. | **Yes** |
| `POST` | `/api/company/verify` | Standalone endpoint for company verification and email domain matching. | **Yes** |
| `POST` | `/api/url/analyze` | Standalone endpoint for local URL heuristic and protocol evaluation. | **Yes** |
| `POST` | `/api/reports` | Submits a community recruitment scam incident report. | **Yes** |
| `POST` | `/api/feedback` | Submits user accuracy feedback and ratings on a specific analysis result. | **Yes** |

> Complete request/response schemas, JSON payloads, and status codes are documented in **[REST API Documentation](docs/api/api-documentation.md)**.

---

## 📂 Project Structure

```
AI-JobShield/
├── backend/                                # FastAPI backend root
│   ├── app/
│   │   ├── main.py                         # Application factory, middleware & CORS configuration
│   │   ├── config.py                       # Pydantic BaseSettings environment loader
│   │   ├── database.py                     # SQLAlchemy engine, session maker & schema handling
│   │   ├── models.py                       # SQLAlchemy ORM entity models
│   │   ├── schemas.py                      # Pydantic request/response payload schemas
│   │   ├── deps.py                         # FastApi dependencies: DbSession & CurrentUser
│   │   ├── routers/                        # REST API routing modules
│   │   │   ├── auth.py                     # Register, Login, Verify Email OTP, Forgot Password
│   │   │   ├── analyze.py                  # Job analysis coordination & persistence
│   │   │   ├── ocr.py                      # Image OCR ingestion & gatekeeper validation
│   │   │   ├── history.py                  # User-scoped history CRUD & record deletion
│   │   │   ├── dashboard.py                # Statistical aggregations & 14-day history
│   │   │   ├── company.py                  # Company registry lookup & domain matching
│   │   │   ├── url.py                      # URL security heuristic evaluation
│   │   │   ├── reports.py                  # Community scam reporting
│   │   │   └── feedback.py                 # Prediction accuracy feedback
│   │   └── services/                       # Core analytical & business logic
│   │       ├── analyzer.py                 # 5D analysis orchestrator
│   │       ├── company_verifier.py         # Evidence-based enterprise verification
│   │       ├── rules.py                    # 14 deterministic red-flag pattern rules
│   │       ├── scoring.py                  # 5-dimensional weighted scoring & safety caps
│   │       ├── explain.py                  # Structured markdown rationale builder
│   │       ├── ml_service.py               # Scikit-Learn TF-IDF model inference
│   │       ├── ocr_service.py              # Tesseract OCR engine integration
│   │       ├── job_content_validator.py    # Pre-analysis OCR job relevance gatekeeper
│   │       ├── url_analyzer.py             # URL security & domain heuristics
│   │       ├── duplicate.py                # Duplicate job posting detection
│   │       └── email_service.py            # Gmail SMTP OTP delivery with console fallback
│   ├── requirements.txt                    # Backend Python dependencies
│   └── seed.py                             # Database seeder (50 users, 12 companies, 14 analyses)
│
├── frontend/                               # React 18 Single-Page Application root
│   ├── src/
│   │   ├── main.jsx                        # React DOM mounting & provider wrappers
│   │   ├── App.jsx                         # Route definitions & protected route guards
│   │   ├── api/
│   │   │   └── client.js                   # Axios HTTP client with JWT interceptors
│   │   ├── components/                     # Modular reusable UI components
│   │   │   ├── Navbar.jsx                  # Header navigation with profile link & auth state
│   │   │   ├── TrustGauge.jsx              # Interactive SVG trust gauge
│   │   │   ├── AnalysisResultView.jsx      # 5D cards, red flags, stored details, OCR viewer
│   │   │   ├── FeedbackWidget.jsx          # Accuracy feedback submission
│   │   │   └── ProtectedRoute.jsx          # Authorization guard for authenticated routes
│   │   ├── context/
│   │   │   └── AuthContext.jsx             # Authentication context & session persistence
│   │   ├── pages/                          # Primary view components
│   │   │   ├── Landing.jsx                 # Public marketing landing page
│   │   │   ├── AuthPage.jsx                # Sign in, Sign up & Email OTP verification
│   │   │   ├── Dashboard.jsx               # Security KPIs, charts & recent scan feed
│   │   │   ├── AnalyzePage.jsx             # Manual job posting analysis input form
│   │   │   ├── OcrPage.jsx                 # Image upload & Tesseract OCR scanning
│   │   │   ├── ResultPage.jsx              # Full analysis view (reloaded from database)
│   │   │   ├── HistoryPage.jsx             # Paginated user scan history with deletion
│   │   │   ├── ProfilePage.jsx             # User profile, verification badge & metrics
│   │   │   ├── CompanyPage.jsx             # Standalone company verification lookup
│   │   │   ├── UrlPage.jsx                 # Standalone URL security inspector
│   │   │   └── ReportsPage.jsx             # Community scam incident reporting
│   │   └── utils/
│   │       └── helpers.js                  # Risk badge styling & sample job loaders
│   ├── package.json                        # Frontend dependencies & scripts
│   └── vite.config.js                      # Vite bundler & development proxy config
│
├── data/                                   # Curated knowledge datasets
│   ├── verified_companies.json             # Recognized enterprise registry & official domains
│   ├── free_email_domains.json             # Public webmail provider list
│   └── suspicious_tlds.json                # High-risk top-level domains
│
├── docs/                                   # Academic & Software Engineering Documentation
│   ├── SRS.md                              # IEEE 830 Software Requirements Specification
│   ├── requirements-traceability-matrix.md # Requirement to Feature to Code to Test mapping
│   ├── uml/                                # Complete UML documentation suite
│   │   ├── use-case/use-case-diagram.md    # System actors & 15 use cases
│   │   ├── class/class-diagram.md          # Domain models, schemas & service classes
│   │   ├── sequence/sequence-diagrams.md   # Step-by-step sequence traces
│   │   ├── communication/communication-diagram.md # Numbered message collaboration
│   │   ├── activity/activity-diagram.md    # Job analysis decision & scoring activity
│   │   ├── state/state-diagram.md          # Account & analysis risk lifecycle states
│   │   ├── component/component-diagram.md  # Software component wiring
│   │   └── deployment/deployment-diagram.md# Runtime deployment topology
│   ├── dfd/
│   │   └── dfd-diagrams.md                 # Context-Level, Level-1 & Level-2 DFD models
│   ├── database/
│   │   └── er-diagram.md                   # Entity-Relationship diagram & data dictionary
│   ├── architecture/
│   │   ├── system-architecture.md          # 4-tier architectural specification
│   │   └── application-workflow.md         # Detailed end-to-end user workflow
│   ├── api/
│   │   └── api-documentation.md            # REST API endpoint reference & schemas
│   ├── testing/
│   │   └── test-cases.md                   # 50 comprehensive manual & automated test cases
│   └── screenshots/
│       └── README.md                       # UI screenshot showcase & tour
│
├── models/                                 # Serialized machine learning assets
│   ├── jobshield_model.joblib              # Pre-trained TF-IDF + SGDClassifier model
│   └── confusion_matrix.png                # Model evaluation performance chart
│
├── tests/                                  # Automated PyTest test suite
│   ├── test_api.py                         # Authentication & core API endpoint tests
│   ├── test_history_and_scoring.py         # History persistence, isolation & Cases A–F
│   ├── test_job_content_validator.py       # OCR gatekeeper validation unit tests
│   └── test_ocr_job_gate_api.py            # OCR endpoint integration tests
│
├── .env.example                            # Safe environment variable template (no secrets)
├── .gitignore                              # Git exclusion rules
├── LICENSE                                 # MIT License
├── README.md                               # Master project documentation
└── requirements.txt                        # Root Python dependencies manifest
```

---

## 🚀 Installation & Setup

### Prerequisites
* **Python**: v3.10, v3.11, or v3.12 (recommended)
* **Node.js**: v18.0 or higher & **npm** v9.0+
* **MySQL**: v8.0 or higher (or use embedded SQLite with zero setup)
* **Tesseract OCR**: Required for OCR screenshot extraction:
  * **Windows**: Download installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and install to `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  * **Linux (Ubuntu/Debian)**: `sudo apt-get install -y tesseract-ocr`
  * **macOS**: `brew install tesseract`

---

### Step 1: Clone Repository
```bash
git clone https://github.com/ChukkaKusuma-24/AI-JobShield.git
cd AI-JobShield
```

---

### Step 2: Configure Environment Variables
Create your local `.env` file from the provided template:
```bash
# Windows PowerShell
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Choose MySQL or SQLite:
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/ai_jobshield
# Or SQLite: DATABASE_URL=sqlite:///./database/jobshield.db

# Gmail SMTP for real OTP delivery:
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_CONSOLE_FALLBACK=false

# Tesseract executable path:
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

### Step 3: Backend Setup & Seed Database
```bash
# Create Python virtual environment
python -m venv backend/venv

# Activate virtual environment
# Windows:
backend\venv\Scripts\activate
# Linux/macOS:
# source backend/venv/bin/activate

# Install backend dependencies (from repository root or backend directory)
pip install -r requirements.txt

# Seed database (creates 50 demo users, 12 companies, 14 analytical scans)
python backend/seed.py

# Launch FastAPI ASGI server
cd backend
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger documentation will be available at: **`http://localhost:8000/docs`**

---

### Step 4: Frontend Setup
Open a separate terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Open **`http://localhost:5173`** in your browser to launch the AI JobShield web application.

---

## ⚙️ Environment Variables

> [!CAUTION]
> Never commit real secrets, private keys, or passwords to version control. The repository includes `.env.example` as a safe template.

| Variable Name | Purpose / Description | Safe Sample / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy connection URI (MySQL or SQLite) | `mysql+pymysql://root:root@localhost:3306/ai_jobshield` |
| `SECRET_KEY` | Application session signing key | `secure-random-cryptographic-string` |
| `JWT_SECRET` | HMAC-SHA256 signature key for JWT tokens | `jwt-random-cryptographic-key` |
| `JWT_ALGORITHM` | Cryptographic JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Bearer token lifetime in minutes | `1440` (24 hours) |
| `SMTP_HOST` | Outgoing SMTP mail relay host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP communication port | `587` |
| `SMTP_USER` | Email address sending verification OTPs | `recruitment.shield@gmail.com` |
| `SMTP_PASSWORD` | 16-character Google App Password | `xxxx xxxx xxxx xxxx` |
| `SMTP_CONSOLE_FALLBACK` | Print OTP to terminal if SMTP is unconfigured | `false` (set `true` for local tests) |
| `TESSERACT_CMD` | Binary path to local Tesseract OCR | `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `VITE_API_BASE` | Frontend target URL for backend API | `http://127.0.0.1:8000/api` |

---

## 👥 Demo & Seed Accounts

When running `python backend/seed.py`, the database is populated with realistic test records for immediate evaluation:

| Account Type | Email Address | Password | Account Status | Intended Usage |
| :--- | :--- | :--- | :---: | :--- |
| **Demo Candidate** | `demo@jobshield.local` | `demo1234` | **Verified** | Standard user testing: scan jobs, review history, profile. |
| **Security Admin** | `admin@jobshield.local` | `admin1234` | **Verified** | Administrative inspection, company registry, telemetry. |
| **Unverified User 1**| `pending1@jobshield.local`| `pass1234` | **Unverified** | Testing email OTP verification flow (OTP: `123456`). |
| **Unverified User 2**| `pending2@jobshield.local`| `pass1234` | **Unverified** | Testing email OTP verification flow (OTP: `123456`). |

* **Total Seed Users**: 50 accounts (40 pre-verified, 10 pending verification).
* **Pre-Seeded Companies**: 12 enterprise records (Infosys, TCS, Google, Amazon, Wipro, etc.).
* **Pre-Seeded Analyses**: 14 analytical records spanning 14 days to provide immediate data for the dashboard chart and scan history table.

---

## 🧪 Automated Testing Suite

AI JobShield includes automated tests executed using PyTest across isolated SQLite and MySQL fixtures:

```bash
# Run the automated test suite
backend\venv\Scripts\python.exe -m pytest tests -v
```

```
============================== test session starts ==============================
platform win32 -- Python 3.13.1, pytest-7.4.3
collected 11 items

tests/test_api.py::test_auth_and_health PASSED                            [  9%]
tests/test_history_and_scoring.py::test_history_lifecycle_and_isolation PASSED [ 18%]
tests/test_history_and_scoring.py::test_case_a_legit_infosys PASSED       [ 27%]
tests/test_history_and_scoring.py::test_case_b_unknown_company PASSED     [ 36%]
tests/test_history_and_scoring.py::test_case_c_registration_fee PASSED   [ 45%]
tests/test_history_and_scoring.py::test_case_d_infosys_impersonation PASSED [ 54%]
tests/test_history_and_scoring.py::test_case_e_infosys_laptop_deposit PASSED [ 63%]
tests/test_history_and_scoring.py::test_case_f_legit_wipro_missing_evidence PASSED [ 72%]
tests/test_job_content_validator.py::test_valid_job_postings PASSED       [ 81%]
tests/test_job_content_validator.py::test_invalid_non_job_text PASSED     [ 90%]
tests/test_ocr_job_gate_api.py::test_ocr_gatekeeper_api PASSED           [100%]

============================== 11 passed in 36.21s ==============================
```

### Verified Scoring Test Matrix
1. **Case A (Verified Brand + Legitimate Details)**:
   * Entity: `Infosys` | Recruiter Email: `careers@infosys.com`
   * **Verdict**: `VERIFIED` | Trust Score: **96/100 (LOW RISK)**.
2. **Case B (Unknown Company + Standard Job Details)**:
   * Entity: `Krypton Web Solutions` | Email: `hiring@kryptonwebsolutions.io`
   * **Verdict**: `UNVERIFIED` | Trust Score: **60/100 (MEDIUM RISK)** (Evidence cap $\le 65$ applied).
3. **Case C (Unknown Company + Fee Solicitation)**:
   * Solicits ₹1,499 registration fee via WhatsApp.
   * **Verdict**: `HIGH RISK / LIKELY SCAM` | Trust Score: **18/100** (Critical fee cap $\le 35$ applied).
4. **Case D (Known Brand + Free Webmail Impersonation)**:
   * Entity: `Infosys` | Recruiter Email: `infosys.campus.recruiter@gmail.com`
   * **Verdict**: `IMPERSONATION_RISK` | Trust Score: **18/100 (HIGH RISK)** (Impersonation cap $\le 25$ applied).
5. **Case E (Known Brand + Laptop Security Deposit)**:
   * Entity: `Infosys` | Description demands ₹5,000 equipment deposit.
   * **Verdict**: `HIGH RISK` | Trust Score: **34/100** (Fee cap $\le 35$ applied; brand name cannot override fee flag).
6. **Case F (Legitimate Brand + Incomplete Evidence)**:
   * Entity: `Wipro` | Missing careers URL and official recruiter email.
   * **Verdict**: `PARTIALLY VERIFIED` | Trust Score: **68/100 (MEDIUM RISK)** (Partial evidence cap $\le 75$ applied).

> View the complete 50-test-case validation suite covering authentication, OCR, scoring, and UI flows in **[Test Cases Documentation](docs/testing/test-cases.md)**.

---

## 📸 UI Screenshots

Visual walkthroughs and interface screenshots are organized in **[UI Showcase Documentation](docs/screenshots/README.md)**:

* 📊 **Executive Security Dashboard**: Live scan counter, Recharts risk distribution charts, and recent activity table.
* 🔎 **Manual Analysis Workspace**: Comprehensive input form with pre-loaded legit and scam demo presets.
* 📷 **OCR Screenshot Scanner**: Drag-and-drop file uploader, real-time OCR extraction, and gatekeeper rejection notices.
* 🛡️ **Credibility Result View**: Dynamic SVG Trust Gauge, 5-dimension score breakdown, direct quote evidence cards, and expandable raw OCR viewer.
* 📜 **User Scan History**: Filterable, paginated scan records with isolated user deletion controls.
* 👤 **User Profile & Security Page**: Identity verification status, registration date, aggregate risk breakdown, and platform security standards.

---

## 🔮 Future Enhancements

* 🌐 **Browser Extension (Manifest V3)**: Real-time overlay directly analyzing job listings on LinkedIn, Indeed, and Internshala with single-click scoring.
* 🤖 **Multi-Modal Vision Analysis**: Integrate lightweight local vision models to inspect corporate letterhead authenticity, manipulated offer letters, and forged stamps.
* 📱 **Cross-Platform Mobile App**: React Native / Flutter client enabling direct camera scanning of physical recruitment newspaper clippings and campus posters.
* 🤝 **Decentralized Threat Consensus**: Peer-reviewed candidate scam reports integrated with automated registrar abuse reporting to take down fraudulent recruitment domains.

---

## 👤 License & Author

* **Author**: Chukka Kusuma
* **GitHub**: [@ChukkaKusuma-24](https://github.com/ChukkaKusuma-24)
* **Repository**: [https://github.com/ChukkaKusuma-24/AI-JobShield.git](https://github.com/ChukkaKusuma-24/AI-JobShield.git)
* **License**: This project is open-source under the [MIT License](LICENSE).

<div align="center">
  <sub>AI JobShield — Intelligent Recruitment Scam Detection & Credibility Analysis Platform. Built for candidate safety.</sub>
</div>
