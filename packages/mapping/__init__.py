from __future__ import annotations

from packages.mapping.is_normaliser import normalize_citation, suggest_near_matches
from packages.mapping.product_mapper import ProductMapper
from packages.mapping.schema import (
    CandidateProductMatch,
    MappingMatchMethod,
    NormalizedCitation,
    ProductMappingResult,
)

__all__ = [
    "CandidateProductMatch",
    "MappingMatchMethod",
    "NormalizedCitation",
    "ProductMapper",
    "ProductMappingResult",
    "normalize_citation",
    "suggest_near_matches",
]
