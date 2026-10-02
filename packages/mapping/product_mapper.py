from __future__ import annotations

import re
import unicodedata

from packages.mapping.schema import (
    CandidateProductMatch,
    MappingMatchMethod,
    ProductMappingResult,
)
from packages.rules.context import ProductRecord


def _normalize_text(text: str) -> str:
    cleaned = unicodedata.normalize("NFKC", text).lower().strip()
    # Strip leading quantities like "50 ", "10 ", "20 "
    cleaned = re.sub(r"^\d+\s+", "", cleaned)
    # Strip common boilerplate words
    cleaned = re.sub(r"\b(?:rated for|square metres|sqm|sq m|conforming to|units|pieces|nos)\b.*$", "", cleaned)
    return cleaned.strip()


def _token_jaccard(a: str, b: str) -> float:
    set_a = set(re.findall(r"\w+", a.lower()))
    set_b = set(re.findall(r"\w+", b.lower()))
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union


def _char_trigram_similarity(a: str, b: str) -> float:
    def get_trigrams(s: str) -> set[str]:
        s = f"  {s}  "
        return {s[i : i + 3] for i in range(len(s) - 2)}

    tri_a = get_trigrams(a.lower())
    tri_b = get_trigrams(b.lower())
    if not tri_a or not tri_b:
        return 0.0
    return 2.0 * len(tri_a & tri_b) / (len(tri_a) + len(tri_b))


class ProductMapper:
    """Multi-step product mapper matching Spec Section 5.4."""

    def __init__(self, products: list[ProductRecord], threshold: float = 0.75) -> None:
        self.products = products
        self.threshold = threshold

    def map_product(self, raw_text: str) -> ProductMappingResult:
        norm_query = _normalize_text(raw_text)
        candidates: list[CandidateProductMatch] = []

        for prod in self.products:
            # 1. Exact match on canonical name
            if norm_query == prod.canonical_name.lower():
                candidates.append(
                    CandidateProductMatch(
                        product_id=prod.id,
                        canonical_name=prod.canonical_name,
                        score=1.0,
                        method=MappingMatchMethod.EXACT,
                    )
                )
                continue

            # 2. Match on synonyms (EN and HI)
            exact_syn_match = False
            for syn in prod.synonyms_en + prod.synonyms_hi:
                syn_norm = _normalize_text(syn)
                if norm_query == syn_norm:
                    candidates.append(
                        CandidateProductMatch(
                            product_id=prod.id,
                            canonical_name=prod.canonical_name,
                            score=0.98,
                            method=MappingMatchMethod.SYNONYM,
                        )
                    )
                    exact_syn_match = True
                    break
                # Word boundary match on synonym
                if syn_norm and len(syn_norm) >= 3:
                    pattern = r"(?:^|\W)" + re.escape(syn_norm) + r"(?:$|\W)"
                    if re.search(pattern, norm_query):
                        candidates.append(
                            CandidateProductMatch(
                                product_id=prod.id,
                                canonical_name=prod.canonical_name,
                                score=0.92,
                                method=MappingMatchMethod.SYNONYM,
                            )
                        )
                        exact_syn_match = True
                        break
                elif syn_norm and norm_query in syn_norm:
                    if _token_jaccard(norm_query, syn_norm) >= 0.5:
                        candidates.append(
                            CandidateProductMatch(
                                product_id=prod.id,
                                canonical_name=prod.canonical_name,
                                score=0.88,
                                method=MappingMatchMethod.SYNONYM,
                            )
                        )
                        exact_syn_match = True
                        break

            if exact_syn_match:
                continue

            # 3. Fuzzy & character n-gram similarity
            sims = [_char_trigram_similarity(norm_query, prod.canonical_name)]
            for syn in prod.synonyms_en + prod.synonyms_hi:
                sims.append(_char_trigram_similarity(norm_query, syn))
                sims.append(_token_jaccard(norm_query, syn))

            best_sim = max(sims) if sims else 0.0

            # Step 4: Semantic candidate restricted to products table
            if best_sim >= 0.40:
                candidates.append(
                    CandidateProductMatch(
                        product_id=prod.id,
                        canonical_name=prod.canonical_name,
                        score=round(best_sim, 3),
                        method=MappingMatchMethod.FUZZY,
                    )
                )

        candidates.sort(key=lambda x: x.score, reverse=True)

        if candidates and candidates[0].score >= self.threshold:
            top = candidates[0]
            return ProductMappingResult(
                raw_text=raw_text,
                canonical_product_id=top.canonical_name,
                canonical_name=top.canonical_name,
                confidence=top.score,
                method=top.method,
                is_unmapped=False,
                candidates=candidates,
                officer_confirmed=False,
            )

        # Candidate below threshold: UNMAPPED
        return ProductMappingResult(
            raw_text=raw_text,
            canonical_product_id=None,
            canonical_name=None,
            confidence=candidates[0].score if candidates else 0.0,
            method=MappingMatchMethod.UNMAPPED,
            is_unmapped=True,
            candidates=candidates,
            officer_confirmed=False,
        )

    def confirm_mapping(
        self,
        result: ProductMappingResult,
        officer_id: str,
        notes: str | None = None,
    ) -> ProductMappingResult:
        """Officer confirms the proposed candidate mapping."""
        confirmed = result.model_copy(deep=True)
        confirmed.officer_confirmed = True
        confirmed.officer_id = officer_id
        confirmed.officer_notes = notes
        return confirmed

    def override_mapping(
        self,
        raw_text: str,
        override_product_name: str,
        officer_id: str,
        notes: str | None = None,
    ) -> ProductMappingResult:
        """Officer overrides mapping to a different product or maps an unmapped item."""
        matched_prod = None
        for p in self.products:
            if p.canonical_name.lower() == override_product_name.lower():
                matched_prod = p
                break

        canonical_name = matched_prod.canonical_name if matched_prod else override_product_name

        return ProductMappingResult(
            raw_text=raw_text,
            canonical_product_id=canonical_name,
            canonical_name=canonical_name,
            confidence=1.0,
            method=MappingMatchMethod.OFFICER_OVERRIDE,
            is_unmapped=False,
            candidates=[],
            officer_confirmed=True,
            officer_id=officer_id,
            officer_notes=notes,
        )
