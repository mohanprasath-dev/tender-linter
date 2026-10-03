# Tender Linter: Operations and Deployment Runbook

Team OnFocus | SIH 2026 | Problem Statement SIH26108

---

## 1. System Overview

Tender Linter is packaged for deployment using multi-stage container images:
- **Web Frontend:** Nginx Alpine serving React SPA with gzip compression, security headers, and reverse proxy routing.
- **API Backend:** Python 3.12 FastAPI application running with Uvicorn workers and structured access logging.
- **Database:** PostgreSQL 16 Alpine with connection pooling, health checks, and persistent volume storage.

---

## 2. Production Deployment

### 2.1 Prerequisites
- Docker Engine 24+ and Docker Compose v2.
- A valid `.env.production` file generated from `infra/.env.production.example`.
- TLS certificates installed on the host reverse proxy (or Cloudflare / AWS ALB / Nginx).

### 2.2 Launch Commands
```bash
# Copy example configuration and populate production secrets
cp infra/.env.production.example infra/.env.production

# Start production containers in detached mode
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.production up -d

# Verify container health status
docker compose -f infra/docker-compose.prod.yml ps
```

---

## 3. Always-On Demo Hosting and Cold-Start Mitigation

To satisfy the M15 quality gate ("the public demo link opens instantly after a day of inactivity"):

1. **Free/Hobby Tier Sleep Prevention:**
   Free hosting tiers (e.g. Render, Koyeb, Hugging Face Spaces) shut down containers after 15 minutes of inactivity, introducing 30 to 60 second cold-start delays.
2. **Automated Keepalive Ping:**
   - GitHub Actions workflow `.github/workflows/keepalive.yml` pings `/health/ready` every 10 minutes.
   - Alternatively, run the daemon script on an external monitoring server:
     ```bash
     python scripts/keepalive.py --url https://demo.tender-linter.gov.in/health/ready --interval 300
     ```
3. **Cold Device Test Procedure:**
   Before demo presentation day:
   - Clear all browser cache or use an incognito window on a fresh mobile device.
   - Access the demo URL directly.
   - Expected initial response time: < 800 ms.

---

## 4. Health Probes, Tracing, and Structured Logging

### 4.1 Probe Endpoints
| Endpoint | Method | Purpose | Expected Status |
|---|---|---|---|
| `/health` | GET | General health and database status | 200 OK |
| `/health/live` | GET | Container liveness check | 200 OK |
| `/health/ready` | GET | Readiness check (DB connection + rules loaded) | 200 OK (or 503 if DB disconnected) |

### 4.2 Request Tracing (`X-Request-ID`)
All HTTP requests receive a unique `X-Request-ID` header. If passed by the client or reverse proxy, it is preserved; otherwise, a unique identifier is generated. The request ID is included in:
- HTTP response headers (`X-Request-ID: req_...`).
- Structured server logs (`rt=... req_id=...`).
- Unhandled 500 error alerts.

---

## 5. Backup, Verification, and Restore Runbook

### 5.1 Automated Backup
To take a full, manifest-verified backup of the database tables and evidence store:
```bash
python scripts/backup_restore.py --backup --output ./backups
```
This produces a compressed archive: `backups/tender_linter_backup_YYYYMMDD_HHMMSS.tar.gz`.

### 5.2 Backup Integrity Check
To verify that all files in a backup archive match their SHA-256 manifest:
```bash
python scripts/backup_restore.py --verify-backup ./backups/tender_linter_backup_20261003_120000.tar.gz
```

### 5.3 Disaster Recovery and Restore
To restore database state and object store files from an archive:
```bash
python scripts/backup_restore.py --restore ./backups/tender_linter_backup_20261003_120000.tar.gz
```

---

## 6. Concurrent Load Testing and Performance SLAs

### 6.1 Performance Targets
- **Readiness probe p95:** < 50 ms.
- **Standards lookup p95:** < 100 ms.
- **Audit evaluation p95:** < 500 ms (cached / reduced regex mode).
- **Error rate:** 0.0% under 20 concurrent users.

### 6.2 Running Load Tests
```bash
python scripts/load_test.py --concurrency 10 --requests 50
```
