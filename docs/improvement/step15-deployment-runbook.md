# Step 15: Production Deployment Runbook

> **IMPORTANT NOTICE**:  
> This document provides **deployment instructions and operational procedures only**.  
> In accordance with Step 15 hard constraints, **NO ACTUAL PRODUCTION DEPLOYMENT WAS PERFORMED** by the assistant.

**Date**: 2026-10-04  
**Target Application**: AI JobShield — Intelligent Recruitment Fraud Detection Platform  
**Target Repository**: `https://github.com/ChukkaKusuma-24/AI-JobShield.git`  
**Git Author**: `karthikeyangullipalli <karthikeyangullipalli@gmail.com>`  
**Validated State**: 110 passed, 1 skipped, 0 failed; 98.44% red-team accuracy; 100% scam recall; 0 false negatives.

---

## A. Deployment Prerequisites

Before deploying the AI JobShield application to a production server or hosting platform:

1. **Host Operating System**: Ubuntu 22.04 / 24.04 LTS, Debian 12, or comparable Linux distribution.
2. **Runtime Dependencies**:
   - Python 3.10, 3.11, or 3.12 (Python 3.12 recommended).
   - Node.js $\ge 18.0.0$ and npm $\ge 9.0.0$.
   - Tesseract OCR (`apt-get install -y tesseract-ocr`).
   - Reverse Proxy: Nginx or Caddy with SSL/TLS certificate (Let's Encrypt / Certbot).
   - Database: SQLite (single-instance VM) or MySQL 8.0+ / PostgreSQL (multi-worker cluster).

---

## B. Production Environment Variables Reference

Create a secure `.env` file on the deployment host. **Never commit actual production secrets to Git.**

| Variable | Scope | Required | Production Recommendation | Description |
| :--- | :---: | :---: | :--- | :--- |
| `SECRET_KEY` | Backend | **Yes** | 64-char hex (`openssl rand -hex 32`) | Primary HMAC-SHA256 signature key for token signing |
| `JWT_SECRET` | Backend | Optional | 64-char hex (`openssl rand -hex 32`) | Dedicated JWT token signature key |
| `DATABASE_URL` | Backend | Optional | `mysql+pymysql://user:pass@db:3306/jobshield` | Production database connection URI |
| `CORS_ORIGINS` | Backend | Optional | `https://jobshield.yourdomain.com` | Allowed browser origins (comma-separated) |
| `VITE_API_BASE` | Frontend | Optional | `https://api.jobshield.yourdomain.com/api` | Target API base URL for compiled frontend Axios client |
| `ML_MODEL_PATH` | Backend | Optional | `models/jobshield_model.joblib` | Path to production model artifact |
| `EXPECTED_MODEL_SHA256` | Backend | Optional | `636e26e42b5a4179a42f9e9161dd7692d4f63146f...` | SHA-256 digest enforced prior to unpickling artifact |
| `TESSERACT_CMD` | Backend | Optional | `/usr/bin/tesseract` | System path to tesseract binary (auto-detected if in PATH) |
| `SMTP_HOST` | Backend | Optional | `smtp.gmail.com` | SMTP relay server for user email OTP delivery |
| `SMTP_PORT` | Backend | Optional | `587` | STARTTLS port |
| `SMTP_USER` | Backend | Optional | `security@yourdomain.com` | Authenticated email address |
| `SMTP_PASSWORD` | Backend | Optional | `<app-specific-password>` | SMTP authentication credential |
| `SMTP_CONSOLE_FALLBACK` | Backend | Optional | `false` | Disable console logging of OTPs in production |

---

## C. Backend Installation Procedure

```bash
# 1. Clone repository to deployment directory
git clone https://github.com/ChukkaKusuma-24/AI-JobShield.git /opt/jobshield
cd /opt/jobshield

# 2. Setup Python virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies from root manifest
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy and edit production environment variables
cp .env.example .env
nano .env

# 5. Verify database and model initialization
python -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
python -c "import sys; sys.path.insert(0, 'backend'); from app.services import ml_service; assert ml_service.load_model() and ml_service.is_sha256_verified()"
```

---

## D. Frontend Build Procedure

```bash
cd /opt/jobshield/frontend

# 1. Install production dependencies
npm install

# 2. Build production assets with production API URL
VITE_API_BASE=https://api.jobshield.yourdomain.com/api npm run build

# 3. Verify output dist
ls -la dist/
# Output includes dist/index.html and optimized dist/assets/
```

---

## E. Database Setup & Migrations

- **SQLite Deployments**: Ensure the directory `/opt/jobshield/database` is writable by the system service user (`chown -R www-data:www-data /opt/jobshield/database`).
- **MySQL / PostgreSQL Deployments**: Create the production database and grant privileges:
  ```sql
  CREATE DATABASE ai_jobshield CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  CREATE USER 'jobshield_app'@'localhost' IDENTIFIED BY '<SECURE_PASSWORD>';
  GRANT ALL PRIVILEGES ON ai_jobshield.* TO 'jobshield_app'@'localhost';
  FLUSH PRIVILEGES;
  ```
- Set `DATABASE_URL=mysql+pymysql://jobshield_app:<SECURE_PASSWORD>@localhost:3306/ai_jobshield` in `.env`.
- Database schema tables are created automatically on service launch via `init_db()`.

---

## F. Machine Learning Model Verification

- The model artifact resides at `models/jobshield_model.joblib`.
- The application automatically verifies SHA-256 integrity on startup:
  `636e26e42b5a4179a42f9e9161dd7692d4f63146f1475659021605b9676bf1a2`.
- Zero online retraining or artifact regeneration occurs on startup or request handling.
- If the artifact is tampered or corrupt, startup logs an error and refuses to load the invalid file, protecting the server against malicious code injection.

---

## G. OCR & Document Processing Prerequisites

1. Install Tesseract OCR:
   ```bash
   sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
   ```
2. Verify binary availability:
   ```bash
   which tesseract
   # Expected: /usr/bin/tesseract
   ```
3. If Tesseract is not installed, the application continues to run in degraded mode: text analysis, company verification, and URL inspection remain 100% active, while image upload requests return a clean HTTP 400 error.

---

## H. Production Startup Commands

### Option 1: Systemd Service (Recommended for Linux VM)

Create `/etc/systemd/system/jobshield-backend.service`:
```ini
[Unit]
Description=AI JobShield FastAPI Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/jobshield
EnvironmentFile=/opt/jobshield/.env
ExecStart=/opt/jobshield/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --chdir /opt/jobshield/backend \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/jobshield/access.log \
    --error-logfile /var/log/jobshield/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jobshield-backend
sudo systemctl start jobshield-backend
sudo systemctl status jobshield-backend
```

---

## I. Reverse Proxy & HTTPS Configuration (Nginx)

Create `/etc/nginx/sites-available/jobshield`:
```nginx
server {
    listen 80;
    server_name jobshield.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name jobshield.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/jobshield.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jobshield.yourdomain.com/privkey.pem;

    # Frontend Static Files
    root /opt/jobshield/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }
}
```

---

## J. Health-Check Endpoint & Post-Deployment Smoke Tests

### Automated Health Verification
```bash
curl -f https://jobshield.yourdomain.com/api/health
# Expected JSON response:
# {"status": "ok", "ml_available": true, "ocr_available": true, ...}
```

### Smoke Test Sequence
1. Send GET request to `/api/health` $\to$ Returns HTTP 200 with `status: "ok"`.
2. Register a new user via `POST /api/auth/register` $\to$ Returns HTTP 201.
3. Log in via `POST /api/auth/login` $\to$ Returns JWT bearer token.
4. Submit legitimate test posting (Infosys / TCS with corporate email) $\to$ Returns score $\ge 75$ (LOW Risk).
5. Submit scam test posting (TCS with `@gmail.com` or registration fee) $\to$ Returns score $\le 35$ (HIGH Risk).
6. Verify `/api/history` contains persisted scan records.

---

## K. Rollback Procedure

If a production defect is discovered post-release:
```bash
# 1. Stop backend service
sudo systemctl stop jobshield-backend

# 2. Check out prior stable commit / release tag
cd /opt/jobshield
git checkout <PREVIOUS_COMMIT_OR_TAG>

# 3. Reinstall dependencies and rebuild frontend
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# 4. Restart backend service
sudo systemctl start jobshield-backend

# 5. Verify health endpoint
curl -f http://127.0.0.1:8000/api/health
```

---

## L. Operational Security Checklist

- [ ] `SECRET_KEY` and `JWT_SECRET` are at least 32 bytes and randomly generated.
- [ ] Debug mode is disabled (`uvicorn --reload` is NOT used in production).
- [ ] `SMTP_CONSOLE_FALLBACK` is set to `false`.
- [ ] Database credentials are protected by strict file permissions (`chmod 600 .env`).
- [ ] HTTPS is enforced with HSTS headers enabled on reverse proxy.
- [ ] Uploads directory is restricted from direct script execution.
