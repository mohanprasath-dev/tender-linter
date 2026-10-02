"""Pydantic schemas for document ingestion and clause segmentation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClauseSegment(BaseModel):
    """Segmented tender clause with character offsets and metadata."""
    id: str
    text: str
    page_number: int | None = None
    paragraph_index: int = 0
    start_char: int = 0
    end_char: int = 0
    language: str = "en"
    source_type: str = "text"  # text, docx_paragraph, docx_table, pdf_page, ocr


class ParsedDocument(BaseModel):
    """Complete parsed document output from ingestion."""
    filename: str
    source_type: str  # text, docx, pdf, ocr
    full_text: str
    clauses: list[ClauseSegment] = Field(default_factory=list)
    page_count: int = 1
    ocr_confidence: float | None = None
    is_ocr: bool = False
    status: str = "SUCCESS"  # SUCCESS, ERROR
    error_message: str | None = None


class BatchIngestResult(BaseModel):
    """Batch ingestion output tracking multiple files."""
    documents: list[ParsedDocument] = Field(default_factory=list)
    total_clauses: int = 0
    errors: list[str] = Field(default_factory=list)
