from __future__ import annotations

from typing import Protocol

from packages.extraction.schema import ExtractionData


class Extractor(Protocol):
    name: str
    model_id: str

    def extract(self, clause: str, language_hint: str | None = None) -> ExtractionData:
        ...
