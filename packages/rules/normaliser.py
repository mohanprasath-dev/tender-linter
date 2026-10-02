from __future__ import annotations

import re

_DEV_MAP = str.maketrans("०१२३४५६७८९", "0123456789")


def normalise_devanagari_digits(text: str) -> str:
    """Convert Devanagari numerals ०-९ to ASCII digits 0-9."""
    return text.translate(_DEV_MAP)


def normalise_devanagari_citation(raw_citation: str) -> str:
    """Normalize Devanagari digits, transliterated prefix, and 'भाग' to standard citation form."""
    res = normalise_devanagari_digits(raw_citation)
    res = re.sub(r"(?i:आई\.?\s?एस\.?|आईएस)", "IS", res)
    res = re.sub(r"भाग\s*(\d+)", r"Part \1", res)
    return res.strip()


def base_is_number(is_str: str) -> str:
    """Extract the base IS number without (Part ...) or Part suffixes."""
    norm = normalise_devanagari_citation(is_str)
    cleaned = re.sub(r"\s*\(?\s*(?:(?i:Part)|भाग)\s*\d+\s*\)?", "", norm).strip()
    return cleaned


def _edit1(a: str, b: str) -> bool:
    """True if a and b have Levenshtein distance == 1."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def suggest_near_standard(cited: str, known_standards: list[str]) -> list[str]:
    """Find known standards where either the full string or base number is 1 edit away."""
    cited_base = base_is_number(cited)
    candidates = []

    for known in known_standards:
        known_base = base_is_number(known)
        if _edit1(cited, known) or _edit1(cited_base, known_base) or _edit1(cited, known_base):
            if known not in candidates:
                candidates.append(known)

    return candidates
