---
name: provenance-row-check
description: Validates seed and curated CSV rows for required provenance (source URL, verified date, verifier, evidence ref, distinct second checker) and rejects UNVERIFIED content. Use before loading seed data, before any pull request that touches packages/data/seed, when a curator adds rows, or when the coverage report is produced.
---

# Provenance row check

**Goal:** No row enters the data layer without source, date, verifier and a different second checker.

## Instructions
1. Run `python scripts/check_provenance.py packages/data/seed/*.csv`.
2. Read the per-row status: VERIFIED, AWAITING_SECOND_CHECK, or FAIL with the missing fields.
3. Report counts. Never fill a missing cell yourself; ask the user for the value.
4. Add `--require-verified` before a release or demo build so unchecked rows block the build.
5. File names must match a known table: standards, product_standard_map, certification_rules, allied_links.

## Constraints
- Do NOT invent URLs, dates or names to make a row pass.
- Do NOT load a row containing the text UNVERIFIED.
- Unknown values stay empty and trigger no claim.
