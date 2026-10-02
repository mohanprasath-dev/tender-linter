from __future__ import annotations

import logging
import time

from packages.extraction.cache import (
    ExtractionCache,
    InMemoryExtractionCache,
    compute_cache_key,
)
from packages.extraction.providers.base import Extractor
from packages.extraction.rate_limiter import CircuitBreaker, TokenBucketRateLimiter
from packages.extraction.regex_extractor import RegexExtractor
from packages.extraction.schema import (
    ExtractionData,
    ExtractionMetadata,
    ExtractionResult,
)
from packages.extraction.span_validator import validate_extraction_spans

logger = logging.getLogger(__name__)


class ExtractionService:
    """Production extraction service with fallback chain, regex cross-check, cache, and span validation."""

    def __init__(
        self,
        primary: Extractor | None = None,
        secondary: Extractor | None = None,
        cache: ExtractionCache | None = None,
        rate_limiter: TokenBucketRateLimiter | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        prompt_version: str = "extract_v1",
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.regex = RegexExtractor()
        self.cache = cache or InMemoryExtractionCache()
        self.rate_limiter = rate_limiter or TokenBucketRateLimiter()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.prompt_version = prompt_version

    def _call_provider_with_retry(
        self,
        provider: Extractor,
        clause: str,
        language_hint: str | None,
        max_retries: int = 2,
    ) -> ExtractionData:
        last_err: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return provider.extract(clause, language_hint=language_hint)
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    time.sleep(0.5 * (2**attempt))
        raise last_err or RuntimeError("Provider call failed")

    def extract(
        self,
        clause_id: str,
        clause: str,
        language_hint: str | None = None,
    ) -> ExtractionResult:
        model_id = self.primary.model_id if self.primary else "regex-only"
        cache_key = compute_cache_key(clause, self.prompt_version, model_id)

        # 1. Check cache
        cached = self.cache.get(cache_key)
        if cached:
            cached_copy = cached.model_copy(deep=True)
            cached_copy.clause_id = clause_id
            cached_copy.meta.cached = True
            return cached_copy

        start_time = time.time()
        provider_name = ""
        used_model_id = ""
        data: ExtractionData | None = None
        reduced_mode = False

        # 2. Try primary provider
        if self.primary and self.circuit_breaker.can_execute() and self.rate_limiter.allow_request():
            try:
                data = self._call_provider_with_retry(self.primary, clause, language_hint)
                self.circuit_breaker.record_success()
                provider_name = self.primary.name
                used_model_id = self.primary.model_id
            except Exception as e:
                logger.warning("Primary extractor %s failed: %s", self.primary.name, e)
                self.circuit_breaker.record_failure()

        # 3. Fallback to secondary provider if primary failed
        if data is None and self.secondary and self.rate_limiter.allow_request():
            try:
                data = self._call_provider_with_retry(self.secondary, clause, language_hint)
                provider_name = self.secondary.name
                used_model_id = self.secondary.model_id
            except Exception as e:
                logger.warning("Secondary extractor %s failed: %s", self.secondary.name, e)

        # 4. Fallback to deterministic regex-only mode
        if data is None:
            data = self.regex.extract(clause, clause_id=clause_id)
            provider_name = "RegexFallback"
            used_model_id = "regex-v1"
            reduced_mode = True

        data.clause_id = clause_id

        # 5. Deterministic cross-check with regex output (Spec 5.3)
        regex_data = self.regex.extract(clause, clause_id=clause_id)
        model_is_numbers = {c.is_number.upper().strip() for c in data.citations}
        regex_is_numbers = {c.is_number.upper().strip() for c in regex_data.citations}
        extraction_uncertain = False
        if not reduced_mode:
            # Check for disagreement between model and regex citations
            if model_is_numbers != regex_is_numbers:
                extraction_uncertain = True

        # 6. Span validation (Spec 5.2 & span-validator skill)
        data_dict = data.model_dump()
        cleaned_dict, dropped, invented = validate_extraction_spans(clause, data_dict)
        cleaned_data = ExtractionData.model_validate(cleaned_dict)

        elapsed_ms = (time.time() - start_time) * 1000.0

        meta = ExtractionMetadata(
            provider=provider_name,
            model_id=used_model_id,
            prompt_version=self.prompt_version,
            cached=False,
            reduced_mode=reduced_mode,
            extraction_uncertain=extraction_uncertain,
            dropped_spans=dropped,
            invented_citations=invented,
            latency_ms=round(elapsed_ms, 2),
        )

        result = ExtractionResult(
            clause_id=clause_id,
            clause_text=clause,
            data=cleaned_data,
            meta=meta,
        )

        # 7. Store in cache
        self.cache.set(cache_key, result)

        return result
