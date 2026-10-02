from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProductItem(BaseModel):
    text: str
    span: tuple[int, int]
    canonical_product_id: str | None = None


class CitationItem(BaseModel):
    raw: str
    span: tuple[int, int]
    is_number: str
    part: str | None = None
    section: str | None = None
    year: int | None = None


class VaguePhraseItem(BaseModel):
    text: str
    span: tuple[int, int]


class RequirementItem(BaseModel):
    text: str
    span: tuple[int, int]


class ExtractionData(BaseModel):
    clause_id: str
    language: str = "en"
    products: list[ProductItem] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
    vague_phrases: list[VaguePhraseItem] = Field(default_factory=list)
    requirements: list[RequirementItem] = Field(default_factory=list)


class ExtractionMetadata(BaseModel):
    provider: str
    model_id: str
    prompt_version: str = "extract_v1"
    cached: bool = False
    reduced_mode: bool = False
    extraction_uncertain: bool = False
    dropped_spans: list[dict[str, Any]] = Field(default_factory=list)
    invented_citations: int = 0
    latency_ms: float = 0.0


class ExtractionResult(BaseModel):
    clause_id: str
    clause_text: str
    data: ExtractionData
    meta: ExtractionMetadata
