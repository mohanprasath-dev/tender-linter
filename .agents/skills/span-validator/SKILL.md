---
name: span-validator
description: Drops extraction spans that are not exact substrings of the clause and counts invented citations (raw text, number or year not present in the clause). Use when implementing or testing the extraction service, running the provider bake-off, writing golden-file tests, or checking a model output before it reaches the rules engine.
---

# Span validator

**Goal:** Nothing the model returns reaches the rules unless it is literally in the clause.

## Instructions
1. Run `python scripts/validate_spans.py clause.txt extraction.json` to print the cleaned extraction, dropped items and the invented-citation count.
2. In service code, apply the same logic on every model result before caching.
3. Log the invented-citation count per provider. The bake-off rejects any provider with one or more.
4. Add `--strict` in tests to fail when anything is dropped.

## Constraints
- Do NOT repair or re-locate a bad span. Drop it.
- Do NOT pass standard data to the model. It sees only the clause.
