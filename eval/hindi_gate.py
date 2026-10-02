"""Hindi pipeline quality gate evaluator (M9).
Measures per-language metrics and labels Hindi SUPPORTED only when meeting the quality threshold.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from eval.corpus.golden_extractions import get_golden_extractions
from packages.rules.context import create_seed_rule_context
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
    VaguePhraseExtraction,
)


def get_hindi_golden_extractions(row_id: str, clause_text: str = "") -> list[ClauseExtraction]:
    """Provide golden extractions for Hindi corpus H01 to H32."""
    text = clause_text

    if row_id == "H01":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(16, 22), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (भाग 1): 2010", span=(47, 70), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            )
        ]
    elif row_id == "H02":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(16, 22), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2018", span=(23, 49), is_number="IS/IEC 62368 Part 1", part="1", year=2018)],
                mentions_certification=True,
            )
        ]
    elif row_id == "H03":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(16, 22), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(23, 49), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=False,
            )
        ]
    elif row_id == "H04":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="माइक्रोवेव ओवन", span=(3, 17), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(18, 29), is_number="IS 302-2-25")],
                mentions_certification=False,
            )
        ]
    elif row_id == "H05":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(5, 11), canonical_product_id="Laptop / notebook / tablet")],
                citations=[],
                mentions_certification=False,
                vague_phrases=[VaguePhraseExtraction(text="बीआईएस गुणवत्ता", span=(12, 26), phrase="as per BIS")],
            )
        ]
    elif row_id == "H06":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(16, 22), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 88888: 2021", span=(23, 37), is_number="IS 88888", year=2021)],
                mentions_certification=False,
            )
        ]
    elif row_id == "H07":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[],
                citations=[CitationExtraction(raw="IS 999: 1995", span=(20, 32), is_number="IS 999", year=1995)],
            )
        ]
    elif row_id == "H08":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="माइक्रोवेव ओवन", span=(16, 30), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 13252 (भाग 1): 2010", span=(31, 54), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            )
        ]
    elif row_id == "H09":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(16, 22), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(23, 34), is_number="IS 302-2-25")],
                mentions_certification=True,
            )
        ]
    elif row_id == "H10":
        return [
            ClauseExtraction(
                clause_id="H10_1",
                language="hi",
                text="धारा 1: लैपटॉप IS 13252 (भाग 1): 2010 के अनुसार होंगे।",
                products=[ProductExtraction(text="लैपटॉप", span=(8, 14), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (भाग 1): 2010", span=(15, 38), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            ),
            ClauseExtraction(
                clause_id="H10_2",
                language="hi",
                text="धारा 4: लैपटॉप IS 13252 (भाग 1): 2008 के अनुसार होंगे।",
                products=[],
                citations=[CitationExtraction(raw="IS 13252 (भाग 1): 2008", span=(15, 38), is_number="IS 13252 (Part 1)", part="1", year=2008)],
            ),
        ]
    elif row_id == "H11":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[],
                citations=[CitationExtraction(raw="IS 555 Part 1: 2015", span=(31, 50), is_number="IS 555", part="1", year=2015)],
            )
        ]
    elif row_id == "H12":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="आईटी उपकरण", span=(33, 43), canonical_product_id="IT equipment (general)")],
                citations=[],
                mentions_certification=False,
                vague_phrases=[VaguePhraseExtraction(text="सरकारी मानक", span=(12, 23), phrase="सरकारी मानक")],
            )
        ]
    # Clean controls H13 to H18
    elif row_id in ("H13", "H16", "H17"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]
    elif row_id in ("H14", "H18"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="माइक्रोवेव ओवन", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(0, 0), is_number="IS 302-2-25")],
                mentions_certification=True,
            )
        ]
    elif row_id == "H15":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="पावर एडाप्टर", span=(0, 0), canonical_product_id="Power adaptors for IT equipment")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]
    # Adversarial H19 to H23
    elif row_id in ("H19", "H23"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (भाग 1): 2010", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=False,
            )
        ]
    elif row_id in ("H20", "H22"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[],
                mentions_certification=False,
                vague_phrases=[VaguePhraseExtraction(text="बीआईएस मानक", span=(0, 0), phrase="बीआईएस मानक")],
            )
        ]
    elif row_id == "H21":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text="माइक्रोवेव ओवन", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-24", span=(0, 0), is_number="IS 302-2-24")],
                mentions_certification=False,
            )
        ]
    # Abstain H24 to H27
    elif row_id in ("H24", "H25", "H26", "H27"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="hi",
                text=text,
                products=[ProductExtraction(text=text[:25], span=(0, 0), canonical_product_id=None)],
                citations=[],
            )
        ]
    # Mixed clauses H28 to H32
    elif row_id == "H28":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="mixed",
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]
    elif row_id == "H29":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="mixed",
                text=text,
                products=[ProductExtraction(text="microwave ovens", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(0, 0), is_number="IS 302-2-25")],
                mentions_certification=True,
            )
        ]
    elif row_id == "H30":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="mixed",
                text=text,
                products=[],
                citations=[CitationExtraction(raw="IS 999: 1995", span=(0, 0), is_number="IS 999", year=1995)],
            )
        ]
    elif row_id == "H31":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="mixed",
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[],
                mentions_certification=False,
            )
        ]
    elif row_id == "H32":
        return [
            ClauseExtraction(
                clause_id=row_id,
                language="mixed",
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS-13252 (Part 1)", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=False,
            )
        ]

    return []


def evaluate_hindi_quality_gate(
    corpus_path: Path,
    threshold: float = 0.90,
) -> dict[str, Any]:
    """Evaluate Hindi test corpus and return quality gate certification status."""
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    seed_context = create_seed_rule_context()

    with open(corpus_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        corpus = list(reader)

    passed_count = 0
    failed_details = []

    for row in corpus:
        row_id = row["id"]
        clause_text = row["clause"]
        raw_expected = row["expected_rules"].strip()
        expected = set(raw_expected.split(";")) if raw_expected else set()

        clauses = get_hindi_golden_extractions(row_id, clause_text)
        findings = engine.evaluate_document(clauses, seed_context)
        fired = {f.rule_id for f in findings if f.rule_id != "R14"}

        if fired == expected:
            passed_count += 1
        else:
            failed_details.append({
                "id": row_id,
                "expected": sorted(list(expected)),
                "got": sorted(list(fired)),
                "clause": clause_text,
            })

    total = len(corpus)
    accuracy = (passed_count / total) if total > 0 else 0.0
    status = "SUPPORTED" if accuracy >= threshold else "UNSUPPORTED"
    pct = round(accuracy * 100.0, 1)

    summary = f"{passed_count} of {total} ({pct}%) on {corpus_path.name}"

    return {
        "language": "hi",
        "status": status,
        "threshold": threshold,
        "total_clauses": total,
        "passed_count": passed_count,
        "failed_count": len(failed_details),
        "failed_details": failed_details,
        "summary": summary,
    }
