"""Tests for Milestone M13: Coverage Expansion.
Validates expanded product family (Cement and concrete), verified standards,
Gazette-backed QCO rules, coverage reporting, and evaluation harness inclusion.
"""

from pathlib import Path

from eval.runner import run_evaluation_suite
from packages.data.curator import generate_coverage_report
from packages.mapping.product_mapper import ProductMapper
from packages.rules.context import create_seed_rule_context
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
)

CORPUS_PATH = Path(__file__).resolve().parents[1] / "eval" / "corpus" / "synthetic-v1.csv"
SEED_DIR = Path(__file__).resolve().parents[1] / "packages" / "data" / "seed"


def test_coverage_report_reflects_expanded_counts() -> None:
    """Verify that generate_coverage_report displays the new family and expanded counts."""
    report = generate_coverage_report(SEED_DIR)

    assert "Products in dataset: 5" in report
    assert "Cement and concrete" in report
    assert "Standards in dataset: 5" in report
    assert "Certification rules: 1" in report
    assert "Allied standard links: 1" in report
    assert "Verified (two-person checked):" in report


def test_cement_product_mapping_en_and_hi() -> None:
    """Verify English and Hindi product synonyms resolve to Ordinary Portland Cement (OPC)."""
    ctx = create_seed_rule_context()
    mapper = ProductMapper(products=list(ctx._products.values()))

    # English queries
    res_en1 = mapper.map_product("Ordinary Portland Cement")
    assert res_en1.canonical_name == "Ordinary Portland Cement (OPC)"

    res_en2 = mapper.map_product("500 bags of cement")
    assert res_en2.canonical_name == "Ordinary Portland Cement (OPC)"

    res_en3 = mapper.map_product("portland cement")
    assert res_en3.canonical_name == "Ordinary Portland Cement (OPC)"

    # Hindi queries
    res_hi1 = mapper.map_product("सीमेंट")
    assert res_hi1.canonical_name == "Ordinary Portland Cement (OPC)"

    res_hi2 = mapper.map_product("ऑर्डिनरी पोर्टलैंड सीमेंट")
    assert res_hi2.canonical_name == "Ordinary Portland Cement (OPC)"


def test_cement_clean_clause_evaluation() -> None:
    """Verify a conforming cement clause with QCO ISI mark triggers zero defect findings."""
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    ctx = create_seed_rule_context()

    clause = ClauseExtraction(
        clause_id="cement_clean",
        text="The contractor shall supply 500 bags of Ordinary Portland Cement conforming to IS 269: 2015 bearing the mandatory ISI mark as per Cement Quality Control Order.",
        products=[
            ProductExtraction(
                text="Ordinary Portland Cement",
                span=(37, 61),
                canonical_product_id="Ordinary Portland Cement (OPC)",
            )
        ],
        citations=[
            CitationExtraction(
                raw="IS 269: 2015",
                span=(76, 88),
                is_number="IS 269",
                year=2015,
            )
        ],
        mentions_certification=True,
    )

    findings = engine.evaluate_document([clause], ctx)
    defect_findings = [f for f in findings if f.rule_id != "R14"]
    assert len(defect_findings) == 0, f"Expected clean clause, got {defect_findings}"


def test_cement_missing_qco_certification_triggers_r06() -> None:
    """Verify cement citing IS 269 without QCO certification triggers rule R06."""
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    ctx = create_seed_rule_context()

    clause = ClauseExtraction(
        clause_id="cement_defect_r06",
        text="The supplier shall deliver 300 bags of Ordinary Portland Cement conforming to IS 269: 2015.",
        products=[
            ProductExtraction(
                text="Ordinary Portland Cement",
                span=(39, 63),
                canonical_product_id="Ordinary Portland Cement (OPC)",
            )
        ],
        citations=[
            CitationExtraction(
                raw="IS 269: 2015",
                span=(78, 90),
                is_number="IS 269",
                year=2015,
            )
        ],
        mentions_certification=False,
    )

    findings = engine.evaluate_document([clause], ctx)
    rule_ids = {f.rule_id for f in findings}
    assert "R06" in rule_ids


def test_cement_outdated_year_triggers_r03() -> None:
    """Verify cement citing superseded publication year 1989 triggers R03."""
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    ctx = create_seed_rule_context()

    clause = ClauseExtraction(
        clause_id="cement_defect_r03",
        text="The contractor shall supply Ordinary Portland Cement conforming to IS 269: 1989 with ISI mark certification as per QCO.",
        products=[
            ProductExtraction(
                text="Ordinary Portland Cement",
                span=(28, 52),
                canonical_product_id="Ordinary Portland Cement (OPC)",
            )
        ],
        citations=[
            CitationExtraction(
                raw="IS 269: 1989",
                span=(67, 79),
                is_number="IS 269",
                year=1989,
            )
        ],
        mentions_certification=True,
    )

    findings = engine.evaluate_document([clause], ctx)
    rule_ids = {f.rule_id for f in findings}
    assert "R03" in rule_ids


def test_cement_cross_domain_standard_triggers_r13() -> None:
    """Verify cement citing IT equipment standard IS 13252 triggers R13 and R05."""
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    ctx = create_seed_rule_context()

    clause = ClauseExtraction(
        clause_id="cement_cross_domain",
        text="The supplier shall supply 200 bags of Ordinary Portland Cement conforming to IS 13252 (Part 1): 2010 with ISI mark.",
        products=[
            ProductExtraction(
                text="Ordinary Portland Cement",
                span=(38, 62),
                canonical_product_id="Ordinary Portland Cement (OPC)",
            )
        ],
        citations=[
            CitationExtraction(
                raw="IS 13252 (Part 1): 2010",
                span=(77, 101),
                is_number="IS 13252 (Part 1)",
                part="1",
                year=2010,
            )
        ],
        mentions_certification=True,
    )

    findings = engine.evaluate_document([clause], ctx)
    rule_ids = {f.rule_id for f in findings}
    assert "R13" in rule_ids
    assert "R05" in rule_ids


def test_eval_suite_includes_expanded_corpus() -> None:
    """Verify full evaluation run succeeds with 100% recall on the expanded 75-clause corpus."""
    results = run_evaluation_suite(corpus_path=CORPUS_PATH, mode="deterministic")

    assert results["total_clauses"] >= 75
    metrics = results["metrics"]

    # All planted defects caught
    assert metrics["rule_recall"]["missed"] == 0, f"Missed: {metrics['rule_recall']['missed_details']}"
    assert metrics["rule_recall"]["caught"] == metrics["rule_recall"]["total_expected"]

    # Zero false alarms on clean controls
    assert metrics["false_alarms"]["count"] == 0, f"False alarms: {metrics['false_alarms']['details']}"

    # 100% abstain correctness
    assert metrics["abstain_correctness"]["correct"] == metrics["abstain_correctness"]["total"]
