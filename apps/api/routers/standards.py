from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.schemas.standards import StandardRead
from packages.data.db import get_db
from packages.data.models import Standard

router = APIRouter(prefix="/standards", tags=["standards"])


@router.get("", response_model=list[StandardRead])
def list_standards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[StandardRead]:
    """Retrieve public metadata of Indian Standards from the catalogue."""
    stmt = select(Standard).offset(skip).limit(limit)
    standards = db.execute(stmt).scalars().all()
    return [StandardRead.model_validate(s) for s in standards]


@router.get("/{standard_id}", response_model=StandardRead)
def get_standard(
    standard_id: int,
    db: Session = Depends(get_db),
) -> StandardRead:
    """Retrieve a single Indian Standard record by identifier."""
    standard = db.execute(select(Standard).where(Standard.id == standard_id)).scalar_one_or_none()
    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard with id {standard_id} not found",
        )
    return StandardRead.model_validate(standard)
