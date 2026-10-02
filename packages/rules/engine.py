from __future__ import annotations

import datetime
import uuid
from typing import Any

from packages.rules.context import (
    ProductRecord,
    RuleDataContext,
)
from packages.rules.normaliser import base_is_number, suggest_near_standard
from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    Finding,
    FindingEvidence,
    RuleCatalog,
    Severity,
    VaguePhraseExtraction,
)

CERTIFICATION_TERMS_LOWER = [
    "crs",
    "compulsory registration scheme",
    "bis registration",
    "isi mark",
    "registration under",
    "अनिवार्य पंजीकरण",
    "सीआरएस",
    "बीआईएस पंजीकरण",
]


class RulesEngine:
    def __init__(self, catalog: RuleCatalog):
        self.catalog = catalog
        self.rules_by_id = {r.id: r for r in catalog.rules}
        self.version = catalog.rule_set_version

    def _mentions_certification(self, clause: ClauseExtraction) -> bool:
        if clause.mentions_certification:
            return True
        text_lower = clause.text.lower()
        return any(term in text_lower for term in CERTIFICATION_TERMS_LOWER)

    def _create_finding(
        self,
        rule_id: str,
        clause_id: str,
        span: tuple[int, int] | None,
        msg_params: dict[str, Any],
        evidence: FindingEvidence | None = None,
        override_severity: Severity | None = None,
    ) -> Finding:
        rule_def = self.rules_by_id[rule_id]
        severity = override_severity or rule_def.severity
        try:
            message_en = rule_def.message_en.format(**msg_params)
        except KeyError:
            message_en = rule_def.message_en

        finding_id = f"f_{uuid.uuid4().hex[:8]}"
        return Finding(
            id=finding_id,
            rule_id=rule_id,
            severity=severity,
            clause_id=clause_id,
            span=span,
            message_en=message_en,
            message_hi=rule_def.message_hi,
            evidence=evidence,
            rule_set_version=self.version,
        )

    def _check_stale(
        self,
        row_id: int,
        verified_on: datetime.date | None,
        clause_id: str,
        context: RuleDataContext,
        used_rows: set[int],
    ) -> Finding | None:
        if row_id in used_rows or verified_on is None:
            return None
        used_rows.add(row_id)
        days_old = (datetime.date.today() - verified_on).days
        if days_old > context.stale_days:
            return self._create_finding(
                rule_id="R14",
                clause_id=clause_id,
                span=None,
                msg_params={"verified_on": str(verified_on)},
                evidence=FindingEvidence(row_id=row_id, verified_on=str(verified_on)),
            )
        return None

    def evaluate_clause(
        self,
        clause: ClauseExtraction,
        context: RuleDataContext,
        all_cited_numbers: set[str] | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        used_rows: set[int] = set()

        if all_cited_numbers is None:
            all_cited_numbers = {base_is_number(c.is_number) for c in clause.citations}

        known_standards = context.list_known_is_numbers()

        # Step 1: Check vague wording (R09)
        vague_phrases = list(clause.vague_phrases)
        if not vague_phrases:
            for vt in context.get_vague_terms():
                if vt.term.lower() in clause.text.lower():
                    # Find span in clause text
                    start = clause.text.lower().find(vt.term.lower())
                    end = start + len(vt.term)
                    vague_phrases.append(
                        VaguePhraseExtraction(
                            text=clause.text[start:end],
                            span=(start, end),
                            phrase=vt.term,
                            explanation=vt.explanation,
                        )
                    )

        for vp in vague_phrases:
            expl = getattr(vp, "explanation", None) or "Refers to quality generally without specifying a standard number."
            findings.append(
                self._create_finding(
                    rule_id="R09",
                    clause_id=clause.clause_id,
                    span=vp.span,
                    msg_params={"explanation": expl},
                    evidence=FindingEvidence(term=vp.text, explanation=expl),
                )
            )

        # Step 2: Product mapping & rules
        mapped_products: list[ProductRecord] = []
        has_unmapped_product = False

        for prod_ext in clause.products:
            prod_record = None
            if prod_ext.canonical_product_id:
                prod_record = context.get_product(prod_ext.canonical_product_id)
            if not prod_record and prod_ext.text:
                prod_record = context.get_product(prod_ext.text)

            if prod_record:
                if prod_record not in mapped_products:
                    mapped_products.append(prod_record)
            else:
                has_unmapped_product = True

        # Rule R10: Abstain if product unmapped
        if has_unmapped_product and not mapped_products and not clause.citations:
            findings.append(
                self._create_finding(
                    rule_id="R10",
                    clause_id=clause.clause_id,
                    span=clause.products[0].span if clause.products else None,
                    msg_params={},
                    evidence=None,
                )
            )
            return findings

        # Rule R07: Mapped product present, but no standard cited
        if mapped_products and not clause.citations:
            for prod in mapped_products:
                maps = context.get_product_standard_maps_for_product(prod.id)
                std_names = []
                verified_date = None
                evidence_url = None
                map_id = None
                for m in maps:
                    std = context.get_standard_by_id(m.standard_id)
                    if std:
                        std_names.append(std.is_number)
                    if m.verified_on and not verified_date:
                        verified_date = str(m.verified_on)
                        evidence_url = m.source_url
                        map_id = m.id

                findings.append(
                    self._create_finding(
                        rule_id="R07",
                        clause_id=clause.clause_id,
                        span=None,
                        msg_params={
                            "standards": ", ".join(std_names) if std_names else "standards in catalogue",
                            "verified_on": verified_date or "verified date not recorded",
                        },
                        evidence=FindingEvidence(url=evidence_url, verified_on=verified_date, row_id=map_id),
                    )
                )

        # Rule R06: Certification not mentioned
        mentions_cert = self._mentions_certification(clause)
        for prod in mapped_products:
            cert_rules = context.get_certification_rules_for_product(prod.id)
            for cr in cert_rules:
                if not mentions_cert:
                    findings.append(
                        self._create_finding(
                            rule_id="R06",
                            clause_id=clause.clause_id,
                            span=None,
                            msg_params={"verified_on": str(cr.verified_on or "")},
                            evidence=FindingEvidence(
                                url=cr.source_url,
                                verified_on=str(cr.verified_on or ""),
                                row_id=cr.id,
                                instrument=cr.instrument,
                            ),
                            override_severity=Severity.CANNOT_VERIFY if cr.is_conflict else None,
                        )
                    )
                    stale_f = self._check_stale(cr.id, cr.verified_on, clause.clause_id, context, used_rows)
                    if stale_f:
                        findings.append(stale_f)

        # Step 3: Evaluate citations
        for citation in clause.citations:
            std_record = context.get_standard_by_number(citation.is_number)
            if not std_record:
                std_record = context.get_standard_by_number(base_is_number(citation.is_number))

            if not std_record:
                # Check R12: Typo candidate
                near_candidates = suggest_near_standard(citation.is_number, known_standards)
                if near_candidates:
                    cand = near_candidates[0]
                    findings.append(
                        self._create_finding(
                            rule_id="R12",
                            clause_id=clause.clause_id,
                            span=citation.span,
                            msg_params={"candidate": cand},
                            evidence=FindingEvidence(candidate=cand),
                        )
                    )
                    # Decision B1: R12 suppresses R01
                    continue
                else:
                    # Rule R01: Unknown citation
                    findings.append(
                        self._create_finding(
                            rule_id="R01",
                            clause_id=clause.clause_id,
                            span=citation.span,
                            msg_params={},
                            evidence=None,
                        )
                    )
                    continue

            # Standard is known: Check conflict status
            is_conflicted = std_record.is_conflict or std_record.status == "CONFLICT"

            # Check staleness
            stale_f = self._check_stale(std_record.id, std_record.verified_on, clause.clause_id, context, used_rows)
            if stale_f:
                findings.append(stale_f)

            # Rule R02: Superseded or withdrawn
            if std_record.status in ("Withdrawn", "Superseded") and std_record.verified_on is not None:
                findings.append(
                    self._create_finding(
                        rule_id="R02",
                        clause_id=clause.clause_id,
                        span=citation.span,
                        msg_params={
                            "status": std_record.status,
                            "verified_on": str(std_record.verified_on),
                        },
                        evidence=FindingEvidence(
                            url=std_record.catalogue_url,
                            verified_on=str(std_record.verified_on),
                            row_id=std_record.id,
                        ),
                        override_severity=Severity.CANNOT_VERIFY if is_conflicted else Severity.ERROR,
                    )
                )

            # Rule R03: Year differs
            if citation.year and std_record.publication_year:
                if citation.year != std_record.publication_year:
                    findings.append(
                        self._create_finding(
                            rule_id="R03",
                            clause_id=clause.clause_id,
                            span=citation.span,
                            msg_params={
                                "cited_year": str(citation.year),
                                "catalogue_year": str(std_record.publication_year),
                                "verified_on": str(std_record.verified_on or ""),
                            },
                            evidence=FindingEvidence(
                                url=std_record.catalogue_url,
                                verified_on=str(std_record.verified_on or ""),
                                row_id=std_record.id,
                            ),
                            override_severity=Severity.CANNOT_VERIFY if is_conflicted else Severity.WARNING,
                        )
                    )

            # Rule R04: Part or section mismatch
            if std_record.part:
                if not citation.part or str(citation.part).strip() != str(std_record.part).strip():
                    findings.append(
                        self._create_finding(
                            rule_id="R04",
                            clause_id=clause.clause_id,
                            span=citation.span,
                            msg_params={"verified_on": str(std_record.verified_on or "")},
                            evidence=FindingEvidence(
                                url=std_record.catalogue_url,
                                verified_on=str(std_record.verified_on or ""),
                                row_id=std_record.id,
                            ),
                            override_severity=Severity.CANNOT_VERIFY if is_conflicted else Severity.WARNING,
                        )
                    )

            # Rule R05: Differs from certification list
            for prod in mapped_products:
                cert_rules = context.get_certification_rules_for_product(prod.id)
                for cr in cert_rules:
                    spec_std = context.get_standard_by_id(cr.specified_standard_id)
                    if spec_std and spec_std.id != std_record.id:
                        findings.append(
                            self._create_finding(
                                rule_id="R05",
                                clause_id=clause.clause_id,
                                span=citation.span,
                                msg_params={
                                    "specified": spec_std.is_number,
                                    "cited": citation.raw,
                                    "verified_on": str(cr.verified_on or ""),
                                },
                                evidence=FindingEvidence(
                                    url=cr.source_url,
                                    verified_on=str(cr.verified_on or ""),
                                    row_id=cr.id,
                                    instrument=cr.instrument,
                                ),
                                override_severity=Severity.CANNOT_VERIFY if (is_conflicted or cr.is_conflict) else Severity.ERROR,
                            )
                        )
                        stale_f = self._check_stale(cr.id, cr.verified_on, clause.clause_id, context, used_rows)
                        if stale_f:
                            findings.append(stale_f)

            # Rule R13: Wrong product family
            for prod in mapped_products:
                std_maps = context.get_product_standard_maps_for_standard(std_record.id)
                mapped_product_ids = {m.product_id for m in std_maps}
                if mapped_product_ids and prod.id not in mapped_product_ids:
                    for m in std_maps:
                        other_prod = context.get_product(m.product_id)
                        if other_prod and other_prod.family != prod.family:
                            other_name = other_prod.canonical_name
                            findings.append(
                                self._create_finding(
                                    rule_id="R13",
                                    clause_id=clause.clause_id,
                                    span=citation.span,
                                    msg_params={
                                        "other_product": other_name,
                                        "verified_on": str(m.verified_on or ""),
                                    },
                                    evidence=FindingEvidence(
                                        url=m.source_url,
                                        verified_on=str(m.verified_on or ""),
                                        row_id=m.id,
                                        other_product=other_name,
                                    ),
                                    override_severity=Severity.CANNOT_VERIFY if (is_conflicted or m.is_conflict) else Severity.WARNING,
                                )
                            )
                            stale_f = self._check_stale(m.id, m.verified_on, clause.clause_id, context, used_rows)
                            if stale_f:
                                findings.append(stale_f)
                            break

            # Rule R08: Allied standard absent
            allied_links = context.get_allied_links_for_standard(std_record.id)
            for link in allied_links:
                target_std = context.get_standard_by_id(link.target_standard_id)
                if target_std:
                    target_base = base_is_number(target_std.is_number)
                    if target_base not in all_cited_numbers and target_std.is_number not in all_cited_numbers:
                        findings.append(
                            self._create_finding(
                                rule_id="R08",
                                clause_id=clause.clause_id,
                                span=citation.span,
                                msg_params={
                                    "allied": target_std.is_number,
                                    "verified_on": str(link.verified_on or ""),
                                },
                                evidence=FindingEvidence(
                                    url=link.source_url,
                                    verified_on=str(link.verified_on or ""),
                                    row_id=link.id,
                                ),
                                override_severity=Severity.CANNOT_VERIFY if (is_conflicted or link.is_conflict) else Severity.INFO,
                            )
                        )
                        stale_f = self._check_stale(link.id, link.verified_on, clause.clause_id, context, used_rows)
                        if stale_f:
                            findings.append(stale_f)

        return findings

    def evaluate_document(
        self,
        clauses: list[ClauseExtraction],
        context: RuleDataContext,
    ) -> list[Finding]:
        all_findings: list[Finding] = []

        all_cited_numbers = {
            base_is_number(c.is_number)
            for cl in clauses
            for c in cl.citations
        }

        # Step 1: Rule R11 - Internal contradiction across document
        citations_by_standard: dict[str, list[tuple[ClauseExtraction, CitationExtraction]]] = {}
        for cl in clauses:
            for cit in cl.citations:
                base = base_is_number(cit.is_number)
                citations_by_standard.setdefault(base, []).append((cl, cit))

        for base, cit_list in citations_by_standard.items():
            if len(cit_list) > 1:
                years = {c[1].year for c in cit_list if c[1].year is not None}
                parts = {c[1].part for c in cit_list if c[1].part is not None}
                if len(years) > 1 or len(parts) > 1:
                    loc_a = f"{cit_list[0][0].clause_id}"
                    loc_b = f"{cit_list[1][0].clause_id}"
                    all_findings.append(
                        self._create_finding(
                            rule_id="R11",
                            clause_id=cit_list[0][0].clause_id,
                            span=cit_list[0][1].span,
                            msg_params={
                                "location_a": loc_a,
                                "location_b": loc_b,
                            },
                            evidence=FindingEvidence(locations=[loc_a, loc_b]),
                        )
                    )

        # Step 2: Evaluate individual clauses
        for clause in clauses:
            clause_findings = self.evaluate_clause(clause, context, all_cited_numbers=all_cited_numbers)
            all_findings.extend(clause_findings)

        return all_findings
