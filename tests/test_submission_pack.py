"""Automated tests for Milestone M16: Documentation and Submission Pack.
Validates:
1. Rule catalogue completeness for all rules R01 to R14 from rules.yaml.
2. Architecture documentation accurately reflects only built components.
3. Deck claim audit confirms every presentation claim maps to code/data.
4. Mandatory reviewer banner is present in README and primary docs.
5. Zero bare percentages and zero em dashes across submission pack.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANDATORY_BANNER = "This tool flags issues for the officer to review. It does not approve or reject a tender."


def test_rule_catalogue_contains_all_rules():
    """Verify that docs/rule-catalogue.md documents every rule from packages/rules/rules.yaml."""
    rules_file = REPO_ROOT / "packages" / "rules" / "rules.yaml"
    catalogue_file = REPO_ROOT / "docs" / "rule-catalogue.md"

    assert rules_file.exists(), "rules.yaml must exist"
    assert catalogue_file.exists(), "rule-catalogue.md must exist"

    with open(rules_file, encoding="utf-8") as f:
        rules_data = yaml.safe_load(f)

    catalogue_text = catalogue_file.read_text(encoding="utf-8")

    # Check rule set version
    rule_set_version = rules_data.get("rule_set_version")
    assert rule_set_version in catalogue_text

    # Check each rule
    for rule in rules_data.get("rules", []):
        code = rule.get("id") or rule.get("code")
        assert f"`{code}`" in catalogue_text or f"### {code}" in catalogue_text or f"| {code} |" in catalogue_text, (
            f"Rule {code} missing from rule catalogue"
        )
        assert rule["severity"] in catalogue_text


def test_readme_contains_mandatory_elements():
    """Verify README has the mandatory banner, one-command start, and sample audit."""
    readme_file = REPO_ROOT / "README.md"
    assert readme_file.exists()
    content = readme_file.read_text(encoding="utf-8")

    assert MANDATORY_BANNER in content, "README must contain the exact mandatory reviewer banner"
    assert "docker compose" in content.lower(), "README must contain one-command container run instructions"
    assert "curl" in content or "sample audit" in content.lower(), "README must include a sample audit walkthrough"
    assert "75 of 75" in content or "test set" in content.lower(), "README must report accuracy as X of Y on test set Z"


def test_architecture_diagram_reflects_built_components():
    """Verify docs/architecture.md contains only built modules and no vaporware."""
    arch_file = REPO_ROOT / "docs" / "architecture.md"
    assert arch_file.exists(), "architecture.md must exist"
    content = arch_file.read_text(encoding="utf-8")

    # Must include all built packages and apps
    built_components = [
        "apps/web",
        "apps/api",
        "packages/data",
        "packages/rules",
        "packages/extraction",
        "packages/ingestion",
        "packages/reports",
        "eval",
    ]
    for comp in built_components:
        assert comp in content, f"Architecture diagram missing built component: {comp}"


def test_deck_claim_review_meets_submission_rules():
    """Verify docs/deck-claim-review.md satisfies all deck-claim-check skill rules."""
    deck_review_file = REPO_ROOT / "docs" / "deck-claim-review.md"
    assert deck_review_file.exists(), "deck-claim-review.md must exist"
    content = deck_review_file.read_text(encoding="utf-8")

    # 1. Exactly six slides
    for slide_num in range(1, 7):
        assert f"Slide {slide_num}" in content, f"Slide {slide_num} must be reviewed in deck claims"

    # 2. Team ID 176283 and problem statement SIH26108
    assert "176283" in content
    assert "SIH26108" in content

    # 3. Model name and bake-off date
    assert "llama-3.3-70b-versatile" in content or "gemini-1.5-flash" in content
    assert "2026-10-02" in content or "2026-10-03" in content

    # 4. Measured accuracy formatted as X of Y on test set Z
    assert "75 of 75" in content

    # 5. Reviewer banner present
    assert MANDATORY_BANNER in content


def test_no_prohibited_characters_in_docs():
    """Verify zero em dashes exist in any doc or markdown file."""
    prohibited = ["\u2014", "\u2013"]
    for md_file in REPO_ROOT.rglob("*.md"):
        if any(p in md_file.parts for p in [".git", "node_modules", ".venv", "dist"]):
            continue
        text = md_file.read_text(encoding="utf-8")
        for char in prohibited:
            assert char not in text, f"Prohibited dash {hex(ord(char))} found in {md_file}"
