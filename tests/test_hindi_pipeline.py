import csv
from pathlib import Path

from packages.extraction.regex_extractor import RegexExtractor
from packages.mapping.product_mapper import ProductMapper
from packages.rules.context import create_seed_rule_context
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.normaliser import (
    normalise_devanagari_citation,
    normalise_devanagari_digits,
)
from packages.rules.schema import ClauseExtraction, ProductExtraction

CORPUS_PATH = Path(__file__).resolve().parents[1] / "eval" / "corpus" / "hindi-v1.csv"


def test_devanagari_digit_normalisation():
    """Verify Devanagari digits ०-९ are converted to ASCII 0-9."""
    dev_str = "IS १३२५२ (भाग १): २०१०"
    converted = normalise_devanagari_digits(dev_str)
    assert "13252" in converted
    assert "2010" in converted
    assert "1" in converted

    # Test full citation normaliser
    norm_cite = normalise_devanagari_citation(dev_str)
    assert "IS 13252" in norm_cite
    assert "2010" in norm_cite


def test_regex_extractor_on_devanagari_digits():
    """Verify regex extractor catches citations with Devanagari digits with original text spans."""
    clause = "आपूर्तिकर्ता 50 लैपटॉप देगा। लैपटॉप IS १३२५२ (भाग १): २०१० के अनुरूप होंगे।"
    extractor = RegexExtractor()
    extracted = extractor.extract(clause)

    assert len(extracted.citations) == 1
    cite = extracted.citations[0]
    assert cite.is_number == "IS 13252"
    assert cite.part == "1"
    assert cite.year == 2010

    # Span must match original substring in Hindi clause
    start, end = cite.span
    assert clause[start:end] == cite.raw
    assert "१३२५२" in cite.raw


def test_hindi_product_synonyms_mapping():
    """Verify Hindi synonyms map to canonical product IDs."""
    context = create_seed_rule_context()
    prods = [context.get_product(i) for i in range(1, 5)]
    mapper = ProductMapper(products=prods)

    # Laptop synonyms
    assert mapper.map_product("लैपटॉप").canonical_name == "Laptop / notebook / tablet"
    assert mapper.map_product("नोटबुक").canonical_name == "Laptop / notebook / tablet"

    # Microwave oven synonyms
    assert mapper.map_product("माइक्रोवेव").canonical_name == "Microwave ovens"
    assert mapper.map_product("माइक्रोवेव ओवन").canonical_name == "Microwave ovens"

    # Power adaptors
    assert mapper.map_product("पावर एडाप्टर").canonical_name == "Power adaptors for IT equipment"

    # IT equipment
    assert mapper.map_product("आईटी उपकरण").canonical_name == "IT equipment (general)"


def test_hindi_vague_terms():
    """Verify Hindi vague terms trigger R09 on original text."""
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    context = create_seed_rule_context()

    clause_text = "आपूर्तिकर्ता सरकारी बीआईएस मानक गुणवत्ता के लैपटॉप प्रदान करेगा।"
    clause = ClauseExtraction(
        clause_id="hi_vague_1",
        text=clause_text,
        language="hi",
        products=[ProductExtraction(text="लैपटॉप", span=(41, 47), canonical_product_id="Laptop / notebook / tablet")],
        citations=[],
        mentions_certification=False,
    )

    findings = engine.evaluate_clause(clause, context)
    r09_findings = [f for f in findings if f.rule_id == "R09"]
    assert len(r09_findings) >= 1
    assert r09_findings[0].span is not None


def test_hindi_corpus_v1_size_and_metrics():
    """Verify dedicated Hindi corpus v1 contains at least 30 clauses."""
    assert CORPUS_PATH.exists(), f"Hindi corpus not found at {CORPUS_PATH}"

    with open(CORPUS_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Spec 7.5 requires at least 30 clauses for Hindi
    assert len(rows) >= 30, f"Expected at least 30 clauses, got {len(rows)}"

    # Check zero em dashes in hindi-v1.csv
    em_dash = chr(8212)
    with open(CORPUS_PATH, encoding="utf-8") as f:
        assert em_dash not in f.read(), "Found forbidden em dash in hindi-v1.csv"


def test_hindi_quality_gate():
    """Verify Hindi pipeline quality gate computes per-language metrics and marks SUPPORTED."""
    from eval.hindi_gate import evaluate_hindi_quality_gate

    gate_result = evaluate_hindi_quality_gate(corpus_path=CORPUS_PATH, threshold=0.90)

    assert gate_result["language"] == "hi"
    assert gate_result["total_clauses"] >= 30
    assert gate_result["status"] == "SUPPORTED"
    assert gate_result["passed_count"] >= int(0.90 * gate_result["total_clauses"])
    assert " of " in gate_result["summary"]
