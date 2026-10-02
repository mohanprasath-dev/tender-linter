"""CLI runner for Hindi pipeline quality gate (M9).
Usage:
    python scripts/check_hindi_gate.py [--corpus eval/corpus/hindi-v1.csv] [--threshold 0.90]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.hindi_gate import evaluate_hindi_quality_gate  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Hindi Quality Gate Checker")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "eval" / "corpus" / "hindi-v1.csv",
        help="Path to Hindi test corpus CSV",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.90,
        help="Minimum required accuracy threshold (default: 0.90)",
    )
    args = parser.parse_args()

    if not args.corpus.exists():
        print(f"Error: Corpus not found at {args.corpus}")
        sys.exit(1)

    print(f"Running Hindi Quality Gate evaluation on {args.corpus.name}...")
    res = evaluate_hindi_quality_gate(corpus_path=args.corpus, threshold=args.threshold)

    print("\n" + "=" * 60)
    print("HINDI PIPELINE QUALITY GATE REPORT")
    print("=" * 60)
    print("- Language: Hindi (hi) and Mixed Hindi-English")
    print(f"- Status: {res['status']}")
    print(f"- Accuracy: {res['summary']}")
    print(f"- Required Threshold: {int(res['threshold'] * 100)}%")
    print(f"- Passed Clauses: {res['passed_count']} of {res['total_clauses']}")
    print(f"- Failed Clauses: {res['failed_count']} of {res['total_clauses']}")

    if res["failed_details"]:
        print("\nFailed Cases:")
        for fd in res["failed_details"]:
            print(f"  - [{fd['id']}] Expected: {fd['expected']}, Got: {fd['got']}")
            print(f"    Clause: {fd['clause']}")

    print("=" * 60)

    if res["status"] == "SUPPORTED":
        print("\n[OK] Hindi Quality Gate passed: Language status is SUPPORTED.")
        sys.exit(0)
    else:
        print(f"\n[FAIL] Hindi Quality Gate failed: Accuracy below {int(res['threshold'] * 100)}%. Status is UNSUPPORTED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
