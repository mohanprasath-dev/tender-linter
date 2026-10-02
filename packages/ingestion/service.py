"""Unified Ingestion Service routing DOCX, PDF, OCR, and text with batch queue support."""

from __future__ import annotations

from pathlib import Path

from packages.ingestion.docx_parser import DocxParser
from packages.ingestion.ocr_parser import OcrParser
from packages.ingestion.pdf_parser import PdfParser
from packages.ingestion.schema import BatchIngestResult, ParsedDocument
from packages.ingestion.segmenter import ClauseSegmenter


class IngestionService:
    """Entry point for document ingestion, clause segmentation, and batch queueing."""

    def __init__(
        self,
        max_file_size_mb: float = 25.0,
        max_page_count: int = 100,
    ) -> None:
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.max_page_count = max_page_count

        self.segmenter = ClauseSegmenter()
        self.docx_parser = DocxParser()
        self.pdf_parser = PdfParser()
        self.ocr_parser = OcrParser()

    def ingest_text(self, text: str, filename: str = "pasted.txt") -> ParsedDocument:
        """Direct ingestion of pasted tender text."""
        segments = self.segmenter.segment(text, base_id="paste", source_type="text")
        return ParsedDocument(
            filename=filename,
            source_type="text",
            full_text=text,
            clauses=segments,
            page_count=1,
            is_ocr=False,
            status="SUCCESS",
        )

    def ingest_bytes(self, content: bytes, filename: str) -> ParsedDocument:
        """Route file bytes to corresponding parser based on file extension."""
        if len(content) > self.max_file_size_bytes:
            return ParsedDocument(
                filename=filename,
                source_type="unknown",
                full_text="",
                status="ERROR",
                error_message=f"File exceeds maximum size limit of {self.max_file_size_bytes // (1024*1024)} MB",
            )

        suffix = Path(filename).suffix.lower()

        if suffix == ".docx":
            return self.docx_parser.parse_bytes(content, filename=filename)
        elif suffix == ".pdf":
            doc = self.pdf_parser.parse_bytes(content, filename=filename)
            if doc.page_count > self.max_page_count:
                doc.status = "ERROR"
                doc.error_message = f"Page count ({doc.page_count}) exceeds limit of {self.max_page_count}"
            return doc
        elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            # OCR image path: simulated or fallback
            return self.ocr_parser.parse_scan(
                raw_text=content.decode("utf-8", errors="replace"),
                filename=filename,
                confidence=0.88,
            )
        else:
            # Fallback to plain text
            text = content.decode("utf-8", errors="replace")
            return self.ingest_text(text, filename=filename)

    def ingest_batch(self, files: list[tuple[str, bytes]]) -> BatchIngestResult:
        """Process multiple files sequentially in a batch queue."""
        docs: list[ParsedDocument] = []
        errors: list[str] = []
        total_clauses = 0

        for filename, content in files:
            try:
                doc = self.ingest_bytes(content, filename=filename)
                docs.append(doc)
                if doc.status == "SUCCESS":
                    total_clauses += len(doc.clauses)
                else:
                    errors.append(f"{filename}: {doc.error_message}")
            except Exception as e:
                err_msg = f"{filename}: Failed to parse ({str(e)})"
                errors.append(err_msg)
                docs.append(
                    ParsedDocument(
                        filename=filename,
                        source_type="error",
                        full_text="",
                        status="ERROR",
                        error_message=err_msg,
                    )
                )

        return BatchIngestResult(
            documents=docs,
            total_clauses=total_clauses,
            errors=errors,
        )
