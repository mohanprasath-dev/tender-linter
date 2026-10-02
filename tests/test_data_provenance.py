from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from packages.data.loader import load_seed_data
from packages.data.models import (
    AuditLog,
    Base,
    Product,
    ProductStandardMap,
    Standard,
)


@pytest.fixture
def db_session() -> Session:
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_valid_standard_insertion_succeeds(db_session: Session) -> None:
    std = Standard(
        is_number="IS 13252",
        part="1",
        title="Information Technology Equipment - Safety",
        publication_year=2010,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/13252",
        verified_on=date(2026, 10, 2),
        verified_by="Ananya",
        second_checked_by="Rohan",
        evidence_ref="evidence/is13252_catalogue.png",
    )
    db_session.add(std)
    db_session.commit()
    assert std.id is not None
    assert std.is_number == "IS 13252"


def test_standard_missing_catalogue_url_fails(db_session: Session) -> None:
    with pytest.raises(ValueError, match="catalogue_url"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment",
            catalogue_url="",  # Empty URL
            verified_on=date(2026, 10, 2),
            verified_by="Ananya",
            evidence_ref="evidence/test.png",
        )


def test_standard_invalid_url_scheme_fails(db_session: Session) -> None:
    with pytest.raises(ValueError, match="https://"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment",
            catalogue_url="http://insecure.example.com",  # Must be https://
            verified_on=date(2026, 10, 2),
            verified_by="Ananya",
            evidence_ref="evidence/test.png",
        )


def test_standard_missing_verified_on_fails(db_session: Session) -> None:
    with pytest.raises(ValueError, match="verified_on"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment",
            catalogue_url="https://example.com/record",
            verified_on=None,
            verified_by="Ananya",
            evidence_ref="evidence/test.png",
        )


def test_standard_missing_verified_by_fails(db_session: Session) -> None:
    with pytest.raises(ValueError, match="verified_by"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment",
            catalogue_url="https://example.com/record",
            verified_on=date(2026, 10, 2),
            verified_by="",
            evidence_ref="evidence/test.png",
        )


def test_standard_missing_evidence_ref_fails(db_session: Session) -> None:
    with pytest.raises(ValueError, match="evidence_ref"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment",
            catalogue_url="https://example.com/record",
            verified_on=date(2026, 10, 2),
            verified_by="Ananya",
            evidence_ref="",
        )


def test_second_checker_must_differ_from_verifier(db_session: Session) -> None:
    with pytest.raises(ValueError, match="second_checked_by must differ"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment",
            catalogue_url="https://example.com/record",
            verified_on=date(2026, 10, 2),
            verified_by="Ananya",
            second_checked_by="Ananya",  # Same person
            evidence_ref="evidence/test.png",
        )


def test_unverified_content_rejected(db_session: Session) -> None:
    with pytest.raises(ValueError, match="prohibited term 'UNVERIFIED'"):
        Standard(
            is_number="IS 13252",
            title="Information Technology Equipment UNVERIFIED draft",
            catalogue_url="https://example.com/record",
            verified_on=date(2026, 10, 2),
            verified_by="Ananya",
            evidence_ref="evidence/test.png",
        )


def test_product_standard_map_provenance_constraints(db_session: Session) -> None:
    prod = Product(canonical_name="Laptop", family="IT equipment")
    db_session.add(prod)
    std = Standard(
        is_number="IS 13252",
        title="IT Safety",
        catalogue_url="https://example.com/rec",
        verified_on=date(2026, 10, 2),
        verified_by="Ananya",
        evidence_ref="evidence/ref.png",
    )
    db_session.add(std)
    db_session.commit()

    # Map with missing source URL should fail validation
    with pytest.raises(ValueError, match="source_url"):
        ProductStandardMap(
            product_id=prod.id,
            standard_id=std.id,
            relation="PRIMARY",
            source_url="",
            verified_on=date(2026, 10, 2),
            verified_by="Ananya",
            evidence_ref="evidence/ref.png",
        )

    # Map with valid provenance succeeds
    good_map = ProductStandardMap(
        product_id=prod.id,
        standard_id=std.id,
        relation="PRIMARY",
        source_url="https://example.com/mapping",
        verified_on=date(2026, 10, 2),
        verified_by="Ananya",
        second_checked_by="Rohan",
        evidence_ref="evidence/ref.png",
    )
    db_session.add(good_map)
    db_session.commit()
    assert good_map.id is not None


def test_audit_log_records_insertions_and_updates(db_session: Session) -> None:
    std = Standard(
        is_number="IS 302-2-25",
        title="Microwave ovens",
        catalogue_url="https://example.com/record",
        verified_on=date(2026, 10, 2),
        verified_by="Ananya",
        evidence_ref="evidence/mwave.png",
    )
    db_session.add(std)
    db_session.commit()

    # Verify audit log recorded INSERT
    logs = db_session.query(AuditLog).filter_by(table_name="standards", record_id=std.id).all()
    assert len(logs) >= 1
    assert logs[0].action == "INSERT"
    assert "is_number" in (logs[0].new_values or "")

    # Perform UPDATE
    std.publication_year = 2014
    db_session.commit()

    update_logs = (
        db_session.query(AuditLog)
        .filter_by(table_name="standards", record_id=std.id, action="UPDATE")
        .all()
    )
    assert len(update_logs) >= 1


def test_seed_loader_validation(db_session: Session, tmp_path: Path) -> None:
    # Test that seed loader rejects files with unverified entries or missing provenance
    invalid_csv = tmp_path / "standards.csv"
    invalid_csv.write_text(
        "is_number,title,catalogue_url,publication_year,status,verified_on,verified_by,second_checked_by,evidence_ref\n"
        "IS 9999,Unverified Test,https://example.com,2020,Active,2026-10-02,Alice,Alice,ref1\n",  # Same verifier & checker
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_seed_data(db_session, seed_dir=tmp_path)


def test_seed_loader_loads_valid_fixture(db_session: Session, tmp_path: Path) -> None:
    # Test that seed loader successfully loads valid curated rows
    std_csv = tmp_path / "standards.csv"
    std_csv.write_text(
        "is_number,part,section,title,publication_year,status,catalogue_url,verified_on,verified_by,second_checked_by,evidence_ref\n"
        "IS 13252,1,,IT Equipment Safety,2010,Active,https://standardsbis.bsbedge.com/rec/13252,2026-10-02,Ananya,Rohan,evidence/is13252.png\n",
        encoding="utf-8",
    )
    prod_csv = tmp_path / "products.csv"
    prod_csv.write_text(
        "canonical_name,family,synonyms_en,synonyms_hi,synonyms_other\n"
        'Laptop,IT equipment,["Notebook"],[],[]\n',
        encoding="utf-8",
    )
    map_csv = tmp_path / "product_standard_map.csv"
    map_csv.write_text(
        "product,is_number,relation,source_url,verified_on,verified_by,second_checked_by,evidence_ref\n"
        "Laptop,IS 13252,PRIMARY,https://bis.gov.in/scheme2,2026-10-02,Ananya,Rohan,evidence/map.png\n",
        encoding="utf-8",
    )

    counts = load_seed_data(db_session, seed_dir=tmp_path)
    assert counts.get("standards") == 1
    assert counts.get("products") == 1
    assert counts.get("product_standard_map") == 1


def test_seed_loader_rejects_uncurated_initial_seed(db_session: Session) -> None:
    # M2 has not run yet, so initial uncurated seed data must fail provenance check
    seed_dir = Path(__file__).resolve().parent.parent / "packages" / "data" / "seed"
    with pytest.raises(ValueError, match="failed provenance check"):
        load_seed_data(db_session, seed_dir=seed_dir)
