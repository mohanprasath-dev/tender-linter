from __future__ import annotations

from pathlib import Path

from packages.extraction.bakeoff import BakeoffRunner
from packages.extraction.cache import InMemoryExtractionCache
from packages.extraction.providers.mock import MockExtractor
from packages.extraction.rate_limiter import CircuitBreaker, TokenBucketRateLimiter
from packages.extraction.regex_extractor import RegexExtractor
from packages.extraction.schema import CitationItem, ProductItem
from packages.extraction.service import ExtractionService
from packages.extraction.span_validator import validate_extraction_spans


def test_span_validator_keeps_exact_spans():
    clause = "The supplier shall deliver 50 laptops conforming to IS 13252 (Part 1): 2010."
    data = {
        "clause_id": "c1",
        "language": "en",
        "products": [{"text": "laptops", "span": [30, 37], "canonical_product_id": None}],
        "citations": [
            {
                "raw": "IS 13252 (Part 1): 2010",
                "span": [52, 75],
                "is_number": "IS 13252",
                "part": "1",
                "year": 2010,
            }
        ],
        "vague_phrases": [],
        "requirements": [],
    }

    cleaned, dropped, invented = validate_extraction_spans(clause, data)
    assert len(dropped) == 0
    assert invented == 0
    assert len(cleaned["products"]) == 1
    assert len(cleaned["citations"]) == 1


def test_span_validator_drops_misplaced_spans():
    clause = "The supplier shall deliver 50 laptops."
    data = {
        "clause_id": "c2",
        "language": "en",
        "products": [
            {"text": "laptops", "span": [10, 17], "canonical_product_id": None}  # wrong span
        ],
        "citations": [],
        "vague_phrases": [],
        "requirements": [],
    }

    cleaned, dropped, invented = validate_extraction_spans(clause, data)
    assert len(dropped) == 1
    assert len(cleaned["products"]) == 0


def test_span_validator_counts_invented_citations():
    clause = "The supplier shall deliver 50 laptops."
    data = {
        "clause_id": "c3",
        "language": "en",
        "products": [],
        "citations": [
            {
                "raw": "IS 99999",
                "span": [0, 8],  # "The supp" != "IS 99999"
                "is_number": "IS 99999",
                "part": None,
                "year": 2020,
            }
        ],
        "vague_phrases": [],
        "requirements": [],
    }

    cleaned, dropped, invented = validate_extraction_spans(clause, data)
    assert len(dropped) == 1
    assert invented == 1
    assert len(cleaned["citations"]) == 0


def test_regex_extractor_english_and_hindi():
    regex_ext = RegexExtractor()

    # English clause
    res_en = regex_ext.extract("Conform to IS/IEC 62368 Part 1: 2023.")
    assert len(res_en.citations) == 1
    c_en = res_en.citations[0]
    assert c_en.is_number == "IS/IEC 62368"
    assert c_en.part == "1"
    assert c_en.year == 2023

    # Hindi clause with Devanagari digits
    res_hi = regex_ext.extract("लैपटॉप IS १३२५२ (भाग १): २०१० के अनुरूप होंगे।")
    assert len(res_hi.citations) == 1
    c_hi = res_hi.citations[0]
    assert c_hi.is_number == "IS 13252"
    assert c_hi.part == "1"
    assert c_hi.year == 2010


def test_rate_limiter_and_circuit_breaker():
    limiter = TokenBucketRateLimiter(rate_per_minute=60, daily_cap=100)
    assert limiter.allow_request() is True
    assert limiter.daily_count == 1

    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=10.0)
    assert cb.can_execute() is True
    cb.record_failure()
    assert cb.can_execute() is True
    cb.record_failure()
    # Now circuit breaker should be open
    assert cb.can_execute() is False
    cb.record_success()
    assert cb.can_execute() is True


def test_extraction_service_fallback_to_secondary():
    clause = "Clause 4.1: IT equipment shall conform to IS 13252 (Part 1): 2010."
    raw = "IS 13252 (Part 1): 2010"
    s = clause.find(raw)
    span = (s, s + len(raw))

    failing_primary = MockExtractor(
        name="MockPrimary",
        model_id="primary-v1",
        should_fail=True,
    )
    working_secondary = MockExtractor(
        name="MockSecondary",
        model_id="secondary-v1",
        canned_citations=[
            CitationItem(
                raw=raw,
                span=span,
                is_number="IS 13252",
                part="1",
                year=2010,
            )
        ],
    )

    service = ExtractionService(
        primary=failing_primary,
        secondary=working_secondary,
        cache=InMemoryExtractionCache(),
    )

    res = service.extract("c101", clause)
    assert res.meta.provider == "MockSecondary"
    assert res.meta.reduced_mode is False
    assert len(res.data.citations) == 1


def test_extraction_service_fallback_to_reduced_regex_mode():
    failing_primary = MockExtractor(name="MockPrimary", model_id="p1", should_fail=True)
    failing_secondary = MockExtractor(name="MockSecondary", model_id="s1", should_fail=True)

    service = ExtractionService(
        primary=failing_primary,
        secondary=failing_secondary,
        cache=InMemoryExtractionCache(),
    )

    clause = "The supplier shall deliver laptops conforming to IS/IEC 62368 Part 1: 2023."
    res = service.extract("c102", clause)
    assert res.meta.reduced_mode is True
    assert res.meta.provider == "RegexFallback"
    assert len(res.data.citations) == 1
    assert res.data.citations[0].is_number == "IS/IEC 62368"


def test_extraction_service_caching():
    clause = "Microwave ovens shall strictly conform to IS 302-2-25."
    raw = "IS 302-2-25"
    s = clause.find(raw)
    span = (s, s + len(raw))

    mock = MockExtractor(
        name="MockPrimary",
        model_id="p1",
        canned_citations=[
            CitationItem(
                raw=raw,
                span=span,
                is_number="IS 302-2-25",
            )
        ],
    )
    service = ExtractionService(primary=mock, cache=InMemoryExtractionCache())

    res1 = service.extract("c103", clause)
    assert res1.meta.cached is False

    # Second call for the same clause returns cached result
    res2 = service.extract("c103", clause)
    assert res2.meta.cached is True
    assert res2.data.citations[0].raw == "IS 302-2-25"


def test_cross_check_detects_disagreement():
    # Model extracts no citations, but regex extracts a citation
    blind_model = MockExtractor(
        name="BlindModel",
        model_id="blind-v1",
        canned_citations=[],  # Model missed it
    )

    service = ExtractionService(primary=blind_model, cache=InMemoryExtractionCache())
    clause = "The laptops shall conform to IS 13252 (Part 1): 2010."
    res = service.extract("c104", clause)
    assert res.meta.extraction_uncertain is True


def test_bakeoff_runner_and_selection_rule(tmp_path: Path):
    clause1 = "The supplier shall deliver 50 laptops conforming to IS 13252 (Part 1): 2010."
    raw_cit = "IS 13252 (Part 1): 2010"
    s_cit = clause1.find(raw_cit)
    span_cit = (s_cit, s_cit + len(raw_cit))

    raw_prod = "laptops"
    s_prod = clause1.find(raw_prod)
    span_prod = (s_prod, s_prod + len(raw_prod))

    candidate_a = MockExtractor(
        name="CandidateA",
        model_id="model-a-reliable",
        canned_products=[ProductItem(text=raw_prod, span=span_prod)],
        canned_citations=[
            CitationItem(
                raw=raw_cit,
                span=span_cit,
                is_number="IS 13252",
                part="1",
                year=2010,
            )
        ],
    )
    # Candidate B hallucinates/invents an absent citation unconditionally
    candidate_b = MockExtractor(
        name="CandidateB",
        model_id="model-b-hallucinator",
        canned_citations=[
            CitationItem(
                raw="IS 99999",
                span=(0, 8),
                is_number="IS 99999",
            )
        ],
        allow_hallucination=True,
    )

    runner = BakeoffRunner(candidates=[candidate_a, candidate_b])

    clauses = [
        clause1,
        "Clean control clause without any citations or standards mentioned.",
    ]

    report = runner.run_bakeoff(clauses, runs_per_clause=3, report_dir=tmp_path)

    # Candidate B must be rejected due to invented citation
    assert report["chosen_primary"] == "CandidateA"
    assert report["results"]["CandidateB"]["invented_citations"] > 0
    assert report["results"]["CandidateA"]["invented_citations"] == 0

    # Ensure report file was written and contains no em dashes
    report_file = tmp_path / report["report_filename"]
    assert report_file.exists()
    report_text = report_file.read_text(encoding="utf-8")
    assert chr(8212) not in report_text
    assert chr(8211) not in report_text
