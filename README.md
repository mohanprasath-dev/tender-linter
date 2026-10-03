# Tender Linter

Evidence-linked auditor for Indian Standards citations in draft tender specifications.  
**Team OnFocus** | **Team ID 176283** | **Smart India Hackathon 2026** | **Problem Statement SIH26108**

> **Mandatory Reviewer Banner:**  
> **This tool flags issues for the officer to review. It does not approve or reject a tender.**

---

## 1. What It Does

Procurement officials drafting government tender specifications must cite applicable, current Indian Standards (IS). Incomplete citations, obsolete years, missing mandatory certifications, or vague quality phrases cause vendor ambiguity, substandard supply, and costly contract disputes.

Tender Linter audits draft tender specifications:
1. **Ingests** raw text, Microsoft Word (`.docx`), and Adobe PDF (`.pdf`) documents.
2. **Extracts** cited Indian Standards, publication years, mentioned products, and subjective quality phrases.
3. **Evaluates** deterministic rules (R01 through R14) against a curated database of source-linked rows.
4. **Reports** line-level findings with direct clickable links to official BIS catalogue records, verified dates, and actionable drafting recommendations.
5. **Abstains cleanly:** If a product or standard is not in the verified dataset, it reports *"No applicable standard in our dataset"* instead of hallucinating answers.

---

## 2. Non-Negotiable Core Principles

1. **The LLM never decides:** The language model extracts entities only. Deterministic rules decide verdicts.
2. **Evidence or silence:** Every finding requires a primary source link (BIS catalogue or Gazette) and a verified date.
3. **Abstain by design:** "Not in our dataset" is a first-class output, not an error.
4. **Metadata, not text:** In accordance with Section 10(5) of the BIS Act 2016, we store and report metadata and links only. Indian Standard text is never reproduced or summarized.
5. **Say what was measured:** Accuracy is strictly reported as *"X of Y on test set Z"* (no bare percentages).
6. **The officer stays in charge:** The tool flags and assists; it never approves or rejects a tender.

---

## 3. Quick Start (One Command)

### Option A: Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/mohanprasath-dev/tender-linter.git
cd tender-linter

# Launch the full stack (Web UI, API Backend, PostgreSQL Database)
docker compose -f infra/docker-compose.yml up --build
```
- **Web Interface:** [http://localhost:3000](http://localhost:3000) (or [http://localhost:5173](http://localhost:5173))
- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Probe:** [http://localhost:8000/health/ready](http://localhost:8000/health/ready)

### Option B: Local Development
```bash
# 1. Install backend dependencies and initialize database
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r apps/api/requirements.txt
python -m packages.data.loader

# 2. Start API backend
uvicorn apps.api.main:app --reload --port 8000

# 3. Start frontend (in a separate terminal)
cd apps/web
npm install
npm run dev
```

---

## 4. Sample Audit Walkthrough

Audit a sample clause referencing an outdated IT equipment standard without mentioning mandatory BIS CRS registration:

```bash
curl -X POST http://localhost:8000/api/v1/audits/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The contractor shall supply 200 laptops conforming to IS 13252 (Part 1): 2010.",
    "language_hint": "en"
  }'
```

### Expected Output Summary
```json
{
  "banner": "This tool flags issues for the officer to review. It does not approve or reject a tender.",
  "clauses": [
    {
      "text": "The contractor shall supply 200 laptops conforming to IS 13252 (Part 1): 2010.",
      "findings": [
        {
          "rule_id": "R05",
          "severity": "ERROR",
          "message": "The certification list specifies IS/IEC 62368 Part 1 for this product. This clause cites IS 13252 (Part 1).",
          "evidence": {
            "source_url": "https://www.meity.gov.in/esdm/standards",
            "verified_on": "2026-10-02"
          }
        },
        {
          "rule_id": "R06",
          "severity": "WARNING",
          "message": "A certification requirement is listed for this product and the clause does not mention it.",
          "evidence": {
            "source_url": "https://www.meity.gov.in/esdm/standards",
            "verified_on": "2026-10-02"
          }
        }
      ]
    }
  ]
}
```

---

## 5. Measured Evaluation Results

Evaluated across the comprehensive synthetic test matrix (`eval/corpus/synthetic-v1.csv`):

- **Rule Recall:** **75 of 75** planted defects caught on synthetic corpus v1.
- **False Alarms:** **0 false alarms** on clean control clauses.
- **Abstain Correctness:** **100% correct abstentions** on unmapped out-of-dataset products (triggering R10).
- **Invented Citations:** **0 hallucinations** (validated by span validator).
- **Rule Latency:** Median p50 of **0.04 ms** per clause.

---

## 6. Repository Layout

```
tender-linter/
  apps/web/            React + TypeScript Reviewer UI and Curation Console
  apps/api/            FastAPI backend, auth, upload scanner, health probes
  packages/data/       SQLAlchemy models, migrations, provenance checks, backup/restore
  packages/rules/      rules.yaml, evaluators R01 to R14, context loader
  packages/extraction/ regex extractor, model adapters, rate limiter, span validator
  packages/ingestion/  DOCX, PDF, and plain text clause parser
  packages/reports/    PDF, DOCX, CSV, and JSON report exporters
  eval/                75-clause test corpus, evaluation runner, and reports
  docs/                spec, architecture, rule catalogue, runbooks, checklists
  infra/               docker-compose, production containers, nginx configs
  scripts/             backup/restore, keepalive daemon, and load test runner
  .agents/skills/      Antigravity skills for provenance, rules, and deck check
```

---

## 7. Key Documentation

- [Full Product Specification](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/PROJECT_SPEC.md)
- [System Architecture](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/architecture.md)
- [Rule Catalogue (R01 to R14)](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/rule-catalogue.md)
- [Curator and Verification Handbook](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/curator-handbook.md)
- [Operations and Deployment Runbook](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/deployment-runbook.md)
- [Submission Deck Claim Review](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/deck-claim-review.md)
- [Local Air-Gapped Model Deployment Guide](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/docs/local-model-deployment.md)

---

## 8. Public Repository and Copyright Compliance

This repository is public. In strict adherence to Section 10(5) of the Bureau of Indian Standards Act 2016, no standard text is reproduced or stored in this repository or database. All data consists solely of public metadata, dates, and official URLs.

**License:** MIT License. See [LICENSE](file:///d:/Hackathons/SIH2026/SIH26108/tender-linter/LICENSE).
