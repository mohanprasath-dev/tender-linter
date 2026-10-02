# Build Prompts (paste one per milestone into Antigravity)

Every prompt starts with this preamble:

```
Follow GEMINI.md. Read docs/PROJECT_SPEC.md section(s) listed below first. Work only on this milestone. Write tests first. Stop at "Done when" and report what you built, what you tested, and anything you could not verify. Ask me if a fact is missing. No em dashes.
```

## M0 Foundation (25 h)
Spec: 16.1, 16.3, 16.5, 14. Task: set up repo layout, CI (lint, type check, tests, secret scan), Docker Compose with api, web and database, conventions, PR template, labels. Done when: a new member runs one command and sees a health page.

## M1 Data model and provenance (50 h)
Spec: 3.1, 12. Task: implement tables with migrations; constraints that block saving a row without source URL, verified date, verifier and evidence ref; second_checked_by must differ from verified_by; audit log triggers; CSV seed loader that runs the provenance-row-check skill logic. Done when: inserting a row without provenance fails in tests.

## M2 Seed data curation (90 h)
Spec: 3.2, 3.3, 17. Task: build the curator workflow around `packages/data/seed/*.csv`; do not invent any value. List which cells I must fill from official pages and stop. Done when: every seed row is verified by two people or marked UNKNOWN, and a coverage report prints counts and dates.

## M3 Rules engine (95 h)
Spec: 6, 16.7. Task: load `packages/rules/rules.yaml`; evaluators R01 to R14; EN and HI templates (HI stays null until a fluent speaker reviews); severity grouping; rule set versioning; conflict handling. Use the rule-author skill. Tests use hand-written extractions. Done when: the synthetic matrix in `eval/corpus/synthetic-v1.csv` passes with mocked extractions. Ask me about each item in `docs/open-verification.md` section B before coding it.

## M4 Extraction service (85 h)
Spec: 5, 16.4. Task: Extractor protocol, two provider adapters, Pydantic schema validation, span validation (use span-validator logic), regex library (use is-number-normaliser logic), cross-check, cache, rate limiter, retry, circuit breaker, reduced mode, versioned prompt files, bake-off runner. Done when: bake-off report exists and primary and fallback are chosen by the selection rule.

## M5 Product mapping (35 h)
Spec: 5.4. Task: IS normaliser, synonym matcher, embedding candidate step restricted to products table, calibrated threshold, officer confirmation hook. Done when: out-of-dataset products end as UNMAPPED on the test set, count reported.

## M6 Backend API (65 h)
Spec: 9, 12. Task: endpoints, roles, auth, file storage, background jobs, audit log, request tracing, contract tests, OpenAPI. Done when: full audit flow works through the API with tests.

## M7 Reviewer UI core (95 h)
Spec: 8. Task: upload and paste, audit view with span highlighting, finding cards, evidence drawer, extraction editor with live re-run, product confirmation, sidebar fallback, accessibility, responsive. No external fonts or scripts. Banner text exact. Done when: a reviewer completes T01 to T13 in the browser without help.

## M8 Evaluation harness (65 h)
Spec: 13. Task: corpus format, runner, metrics, report generator (use eval-report skill), CI gate that blocks regressions, corpus v1 expanded to at least 60 clauses. Done when: one command prints "X of Y" results with the corpus description.

## M9 Hindi pipeline (80 h)
Spec: 7. Task: Hindi synonyms and vague terms, Devanagari digit normalisation, per-language metrics, quality gate. Hindi messages need a fluent reviewer. Done when: Hindi results are reported separately and UI shows language status.

## M10 Ingestion (55 h)
Spec: 4. Task: DOCX parser, text PDF parser, OCR with confidence and editable text, clause segmentation, offset mapping, batch queue. Done when: DOCX, PDF and a scanned page give the same findings as pasted text (or show OCR differences).

## M11 Exports, history, diff (35 h)
Spec: 8, 9. Task: PDF, DOCX, JSON, CSV exports, bilingual layout, version history, diff. Done when: an exported report opens and every finding has its evidence link and date.

## M12 Curation console (65 h)
Spec: 10. Task: row editor with required provenance, two-person queue, bulk CSV import with validation report, stale dashboard, conflict queue, rule and vague-term editor with auto tests. Done when: a row goes from entry to verified without touching the database.

## M13 Coverage expansion (55 h)
Spec: 3.4. Task: add one product family at a time, only where the source can be read. Done when: coverage report shows new counts and evaluation includes the family. Cement only after Gazette entries are read.

## M14 Security and legal (30 h)
Spec: 12. Task: work through `docs/security-legal-checklist.md`. Done when: the checklist is signed off.

## M15 Deployment (40 h)
Spec: 14. Task: production containers, always-on hosting, logs, tracing, alerts, backup and tested restore, load test. Done when: the public demo link opens instantly after a day of inactivity.

## M16 Documentation and submission (35 h)
Spec: 15, 16.10. Task: README, handbook, rule catalogue generated from rules.yaml, architecture diagram of built parts only, demo script and video, screenshots, deck consistency check (deck-claim-check skill). Done when: every slide claim maps to a built feature or verified fact.
