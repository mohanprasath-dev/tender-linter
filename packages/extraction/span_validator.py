from __future__ import annotations

import re
import unicodedata
from typing import Any

_DEV = {ord(c): str(i) for i, c in enumerate("०१२३४५६७८९")}
FIELDS = (
    ("products", "text"),
    ("citations", "raw"),
    ("vague_phrases", "text"),
    ("requirements", "text"),
)


def _fold(s: str) -> str:
    return "".join(
        n if len(n := unicodedata.normalize("NFKC", c)) == 1 else c for c in s
    ).translate(_DEV)


def _span_ok(clause: str, item: dict[str, Any], key: str) -> bool:
    span, text = item.get("span"), item.get(key)
    if not (
        (isinstance(span, list) or isinstance(span, tuple))
        and len(span) == 2
        and isinstance(text, str)
    ):
        return False
    s, e = span
    return isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(clause) and clause[s:e] == text


def _citation_consistent(item: dict[str, Any]) -> bool:
    raw = _fold(item.get("raw") or "")
    year = item.get("year")
    if year is not None and str(year) not in raw:
        return False
    num = item.get("is_number")
    if num:
        return all(g in raw for g in re.findall(r"\d+", num))
    return True


def validate_extraction_spans(
    clause: str,
    extraction: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    """Validate extraction spans against clause text.
    Drops spans that are not exact substrings of clause.
    Returns (cleaned_dict, dropped_items, invented_citations_count).
    """
    out = dict(extraction)
    dropped: list[dict[str, Any]] = []
    invented = 0

    for field, key in FIELDS:
        kept = []
        for item in extraction.get(field, []):
            item_dict = item if isinstance(item, dict) else item.model_dump()
            ok = _span_ok(clause, item_dict, key)
            if ok and field == "citations" and not _citation_consistent(item_dict):
                ok = False
                invented += 1
            elif not ok and field == "citations" and (item_dict.get(key) or "") not in clause:
                invented += 1

            if ok:
                kept.append(item)
            else:
                dropped.append({"field": field, "item": item_dict})

        out[field] = kept

    return out, dropped, invented
