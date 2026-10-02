---
name: eval-report
description: Turns evaluation results into honest "X of Y on test set Z" lines (rule recall, false alarms on clean controls, abstain correctness, per language). Use when running the evaluation harness, writing a release report, preparing the measured number for the deck, or when anyone asks for an accuracy figure.
---

# Eval report

**Goal:** Every reported result carries counts and a test set description. No bare percentages.

## Instructions
1. Produce a results JSON: `{"set_name", "description", "results": [{"id", "language", "kind": "defect|clean|abstain", "expected": [rule ids], "got": [rule ids]}]}`.
2. Run `python scripts/eval_report.py results.json`.
3. Paste the output into `eval/reports/<date>.md` with rule set, prompt, model and data snapshot versions.
4. Always say the set is synthetic when it is.

## Constraints
- Do NOT report a percentage without its counts.
- Do NOT imply synthetic results apply to real tenders.
- A release is blocked if a previously caught planted defect is now missed.
