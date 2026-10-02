# AI JobShield — Deployment Diagram

This document details the physical, process, and network deployment topology of **AI JobShield**, illustrating runtime nodes, process containers, network protocols, ports, and hardware boundaries.

---

## 1. Deployment Topology Diagram

```mermaid
graph TB
    %% =========================================================================
    %% CLIENT NODE
    %% =========================================================================
    subgraph ClientDevice ["Client Tier: End-User Device (Windows / macOS / Linux)"]
        subgraph BrowserRuntime ["Web Browser (Chrome, Firefox, Safari, Edge)"]
            SPA["React 18 Single-Page Application (HTML5 / ES6+ JavaScript)<br/>Client-Side Routing via React Router v6<br/>State Management via AuthContext & Axios Client"]
        end
    end

    %% =========================================================================
    %% HOST SERVER
    %% =========================================================================
    subgraph HostServer ["Application Tier: Host Workstation / Server"]
        subgraph WebServerNode ["Frontend Web Server (Node.js / Nginx)"]
            ViteDev["Vite Development Server (Port: 5173)<br/>Hot Module Replacement (HMR)<br/>Static Asset Bundle: frontend/dist/"]
        end

        subgraph AppServerNode ["Backend Application Server (Python 3.10+ Runtime)"]
            Uvicorn["Uvicorn ASGI Server (Port: 8000)<br/>Asynchronous Event Loop (AnyIO / uvloop)<br/>FastAPI Web Framework (app/main.py)"]

            subgraph PythonVenv ["Python Virtual Environment (.venv / venv)"]
                AppRouterGroup["API Routers (auth, analyze, ocr, history...)"]
                AnalyticalEngines["Core Analytical Engines (ML, Rules, Scoring)"]
                ORM["SQLAlchemy 2.0 ORM Engine"]
            end

            Uvicorn --> AppRouterGroup
            AppRouterGroup --> AnalyticalEngines
            AnalyticalEngines --> ORM
        end

        subgraph NativeTools ["Native Operating System Subsystems"]
            TesseractExe["Tesseract OCR Executable Binary<br/>Path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe<br/>(or /usr/bin/tesseract on Linux)"]
            FileStorage["Local Upload Storage Directory<br/>Path: uploads/*.png, *.jpg, *.webp"]
        end

        subgraph DatabaseNode ["Persistence Tier: Relational Database"]
            MySQLServer["MySQL 8.0 Server Daemon<br/>(Port: 3306, Database: jobshield)<br/>InnoDB Engine, utf8mb4 collation"]
            SQLiteFile["SQLite 3 Database File (Zero-Config Fallback)<br/>Path: database/jobshield.db"]
        end
    end

    %% =========================================================================
    %% EXTERNAL CLOUD SERVICES
    %% =========================================================================
    subgraph ExternalCloud ["External Communications Tier"]
        GmailSMTP["Google Gmail SMTP Server<br/>(smtp.gmail.com : Port 587)<br/>STARTTLS Encryption with App Passwords"]
    end

    %% =========================================================================
    %% CONNECTIONS & PROTOCOLS
    %% =========================================================================
    SPA -->|HTTP / localhost:5173| ViteDev
    SPA -->|REST API over HTTP/1.1 (CORS Enabled)<br/>Authorization: Bearer JWT<br/>Port: 8000| Uvicorn

    Uvicorn -->|Subprocess Execution / STDIN-STDOUT<br/>pytesseract.image_to_string| TesseractExe
    Uvicorn -->|File I/O / Local Writes| FileStorage

    ORM -->|PyMySQL Connection Pool (TCP/IP)<br/>Port: 3306| MySQLServer
    ORM -.->|Direct Disk File I/O (Fallback / Testing)| SQLiteFile

    AppServerNode -->|SMTP over TLS / Port: 587<br/>smtplib.SMTP_SSL / STARTTLS| GmailSMTP
```

---

## 2. Infrastructure Node Specifications

### A. Client Tier (End-User Browser)
* **Execution Environment**: Standard evergreen web browser (Google Chrome ≥ 100, Mozilla Firefox ≥ 100, Microsoft Edge ≥ 100, Apple Safari ≥ 15).
* **Delivered Artifacts**: Minified HTML5, CSS3 (Tailwind styles compiled by PostCSS), and bundled JavaScript executed directly in the browser's V8 / JavaScriptCore engine.
* **Storage Consumption**: Browser `localStorage` holds the signed JWT authentication token; no sensitive user data is stored unencrypted in client cookies.

### B. Frontend Hosting Tier (Vite / Nginx)
* **Development Mode**: `npm run dev` running on `http://localhost:5173` with fast Hot Module Replacement (HMR).
* **Production Build**: `npm run build` generates static HTML/JS/CSS distribution in `frontend/dist/`. In production, this can be served by an Nginx reverse proxy, Caddy, or mounted directly onto FastAPI as a static mount.
* **CORS Policy**: Configured in FastAPI backend via `CORSMiddleware`, permitting origins `http://localhost:5173`, `http://127.0.0.1:5173`, and configured deployment hostnames.

### C. Backend Application Tier (FastAPI + Uvicorn)
* **Runtime**: Python 3.10 to 3.13 executed inside an isolated virtual environment (`backend/venv` or `.venv`).
* **Web Server**: Uvicorn ASGI server running asynchronous event loops on `http://127.0.0.1:8000`.
* **Process Model**: Single-process asynchronous worker during local development; scalable to multi-worker gunicorn-managed processes (`uvicorn.workers.UvicornWorker`) in clustered environments.
* **System Logging**: Application logs stream to stdout and rotating log files with timestamp, route, status code, and latency.

### D. Native Tooling & Operating System Subsystems
* **Optical Character Recognition (OCR)**:
  * Uses the native `tesseract` binary executable.
  * Windows Default Path: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  * Linux Default Path: `/usr/bin/tesseract`.
  * Configured via `.env` variable: `TESSERACT_CMD`.
* **File Uploads Storage**:
  * Stored on the local filesystem under the `uploads/` directory.
  * Files are saved with cryptographically random UUIDv4 names (e.g. `03fcf004e1db4062a58c95c0377d5d98.png`) to prevent directory traversal and file overwrite collisions.

### E. Database Tier (MySQL 8.0 & SQLite3)
* **Production Database**: MySQL 8.0 running on `localhost:3306` with `InnoDB` storage engine, `utf8mb4` character set, and `utf8mb4_unicode_ci` collation.
* **Zero-Configuration Fallback**: SQLite 3 database (`database/jobshield.db`) automatically activated when `DATABASE_URL` is omitted or in test runner environments (`tests/test_*.py`), enabling zero-friction local execution.
* **Connection Pooling**: SQLAlchemy `QueuePool` with health check pre-pings (`pool_pre_ping=True`) ensuring disconnected connections are automatically refreshed.

### F. Mail Gateway Tier (SMTP Relay)
* **Relay Target**: Google Gmail SMTP (`smtp.gmail.com:587`) or custom institution SMTP server.
* **Encryption**: `STARTTLS` encryption with port 587.
* **Authentication**: 16-character Google App Passwords; real passwords are never stored.
* **Testing Fallback**: When SMTP credentials are not supplied in `.env`, the backend enables `SMTP_CONSOLE_FALLBACK=True`, outputting verification OTP codes directly to server logs without failing.
