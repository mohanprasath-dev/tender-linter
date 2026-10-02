from __future__ import annotations

from packages.extraction.regex_extractor import RegexExtractor
from packages.mapping.schema import NormalizedCitation
from packages.rules.normaliser import suggest_near_standard


def normalize_citation(raw_text: str) -> NormalizedCitation | None:
    """Normalize a citation string into canonical IS citation fields."""
    extractor = RegexExtractor()
    data = extractor.extract(raw_text)
    if not data.citations:
        return None
    cit = data.citations[0]
    return NormalizedCitation(
        raw=cit.raw,
        is_number=cit.is_number,
        part=cit.part,
        section=cit.section,
        year=cit.year,
        span=cit.span,
    )


def suggest_near_matches(is_number: str, known_numbers: list[str]) -> list[str]:
    """Return candidates exactly one edit away from known standards."""
    return suggest_near_standard(is_number, known_numbers)
