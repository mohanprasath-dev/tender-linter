"""Validate extraction spans against the clause text."""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

_DEV = {ord(c): str(i) for i, c in enumerate("०१२३४५६७८९")}
FIELDS = (("products", "text"), ("citations", "raw"), ("vague_phrases", "text"), ("requirements", "text"))


def _fold(s: str) -> str:
    return "".join(
        n if len(n := unicodedata.normalize("NFKC", c)) == 1 else c for c in s
    ).translate(_DEV)


def _span_ok(clause: str, item: dict, key: str) -> bool:
    span, text = item.get("span"), item.get(key)
    if not (isinstance(span, list) and len(span) == 2 and isinstance(text, str)):
        return False
    s, e = span
    return isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(clause) and clause[s:e] == text


def _citation_consistent(item: dict) -> bool:
    raw = _fold(item.get("raw") or "")
    year = item.get("year")
    if year is not None and str(year) not in raw:
        return False
    num = item.get("is_number")
    if num:
        return all(g in raw for g in re.findall(r"\d+", num))
    return True


def validate(clause: str, extraction: dict) -> tuple[dict, list[dict], int]:
    out = dict(extraction)
    dropped: list[dict] = []
    invented = 0
    for field, key in FIELDS:
        kept = []
        for item in extraction.get(field, []):
            ok = _span_ok(clause, item, key)
            if ok and field == "citations" and not _citation_consistent(item):
                ok = False
                invented += 1
            elif not ok and field == "citations" and (item.get(key) or "") not in clause:
                invented += 1
            (kept if ok else dropped).append(item if ok else {"field": field, "item": item})
        out[field] = kept
    return out, dropped, invented


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("clause_file")
    p.add_argument("extraction_file")
    p.add_argument("--strict", action="store_true")
    a = p.parse_args(argv)
    with open(a.clause_file, encoding="utf-8") as fh:
        clause = fh.read()
    with open(a.extraction_file, encoding="utf-8") as fh:
        extraction = json.load(fh)
    cleaned, dropped, invented = validate(clause, extraction)
    print(json.dumps({"cleaned": cleaned, "dropped": dropped, "invented_citations": invented},
                     ensure_ascii=False, indent=2))
    return 1 if a.strict and dropped else 0


if __name__ == "__main__":
    sys.exit(main())
