---
name: rule-author
description: Adds or changes a rule in packages/rules/rules.yaml (R01 to R14 style) with evaluator, English message, Hindi placeholder and unit tests using hand-written extractions. Use when implementing the rules engine, adding a rule, changing a message template, resolving a rule interaction, or bumping the rule set version.
---

# Rule author

**Goal:** Every rule is data plus a small tested evaluator, traceable to a verified row.

## Instructions
1. Read `references/wording-rules.md` and the rule's entry in `packages/rules/rules.yaml`.
2. Add or edit the YAML entry: id, name, severity, fires_when, evidence, `message_en`, `message_hi: null`.
3. Write the unit test first with a hand-written extraction object and in-memory rows. No live model.
4. Implement the evaluator. It may only read rows that are verified and not in CONFLICT.
5. Bump `rule_set_version`. Regenerate `docs/rule-catalogue.md` from the YAML once the generator exists.
6. If the rule interacts with another (see `docs/open-verification.md` section B), ask the user before choosing.

## Constraints
- Do NOT write "outdated" or "withdrawn" unless R02 fires from a verified status.
- Do NOT show a finding without evidence link and verified date (CANNOT_VERIFY shows its reason).
- Do NOT fill `message_hi` without a fluent reviewer.
