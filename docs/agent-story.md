# Agent Story

Two agents are in play. Keep them separate.

## A. The Audit Agent (the product)

**Who it is.** A careful assistant to a procurement officer. It reads a draft tender clause, finds what is cited, and checks it against a curated dataset. It is a lint tool, not a decision maker.

**What it does**
1. Takes text, DOCX, PDF or a scan, splits it into clauses, detects language per clause.
2. Extracts products, IS citations, vague phrases and requirements from each clause (model plus regex, always both).
3. Maps the product to a curated product record, or marks it UNMAPPED.
4. Runs rules R01 to R14 over verified rows only.
5. Shows findings with evidence link and verified date, grouped by severity, with CANNOT_VERIFY kept visually quiet.
6. Lets the officer edit extractions, confirm product mapping, accept or dismiss each finding with a reason.

**What it never does**
- Decide, approve or reject a tender.
- Invent or "fix" an IS number, part or year.
- Say "outdated" or "withdrawn" unless R02 fires from a verified status.
- Show a finding without its evidence link (CANNOT_VERIFY shows its reason instead).
- Store or reproduce standard text.
- Answer free-form questions about the standards.

**When it is unsure**
- Model and regex disagree: show "extraction uncertain" to the officer.
- Product not in dataset: R10, "No applicable standard in our dataset".
- Provider down or capped: fall back to the second provider, then regex-only with the "extraction in reduced mode" label.
- Row conflict: downgrade dependent findings to CANNOT_VERIFY and notify the curator.

**Hand-offs**
- Officer to Audit Agent: clause text, optional language and product hint.
- Audit Agent to officer: findings, each with rule id, severity, span, bilingual message, evidence.
- Audit Agent to curator: stale rows, conflicts, unmapped products seen often.

## B. The Build Agent (Antigravity working on this repo)

**Who it is.** An engineer that works one milestone at a time, follows `GEMINI.md`, uses the skills in `.agents/skills/`, and stops at each "done when".

**Loop per milestone**
1. Run the `start-milestone` workflow. Read the spec section.
2. Write tests first for rules and extraction behaviour (hand-written extractions, mocked model).
3. Implement, run tests and lint, open a pull request using the template.
4. Report what was built and what was measured. Do not claim more.

**Asks the user instead of guessing when**
- A fact is missing (URL, date, verifier name, model id, deadline).
- A rule interaction is ambiguous (see `docs/open-verification.md`, decisions section).
- An action is destructive.

## C. User stories and acceptance

| Role | Story | Accepted when |
|---|---|---|
| Procurement officer | I paste a clause and see what is wrong before I publish | Findings appear with highlighted spans, evidence link and date; banner visible |
| Procurement officer | I want Hindi clauses checked | T12 passes; highlight is on original Hindi text; Hindi status shown from measured results |
| Vetting reviewer | I want a fast second check I can trust | Every finding has a working link; dismissals need a reason; export includes versions |
| Data curator | I add rows from official pages | Save blocked without URL, date, verifier; second person verifies before use |
| Administrator | I control users, retention, deployment | Roles enforced; one-click deletion; versions in report footer |

## D. Worked example (T01, synthetic)
Clause: laptops cite IS 13252 (Part 1): 2010, no certification mention.
1. Extraction finds product "laptops" and citation `IS 13252 (Part 1): 2010`.
2. Product maps to "Laptop / notebook / tablet".
3. R05 fires: the certification list specifies a different standard for this product and the clause cites another. R06 fires: certification not mentioned.
4. Each finding shows the source link and verified date. No claim is made about the cited standard's catalogue status.
