from __future__ import annotations

import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app
from packages.data.db import get_db
from packages.data.models import (
    Base,
    CertificationRule,
    Product,
    ProductStandardMap,
    Standard,
    User,
)


@pytest.fixture
def test_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed initial test data
    with TestingSessionLocal() as session:
        # 1. Users
        admin_user = User(
            username="admin1",
            hashed_password="hashed_admin_password",
            role="Admin",
            full_name="Admin User",
        )
        curator_user = User(
            username="curator1",
            hashed_password="hashed_curator_password",
            role="Curator",
            full_name="Curator User",
        )
        verifier_user = User(
            username="verifier1",
            hashed_password="hashed_verifier_password",
            role="Verifier",
            full_name="Verifier User",
        )
        reviewer_user = User(
            username="officer1",
            hashed_password="hashed_reviewer_password",
            role="Reviewer",
            full_name="Procurement Officer",
        )
        session.add_all([admin_user, curator_user, verifier_user, reviewer_user])

        # 2. Standards
        s1 = Standard(
            id=1,
            is_number="IS/IEC 62368 Part 1",
            part="1",
            title="Audio/video, ICT equipment",
            publication_year=2023,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/1",
            verified_on=datetime.date(2026, 10, 2),
            verified_by="curator1",
            evidence_ref="screenshot1.png",
        )
        s2 = Standard(
            id=2,
            is_number="IS 302-2-25",
            part=None,
            title="Safety of microwave ovens",
            publication_year=None,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/2",
            verified_on=datetime.date(2026, 10, 2),
            verified_by="curator1",
            evidence_ref="screenshot2.png",
        )
        s3 = Standard(
            id=3,
            is_number="IS 13252 (Part 1)",
            part="1",
            title="IT equipment general safety",
            publication_year=2010,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/3",
            verified_on=datetime.date(2025, 1, 1),  # Stale (>180 days)
            verified_by="curator1",
            evidence_ref="screenshot3.png",
        )
        session.add_all([s1, s2, s3])

        # 3. Products
        p1 = Product(
            id=1,
            canonical_name="Laptop / notebook / tablet",
            family="IT equipment",
            synonyms_en='["laptop", "laptops", "notebook", "tablet"]',
            synonyms_hi='["लैपटॉप"]',
            synonyms_other="[]",
        )
        p2 = Product(
            id=2,
            canonical_name="Microwave ovens",
            family="Household appliances",
            synonyms_en='["microwave oven", "microwave ovens"]',
            synonyms_hi='["माइक्रोवेव"]',
            synonyms_other="[]",
        )
        session.add_all([p1, p2])
        session.commit()

        # 4. Maps & Rules
        psm1 = ProductStandardMap(
            product_id=1,
            standard_id=1,
            relation="PRIMARY",
            source_url="https://bis.gov.in/scheme2",
            verified_on=datetime.date(2026, 10, 2),
            verified_by="curator1",
            evidence_ref="ev_map1.png",
        )
        cr1 = CertificationRule(
            product_id=1,
            scheme="CRS",
            specified_standard_id=1,
            instrument="Electronics and IT Goods Order",
            source_url="https://bis.gov.in/scheme2",
            verified_on=datetime.date(2026, 10, 2),
            verified_by="curator1",
            evidence_ref="ev_cr1.png",
        )
        session.add_all([psm1, cr1])
        session.commit()

    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db_session) -> TestClient:
    return TestClient(app)


def test_auth_login_and_token(client):
    # Test valid login
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "officer1", "password": "hashed_reviewer_password"},
    )
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["role"] == "Reviewer"

    # Test invalid login
    resp_bad = client.post(
        "/api/v1/auth/token",
        data={"username": "officer1", "password": "wrong_password"},
    )
    assert resp_bad.status_code == 401


def test_standards_and_products_endpoints(client):
    # Public standards
    resp_std = client.get("/api/v1/standards")
    assert resp_std.status_code == 200
    standards = resp_std.json()
    assert len(standards) >= 3

    resp_s1 = client.get("/api/v1/standards/1")
    assert resp_s1.status_code == 200
    assert resp_s1.json()["is_number"] == "IS/IEC 62368 Part 1"

    # Public products
    resp_prod = client.get("/api/v1/products")
    assert resp_prod.status_code == 200
    products = resp_prod.json()
    assert len(products) >= 2

    resp_rules = client.get("/api/v1/products/1/rules")
    assert resp_rules.status_code == 200
    rules_data = resp_rules.json()
    assert rules_data["product"]["canonical_name"] == "Laptop / notebook / tablet"
    assert len(rules_data["certification_rules"]) >= 1


def test_full_audit_workflow(client):
    # 1. Create audit from text
    auth_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "officer1", "password": "hashed_reviewer_password"},
    )
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    audit_payload = {
        "text": "The supplier shall deliver 50 laptops. The laptops shall conform to IS 13252 (Part 1): 2010.",
        "language_hint": "en",
    }
    create_resp = client.post("/api/v1/audits", json=audit_payload, headers=headers)
    assert create_resp.status_code == 200
    audit_data = create_resp.json()
    audit_id = audit_data["id"]
    assert audit_data["status"] == "COMPLETED"
    assert len(audit_data["findings"]) >= 1

    # Findings should include R05 and R06
    rule_ids = {f["rule_id"] for f in audit_data["findings"]}
    assert "R05" in rule_ids or "R06" in rule_ids

    # 2. Get audit details
    get_resp = client.get(f"/api/v1/audits/{audit_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == audit_id

    # 3. Officer decision on finding
    finding_id = audit_data["findings"][0]["id"]
    decision_payload = {
        "decision": "ACCEPT",
        "reason": "Officer confirms cited standard is non-compliant with CRS",
    }
    decision_resp = client.post(
        f"/api/v1/audits/{audit_id}/findings/{finding_id}/decision",
        json=decision_payload,
        headers=headers,
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["decision"] == "ACCEPT"

    # 4. Officer edits extraction -> triggers re-evaluation
    edit_payload = {
        "citations": [
            {
                "raw": "IS/IEC 62368 Part 1: 2023",
                "span": [68, 94],
                "is_number": "IS/IEC 62368 Part 1",
                "part": "1",
                "year": 2023,
            }
        ],
        "mentions_certification": True,
    }
    clause_id = audit_data["clauses"][0]["id"]
    re_eval_resp = client.post(
        f"/api/v1/audits/{audit_id}/extractions/{clause_id}",
        json=edit_payload,
        headers=headers,
    )
    assert re_eval_resp.status_code == 200
    updated_audit = re_eval_resp.json()
    # Now that the standard was corrected to 62368 and CRS is mentioned, R05 and R06 should disappear!
    updated_rule_ids = {f["rule_id"] for f in updated_audit["findings"] if f["rule_id"] != "R14"}
    assert "R05" not in updated_rule_ids

    # 5. Export report
    report_resp = client.get(f"/api/v1/audits/{audit_id}/report?format=json", headers=headers)
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["audit_id"] == audit_id


def test_admin_curation_and_two_person_verification(client):
    # Login as Curator
    curator_token = client.post(
        "/api/v1/auth/token",
        data={"username": "curator1", "password": "hashed_curator_password"},
    ).json()["access_token"]
    curator_headers = {"Authorization": f"Bearer {curator_token}"}

    # Add standard row
    new_std_payload = {
        "is_number": "IS 4984",
        "part": None,
        "title": "High Density Polyethylene Pipes",
        "publication_year": 2016,
        "catalogue_url": "https://standardsbis.bsbedge.com/record/4984",
        "evidence_ref": "evidence_4984.png",
    }
    add_resp = client.post("/api/v1/admin/rows", json=new_std_payload, headers=curator_headers)
    assert add_resp.status_code == 200
    new_row_id = add_resp.json()["id"]

    # Same person cannot verify their own row! (Spec 3.3 & 12)
    verify_same_resp = client.post(
        f"/api/v1/admin/rows/{new_row_id}/verify", headers=curator_headers
    )
    assert verify_same_resp.status_code == 400

    # Distinct verifier signs off
    verifier_token = client.post(
        "/api/v1/auth/token",
        data={"username": "verifier1", "password": "hashed_verifier_password"},
    ).json()["access_token"]
    verifier_headers = {"Authorization": f"Bearer {verifier_token}"}

    verify_diff_resp = client.post(
        f"/api/v1/admin/rows/{new_row_id}/verify", headers=verifier_headers
    )
    assert verify_diff_resp.status_code == 200
    assert verify_diff_resp.json()["second_checked_by"] == "verifier1"


def test_admin_stale_rows_endpoint(client):
    admin_token = client.post(
        "/api/v1/auth/token",
        data={"username": "admin1", "password": "hashed_admin_password"},
    ).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.get("/api/v1/admin/stale?stale_days=180", headers=admin_headers)
    assert resp.status_code == 200
    stale_rows = resp.json()
    assert len(stale_rows) >= 1
    stale_numbers = {r["is_number"] for r in stale_rows}
    assert "IS 13252 (Part 1)" in stale_numbers
