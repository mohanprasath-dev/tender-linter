# Provider Bake-off Report

Date: 
Frozen test set: name, size (at least 60 clauses; 10 clean; 10 adversarial), languages
Prompt version: 
Runs per clause: 3 at temperature 0

| Provider | Exact model id | Valid-schema rate | Citation recall | Citation precision | Product-span correct | Invented citations | Hindi recall | Repeatability | Latency p50 | Latency p95 | Rate-limit errors |
|---|---|---|---|---|---|---|---|---|---|---|---|

Report counts as "X of Y". Hindi reported separately.

## Selection (spec 16.4.4)
1. Reject any candidate with one or more invented citations.
2. Highest citation recall among the rest.
3. Tie-break: Hindi, then repeatability, then latency.
4. Second best is the fallback.

Chosen primary: (model id, date)
Chosen fallback: (model id, date)
Raw outputs: `eval/reports/raw/` (git-ignored; keep a copy in the object store)
