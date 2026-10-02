from pathlib import Path

import yaml
from fastapi import APIRouter

from apps.api.core.config import settings
from apps.api.schemas.version import VersionResponse

router = APIRouter()


def get_rule_set_version() -> str | None:
    """Read rule set version directly from packages/rules/rules.yaml."""
    rules_file = settings.BASE_DIR / "packages" / "rules" / "rules.yaml"
    if not rules_file.exists():
        # Fallback to local package path if base directory differs
        rules_file = Path("packages/rules/rules.yaml")

    if rules_file.exists():
        try:
            with open(rules_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    return data.get("rule_set_version")
        except Exception:
            return None
    return None


@router.get("/version", response_model=VersionResponse)
def get_version() -> VersionResponse:
    """Return version details for app, rule set, model, and prompt."""
    return VersionResponse(
        app=settings.APP_VERSION,
        rule_set=get_rule_set_version(),
        model=None,
        prompt=None,
    )
