import csv
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / ".agents" / "skills"


def load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, SK / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


norm = load("is-number-normaliser/scripts/normalise_is.py", "norm")
prov = load("provenance-row-check/scripts/check_provenance.py", "prov")
spans = load("span-validator/scripts/validate_spans.py", "spans")
evalr = load("eval-report/scripts/eval_report.py", "evalr")


# ---- normaliser ----
def test_part_and_year():
    c = norm.find_citations("conform to IS 13252 (Part 1): 2010.")[0]
    assert (c["is_number"], c["part"], c["year"]) == ("IS 13252", "1", 2010)
    assert c["raw"] == "IS 13252 (Part 1): 2010"


def test_is_iec_form():
    c = norm.find_citations("IS/IEC 62368 Part 1: 2023")[0]
    assert (c["is_number"], c["part"], c["year"]) == ("IS/IEC 62368", "1", 2023)


def test_dashed_number_no_year():
    c = norm.find_citations("IS 302-2-25")[0]
    assert (c["is_number"], c["part"], c["year"]) == ("IS 302-2-25", None, None)


def test_dash_year_form():
    c = norm.find_citations("IS 13252-2010")[0]
    assert (c["is_number"], c["year"]) == ("IS 13252", 2010)


def test_devanagari_digits_and_offsets():
    text = "लैपटॉप IS १३२५२ (भाग १): २०१०"
    c = norm.find_citations(text)[0]
    assert (c["is_number"], c["part"], c["year"]) == ("IS 13252", "1", 2010)
    s, e = c["span"]
    assert text[s:e] == c["raw"]


def test_no_false_match_on_lowercase_is():
    assert norm.find_citations("this is 2010 units and ISO 9001") == []


def test_suggest_near():
    assert norm.suggest_near("IS 13253", ["IS 13252", "IS 302-2-25"]) == ["IS 13252"]
    assert norm.suggest_near("IS 13252", ["IS 13252"]) == []


# ---- provenance ----
def good_row():
    return {
        "is_number": "IS 1",
        "title": "t",
        "catalogue_url": "https://x.example/a",
        "verified_on": "2026-10-02",
        "verified_by": "A",
        "second_checked_by": "B",
        "evidence_ref": "e1",
        "status": "Active",
        "publication_year": "2010",
    }


def test_provenance_verified():
    assert prov.check_row("standards", good_row())[0] == "VERIFIED"


def test_provenance_missing_blocks():
    r = good_row()
    r["catalogue_url"] = ""
    status, problems = prov.check_row("standards", r)
    assert status == "FAIL" and "catalogue_url" in problems[0]


def test_provenance_same_person_fails():
    r = good_row()
    r["second_checked_by"] = "a"
    assert prov.check_row("standards", r)[0] == "FAIL"


def test_provenance_unverified_text_fails():
    r = good_row()
    r["title"] = "UNVERIFIED claim"
    assert prov.check_row("standards", r)[0] == "FAIL"


def test_provenance_awaiting_second():
    r = good_row()
    r["second_checked_by"] = ""
    assert prov.check_row("standards", r)[0] == "AWAITING_SECOND_CHECK"


def test_seed_files_fail_until_filled():
    rows = prov.check_file(ROOT / "packages/data/seed/standards.csv")
    assert rows and all(s == "FAIL" for _, s, _ in rows)


# ---- spans ----
def test_spans_drop_and_count_invented():
    clause = "Laptops shall conform to IS 13252 (Part 1): 2010."
    s = clause.index("IS 13252")
    e = s + len("IS 13252 (Part 1): 2010")
    ext = {
        "products": [{"text": "Laptops", "span": [0, 7]}],
        "citations": [
            {
                "raw": "IS 13252 (Part 1): 2010",
                "span": [s, e],
                "is_number": "IS 13252",
                "part": "1",
                "year": 2010,
            },
            {"raw": "IS 99999: 2015", "span": [0, 5], "is_number": "IS 99999", "year": 2015},
            {
                "raw": "IS 13252 (Part 1): 2010",
                "span": [s, e],
                "is_number": "IS 13252",
                "year": 2011,
            },
        ],
    }
    out, dropped, invented = spans.validate(clause, ext)
    assert len(out["citations"]) == 1 and len(out["products"]) == 1
    assert len(dropped) == 2 and invented == 2


# ---- eval report ----
def test_eval_report_counts_and_requires_description():
    data = {
        "set_name": "synthetic-v1",
        "description": "synthetic, team-written",
        "results": [
            {
                "id": "T01",
                "language": "en",
                "kind": "defect",
                "expected": ["R05", "R06"],
                "got": ["R05"],
            },
            {"id": "T13", "language": "en", "kind": "clean", "expected": [], "got": []},
            {"id": "T07", "language": "en", "kind": "abstain", "expected": ["R10"], "got": ["R10"]},
        ],
    }
    text = "\n".join(evalr.summarise(data))
    assert "[all] Rule recall: 1 of 2 planted defects caught" in text
    assert "0 of 1 clean controls" in text
    assert "1 of 1 out-of-dataset" in text
    assert "%" not in text
    del data["description"]
    try:
        evalr.summarise(data)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


# ---- rules and corpus ----
def test_rules_yaml_complete():
    d = yaml.safe_load((ROOT / "packages/rules/rules.yaml").read_text(encoding="utf-8"))
    ids = [r["id"] for r in d["rules"]]
    assert ids == [f"R{i:02d}" for i in range(1, 15)]
    assert all(r["message_en"] and r["message_hi"] is None for r in d["rules"])
    banned = ("outdated", "withdrawn")
    for r in d["rules"]:
        if r["id"] != "R02":
            assert not any(b in r["message_en"].lower() for b in banned)


def test_corpus_matrix_and_normaliser_agree():
    rows = list(csv.DictReader((ROOT / "eval/corpus/synthetic-v1.csv").open(encoding="utf-8")))
    assert [r["id"] for r in rows] == [f"T{i:02d}" for i in range(1, 14)]
    t12 = next(r for r in rows if r["id"] == "T12")
    assert norm.find_citations(t12["clause"])[0]["is_number"] == "IS 13252"
    t10 = next(r for r in rows if r["id"] == "T10")
    assert norm.suggest_near(norm.find_citations(t10["clause"])[0]["is_number"], ["IS 13252"]) == [
        "IS 13252"
    ]


def test_no_em_dashes_in_repo_text():
    for p in ROOT.rglob("*"):
        if (
            p.suffix in {".md", ".yaml", ".yml", ".csv", ".py"}
            and ".git" not in p.parts
            and "node_modules" not in p.parts
            and ".venv" not in p.parts
            and p.name != "test_skill_scripts.py"
        ):
            assert "\u2014" not in p.read_text(encoding="utf-8"), p
