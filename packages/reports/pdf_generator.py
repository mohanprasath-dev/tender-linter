from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BANNER_TEXT = "This tool flags issues for the officer to review. It does not approve or reject a tender."


def generate_pdf_report(
    audit_meta: dict[str, Any],
    clauses: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> bytes:
    """Generate official bilingual tender audit report in PDF format."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
    )
    banner_style = ParagraphStyle(
        "BannerText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#b45309"),
    )
    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )
    table_head = ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )
    cell_text = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    cell_url = ParagraphStyle(
        "CellUrl",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1d4ed8"),
    )

    story: list[Any] = []

    # Title
    story.append(Paragraph("Tender Linter: Specification Audit Report", title_style))
    story.append(Spacer(1, 6))

    # Mandatory Reviewer Banner
    banner_data = [[Paragraph(f"NOTICE: {BANNER_TEXT}", banner_style)]]
    banner_table = Table(banner_data, colWidths=[540])
    banner_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f59e0b")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # Document Metadata Grid
    doc_name = audit_meta.get("document_name") or "Unnamed Document"
    audit_id = str(audit_meta.get("id", ""))
    created_at = audit_meta.get("created_at") or datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lang_hint = str(audit_meta.get("language_hint", "en")).upper()

    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "CANNOT_VERIFY": 0}
    for f in findings:
        sev = f.get("severity", "INFO")
        counts[sev] = counts.get(sev, 0) + 1

    meta_grid = [
        [
            Paragraph("Document Name:", meta_label),
            Paragraph(doc_name, meta_val),
            Paragraph("Audit ID:", meta_label),
            Paragraph(audit_id, meta_val),
        ],
        [
            Paragraph("Audited On:", meta_label),
            Paragraph(str(created_at), meta_val),
            Paragraph("Language Hint:", meta_label),
            Paragraph(lang_hint, meta_val),
        ],
        [
            Paragraph("Total Clauses:", meta_label),
            Paragraph(str(len(clauses)), meta_val),
            Paragraph("Total Findings:", meta_label),
            Paragraph(f"{len(findings)} (Errors: {counts['ERROR']}, Warnings: {counts['WARNING']}, Info: {counts['INFO']})", meta_val),
        ],
    ]
    meta_table = Table(meta_grid, colWidths=[90, 180, 90, 180])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # Section Heading
    story.append(Paragraph("Audit Findings and Verified Evidence", styles["Heading2"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=8))

    if not findings:
        story.append(Paragraph("No standard discrepancies or defect rules triggered.", styles["Normal"]))
    else:
        # Build clause map
        clause_map = {c.get("id"): c.get("text", "") for c in clauses}

        # Table header
        table_rows = [
            [
                Paragraph("Clause / Rule", table_head),
                Paragraph("Severity", table_head),
                Paragraph("Explanation (Bilingual: EN / HI)", table_head),
                Paragraph("Evidence & Verification", table_head),
                Paragraph("Officer Action", table_head),
            ]
        ]

        for f in findings:
            cid = f.get("clause_id", "")
            clause_snip = clause_map.get(cid, "")
            if len(clause_snip) > 80:
                clause_snip = clause_snip[:77] + "..."

            rule_id = f.get("rule_id", "")
            sev = f.get("severity", "INFO")
            msg_en = f.get("message_en", "")
            msg_hi = f.get("message_hi", "")

            ev = f.get("evidence") or {}
            ev_url = ev.get("url") or "N/A"
            ev_date = ev.get("verified_on") or "N/A"
            ev_ref = ev.get("evidence_ref") or ""

            col_clause = [
                Paragraph(f"<b>Clause:</b> {cid}", cell_bold),
                Paragraph(f'"{clause_snip}"', cell_text),
                Spacer(1, 2),
                Paragraph(f"<b>Rule:</b> {rule_id}", cell_bold),
            ]

            # Severity badge styling
            col_sev = Paragraph(f"<b>{sev}</b>", cell_bold)

            col_msg = [
                Paragraph(f"<b>[EN]</b> {msg_en}", cell_text),
                Spacer(1, 3),
                Paragraph(f"<b>[HI]</b> {msg_hi}", cell_text),
            ]

            col_evidence = [
                Paragraph(f"<b>Verified Date:</b> {ev_date}", cell_bold),
                Paragraph("<b>Evidence URL:</b>", cell_bold),
                Paragraph(f"<a href='{ev_url}'>{ev_url}</a>", cell_url),
            ]
            if ev_ref:
                col_evidence.append(Paragraph(f"<b>Ref:</b> {ev_ref}", cell_text))

            decision = f.get("decision")
            reason = f.get("decision_reason")
            decision_text = decision if decision else "Pending Review"
            col_action = [
                Paragraph(f"<b>Status:</b> {decision_text}", cell_bold),
            ]
            if reason:
                col_action.append(Paragraph(f"<b>Reason:</b> {reason}", cell_text))

            table_rows.append([col_clause, col_sev, col_msg, col_evidence, col_action])

        findings_table = Table(table_rows, colWidths=[100, 55, 175, 135, 75], repeatRows=1)
        findings_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(findings_table)

    doc.build(story)
    return buffer.getvalue()
