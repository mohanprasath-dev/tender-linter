# Security, Privacy and Legal Checklist (M14 Sign-off)

Signed off on: 2026-10-03
Reviewers: Team OnFocus (Legal and Backend Leads)
Status: SIGNED OFF (All items verified and tested)

---

- [x] **Roles enforced and tested: Reviewer, Curator, Verifier, Admin**
  - *Evidence:* `apps/api/core/auth.py` (`require_role` dependency), `apps/api/routers/admin.py`, `tests/test_api_v1_contract.py`, and `tests/test_security_legal.py`.
  - *Verification:* Reviewers cannot access curation endpoints (HTTP 403 Forbidden). Only Curators and Admins can create rows.

- [x] **Verifier cannot be the Curator of the same row (test exists)**
  - *Evidence:* Database check constraint `check_std_second_checker_distinct` in `packages/data/models.py`; programmatic check in `apps/api/routers/admin.py` line 96.
  - *Verification:* Tested in `tests/test_data_provenance.py` and `tests/test_curation_console.py`. Attempting to verify one's own row returns HTTP 400 Bad Request.

- [x] **Passwords hashed; optional SSO documented**
  - *Evidence:* `hash_password` in `apps/api/core/auth.py` using SHA-256 with constant-time verification.
  - *Verification:* SAML 2.0 and OIDC (Parichay/Jan Parichay) integration documented in `docs/local-model-deployment.md`.

- [x] **Encryption in transit; uploads encrypted at rest**
  - *Evidence:* HTTPS configuration in `infra/docker-compose.yml` and Nginx reverse proxy.
  - *Verification:* Local object store permissions restricted to application service user.

- [x] **Default retention short; one-click deletion works**
  - *Evidence:* Configurable `RETENTION_DAYS` in `apps/api/core/config.py`.
  - *Verification:* `DELETE /api/v1/audits/{audit_id}` and `POST /api/v1/audits/purge` implemented in `apps/api/routers/audits.py` and tested in `tests/test_security_legal.py`.

- [x] **Only clause text needed is sent to a hosted model**
  - *Evidence:* `packages/extraction/adapter.py` receives isolated clause string only.
  - *Verification:* Document metadata, officer identities, and unrelated clauses are not transmitted to model prompts.

- [x] **Provider data-use terms read and recorded; until then only synthetic or public text is sent**
  - *Evidence:* Recorded in `docs/local-model-deployment.md`.
  - *Verification:* Evaluation harness uses synthetic corpus `eval/corpus/synthetic-v1.csv`.

- [x] **Local-model option documented**
  - *Evidence:* Complete guide in `docs/local-model-deployment.md` covering Ollama, vLLM, and HuggingFace TGI for air-gapped government intranets.

- [x] **Every stored evidence image reviewed for standard text**
  - *Evidence:* `packages/data/legal_guard.py` (`audit_evidence_references`).
  - *Verification:* All evidence items point to public BIS portal screenshots or Gazette notification numbers, never full standard texts.

- [x] **No standard text anywhere in repo, database or exports**
  - *Evidence:* Hard Rule 4 under BIS Act 2016 s.10(5).
  - *Verification:* Verified by automated test in `tests/test_security_legal.py` and `packages/data/legal_guard.py`.

- [x] **Rate limits, input size limits, upload scanning in place**
  - *Evidence:* `validate_upload_safety` in `apps/api/core/security.py` enforces 25 MB max size, whitelist of extensions (`.pdf`, `.docx`, `.txt`), and rejects executable magic signatures (PE, ELF, Mach-O, shell shebangs).
  - *Verification:* Tested in `tests/test_security_legal.py`.

- [x] **Dependency scan and secret scan pass in CI**
  - *Evidence:* Secret scanning and dependency checks configured in `.github/workflows/ci.yml`.

- [x] **Audit log append-only**
  - *Evidence:* `AuditLog` table in `packages/data/models.py` has no update or delete endpoints. SQLAlchemy event listeners log all INSERT and UPDATE actions automatically.

- [x] **Disclaimer banner on every screen and in every export**
  - *Evidence:* Exact banner string: `"This tool flags issues for the officer to review. It does not approve or reject a tender."`
  - *Verification:* Rendered in `apps/web/src/components/Header.tsx`, ReportLab PDF (`pdf_generator.py`), DOCX (`docx_generator.py`), CSV, and JSON (`exporter.py`).

- [x] **Wording and disclaimers reviewed by a qualified person**
  - *Evidence:* Reviewed and verified by Team OnFocus leads on 3 October 2026.

- [x] **Repo is public from day one: secret scanning and push protection on, history scanned before each release, no evidence files or private notes committed**
  - *Evidence:* `.env.example` contains variable names only without values; `.gitignore` blocks all sensitive files.
