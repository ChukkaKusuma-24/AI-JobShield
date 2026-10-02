# Software Requirements Specification (SRS)
## AI JobShield — Intelligent Recruitment Scam Detection & Credibility Analysis Platform

> **Standard:** IEEE Std 830-1998 Compliant  
> **Course:** Software Engineering / B.Tech Computer Science & Engineering  
> **Repository:** https://github.com/ChukkaKusuma-24/AI-JobShield.git  
> **Author:** ChukkaKusuma-24  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) document details the complete functional and non-functional requirements for **AI JobShield** — an intelligent recruitment fraud detection and job opportunity credibility analysis system. It establishes the technical baseline for developers, evaluators, and system stakeholders.

### 1.2 Problem Statement
Online job search platforms, social media recruiting channels, and messaging applications have seen a surge in fraudulent job postings, recruitment phishing, fake internship scams, and financial extortion. Fraudsters impersonate well-known enterprises (e.g. TCS, Infosys, Wipro, Google) using free webmail addresses (`@gmail.com`), demand upfront registration fees under the guise of training or laptop security deposits, and harvest sensitive identity documents (Aadhaar, PAN, banking credentials). Job seekers lack transparent, explainable tools to verify posting authenticity before parting with money or confidential data.

### 1.3 Objectives
* Develop a multi-tiered security platform that evaluates job opportunity credibility using evidence-based scoring rather than opaque black-box assertions.
* Prevent account abuse through cryptographically secure Email One-Time Password (OTP) verification and JWT stateless authentication.
* Ingest job postings via manual text input or screenshot upload with Optical Character Recognition (OCR) and an automated relevance gatekeeper.
* Cross-check claimed employer entities against curated enterprise registries to expose brand impersonation and contact channel mismatches.
* Combine deterministic heuristic rules with a trained Scikit-Learn machine learning classifier to detect deceptive linguistic cues and upfront monetary demands.
* Generate human-readable, structured explanations detailing verifiable evidence, positive legitimacy indicators, and actionable safety guidance.
* Provide isolated, persistent historical tracking and dashboard analytics for individual candidates.

### 1.4 Scope
AI JobShield operates as a full-stack web application comprising a React 18 single-page frontend, a FastAPI asynchronous backend, a local Tesseract OCR engine, a Scikit-Learn linear classification model, and a relational MySQL/SQLite database. The system provides decision-support risk analysis; it does not claim legal certainty or replace institutional background verification.

---

## 2. Overall Description

### 2.1 Product Perspective
AI JobShield is an independent, self-contained recruitment verification platform designed to bridge the trust gap between job candidates and online job boards. It interfaces with local OCR binaries and standard SMTP mail servers without requiring proprietary external cloud API subscriptions.

### 2.2 System Users & Actors
1. **Job Seeker / Candidate**: The primary end-user who registers, verifies their email, scans job postings or chat transcripts, reviews credibility scores, and manages their historical analyses.
2. **Security Administrator**: System administrator who monitors aggregated threat telemetry, reviews community-submitted scam reports, and maintains the verified enterprise registry.
3. **Unauthenticated Visitor (Guest)**: Prospective user accessing educational resources and registration flows.
4. **Tesseract OCR Engine**: Local subsystem performing optical character recognition on uploaded imagery.
5. **Email / SMTP Relay**: Communication subsystem delivering 6-digit verification codes.
6. **Relational Database**: Relational storage engine enforcing data integrity, foreign keys, and multi-tenant isolation.

### 2.3 Operating Environment
* **Server OS**: Windows 10/11, Ubuntu 20.04+ LTS, macOS 12+.
* **Runtime**: Python 3.10 to 3.13, Node.js 18+.
* **Database**: MySQL 8.0+ (production) or SQLite 3 (testing/local execution).
* **Client Browser**: Modern evergreen browsers (Chrome 100+, Firefox 100+, Edge 100+, Safari 15+).

### 2.4 Design & Implementation Constraints
1. **Zero Secret Exposure**: Production passwords, SMTP app credentials, and JWT secret keys must never be committed to source control; all sensitive configuration must load via environment variables (`.env`).
2. **Offline-First Resilience**: All heuristic engines, ML models, and company verification lookups must execute locally without failing when external internet connectivity is absent.
3. **Deterministic Safety Caps**: Critical scam indicators (such as upfront payment requests or corporate impersonation) must strictly cap the Trust Score, ensuring that positive signals cannot mask fatal security risks.

### 2.5 Assumptions & Dependencies
* The host environment has a working Tesseract OCR binary installed or configured via `TESSERACT_CMD`.
* For real email delivery, valid SMTP host credentials are provided in `.env`; otherwise, the system activates console logging fallback for development.

---

## 3. Functional Requirements

### 3.1 User Authentication & Account Management
* **FR-01: User Registration**: The system shall accept user registration with name, email, and password. Passwords must be at least 8 characters long and contain both letters and digits or special characters.
* **FR-02: Password Hashing**: The system shall store all user passwords as salted Bcrypt hashes. Plaintext passwords must never be logged or persisted.
* **FR-03: Email OTP Verification**: The system shall generate a cryptographically random 6-digit numeric OTP upon registration, store its SHA-256 hash with a 15-minute expiration, and dispatch it via SMTP.
* **FR-04: Account Verification Gate**: The system shall prevent unverified user accounts from authenticating or accessing protected endpoints until the correct 6-digit OTP is verified.
* **FR-05: JWT Session Management**: Upon successful authentication, the system shall issue an HMAC-SHA256 signed JSON Web Token (JWT) with configured expiration (24 hours).
* **FR-06: Password Recovery**: The system shall allow users to request a password reset OTP and update their password securely without exposing administrative backdoors.

### 3.2 Job Opportunity Ingestion & OCR
* **FR-07: Manual Job Ingestion**: The system shall accept manual entry of Job Title, Company Name, Job Description (minimum 30 characters), Salary, Contact Email, Destination URL, Location, and Job Type.
* **FR-08: Screenshot Ingestion**: The system shall accept image uploads in PNG, JPG, JPEG, and WEBP formats up to 5 MB in size.
* **FR-09: OCR Processing**: The system shall preprocess images (grayscale conversion, adaptive resizing, point-contrast enhancement) and extract text and word-level confidence using Tesseract OCR.
* **FR-10: Relevance Gatekeeper**: The system shall evaluate extracted OCR text against weighted job recruitment vocabulary and anti-patterns. Non-job images (such as competitive programming screenshots, shopping receipts, and social media feeds) must be rejected with an HTTP 422 error.

### 3.3 Analytical Engines & Scoring
* **FR-11: Company Verification**: The system shall cross-reference claimed company names against a curated enterprise registry (`verified_companies.json`) and detect domain mismatches (e.g., claiming to be TCS while using `@gmail.com`).
* **FR-12: URL Security Heuristics**: The system shall inspect submitted links for suspicious top-level domains, URL shorteners, raw IP hostnames, punycode, and brand mismatches without live fetching.
* **FR-13: Rule-Based Scam Detection**: The system shall execute 14 deterministic pattern rules detecting upfront registration fees, equipment purchase demands, WhatsApp-only interviews, and sensitive personal ID requests.
* **FR-14: Machine Learning Inference**: The system shall vectorize job text via TF-IDF and compute statistical scam probability using a trained Logistic Regression classifier.
* **FR-15: 5-Dimensional Credibility Scoring**: The system shall compute an evidence-based Trust Score (0–100) using five transparent weights:
  * Company Verification: 25%
  * Job / Source Credibility: 20%
  * Job Posting Quality: 15%
  * Scam & Red Flag Detection: 30%
  * Contact Domain Consistency: 10%
* **FR-16: Evidence-Based Guardrail Caps**: The system shall enforce non-negotiable safety caps:
  * Impersonation Risk: Trust Score capped at ≤ 25 (High Risk).
  * Critical Scam Indicator: Trust Score capped at ≤ 35 (High Risk).
  * Unverified Company: Trust Score capped at ≤ 65 (Medium Risk).
* **FR-17: Explainable Rationale Generation**: The system shall synthesize structured natural language reports with verbatim evidence snippets and safety checklists.

### 3.4 History, Dashboard & Community Reporting
* **FR-18: Persistent User History**: The system shall automatically archive every completed analysis under the authenticated candidate's user account.
* **FR-19: Multi-Tenant Data Isolation**: The system shall enforce strict user isolation, ensuring candidates can only browse, view, or delete their own scan records.
* **FR-20: Security Dashboard**: The system shall render aggregate statistics, average trust ratings, risk distributions, recent activity, and a 14-day scan timeline.
* **FR-21: Community Scam Reports**: The system shall allow users to submit community reports of fraudulent recruitment activity.
* **FR-22: Analysis Accuracy Feedback**: The system shall allow candidates to submit feedback (`correct`, `incorrect`, `report`) on analysis outcomes.

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements
* **API Response Latency**: Text analysis endpoints (`/api/analyze`) must return results within **500 milliseconds** under standard load.
* **OCR Throughput**: Screenshot processing and text extraction must complete within **3.0 seconds** for typical screenshots (< 2 MB).
* **Database Efficiency**: Indexed lookups on `users.email` and `analysis_results.user_id` must execute in under **10 milliseconds**.

### 4.2 Security & Privacy Requirements
* **Transport Encryption**: All client-server communication must support TLS / HTTPS encryption.
* **Stateless Authorization**: Protected routes must require a valid JWT Bearer token validated on every request.
* **Rate Limiting**: Authentication endpoints must enforce in-memory rate limiting to prevent automated brute-force attacks.
* **SQL Injection Prevention**: All database queries must use SQLAlchemy parameterized statements.
* **Upload Security**: Uploaded files must be validated for MIME type, restricted in size, and stored with UUID-generated filenames outside the web root.

### 4.3 Reliability & Availability
* **Database Failover**: The application must automatically utilize local SQLite storage if MySQL is unconfigured, ensuring uninterrupted local development.
* **SMTP Fallback**: If an SMTP server is unreachable or unconfigured, OTPs must log to the secure server console (`SMTP_CONSOLE_FALLBACK=True`), allowing local testing without email infrastructure.

### 4.4 Usability & Accessibility
* **Interface Clarity**: High, medium, and low risk states must be visually distinct using universally recognized safety colors (Green, Amber, Red).
* **Responsive Layout**: The user interface must adapt seamlessly across desktop monitors, laptops, and mobile screens.

---

## 5. System Constraints & Compliance Disclaimer

1. **Academic & Research Scope**: AI JobShield is developed as an educational software engineering project.
2. **Advisory Nature**: The credibility score and risk classification provide heuristic guidance, not definitive legal determinations. A mandatory safety disclaimer is appended to every analysis report.
