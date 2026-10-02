"""Evaluation harness runner for Tender Linter.
Measures metrics according to docs/PROJECT_SPEC.md Section 13.
"""

from __future__ import annotations

import csv
import statistics
import time
from pathlib import Path
from typing import Any

from eval.corpus.golden_extractions import get_golden_extractions
from packages.rules.context import create_seed_rule_context
from packages.rules.engine import RulesEngine
from packages.rules.loader import load_rules_from_yaml
from packages.rules.schema import Finding


def run_evaluation_suite(
    corpus_path: Path,
    mode: str = "deterministic",
) -> dict[str, Any]:
    """Execute the evaluation test set and return comprehensive metrics.

    Args:
        corpus_path: Path to the CSV corpus file.
        mode: 'deterministic' (mocked/gold extractions) or 'regex' (live regex extractor).

    Returns:
        Structured evaluation results with metrics matching spec 13.2.
    """
    catalog = load_rules_from_yaml()
    engine = RulesEngine(catalog=catalog)
    seed_context = create_seed_rule_context()

    with open(corpus_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        corpus = list(reader)

    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []

    total_expected_defects = 0
    caught_expected_defects = 0
    missed_defects: list[dict[str, Any]] = []

    clean_total = 0
    clean_false_alarms = 0
    clean_details: list[dict[str, Any]] = []

    abstain_total = 0
    abstain_correct = 0
    abstain_details: list[dict[str, Any]] = []

    adversarial_total = 0
    adversarial_passed = 0
    adversarial_details: list[dict[str, Any]] = []

    lang_stats: dict[str, dict[str, int]] = {
        "en": {"total": 0, "passed": 0},
        "hi": {"total": 0, "passed": 0},
        "mixed": {"total": 0, "passed": 0},
    }

    evidence_checked = 0
    evidence_complete = 0

    for row in corpus:
        row_id = row["id"]
        lang = row.get("language", "en")
        kind = row.get("kind", "defect")
        clause_text = row.get("clause", "")
        raw_expected = row.get("expected_rules", "").strip()
        expected_rules = set(raw_expected.split(";")) if raw_expected else set()

        # Update language counts
        if lang in lang_stats:
            lang_stats[lang]["total"] += 1

        t_start = time.perf_counter()

        # Obtain extractions
        if mode == "deterministic":
            clauses = get_golden_extractions(row_id, clause_text)
        else:
            # Fallback to regex extractor if requested
            from packages.extraction.regex_library import RegexExtractor
            extractor = RegexExtractor()
            clauses = [extractor.extract_clause(clause_text, clause_id=row_id)]

        # Evaluate rules
        findings = engine.evaluate_document(clauses, seed_context)
        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        latencies.append(t_elapsed_ms)

        # Ignore informational stale row R14 in synthetic matrix evaluation
        fired_rules = {f.rule_id for f in findings if f.rule_id != "R14"}

        # Evidence completeness check on applicable findings
        for f in findings:
            if f.rule_id in {"R02", "R03", "R04", "R05", "R06", "R07", "R08", "R13"}:
                evidence_checked += 1
                if f.evidence and (f.evidence.url or f.evidence.verified_on or f.evidence.instrument or f.evidence.candidate):
                    evidence_complete += 1

        case_passed = (fired_rules == expected_rules)

        if lang in lang_stats and case_passed:
            lang_stats[lang]["passed"] += 1

        # Track metrics by kind
        if kind == "clean":
            clean_total += 1
            if fired_rules:
                clean_false_alarms += 1
                clean_details.append({"id": row_id, "fired": sorted(list(fired_rules))})
        elif kind == "abstain":
            abstain_total += 1
            if "R10" in fired_rules and case_passed:
                abstain_correct += 1
            else:
                abstain_details.append({"id": row_id, "expected": sorted(list(expected_rules)), "got": sorted(list(fired_rules))})
        elif kind == "adversarial":
            adversarial_total += 1
            if case_passed:
                adversarial_passed += 1
            else:
                adversarial_details.append({"id": row_id, "expected": sorted(list(expected_rules)), "got": sorted(list(fired_rules))})
        else:
            # Planted defect
            for exp_r in expected_rules:
                total_expected_defects += 1
                if exp_r in fired_rules:
                    caught_expected_defects += 1
                else:
                    missed_defects.append({"id": row_id, "missed_rule": exp_r, "fired": sorted(list(fired_rules))})

        case_results.append({
            "id": row_id,
            "language": lang,
            "kind": kind,
            "clause": clause_text,
            "expected": sorted(list(expected_rules)),
            "got": sorted(list(fired_rules)),
            "passed": case_passed,
            "latency_ms": round(t_elapsed_ms, 2),
        })

    # Latency percentiles
    latencies_sorted = sorted(latencies)
    p50_ms = round(latencies_sorted[int(len(latencies_sorted) * 0.50)], 2)
    p95_ms = round(latencies_sorted[int(len(latencies_sorted) * 0.95)], 2)
    avg_ms = round(statistics.mean(latencies), 2)

    return {
        "set_name": "synthetic-v1",
        "description": "Expanded synthetic test corpus v1 with 65 clauses across English, Hindi, and mixed language.",
        "rule_set_version": catalog.rule_set_version,
        "total_clauses": len(corpus),
        "results": case_results,
        "metrics": {
            "rule_recall": {
                "total_expected": total_expected_defects,
                "caught": caught_expected_defects,
                "missed": len(missed_defects),
                "missed_details": missed_defects,
            },
            "false_alarms": {
                "clean_total": clean_total,
                "count": clean_false_alarms,
                "details": clean_details,
            },
            "abstain_correctness": {
                "total": abstain_total,
                "correct": abstain_correct,
                "details": abstain_details,
            },
            "adversarial_robustness": {
                "total": adversarial_total,
                "passed": adversarial_passed,
                "details": adversarial_details,
            },
            "languages": {
                lang: {
                    "passed": stats["passed"],
                    "total": stats["total"],
                }
                for lang, stats in lang_stats.items()
            },
            "evidence_completeness": {
                "total_applicable": evidence_checked,
                "complete": evidence_complete,
                "missing": evidence_checked - evidence_complete,
            },
            "latency": {
                "p50_ms": p50_ms,
                "p95_ms": p95_ms,
                "avg_ms": avg_ms,
                "total_ms": round(sum(latencies), 2),
            },
        },
    }
