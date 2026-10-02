# Tender Linter: always-on rules for the coding agent

Project: Tender Linter (SIH 2026, Team OnFocus). Source of truth: `docs/PROJECT_SPEC.md`.
Read the spec section for the milestone you are working on before writing code.

## Hard rules
1. The LLM only extracts. Verdicts come from deterministic rules over database rows.
2. No IS number, year, status, section number, link or statistic enters code, data, docs or the deck unless it exists as a source-linked row in the data layer.
3. Anything marked UNVERIFIED in the spec stays out of product and deck. Unknown fields stay NULL and trigger no claim.
4. Never store, paste, summarise or reproduce text of any Indian Standard. Metadata and links only.
5. Never write "outdated" or "withdrawn" in a message unless rule R02 fires from a verified status.
6. Report accuracy only as "X of Y on test set Z". No bare percentages.
7. The tool never approves or rejects a tender. Keep the banner text in the UI.
8. The repo is PUBLIC. Never commit secrets, keys, evidence screenshots, uploaded tenders, private notes, or any standard text. Check every diff for these before committing.
9. Do not use em dashes in any copy, docs, prompts or messages.

## Working rules
- One milestone at a time (M0 to M16). Stop at "done when" and report.
- Every change goes through a pull request with tests. New rule or extraction behaviour needs its own tests.
- Rule tests use hand-written extraction objects, never a live model.
- Python 3.12 with type hints, ruff, pytest. TypeScript strict. Lockfiles pinned. Conventional commits.
- Secrets never enter the repo. Add new variables to `.env.example` without values.
- Ask before any destructive action (drop table, delete files, force push, reset --hard).
- If a fact is missing, ask the user. Do not fill it in.

## Skills (in `.agents/skills/`)
is-number-normaliser, provenance-row-check, span-validator, rule-author, eval-report, deck-claim-check.

## Workflows (in `.agents/workflows/`)
start-milestone, release-gate, demo-day.
