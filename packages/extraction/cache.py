from __future__ import annotations

import hashlib
from typing import Protocol

from packages.extraction.schema import ExtractionResult


def compute_cache_key(clause: str, prompt_version: str, model_id: str) -> str:
    raw = f"{clause.strip()}||{prompt_version}||{model_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ExtractionCache(Protocol):
    def get(self, key: str) -> ExtractionResult | None:
        ...

    def set(self, key: str, result: ExtractionResult) -> None:
        ...


class InMemoryExtractionCache:
    def __init__(self) -> None:
        self._store: dict[str, ExtractionResult] = {}

    def get(self, key: str) -> ExtractionResult | None:
        return self._store.get(key)

    def set(self, key: str, result: ExtractionResult) -> None:
        self._store[key] = result
