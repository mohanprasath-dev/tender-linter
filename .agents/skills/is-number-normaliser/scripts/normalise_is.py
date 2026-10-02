"""Parse and normalise Indian Standard citations. Deterministic, no model."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata

_DEV = {ord(c): str(i) for i, c in enumerate("०१२३४५६७८९")}
_PREFIX = r"(?:I\.?\s?S\.?|आई\.?\s?एस\.?)"
_CITE = re.compile(
    r"(?<![A-Za-z])(?P<prefix>" + _PREFIX + r")(?:\s*/\s*(?P<body>IEC|ISO))?"
    r"\s*[:.]?\s*(?P<num>\d{2,6}(?:\s*-\s*\d{1,4})*)"
    r"(?:\s*\(?\s*(?:(?i:Part)|भाग)\s*(?P<part>\d+)\s*\)?)?"
    r"(?:\s*[:/\-]\s*(?P<year>(?:19|20)\d{2})(?!\d))?"
)
_YEAR = re.compile(r"(?:19|20)\d{2}$")


def fold(text: str) -> str:
    """Normalise width and Devanagari digits without changing string length."""
    out = []
    for ch in text:
        n = unicodedata.normalize("NFKC", ch)
        out.append(n if len(n) == 1 else ch)
    return "".join(out).translate(_DEV)


def find_citations(text: str) -> list[dict]:
    folded = fold(text)
    found = []
    for m in _CITE.finditer(folded):
        groups = re.split(r"\s*-\s*", m.group("num").strip())
        year = int(m.group("year")) if m.group("year") else None
        if year is None and len(groups) > 1 and _YEAR.match(groups[-1]):
            year = int(groups.pop())
        body = m.group("body")
        prefix = "IS/" + body.upper() if body else "IS"
        found.append(
            {
                "raw": text[m.start():m.end()],
                "span": [m.start(), m.end()],
                "is_number": f"{prefix} {'-'.join(groups)}",
                "part": m.group("part"),
                "year": year,
            }
        )
    return found


def _edit1(a: str, b: str) -> bool:
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def suggest_near(is_number: str, known: list[str]) -> list[str]:
    """Known numbers exactly one edit away. Candidates only, never auto-applied."""
    return [k for k in known if _edit1(is_number, k)]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--suggest")
    p.add_argument("--known", nargs="*", default=[])
    a = p.parse_args()
    if a.suggest:
        print(json.dumps(suggest_near(a.suggest, a.known), ensure_ascii=False))
    else:
        print(json.dumps(find_citations(a.text), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
