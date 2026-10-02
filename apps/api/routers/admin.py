from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.api.core.auth import require_role
from apps.api.schemas.admin import (
    StandardRowCreate,
    StandardRowResponse,
    StandardRowUpdate,
)
from packages.data.db import get_db
from packages.data.models import Standard, User

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
