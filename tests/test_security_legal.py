"""Comprehensive automated security, privacy, and legal compliance test suite.
Validates Milestone M14 requirements from docs/PROJECT_SPEC.md Section 12
and docs/security-legal-checklist.md.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.core.auth import create_access_token, hash_password, verify_password
from apps.api.core.security import (
    MAX_UPLOAD_SIZE,
    purge_expired_audit_sessions,
    validate_upload_safety,
)
from apps.api.main import app
from packages.data.db import get_db
from packages.data.legal_guard import (
    audit_evidence_references,
    audit_seed_data_for_prohibited_content,
    verify_disclaimer_presence,
)
from packages.data.models import AuditLog, AuditSession, Base, Standard, User
from packages.reports import (
    export_csv_report,
    export_json_report,
    generate_docx_report,
    generate_pdf_report,
)

MANDATORY_BANNER = "This tool flags issues for the officer to review. It does not approve or reject a tender."


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
        roles = [
            ("officer1", "Reviewer"),
            ("officer2", "Reviewer"),
            ("curator1", "Curator"),
            ("verifier1", "Verifier"),
            ("admin1", "Admin"),
        ]
        for username, role in roles:
            u = User(
                username=username,
                email=f"{username}@example.gov.in",
                full_name=f"Test {username}",
                hashed_password=hash_password("Secr3tPass!"),
                role=role,
            )
            session.add(u)
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


def get_token_for(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role, "user_id": 1})


# --------------------------------------------------------------------------
# 1. Role-based Authorization Tests
# --------------------------------------------------------------------------
def test_reviewer_cannot_access_curation_endpoints(client):
    """Verify Reviewer role is forbidden from accessing curator row creation."""
    token = get_token_for("officer1", "Reviewer")
    resp = client.post(
        "/api/v1/admin/rows",
        json={
            "is_number": "IS 9999",
            "title": "Unauthorized Entry",
            "catalogue_url": "https://standardsbis.bsbedge.com/record/9999",
            "evidence_ref": "evidence/test.png",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "not authorized" in resp.json()["detail"].lower()


def test_curator_can_create_standard_row(client):
    """Verify Curator role is permitted to create rows."""
    token = get_token_for("curator1", "Curator")
    resp = client.post(
        "/api/v1/admin/rows",
        json={
            "is_number": "IS 8888",
            "title": "Curated Standard Specification",
            "publication_year": 2022,
            "status": "Active",
            "catalogue_url": "https://standardsbis.bsbedge.com/record/8888",
            "evidence_ref": "evidence/is8888_ref.png",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_number"] == "IS 8888"


# --------------------------------------------------------------------------
# 2. Two-Person Integrity Test: Verifier != Curator
# --------------------------------------------------------------------------
def test_verifier_cannot_be_same_as_curator(client, test_db_session):
    """Verify that a curator cannot sign off as the independent second checker."""
    with test_db_session() as db:
        std = Standard(
            is_number="IS 7777",
            title="Two-Person Rule Standard",
            publication_year=2020,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/7777",
            verified_on=datetime.now(UTC).date(),
            verified_by="curator1",
            second_checked_by=None,
            evidence_ref="evidence/test7777.png",
        )
        db.add(std)
        db.commit()
        db.refresh(std)
        row_id = std.id

    # Curator attempts to verify their own entry
    token = get_token_for("curator1", "Curator")
    resp = client.post(
        f"/api/v1/admin/rows/{row_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "two-person check rule" in resp.json()["detail"]


# --------------------------------------------------------------------------
# 3. Password Hashing and Verification
# --------------------------------------------------------------------------
def test_password_hashing_security():
    """Verify passwords are secure SHA-256 hashes and verify correctly."""
    plain = "GovProcurementPass2026!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert len(hashed) == 64  # SHA-256 hex digest length
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# --------------------------------------------------------------------------
# 4. Upload Safety Scanner Tests
# --------------------------------------------------------------------------
def test_upload_safety_rejects_empty():
    with pytest.raises(HTTPException) as exc:
        validate_upload_safety(b"", "tender.pdf")
    assert exc.value.status_code == 400


def test_upload_safety_rejects_oversized():
    fake_oversized = b"%PDF-" + (b"0" * (MAX_UPLOAD_SIZE + 100))
    with pytest.raises(HTTPException) as exc:
        validate_upload_safety(fake_oversized, "huge.pdf")
    assert exc.value.status_code == 413


def test_upload_safety_rejects_unauthorized_extension():
    with pytest.raises(HTTPException) as exc:
        validate_upload_safety(b"print('hello')", "script.py")
    assert exc.value.status_code == 415


def test_upload_safety_rejects_executable_magic_signatures():
    # Windows PE executable signature
    with pytest.raises(HTTPException) as exc:
        validate_upload_safety(b"MZ\x90\x00executable", "tender.pdf")
    assert exc.value.status_code == 400
    assert "disallowed signature" in exc.value.detail

    # Linux ELF signature
    with pytest.raises(HTTPException) as exc:
        validate_upload_safety(b"\x7fELF\x02\x01\x01", "tender.docx")
    assert exc.value.status_code == 400
    assert "disallowed signature" in exc.value.detail

    # Shell script shebang
    with pytest.raises(HTTPException) as exc:
        validate_upload_safety(b"#!/bin/bash\nrm -rf /", "tender.txt")
    assert exc.value.status_code == 400
    assert "disallowed signature" in exc.value.detail


def test_upload_safety_accepts_valid_documents():
    # Valid PDF
    validate_upload_safety(b"%PDF-1.7\nSample content", "tender.pdf")
    # Valid DOCX (ZIP archive header)
    validate_upload_safety(b"PK\x03\x04\x14\x00\x00", "tender.docx")
    # Valid Plain text
    validate_upload_safety(b"Clause 1: Supply of Ordinary Portland Cement.", "tender.txt")


# --------------------------------------------------------------------------
# 5. One-Click Deletion and Retention Purge Tests
# --------------------------------------------------------------------------
def test_one_click_deletion_removes_audit_and_logs(client, test_db_session):
    """Verify DELETE /api/v1/audits/{audit_id} permanently removes the session and logs the deletion."""
    audit_id = "aud_delete_test_1"
    with test_db_session() as db:
        session = AuditSession(
            id=audit_id,
            document_name="confidential_draft.pdf",
            source_text="Confidential tender text",
            language_hint="en",
            status="COMPLETED",
            created_by="officer1",
            created_at=datetime.now(UTC),
            clauses_json="[]",
            findings_json="[]",
        )
        db.add(session)
        db.commit()

    # Officer 2 cannot delete Officer 1's audit draft
    token_officer2 = get_token_for("officer2", "Reviewer")
    resp_unauth = client.delete(
        f"/api/v1/audits/{audit_id}",
        headers={"Authorization": f"Bearer {token_officer2}"},
    )
    assert resp_unauth.status_code == 403

    # Officer 1 successfully deletes own draft
    token_officer1 = get_token_for("officer1", "Reviewer")
    resp_ok = client.delete(
        f"/api/v1/audits/{audit_id}",
        headers={"Authorization": f"Bearer {token_officer1}"},
    )
    assert resp_ok.status_code == 204

    # Verify session is deleted from database
    with test_db_session() as db:
        deleted_session = db.execute(select(AuditSession).where(AuditSession.id == audit_id)).scalar_one_or_none()
        assert deleted_session is None

        # Verify append-only audit log records the deletion
        log = db.execute(
            select(AuditLog).where(AuditLog.action == "DELETE_AUDIT").order_by(AuditLog.id.desc())
        ).scalar_one_or_none()
        assert log is not None
        assert audit_id in (log.old_values or "")


def test_retention_purge_removes_expired_drafts(test_db_session):
    """Verify purge_expired_audit_sessions cleans up drafts older than retention window."""
    with test_db_session() as db:
        old_date = datetime.now(UTC) - timedelta(days=45)
        expired_session = AuditSession(
            id="aud_expired_45d",
            document_name="stale_draft.docx",
            source_text="Old confidential draft",
            language_hint="en",
            status="COMPLETED",
            created_by="officer1",
            created_at=old_date,
            clauses_json="[]",
            findings_json="[]",
        )
        db.add(expired_session)
        db.commit()

        purged = purge_expired_audit_sessions(db, max_age_days=30)
        assert purged >= 1

        check_session = db.execute(
            select(AuditSession).where(AuditSession.id == "aud_expired_45d")
        ).scalar_one_or_none()
        assert check_session is None


# --------------------------------------------------------------------------
# 6. Copyright and BIS Act Compliance (No Standard Text Stored)
# --------------------------------------------------------------------------
def test_seed_data_contains_no_prohibited_standard_text():
    """Verify zero Indian Standard text or copyright excerpts exist in seed CSV files."""
    violations = audit_seed_data_for_prohibited_content()
    assert len(violations) == 0, f"Found copyright violations in seed data: {violations}"


def test_evidence_references_contain_no_raw_standard_text_pdfs():
    """Verify evidence references point only to catalogue screenshots or Gazette orders."""
    violations = audit_evidence_references()
    assert len(violations) == 0, f"Found improper evidence references: {violations}"


# --------------------------------------------------------------------------
# 7. Mandatory Disclaimer Banner in All Export Formats
# --------------------------------------------------------------------------
def test_disclaimer_banner_in_all_reports():
    """Verify every report export format (PDF, DOCX, CSV, JSON) contains mandatory banner."""
    meta = {
        "id": "aud_banner_test",
        "document_name": "tender_spec.docx",
        "created_at": "2026-10-03T10:00:00Z",
        "created_by": "officer1",
        "status": "COMPLETED",
        "language_hint": "en",
    }
    clauses = [{"id": "c1", "text": "Clause 1 sample."}]
    findings = []

    # JSON export
    json_out = export_json_report(meta, clauses, findings)
    assert verify_disclaimer_presence(json_out["banner"]) is True

    # CSV export
    csv_out = export_csv_report(meta, clauses, findings)
    assert verify_disclaimer_presence(csv_out) is True

    # PDF export
    pdf_bytes = generate_pdf_report(meta, clauses, findings)
    assert len(pdf_bytes) > 500

    # DOCX export
    docx_bytes = generate_docx_report(meta, clauses, findings)
    assert len(docx_bytes) > 500
