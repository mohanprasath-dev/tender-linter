"""PDF parser extracting text with layout order, page numbers, and character offsets."""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader

from packages.ingestion.schema import ClauseSegment, ParsedDocument
from packages.ingestion.segmenter import ClauseSegmenter


class PdfParser:
    """Extracts text from PDF files with page-level tracking and clause segmentation."""

    def __init__(self) -> None:
        self.segmenter = ClauseSegmenter()

    def parse_file(self, file_path: Path) -> ParsedDocument:
        with open(file_path, "rb") as f:
            return self.parse_bytes(f.read(), filename=file_path.name)

    def parse_bytes(self, content: bytes, filename: str = "document.pdf") -> ParsedDocument:
        reader = PdfReader(io.BytesIO(content))
        total_pages = len(reader.pages)

        all_clauses: list[ClauseSegment] = []
        page_texts: list[str] = []
        curr_doc_offset = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue

            page_texts.append(text)
            page_segments = self.segmenter.segment(
                text,
                base_id=f"pdf_p{page_idx}",
                page_number=page_idx,
                source_type="pdf_page",
            )

            # Adjust offsets relative to total document text
            for seg in page_segments:
                seg.start_char += curr_doc_offset
                seg.end_char += curr_doc_offset
                all_clauses.append(seg)

            curr_doc_offset += len(text) + 2

        full_doc_text = "\n\n".join(page_texts)

        return ParsedDocument(
            filename=filename,
            source_type="pdf",
            full_text=full_doc_text,
            clauses=all_clauses,
            page_count=max(1, total_pages),
            is_ocr=False,
            status="SUCCESS",
        )
