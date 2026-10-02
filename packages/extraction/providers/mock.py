from __future__ import annotations

import time

from packages.extraction.regex_extractor import RegexExtractor
from packages.extraction.schema import (
    CitationItem,
    ExtractionData,
    ProductItem,
    RequirementItem,
    VaguePhraseItem,
)


class MockExtractor:
    """Deterministic mock extractor for unit tests, offline evaluation and bake-off."""

    def __init__(
        self,
        name: str = "MockExtractor",
        model_id: str = "mock-model-v1",
        should_fail: bool = False,
        canned_products: list[ProductItem] | None = None,
        canned_citations: list[CitationItem] | None = None,
        canned_vague_phrases: list[VaguePhraseItem] | None = None,
        canned_requirements: list[RequirementItem] | None = None,
        allow_hallucination: bool = False,
        simulated_latency_sec: float = 0.0,
    ) -> None:
        self.name = name
        self.model_id = model_id
        self.should_fail = should_fail
        self.canned_products = canned_products
        self.canned_citations = canned_citations
        self.canned_vague_phrases = canned_vague_phrases
        self.canned_requirements = canned_requirements
        self.simulated_latency_sec = simulated_latency_sec
        self.allow_hallucination = allow_hallucination
        self.regex = RegexExtractor()

    def extract(self, clause: str, language_hint: str | None = None) -> ExtractionData:
        if self.should_fail:
            raise RuntimeError(f"Provider {self.name} failed to extract clause")

        if self.simulated_latency_sec > 0:
            time.sleep(self.simulated_latency_sec)

        # If canned citations or products specified, use them; otherwise use regex extraction
        if self.canned_citations is not None or self.canned_products is not None:
            if self.allow_hallucination:
                products = self.canned_products or []
                citations = self.canned_citations or []
            else:
                products = [p for p in (self.canned_products or []) if p.text in clause]
                citations = [c for c in (self.canned_citations or []) if c.raw in clause]
            vague = self.canned_vague_phrases or []
            reqs = self.canned_requirements or []
            return ExtractionData(
                clause_id="c_mock",
                language=language_hint or "en",
                products=products,
                citations=citations,
                vague_phrases=vague,
                requirements=reqs,
            )

        # Fallback to regex
        reg_res = self.regex.extract(clause, clause_id="c_mock")
        if language_hint:
            reg_res.language = language_hint
        return reg_res
