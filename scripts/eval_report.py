"""Evaluation report generator following the eval-report skill.
Formats evaluation results with honest 'X of Y' counts. No bare percentages.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def format_count_line(label: str, numerator: int, denominator: int, set_description: str = "") -> str:
    """Format an honest metric line as 'X of Y on Z' without bare percentages."""
    if denominator == 0:
        return f"- **{label}:** 0 of 0 (no applicable test cases)"
    pct = round((numerator / denominator) * 100.0, 1)
    suffix = f" on {set_description}" if set_description else ""
    return f"- **{label}:** {numerator} of {denominator} ({pct}%){suffix}"


def generate_markdown_report(results: dict[str, Any]) -> str:
    """Generate a compliant markdown report adhering to eval-report skill constraints."""
    today = datetime.date.today().isoformat()
    metrics = results.get("metrics", {})
    recall = metrics.get("rule_recall", {})
    alarms = metrics.get("false_alarms", {})
    abstain = metrics.get("abstain_correctness", {})
    adversarial = metrics.get("adversarial_robustness", {})
    languages = metrics.get("languages", {})
    latency = metrics.get("latency", {})
    evidence = metrics.get("evidence_completeness", {})

    rule_set_ver = results.get("rule_set_version", "0.1.0")
    total_clauses = results.get("total_clauses", len(results.get("results", [])))
    set_name = results.get("set_name", "synthetic-v1")
    description = results.get("description", "Synthetic test corpus v1")

    lines = [
        f"# Evaluation Report: {set_name}",
        "",
        "> **Notice:** This test set is synthetic. Synthetic evaluation results do not imply performance on real tenders.",
        "",
        "## 1. Metadata and Versions",
        f"- **Date:** {today}",
        f"- **Corpus:** {set_name} ({total_clauses} clauses, synthetic)",
        f"- **Description:** {description}",
        f"- **Rule Set Version:** {rule_set_ver}",
        "- **Prompt Version:** v1.0.0 (extraction-prompt-v1.txt)",
        "- **Model ID:** Deterministic golden extraction reference (CI regression gate)",
        "- **Data Snapshot:** Verified seed data (IS/IEC 62368-1, IS 302-2-25, IS 13252 Part 1)",
        "",
        "## 2. Core Metrics (Measured Counts)",
        "",
        format_count_line(
            "Rule Recall (Planted Defects Caught)",
            recall.get("caught", 0),
            recall.get("total_expected", 0),
            f"planted defect set ({recall.get('total_expected', 0)} defect instances)",
        ),
        format_count_line(
            "Clean Controls (Zero False Alarms)",
            alarms.get("clean_total", 0) - alarms.get("count", 0),
            alarms.get("clean_total", 0),
            f"clean control set ({alarms.get('clean_total', 0)} clean clauses)",
        ),
        format_count_line(
            "Abstain Correctness (R10 on Out-of-Dataset)",
            abstain.get("correct", 0),
            abstain.get("total", 0),
            f"unmapped product set ({abstain.get('total', 0)} clauses)",
        ),
        format_count_line(
            "Adversarial Robustness",
            adversarial.get("passed", 0),
            adversarial.get("total", 0),
            f"adversarial stress set ({adversarial.get('total', 0)} clauses)",
        ),
        format_count_line(
            "Evidence Completeness (Link and Date present)",
            evidence.get("complete", 0),
            evidence.get("total_applicable", 0),
            f"applicable finding instances ({evidence.get('total_applicable', 0)} findings)",
        ),
        "",
        "## 3. Language Breakdown",
        "",
    ]

    for lang, lstats in languages.items():
        lang_title = {"en": "English", "hi": "Hindi", "mixed": "Mixed Hindi-English"}.get(lang, lang.upper())
        lines.append(
            format_count_line(
                f"{lang_title} Accuracy",
                lstats.get("passed", 0),
                lstats.get("total", 0),
                f"{lang_title} subset ({lstats.get('total', 0)} clauses)",
            )
        )

    lines.extend([
        "",
        "## 4. Latency Performance",
        f"- **Median Latency (p50):** {latency.get('p50_ms', 0)} ms per clause",
        f"- **95th Percentile (p95):** {latency.get('p95_ms', 0)} ms per clause",
        f"- **Average Latency:** {latency.get('avg_ms', 0)} ms per clause",
        f"- **Total Suite Execution Time:** {latency.get('total_ms', 0)} ms",
        "",
        "## 5. Regression Gate Status",
        "",
    ])

    missed_count = recall.get("missed", 0)
    alarms_count = alarms.get("count", 0)
    abstain_fail = abstain.get("total", 0) - abstain.get("correct", 0)

    if missed_count == 0 and alarms_count == 0 and abstain_fail == 0:
        lines.append(
            "**Gate Passed:** All planted defects caught, zero false alarms on clean controls, "
            "and all out-of-dataset products correctly abstained. Ready for release."
        )
    else:
        lines.append(
            f"**Gate Failed:** Missed {missed_count} planted defects, {alarms_count} false alarms on clean controls, "
            f"and {abstain_fail} abstain failures. Release blocked."
        )

    return "\n".join(lines)


def main() -> None:
    """CLI entrypoint for generating report from a results JSON file."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/eval_report.py <results_file.json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: Results file not found at {json_path}")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        results = json.load(f)

    report_content = generate_markdown_report(results)
    print(report_content)

    # Save to eval/reports/<date>.md
    today = datetime.date.today().isoformat()
    out_dir = Path(__file__).resolve().parents[1] / "eval" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"eval-{today}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\n[OK] Report written to {report_file}")


if __name__ == "__main__":
    main()
