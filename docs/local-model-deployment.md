# Local Model Deployment and Security Architecture

## 1. Overview
Tender Linter is designed for secure deployment in sensitive government procurement environments. This document outlines the security architecture, local air-gapped model execution, data privacy policies, and institutional Single Sign-On (SSO) integration options according to Section 12 of the product specification.

---

## 2. Air-Gapped and Local Model Deployment

For restricted or confidential environments where procurement drafts cannot leave the intranet, Tender Linter provides first-class support for local model backends via the standard `Extractor` interface (`packages/extraction/adapter.py`).

### 2.1 Supported Local Inference Engines
- **Ollama:** Lightweight local execution for models such as Llama 3.1 8B, Mistral, or Qwen.
- **vLLM / HuggingFace TGI:** High-throughput production serving with batching and GPU acceleration.
- **Deterministic Regex Fallback:** Zero-GPU, zero-network mode that extracts citations and maps products purely via deterministic regex and curated synonym dictionaries.

### 2.2 Configuration (.env)
To route extraction to a local inference instance, configure the following environment variables:
```bash
# Provider Configuration for Local Model
PROVIDER_PRIMARY=ollama
MODEL_ID_PRIMARY=llama3.1:8b-instruct-q4_K_M
PROVIDER_PRIMARY_BASE_URL=http://localhost:11434
PROVIDER_PRIMARY_KEY=none

# Local Timeout and Request Limits
EXTRACTOR_TIMEOUT_SECONDS=15
RATE_LIMIT_RPM=120
DAILY_CAP=10000
```

### 2.3 Strict Privacy and Egress Boundaries
- When using local models, all inference runs within the local boundary with zero outbound network calls.
- Even when a hosted provider is configured in development, **only the single clause text under review is submitted** to the model. The entire tender document, officer identities, file paths, and administrative metadata are never transmitted.

---

## 3. Hosted Provider Data-Handling Policies

When hosted providers are evaluated or used:
- **Groq:** Free-tier API calls process input text ephemerally without persistent training on submitted customer data under their developer terms of service.
- **Google Gemini:** Vertex AI and Gemini API enterprise endpoints do not use customer prompts or generated outputs to train foundational models.
- **Synthetic Data Baseline:** Until institutional data-use agreements are formally signed, the project evaluation suite and demonstrations utilize synthetic test sets (`eval/corpus/synthetic-v1.csv`) to eliminate any risk of confidential tender disclosure.

---

## 4. Institutional Single Sign-On (SSO) Integration

Tender Linter supports standard token-based authentication (JWT with SHA-256 hashed credentials) and can be connected to institutional identity providers (IdPs) via standard protocols:

### 4.1 Supported SSO Protocols
- **SAML 2.0:** Compatible with enterprise Active Directory Federation Services (ADFS) and government portals.
- **OpenID Connect (OIDC) / OAuth 2.0:** Compatible with NIC Parichay / Jan Parichay and Keycloak.

### 4.2 Role Mapping
Incoming IdP claims map directly to the four role tiers enforced by the API:
- `Reviewer`: Procurement officers drafting and auditing tenders.
- `Curator`: Standard catalog maintainers submitting new rows and evidence.
- `Verifier`: Independent second-checkers approving verified standard rows.
- `Admin`: System operators configuring retention, users, and audit purges.

---

## 5. Data Retention and One-Click Deletion

Tender specifications often contain pre-publication procurement estimates and technical criteria:
- **Default Short Retention:** Configurable via `RETENTION_DAYS` (default 30 days; can be set to 7 days or 24 hours).
- **One-Click Deletion:** Officers can delete an entire draft audit and all parsed clauses at any time via `DELETE /api/v1/audits/{audit_id}`.
- **Automated Retention Purge:** Operators can trigger a purge of expired drafts via `POST /api/v1/audits/purge`.
- **Append-Only Audit Trail:** Deletions and purges are immutably recorded in the `audit_log` table with timestamps and user identifiers.

---

## 6. Copyright and Legal Posture (BIS Act 2016 s.10(5))

In strict accordance with Section 10(5) of the Bureau of Indian Standards Act, 2016:
- The product **never stores, pastes, summarises, or reproduces** the text of any Indian Standard.
- Only official metadata (standard numbers, parts, publication years, titles, and status) and direct links to official BIS portals are retained.
- Attached evidence references consist of screenshots of public catalogue search pages and Gazette orders, with no reproduction of standard technical bodies.
- All exported reports and user interfaces feature the mandatory disclaimer:
  *"This tool flags issues for the officer to review. It does not approve or reject a tender."*
