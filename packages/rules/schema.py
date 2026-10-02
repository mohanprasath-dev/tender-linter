from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    CANNOT_VERIFY = "CANNOT_VERIFY"


class FindingEvidence(BaseModel):
    url: str | None = None
    verified_on: str | None = None
    row_id: int | None = None
    instrument: str | None = None
    candidate: str | None = None
    term: str | None = None
    explanation: str | None = None
    other_product: str | None = None
    locations: list[str] | None = None
    details: dict[str, Any] | None = None


class Finding(BaseModel):
    id: str
    rule_id: str
    severity: Severity
    clause_id: str
    span: tuple[int, int] | None = None
    message_en: str
    message_hi: str | None = None
    evidence: FindingEvidence | None = None
    rule_set_version: str


class CitationExtraction(BaseModel):
    raw: str
    span: tuple[int, int]
    is_number: str
    part: str | None = None
    section: str | None = None
    year: int | None = None


class ProductExtraction(BaseModel):
    text: str
    span: tuple[int, int]
    canonical_product_id: str | None = None


class VaguePhraseExtraction(BaseModel):
    text: str
    span: tuple[int, int]
    phrase: str | None = None
    explanation: str | None = None


class ClauseExtraction(BaseModel):
    clause_id: str
    text: str
    language: str = "en"
    products: list[ProductExtraction] = Field(default_factory=list)
    citations: list[CitationExtraction] = Field(default_factory=list)
    vague_phrases: list[VaguePhraseExtraction] = Field(default_factory=list)
    mentions_certification: bool = False


class RuleDefinition(BaseModel):
    id: str
    name: str
    severity: Severity
    fires_when: str
    evidence: str
    message_en: str
    message_hi: str | None = None


class RuleCatalog(BaseModel):
    rule_set_version: str
    rules: list[RuleDefinition]
