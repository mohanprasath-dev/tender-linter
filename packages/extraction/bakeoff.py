from __future__ import annotations

import datetime
import time
from pathlib import Path
from typing import Any

from packages.extraction.providers.base import Extractor
from packages.extraction.regex_extractor import RegexExtractor, detect_language
from packages.extraction.schema import ExtractionData
from packages.extraction.span_validator import validate_extraction_spans


class BakeoffRunner:
    """Executes the provider bake-off protocol and enforces selection rules (Spec 16.4)."""

    def __init__(self, candidates: list[Extractor]) -> None:
        self.candidates = candidates
        self.regex = RegexExtractor()

    def run_bakeoff(
        self,
        clauses: list[str],
        runs_per_clause: int = 3,
        report_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        today_str = datetime.date.today().isoformat()
        results: dict[str, dict[str, Any]] = {}

        for cand in self.candidates:
            cand_name = cand.name
            total_runs = 0
            valid_schema_runs = 0
            invented_citations = 0
            latencies: list[float] = []
            hindi_total = 0
            hindi_correct = 0
            outputs_per_clause: dict[int, list[str]] = {}

            # True citations from regex baseline on test set
            total_expected_citations = 0
            retrieved_expected_citations = 0
            total_predicted_citations = 0

            for idx, clause in enumerate(clauses):
                lang = detect_language(clause)
                baseline_citations = self.regex.extract(clause).citations
                total_expected_citations += len(baseline_citations)

                clause_runs_output = []

                for _ in range(runs_per_clause):
                    total_runs += 1
                    t0 = time.time()
                    try:
                        ext: ExtractionData = cand.extract(clause, language_hint=lang)
                        elapsed = (time.time() - t0) * 1000.0
                        latencies.append(elapsed)
                        valid_schema_runs += 1

                        # Validate spans
                        cleaned_dict, dropped, invented = validate_extraction_spans(
                            clause, ext.model_dump()
                        )
                        invented_citations += invented

                        # Citation recall calculation against baseline
                        model_citations = ext.citations
                        total_predicted_citations += len(model_citations)
                        for b_cit in baseline_citations:
                            if any(
                                m.is_number.upper().strip() == b_cit.is_number.upper().strip()
                                for m in model_citations
                            ):
                                retrieved_expected_citations += 1

                        if lang in ("hi", "mixed"):
                            hindi_total += 1
                            if len(model_citations) == len(baseline_citations):
                                hindi_correct += 1

                        # Serialized output for repeatability
                        clause_runs_output.append(
                            f"{[c.is_number for c in model_citations]}|{[p.text for p in ext.products]}"
                        )
                    except Exception:
                        latencies.append((time.time() - t0) * 1000.0)
                        clause_runs_output.append("ERROR")

                outputs_per_clause[idx] = clause_runs_output

            # Compute repeatability: fraction of clauses with identical outputs across runs
            identical_clauses = sum(
                1 for outputs in outputs_per_clause.values() if len(set(outputs)) == 1
            )
            repeatability = (
                identical_clauses / len(clauses) if clauses else 1.0
            )

            latencies.sort()
            p50 = latencies[len(latencies) // 2] if latencies else 0.0
            p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

            recall = (
                retrieved_expected_citations / (total_expected_citations * runs_per_clause)
                if total_expected_citations > 0
                else 1.0
            )
            precision = (
                retrieved_expected_citations / total_predicted_citations
                if total_predicted_citations > 0
                else 1.0
            )
            hindi_acc = hindi_correct / hindi_total if hindi_total > 0 else 1.0

            results[cand_name] = {
                "name": cand_name,
                "model_id": cand.model_id,
                "valid_schema_rate": valid_schema_runs / total_runs if total_runs > 0 else 0.0,
                "invented_citations": invented_citations,
                "citation_recall": round(recall, 4),
                "citation_precision": round(precision, 4),
                "hindi_accuracy": round(hindi_acc, 4),
                "repeatability": round(repeatability, 4),
                "latency_p50_ms": round(p50, 2),
                "latency_p95_ms": round(p95, 2),
                "rejected": invented_citations > 0,
            }

        # Apply Selection Rule (Spec 16.4.4):
        # 1. Reject any candidate with >= 1 invented citations
        eligible = [r for r in results.values() if not r["rejected"]]

        # 2. Highest citation recall, tie break on hindi, repeatability, latency
        eligible.sort(
            key=lambda x: (
                x["citation_recall"],
                x["hindi_accuracy"],
                x["repeatability"],
                -x["latency_p50_ms"],
            ),
            reverse=True,
        )

        chosen_primary = eligible[0]["name"] if eligible else None
        chosen_fallback = eligible[1]["name"] if len(eligible) > 1 else "RegexFallback"

        # Generate Report in Markdown
        report_lines = [
            f"# Provider Bake-off Report ({today_str})",
            "",
            "Planning basis: SIH2026 Problem Statement SIH26108. Team OnFocus.",
            f"Test set size: {len(clauses)} clauses, {runs_per_clause} runs per clause.",
            "",
            "## Results Table",
            "| Provider | Model ID | Schema Valid | Invented | Recall | Precision | Hindi Acc | Repeatability | p50 (ms) | Status |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]

        for r in results.values():
            status = "REJECTED (Invented Citations)" if r["rejected"] else "ELIGIBLE"
            report_lines.append(
                f"| {r['name']} | {r['model_id']} | {r['valid_schema_rate']*100:.1f}% | "
                f"{r['invented_citations']} | {r['citation_recall']*100:.1f}% | {r['citation_precision']*100:.1f}% | "
                f"{r['hindi_accuracy']*100:.1f}% | {r['repeatability']*100:.1f}% | {r['latency_p50_ms']} | {status} |"
            )

        report_lines.extend(
            [
                "",
                "## Selection Decision",
                f"- Primary Provider: {chosen_primary or 'None'}",
                f"- Fallback Provider: {chosen_fallback}",
                "- Selection Rule Applied: Spec 16.4.4 (reject candidates with >= 1 invented citations; pick highest recall).",
                "",
            ]
        )

        report_content = "\n".join(report_lines)

        filename = f"bakeoff-{today_str}.md"
        if report_dir:
            out_dir = Path(report_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            report_path = out_dir / filename
            report_path.write_text(report_content, encoding="utf-8")

        return {
            "date": today_str,
            "chosen_primary": chosen_primary,
            "chosen_fallback": chosen_fallback,
            "results": results,
            "report_filename": filename,
        }
