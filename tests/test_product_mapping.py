from __future__ import annotations

import pytest

from packages.mapping.is_normaliser import normalize_citation, suggest_near_matches
from packages.mapping.product_mapper import ProductMapper
from packages.mapping.schema import MappingMatchMethod
from packages.rules.context import ProductRecord, create_seed_rule_context


@pytest.fixture
def seed_products() -> list[ProductRecord]:
    ctx = create_seed_rule_context()
    return [
        ctx.get_product(1),  # Laptop / notebook / tablet
        ctx.get_product(2),  # Power adaptors for IT equipment
        ctx.get_product(3),  # Microwave ovens
        ctx.get_product(4),  # IT equipment (general)
    ]


@pytest.fixture
def mapper(seed_products) -> ProductMapper:
    return ProductMapper(products=seed_products, threshold=0.75)


def test_exact_and_synonym_matching_english(mapper):
    res_laptop = mapper.map_product("laptops")
    assert res_laptop.is_unmapped is False
    assert res_laptop.canonical_name == "Laptop / notebook / tablet"
    assert res_laptop.confidence >= 0.95

    res_mw = mapper.map_product("microwave ovens")
    assert res_mw.is_unmapped is False
    assert res_mw.canonical_name == "Microwave ovens"
    assert res_mw.confidence >= 0.95


def test_hindi_synonym_matching(mapper):
    res_laptop_hi = mapper.map_product("लैपटॉप")
    assert res_laptop_hi.is_unmapped is False
    assert res_laptop_hi.canonical_name == "Laptop / notebook / tablet"

    res_mw_hi = mapper.map_product("माइक्रोवेव")
    assert res_mw_hi.is_unmapped is False
    assert res_mw_hi.canonical_name == "Microwave ovens"


def test_fuzzy_matching_close_variants(mapper):
    # Close variation: "laptop computers"
    res = mapper.map_product("laptop computers")
    assert res.is_unmapped is False
    assert res.canonical_name == "Laptop / notebook / tablet"
    assert res.confidence >= 0.75


def test_out_of_dataset_products_end_as_unmapped(mapper):
    unmapped_queries = [
        "portable air purifiers",
        "air purifier",
        "solar water heater",
        "smart watch",
        "cement bags",
        "concrete mix",
        "office furniture",
    ]

    for q in unmapped_queries:
        res = mapper.map_product(q)
        assert res.is_unmapped is True, f"Query '{q}' should be UNMAPPED, but got {res.canonical_name} (conf={res.confidence})"
        assert res.canonical_product_id is None
        assert res.method == MappingMatchMethod.UNMAPPED


def test_officer_confirmation_and_override_hook(mapper):
    # Initially maps to Laptop / notebook / tablet
    res = mapper.map_product("laptops")
    assert res.canonical_name == "Laptop / notebook / tablet"
    assert res.officer_confirmed is False

    # Officer confirms mapping
    confirmed = mapper.confirm_mapping(res, officer_id="officer_42")
    assert confirmed.officer_confirmed is True
    assert confirmed.canonical_name == "Laptop / notebook / tablet"

    # Officer overrides mapping to IT equipment (general)
    overridden = mapper.override_mapping(
        raw_text="laptops",
        override_product_name="IT equipment (general)",
        officer_id="officer_42",
        notes="Procurement clause applies to general IT batch",
    )
    assert overridden.canonical_name == "IT equipment (general)"
    assert overridden.method == MappingMatchMethod.OFFICER_OVERRIDE
    assert overridden.officer_notes is not None


def test_is_normaliser_forms():
    # Part and year
    c1 = normalize_citation("IS 13252 (Part 1): 2010")
    assert c1.is_number == "IS 13252"
    assert c1.part == "1"
    assert c1.year == 2010

    # IS/IEC form
    c2 = normalize_citation("IS/IEC 62368 Part 1: 2023")
    assert c2.is_number == "IS/IEC 62368"
    assert c2.part == "1"
    assert c2.year == 2023

    # Devanagari numerals
    c3 = normalize_citation("IS १३२५२ (भाग १): २०१०")
    assert c3.is_number == "IS 13252"
    assert c3.part == "1"
    assert c3.year == 2010


def test_is_normaliser_typo_suggestions():
    known = ["IS 13252", "IS 302-2-25", "IS/IEC 62368 Part 1"]
    suggestions = suggest_near_matches("IS 13253", known)
    assert "IS 13252" in suggestions

    # Exact match should have no suggestions
    assert suggest_near_matches("IS 13252", known) == []


def test_synthetic_test_set_unmapped_rate(mapper):
    """Verify that out-of-dataset clauses from synthetic-v1.csv reliably end as UNMAPPED."""
    # In synthetic-v1, T07 is portable air purifiers (unmapped)
    res_t07 = mapper.map_product("portable air purifiers rated for 30 square metres")
    assert res_t07.is_unmapped is True

    # Other synthetic items mapped
    res_t01 = mapper.map_product("50 laptops")
    assert res_t01.is_unmapped is False
    assert res_t01.canonical_name == "Laptop / notebook / tablet"

    res_t04 = mapper.map_product("10 microwave ovens")
    assert res_t04.is_unmapped is False
    assert res_t04.canonical_name == "Microwave ovens"
