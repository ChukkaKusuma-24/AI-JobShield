# AI JobShield — Communication Diagram

This document illustrates the collaboration between system objects and architectural subsystems during runtime execution, emphasizing message sequencing, structural pathways, and communication channels.

---

## 1. Collaboration Overview

Unlike sequence diagrams which emphasize linear time order, communication diagrams emphasize the structural linkages between collaborating objects and subsystems.

```mermaid
graph LR
    %% Objects / Subsystems
    User["1: Job Seeker<br/>(Client Browser)"]
    Frontend["2: React SPA<br/>(AnalyzePage & Axios)"]
    Gateway["3: FastAPI Gateway<br/>(/api/analyze Router)"]
    AuthService["4: Security Service<br/>(JWT & Session)"]
    Analyzer["5: Analyzer Service<br/>(Orchestrator)"]
    CompanyVerifier["6: Company Verifier<br/>(Registry Matcher)"]
    URLAnalyzer["7: URL Analyzer<br/>(Heuristics)"]
    RuleEngine["8: Rule Engine<br/>(14 Red Flag Patterns)"]
    MLService["9: ML Service<br/>(TF-IDF + Logistic Reg)"]
    ScoringEngine["10: 5D Scoring Engine<br/>(Weights & Hard Caps)"]
    ExplainBuilder["11: Explainability Builder<br/>(Rationale Synthesizer)"]
    Database[("12: Database System<br/>(MySQL / SQLite)")]

    %% Structural links and numbered messages
    User <-->|1: Fills job form & submits<br/>18: Views rendered trust gauge & report| Frontend
    Frontend <-->|2: POST /api/analyze (Bearer JWT + Payload)<br/>17: 200 OK (Full Analysis JSON)| Gateway
    Gateway <-->|3: Verify Bearer JWT<br/>4: CurrentUser verified (user_id)| AuthService
    Gateway <-->|5: run_analysis(user_id, job_data)<br/>16: Serialized analysis result| Analyzer

    Analyzer <-->|6: verify_company(company, email, url)<br/>7: Verification status & reasons| CompanyVerifier
    Analyzer <-->|8: analyze_url(url)<br/>9: URL risk score & indicators| URLAnalyzer
    Analyzer <-->|10: analyze_rules(job_text, company_status)<br/>11: Red flags & positive bonuses| RuleEngine
    Analyzer <-->|12: predict(job_text)<br/>13: Scam probability & top terms| MLService

    Analyzer -->|14: compute_trust_score(dim1..dim5, caps)| ScoringEngine
    Analyzer -->|15: build_explanation(score, flags, breakdown)| ExplainBuilder

    Analyzer <-->|16a: INSERT into job_postings<br/>16b: INSERT into analysis_results<br/>16c: COMMIT transaction| Database
```

---

## 2. Numbered Communication Message Trace

| Sequence # | Sender | Receiver | Message Name & Parameters | Purpose |
| :---: | :--- | :--- | :--- | :--- |
| **1** | User | React Frontend | `submitJobForm(title, company, description, salary, email, url)` | User triggers analysis from the UI form. |
| **2** | React Frontend | FastAPI Gateway | `POST /api/analyze (Header: Bearer <token>, Body: JSON)` | Dispatches HTTP payload to the backend API router. |
| **3** | FastAPI Gateway | Security Service | `get_current_user(token: str)` | Validates HMAC-SHA256 signature and token expiry. |
| **4** | Security Service | FastAPI Gateway | `return CurrentUser(id, email, role)` | Passes authenticated user context to the router handler. |
| **5** | FastAPI Gateway | Analyzer Service | `run_analysis(db, user_id, title, company_name, description, ...)` | Initiates core multi-engine analytical workflow. |
| **6** | Analyzer Service | Company Verifier | `verify_company(db, company_name, email, url)` | Matches company against `verified_companies.json` and checks domain consistency. |
| **7** | Company Verifier | Analyzer Service | `return {status, confidence, reasons, company_score}` | Supplies company verification status and domain mismatch warnings. |
| **8** | Analyzer Service | URL Analyzer | `analyze_url(url, company_name)` | Evaluates link against suspicious TLDs, IP hosts, shorteners, and punycode. |
| **9** | URL Analyzer | Analyzer Service | `return {valid, risk_level, risk_score, indicators}` | Supplies source credibility score and indicators. |
| **10** | Analyzer Service | Rule Engine | `analyze_rules(title, company, description, salary, email, url, company_status)` | Executes 14 deterministic regex heuristics and positive checks. |
| **11** | Rule Engine | Analyzer Service | `return (red_flags, positives, positive_bonus)` | Returns flagged patterns with evidence snippets and positive indicators. |
| **12** | Analyzer Service | ML Service | `predict(cleaned_text)` | Performs TF-IDF tokenization and Logistic Regression probability inference. |
| **13** | ML Service | Analyzer Service | `return {scam_probability, top_terms}` | Returns statistical likelihood of fraud and influential vocabulary tokens. |
| **14** | Analyzer Service | 5D Scoring Engine | `compute_trust_score(red_flags, bonus, ml_prob, company_res, url_res, positives)` | Aggregates 5 dimensions and applies safety hard caps. |
| **15** | Analyzer Service | Explainability Builder| `build_explanation(trust_score, risk_level, red_flags, positives, ...)` | Assembles structured markdown text detailing rationale and advice. |
| **16a** | Analyzer Service | Database | `INSERT INTO job_postings (...)` | Records raw posting parameters and owner user reference. |
| **16b** | Analyzer Service | Database | `INSERT INTO analysis_results (...)` | Stores computed score, risk level, JSON breakdowns, and explanation. |
| **16c** | Analyzer Service | Database | `COMMIT` | Finalizes database transaction atomically. |
| **17** | FastAPI Gateway | React Frontend | `HTTP 200 OK (application/json)` | Returns complete serialized analysis payload to the client. |
| **18** | React Frontend | User | `renderView(TrustGauge, DimensionCards, RedFlagList, Explanation)` | Displays interactive, transparent evaluation report to candidate. |

---

## 3. Communication Pathways & Protocols

1. **Client-to-Gateway Channel**:
   * Protocol: `HTTPS / HTTP/1.1` with Cross-Origin Resource Sharing (CORS) credentials.
   * Format: UTF-8 JSON payloads with `Authorization: Bearer <JWT>` header.
2. **Gateway-to-Service Intra-Process Calls**:
   * Asynchronous, in-memory Python method calls within the Uvicorn worker runtime, avoiding inter-process network serialization overhead.
3. **Service-to-Database Channel**:
   * Protocol: Native MySQL TCP/IP protocol (port 3306) via PyMySQL / SQLAlchemy connection pool with `pool_pre_ping=True`, or direct local filesystem I/O for SQLite.
4. **Gateway-to-SMTP Channel**:
   * Protocol: SMTP over TLS (`STARTTLS`, port 587) with RFC 5322 MIME message formatting.
