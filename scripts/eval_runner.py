"""CLI runner for evaluation harness.
Usage:
    python scripts/eval_runner.py [--corpus eval/corpus/synthetic-v1.csv] [--mode deterministic|regex]
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.runner import run_evaluation_suite  # noqa: E402
from scripts.eval_report import generate_markdown_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Tender Linter Evaluation Harness Runner")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "eval" / "corpus" / "synthetic-v1.csv",
        help="Path to evaluation corpus CSV",
    )
    parser.add_argument(
        "--mode",
        choices=["deterministic", "regex"],
        default="deterministic",
        help="Evaluation mode (deterministic=gold extractions for CI gate, regex=live regex extractor)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "eval" / "reports",
        help="Output directory for reports",
    )
    args = parser.parse_args()

    if not args.corpus.exists():
        print(f"Error: Corpus file not found at {args.corpus}")
        sys.exit(1)

    print(f"Starting evaluation run on {args.corpus.name} (mode: {args.mode})...")
    results = run_evaluation_suite(corpus_path=args.corpus, mode=args.mode)

    # Generate Markdown Report
    report_md = generate_markdown_report(results)
    print("\n" + report_md + "\n")

    # Save artifacts
    today = datetime.date.today().isoformat()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    json_file = args.output_dir / f"results-{today}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    report_file = args.output_dir / f"eval-{today}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print("Artifacts saved:")
    print(f"  - Results JSON: {json_file}")
    print(f"  - Markdown Report: {report_file}")

    # Check CI regression gate
    metrics = results["metrics"]
    missed_defects = metrics["rule_recall"]["missed"]
    false_alarms = metrics["false_alarms"]["count"]
    abstain_fail = metrics["abstain_correctness"]["total"] - metrics["abstain_correctness"]["correct"]

    if missed_defects > 0 or false_alarms > 0 or abstain_fail > 0:
        print(f"\n[CI REGRESSION GATE FAILED] Missed defects: {missed_defects}, False alarms: {false_alarms}, Abstain fails: {abstain_fail}")
        sys.exit(1)

    print("\n[CI REGRESSION GATE PASSED] All release criteria satisfied.")
    sys.exit(0)


if __name__ == "__main__":
    main()
