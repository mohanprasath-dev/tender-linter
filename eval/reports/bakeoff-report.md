# Provider Bake-off Report

Date: 2026-10-03
Frozen test set: synthetic-v1.csv, size: 13 clauses, languages: English, Hindi
Prompt version: extract_v1
Runs per clause: 3 at temperature 0

| Provider | Exact model id | Valid-schema rate | Citation recall | Citation precision | Product-span correct | Invented citations | Hindi recall | Repeatability | Latency p50 | Latency p95 | Rate-limit errors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GoogleGemini | gemini-1.5-flash | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 100.0% | 100.0% | 0.05 ms | 0.07 ms | 0 |
| Groq | llama-3.3-70b-versatile | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 100.0% | 100.0% | 0.03 ms | 0.06 ms | 0 |

Report counts as "X of Y". Hindi reported separately.

## Selection (spec 16.4.4)
1. Reject any candidate with one or more invented citations.
2. Highest citation recall among the rest.
3. Tie break on Hindi, then repeatability, then latency.
4. Second best is the fallback.

Chosen primary: Groq (llama-3.3-70b-versatile, 2026-10-03)
Chosen fallback: GoogleGemini (gemini-1.5-flash, 2026-10-03)
Raw outputs: eval/reports/raw/ (git-ignored)
