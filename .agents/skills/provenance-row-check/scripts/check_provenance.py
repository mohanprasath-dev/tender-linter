"""Check provenance fields on curated CSV rows. Exit 1 on failures."""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

PROVENANCE = ["verified_on", "verified_by", "evidence_ref"]
REQUIRED = {
    "standards": ["is_number", "title", "catalogue_url", *PROVENANCE],
    "product_standard_map": ["product", "is_number", "relation", "source_url", *PROVENANCE],
    "certification_rules": [
        "product", "scheme", "specified_is_number", "instrument", "source_url", *PROVENANCE,
    ],
    "allied_links": ["from_is_number", "to_is_number", "relation", "source_url", *PROVENANCE],
}
URL_FIELDS = ("catalogue_url", "source_url")
STATUSES = {"Active", "Withdrawn", "Superseded", "UNKNOWN", ""}


def check_row(table: str, row: dict) -> tuple[str, list[str]]:
    problems: list[str] = []
    missing = [f for f in REQUIRED[table] if not (row.get(f) or "").strip()]
    if missing:
        problems.append("missing: " + ", ".join(missing))
    if any("unverified" in (v or "").lower() for v in row.values()):
        problems.append("contains UNVERIFIED")
    on = (row.get("verified_on") or "").strip()
    if on:
        try:
            date.fromisoformat(on)
        except ValueError:
            problems.append("verified_on is not YYYY-MM-DD")
    for f in URL_FIELDS:
        v = (row.get(f) or "").strip()
        if v and not v.startswith("https://"):
            problems.append(f"{f} must start with https://")
    if table == "standards":
        if (row.get("status") or "").strip() not in STATUSES:
            problems.append("status not in Active/Withdrawn/Superseded/UNKNOWN")
        y = (row.get("publication_year") or "").strip()
        if y and not (y.isdigit() and len(y) == 4):
            problems.append("publication_year must be 4 digits")
    first = (row.get("verified_by") or "").strip().lower()
    second = (row.get("second_checked_by") or "").strip().lower()
    if first and second and first == second:
        problems.append("second_checked_by must differ from verified_by")
    if problems:
        return "FAIL", problems
    if not second:
        return "AWAITING_SECOND_CHECK", []
    return "VERIFIED", []


def check_file(path: Path) -> list[tuple[int, str, list[str]]]:
    table = path.stem
    if table not in REQUIRED:
        return [(0, "FAIL", [f"unknown table file name: {path.name}"])]
    out = []
    with path.open(newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=2):
            status, problems = check_row(table, row)
            out.append((i, status, problems))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--require-verified", action="store_true")
    a = p.parse_args(argv)
    counts = {"VERIFIED": 0, "AWAITING_SECOND_CHECK": 0, "FAIL": 0}
    for f in a.files:
        path = Path(f)
        if path.name in ("README.md", "products.csv"):
            continue
        for line, status, problems in check_file(path):
            counts[status] += 1
            extra = "; ".join(problems)
            print(f"{path.name}:{line} {status} {extra}".rstrip())
    total = sum(counts.values())
    print(
        f"{counts['VERIFIED']} of {total} rows verified, "
        f"{counts['AWAITING_SECOND_CHECK']} awaiting second check, {counts['FAIL']} failing"
    )
    if counts["FAIL"] or (a.require_verified and counts["AWAITING_SECOND_CHECK"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
