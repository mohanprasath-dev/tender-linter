from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    id: int
    canonical_name: str
    family: str
    synonyms_en: str
    synonyms_hi: str
    synonyms_other: str

    model_config = ConfigDict(from_attributes=True)


class CertificationRuleRead(BaseModel):
    id: int
    product_id: int
    scheme: str
    specified_standard_id: int
    instrument: str
    effective_from: datetime.date | None = None
    transition_until: datetime.date | None = None
    source_url: str
    verified_on: datetime.date
    verified_by: str
    second_checked_by: str | None = None
    evidence_ref: str

    model_config = ConfigDict(from_attributes=True)


class ProductRulesResponse(BaseModel):
    product: ProductRead
    certification_rules: list[CertificationRuleRead]
