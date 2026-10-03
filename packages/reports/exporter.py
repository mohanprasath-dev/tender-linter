from __future__ import annotations

import csv
import io
from typing import Any

from packages.reports.diff_analyzer import AuditDiffResult, analyze_audit_diff
from packages.reports.docx_generator import generate_docx_report
from packages.reports.pdf_generator import generate_pdf_report

BANNER_TEXT = "This tool flags issues for the officer to review. It does not approve or reject a tender."


def export_json_report(
    audit_meta: dict[str, Any],
    clauses: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate structured JSON report payload for an audit session."""
    return {
        "audit_id": audit_meta.get("id"),
        "document_name": audit_meta.get("document_name"),
        "created_at": audit_meta.get("created_at"),
        "status": audit_meta.get("status"),
        "banner": BANNER_TEXT,
        "total_clauses": len(clauses),
        "total_findings": len(findings),
        "clauses": clauses,
        "findings": findings,
    }


def export_csv_report(
    audit_meta: dict[str, Any],
    clauses: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> str:
    """Generate RFC-4180 compliant CSV export for audit findings with evidence links."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Clause ID",
            "Rule ID",
            "Severity",
            "English Message",
            "Hindi Message",
            "Evidence URL",
            "Verified On",
            "Evidence Ref",
            "Decision",
            "Decision Reason",
        ]
    )
    for f in findings:
        ev = f.get("evidence") or {}
        writer.writerow(
            [
                f.get("clause_id"),
                f.get("rule_id"),
                f.get("severity"),
                f.get("message_en"),
                f.get("message_hi"),
                ev.get("url"),
                ev.get("verified_on"),
                ev.get("evidence_ref"),
                f.get("decision"),
                f.get("decision_reason"),
            ]
        )
    return output.getvalue()


__all__ = [
    "BANNER_TEXT",
    "AuditDiffResult",
    "analyze_audit_diff",
    "export_csv_report",
    "export_json_report",
    "generate_docx_report",
    "generate_pdf_report",
]
