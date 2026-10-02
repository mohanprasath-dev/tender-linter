from __future__ import annotations

from packages.extraction.bakeoff import BakeoffRunner
from packages.extraction.cache import (
    ExtractionCache,
    InMemoryExtractionCache,
    compute_cache_key,
)
from packages.extraction.providers.base import Extractor
from packages.extraction.providers.gemini import GeminiExtractor
from packages.extraction.providers.groq import GroqExtractor
from packages.extraction.providers.mock import MockExtractor
from packages.extraction.rate_limiter import CircuitBreaker, TokenBucketRateLimiter
from packages.extraction.regex_extractor import RegexExtractor
from packages.extraction.schema import (
    CitationItem,
    ExtractionData,
    ExtractionMetadata,
    ExtractionResult,
    ProductItem,
    RequirementItem,
    VaguePhraseItem,
)
from packages.extraction.service import ExtractionService
from packages.extraction.span_validator import validate_extraction_spans

__all__ = [
    "BakeoffRunner",
    "CitationItem",
    "CircuitBreaker",
    "ExtractionCache",
    "ExtractionData",
    "ExtractionMetadata",
    "ExtractionResult",
    "ExtractionService",
    "Extractor",
    "GeminiExtractor",
    "GroqExtractor",
    "InMemoryExtractionCache",
    "MockExtractor",
    "ProductItem",
    "RegexExtractor",
    "RequirementItem",
    "TokenBucketRateLimiter",
    "VaguePhraseItem",
    "compute_cache_key",
    "validate_extraction_spans",
]
