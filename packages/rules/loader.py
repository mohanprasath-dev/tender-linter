from __future__ import annotations

from pathlib import Path

import yaml

from packages.rules.schema import RuleCatalog

DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "rules.yaml"


def load_rules_from_yaml(path: Path | str | None = None) -> RuleCatalog:
    file_path = Path(path) if path else DEFAULT_RULES_PATH
    if not file_path.exists():
        raise FileNotFoundError(f"Rules YAML not found at: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return RuleCatalog.model_validate(data)
