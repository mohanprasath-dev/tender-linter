from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClauseDiff(BaseModel):
    added: list[dict[str, Any]] = Field(default_factory=list)
    removed: list[dict[str, Any]] = Field(default_factory=list)
    modified: list[dict[str, Any]] = Field(default_factory=list)
    unchanged: list[dict[str, Any]] = Field(default_factory=list)


class AuditDiffResult(BaseModel):
    draft_a_id: str
    draft_b_id: str
    added_findings: list[dict[str, Any]] = Field(default_factory=list)
    resolved_findings: list[dict[str, Any]] = Field(default_factory=list)
    retained_findings: list[dict[str, Any]] = Field(default_factory=list)
    clause_diff: ClauseDiff = Field(default_factory=ClauseDiff)
    summary: dict[str, Any] = Field(default_factory=dict)


def analyze_audit_diff(
    draft_a_id: str,
    draft_b_id: str,
    clauses_a: list[dict[str, Any]],
    clauses_b: list[dict[str, Any]],
    findings_a: list[dict[str, Any]],
    findings_b: list[dict[str, Any]],
) -> AuditDiffResult:
    """Compare clauses and findings between two tender draft audits."""
    # 1. Clause diff by ID and normalized text
    map_clauses_a = {c.get("id"): c for c in clauses_a}
    map_clauses_b = {c.get("id"): c for c in clauses_b}

    added_clauses: list[dict[str, Any]] = []
    removed_clauses: list[dict[str, Any]] = []
    modified_clauses: list[dict[str, Any]] = []
    unchanged_clauses: list[dict[str, Any]] = []

    for cid, ca in map_clauses_a.items():
        if cid not in map_clauses_b:
            removed_clauses.append(ca)
        else:
            cb = map_clauses_b[cid]
            if ca.get("text", "").strip() != cb.get("text", "").strip():
                modified_clauses.append({
                    "id": cid,
                    "old_text": ca.get("text"),
                    "new_text": cb.get("text"),
                })
            else:
                unchanged_clauses.append(cb)

    for cid, cb in map_clauses_b.items():
        if cid not in map_clauses_a:
            added_clauses.append(cb)

    clause_diff = ClauseDiff(
        added=added_clauses,
        removed=removed_clauses,
        modified=modified_clauses,
        unchanged=unchanged_clauses,
    )

    # 2. Finding diff by (clause_id, rule_id, span)
    def finding_key(f: dict[str, Any]) -> tuple[Any, ...]:
        span = tuple(f.get("span") or (0, 0))
        return (f.get("clause_id"), f.get("rule_id"), span)

    keys_a = {finding_key(f): f for f in findings_a}
    keys_b = {finding_key(f): f for f in findings_b}

    added_findings = [keys_b[k] for k in keys_b.keys() - keys_a.keys()]
    resolved_findings = [keys_a[k] for k in keys_a.keys() - keys_b.keys()]
    retained_findings = [keys_b[k] for k in keys_a.keys() & keys_b.keys()]

    summary = {
        "total_findings_draft_a": len(findings_a),
        "total_findings_draft_b": len(findings_b),
        "added_count": len(added_findings),
        "resolved_count": len(resolved_findings),
        "retained_count": len(retained_findings),
        "clauses_added_count": len(added_clauses),
        "clauses_modified_count": len(modified_clauses),
        "clauses_removed_count": len(removed_clauses),
    }

    return AuditDiffResult(
        draft_a_id=draft_a_id,
        draft_b_id=draft_b_id,
        added_findings=added_findings,
        resolved_findings=resolved_findings,
        retained_findings=retained_findings,
        clause_diff=clause_diff,
        summary=summary,
    )
