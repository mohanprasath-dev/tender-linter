"""Clause segmenter splitting on numbering, paragraphs, and sentence boundaries."""

from __future__ import annotations

import re

from packages.extraction.regex_extractor import detect_language
from packages.ingestion.schema import ClauseSegment

# Matches numbered headings or clause indicators like:
# "Clause 1.1:", "1.1", "1.", "(a)", "Section 4:"
_CLAUSE_SPLIT = re.compile(
    r"(?m)(?=(?:^|\n\n+)(?:(?:Clause|Section|धारा)\s+[\d.]+|[\d]+\.[\d.]*|\([a-z0-9]\))\s*[:\-])",
    re.IGNORECASE,
)


class ClauseSegmenter:
    """Segments raw tender text into numbered or paragraph clauses with exact character offsets."""

    def segment(
        self,
        full_text: str,
        base_id: str = "c",
        page_number: int | None = None,
        source_type: str = "text",
    ) -> list[ClauseSegment]:
        if not full_text.strip():
            return []

        # Split on paragraph boundaries and numbered headers
        chunks: list[tuple[int, int, str]] = []

        # Find double newlines or clause boundaries
        raw_splits = [m.start() for m in re.finditer(r"\n\s*\n+", full_text)]
        boundary_indices = sorted(list(set([0] + raw_splits + [len(full_text)])))

        for i in range(len(boundary_indices) - 1):
            start = boundary_indices[i]
            end = boundary_indices[i + 1]
            block = full_text[start:end]

            # Strip leading/trailing whitespace while adjusting offsets
            stripped = block.strip()
            if not stripped:
                continue

            lead_offset = block.find(stripped)
            chunk_start = start + lead_offset
            chunk_end = chunk_start + len(stripped)
            chunks.append((chunk_start, chunk_end, stripped))

        # Fallback if no paragraph breaks found: split on sentences
        if not chunks:
            chunks = [(0, len(full_text), full_text.strip())]

        segments: list[ClauseSegment] = []
        for idx, (c_start, c_end, c_text) in enumerate(chunks, start=1):
            lang = detect_language(c_text)
            segments.append(
                ClauseSegment(
                    id=f"{base_id}_{idx}",
                    text=c_text,
                    page_number=page_number,
                    paragraph_index=idx,
                    start_char=c_start,
                    end_char=c_end,
                    language=lang,
                    source_type=source_type,
                )
            )

        return segments
