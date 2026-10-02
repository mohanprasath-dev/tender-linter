import csv
import subprocess
import sys
from pathlib import Path

from packages.rules.loader import load_rules_from_yaml

CORPUS_PATH = Path(__file__).resolve().parents[1] / "eval" / "corpus" / "synthetic-v1.csv"
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def test_corpus_v1_size_and_structure():
    """Verify that test corpus v1 has at least 60 clauses and proper categorization."""
    assert CORPUS_PATH.exists(), f"Corpus not found at {CORPUS_PATH}"

    with open(CORPUS_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Must have at least 60 clauses per spec 16.6 M8
    assert len(rows) >= 60, f"Expected at least 60 clauses, found {len(rows)}"

    required_fields = {"id", "language", "kind", "clause", "expected_rules", "notes"}
    assert required_fields.issubset(set(reader.fieldnames or []))

    # Verify counts by kind
    clean_controls = [r for r in rows if r["kind"] == "clean"]
    adversarial_cases = [r for r in rows if r["kind"] == "adversarial"]
    abstain_cases = [r for r in rows if r["kind"] == "abstain"]
    defect_cases = [r for r in rows if r["kind"] == "defect"]

    assert len(clean_controls) >= 10, f"Expected at least 10 clean controls, found {len(clean_controls)}"
    assert len(adversarial_cases) >= 10, f"Expected at least 10 adversarial cases, found {len(adversarial_cases)}"
    assert len(abstain_cases) >= 5, f"Expected at least 5 abstain cases, found {len(abstain_cases)}"
    assert len(defect_cases) >= 20, f"Expected at least 20 defect cases, found {len(defect_cases)}"

    # Verify languages present: en, hi, mixed
    languages = {r["language"] for r in rows}
    assert "en" in languages, "Missing English clauses"
    assert "hi" in languages, "Missing Hindi clauses"
    assert "mixed" in languages, "Missing mixed clauses"

    # Verify clean controls have no expected defect rules
    for c in clean_controls:
        assert not c["expected_rules"].strip(), f"Clean control {c['id']} must not expect rules, got {c['expected_rules']}"

    # Verify abstain cases trigger R10
    for a in abstain_cases:
        assert "R10" in a["expected_rules"], f"Abstain case {a['id']} must expect R10"


def test_no_em_dashes_in_corpus():
    """Strictly enforce zero em dashes in corpus text."""
    em_dash = chr(8212)
    with open(CORPUS_PATH, encoding="utf-8") as f:
        content = f.read()
    assert em_dash not in content, "Found forbidden em dash in eval/corpus/synthetic-v1.csv"


def test_eval_runner_execution_and_metrics():
    """Verify that the eval runner executes and returns valid metrics structure."""
    from eval.runner import run_evaluation_suite

    results = run_evaluation_suite(corpus_path=CORPUS_PATH, mode="deterministic")

    assert results["set_name"] == "synthetic-v1"
    assert "synthetic" in results["description"].lower()
    assert results["total_clauses"] >= 60

    # Rule recall: all planted defects caught
    metrics = results["metrics"]
    assert metrics["rule_recall"]["missed"] == 0, f"Missed planted defects: {metrics['rule_recall']['missed_details']}"
    assert metrics["rule_recall"]["caught"] == metrics["rule_recall"]["total_expected"]

    # False alarms: 0 on clean controls
    assert metrics["false_alarms"]["count"] == 0, f"False alarms on clean controls: {metrics['false_alarms']['details']}"

    # Abstain correctness: all unmapped products triggered R10
    assert metrics["abstain_correctness"]["correct"] == metrics["abstain_correctness"]["total"]

    # Evidence completeness: 100% of findings on verified standards have link and date
    assert metrics["evidence_completeness"]["missing"] == 0


def test_eval_report_generation():
    """Verify eval_report.py generates report adhering to eval-report skill constraints."""
    from eval.runner import run_evaluation_suite
    from scripts.eval_report import generate_markdown_report

    results = run_evaluation_suite(corpus_path=CORPUS_PATH, mode="deterministic")
    report_md = generate_markdown_report(results)

    # Must say synthetic
    assert "synthetic" in report_md.lower()

    # Rule set version recorded
    catalog = load_rules_from_yaml()
    assert catalog.rule_set_version in report_md

    # Honest X of Y format
    assert " of " in report_md

    # Check zero em dashes in generated report
    em_dash = chr(8212)
    assert em_dash not in report_md, "Found em dash in generated eval report"


def test_cli_runner_exit_code_zero():
    """Verify the CLI runner command executes and returns exit code 0."""
    runner_script = SCRIPTS_DIR / "eval_runner.py"
    assert runner_script.exists(), "eval_runner.py not found in scripts/"

    cmd = [sys.executable, str(runner_script), "--corpus", str(CORPUS_PATH), "--mode", "deterministic"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert proc.returncode == 0, f"Runner failed with exit code {proc.returncode}:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "Evaluation Report" in proc.stdout
    assert " of " in proc.stdout
