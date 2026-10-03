from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class StandardRowCreate(BaseModel):
    is_number: str
    part: str | None = None
    section: str | None = None
    title: str
    publication_year: int | None = None
    status: str = "Active"
    catalogue_url: str
    evidence_ref: str


class StandardRowUpdate(BaseModel):
    title: str | None = None
    publication_year: int | None = None
    status: str | None = None
    catalogue_url: str | None = None
    evidence_ref: str | None = None


class StandardRowResponse(BaseModel):
    id: int
    is_number: str
    part: str | None = None
    title: str
    publication_year: int | None = None
    status: str
    catalogue_url: str
    verified_on: datetime.date
    verified_by: str
    second_checked_by: str | None = None
    evidence_ref: str

    model_config = ConfigDict(from_attributes=True)


class StandardRowReverify(BaseModel):
    evidence_ref: str


class BulkImportReport(BaseModel):
    total_rows: int
    imported_count: int
    rejected_count: int
    errors: list[dict[str, Any]]


class VagueTermCreate(BaseModel):
    phrase: str
    language: str = "en"
    explanation: str


class VagueTermResponse(BaseModel):
    id: int
    phrase: str
    language: str
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    timestamp: str
    user_id: int | None = None
    action: str
    table_name: str
    record_id: int
    old_values: str | None = None
    new_values: str | None = None


class RuleItemResponse(BaseModel):
    id: str
    name: str
    severity: str
    fires_when: str
    evidence: str
    message_en: str
    message_hi: str | None = None


