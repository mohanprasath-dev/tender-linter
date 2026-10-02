from pathlib import Path

import yaml
from fastapi.testclient import TestClient

# Import FastAPI app from apps.api.main
from apps.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "database" in data


def test_health_alias_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_version_endpoint() -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()

    # Read expected rule_set version directly from packages/rules/rules.yaml
    rules_path = Path(__file__).resolve().parent.parent / "packages" / "rules" / "rules.yaml"
    with open(rules_path, encoding="utf-8") as f:
        rules_data = yaml.safe_load(f)
    expected_rule_set_version = rules_data.get("rule_set_version")

    assert data.get("app") is not None
    assert data.get("rule_set") == expected_rule_set_version
    assert data.get("model") is None
    assert data.get("prompt") is None


def test_database_config_sqlite() -> None:
    from apps.api.core.config import Settings

    settings = Settings(DATABASE_URL="sqlite:///./test.sqlite")
    assert settings.DATABASE_URL.startswith("sqlite")


def test_database_config_postgres() -> None:
    from apps.api.core.config import Settings

    settings = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/tender_db")
    assert settings.DATABASE_URL.startswith("postgresql")
