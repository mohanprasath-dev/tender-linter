"""Evaluate product mapping against test sets and report UNMAPPED rate."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from packages.mapping.product_mapper import ProductMapper  # noqa: E402
from packages.rules.context import create_seed_rule_context  # noqa: E402

CORPUS_FILE = ROOT / "eval" / "corpus" / "synthetic-v1.csv"


def main() -> None:
    ctx = create_seed_rule_context()
    seed_prods = [ctx.get_product(i) for i in range(1, 5)]
    mapper = ProductMapper(products=seed_prods, threshold=0.75)

    # In-dataset and out-of-dataset test items
    test_cases = [
        # (text, expected_unmapped, label)
        ("laptops", False, "In-dataset: Laptop"),
        ("50 laptops", False, "In-dataset: Laptop with quantity"),
        ("लैपटॉप", False, "In-dataset: Hindi Laptop"),
        ("microwave ovens", False, "In-dataset: Microwave"),
        ("10 microwave ovens", False, "In-dataset: Microwave with quantity"),
        ("माइक्रोवेव", False, "In-dataset: Hindi Microwave"),
        ("power adaptors", False, "In-dataset: Power adaptors"),
        ("IT equipment", False, "In-dataset: IT equipment"),
        ("portable air purifiers", True, "Out-of-dataset: Air purifiers"),
        ("portable air purifiers rated for 30 square metres", True, "Out-of-dataset: Air purifier clause"),
        ("solar water heater", True, "Out-of-dataset: Solar heater"),
        ("smart watch", True, "Out-of-dataset: Smart watch"),
        ("cement bags", True, "Out-of-dataset: Cement"),
        ("concrete mix", True, "Out-of-dataset: Concrete"),
        ("office furniture", True, "Out-of-dataset: Furniture"),
    ]

    total_out = sum(1 for _, expected_unmapped, _ in test_cases if expected_unmapped)
    unmapped_correct = 0

    print("=== Product Mapping Evaluation ===")
    print(f"Calibrated Threshold: {mapper.threshold}")
    print(f"Total test cases: {len(test_cases)}")
    print(f"Out-of-dataset test cases: {total_out}")
    print("-" * 50)

    for text, expected_unmapped, label in test_cases:
        res = mapper.map_product(text)
        is_unmapped = res.is_unmapped
        match_str = "UNMAPPED" if is_unmapped else f"Mapped -> {res.canonical_name}"
        status = "PASS" if is_unmapped == expected_unmapped else "FAIL"
        print(f"[{status}] {label} ('{text}') -> {match_str} (confidence: {res.confidence})")

        if expected_unmapped and is_unmapped:
            unmapped_correct += 1

    print("-" * 50)
    print(f"Out-of-dataset UNMAPPED result: {unmapped_correct} of {total_out} correctly unmapped.")
    assert unmapped_correct == total_out, f"Expected all {total_out} to be UNMAPPED"
    print("M5 Quality Gate: PASSED.")


if __name__ == "__main__":
    main()
