from __future__ import annotations

import io
from datetime import UTC, datetime

import docx
import pypdf
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from packages.reports.diff_analyzer import AuditDiffResult, analyze_audit_diff
from packages.reports.docx_generator import generate_docx_report
from packages.reports.exporter import export_csv_report, export_json_report
from packages.reports.pdf_generator import generate_pdf_report


@pytest.fixture
def sample_audit_data():
    audit_meta = {
        "id": "audit-test-m11",
        "document_name": "Tender_Specification_M11.docx",
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": "officer_test",
        "status": "COMPLETED",
        "language_hint": "en",
    }
    clauses = [
        {
            "id": "c1",
            "text": "Cement shall strictly conform to IS 269:1989 for 33 grade ordinary Portland cement.",
            "source_type": "docx",
            "page_number": 1,
            "start_char": 0,
            "end_char": 84,
            "extractions": {
                "citations": [{"raw": "IS 269:1989", "is_number": "269", "year": 1989}],
                "products": [{"text": "Ordinary Portland Cement", "canonical_product_id": "opc-33"}],
                "mentions_certification": False,
                "vague_phrases": [],
            },
        },
        {
            "id": "c2",
            "text": "All fire extinguishers must have ISI mark as per BIS guidelines.",
            "source_type": "docx",
            "page_number": 1,
            "start_char": 85,
            "end_char": 150,
            "extractions": {
                "citations": [],
                "products": [],
                "mentions_certification": True,
                "vague_phrases": [],
            },
        },
    ]
    findings = [
        {
            "id": "f1",
            "clause_id": "c1",
            "rule_id": "R02",
            "severity": "ERROR",
            "message_en": "Standard IS 269:1989 is superseded by IS 269:2015. Please reference the current standard.",
            "message_hi": "मानक IS 269:1989 को IS 269:2015 द्वारा प्रतिस्थापित किया गया है। कृपया वर्तमान मानक का संदर्भ लें।",
            "span": [36, 47],
            "evidence": {
                "url": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails/269",
                "verified_on": "2026-10-02",
                "verified_by": "curator_test",
                "evidence_ref": "Gazette notification S.O. 123(E)",
            },
            "decision": None,
            "decision_reason": None,
        },
        {
            "id": "f2",
            "clause_id": "c2",
            "rule_id": "R05",
            "severity": "WARNING",
            "message_en": "Certification mentioned without citing the specific Indian Standard number.",
            "message_hi": "विशिष्ट भारतीय मानक संख्या का उल्लेख किए बिना प्रमाणन का उल्लेख किया गया है।",
            "span": [29, 37],
            "evidence": {
                "url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/",
                "verified_on": "2026-10-02",
                "verified_by": "curator_test",
                "evidence_ref": "BIS Act 2016 Section 16(1)",
            },
            "decision": "ACCEPTED",
            "decision_reason": "Officer verified mandatory standard requirement.",
        },
    ]
    return audit_meta, clauses, findings


def test_pdf_report_generation(sample_audit_data):
    audit_meta, clauses, findings = sample_audit_data
    pdf_bytes = generate_pdf_report(audit_meta, clauses, findings)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

    # Read back with pypdf to verify it opens and parses cleanly
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    full_text = " ".join([page.extract_text() or "" for page in reader.pages])

    # Check mandatory banner
    banner = "This tool flags issues for the officer to review. It does not approve or reject a tender."
    assert banner in full_text or "flags issues for the officer" in full_text

    # Check evidence link and date for every finding
    for f in findings:
        assert f["rule_id"] in full_text
        assert f["evidence"]["verified_on"] in full_text


def test_docx_report_generation(sample_audit_data):
    audit_meta, clauses, findings = sample_audit_data
    docx_bytes = generate_docx_report(audit_meta, clauses, findings)

    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 2000

    # Read back with python-docx to verify it opens cleanly
    doc = docx.Document(io.BytesIO(docx_bytes))
    doc_text = " ".join([p.text for p in doc.paragraphs])
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                doc_text += " " + cell.text

    assert "This tool flags issues for the officer to review" in doc_text

    # Verify every finding includes evidence url and verified date
    for f in findings:
        assert f["rule_id"] in doc_text
        assert f["evidence"]["verified_on"] in doc_text
        assert f["evidence"]["url"] in doc_text


def test_json_and_csv_reports(sample_audit_data):
    audit_meta, clauses, findings = sample_audit_data
    json_data = export_json_report(audit_meta, clauses, findings)

    assert json_data["audit_id"] == audit_meta["id"]
    assert json_data["total_findings"] == len(findings)
    assert "flags issues for the officer to review" in json_data["banner"]
    for f in json_data["findings"]:
        assert f["evidence"]["url"].startswith("https://")
        assert f["evidence"]["verified_on"] is not None

    csv_text = export_csv_report(audit_meta, clauses, findings)
    assert "Clause ID,Rule ID,Severity" in csv_text
    assert "https://www.services.bis.gov.in" in csv_text
    assert "2026-10-02" in csv_text


def test_audit_diff_analyzer():
    clauses_a = [
        {"id": "c1", "text": "Old text IS 269:1989."},
        {"id": "c2", "text": "Unchanged text."},
    ]
    clauses_b = [
        {"id": "c1", "text": "Updated text IS 269:2015."},
        {"id": "c2", "text": "Unchanged text."},
        {"id": "c3", "text": "New clause IS 456:2000."},
    ]
    findings_a = [
        {
            "id": "f1",
            "clause_id": "c1",
            "rule_id": "R02",
            "severity": "ERROR",
            "message_en": "Outdated standard",
            "evidence": {"url": "https://bis.gov.in", "verified_on": "2026-10-02"},
        },
        {
            "id": "f2",
            "clause_id": "c2",
            "rule_id": "R05",
            "severity": "WARNING",
            "message_en": "Warning 1",
            "evidence": {"url": "https://bis.gov.in", "verified_on": "2026-10-02"},
        },
    ]
    findings_b = [
        {
            "id": "f2",
            "clause_id": "c2",
            "rule_id": "R05",
            "severity": "WARNING",
            "message_en": "Warning 1",
            "evidence": {"url": "https://bis.gov.in", "verified_on": "2026-10-02"},
        },
        {
            "id": "f3",
            "clause_id": "c3",
            "rule_id": "R08",
            "severity": "INFO",
            "message_en": "Allied link",
            "evidence": {"url": "https://bis.gov.in", "verified_on": "2026-10-02"},
        },
    ]

    diff: AuditDiffResult = analyze_audit_diff(
        draft_a_id="draft-1",
        draft_b_id="draft-2",
        clauses_a=clauses_a,
        clauses_b=clauses_b,
        findings_a=findings_a,
        findings_b=findings_b,
    )

    assert len(diff.added_findings) == 1
    assert diff.added_findings[0]["id"] == "f3"
    assert len(diff.resolved_findings) == 1
    assert diff.resolved_findings[0]["id"] == "f1"
    assert len(diff.retained_findings) == 1
    assert diff.retained_findings[0]["id"] == "f2"

    assert len(diff.clause_diff.added) == 1
    assert diff.clause_diff.added[0]["id"] == "c3"
    assert len(diff.clause_diff.modified) == 1
    assert diff.clause_diff.modified[0]["id"] == "c1"
    assert len(diff.clause_diff.unchanged) == 1
    assert diff.clause_diff.unchanged[0]["id"] == "c2"


def test_api_export_and_diff_endpoints():
    from datetime import date

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from apps.api.core.auth import hash_password
    from packages.data.db import get_db
    from packages.data.models import Base, Standard, User

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with TestingSession() as session:
        user = User(
            username="reviewer_test",
            hashed_password=hash_password("password123"),
            role="Reviewer",
            full_name="Reviewer Officer",
        )
        s1 = Standard(
            id=1,
            is_number="IS 269",
            part=None,
            title="Specification for 33 grade ordinary Portland cement",
            publication_year=2015,
            status="Active",
            catalogue_url="https://standardsbis.bsbedge.com/record/269",
            verified_on=date(2026, 10, 2),
            verified_by="curator_test",
            evidence_ref="screenshot269.png",
        )
        session.add_all([user, s1])
        session.commit()

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        # 1. Login to get token
        login_res = client.post(
            "/api/v1/auth/token",
            data={"username": "reviewer_test", "password": "password123"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Draft A
        text_a = "Cement shall conform to IS 269:1989 for construction."
        res_a = client.post(
            "/api/v1/audits",
            json={"text": text_a, "document_name": "Draft_A.txt", "language_hint": "en"},
            headers=headers,
        )
        assert res_a.status_code == 200
        audit_a_id = res_a.json()["id"]

        # 3. Create Draft B (fixed cement standard to IS 269:2015)
        text_b = "Cement shall conform to IS 269:2015 for construction."
        res_b = client.post(
            "/api/v1/audits",
            json={"text": text_b, "document_name": "Draft_B.txt", "language_hint": "en"},
            headers=headers,
        )
        assert res_b.status_code == 200
        audit_b_id = res_b.json()["id"]

        # 4. List audits (History)
        list_res = client.get("/api/v1/audits", headers=headers)
        assert list_res.status_code == 200
        audits_list = list_res.json()
        assert isinstance(audits_list, list)
        assert any(a["id"] == audit_a_id for a in audits_list)

        # 5. Export PDF
        pdf_res = client.get(f"/api/v1/audits/{audit_a_id}/report?format=pdf", headers=headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert "attachment; filename=" in pdf_res.headers.get("content-disposition", "")
        assert pdf_res.content.startswith(b"%PDF")

        # 6. Export DOCX
        docx_res = client.get(f"/api/v1/audits/{audit_a_id}/report?format=docx", headers=headers)
        assert docx_res.status_code == 200
        assert "wordprocessingml.document" in docx_res.headers["content-type"]
        assert "attachment; filename=" in docx_res.headers.get("content-disposition", "")
        assert len(docx_res.content) > 1000

        # 7. Export CSV & JSON
        csv_res = client.get(f"/api/v1/audits/{audit_a_id}/report?format=csv", headers=headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]

        json_res = client.get(f"/api/v1/audits/{audit_a_id}/report?format=json", headers=headers)
        assert json_res.status_code == 200
        assert "total_findings" in json_res.json()

        # 8. Diff between Draft A and Draft B
        diff_res = client.get(f"/api/v1/audits/{audit_a_id}/diff/{audit_b_id}", headers=headers)
        assert diff_res.status_code == 200
        diff_data = diff_res.json()
        assert "resolved_findings" in diff_data
        assert "added_findings" in diff_data
        assert "clause_diff" in diff_data
        # R03 in Draft A was resolved in Draft B (year 1989 corrected to 2015)
        resolved_rule_ids = [f["rule_id"] for f in diff_data["resolved_findings"]]
        assert "R03" in resolved_rule_ids
    finally:
        app.dependency_overrides.clear()


