from pydantic import BaseModel


class VersionResponse(BaseModel):
    """Version response schema returning app, rule_set, model, and prompt versions."""

    app: str
    rule_set: str | None
    model: str | None = None
    prompt: str | None = None
