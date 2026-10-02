import csv
from pathlib import Path

from packages.rules.context import create_seed_rule_context
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
    VaguePhraseExtraction,
)

CORPUS_PATH = Path(__file__).resolve().parents[1] / "eval" / "corpus" / "synthetic-v1.csv"


def get_mock_extractions_for_synthetic_row(row_id: str) -> list[ClauseExtraction]:
    """Provide hand-written, deterministic extractions for synthetic matrix T01-T13.
    Matches spec 16.7.
    """
    if row_id == "T01":
        # The supplier shall deliver 50 laptops. The laptops shall conform to IS 13252 (Part 1): 2010.
        return [
            ClauseExtraction(
                clause_id="T01",
                text="The supplier shall deliver 50 laptops. The laptops shall conform to IS 13252 (Part 1): 2010.",
                products=[
                    ProductExtraction(
                        text="laptops",
                        span=(30, 37),
                        canonical_product_id="Laptop / notebook / tablet",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 13252 (Part 1): 2010",
                        span=(68, 92),
                        is_number="IS 13252 (Part 1)",
                        part="1",
                        year=2010,
                    )
                ],
                mentions_certification=False,
            )
        ]

    elif row_id == "T02":
        # The supplier shall deliver 50 laptops. The laptops shall conform to IS/IEC 62368 Part 1: 2023.
        return [
            ClauseExtraction(
                clause_id="T02",
                text="The supplier shall deliver 50 laptops. The laptops shall conform to IS/IEC 62368 Part 1: 2023.",
                products=[
                    ProductExtraction(
                        text="laptops",
                        span=(30, 37),
                        canonical_product_id="Laptop / notebook / tablet",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS/IEC 62368 Part 1: 2023",
                        span=(68, 94),
                        is_number="IS/IEC 62368 Part 1",
                        part="1",
                        year=2023,
                    )
                ],
                mentions_certification=False,
            )
        ]

    elif row_id == "T03":
        # The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2019. Registration under the Compulsory Registration Scheme is required.
        return [
            ClauseExtraction(
                clause_id="T03",
                text="The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2019. Registration under the Compulsory Registration Scheme is required.",
                products=[
                    ProductExtraction(
                        text="laptops",
                        span=(27, 34),
                        canonical_product_id="Laptop / notebook / tablet",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS/IEC 62368 Part 1: 2019",
                        span=(49, 75),
                        is_number="IS/IEC 62368 Part 1",
                        part="1",
                        year=2019,
                    )
                ],
                mentions_certification=True,
            )
        ]

    elif row_id == "T04":
        # The supplier shall deliver 10 microwave ovens conforming to IS 302-2-25.
        return [
            ClauseExtraction(
                clause_id="T04",
                text="The supplier shall deliver 10 microwave ovens conforming to IS 302-2-25.",
                products=[
                    ProductExtraction(
                        text="microwave ovens",
                        span=(30, 45),
                        canonical_product_id="Microwave ovens",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 302-2-25",
                        span=(60, 71),
                        is_number="IS 302-2-25",
                    )
                ],
                mentions_certification=False,
            )
        ]

    elif row_id == "T05":
        # The supplier shall deliver 10 microwave ovens. Registration under the Compulsory Registration Scheme is required.
        return [
            ClauseExtraction(
                clause_id="T05",
                text="The supplier shall deliver 10 microwave ovens. Registration under the Compulsory Registration Scheme is required.",
                products=[
                    ProductExtraction(
                        text="microwave ovens",
                        span=(30, 45),
                        canonical_product_id="Microwave ovens",
                    )
                ],
                citations=[],
                mentions_certification=True,
            )
        ]

    elif row_id == "T06":
        # The supplier shall deliver IT equipment of ISI quality.
        return [
            ClauseExtraction(
                clause_id="T06",
                text="The supplier shall deliver IT equipment of ISI quality.",
                products=[
                    ProductExtraction(
                        text="IT equipment",
                        span=(27, 39),
                        canonical_product_id="IT equipment (general)",
                    )
                ],
                citations=[],
                vague_phrases=[
                    VaguePhraseExtraction(
                        text="ISI quality",
                        span=(43, 54),
                        phrase="ISI quality",
                    )
                ],
            )
        ]

    elif row_id == "T07":
        # The supplier shall deliver 20 portable air purifiers rated for 30 square metres.
        return [
            ClauseExtraction(
                clause_id="T07",
                text="The supplier shall deliver 20 portable air purifiers rated for 30 square metres.",
                products=[
                    ProductExtraction(
                        text="portable air purifiers",
                        span=(30, 52),
                        canonical_product_id=None,
                    )
                ],
                citations=[],
            )
        ]

    elif row_id == "T08":
        # The supplier shall deliver IT equipment conforming to IS 99999: 2015.
        return [
            ClauseExtraction(
                clause_id="T08",
                text="The supplier shall deliver IT equipment conforming to IS 99999: 2015.",
                products=[
                    ProductExtraction(
                        text="IT equipment",
                        span=(27, 39),
                        canonical_product_id="IT equipment (general)",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 99999: 2015",
                        span=(54, 69),
                        is_number="IS 99999",
                        year=2015,
                    )
                ],
            )
        ]

    elif row_id == "T09":
        # Clause 4.1: IT equipment shall conform to IS 13252 (Part 1): 2010. Clause 9.2: testing shall follow IS 13252 (Part 1): 2008.
        return [
            ClauseExtraction(
                clause_id="T09_1",
                text="Clause 4.1: IT equipment shall conform to IS 13252 (Part 1): 2010.",
                products=[
                    ProductExtraction(
                        text="IT equipment",
                        span=(12, 24),
                        canonical_product_id="IT equipment (general)",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 13252 (Part 1): 2010",
                        span=(43, 67),
                        is_number="IS 13252 (Part 1)",
                        part="1",
                        year=2010,
                    )
                ],
            ),
            ClauseExtraction(
                clause_id="T09_2",
                text="Clause 9.2: testing shall follow IS 13252 (Part 1): 2008.",
                products=[
                    ProductExtraction(
                        text="testing",
                        span=(12, 19),
                        canonical_product_id=None,
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 13252 (Part 1): 2008",
                        span=(33, 57),
                        is_number="IS 13252 (Part 1)",
                        part="1",
                        year=2008,
                    )
                ],
            ),
        ]

    elif row_id == "T10":
        # The supplier shall deliver IT equipment conforming to IS 13253 (Part 1): 2010.
        return [
            ClauseExtraction(
                clause_id="T10",
                text="The supplier shall deliver IT equipment conforming to IS 13253 (Part 1): 2010.",
                products=[
                    ProductExtraction(
                        text="IT equipment",
                        span=(27, 39),
                        canonical_product_id="IT equipment (general)",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 13253 (Part 1): 2010",
                        span=(54, 78),
                        is_number="IS 13253",
                        part="1",
                        year=2010,
                    )
                ],
            )
        ]

    elif row_id == "T11":
        # The supplier shall deliver 10 microwave ovens conforming to IS 13252 (Part 1): 2010. Registration under the Compulsory Registration Scheme is required.
        return [
            ClauseExtraction(
                clause_id="T11",
                text="The supplier shall deliver 10 microwave ovens conforming to IS 13252 (Part 1): 2010. Registration under the Compulsory Registration Scheme is required.",
                products=[
                    ProductExtraction(
                        text="microwave ovens",
                        span=(30, 45),
                        canonical_product_id="Microwave ovens",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 13252 (Part 1): 2010",
                        span=(60, 84),
                        is_number="IS 13252 (Part 1)",
                        part="1",
                        year=2010,
                    )
                ],
                mentions_certification=True,
            )
        ]

    elif row_id == "T12":
        # आपूर्तिकर्ता 50 लैपटॉप की आपूर्ति करेगा। लैपटॉप IS 13252 (भाग 1): 2010 के अनुरूप होंगे। अनिवार्य पंजीकरण योजना (CRS) के अंतर्गत पंजीकरण आवश्यक है।
        return [
            ClauseExtraction(
                clause_id="T12",
                language="hi",
                text="आपूर्तिकर्ता 50 लैपटॉप की आपूर्ति करेगा। लैपटॉप IS 13252 (भाग 1): 2010 के अनुरूप होंगे। अनिवार्य पंजीकरण योजना (CRS) के अंतर्गत पंजीकरण आवश्यक है।",
                products=[
                    ProductExtraction(
                        text="लैपटॉप",
                        span=(16, 22),
                        canonical_product_id="Laptop / notebook / tablet",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS 13252 (भाग 1): 2010",
                        span=(47, 70),
                        is_number="IS 13252 (Part 1)",
                        part="1",
                        year=2010,
                    )
                ],
                mentions_certification=True,
            )
        ]

    elif row_id == "T13":
        # The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2023. Registration under the Compulsory Registration Scheme is required.
        return [
            ClauseExtraction(
                clause_id="T13",
                text="The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2023. Registration under the Compulsory Registration Scheme is required.",
                products=[
                    ProductExtraction(
                        text="laptops",
                        span=(27, 34),
                        canonical_product_id="Laptop / notebook / tablet",
                    )
                ],
                citations=[
                    CitationExtraction(
                        raw="IS/IEC 62368 Part 1: 2023",
                        span=(49, 75),
                        is_number="IS/IEC 62368 Part 1",
                        part="1",
                        year=2023,
                    )
                ],
                mentions_certification=True,
            )
        ]

    return []


def test_synthetic_matrix_t01_to_t13():
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    seed_context = create_seed_rule_context()

    with open(CORPUS_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        matrix = list(reader)

    matrix_t01_t13 = [r for r in matrix if r["id"] in {f"T{i:02d}" for i in range(1, 14)}]
    assert len(matrix_t01_t13) == 13

    for row in matrix_t01_t13:
        t_id = row["id"]
        expected_rules = set(row["expected_rules"].split(";")) if row["expected_rules"] else set()
        clauses = get_mock_extractions_for_synthetic_row(t_id)

        findings = engine.evaluate_document(clauses, seed_context)
        fired_rule_ids = {f.rule_id for f in findings}

        # Filter out informational stale row if present in general tests
        fired_without_stale = {r for r in fired_rule_ids if r != "R14"}

        assert (
            fired_without_stale == expected_rules
        ), f"Row {t_id} failed: expected {expected_rules}, got {fired_without_stale} on clause '{row['clause']}'"
