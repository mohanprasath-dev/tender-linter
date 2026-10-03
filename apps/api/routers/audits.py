from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.auth import get_current_user, require_role
from apps.api.core.security import (
    delete_audit_session,
    purge_expired_audit_sessions,
    validate_upload_safety,
)
from apps.api.schemas.audits import (
    AuditCreateRequest,
    AuditDiffResponse,
    AuditResponse,
    AuditSummaryResponse,
    ClauseResponse,
    ExtractionEditRequest,
    FindingDecisionRequest,
    FindingResponse,
)
from packages.data.db import get_db
from packages.data.models import AuditLog, AuditSession, User
from packages.extraction import RegexExtractor, validate_extraction_spans
from packages.ingestion import IngestionService
from packages.mapping.product_mapper import ProductMapper
from packages.reports import (
    analyze_audit_diff,
    export_csv_report,
    export_json_report,
    generate_docx_report,
    generate_pdf_report,
)
from packages.rules.context import create_rule_context_from_db
from packages.rules.engine import CERTIFICATION_TERMS_LOWER, RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
    VaguePhraseExtraction,
)

router = APIRouter(prefix="/audits", tags=["audits"])

# Cache loaded rules catalog
_RULES_CATALOG = load_rules_from_yaml()


def _run_clause_audit(
    clause_id: str,
    clause_text: str,
    language_hint: str,
    db: Session,
    override_extractions: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract entities and evaluate rules for a single clause."""
    rules_engine = RulesEngine(_RULES_CATALOG)
    rule_context = create_rule_context_from_db(db)

    if override_extractions is not None:
        # Use officer-edited extractions
        citations_data = override_extractions.get("citations", [])
        citations = [
            CitationExtraction(
                raw=c.get("raw", ""),
                span=tuple(c["span"]) if "span" in c and c["span"] else (0, 0),
                is_number=c.get("is_number", ""),
                part=c.get("part"),
                section=c.get("section"),
                year=c.get("year"),
            )
            for c in citations_data
        ]
        mentions_cert = override_extractions.get(
            "mentions_certification",
            any(term in clause_text.lower() for term in CERTIFICATION_TERMS_LOWER),
        )
        products_data = override_extractions.get("products", [])
        products = [
            ProductExtraction(
                text=p.get("text", ""),
                span=tuple(p["span"]) if "span" in p and p["span"] else (0, 0),
                canonical_product_id=p.get("canonical_product_id"),
            )
            for p in products_data
        ]
        vague_data = override_extractions.get("vague_phrases", [])
        vague_phrases = [
            VaguePhraseExtraction(
                text=v.get("text", ""),
                span=tuple(v["span"]) if "span" in v and v["span"] else (0, 0),
                phrase=v.get("phrase"),
                explanation=v.get("explanation"),
            )
            for v in vague_data
        ]
    else:
        # 1. Regex citation extraction + span validation
        extractor = RegexExtractor()
        extracted = extractor.extract(clause_text)
        extraction_dict = extracted.model_dump() if hasattr(extracted, "model_dump") else extracted
        cleaned_dict, _, _ = validate_extraction_spans(clause_text, extraction_dict)
        citations = [
            CitationExtraction(
                raw=c["raw"],
                span=tuple(c["span"]) if "span" in c and c["span"] else (0, 0),
                is_number=c["is_number"],
                part=c.get("part"),
                section=c.get("section"),
                year=c.get("year"),
            )
            for c in cleaned_dict.get("citations", [])
        ]

        # 2. Product mapping
        products_list = list(rule_context._products.values())
        mapper = ProductMapper(products=products_list)
        map_res = mapper.map_product(clause_text)
        products = []
        if not map_res.is_unmapped and map_res.canonical_name:
            products.append(
                ProductExtraction(
                    text=map_res.canonical_name,
                    span=(0, len(clause_text)),
                    canonical_product_id=map_res.canonical_product_id,
                )
            )

        # 3. Certification mention check
        mentions_cert = any(term in clause_text.lower() for term in CERTIFICATION_TERMS_LOWER)
        vague_phrases = []

    clause_obj = ClauseExtraction(
        clause_id=clause_id,
        text=clause_text,
        language=language_hint,
        products=products,
        citations=citations,
        vague_phrases=vague_phrases,
        mentions_certification=mentions_cert,
    )

    rule_findings = rules_engine.evaluate_clause(clause_obj, rule_context)

    extractions_payload = {
        "citations": [c.model_dump() for c in citations],
        "products": [p.model_dump() for p in products],
        "mentions_certification": mentions_cert,
        "vague_phrases": [v.model_dump() for v in vague_phrases],
    }

    findings_payload = []
    for rf in rule_findings:
        findings_payload.append(
            {
                "id": rf.id,
                "rule_id": rf.rule_id,
                "severity": rf.severity.value,
                "clause_id": rf.clause_id,
                "span": list(rf.span) if rf.span else None,
                "message_en": rf.message_en,
                "message_hi": rf.message_hi,
                "evidence": rf.evidence.model_dump() if rf.evidence else None,
                "decision": None,
                "decision_reason": None,
                "rule_set_version": rules_engine.version,
                "model_version": "regex-baseline",
                "prompt_version": "v1",
            }
        )

    return extractions_payload, findings_payload


@router.post("", response_model=AuditResponse)
def create_audit(
    audit_in: AuditCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditResponse:
    """Create a new tender audit session, run extractions, and evaluate rules."""
    audit_id = f"aud_{uuid.uuid4().hex[:10]}"
    source_text = audit_in.text.strip()
    if not source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender specification text cannot be empty",
        )

    ingest_svc = IngestionService()
    parsed_doc = ingest_svc.ingest_text(source_text, filename=audit_in.document_name or "pasted.txt")

    clauses_data = []
    all_findings = []

    for seg in parsed_doc.clauses:
        extractions, findings = _run_clause_audit(
            clause_id=seg.id,
            clause_text=seg.text,
            language_hint=audit_in.language_hint or seg.language,
            db=db,
        )
        clauses_data.append({
            "id": seg.id,
            "text": seg.text,
            "extractions": extractions,
            "page_number": seg.page_number,
            "start_char": seg.start_char,
            "end_char": seg.end_char,
            "source_type": seg.source_type,
        })
        all_findings.extend(findings)

    audit_session = AuditSession(
        id=audit_id,
        document_name=audit_in.document_name,
        source_text=source_text,
        language_hint=audit_in.language_hint,
        status="COMPLETED",
        created_by=current_user.username,
        created_at=datetime.now(UTC),
        clauses_json=json.dumps(clauses_data),
        findings_json=json.dumps(all_findings),
    )
    db.add(audit_session)

    # Append to audit log
    audit_log_entry = AuditLog(
        timestamp=datetime.now(UTC),
        user_id=current_user.id,
        action="CREATE_AUDIT",
        table_name="audit_sessions",
        record_id=0,
        new_values=json.dumps({"audit_id": audit_id, "clauses_count": len(clauses_data)}),
    )
    db.add(audit_log_entry)
    db.commit()

    return AuditResponse(
        id=audit_session.id,
        document_name=audit_session.document_name,
        status=audit_session.status,
        language_hint=audit_session.language_hint,
        clauses=[ClauseResponse(**c) for c in clauses_data],
        findings=[FindingResponse(**f) for f in all_findings],
    )


@router.post("/upload", response_model=AuditResponse)
async def upload_audit(
    file: UploadFile = File(...),
    language_hint: str = Form(default="en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditResponse:
    """Ingest a DOCX, PDF, or text tender document, segment clauses, and run audit."""
    content = await file.read()
    validate_upload_safety(content, file.filename or "uploaded_tender.txt")

    ingest_svc = IngestionService()
    parsed_doc = ingest_svc.ingest_bytes(content, filename=file.filename or "uploaded_tender")

    if parsed_doc.status != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=parsed_doc.error_message or "Failed to parse uploaded document",
        )

    audit_id = f"aud_{uuid.uuid4().hex[:10]}"
    clauses_data = []
    all_findings = []

    for seg in parsed_doc.clauses:
        extractions, findings = _run_clause_audit(
            clause_id=seg.id,
            clause_text=seg.text,
            language_hint=language_hint or seg.language,
            db=db,
        )
        clauses_data.append({
            "id": seg.id,
            "text": seg.text,
            "extractions": extractions,
            "page_number": seg.page_number,
            "start_char": seg.start_char,
            "end_char": seg.end_char,
            "source_type": seg.source_type,
        })
        all_findings.extend(findings)

    audit_session = AuditSession(
        id=audit_id,
        document_name=file.filename or "uploaded_tender",
        source_text=parsed_doc.full_text,
        language_hint=language_hint,
        status="COMPLETED",
        created_by=current_user.username,
        created_at=datetime.now(UTC),
        clauses_json=json.dumps(clauses_data),
        findings_json=json.dumps(all_findings),
    )
    db.add(audit_session)

    # Append to audit log
    audit_log_entry = AuditLog(
        timestamp=datetime.now(UTC),
        user_id=current_user.id,
        action="UPLOAD_AUDIT",
        table_name="audit_sessions",
        record_id=0,
        new_values=json.dumps({
            "audit_id": audit_id,
            "filename": file.filename,
            "source_type": parsed_doc.source_type,
            "clauses_count": len(clauses_data),
        }),
    )
    db.add(audit_log_entry)
    db.commit()

    return AuditResponse(
        id=audit_session.id,
        document_name=audit_session.document_name,
        status=audit_session.status,
        language_hint=audit_session.language_hint,
        clauses=[ClauseResponse(**c) for c in clauses_data],
        findings=[FindingResponse(**f) for f in all_findings],
    )


@router.get("", response_model=list[AuditSummaryResponse])
def list_audits(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditSummaryResponse]:
    """List recent audit sessions for history and diff comparison."""
    stmt = (
        select(AuditSession)
        .order_by(AuditSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = db.execute(stmt).scalars().all()
    results = []
    for s in sessions:
        clauses = json.loads(s.clauses_json)
        findings = json.loads(s.findings_json)
        results.append(
            AuditSummaryResponse(
                id=s.id,
                document_name=s.document_name,
                created_at=s.created_at.isoformat(),
                created_by=s.created_by,
                status=s.status,
                language_hint=s.language_hint,
                total_clauses=len(clauses),
                total_findings=len(findings),
            )
        )
    return results


@router.get("/{audit_id}", response_model=AuditResponse)
def get_audit(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditResponse:
    """Retrieve audit session status, clauses, and finding cards."""
    session = db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit session {audit_id} not found",
        )

    clauses_data = json.loads(session.clauses_json)
    findings_data = json.loads(session.findings_json)

    return AuditResponse(
        id=session.id,
        document_name=session.document_name,
        status=session.status,
        language_hint=session.language_hint,
        clauses=[ClauseResponse(**c) for c in clauses_data],
        findings=[FindingResponse(**f) for f in findings_data],
    )


@router.post("/{audit_id}/findings/{finding_id}/decision")
def record_finding_decision(
    audit_id: str,
    finding_id: str,
    decision_in: FindingDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Record procurement officer review decision (Accept or Dismiss with reason)."""
    session = db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit session {audit_id} not found",
        )

    findings = json.loads(session.findings_json)
    target_finding = None
    for f in findings:
        if f["id"] == finding_id:
            f["decision"] = decision_in.decision
            f["decision_reason"] = decision_in.reason
            f["decided_by"] = current_user.username
            f["decided_on"] = datetime.now(UTC).isoformat()
            target_finding = f
            break

    if not target_finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding {finding_id} not found in audit {audit_id}",
        )

    session.findings_json = json.dumps(findings)

    # Log officer decision in append-only audit log
    audit_log = AuditLog(
        timestamp=datetime.now(UTC),
        user_id=current_user.id,
        action="FINDING_DECISION",
        table_name="findings",
        record_id=0,
        new_values=json.dumps(
            {
                "audit_id": audit_id,
                "finding_id": finding_id,
                "decision": decision_in.decision,
                "reason": decision_in.reason,
                "officer": current_user.username,
            }
        ),
    )
    db.add(audit_log)
    db.commit()

    return target_finding


@router.post("/{audit_id}/extractions/{clause_id}", response_model=AuditResponse)
def edit_clause_extraction(
    audit_id: str,
    clause_id: str,
    edit_in: ExtractionEditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditResponse:
    """Officer edits extracted entities; triggers deterministic re-evaluation of rules."""
    session = db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit session {audit_id} not found",
        )

    clauses = json.loads(session.clauses_json)
    target_clause = None
    for c in clauses:
        if c["id"] == clause_id:
            target_clause = c
            break

    if not target_clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found in audit {audit_id}",
        )

    # Apply overrides
    curr_extractions = target_clause.get("extractions", {})
    if edit_in.citations is not None:
        curr_extractions["citations"] = edit_in.citations
    if edit_in.mentions_certification is not None:
        curr_extractions["mentions_certification"] = edit_in.mentions_certification
    if edit_in.mapped_product is not None:
        curr_extractions["products"] = [edit_in.mapped_product]

    # Re-evaluate rules for this clause
    new_extractions, new_findings = _run_clause_audit(
        clause_id=clause_id,
        clause_text=target_clause["text"],
        language_hint=session.language_hint,
        db=db,
        override_extractions=curr_extractions,
    )
    target_clause["extractions"] = new_extractions

    # Replace findings for this clause
    existing_findings = json.loads(session.findings_json)
    preserved_findings = [f for f in existing_findings if f["clause_id"] != clause_id]
    updated_findings = preserved_findings + new_findings

    session.clauses_json = json.dumps(clauses)
    session.findings_json = json.dumps(updated_findings)
    db.commit()

    return AuditResponse(
        id=session.id,
        document_name=session.document_name,
        status=session.status,
        language_hint=session.language_hint,
        clauses=[ClauseResponse(**c) for c in clauses],
        findings=[FindingResponse(**f) for f in updated_findings],
    )


@router.get("/{audit_id}/report")
def export_audit_report(
    audit_id: str,
    format: str = Query(default="json", pattern="^(json|csv|pdf|docx)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export evidence-linked audit report in JSON, CSV, PDF, or DOCX format."""
    session = db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit session {audit_id} not found",
        )

    clauses = json.loads(session.clauses_json)
    findings = json.loads(session.findings_json)
    audit_meta = {
        "id": session.id,
        "document_name": session.document_name,
        "created_at": session.created_at.isoformat(),
        "created_by": session.created_by,
        "status": session.status,
        "language_hint": session.language_hint,
    }

    short_id = session.id[:8]
    if format == "json":
        json_data = export_json_report(audit_meta, clauses, findings)
        return Response(
            content=json.dumps(json_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="tender_audit_{short_id}.json"'},
        )

    if format == "csv":
        csv_content = export_csv_report(audit_meta, clauses, findings)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="tender_audit_{short_id}.csv"'},
        )

    if format == "pdf":
        pdf_bytes = generate_pdf_report(audit_meta, clauses, findings)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="tender_audit_{short_id}.pdf"'},
        )

    if format == "docx":
        docx_bytes = generate_docx_report(audit_meta, clauses, findings)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="tender_audit_{short_id}.docx"'},
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported export format: {format}",
    )


@router.get("/{draft_a_id}/diff/{draft_b_id}", response_model=AuditDiffResponse)
def diff_audit_drafts(
    draft_a_id: str,
    draft_b_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditDiffResponse:
    """Compare findings and clauses between two tender draft audits."""
    session_a = db.execute(
        select(AuditSession).where(AuditSession.id == draft_a_id)
    ).scalar_one_or_none()
    session_b = db.execute(
        select(AuditSession).where(AuditSession.id == draft_b_id)
    ).scalar_one_or_none()

    if not session_a or not session_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both audit draft sessions were not found",
        )

    clauses_a = json.loads(session_a.clauses_json)
    clauses_b = json.loads(session_b.clauses_json)
    findings_a = json.loads(session_a.findings_json)
    findings_b = json.loads(session_b.findings_json)

    diff_result = analyze_audit_diff(
        draft_a_id=draft_a_id,
        draft_b_id=draft_b_id,
        clauses_a=clauses_a,
        clauses_b=clauses_b,
        findings_a=findings_a,
        findings_b=findings_b,
    )

    return AuditDiffResponse(
        draft_a_id=diff_result.draft_a_id,
        draft_b_id=diff_result.draft_b_id,
        added_findings=diff_result.added_findings,
        resolved_findings=diff_result.resolved_findings,
        retained_findings=diff_result.retained_findings,
        clause_diff=diff_result.clause_diff.model_dump(),
        summary=diff_result.summary,
    )


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_audit(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Perform one-click complete deletion of a confidential audit draft."""
    deleted = delete_audit_session(db, audit_id, current_user)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit session {audit_id} not found",
        )


@router.post("/purge")
def purge_audits(
    max_age_days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Purge confidential audit sessions older than the specified retention threshold."""
    purged_count = purge_expired_audit_sessions(db, max_age_days=max_age_days)
    return {
        "status": "SUCCESS",
        "purged_count": purged_count,
        "max_age_days": max_age_days,
        "purged_by": current_user.username,
    }

