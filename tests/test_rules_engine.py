import datetime

import pytest

from packages.rules.context import (
    AlliedLinkRecord,
    CertificationRuleRecord,
    InMemoryRuleDataContext,
    ProductRecord,
    ProductStandardMapRecord,
    StandardRecord,
    VagueTermRecord,
)
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
    Severity,
    VaguePhraseExtraction,
)


@pytest.fixture
def mock_context() -> InMemoryRuleDataContext:
    ctx = InMemoryRuleDataContext(stale_days=180)

    # Standards
    s1 = StandardRecord(
        id=1,
        is_number="IS/IEC 62368 Part 1",
        part="1",
        title="Audio/video, information and communication technology equipment",
        publication_year=2023,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/1",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    s2 = StandardRecord(
        id=2,
        is_number="IS 302-2-25",
        part=None,
        title="Safety of household appliances: Microwave ovens",
        publication_year=2014,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    s3 = StandardRecord(
        id=3,
        is_number="IS 13252 (Part 1)",
        part="1",
        title="Information Technology Equipment - Safety Part 1",
        publication_year=2010,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/3",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    s_withdrawn = StandardRecord(
        id=4,
        is_number="IS 999",
        part=None,
        title="Old Standard",
        publication_year=1990,
        status="Withdrawn",
        catalogue_url="https://standardsbis.bsbedge.com/record/4",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    s_conflict = StandardRecord(
        id=5,
        is_number="IS 888",
        part=None,
        title="Conflicting Standard",
        publication_year=2015,
        status="CONFLICT",
        catalogue_url="https://standardsbis.bsbedge.com/record/5",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
        is_conflict=True,
    )
    s_stale = StandardRecord(
        id=6,
        is_number="IS 777",
        part=None,
        title="Stale Standard",
        publication_year=2012,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/6",
        verified_on=datetime.date(2025, 1, 1),  # older than 180 days relative to 2026-10-02
        verified_by="curator1",
    )

    ctx.add_standards([s1, s2, s3, s_withdrawn, s_conflict, s_stale])

    # Products
    p1 = ProductRecord(
        id=1,
        canonical_name="Laptop / notebook / tablet",
        family="IT equipment",
        synonyms_en=["laptop", "notebook", "tablet", "laptops"],
        synonyms_hi=["लैपटॉप"],
    )
    p2 = ProductRecord(
        id=2,
        canonical_name="Microwave ovens",
        family="Household appliances",
        synonyms_en=["microwave oven", "microwave ovens"],
        synonyms_hi=["माइक्रोवेव"],
    )
    p3 = ProductRecord(
        id=3,
        canonical_name="IT equipment (general)",
        family="IT equipment",
        synonyms_en=["it equipment"],
        synonyms_hi=[],
    )

    ctx.add_products([p1, p2, p3])

    # Product-Standard Map
    psm1 = ProductStandardMapRecord(
        id=1,
        product_id=1,
        standard_id=1,
        relation="PRIMARY",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    psm2 = ProductStandardMapRecord(
        id=2,
        product_id=2,
        standard_id=2,
        relation="PRIMARY",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    psm3 = ProductStandardMapRecord(
        id=3,
        product_id=3,
        standard_id=3,
        relation="PRIMARY",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )

    ctx.add_product_standard_maps([psm1, psm2, psm3])

    # Certification rules (CRS for Laptops -> IS/IEC 62368 Part 1; CRS for Microwave -> IS 302-2-25)
    cr1 = CertificationRuleRecord(
        id=1,
        product_id=1,
        scheme="CRS",
        specified_standard_id=1,
        instrument="Electronics and IT Goods (Requirement for Compulsory Registration) Order",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    cr2 = CertificationRuleRecord(
        id=2,
        product_id=2,
        scheme="CRS",
        specified_standard_id=2,
        instrument="Electrical Appliances (Quality Control) Order",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )

    ctx.add_certification_rules([cr1, cr2])

    # Allied links: IS 13252 (Part 1) has allied standard IS/IEC 62368 Part 1
    al1 = AlliedLinkRecord(
        id=1,
        source_standard_id=3,
        target_standard_id=1,
        relation="NORMATIVE",
        source_url="https://standardsbis.bsbedge.com/record/3",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="curator1",
    )
    ctx.add_allied_links([al1])

    # Vague terms
    vt1 = VagueTermRecord(
        id=1,
        term="ISI quality",
        language="en",
        explanation="Refers to quality generally without specifying an Indian Standard number.",
    )
    vt2 = VagueTermRecord(
        id=2,
        term="as per BIS",
        language="en",
        explanation="Names the bureau without citing an applicable standard number.",
    )
    ctx.add_vague_terms([vt1, vt2])

    return ctx


@pytest.fixture
def engine() -> RulesEngine:
    catalog = load_rules_from_yaml()
    return RulesEngine(catalog=catalog)


def test_rule_catalog_loaded():
    catalog = load_rules_from_yaml()
    assert catalog.rule_set_version == "0.1.0"
    rule_ids = {r.id for r in catalog.rules}
    expected_ids = {f"R{i:02d}" for i in range(1, 15)}
    assert expected_ids.issubset(rule_ids)


def test_r01_unknown_citation(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c1",
        text="The supplier shall deliver IT equipment conforming to IS 99999: 2015.",
        citations=[
            CitationExtraction(
                raw="IS 99999: 2015",
                span=(54, 69),
                is_number="IS 99999",
                year=2015,
            )
        ],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    r01_findings = [f for f in findings if f.rule_id == "R01"]
    assert len(r01_findings) == 1
    assert r01_findings[0].severity == Severity.CANNOT_VERIFY
    assert "not in our dataset" in r01_findings[0].message_en


def test_r02_superseded_or_withdrawn(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c2",
        text="Material shall conform to IS 999.",
        citations=[
            CitationExtraction(
                raw="IS 999",
                span=(26, 32),
                is_number="IS 999",
            )
        ],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    r02_findings = [f for f in findings if f.rule_id == "R02"]
    assert len(r02_findings) == 1
    assert r02_findings[0].severity == Severity.ERROR
    assert "Withdrawn" in r02_findings[0].message_en
    assert r02_findings[0].evidence.url == "https://standardsbis.bsbedge.com/record/4"


def test_r03_year_differs(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c3",
        text="Deliver laptops conforming to IS/IEC 62368 Part 1: 2019. Registration under CRS is required.",
        products=[
            ProductExtraction(
                text="laptops",
                span=(8, 15),
                canonical_product_id="Laptop / notebook / tablet",
            )
        ],
        citations=[
            CitationExtraction(
                raw="IS/IEC 62368 Part 1: 2019",
                span=(30, 55),
                is_number="IS/IEC 62368 Part 1",
                part="1",
                year=2019,
            )
        ],
        mentions_certification=True,
    )
    findings = engine.evaluate_clause(clause, mock_context)
    r03_findings = [f for f in findings if f.rule_id == "R03"]
    assert len(r03_findings) == 1
    assert r03_findings[0].severity == Severity.WARNING
    assert "2019" in r03_findings[0].message_en
    assert "2023" in r03_findings[0].message_en


def test_r04_part_mismatch(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c4",
        text="Shall conform to IS 13252 (Part 2): 2010.",
        citations=[
            CitationExtraction(
                raw="IS 13252 (Part 2): 2010",
                span=(17, 40),
                is_number="IS 13252 (Part 1)",
                part="2",
                year=2010,
            )
        ],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    r04_findings = [f for f in findings if f.rule_id == "R04"]
    assert len(r04_findings) == 1
    assert r04_findings[0].severity == Severity.WARNING


def test_r05_and_r06_for_laptops(engine, mock_context):
    # Laptop clause cites IS 13252 (Part 1) instead of specified IS/IEC 62368 Part 1, no CRS mention
    clause = ClauseExtraction(
        clause_id="c5",
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
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R05" in rule_ids
    assert "R06" in rule_ids


def test_r07_no_standard_cited(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c6",
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
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R07" in rule_ids
    assert "R06" not in rule_ids  # Because CRS is mentioned


def test_r08_allied_standard_absent(engine, mock_context):
    # Standard IS 13252 (Part 1) has allied link to IS/IEC 62368 Part 1
    clause = ClauseExtraction(
        clause_id="c7",
        text="IT equipment shall conform to IS 13252 (Part 1): 2010.",
        products=[
            ProductExtraction(
                text="IT equipment",
                span=(0, 12),
                canonical_product_id="IT equipment (general)",
            )
        ],
        citations=[
            CitationExtraction(
                raw="IS 13252 (Part 1): 2010",
                span=(30, 54),
                is_number="IS 13252 (Part 1)",
                part="1",
                year=2010,
            )
        ],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    r08_findings = [f for f in findings if f.rule_id == "R08"]
    assert len(r08_findings) == 1
    assert r08_findings[0].severity == Severity.INFO


def test_r09_vague_wording(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c8",
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
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    # Decision B2: both R07 and R09 fire
    assert "R07" in rule_ids
    assert "R09" in rule_ids


def test_r10_abstain_unmapped_product(engine, mock_context):
    clause = ClauseExtraction(
        clause_id="c9",
        text="The supplier shall deliver 20 portable air purifiers rated for 30 square metres.",
        products=[
            ProductExtraction(
                text="portable air purifiers",
                span=(30, 52),
                canonical_product_id=None,  # unmapped
            )
        ],
        citations=[],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R10" in rule_ids
    assert findings[0].severity == Severity.CANNOT_VERIFY
    assert findings[0].message_en == "No applicable standard in our dataset."


def test_r11_internal_contradiction(engine, mock_context):
    # Two citations of same standard with different years
    clauses = [
        ClauseExtraction(
            clause_id="c10_1",
            text="Clause 4.1: IT equipment shall conform to IS 13252 (Part 1): 2010.",
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
            clause_id="c10_2",
            text="Clause 9.2: testing shall follow IS 13252 (Part 1): 2008.",
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
    findings = engine.evaluate_document(clauses, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R11" in rule_ids
    assert "R03" in rule_ids  # 2008 differs from catalogue year 2010


def test_r12_malformed_citation_suppresses_r01(engine, mock_context):
    # IS 13253 is a 1-digit typo of IS 13252 (Part 1)
    clause = ClauseExtraction(
        clause_id="c11",
        text="The supplier shall deliver IT equipment conforming to IS 13253 (Part 1): 2010.",
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
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R12" in rule_ids
    # Decision B1: R12 suppresses R01
    assert "R01" not in rule_ids


def test_r13_wrong_product_family(engine, mock_context):
    # Microwave ovens citing IT equipment standard IS 13252 (Part 1)
    clause = ClauseExtraction(
        clause_id="c12",
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
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R13" in rule_ids
    assert "R05" in rule_ids  # Differs from specified IS 302-2-25


def test_r14_stale_row(engine, mock_context):
    # Standard IS 777 has verified_on older than 180 days
    clause = ClauseExtraction(
        clause_id="c13",
        text="Conform to IS 777: 2012.",
        citations=[
            CitationExtraction(
                raw="IS 777: 2012",
                span=(11, 23),
                is_number="IS 777",
                year=2012,
            )
        ],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    rule_ids = {f.rule_id for f in findings}
    assert "R14" in rule_ids


def test_conflict_handling_downgrades_to_cannot_verify(engine, mock_context):
    # Standard IS 888 has is_conflict=True
    clause = ClauseExtraction(
        clause_id="c14",
        text="Conform to IS 888: 2015.",
        citations=[
            CitationExtraction(
                raw="IS 888: 2015",
                span=(11, 23),
                is_number="IS 888",
                year=2015,
            )
        ],
    )
    findings = engine.evaluate_clause(clause, mock_context)
    for f in findings:
        assert f.severity == Severity.CANNOT_VERIFY


def test_database_rule_data_context(engine):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from packages.data.models import (
        Base,
        CertificationRule,
        Product,
        Standard,
    )
    from packages.rules.context import DatabaseRuleDataContext

    db_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(db_engine)

    with Session(db_engine) as session:
        std = Standard(
            is_number="IS/IEC 62368 Part 1",
            part="1",
            title="Audio/video tech equipment",
            publication_year=2023,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/1",
            verified_on=datetime.date(2026, 10, 2),
            verified_by="team",
            evidence_ref="screenshot.png",
        )
        prod = Product(
            canonical_name="Laptop / notebook / tablet",
            family="IT equipment",
            synonyms_en='["laptop", "laptops"]',
            synonyms_hi='["लैपटॉप"]',
            synonyms_other="[]",
        )
        session.add_all([std, prod])
        session.commit()

        cert = CertificationRule(
            product_id=prod.id,
            scheme="CRS",
            specified_standard_id=std.id,
            instrument="Electronics and IT Goods Order",
            source_url="https://bis.gov.in/scheme2",
            verified_on=datetime.date(2026, 10, 2),
            verified_by="team",
            evidence_ref="gazette.pdf",
        )
        session.add(cert)
        session.commit()

        db_context = DatabaseRuleDataContext(session)

        # Evaluate laptop clause with no CRS mentioned -> should fire R06
        clause = ClauseExtraction(
            clause_id="c_db_1",
            text="The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2023.",
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
            mentions_certification=False,
        )

        findings = engine.evaluate_clause(clause, db_context)
        rule_ids = {f.rule_id for f in findings}
        assert "R06" in rule_ids


def test_no_em_dashes_in_rule_messages(engine, mock_context):
    catalog = load_rules_from_yaml()
    em_dash = chr(8212)
    en_dash = chr(8211)
    for rule in catalog.rules:
        assert em_dash not in rule.message_en, f"Em dash in {rule.id} message_en"
        assert en_dash not in rule.message_en, f"En dash in {rule.id} message_en"
        assert em_dash not in rule.name, f"Em dash in {rule.id} name"
        assert en_dash not in rule.name, f"En dash in {rule.id} name"

