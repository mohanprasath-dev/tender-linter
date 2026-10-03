import argparse
import csv
import sys
from pathlib import Path
from typing import Any

from packages.data.loader import REQUIRED_FIELDS, validate_row_provenance


def get_needed_cells(seed_dir: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Inspect CSV seed files and list exact rows and cells needing primary source data."""
    if seed_dir is None:
        seed_dir = Path(__file__).resolve().parent / "seed"

    needed: dict[str, list[dict[str, Any]]] = {}

    for csv_file in sorted(seed_dir.glob("*.csv")):
        table = csv_file.stem
        if table not in REQUIRED_FIELDS:
            continue

        needed[csv_file.name] = []
        with csv_file.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                missing_fields = [
                    f for f in REQUIRED_FIELDS[table] if not (row.get(f) or "").strip()
                ]
                identifier = row.get("is_number") or row.get("product") or f"row-{idx}"
                if missing_fields:
                    needed[csv_file.name].append(
                        {
                            "line": idx,
                            "identifier": identifier,
                            "missing": missing_fields,
                        }
                    )

    return needed


def generate_coverage_report(seed_dir: Path | None = None) -> str:
    """Generate an honest coverage report printing verified counts, dates, and open items."""
    if seed_dir is None:
        seed_dir = Path(__file__).resolve().parent / "seed"

    counts = {"VERIFIED": 0, "AWAITING_SECOND_CHECK": 0, "FAIL": 0}
    dates_seen: set[str] = set()

    # Track entity counts
    product_count = 0
    families_seen: set[str] = set()
    products_file = seed_dir / "products.csv"
    if products_file.exists():
        with products_file.open(newline="", encoding="utf-8") as fh:
            for p_row in csv.DictReader(fh):
                product_count += 1
                fam = (p_row.get("family") or "").strip()
                if fam:
                    families_seen.add(fam)

    standard_count = 0
    standards_file = seed_dir / "standards.csv"
    if standards_file.exists():
        with standards_file.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                standard_count += 1
                problems = validate_row_provenance("standards", row)
                if problems:
                    counts["FAIL"] += 1
                elif not (row.get("second_checked_by") or "").strip():
                    counts["AWAITING_SECOND_CHECK"] += 1
                else:
                    counts["VERIFIED"] += 1

                on = (row.get("verified_on") or "").strip()
                if on:
                    dates_seen.add(on)

    # Track map rows
    map_file = seed_dir / "product_standard_map.csv"
    map_count = 0
    if map_file.exists():
        with map_file.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                map_count += 1
                problems = validate_row_provenance("product_standard_map", row)
                if problems:
                    counts["FAIL"] += 1
                elif not (row.get("second_checked_by") or "").strip():
                    counts["AWAITING_SECOND_CHECK"] += 1
                else:
                    counts["VERIFIED"] += 1

                on = (row.get("verified_on") or "").strip()
                if on:
                    dates_seen.add(on)

    # Track certification rules
    cert_file = seed_dir / "certification_rules.csv"
    cert_count = 0
    if cert_file.exists():
        with cert_file.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                cert_count += 1
                problems = validate_row_provenance("certification_rules", row)
                if problems:
                    counts["FAIL"] += 1
                elif not (row.get("second_checked_by") or "").strip():
                    counts["AWAITING_SECOND_CHECK"] += 1
                else:
                    counts["VERIFIED"] += 1

                on = (row.get("verified_on") or "").strip()
                if on:
                    dates_seen.add(on)

    # Track allied links
    allied_file = seed_dir / "allied_links.csv"
    allied_count = 0
    if allied_file.exists():
        with allied_file.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                allied_count += 1
                problems = validate_row_provenance("allied_links", row)
                if problems:
                    counts["FAIL"] += 1
                elif not (row.get("second_checked_by") or "").strip():
                    counts["AWAITING_SECOND_CHECK"] += 1
                else:
                    counts["VERIFIED"] += 1

                on = (row.get("verified_on") or "").strip()
                if on:
                    dates_seen.add(on)

    total_curated_rows = sum(counts.values())
    verified_date_str = ", ".join(sorted(dates_seen)) if dates_seen else "no dates verified yet"
    families_str = ", ".join(sorted(families_seen)) if families_seen else "none"

    lines = [
        "===========================================================",
        "Tender Linter: Dataset Coverage Report",
        "===========================================================",
        f"Products in dataset: {product_count}",
        f"Product families: {families_str}",
        f"Standards in dataset: {standard_count}",
        f"Product-Standard mappings: {map_count}",
        f"Certification rules: {cert_count}",
        f"Allied standard links: {allied_count}",
        f"Verification dates recorded: {verified_date_str}",
        "",
        "Provenance Verification Status:",
        f"- Verified (two-person checked): {counts['VERIFIED']} of {total_curated_rows}",
        f"- Awaiting second check: {counts['AWAITING_SECOND_CHECK']} of {total_curated_rows}",
        f"- Incomplete / missing provenance: {counts['FAIL']} of {total_curated_rows}",
        "===========================================================",
    ]

    needed = get_needed_cells(seed_dir)
    has_missing = any(len(cells) > 0 for cells in needed.values())
    if has_missing:
        lines.append("\nCells Requiring Primary Source Data:")
        for filename, rows in needed.items():
            if rows:
                lines.append(f"\n[{filename}]")
                for r in rows:
                    lines.append(
                        f"  Line {r['line']} ({r['identifier']}): missing {', '.join(r['missing'])}"
                    )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tender Linter Seed Curator Tool")
    parser.add_argument("command", choices=["report", "needed"], default="report", nargs="?")
    args = parser.parse_args(argv)

    if args.command in ("report", "needed"):
        print(generate_coverage_report())

    return 0


if __name__ == "__main__":
    sys.exit(main())
