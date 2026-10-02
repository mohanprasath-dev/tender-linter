"""OCR parser reporting confidence scores and supporting reviewer text corrections."""

from __future__ import annotations

from packages.ingestion.schema import ParsedDocument
from packages.ingestion.segmenter import ClauseSegmenter


class OcrParser:
    """Parses scanned documents and images, reporting confidence and enabling interactive corrections."""

    def __init__(self) -> None:
        self.segmenter = ClauseSegmenter()

    def parse_scan(
        self,
        raw_text: str,
        filename: str = "scan.png",
        confidence: float = 0.90,
    ) -> ParsedDocument:
        """Create a ParsedDocument representing an OCR output with recorded confidence."""
        segments = self.segmenter.segment(
            raw_text,
            base_id="ocr_c",
            page_number=1,
            source_type="ocr",
        )

        return ParsedDocument(
            filename=filename,
            source_type="ocr",
            full_text=raw_text,
            clauses=segments,
            page_count=1,
            ocr_confidence=round(confidence, 2),
            is_ocr=True,
            status="SUCCESS",
        )

    def apply_officer_correction(
        self,
        original_doc: ParsedDocument,
        corrected_text: str,
    ) -> ParsedDocument:
        """Update parsed document with officer-corrected text, setting verified confidence to 1.0."""
        new_segments = self.segmenter.segment(
            corrected_text,
            base_id="ocr_corrected",
            page_number=1,
            source_type="ocr_verified",
        )

        return ParsedDocument(
            filename=original_doc.filename,
            source_type="ocr",
            full_text=corrected_text,
            clauses=new_segments,
            page_count=original_doc.page_count,
            ocr_confidence=1.0,  # 100% verified by officer
            is_ocr=True,
            status="SUCCESS",
        )
