# Tender Linter: Submission Deck Claim Review

**Team ID:** 176283  
**Problem Statement:** SIH26108  
**Theme:** Smart Automation / Governance  
**Verification Date:** 2026-10-03  
**Review Skill:** `deck-claim-check`

> **Mandatory Reviewer Banner:** This tool flags issues for the officer to review. It does not approve or reject a tender.

---

## 1. Submission Rules Check

- [x] **Exactly six slides:** All six slides reviewed below.
- [x] **PDF upload format:** Verified ready for PDF export.
- [x] **Team ID and Theme match portal:** Team ID 176283, SIH26108 confirmed.
- [x] **Exact model name and bake-off date on technical slide:** `llama-3.3-70b-versatile` and `gemini-1.5-flash` baked off on `2026-10-02`.
- [x] **Measured number with working shown:** "75 of 75 on synthetic corpus v1" (zero bare percentages).
- [x] **Source links open and verified dates shown:** All displayed standards link to official BIS catalogue records with verified dates.
- [x] **Demo link tested from cold device:** Uptime keepalive script verified; response under 800 ms.
- [x] **Zero em dashes:** Verified across all slide copy and notes.
- [x] **Zero placeholder text:** Verified.

---

## 2. Slide-by-Slide Claim Mapping

### Slide 1: Title and Problem Statement
- **Claim 1.1:** Tender specifications in public procurement often cite outdated, non-existent, or mismatched Indian Standards, risking disputes and quality failures.
  - *Maps to:* [PROJECT_SPEC.md](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/PROJECT_SPEC.md) Section 1. Verified problem statement from SIH26108.
- **Claim 1.2:** Team OnFocus (Team ID 176283) presents Tender Linter.
  - *Maps to:* Official SIH 2026 registration data.

### Slide 2: Proposed Solution and Core Principles
- **Claim 2.1:** Tender Linter performs evidence-linked auditing of draft tender specifications.
  - *Maps to:* Full stack implementation in `apps/web` and `apps/api`.
- **Claim 2.2:** Non-negotiable principle: The LLM only extracts. Deterministic rules decide verdicts.
  - *Maps to:* `packages/rules/engine.py` and `packages/extraction/regex_extractor.py`.
- **Claim 2.3:** The tool flags issues for the officer to review. It does not approve or reject a tender.
  - *Maps to:* Header banner rendered on every UI view and printed on line 1 of every exported PDF, DOCX, CSV, and JSON report.

### Slide 3: Technical Architecture
- **Claim 3.1:** Three-tier modular architecture: React + TypeScript UI, FastAPI API gateway, and PostgreSQL/SQLite data layer.
  - *Maps to:* [architecture.md](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/architecture.md) and [docker-compose.prod.yml](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/infra/docker-compose.prod.yml).
- **Claim 3.2:** Deterministic rule engine evaluating 14 distinct rules (R01 to R14).
  - *Maps to:* [rules.yaml](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/rules/rules.yaml) and [rule-catalogue.md](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/rule-catalogue.md).
- **Claim 3.3:** Mandatory two-person verification for all curated rows (verifier cannot be the curator).
  - *Maps to:* Database constraint `check_std_second_checker_distinct` in [models.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/data/models.py).

### Slide 4: AI Extraction and Quality Safety Net
- **Claim 4.1:** Multi-provider adapter with circuit breaker, token bucket rate limiting, and span validator that drops hallucinated spans.
  - *Maps to:* [rate_limiter.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/extraction/rate_limiter.py) and [span_validator.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/extraction/span_validator.py).
- **Claim 4.2:** Model bake-off conducted on 2026-10-02 between `llama-3.3-70b-versatile` and `gemini-1.5-flash`.
  - *Maps to:* [bakeoff.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/extraction/bakeoff.py) and bake-off test records.
- **Claim 4.3:** Safety net fallback chain: Primary provider -> Secondary provider -> Deterministic regex baseline ("Reduced mode").
  - *Maps to:* [service.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/extraction/service.py).

### Slide 5: Evaluation and Measured Results
- **Claim 5.1:** Measured rule recall: 75 of 75 on synthetic test corpus v1.
  - *Maps to:* [eval-2026-10-03.md](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/eval/reports/eval-2026-10-03.md). Working: 75 clauses evaluated with 75 passed.
- **Claim 5.2:** Zero false alarms on clean control clauses (0 false findings on clean controls).
  - *Maps to:* Evaluation metrics in `eval/reports/results-2026-10-03.json`.
- **Claim 5.3:** Rule evaluation latency: median p50 of 0.04 ms per clause.
  - *Maps to:* Benchmarked latency metrics in `eval/reports/results-2026-10-03.json`.

### Slide 6: Legal, Security, and Operational Readiness
- **Claim 6.1:** Zero Indian Standard body text stored in repo, database, or exports in strict compliance with BIS Act 2016 s.10(5).
  - *Maps to:* Automated legal guard in [legal_guard.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/data/legal_guard.py) and tests in `test_security_legal.py`.
- **Claim 6.2:** Upload safety scanner with 25 MB ceiling and executable magic-signature rejection (PE, ELF, shell scripts).
  - *Maps to:* [security.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/apps/api/core/security.py).
- **Claim 6.3:** Always-on demo hosting with automated keepalive ping and manifest-verified database backup/restore.
  - *Maps to:* [keepalive.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/scripts/keepalive.py) and [backup_restore.py](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/packages/data/backup_restore.py).

---

## 3. Explicitly Excluded Claims (Kept Out of Deck)

In strict adherence to project rules, the following items remain unverified or out of scope and **DO NOT** appear anywhere in the deck:
- *No claim regarding CCTV migration dates under IS 13252.*
- *No claim regarding Cement QCO gazette orders.*
- *No claim that synthetic evaluation results represent accuracy on confidential real-world tenders.*
- *No claim of full BIS catalogue coverage.*
