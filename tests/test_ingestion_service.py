import io

import docx
from reportlab.pdfgen import canvas

from packages.ingestion.docx_parser import DocxParser
from packages.ingestion.ocr_parser import OcrParser
from packages.ingestion.pdf_parser import PdfParser
from packages.ingestion.segmenter import ClauseSegmenter
from packages.ingestion.service import IngestionService
from packages.rules.context import create_seed_rule_context
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
)

SAMPLE_CLAUSE = "The supplier shall deliver 50 laptops. The laptops shall conform to IS 13252 (Part 1): 2010."


def create_sample_docx(text: str) -> bytes:
    """Create in-memory DOCX file with sample text and tables."""
    doc = docx.Document()
    doc.add_heading("Tender Specification Document", level=1)
    doc.add_paragraph("Clause 1.1: General Equipment Requirements")
    doc.add_paragraph(text)

    # Add a table
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "Standard"
    table.cell(1, 0).text = "Laptops"
    table.cell(1, 1).text = "IS 13252 (Part 1): 2010"

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def create_sample_pdf(text: str) -> bytes:
    """Create in-memory PDF file with reportlab."""
    bio = io.BytesIO()
    c = canvas.Canvas(bio)
    c.drawString(100, 750, "Tender Specification Document")
    c.drawString(100, 700, "Clause 1.1: Equipment Requirements")
    c.drawString(100, 650, text)
    c.showPage()
    c.save()
    return bio.getvalue()


def test_clause_segmenter_numbering_and_offsets():
    """Verify segmenter detects numbered clauses and preserves character offsets."""
    raw_text = (
        "Clause 1.1: The supplier shall deliver 50 laptops. The laptops shall conform to IS 13252 (Part 1): 2010.\n\n"
        "Clause 1.2: 10 microwave ovens conforming to IS 302-2-25 shall be delivered.\n\n"
        "Clause 1.3: Registration under the Compulsory Registration Scheme is required."
    )

    segmenter = ClauseSegmenter()
    segments = segmenter.segment(raw_text)

    assert len(segments) >= 3
    assert "laptops" in segments[0].text
    assert "microwave" in segments[1].text
    assert "Registration" in segments[2].text

    # Offsets must slice exact substring
    for seg in segments:
        assert raw_text[seg.start_char : seg.end_char] == seg.text


def test_docx_parser():
    """Verify DocxParser extracts paragraphs and tables into structured clauses."""
    docx_bytes = create_sample_docx(SAMPLE_CLAUSE)
    parser = DocxParser()
    parsed = parser.parse_bytes(docx_bytes, filename="tender_spec.docx")

    assert parsed.filename == "tender_spec.docx"
    assert parsed.source_type == "docx"
    assert len(parsed.clauses) >= 2

    # Check that our sample clause is present in the extracted clauses
    found_clause = any(SAMPLE_CLAUSE in c.text for c in parsed.clauses)
    assert found_clause, "Sample clause not found in parsed DOCX output"


def test_pdf_parser():
    """Verify PdfParser extracts text preserving page numbers and clause offsets."""
    pdf_bytes = create_sample_pdf(SAMPLE_CLAUSE)
    parser = PdfParser()
    parsed = parser.parse_bytes(pdf_bytes, filename="tender_spec.pdf")

    assert parsed.filename == "tender_spec.pdf"
    assert parsed.source_type == "pdf"
    assert parsed.page_count >= 1
    assert len(parsed.clauses) >= 1

    # Check clause text extraction
    combined = " ".join(c.text for c in parsed.clauses)
    assert "50 laptops" in combined
    assert "IS 13252" in combined


def test_ocr_parser_with_confidence_and_correction():
    """Verify OcrParser provides confidence score, editable text, and offset mapping."""
    parser = OcrParser()
    # Mock scanned image or low-confidence page
    simulated_scan_text = "The supplier sha11 deliver 50 laptops conforming to IS 13252 (Part 1): 2010."
    parsed = parser.parse_scan(simulated_scan_text, filename="scanned_tender.png", confidence=0.91)

    assert parsed.is_ocr is True
    assert parsed.ocr_confidence == 0.91
    assert "sha11" in parsed.full_text

    # Officer correction hook
    corrected_text = parsed.full_text.replace("sha11", "shall")
    corrected_doc = parser.apply_officer_correction(parsed, corrected_text)

    assert "shall" in corrected_doc.full_text
    assert "sha11" not in corrected_doc.full_text
    assert corrected_doc.is_ocr is True
    assert corrected_doc.ocr_confidence == 1.0  # Officer verified


def test_ingestion_parity_with_pasted_text():
    """Verify DOCX, PDF, and pasted text yield the same findings under the rules engine."""
    service = IngestionService()
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    context = create_seed_rule_context()

    # 1. Pasted text ingestion
    pasted_doc = service.ingest_text(SAMPLE_CLAUSE, filename="pasted.txt")

    # 2. DOCX ingestion
    docx_bytes = create_sample_docx(SAMPLE_CLAUSE)
    docx_doc = service.ingest_bytes(docx_bytes, filename="tender.docx")

    # 3. PDF ingestion
    pdf_bytes = create_sample_pdf(SAMPLE_CLAUSE)
    pdf_doc = service.ingest_bytes(pdf_bytes, filename="tender.pdf")

    def run_audit_on_doc(doc) -> set[str]:
        # Build extractions for clause containing SAMPLE_CLAUSE
        target_clause = next(c for c in doc.clauses if "50 laptops" in c.text)
        ce = ClauseExtraction(
            clause_id=target_clause.id,
            text=target_clause.text,
            products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
            citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2010)],
            mentions_certification=False,
        )
        findings = engine.evaluate_document([ce], context)
        return {f.rule_id for f in findings if f.rule_id != "R14"}

    pasted_findings = run_audit_on_doc(pasted_doc)
    docx_findings = run_audit_on_doc(docx_doc)
    pdf_findings = run_audit_on_doc(pdf_doc)

    assert pasted_findings == {"R05", "R06"}
    assert docx_findings == pasted_findings
    assert pdf_findings == pasted_findings


def test_batch_ingestion_queue():
    """Verify batch ingestion handles multiple documents and returns per-file reports."""
    service = IngestionService()

    files = [
        ("doc1.docx", create_sample_docx(SAMPLE_CLAUSE)),
        ("doc2.pdf", create_sample_pdf(SAMPLE_CLAUSE)),
        ("doc3.txt", SAMPLE_CLAUSE.encode("utf-8")),
    ]

    batch_result = service.ingest_batch(files)

    assert len(batch_result.documents) == 3
    assert batch_result.total_clauses >= 3
    assert all(d.status == "SUCCESS" for d in batch_result.documents)
