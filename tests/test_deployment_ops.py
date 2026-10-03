"""Automated test suite for Milestone M15: Deployment and Operations.
Validates:
1. Request tracing and structured logging middleware (X-Request-ID propagation).
2. Liveness and readiness health check endpoints (/health, /health/live, /health/ready).
3. Version endpoint reporting app, rule set, prompt, and data snapshot versions.
4. Database and evidence backup and tested restore with full integrity verification.
5. In-process concurrent load testing harness with SLA latency verification.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.core.config import settings
from apps.api.main import app
from packages.data.backup_restore import create_backup, restore_backup, verify_backup_integrity
from packages.data.db import get_db
from packages.data.models import Base, Product, Standard, User


@pytest.fixture
def test_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with TestingSessionLocal() as session:
        # Seed test standard and user
        std = Standard(
            is_number="IS 10262",
            title="Concrete Mix Proportioning Guidelines",
            publication_year=2019,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/10262",
            verified_on=datetime.now(UTC).date(),
            verified_by="curator1",
            second_checked_by="verifier1",
            evidence_ref="evidence/is10262.png",
        )
        prod = Product(
            canonical_name="Concrete",
            family="Construction Materials",
            synonyms_en='["Ready mix concrete", "RMC", "cement concrete"]',
            synonyms_hi='["कंक्रीट"]',
            synonyms_other="[]",
        )
        officer = User(
            username="officer1",
            email="officer1@example.gov.in",
            full_name="Procurement Officer",
            hashed_password="hashed_pass",
            role="Reviewer",
        )
        session.add_all([std, prod, officer])
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


# --------------------------------------------------------------------------
# 1. Request Tracing and Structured Logging Tests
# --------------------------------------------------------------------------
def test_request_tracing_generates_request_id(client):
    """Verify that requests without X-Request-ID receive a generated request ID in response headers."""
    resp = client.get("/health")
    assert resp.status_code == 200
    req_id = resp.headers.get("X-Request-ID")
    assert req_id is not None
    assert req_id.startswith("req_") or len(req_id) > 8


def test_request_tracing_propagates_existing_request_id(client):
    """Verify that incoming X-Request-ID header is preserved and returned."""
    custom_id = "test-officer-trace-12345"
    resp = client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id


# --------------------------------------------------------------------------
# 2. Health Probes Tests (Liveness & Readiness)
# --------------------------------------------------------------------------
def test_liveness_probe_returns_live(client):
    """Verify /health/live returns HTTP 200 with live status."""
    resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "live"
    assert "timestamp" in data


def test_readiness_probe_returns_ready_when_db_and_rules_healthy(client):
    """Verify /health/ready returns HTTP 200 with database and rules status."""
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["rules_loaded"] is True
    assert "database" in data
    assert "app_version" in data


# --------------------------------------------------------------------------
# 3. Comprehensive Version Endpoint Test
# --------------------------------------------------------------------------
def test_version_endpoint_reports_all_dimensions(client):
    """Verify /api/v1/version returns app, rule set, prompt, and data snapshot versions."""
    resp = client.get("/api/v1/version?include_runtime=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("app") == settings.APP_VERSION
    assert data.get("rule_set") is not None
    assert data.get("prompt") is not None
    assert data.get("data_snapshot") is not None


# --------------------------------------------------------------------------
# 4. Backup and Tested Restore Integrity Tests
# --------------------------------------------------------------------------
def test_backup_and_tested_restore_cycle(test_db_session, tmp_path):
    """Verify complete backup creation, manifest checksum verification, and exact restore."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    obj_store_dir = tmp_path / "object_store"
    obj_store_dir.mkdir(parents=True, exist_ok=True)

    # Put a sample evidence file in object store
    evidence_file = obj_store_dir / "sample_evidence.txt"
    evidence_file.write_text("Public BIS Catalogue Record Screenshot Mock", encoding="utf-8")

    # Step 1: Create backup
    with test_db_session() as db:
        backup_path = create_backup(
            db=db,
            output_dir=backup_dir,
            object_store_path=obj_store_dir,
            app_version="0.1.0",
        )
    assert backup_path.exists()
    assert backup_path.name.endswith(".tar.gz")

    # Step 2: Verify backup archive integrity and manifest
    integrity_report = verify_backup_integrity(backup_path)
    assert integrity_report["valid"] is True
    assert integrity_report["table_counts"]["standards"] >= 1
    assert integrity_report["table_counts"]["products"] >= 1

    # Step 3: Simulate data loss / corruption by wiping tables
    with test_db_session() as db:
        db.query(Standard).delete()
        db.query(Product).delete()
        db.commit()

        # Verify tables are empty
        assert db.scalar(select(Standard)) is None
        assert db.scalar(select(Product)) is None

    # Step 4: Restore backup into target database
    restore_obj_dir = tmp_path / "restored_store"
    with test_db_session() as db:
        restore_result = restore_backup(
            backup_path=backup_path,
            db=db,
            target_object_store_path=restore_obj_dir,
        )

    assert restore_result["status"] == "success"
    assert restore_result["rows_restored"] >= 2
    assert (restore_obj_dir / "sample_evidence.txt").exists()

    # Step 5: Verify restored database contents match original state
    with test_db_session() as db:
        restored_std = db.execute(select(Standard).where(Standard.is_number == "IS 10262")).scalar_one_or_none()
        assert restored_std is not None
        assert restored_std.title == "Concrete Mix Proportioning Guidelines"
        assert restored_std.publication_year == 2019

        restored_prod = db.execute(select(Product).where(Product.canonical_name == "Concrete")).scalar_one_or_none()
        assert restored_prod is not None
        assert "Construction" in restored_prod.family


# --------------------------------------------------------------------------
# 5. Concurrent Load Testing Harness Test
# --------------------------------------------------------------------------
def test_in_process_load_test_meets_latency_sla(client):
    """Verify that concurrent requests meet latency SLA with zero error rate."""
    from scripts.load_test import run_in_process_load_test

    results = run_in_process_load_test(
        client=client,
        concurrency=5,
        total_requests=25,
    )

    assert results["total_requests"] == 25
    assert results["failed_requests"] == 0
    assert results["error_rate"] == 0.0
    # p95 latency should be well under 500ms for in-process queries
    assert results["p95_ms"] < 500.0
    assert results["requests_per_second"] > 10.0
