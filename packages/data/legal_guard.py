"""Legal compliance and copyright guard utilities for Tender Linter.
Enforces BIS Act 2016 s.10(5) compliance: standard text is never stored, reproduced,
summarised, or exported. Only public catalogue metadata and official links are permitted.
"""

from __future__ import annotations

import csv
from pathlib import Path


def audit_seed_data_for_prohibited_content(seed_dir: Path | None = None) -> list[str]:
    """Scan seed CSV files for unauthorized standard body text or prohibited terms.

    Returns:
        List of error descriptions if unauthorized standard text is detected.
    """
    if seed_dir is None:
        seed_dir = Path(__file__).resolve().parent / "seed"

    violations: list[str] = []

    # Prohibited clauses or terms that indicate reproduction of standard body text
    prohibited_snippets = [
        "this standard specifies requirements for",
        "clause 1 scope",
        "clause 2 normative references",
        "clause 3 terms and definitions",
        "shall withstand a test voltage of",
        "tensile strength shall not be less than",
        "copyright bureau of indian standards",
        "all rights reserved. no part of this publication may be reproduced",
    ]

    for csv_file in seed_dir.glob("*.csv"):
        with csv_file.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                for col, val in row.items():
                    val_lower = str(val or "").lower()
                    for snippet in prohibited_snippets:
                        if snippet in val_lower:
                            violations.append(
                                f"{csv_file.name}:{idx} column '{col}' contains prohibited standard text snippet: '{snippet}'"
                            )
                    # Check for prohibited UNVERIFIED marker
                    if "unverified" in val_lower:
                        violations.append(
                            f"{csv_file.name}:{idx} contains unverified fact marker in '{col}'"
                        )

    return violations


def audit_evidence_references(seed_dir: Path | None = None) -> list[str]:
    """Verify that all evidence references in seed files point to screenshots or metadata references,
    not raw standard PDF reproductions.
    """
    if seed_dir is None:
        seed_dir = Path(__file__).resolve().parent / "seed"

    violations: list[str] = []

    for csv_file in seed_dir.glob("*.csv"):
        with csv_file.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                ref = row.get("evidence_ref", "").strip().lower()
                if ref:
                    # Reject evidence referencing full standard text PDFs
                    if "full_standard" in ref or "standard_text" in ref or "is_text" in ref:
                        violations.append(
                            f"{csv_file.name}:{idx} evidence_ref '{ref}' appears to point to full standard text reproduction"
                        )

    return violations


def verify_disclaimer_presence(report_text: str) -> bool:
    """Verify that mandatory reviewer banner text is present in the report copy."""
    required_banner = (
        "This tool flags issues for the officer to review. It does not approve or reject a tender."
    )
    return required_banner in report_text
