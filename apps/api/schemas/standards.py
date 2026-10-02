from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class StandardRead(BaseModel):
    id: int
    is_number: str
    part: str | None = None
    section: str | None = None
    title: str
    publication_year: int | None = None
    status: str
    catalogue_url: str
    verified_on: datetime.date
    verified_by: str
    second_checked_by: str | None = None
    evidence_ref: str

    model_config = ConfigDict(from_attributes=True)
