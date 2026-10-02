# Curator and Verification Handbook

Rule of the job: enter only what the official page shows. If it is not visible, leave it empty.

## Steps for every row
1. Open the official source: BIS catalogue record, BIS Scheme II page, or Gazette PDF.
2. Enter only visible facts. Empty cells stay empty. Never fill from memory or from a news report.
3. Attach evidence: URL, access date, and a saved copy or screenshot of the metadata area.
4. A second person re-checks the row against the source and records their name in `second_checked_by`. Same person twice is not allowed.
5. Run `python .agents/skills/provenance-row-check/scripts/check_provenance.py packages/data/seed/*.csv`.
6. Open a pull request. Reviewer confirms the source link opens.

## Evidence rules
- Screenshots show metadata (number, title, year, status, amendments list). Do not capture standard text. If a page shows text, crop it out.
- Never paste official text into any committed file. Use `private_notes/` (git-ignored) for working notes.
- Evidence files go to the object store, not Git.

## What stays UNVERIFIED until read from a primary source
CCTV listing under IS 13252 (Part 1), any migration date, any cement or concrete QCO detail, IS 302-1, IS 875 parts, IS 1893 (Part 1). See `open-verification.md`.

## Freshness
Rows older than `STALE_DAYS` show a stale tag on every finding that uses them (R14). A weekly job lists rows due. Re-verify from the source, update `verified_on`, and have a second person re-check.

## Conflicts
If two verified sources disagree, mark the row CONFLICT. Dependent findings become CANNOT_VERIFY until resolved.

## Adding a product family
Only where the certification list or catalogue can be read directly. Each family needs: product record with English and Hindi synonyms, primary standard, verified normative links, certification rule if the source lists one, and at least 10 test clauses. Cement only after the Gazette entries are read.
