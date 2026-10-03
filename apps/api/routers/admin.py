from __future__ import annotations

import csv
import datetime
import io
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.api.core.auth import require_role
from apps.api.schemas.admin import (
    AuditLogResponse,
    BulkImportReport,
    RuleItemResponse,
    StandardRowCreate,
    StandardRowResponse,
    StandardRowReverify,
    StandardRowUpdate,
    VagueTermCreate,
    VagueTermResponse,
)
from packages.data.db import get_db
from packages.data.models import AuditLog, Standard, User, VagueTerm
from packages.rules.loader import load_rules_from_yaml

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/rows", response_model=StandardRowResponse)
def create_standard_row(
    row_in: StandardRowCreate,
    current_user: User = Depends(require_role(["Admin", "Curator"])),
    db: Session = Depends(get_db),
) -> StandardRowResponse:
    """Create a new standard catalogue entry with curator provenance."""
    new_standard = Standard(
        is_number=row_in.is_number,
        part=row_in.part,
        section=row_in.section,
        title=row_in.title,
        publication_year=row_in.publication_year,
        status=row_in.status,
        catalogue_url=row_in.catalogue_url,
        verified_on=datetime.date.today(),
        verified_by=current_user.username,
        second_checked_by=None,
        evidence_ref=row_in.evidence_ref,
    )
    db.add(new_standard)
    db.commit()
    db.refresh(new_standard)
    return StandardRowResponse.model_validate(new_standard)


@router.patch("/rows/{row_id}", response_model=StandardRowResponse)
def update_standard_row(
    row_id: int,
    row_in: StandardRowUpdate,
    current_user: User = Depends(require_role(["Admin", "Curator"])),
    db: Session = Depends(get_db),
) -> StandardRowResponse:
    """Update metadata of an existing standard row."""
    standard = db.execute(select(Standard).where(Standard.id == row_id)).scalar_one_or_none()
    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard row with id {row_id} not found",
        )

    update_data = row_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(standard, field, value)

    db.commit()
    db.refresh(standard)
    return StandardRowResponse.model_validate(standard)


@router.post("/rows/{row_id}/verify", response_model=StandardRowResponse)
def verify_standard_row(
    row_id: int,
    current_user: User = Depends(require_role(["Admin", "Verifier", "Curator"])),
    db: Session = Depends(get_db),
) -> StandardRowResponse:
    """Sign off as the independent second verifier for a standard entry."""
    standard = db.execute(select(Standard).where(Standard.id == row_id)).scalar_one_or_none()
    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard row with id {row_id} not found",
        )

    # Enforce two-person check constraint
    if standard.verified_by.strip().lower() == current_user.username.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifier cannot be the same person as the curator (two-person check rule)",
        )

    standard.second_checked_by = current_user.username
    db.commit()
    db.refresh(standard)
    return StandardRowResponse.model_validate(standard)


@router.post("/rows/{row_id}/re-verify", response_model=StandardRowResponse)
def reverify_standard_row(
    row_id: int,
    reverify_in: StandardRowReverify,
    current_user: User = Depends(require_role(["Admin", "Curator", "Verifier"])),
    db: Session = Depends(get_db),
) -> StandardRowResponse:
    """Re-verify a standard row, updating its verified date and evidence ref."""
    standard = db.execute(select(Standard).where(Standard.id == row_id)).scalar_one_or_none()
    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard row with id {row_id} not found",
        )

    standard.verified_on = datetime.date.today()
    standard.evidence_ref = reverify_in.evidence_ref
    db.commit()
    db.refresh(standard)
    return StandardRowResponse.model_validate(standard)


@router.get("/queue/unverified", response_model=list[StandardRowResponse])
def get_unverified_queue(
    current_user: User = Depends(require_role(["Admin", "Curator", "Verifier"])),
    db: Session = Depends(get_db),
) -> list[StandardRowResponse]:
    """Retrieve standard rows awaiting second-person verification sign-off."""
    stmt = (
        select(Standard)
        .where(Standard.second_checked_by.is_(None))
        .order_by(Standard.id.desc())
    )
    unverified = db.execute(stmt).scalars().all()
    return [StandardRowResponse.model_validate(s) for s in unverified]


@router.get("/stale", response_model=list[StandardRowResponse])
def get_stale_rows(
    stale_days: int = Query(default=180, ge=1),
    current_user: User = Depends(require_role(["Admin", "Curator", "Verifier"])),
    db: Session = Depends(get_db),
) -> list[StandardRowResponse]:
    """Retrieve standard rows that are due for re-verification."""
    cutoff_date = datetime.date.today() - datetime.timedelta(days=stale_days)
    stmt = select(Standard).where(
        or_(
            Standard.verified_on < cutoff_date,
            Standard.verified_on.is_(None),
        )
    )
    stale_standards = db.execute(stmt).scalars().all()
    return [StandardRowResponse.model_validate(s) for s in stale_standards]


@router.post("/import-csv", response_model=BulkImportReport)
async def bulk_import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["Admin", "Curator"])),
    db: Session = Depends(get_db),
) -> BulkImportReport:
    """Bulk import curated standard rows with strict provenance validation."""
    content = await file.read()
    decoded = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(decoded))

    total = 0
    imported = 0
    errors: list[dict[str, Any]] = []

    for idx, row in enumerate(reader, start=2):
        total += 1
        is_num = (row.get("is_number") or "").strip()
        title = (row.get("title") or "").strip()
        pub_year_raw = (row.get("publication_year") or "").strip()
        pub_year = int(pub_year_raw) if pub_year_raw.isdigit() else None
        cat_url = (row.get("catalogue_url") or "").strip()
        ev_ref = (row.get("evidence_ref") or "").strip()
        status_val = (row.get("status") or "Active").strip()

        # Validation rules
        if not is_num:
            errors.append({"line": idx, "reason": "Missing is_number"})
            continue
        if not title:
            errors.append({"line": idx, "reason": "Missing title"})
            continue
        if not cat_url.startswith("https://"):
            errors.append({"line": idx, "reason": "Missing or invalid catalogue_url (must start with https://)"})
            continue
        if not ev_ref or "UNVERIFIED" in ev_ref.upper():
            errors.append({"line": idx, "reason": "Rejected unverified or missing evidence_ref"})
            continue

        std = Standard(
            is_number=is_num,
            title=title,
            publication_year=pub_year,
            status=status_val,
            catalogue_url=cat_url,
            verified_on=datetime.date.today(),
            verified_by=current_user.username,
            second_checked_by=None,
            evidence_ref=ev_ref,
        )
        db.add(std)
        imported += 1

    if imported > 0:
        db.commit()

    return BulkImportReport(
        total_rows=total,
        imported_count=imported,
        rejected_count=len(errors),
        errors=errors,
    )


@router.get("/vague-terms", response_model=list[VagueTermResponse])
def list_vague_terms(
    current_user: User = Depends(require_role(["Admin", "Curator", "Verifier"])),
    db: Session = Depends(get_db),
) -> list[VagueTermResponse]:
    """List curated vague phrases that imply standards without citing an exact number."""
    terms = db.execute(select(VagueTerm).order_by(VagueTerm.phrase)).scalars().all()
    return [VagueTermResponse.model_validate(t) for t in terms]


@router.post("/vague-terms", response_model=VagueTermResponse)
def create_vague_term(
    term_in: VagueTermCreate,
    current_user: User = Depends(require_role(["Admin", "Curator"])),
    db: Session = Depends(get_db),
) -> VagueTermResponse:
    """Create a new curated vague phrase for defect rule R09."""
    existing = db.execute(select(VagueTerm).where(VagueTerm.phrase == term_in.phrase)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vague term '{term_in.phrase}' already exists",
        )

    term = VagueTerm(
        phrase=term_in.phrase,
        language=term_in.language,
        explanation=term_in.explanation,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return VagueTermResponse.model_validate(term)


@router.delete("/vague-terms/{term_id}")
def delete_vague_term(
    term_id: int,
    current_user: User = Depends(require_role(["Admin", "Curator"])),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a vague phrase from the catalog."""
    term = db.execute(select(VagueTerm).where(VagueTerm.id == term_id)).scalar_one_or_none()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vague term {term_id} not found",
        )
    db.delete(term)
    db.commit()
    return {"status": "deleted"}


@router.get("/rules", response_model=list[RuleItemResponse])
def list_rules_catalogue(
    current_user: User = Depends(require_role(["Admin", "Curator", "Verifier"])),
) -> list[RuleItemResponse]:
    """List deterministic rules from rules.yaml."""
    catalog = load_rules_from_yaml()
    return [
        RuleItemResponse(
            id=r.id,
            name=r.name,
            severity=r.severity,
            fires_when=r.fires_when,
            evidence=r.evidence,
            message_en=r.message_en,
            message_hi=r.message_hi,
        )
        for r in catalog.rules
    ]


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_role(["Admin", "Curator", "Verifier"])),
    db: Session = Depends(get_db),
) -> list[AuditLogResponse]:
    """Retrieve append-only audit log records."""
    logs = db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)).scalars().all()
    return [
        AuditLogResponse(
            id=log.id,
            timestamp=log.timestamp.isoformat(),
            user_id=log.user_id,
            action=log.action,
            table_name=log.table_name,
            record_id=log.record_id,
            old_values=log.old_values,
            new_values=log.new_values,
        )
        for log in logs
    ]
