---
name: is-number-normaliser
description: Parses and normalises Indian Standard citations (IS, IS/IEC, parts, years, Devanagari digits, full-width characters) with a deterministic script. Use when writing or testing the citation regex library, normalising an IS number for a lookup, extracting citations from clause text with offsets, or suggesting a near-match for a typo (rule R12).
---

# IS number normaliser

**Goal:** One tested, deterministic way to turn citation text into `is_number`, `part`, `year` with character offsets.

## Instructions
1. Run `python scripts/normalise_is.py "<clause text>"` to list citations with spans.
2. For typo suggestions run `python scripts/normalise_is.py --suggest "IS 13253" --known "IS 13252" "IS 302-2-25"`.
3. Reuse `fold`, `find_citations`, `suggest_near` in code. Do not rewrite the regex elsewhere.
4. When a new citation form fails, add a test case to `tests/test_skill_scripts.py` first, then fix the script.
5. Offsets refer to the original text. The script keeps string length unchanged when folding.

## Constraints
- Never correct, complete or invent an IS number, part or year. Suggestions are candidates only and need officer confirmation.
- Do not hardcode IS numbers as facts. Known numbers come from the standards table.
