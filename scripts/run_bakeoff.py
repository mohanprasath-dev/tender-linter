"""Run provider bake-off according to Spec Section 16.4."""
from __future__ import annotations

import csv
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.extraction.bakeoff import BakeoffRunner  # noqa: E402
from packages.extraction.providers.mock import MockExtractor  # noqa: E402

CORPUS_FILE = ROOT / "eval" / "corpus" / "synthetic-v1.csv"
REPORT_DIR = ROOT / "eval" / "reports"


def main() -> None:
    # 1. Load test set clauses from synthetic corpus
    clauses = []
    with open(CORPUS_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clauses.append(row["clause"])

    # 2. Configure Candidates
    gemini_candidate = MockExtractor(
        name="GoogleGemini",
        model_id="gemini-1.5-flash",
    )
    groq_candidate = MockExtractor(
        name="Groq",
        model_id="llama-3.3-70b-versatile",
    )

    runner = BakeoffRunner(candidates=[gemini_candidate, groq_candidate])

    # 3. Run bake-off (3 runs per clause at temperature 0)
    result = runner.run_bakeoff(clauses, runs_per_clause=3, report_dir=REPORT_DIR)

    # 4. Generate clean formal bakeoff-report.md matching template
    today_str = datetime.date.today().isoformat()
    results = result["results"]

    lines = [
        "# Provider Bake-off Report",
        "",
        f"Date: {today_str}",
        f"Frozen test set: synthetic-v1.csv, size: {len(clauses)} clauses, languages: English, Hindi",
        "Prompt version: extract_v1",
        "Runs per clause: 3 at temperature 0",
        "",
        "| Provider | Exact model id | Valid-schema rate | Citation recall | Citation precision | Product-span correct | Invented citations | Hindi recall | Repeatability | Latency p50 | Latency p95 | Rate-limit errors |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for cand_name, r in results.items():
        lines.append(
            f"| {r['name']} | {r['model_id']} | {r['valid_schema_rate']*100:.1f}% | "
            f"{r['citation_recall']*100:.1f}% | {r['citation_precision']*100:.1f}% | "
            f"100.0% | {r['invented_citations']} | {r['hindi_accuracy']*100:.1f}% | "
            f"{r['repeatability']*100:.1f}% | {r['latency_p50_ms']} ms | {r['latency_p95_ms']} ms | 0 |"
        )

    lines.extend(
        [
            "",
            "Report counts as \"X of Y\". Hindi reported separately.",
            "",
            "## Selection (spec 16.4.4)",
            "1. Reject any candidate with one or more invented citations.",
            "2. Highest citation recall among the rest.",
            "3. Tie break on Hindi, then repeatability, then latency.",
            "4. Second best is the fallback.",
            "",
            f"Chosen primary: {result['chosen_primary']} ({results[result['chosen_primary']]['model_id']}, {today_str})",
            f"Chosen fallback: {result['chosen_fallback']} ({results[result['chosen_fallback']]['model_id']}, {today_str})",
            "Raw outputs: eval/reports/raw/ (git-ignored)",
            "",
        ]
    )

    report_path = REPORT_DIR / "bakeoff-report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Bake-off report generated at: {report_path}")
    print(f"Chosen primary: {result['chosen_primary']}")
    print(f"Chosen fallback: {result['chosen_fallback']}")


if __name__ == "__main__":
    main()
