# Tender Linter: Full Product Specification

Team OnFocus | Team ID 176283 | SIH 2026 | Problem Statement SIH26108
Planning basis: 1,000 engineering hours, no calendar limit.

---

## 0. How to read this document

- Everything here is a build target. The submitted deck may only describe what is built and verified at the time of submission.
- Anything marked **UNVERIFIED** is a fact nobody on the team has confirmed from a primary source. Do not ship it in the product or the deck until it is verified.
- No IS number, year, status, section number, link or statistic enters the product unless it exists as a source-linked row in the data layer (Section 3).

### Non-negotiable principles

1. **The LLM never decides.** It extracts. Rules decide. Every verdict is a lookup that a human can trace.
2. **Evidence or silence.** A finding without a source link and a verified date is not shown. A field we have not verified stays NULL and triggers no claim.
3. **Abstain by design.** "No applicable standard in our dataset" is a first-class output, not an error.
4. **Metadata, not text.** The product stores and shows numbers, titles, years, status, certification mapping and links. It never stores or reproduces standard text. Copyright in Indian Standards vests in BIS (BIS Act 2016, s.10(5), read directly by the team on 2 Oct 2026).
5. **Say what was measured.** Any accuracy figure is reported as "X of Y on test set Z", with Z described and its size stated.
6. **The officer stays in charge.** The tool flags and explains. It does not approve or reject a tender.

---

## 1. Purpose, users and scope

### Problem (from the official statement)
Procurement officials must reference the right Indian Standards in tender specifications. Tenders may omit relevant standards, reference outdated versions, or include incomplete technical requirements, which causes ambiguity, reduced quality and disputes.

### Product statement
Tender Linter audits a draft tender specification. It reads the standards the officer already cited, checks them against a curated, source-linked dataset, and reports line-level findings with evidence. It also recommends missing items only where the dataset has verified rows.

### Users
| Role | Need |
|---|---|
| Procurement officer (drafter) | Check a clause before publishing |
| Tender vetting reviewer | Fast, evidence-linked second check |
| Data curator (team or BIS-side maintainer) | Add and verify rows, keep them current |
| Administrator | Manage users, rules, retention, deployment |

### In scope
Text, PDF and DOCX input; English and Hindi first, then other Indian languages; rule-based audit with evidence; reviewer UI; exports; curation console; evaluation harness; deployment package.

### Out of scope (non-goals)
- Reproducing or summarising standard text.
- Legal advice or approval of tenders.
- Free-form "chat with the standards" answers.
- Cost estimation, vendor evaluation, bid scoring.
- Any claim of full catalogue coverage.

### Mapping to the six expected features of the statement
| Statement feature | Where it is met |
|---|---|
| 1. Accept descriptions, specifications, tender documents | Section 4 (ingestion) |
| 2. Recommend relevant IS by semantic understanding | Section 5 product mapping plus Section 6 rules R06 to R08, over verified rows only |
| 3. Identify allied standards | Table `allied_links`, rule R08, only where a link is verified |
| 4. Highlight latest version and amendments | Fields `year`, `status`, `superseded_by`, `amendments`, rules R02 to R04 |
| 5. Suggest mandatory certification | Table `certification_rules`, rules R05 and R06 |
| 6. Multilingual and natural language | Section 7 |

---

## 2. System architecture

```
 Browser (React)  <--HTTPS/JSON-->  API gateway (FastAPI)
                                       |
        +------------+-----------------+-----------------+--------------+
        |            |                 |                 |              |
   Ingestion    Extraction        Rules engine     Report service   Admin/curation
   service      service           (deterministic)  (render/export)  service
        |            |                 |                 |              |
        +------------+--------+--------+-----------------+--------------+
                              |
                    Data layer (SQLite for dev, PostgreSQL for production)
                    + object store for uploaded files and exports
                              |
                    Evaluation harness + CI (reads same rules and data)
```

### Technology choices
| Layer | Choice | Reason |
|---|---|---|
| Frontend | React with TypeScript | Team skill; strong span-highlighting libraries |
| Backend | Python 3.12, FastAPI, Pydantic v2 | Team skill; schema-validated I/O |
| Database | SQLite in development, PostgreSQL in production | Same SQL, easy local demo |
| Rules | Python, rules defined as data (YAML) plus code evaluators | Auditable, testable |
| Extraction model | Provider-agnostic interface; free-tier hosted providers first (Groq, Gemini or similar), chosen by bake-off | Section 16.4. Name the exact model and date on the deck. |
| OCR | Tesseract with Hindi and English language packs (evaluate alternatives) | Scanned tenders |
| Packaging | Docker Compose | One-command run; no sleeping free host for the demo |
| CI | GitHub Actions: lint, unit tests, rule tests, evaluation run | Regression safety |

---

## 3. Data layer

This layer is the product. Spend the most hours here.

### 3.1 Tables

**standards**
| Field | Type | Notes |
|---|---|---|
| id | integer | primary key |
| is_number | text | normalised form, e.g. `IS 302-2-25`; separate `part` and `section` columns where applicable |
| part | text, nullable | |
| title | text | as shown in the BIS catalogue |
| publication_year | integer, nullable | NULL if not verified |
| status | enum Active / Withdrawn / Superseded / UNKNOWN | UNKNOWN triggers no status claim |
| superseded_by_id | integer, nullable | foreign key |
| amendments | text, nullable | list as shown in catalogue; NULL if not verified |
| catalogue_url | text | official BIS catalogue record |
| verified_on | date | |
| verified_by | text | person |
| evidence_ref | text | screenshot or PDF stored in object store |

**products**
| Field | Notes |
|---|---|
| id, canonical_name | e.g. "Laptop / notebook / tablet" |
| synonyms_en, synonyms_hi, synonyms_other | JSON arrays; curated, not generated |
| family | grouping, e.g. IT equipment, household appliances |

**product_standard_map**
| Field | Notes |
|---|---|
| product_id, standard_id | |
| relation | enum PRIMARY / NORMATIVE / TEST_METHOD / TERMINOLOGY / INSTALLATION / RELATED |
| source_url, verified_on, verified_by, evidence_ref | mandatory |

**certification_rules**
| Field | Notes |
|---|---|
| product_id | |
| scheme | enum CRS / BIS_MARK / QCO / HALLMARKING / NONE_FOUND |
| specified_standard_id | the standard the scheme names for this product |
| instrument | order, notification or list entry as named in the source |
| source_url, verified_on, verified_by, evidence_ref | mandatory |
| effective_from, transition_until | nullable; only filled from a read source text |

**allied_links**: standard to standard links (normative reference, test method). Same provenance fields. Only rows read from an official source.

**vague_terms**: curated phrases per language (e.g. "ISI quality", "as per BIS") with a plain-language explanation. Curated by hand.

**audit_log** and **user** tables: Section 12.

### 3.2 Seed rows (verified by the team on 2 Oct 2026 unless marked)

| Product | Standard | Verified fact | Source | Open fields |
|---|---|---|---|---|
| Laptop, notebook, tablet | IS/IEC 62368 Part 1: 2023 | Listed by the BIS Scheme II registration page for these products | BIS Scheme II page | Catalogue status, superseded-by, amendments: NOT FOUND |
| Power adaptors for IT equipment | IS/IEC 62368 Part 1: 2023 | Same page | Same | Same |
| Microwave ovens | IS 302-2-25 | Listed on same page; title "Safety of household and similar electrical appliances: Part 2 Particular requirements: Section 25 Microwave ovens" | Same | Year, status, superseded-by, amendments: NOT FOUND |
| IT equipment (general) | IS 13252 (Part 1): 2010 | Catalogue page shows title "Information Technology Equipment - Safety Part 1: General Requirements (Second Revision)", year 2010, status Active, no superseded-by listed | BIS catalogue record | Amendments: NOT FOUND |

**UNVERIFIED, do not load as facts:**
- CCTV cameras under IS 13252 (Part 1): 2010 (reported from a 2021 Gazette Order; the order text and link have not been captured).
- A migration date of November 2028 from IS 13252 to IS/IEC 62368-1 (reported, text not captured).
- Any cement or concrete QCO details. Two notification numbers (S.O. 191(E) of 17 Feb 2003 and S.O. 5178(E) of 6 Dec 2023) were reported, and the relationship between them and the IS numbers they name was not read from the Gazette.
- IS 302-1 title, year and status.
- IS 875 parts and IS 1893 (Part 1) status.

### 3.3 Row verification workflow
1. Curator opens the official source (BIS catalogue record, Scheme II page, Gazette PDF).
2. Curator enters only what the page shows. Anything not visible stays NULL.
3. Curator attaches evidence: URL, access date, and a saved copy or screenshot.
4. A second person re-checks the row against the source. Two-person sign-off marks the row `verified`.
5. Rows older than a configurable age show a "stale" tag on every finding that uses them (rule R14).
6. A weekly job lists rows due for re-verification.
7. Every edit writes to the audit log with before and after values.

### 3.4 Coverage expansion plan
Order of expansion: finish the three seed families, then add families by this rule: only families where the certification list or the catalogue can be read directly. Each family needs: product record with synonyms in English and Hindi, primary standard, any verified normative links, certification rule, and 10 or more test clauses.
Report coverage honestly: "N products, M standards, verified as of date".

---

## 4. Ingestion service

| Input | Handling |
|---|---|
| Pasted text | Direct |
| DOCX | Parse paragraphs, numbered clauses, tables; keep paragraph ids for span mapping |
| Text PDF | Text extraction with layout order; keep page and offset |
| Scanned PDF or image | OCR; show OCR confidence; allow officer to correct text before audit |
| Multiple files | Batch queue, per-file report |

**Clause segmentation:** split on numbering (1., 1.1, (a)), table rows and sentence boundaries. Each clause gets an id, page, and character offsets. Every finding references a clause id and an offset range so the UI can highlight exactly.

**Language detection:** per clause (Devanagari, Latin, mixed). Mixed text is allowed.

**Limits:** file size, page count and rate limits configurable by administrator.

---

## 5. Extraction service

### 5.1 Contract
Input: one clause (or a window of clauses). Output must validate against this Pydantic schema or be rejected:

```json
{
  "clause_id": "c12",
  "language": "hi|en|mixed",
  "products": [
    {"text": "...", "span": [start, end], "canonical_product_id": null}
  ],
  "citations": [
    {"raw": "IS 13252 (Part 1): 2010", "span": [start, end],
     "is_number": "IS 13252", "part": "1", "year": 2010}
  ],
  "vague_phrases": [{"text": "ISI quality", "span": [start, end]}],
  "requirements": [{"text": "...", "span": [start, end]}]
}
```

### 5.2 Rules for the model call
- Temperature 0; fixed prompt version stored with every result.
- The prompt forbids inventing numbers. Output spans must be substrings of the input; any span that is not is dropped.
- No standard data is passed to the model. It sees only the clause.
- Result cache keyed by clause hash, prompt version and model version.
- Timeouts and retries with backoff; on failure fall back to 5.3.

### 5.3 Deterministic fallback and cross-check
- Regex library for citation patterns: `IS`, `IS/IEC`, `IS:`, parts, sections, year separators (`:`, `-`, `/`), Devanagari digits, and common typos. Maintained as tested data.
- The regex output always runs alongside the model output. Disagreements are surfaced to the officer as "extraction uncertain" rather than silently resolved.

### 5.4 Product mapping
- Step 1: exact and fuzzy match against curated synonyms (English and Hindi).
- Step 2: embedding similarity restricted to the products table, used only to propose a candidate.
- Step 3: a candidate is accepted only above a calibrated threshold; otherwise status is `UNMAPPED` and rule R10 (abstain) fires.
- The officer can confirm or change the product mapping in the UI; the choice is logged.

### 5.5 Model abstraction
A provider interface so the model can be swapped (hosted API, or a local model for restricted environments). Every model change reruns the evaluation harness before release.

---

## 6. Rules engine

Rules are data plus small evaluators. Each rule has an id, severity, input conditions, message template (English and Hindi), required evidence fields, and unit tests. Rule changes are versioned; every report records the rule set version.

### 6.1 Severity
`ERROR` (cited standard conflicts with a verified source), `WARNING` (probable omission), `INFO` (style or clarity), `CANNOT_VERIFY` (data missing, no claim made).

### 6.2 Rule catalogue
| ID | Name | Fires when | Severity | Evidence shown |
|---|---|---|---|---|
| R01 | Unknown citation | Cited IS number not in `standards` | CANNOT_VERIFY | none; says "not in dataset" |
| R02 | Superseded or withdrawn | Row status is Withdrawn or Superseded **and** the row is verified | ERROR | catalogue record link, verified date |
| R03 | Year differs | Cited year differs from the row's verified year | WARNING | catalogue link; says which year the catalogue shows |
| R04 | Part or section mismatch | Cited part or section absent or different from the verified row | WARNING | catalogue link |
| R05 | Differs from certification list | Product has a certification rule naming standard X, clause cites Y | ERROR | certification source link, instrument name |
| R06 | Certification not mentioned | Product has a certification rule and the clause never mentions it | WARNING | certification source link |
| R07 | No standard cited | Product mapped, clause cites nothing | WARNING | product-standard map link |
| R08 | Allied standard absent | Verified `allied_links` exist from the cited standard, none cited | INFO | link row source |
| R09 | Vague wording | Phrase found in `vague_terms` | INFO | explanation |
| R10 | Abstain | Product unmapped or no rows exist | CANNOT_VERIFY | "No applicable standard in our dataset" |
| R11 | Internal contradiction | Same standard cited with two different years or parts in one document | WARNING | both clause locations |
| R12 | Malformed citation | Citation pattern near-matches a known number (typo) | INFO | suggested candidate, needs confirmation |
| R13 | Wrong product family | Cited standard is linked to a different product in the map | WARNING | map source link |
| R14 | Stale row | Any used row exceeds the freshness limit | INFO | shows verified date |

### 6.3 Wording rules (important)
- Never say "outdated" or "withdrawn" unless R02 fires from a verified status.
- For R05 the message is: "The certification list specifies [standard] for this product. This clause cites [other]." It makes no claim about the cited standard's catalogue status.
- Every message states the verified date and links the source.
- CANNOT_VERIFY findings are shown in a separate, visually quiet group.

### 6.4 Conflict handling
When two verified sources disagree, the row is flagged `CONFLICT`, findings that depend on it are downgraded to CANNOT_VERIFY, and the curator is notified.

---

## 7. Multilingual support

1. **Hindi first, in the same pipeline.** The model extracts directly from the source-language clause. The product mapping uses curated Hindi synonyms. Rule messages exist in English and Hindi.
2. **Span integrity.** Highlights always point to the original-language text. The English summary is a rendering, not a replacement.
3. **Numerals and scripts.** Normalise Devanagari digits, full-width characters and common transliterations of "IS".
4. **Bilingual report.** The exported report shows the original clause with both language explanations.
5. **Expansion.** Add one language at a time. Each needs: curated synonyms, vague-phrase list, message translations reviewed by a fluent speaker, and a test set of at least 30 clauses.
6. **Quality gate.** Per-language extraction scores are reported separately. A language is labelled "supported" only after its measured results meet the team's published threshold.

---

## 8. Reviewer user interface

### Screens
1. **Upload / paste**: text box, file drop, language hint, product hint (optional).
2. **Audit view**: left, original document with highlighted spans; right, finding cards grouped by severity; top bar with counts and rule set version.
3. **Finding card**: title, plain explanation, evidence link, verified date, "Accept", "Dismiss with reason", "Not applicable".
4. **Evidence drawer**: row fields, source URL, access date, evidence image, history of the row.
5. **Extraction panel**: shows what the model and regex extracted, editable. Edits re-run the rules instantly.
6. **Product confirmation**: shows mapped product with alternatives.
7. **Report preview and export**: PDF, DOCX, JSON, CSV of findings.
8. **History**: previous audits, version diff (what changed between two drafts).
9. **Settings**: language, text size, contrast mode, keyboard shortcuts.

### Behaviour requirements
- A finding is never shown without its evidence link, except CANNOT_VERIFY items, which show the reason.
- Highlight fallback: if a span cannot be located, the finding still appears in the sidebar with the clause reference.
- Fully keyboard-operable; screen-reader labels; colour is never the only signal.
- Works at low bandwidth; no external fonts or scripts required at runtime.
- Clear banner: "This tool flags issues for the officer to review. It does not approve or reject a tender."

---

## 9. API specification

Base path `/api/v1`. JSON over HTTPS. All write endpoints require auth.

| Method and path | Purpose |
|---|---|
| POST `/audits` | Create audit from text or file id; returns audit id |
| GET `/audits/{id}` | Status, clauses, extractions, findings |
| POST `/audits/{id}/extractions/{clause}` | Officer edits extraction; triggers re-evaluation |
| POST `/audits/{id}/findings/{fid}/decision` | Accept, dismiss, not applicable, with reason |
| GET `/audits/{id}/report?format=pdf|docx|json|csv` | Export |
| GET `/audits/{a}/diff/{b}` | Compare two drafts |
| GET `/standards`, `/standards/{id}` | Read data (public metadata only) |
| GET `/products`, `/products/{id}/rules` | Product, standards, certification mapping |
| POST `/admin/rows`, PATCH `/admin/rows/{id}` | Curation (admin role) |
| POST `/admin/rows/{id}/verify` | Second-person sign-off |
| GET `/admin/stale` | Rows due for re-verification |
| GET `/health`, `/version` | Liveness; model, prompt and rule set versions |

Finding object:
```json
{
  "id": "f7", "rule_id": "R05", "severity": "ERROR",
  "clause_id": "c12", "span": [34, 56],
  "message_en": "...", "message_hi": "...",
  "evidence": {"url": "...", "verified_on": "2026-10-02", "row_id": 41},
  "rule_set_version": "1.0.0", "model_version": "...", "prompt_version": "..."
}
```

---

## 10. Admin and curation console

- Row editor with required provenance fields; save is blocked without a source URL and date.
- Side-by-side view: the saved row and the pasted official source text (kept only as a private working note, never exported or shown to reviewers).
- Two-person verification queue.
- Bulk import from a CSV of the team's own curated rows, with validation report.
- Staleness dashboard and reminders.
- Conflict queue.
- Rule editor for message templates and `vague_terms`, with automatic test run before publishing.
- Full audit log, filterable.

---

## 11. Integrations (optional, build after core)

- **Procurement portal adapter:** an interface that receives a draft specification and returns the findings. Access terms and technical interfaces of any specific portal are **UNVERIFIED**; build against a generic adapter and a webhook, and confirm access before naming any portal.
- **Browser or word-processor plug-in:** a thin client that calls the same API.
- **CLI:** batch audits for a folder of drafts, outputs JSON.
- **Official-data sync:** if BIS or MeitY expose a lawful data feed, replace manual row entry for the covered fields. Not assumed to exist.

---

## 12. Security, privacy, compliance

- Tender drafts can be confidential. Default retention is short, configurable per deployment, with one-click deletion.
- Roles: Reviewer, Curator, Verifier, Admin. Verifier cannot be the same person as the Curator for a row.
- Authentication with hashed passwords and optional institutional single sign-on.
- Encryption in transit; encryption at rest for uploads.
- Model data handling: documents sent to a hosted model are limited to the clause text needed. Provide a local-model deployment option for restricted environments.
- No standard text stored. The evidence images attached to rows are metadata screenshots; review them for any standard text before storing.
- Rate limiting, input size limits, upload scanning, dependency scanning in CI.
- Audit log is append-only.
- Legal posture: the product shows public metadata and links to official pages; confirm the final wording with a qualified person before publication.

---

## 13. Quality and evaluation

### 13.1 Test corpus
- **Synthetic set:** clauses written by the team with planted defects, one defect type per clause and mixed ones. Each defect has an expected rule id. Declared as synthetic everywhere it is reported.
- **Real public tenders:** include only if lawfully obtained and permitted for use; otherwise do not use. Never imply a synthetic result applies to real tenders.
- **Clean controls:** clauses with no defects, to measure false alarms.
- **Hindi and mixed-language set:** separate.
- **Adversarial set:** typos, odd separators, scans with noise, standards cited by title only.
- Labelling by one person, reviewed by a second.

### 13.2 Metrics
| Metric | Definition |
|---|---|
| Extraction recall and precision | Citations and products found vs labelled, per language |
| Rule recall | Planted defects caught |
| False alarm rate | Findings on clean controls |
| Abstain correctness | Share of out-of-dataset products that triggered R10 |
| Latency | p50 and p95 per clause and per document |
| Evidence completeness | Findings with link and verified date (target: all) |

### 13.3 Reporting rule
Publish only "X of Y on test set Z (size, type, language)". No percentages without the counts. Re-run on every release and keep the history.

### 13.4 Regression gates in CI
Unit tests for every rule; golden-file tests for extraction (with a mocked model); a full evaluation run before any rule, prompt or model change merges; a release is blocked if any previously passing planted defect is missed.

### 13.5 Human review
Monthly sample of real audits reviewed by a person who did not build the rule; disagreements become new tests.

---

## 14. Operations

- Docker Compose for local and demo; a container deployment for production.
- Demo hosting must not sleep. Test the public link from a cold device before submission day.
- Structured logs, request tracing with ids, error alerts, health checks.
- Backups of the database and evidence store with a tested restore.
- Environment configuration separate from code; secrets in a secret store.
- Versioning: semantic versions for the app, rule set, prompt and data snapshot; each report records all four.
- Database migrations tracked and reversible.
- Basic load test at the expected concurrent users.

---

## 15. Documentation and submission assets

- README with one-command run and a sample audit.
- Data dictionary and verification handbook for curators.
- Rule catalogue page generated from the rule data.
- Architecture diagram with only the components that exist.
- Demo script, demo video, and a screenshot set taken from the real running system.
- Deck consistency check: every claim on a slide must map to a built feature or a verified fact in this file. Remove the rest.

---

## 16. Build plan (1,000 hours)

This section replaces the earlier allocation table. It is the working plan for the whole build.

### 16.1 Definition of done (every milestone)
- Merged by pull request and reviewed by a second person.
- Tests pass in CI. New rule or extraction behaviour has its own tests.
- README, data dictionary or rule catalogue updated.
- Nothing in the product or deck claims more than was measured or verified.
- The demo path still runs from a clean machine.

### 16.2 Roles (six people; map to your real team)
| Role | Owns |
|---|---|
| Data lead | Schema, curation, verification workflow, evidence |
| Rules and backend lead | Rules engine, API, auth, storage |
| Extraction lead | Provider adapter, prompts, regex, product mapping, Hindi |
| Frontend lead | Reviewer UI, curation console UI, accessibility |
| Evaluation lead | Test corpus, metrics, CI gates, reporting |
| Integration and docs lead | Ingestion, exports, deployment, demo, deck, submission pack |

Each milestone has one owner and one reviewer who is not the owner.

### 16.3 Repository layout
```
tender-linter/
  apps/web/            React + TypeScript
  apps/api/            FastAPI app, routers, auth
  packages/data/       schema, migrations, seed CSVs, loaders
  packages/rules/      rule data (YAML), evaluators, templates (en, hi)
  packages/extraction/ provider adapter, prompts, regex, mapping
  eval/                corpus, runner, reports (versioned)
  docs/                data dictionary, verification handbook, rule catalogue
  infra/               docker-compose, CI workflows, deployment files
  .env.example         every variable, no secrets
```
Conventions: Python with type hints and a formatter and linter in CI; TypeScript strict mode; pinned dependency lockfiles; conventional commit messages; main branch protected.

### 16.4 LLM provider plan

**Position.** Free providers can change models, limits and terms without notice. The product depends on an interface, not on one provider. The provider is chosen by a measured bake-off on your own test set, not by reputation.

**16.4.1 Adapter interface**
```python
class Extractor(Protocol):
    name: str            # provider label
    model_id: str        # exact model string, recorded in every result
    def extract(self, clause: str, language_hint: str | None) -> ExtractionResult: ...
```
Config per provider: base URL, model id, API key variable name, timeout, max retries, requests-per-minute limit, daily request cap, structured-output mode (on or off).

**16.4.2 Candidates**
Groq, Gemini, and any other free-tier provider the team can access. Do not rely on any figure about limits, model names, languages or terms until you have read the provider's current documentation (use the fact-gathering prompt in 16.4.8).

**16.4.3 Bake-off protocol**
1. Freeze a test set: at least 60 clauses (English, Hindi, mixed), 10 clean controls, 10 adversarial (typos, odd separators, citation by title only). Use the synthetic matrix in 16.7 as the core.
2. Run each candidate three times per clause at temperature 0.
3. Record per candidate:
   - valid-schema rate
   - citation recall and precision
   - product-span correctness
   - invented-citation count (any span not found in the input)
   - Hindi results reported separately
   - repeatability (same output across the three runs)
   - latency p50 and p95
   - rate-limit errors and how they surface
4. Save raw outputs and the report in `eval/reports/` with the date and exact model ids.

**16.4.4 Selection rule**
1. Reject any candidate with one or more invented citations on the frozen set.
2. Among the rest, pick the highest citation recall.
3. Tie-break on Hindi results, then repeatability, then latency.
4. Keep the second-best as the fallback provider.
5. Record the chosen model id and the bake-off date on the deck.

**16.4.5 Operating rules for free tiers**
- Client-side rate limiter (token bucket) set below the provider's published limit.
- Daily request counter with a hard stop and a clear message when the cap is near.
- Retry with exponential backoff and jitter; circuit breaker after repeated failures.
- Fallback chain: primary provider, secondary provider, regex-only mode (the UI shows "extraction in reduced mode").
- Cache every result by clause hash, prompt version and model id.
- One call per clause by default. Test batching only after the bake-off, and only if span accuracy holds.
- Demo day: pre-warm the cache for the demo clauses and keep the regex-only mode working as the safety net.

**16.4.6 Privacy**
Free tiers may handle submitted text differently from paid plans. Check each provider's data-use terms before sending anything. Until verified, send only synthetic or public text. Real tender drafts need a verified policy or a local model.

**16.4.7 Prompt skeleton (store as a versioned file)**
```
You extract structured data from one tender clause. Output JSON only, matching the schema.
Rules:
- Copy citation text exactly as written. Never correct, complete or invent an IS number, part or year.
- If a field is absent, return null or an empty list.
- Report phrases that name quality or standards without a number (for example "ISI quality") under vague_phrases.
- Return character spans that are exact substrings of the clause.
- The clause may be in Hindi, English or both. Do not translate the spans.
```
Add 6 to 10 worked examples (English, Hindi, mixed, no-citation, typo). Examples are synthetic.

**16.4.8 Fact-gathering prompt (paste into a search-enabled chat)**
```
You are a researcher. Use only each provider's official documentation, pricing page and terms. Do not rely on memory. If a fact is not on an official page, write NOT FOUND. No em dashes.
Providers: Groq, Google Gemini (AI Studio / Gemini API), plus any other provider that has a free API tier today.
For each provider give: free tier available (yes/no); model names currently offered on it; requests per minute and per day and tokens per minute limits for each model I could use; whether JSON or structured output is supported; documented support for Hindi; whether free-tier inputs may be used to improve models or retained, quoting at most 15 words; any stated deprecation dates; sign-up requirements for students in India; the page URL and access date for each fact.
Finish with a table, then list everything you could not verify.
```

### 16.5 Environments and configuration
| Environment | Purpose | Data |
|---|---|---|
| dev | Local work | Seed CSVs, synthetic clauses |
| test | CI | Fixtures, mocked provider |
| demo | Judges and screenshots | Seed data, cache pre-warmed, fixed rule set version |
| prod | Pilot (later) | Verified rows, retention policy active |

Variables in `.env.example`: `DATABASE_URL`, `OBJECT_STORE_PATH`, `PROVIDER_PRIMARY`, `PROVIDER_SECONDARY`, `MODEL_ID_PRIMARY`, `MODEL_ID_SECONDARY`, `PROVIDER_PRIMARY_KEY`, `PROVIDER_SECONDARY_KEY`, `RATE_LIMIT_RPM`, `DAILY_CAP`, `STALE_DAYS`, `RETENTION_DAYS`, `JWT_SECRET`, `ALLOWED_ORIGINS`, `LOG_LEVEL`. Secrets never enter the repo; CI runs a secret scan.

### 16.6 Milestones

| # | Milestone | Hours | Depends on |
|---|---|---|---|
| M0 | Foundation | 25 | none |
| M1 | Data model and provenance enforcement | 50 | M0 |
| M2 | Seed data curation and verification | 90 | M1 |
| M3 | Rules engine and rule tests | 95 | M1 |
| M4 | Extraction service | 85 | M0 |
| M5 | Product mapping and normalisation | 35 | M2, M4 |
| M6 | Backend API, auth, storage, audit log | 65 | M1, M3 |
| M7 | Reviewer UI core | 95 | M6 |
| M8 | Evaluation harness and corpus v1 | 65 | M3, M4 |
| M9 | Hindi pipeline and quality gate | 80 | M4, M8 |
| M10 | Ingestion (DOCX, text PDF, OCR) | 55 | M6 |
| M11 | Exports, history, diff | 35 | M7 |
| M12 | Curation console, verification queue, staleness, conflicts | 65 | M6 |
| M13 | Coverage expansion | 55 | M2, M12 |
| M14 | Security, privacy, legal review | 30 | M6 |
| M15 | Deployment, observability, load test | 40 | M6 |
| M16 | Documentation, demo, submission pack | 35 | all |
| | **Total** | **1,000** | |

**M0 Foundation (25 h).** Create repo and layout; CI with lint, type check, tests, secret scan; Docker Compose with API, web and database; coding conventions; pull request template; issue labels.
Done when: a new member runs one command and sees a health page.

**M1 Data model and provenance (50 h).** Implement tables from Section 3; migrations; constraints that block saving a row without source URL, verified date and verifier; audit log triggers; loader for CSV seed files; data dictionary draft.
Done when: inserting a row without provenance fails in tests.

**M2 Seed data curation (90 h).** For each seed product: open the official page, record only what is visible, attach evidence, second-person check. Close the open items in Section 17 (IS 302-2-25 year and status, IS/IEC 62368-1 catalogue status, IS 13252 amendments, IS 302-1). Add English and Hindi synonyms for each product, and the first `vague_terms` list. Read the Gazette entries for CCTV and cement before adding either.
Done when: every seed row is verified by two people or is marked UNKNOWN, and a coverage report prints counts and dates.

**M3 Rules engine (95 h).** Rule data format (YAML); evaluators for R01 to R14; message templates in English and Hindi; severity and grouping; rule set versioning; conflict handling; unit tests per rule using hand-written extraction objects (no model).
Done when: the synthetic matrix in 16.7 passes with mocked extractions.

**M4 Extraction service (85 h).** Provider adapter and two provider implementations; schema validation; span validation (drop spans not in input); regex library with tests; cross-check logic; cache; rate limiter, retry, circuit breaker; reduced mode; prompt files with versions; the bake-off in 16.4.3.
Done when: the bake-off report exists and the primary and fallback providers are chosen by the selection rule.

**M5 Product mapping and normalisation (35 h).** IS-number normaliser; synonym matcher; embedding candidate step; threshold calibration on the test set; officer confirmation hook.
Done when: out-of-dataset products reliably end as UNMAPPED on the test set, with the count reported.

**M6 Backend API (65 h).** Endpoints from Section 9; roles and auth; file storage; background jobs for long audits; audit log; request tracing; contract tests; OpenAPI document.
Done when: the full audit flow works through the API with tests.

**M7 Reviewer UI core (95 h).** Upload and paste; audit view with span highlighting; finding cards; evidence drawer; extraction editor with live re-run; product confirmation; sidebar fallback when a span cannot be placed; accessibility pass (keyboard, labels, contrast); responsive layout.
Done when: a reviewer can complete the T01 to T13 matrix in the browser without help.

**M8 Evaluation harness (65 h).** Corpus format; runner; metrics from Section 13; report generator; CI gate that blocks regressions; test corpus v1 (the 16.7 matrix expanded to at least 60 clauses).
Done when: one command prints "X of Y" results with the corpus description.

**M9 Hindi pipeline (80 h).** Hindi synonyms and vague terms; Devanagari digit normalisation; Hindi rule messages reviewed by a fluent speaker; Hindi test set of at least 30 clauses; per-language metrics; quality gate that labels a language "supported" only after the published threshold is met.
Done when: Hindi results are reported separately and the UI shows the language status.

**M10 Ingestion (55 h).** DOCX parser; text PDF parser; OCR path with confidence display and editable text; clause segmentation; offsets mapping back to the original file; batch queue.
Done when: sample DOCX, PDF and a scanned page all produce the same findings as pasted text on the same content (or show the OCR differences).

**M11 Exports, history, diff (35 h).** PDF, DOCX, JSON, CSV exports; bilingual report layout; version history; diff between two drafts.
Done when: an exported report opens correctly and every finding includes its evidence link and date.

**M12 Curation console (65 h).** Row editor with required provenance; two-person verification queue; bulk CSV import with validation report; stale-row dashboard; conflict queue; rule and vague-term editor with auto tests.
Done when: a new row can go from entry to verified without touching the database directly.

**M13 Coverage expansion (55 h).** Add product families one at a time using Section 3.4. Each family needs verified rows, English and Hindi synonyms, certification rule if the source lists one, and at least 10 test clauses. Cement only after the Gazette entries are read.
Done when: the coverage report shows the new counts and the evaluation run includes the new families.

**M14 Security and legal (30 h).** Roles and permission tests; retention and deletion; upload scanning; dependency scan; review of all stored evidence for any standard text; legal review of wording and disclaimers by a qualified person.
Done when: the checklist in Section 12 is signed off.

**M15 Deployment and operations (40 h).** Production containers; always-on hosting for the demo (cold-start test from a fresh device); logs, tracing, alerts; backup and tested restore; basic load test.
Done when: the public demo link opens instantly after a day of inactivity.

**M16 Documentation and submission pack (35 h).** README; curator handbook; rule catalogue page; architecture diagram of built components only; demo script and video; screenshots from the running system; deck updates from the real results; consistency check of every slide claim against this file.
Done when: every slide claim maps to a built feature or a verified fact.

### 16.7 Synthetic test matrix (core of the corpus)
All clauses are written by the team and labelled synthetic. Expected rules assume the seed rows in Section 3.2.

| ID | Clause idea | Expected |
|---|---|---|
| T01 | Laptops cite IS 13252 (Part 1): 2010, no CRS mention | R05, R06 |
| T02 | Laptops cite IS/IEC 62368 Part 1: 2023, no CRS mention | R06 only |
| T03 | Laptops cite IS/IEC 62368 Part 1 with a different year | R03 |
| T04 | Microwave ovens cite IS 302-2-25, no CRS mention | R06 |
| T05 | Microwave ovens, no standard cited | R07 |
| T06 | "ISI quality" wording | R09 |
| T07 | A product not in the dataset | R10 |
| T08 | An IS number not in the dataset | R01 |
| T09 | Same standard cited with two different years | R11 |
| T10 | A one-digit typo in a known IS number | R12 |
| T11 | Microwave clause citing the IT equipment standard | R13 (and R05 if the rule applies) |
| T12 | Hindi laptop clause citing IS 13252 (Part 1) | R05 in Hindi, span on original text |
| T13 | Clean laptop clause with the right standard and CRS mentioned | no findings |

Expand each into several variants (different wording, separators, numerals, languages).

### 16.8 Release and quality gates
- All rule tests and the evaluation run pass; no previously caught planted defect is missed.
- Invented-citation count on the corpus is zero.
- Every finding in a sample of 50 has a working source link and a verified date.
- Rule set, prompt, model and data snapshot versions are printed in the report footer.
- Accessibility check on the three main screens.
- Backup restore tested.

### 16.9 Risk register
| Risk | Effect | Response |
|---|---|---|
| Free-tier limits or terms change | Extraction stops | Adapter, fallback provider, regex-only mode, cache |
| Free-tier data terms unsuitable | Privacy problem | Synthetic or public text only until verified; local model option |
| Curated rows wrong | Wrong findings | Two-person check, evidence, stale tags, UNKNOWN stays silent |
| Hindi quality below threshold | Overclaim | Quality gate; do not label "supported" |
| Span mapping fails on DOCX or PDF | Highlights misplaced | Sidebar fallback; offset tests |
| Team overload | Missed milestones | Owner plus reviewer per milestone; cut M13 first |
| Demo host sleeps or fails | Blank page for evaluators | Always-on hosting, cold-start test, recorded video as backup |
| Deck claims outrun the build | Credibility loss | Consistency check in M16 |

### 16.10 Submission pack checklist
- Team ID, theme and category copied from the portal page.
- No placeholder text, no notes to self, exactly six slides, PDF upload.
- Exact model name and bake-off date on the technical slide.
- One measured number with its working shown (counts and test set description).
- Source links open; verified dates shown.
- Demo link tested from a cold device; video link tested.
- Deadline confirmed with the portal and the college SPOC.

---

## 17. Open verification items (owner: team)

| Item | Needed from |
|---|---|
| Final submission deadline and any extension | Portal and college SPOC |
| Current free-tier limits, models, Hindi support and data terms per provider | Fact-gathering prompt in 16.4.8 |
| Team ID is 176283 (supplied). Still confirm exact theme and category as shown on the portal | Portal statement page |
| IS 302-2-25: year, status, newer edition | BIS catalogue record |
| IS/IEC 62368-1: catalogue status, amendments | BIS catalogue record |
| IS 13252 (Part 1) amendments; CCTV listing and any migration date | Gazette order text and link |
| IS 302-1 | BIS catalogue record |
| Cement QCO: which order is current, which IS numbers it names | Gazette entries |
| Exact model name and version used for extraction | Bake-off result (16.4.3), then record model id and date |
| One measured impact number with its working | Evaluation harness output |
| Whether any procurement portal permits integration | Portal operator |
