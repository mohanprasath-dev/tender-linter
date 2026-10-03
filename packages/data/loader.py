import csv
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from packages.data.models import (
    AlliedLink,
    CertificationRule,
    Product,
    ProductStandardMap,
    Standard,
)

# Provenance rules matching provenance-row-check skill
PROVENANCE_FIELDS = ["verified_on", "verified_by", "evidence_ref"]
REQUIRED_FIELDS = {
    "standards": ["is_number", "title", "catalogue_url", *PROVENANCE_FIELDS],
    "product_standard_map": ["product", "is_number", "relation", "source_url", *PROVENANCE_FIELDS],
    "certification_rules": [
        "product",
        "scheme",
        "specified_is_number",
        "instrument",
        "source_url",
        *PROVENANCE_FIELDS,
    ],
    "allied_links": [
        "from_is_number",
        "to_is_number",
        "relation",
        "source_url",
        *PROVENANCE_FIELDS,
    ],
}
STATUSES = {"Active", "Withdrawn", "Superseded", "UNKNOWN", ""}


def validate_row_provenance(table: str, row: dict[str, Any]) -> list[str]:
    """Validate a CSV row against provenance and integrity rules."""
    problems: list[str] = []
    missing = [f for f in REQUIRED_FIELDS.get(table, []) if not (row.get(f) or "").strip()]
    if missing:
        problems.append("missing: " + ", ".join(missing))

    if any("unverified" in str(v or "").lower() for v in row.values()):
        problems.append("contains prohibited term UNVERIFIED")

    on = (row.get("verified_on") or "").strip()
    if on:
        try:
            date.fromisoformat(on)
        except ValueError:
            problems.append("verified_on is not YYYY-MM-DD")

    for url_field in ("catalogue_url", "source_url"):
        val = (row.get(url_field) or "").strip()
        if val and not val.startswith("https://"):
            problems.append(f"{url_field} must start with https://")

    if table == "standards":
        status_val = (row.get("status") or "").strip()
        if status_val not in STATUSES:
            problems.append("status not in Active/Withdrawn/Superseded/UNKNOWN")
        year_val = (row.get("publication_year") or "").strip()
        if year_val and not (year_val.isdigit() and len(year_val) == 4):
            problems.append("publication_year must be 4 digits")

    verifier = (row.get("verified_by") or "").strip().lower()
    second_checker = (row.get("second_checked_by") or "").strip().lower()
    if verifier and second_checker and verifier == second_checker:
        problems.append("second_checked_by must differ from verified_by")

    return problems


def load_seed_data(session: Session, seed_dir: Path | None = None) -> dict[str, int]:
    """Load and validate seed CSV files into the database session."""
    if seed_dir is None:
        seed_dir = Path(__file__).resolve().parent / "seed"

    loaded_counts: dict[str, int] = {}

    # 1. Load products
    products_file = seed_dir / "products.csv"
    product_map: dict[str, Product] = {}
    if products_file.exists():
        with products_file.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                name = row["canonical_name"].strip()
                if "unverified" in name.lower():
                    raise ValueError(f"Product {name} contains prohibited term UNVERIFIED")
                prod = session.query(Product).filter_by(canonical_name=name).first()
                if not prod:
                    prod = Product(
                        canonical_name=name,
                        family=row.get("family", "").strip(),
                        synonyms_en=row.get("synonyms_en", "[]").strip(),
                        synonyms_hi=row.get("synonyms_hi", "[]").strip(),
                        synonyms_other=row.get("synonyms_other", "[]").strip(),
                    )
                    session.add(prod)
                    session.flush()
                product_map[name] = prod
        loaded_counts["products"] = len(product_map)

    # 2. Load standards
    standards_file = seed_dir / "standards.csv"
    standard_map: dict[str, Standard] = {}
    if standards_file.exists():
        with standards_file.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                problems = validate_row_provenance("standards", row)
                if problems:
                    raise ValueError(
                        f"standards.csv line {idx} failed provenance check: {'; '.join(problems)}"
                    )

                is_num = row["is_number"].strip()
                pub_year = (
                    int(row["publication_year"])
                    if (row.get("publication_year") or "").strip().isdigit()
                    else None
                )
                std = session.query(Standard).filter_by(is_number=is_num).first()
                if not std:
                    std = Standard(
                        is_number=is_num,
                        part=row.get("part") or None,
                        section=row.get("section") or None,
                        title=row["title"].strip(),
                        publication_year=pub_year,
                        status=(row.get("status") or "UNKNOWN").strip(),
                        catalogue_url=row["catalogue_url"].strip(),
                        verified_on=date.fromisoformat(row["verified_on"].strip()),
                        verified_by=row["verified_by"].strip(),
                        second_checked_by=(row.get("second_checked_by") or None),
                        evidence_ref=row["evidence_ref"].strip(),
                    )
                    session.add(std)
                    session.flush()
                standard_map[is_num] = std
        loaded_counts["standards"] = len(standard_map)

    # 3. Load product_standard_map
    map_file = seed_dir / "product_standard_map.csv"
    if map_file.exists():
        count = 0
        with map_file.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                problems = validate_row_provenance("product_standard_map", row)
                if problems:
                    raise ValueError(
                        f"product_standard_map.csv line {idx} failed check: {'; '.join(problems)}"
                    )

                prod_name = row["product"].strip()
                is_num = row["is_number"].strip()
                prod = (
                    product_map.get(prod_name)
                    or session.query(Product).filter_by(canonical_name=prod_name).first()
                )
                std = (
                    standard_map.get(is_num)
                    or session.query(Standard).filter_by(is_number=is_num).first()
                )

                if prod and std:
                    existing = (
                        session.query(ProductStandardMap)
                        .filter_by(product_id=prod.id, standard_id=std.id)
                        .first()
                    )
                    if not existing:
                        psm = ProductStandardMap(
                            product_id=prod.id,
                            standard_id=std.id,
                            relation=row["relation"].strip(),
                            source_url=row["source_url"].strip(),
                            verified_on=date.fromisoformat(row["verified_on"].strip()),
                            verified_by=row["verified_by"].strip(),
                            second_checked_by=(row.get("second_checked_by") or None),
                            evidence_ref=row["evidence_ref"].strip(),
                        )
                        session.add(psm)
                        count += 1
        loaded_counts["product_standard_map"] = count

    # 4. Load certification_rules
    cert_file = seed_dir / "certification_rules.csv"
    if cert_file.exists():
        count = 0
        with cert_file.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                problems = validate_row_provenance("certification_rules", row)
                if problems:
                    raise ValueError(
                        f"certification_rules.csv line {idx} failed check: {'; '.join(problems)}"
                    )

                prod_name = row["product"].strip()
                is_num = row["specified_is_number"].strip()
                prod = (
                    product_map.get(prod_name)
                    or session.query(Product).filter_by(canonical_name=prod_name).first()
                )
                std = (
                    standard_map.get(is_num)
                    or session.query(Standard).filter_by(is_number=is_num).first()
                )

                if prod and std:
                    existing = (
                        session.query(CertificationRule)
                        .filter_by(product_id=prod.id, specified_standard_id=std.id)
                        .first()
                    )
                    if not existing:
                        c_rule = CertificationRule(
                            product_id=prod.id,
                            scheme=row["scheme"].strip(),
                            specified_standard_id=std.id,
                            instrument=row["instrument"].strip(),
                            source_url=row["source_url"].strip(),
                            verified_on=date.fromisoformat(row["verified_on"].strip()),
                            verified_by=row["verified_by"].strip(),
                            second_checked_by=(row.get("second_checked_by") or None),
                            evidence_ref=row["evidence_ref"].strip(),
                        )
                        session.add(c_rule)
                        count += 1
        loaded_counts["certification_rules"] = count

    # 5. Load allied_links
    allied_file = seed_dir / "allied_links.csv"
    if allied_file.exists():
        count = 0
        with allied_file.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                problems = validate_row_provenance("allied_links", row)
                if problems:
                    raise ValueError(
                        f"allied_links.csv line {idx} failed check: {'; '.join(problems)}"
                    )

                from_num = row["from_is_number"].strip()
                to_num = row["to_is_number"].strip()
                from_std = (
                    standard_map.get(from_num)
                    or session.query(Standard).filter_by(is_number=from_num).first()
                )
                to_std = (
                    standard_map.get(to_num)
                    or session.query(Standard).filter_by(is_number=to_num).first()
                )

                if from_std and to_std:
                    existing = (
                        session.query(AlliedLink)
                        .filter_by(from_standard_id=from_std.id, to_standard_id=to_std.id)
                        .first()
                    )
                    if not existing:
                        alink = AlliedLink(
                            from_standard_id=from_std.id,
                            to_standard_id=to_std.id,
                            relation=row["relation"].strip(),
                            source_url=row["source_url"].strip(),
                            verified_on=date.fromisoformat(row["verified_on"].strip()),
                            verified_by=row["verified_by"].strip(),
                            second_checked_by=(row.get("second_checked_by") or None),
                            evidence_ref=row["evidence_ref"].strip(),
                        )
                        session.add(alink)
                        count += 1
        loaded_counts["allied_links"] = count

    session.commit()
    return loaded_counts
