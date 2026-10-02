"""Ingestion package providing DOCX, PDF, OCR, and text parsing services."""

from packages.ingestion.docx_parser import DocxParser
from packages.ingestion.ocr_parser import OcrParser
from packages.ingestion.pdf_parser import PdfParser
from packages.ingestion.schema import BatchIngestResult, ClauseSegment, ParsedDocument
from packages.ingestion.segmenter import ClauseSegmenter
from packages.ingestion.service import IngestionService

__all__ = [
    "BatchIngestResult",
    "ClauseSegment",
    "ClauseSegmenter",
    "DocxParser",
    "IngestionService",
    "OcrParser",
    "ParsedDocument",
    "PdfParser",
]
