from __future__ import annotations

import io
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.core.auth import hash_password
from apps.api.main import app
from packages.data.db import get_db
from packages.data.models import Base, Standard, User


@pytest.fixture
def curation_test_setup():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with TestingSession() as session:
        curator = User(
            username="curator_alice",
            hashed_password=hash_password("curatorpass"),
            role="Curator",
            full_name="Alice Curator",
        )
        verifier = User(
            username="verifier_bob",
            hashed_password=hash_password("verifierpass"),
            role="Verifier",
            full_name="Bob Verifier",
        )
        reviewer = User(
            username="officer_carol",
            hashed_password=hash_password("officerpass"),
            role="Reviewer",
            full_name="Carol Officer",
        )
        # Add an initial stale standard
        stale_std = Standard(
            id=101,
            is_number="IS 456",
            title="Plain and reinforced concrete code of practice",
            publication_year=2000,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/456",
            verified_on=date.today() - timedelta(days=200),
            verified_by="curator_old",
            second_checked_by="verifier_old",
            evidence_ref="gazette_2000.pdf",
        )
        session.add_all([curator, verifier, reviewer, stale_std])
        session.commit()

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSession
    app.dependency_overrides.clear()


def test_row_entry_to_verification_flow(curation_test_setup):
    """Test full flow: a row goes from entry to verified without touching the database."""
    client = TestClient(app)

    # 1. Curator Alice logs in
    login_alice = client.post(
        "/api/v1/auth/token",
        data={"username": "curator_alice", "password": "curatorpass"},
    )
    assert login_alice.status_code == 200
    token_alice = login_alice.json()["access_token"]
    headers_alice = {"Authorization": f"Bearer {token_alice}"}

    # 2. Curator Alice creates a new standard row
    create_payload = {
        "is_number": "IS 10600",
        "title": "Industrial safety helmets specifications",
        "publication_year": 2021,
        "status": "Active",
        "catalogue_url": "https://standardsbis.bsbedge.com/record/10600",
        "evidence_ref": "https://bis.gov.in/gazette/helmet_order_2021.pdf",
    }
    create_res = client.post("/api/v1/admin/rows", json=create_payload, headers=headers_alice)
    assert create_res.status_code == 200
    created_std = create_res.json()
    new_id = created_std["id"]
    assert created_std["is_number"] == "IS 10600"
    assert created_std["verified_by"] == "curator_alice"
    assert created_std["second_checked_by"] is None

    # 3. Check verification queue - the row must appear as pending second verification
    queue_res = client.get("/api/v1/admin/queue/unverified", headers=headers_alice)
    assert queue_res.status_code == 200
    unverified_ids = [row["id"] for row in queue_res.json()]
    assert new_id in unverified_ids

    # 4. Curator Alice attempts to sign off on her own row -> MUST be rejected (two-person check)
    self_verify_res = client.post(f"/api/v1/admin/rows/{new_id}/verify", headers=headers_alice)
    assert self_verify_res.status_code == 400
    assert "two-person" in self_verify_res.json()["detail"].lower()

    # 5. Verifier Bob logs in
    login_bob = client.post(
        "/api/v1/auth/token",
        data={"username": "verifier_bob", "password": "verifierpass"},
    )
    assert login_bob.status_code == 200
    token_bob = login_bob.json()["access_token"]
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # 6. Verifier Bob signs off on the row
    verify_res = client.post(f"/api/v1/admin/rows/{new_id}/verify", headers=headers_bob)
    assert verify_res.status_code == 200
    verified_data = verify_res.json()
    assert verified_data["id"] == new_id
    assert verified_data["verified_by"] == "curator_alice"
    assert verified_data["second_checked_by"] == "verifier_bob"

    # 7. Check verification queue again - row must now be gone from unverified queue
    queue_after = client.get("/api/v1/admin/queue/unverified", headers=headers_bob)
    assert queue_after.status_code == 200
    unverified_after_ids = [row["id"] for row in queue_after.json()]
    assert new_id not in unverified_after_ids


def test_staleness_dashboard_and_reverification(curation_test_setup):
    """Test stale standards retrieval and re-verification."""
    client = TestClient(app)
    login_alice = client.post(
        "/api/v1/auth/token",
        data={"username": "curator_alice", "password": "curatorpass"},
    )
    headers = {"Authorization": f"Bearer {login_alice.json()['access_token']}"}

    # Retrieve stale rows (IS 456 was seeded with 200 days old verified_on)
    stale_res = client.get("/api/v1/admin/stale?stale_days=180", headers=headers)
    assert stale_res.status_code == 200
    stale_list = stale_res.json()
    assert any(s["id"] == 101 for s in stale_list)

    # Re-verify the stale standard
    reverify_res = client.post(
        "/api/v1/admin/rows/101/re-verify",
        json={"evidence_ref": "https://bis.gov.in/gazette/reaffirmation_2026.pdf"},
        headers=headers,
    )
    assert reverify_res.status_code == 200
    assert reverify_res.json()["verified_on"] == date.today().isoformat()


def test_bulk_csv_import_with_validation_report(curation_test_setup):
    """Test bulk CSV import with provenance validation report."""
    client = TestClient(app)
    login_alice = client.post(
        "/api/v1/auth/token",
        data={"username": "curator_alice", "password": "curatorpass"},
    )
    headers = {"Authorization": f"Bearer {login_alice.json()['access_token']}"}

    # Valid CSV content + Invalid CSV content (missing source URL and UNVERIFIED marker)
    csv_content = (
        "is_number,title,publication_year,status,catalogue_url,evidence_ref\n"
        "IS 1239,Steel tubes specifications,2018,Active,https://standardsbis.bsbedge.com/record/1239,gazette_1239.pdf\n"
        "IS 9999,Invalid row missing url,2020,Active,,missing_url.pdf\n"
        "IS 8888,Unverified row,2021,Active,https://bis.gov.in/8888,UNVERIFIED evidence\n"
    )

    import_res = client.post(
        "/api/v1/admin/import-csv",
        files={"file": ("curated_batch.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=headers,
    )
    assert import_res.status_code == 200
    report = import_res.json()
    assert report["total_rows"] == 3
    assert report["imported_count"] == 1
    assert report["rejected_count"] == 2
    assert len(report["errors"]) == 2


def test_vague_terms_and_rules_catalogue(curation_test_setup):
    """Test vague terms management and rules catalog endpoints."""
    client = TestClient(app)
    login_alice = client.post(
        "/api/v1/auth/token",
        data={"username": "curator_alice", "password": "curatorpass"},
    )
    headers = {"Authorization": f"Bearer {login_alice.json()['access_token']}"}

    # 1. Add vague term
    vt_res = client.post(
        "/api/v1/admin/vague-terms",
        json={
            "phrase": "latest bis standards",
            "language": "en",
            "explanation": "Tender states latest standards without citing the IS number and edition.",
        },
        headers=headers,
    )
    assert vt_res.status_code == 200
    vt_id = vt_res.json()["id"]

    # 2. List vague terms
    list_vt = client.get("/api/v1/admin/vague-terms", headers=headers)
    assert list_vt.status_code == 200
    assert any(v["id"] == vt_id for v in list_vt.json())

    # 3. List rules catalog
    rules_res = client.get("/api/v1/admin/rules", headers=headers)
    assert rules_res.status_code == 200
    rules = rules_res.json()
    assert len(rules) >= 14
    assert any(r["id"] == "R01" for r in rules)

    # 4. View append-only audit log
    audit_res = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert isinstance(logs, list)
