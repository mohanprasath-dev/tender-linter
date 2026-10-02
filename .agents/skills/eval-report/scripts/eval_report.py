"""Format evaluation results as 'X of Y on test set Z'."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict


def summarise(data: dict) -> list[str]:
    name, desc = data.get("set_name"), data.get("description")
    if not name or not desc:
        raise ValueError("set_name and description are required")
    res = data["results"]
    langs = sorted({r["language"] for r in res})
    head = f"Test set {name}: {len(res)} clauses, languages {'+'.join(langs)}. {desc}"
    lines = [head]
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in res:
        groups["all"].append(r)
        groups[r["language"]].append(r)
    for label, rows in groups.items():
        defects = [r for r in rows if r["kind"] == "defect"]
        planted = sum(len(r["expected"]) for r in defects)
        caught = sum(len(set(r["expected"]) & set(r["got"])) for r in defects)
        unexpected = sum(len(set(r["got"]) - set(r["expected"])) for r in defects)
        clean = [r for r in rows if r["kind"] == "clean"]
        false_alarm = sum(1 for r in clean if r["got"])
        abst = [r for r in rows if r["kind"] == "abstain"]
        abst_ok = sum(1 for r in abst if "R10" in r["got"])
        lines.append(f"[{label}] Rule recall: {caught} of {planted} planted defects caught")
        lines.append(f"[{label}] Unexpected findings on defect clauses: {unexpected}")
        lines.append(f"[{label}] False alarms: {false_alarm} of {len(clean)} clean controls had findings")
        lines.append(f"[{label}] Abstain correctness: {abst_ok} of {len(abst)} out-of-dataset clauses gave R10")
    return lines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("results_json")
    a = p.parse_args(argv)
    with open(a.results_json, encoding="utf-8") as fh:
        data = json.load(fh)
    print("\n".join(summarise(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
