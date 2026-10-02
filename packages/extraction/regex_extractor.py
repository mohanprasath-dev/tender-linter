from __future__ import annotations

import re
import unicodedata

from packages.extraction.schema import (
    CitationItem,
    ExtractionData,
    VaguePhraseItem,
)

_DEV = {ord(c): str(i) for i, c in enumerate("०१२३४५६७८९")}
_PREFIX = r"(?:I\.?\s?S\.?|आई\.?\s?एस\.?)"
_CITE = re.compile(
    r"(?<![A-Za-z])(?P<prefix>" + _PREFIX + r")(?:\s*/\s*(?P<body>IEC|ISO))?"
    r"\s*[:.]?\s*(?P<num>\d{2,6}(?:\s*-\s*\d{1,4})*)"
    r"(?:\s*\(?\s*(?:(?i:Part)|भाग)\s*(?P<part>\d+)\s*\)?)?"
    r"(?:\s*[:/\-]\s*(?P<year>(?:19|20)\d{2})(?!\d))?"
)
_YEAR = re.compile(r"(?:19|20)\d{2}$")

VAGUE_PATTERNS = [
    r"ISI\s+quality",
    r"as\s+per\s+BIS",
    r"आईएसआई\s+गुणवत्ता",
    r"बीआईएस\s+के\s+अनुसार",
]


def fold_digits(text: str) -> str:
    """Normalize Devanagari digits and full-width characters without changing length."""
    out = []
    for ch in text:
        n = unicodedata.normalize("NFKC", ch)
        out.append(n if len(n) == 1 else ch)
    return "".join(out).translate(_DEV)


def detect_language(text: str) -> str:
    has_devanagari = any("\u0900" <= ch <= "\u097f" for ch in text)
    has_latin = any("a" <= ch.lower() <= "z" for ch in text)
    if has_devanagari and has_latin:
        return "mixed"
    if has_devanagari:
        return "hi"
    return "en"


class RegexExtractor:
    """Deterministic fallback and cross-check citation extraction library."""

    def extract(self, clause: str, clause_id: str = "c_regex") -> ExtractionData:
        folded = fold_digits(clause)
        citations: list[CitationItem] = []

        for m in _CITE.finditer(folded):
            groups = re.split(r"\s*-\s*", m.group("num").strip())
            year = int(m.group("year")) if m.group("year") else None
            if year is None and len(groups) > 1 and _YEAR.match(groups[-1]):
                year = int(groups.pop())
            body = m.group("body")
            prefix = "IS/" + body.upper() if body else "IS"
            is_number = f"{prefix} {'-'.join(groups)}"
            part = m.group("part")

            citations.append(
                CitationItem(
                    raw=clause[m.start():m.end()],
                    span=(m.start(), m.end()),
                    is_number=is_number,
                    part=part,
                    year=year,
                )
            )

        vague_phrases: list[VaguePhraseItem] = []
        for pat in VAGUE_PATTERNS:
            for vm in re.finditer(pat, clause, re.IGNORECASE):
                vague_phrases.append(
                    VaguePhraseItem(
                        text=clause[vm.start():vm.end()],
                        span=(vm.start(), vm.end()),
                    )
                )

        lang = detect_language(clause)

        return ExtractionData(
            clause_id=clause_id,
            language=lang,
            products=[],
            citations=citations,
            vague_phrases=vague_phrases,
            requirements=[],
        )
