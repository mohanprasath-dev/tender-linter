---
description: Run the release quality gates before a demo build or submission
---
1. Run all rule tests and the evaluation run; use the eval-report skill for output.
2. Confirm invented-citation count on the corpus is zero.
3. Sample 50 findings; each needs a working source link and verified date.
4. Run provenance-row-check with `--require-verified`.
5. Confirm report footer prints rule set, prompt, model and data snapshot versions.
6. Check accessibility on the three main screens and a tested backup restore.
7. Stop and list failures. Do not ship on a partial pass.
