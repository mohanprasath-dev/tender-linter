from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MappingMatchMethod(StrEnum):
    EXACT = "EXACT"
    SYNONYM = "SYNONYM"
    FUZZY = "FUZZY"
    EMBEDDING = "EMBEDDING"
    OFFICER_OVERRIDE = "OFFICER_OVERRIDE"
    UNMAPPED = "UNMAPPED"


class CandidateProductMatch(BaseModel):
    product_id: int
    canonical_name: str
    score: float
    method: MappingMatchMethod


class ProductMappingResult(BaseModel):
    raw_text: str
    canonical_product_id: str | None = None
    canonical_name: str | None = None
    confidence: float = 0.0
    method: MappingMatchMethod = MappingMatchMethod.UNMAPPED
    is_unmapped: bool = True
    candidates: list[CandidateProductMatch] = Field(default_factory=list)
    officer_confirmed: bool = False
    officer_id: str | None = None
    officer_notes: str | None = None


class NormalizedCitation(BaseModel):
    raw: str
    is_number: str
    part: str | None = None
    section: str | None = None
    year: int | None = None
    span: tuple[int, int] | None = None
