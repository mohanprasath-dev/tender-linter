from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AuditCreateRequest(BaseModel):
    text: str
    language_hint: str = "en"
    document_name: str | None = None


class ClauseResponse(BaseModel):
    id: str
    text: str
    extractions: dict[str, Any]
    page_number: int | None = None
    start_char: int | None = None
    end_char: int | None = None
    source_type: str | None = None


class FindingResponse(BaseModel):
    id: str
    rule_id: str
    severity: str
    clause_id: str
    span: list[int] | tuple[int, int] | None = None
    message_en: str
    message_hi: str | None = None
    evidence: dict[str, Any] | None = None
    decision: str | None = None
    decision_reason: str | None = None
    rule_set_version: str
    model_version: str | None = None
    prompt_version: str | None = None


class AuditResponse(BaseModel):
    id: str
    document_name: str | None = None
    status: str
    language_hint: str
    clauses: list[ClauseResponse]
    findings: list[FindingResponse]


class ExtractionEditRequest(BaseModel):
    citations: list[dict[str, Any]] | None = None
    mentions_certification: bool | None = None
    mapped_product: dict[str, Any] | None = None


class FindingDecisionRequest(BaseModel):
    decision: str
    reason: str | None = None


class AuditReportResponse(BaseModel):
    audit_id: str
    document_name: str | None = None
    created_at: str
    status: str
    banner: str
    total_clauses: int
    total_findings: int
    findings: list[dict[str, Any]]


class AuditSummaryResponse(BaseModel):
    id: str
    document_name: str | None = None
    created_at: str
    created_by: str
    status: str
    language_hint: str
    total_clauses: int
    total_findings: int


class AuditDiffResponse(BaseModel):
    draft_a_id: str
    draft_b_id: str
    added_findings: list[dict[str, Any]]
    resolved_findings: list[dict[str, Any]]
    retained_findings: list[dict[str, Any]]
    clause_diff: dict[str, Any]
    summary: dict[str, Any]

