from pydantic import BaseModel


class VersionResponse(BaseModel):
    """Version response schema returning app, rule_set, model, prompt, and data_snapshot versions."""

    app: str
    rule_set: str | None
    model: str | None = None
    prompt: str | None = None
    data_snapshot: str | None = None
