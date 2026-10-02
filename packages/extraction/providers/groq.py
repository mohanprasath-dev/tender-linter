from __future__ import annotations

import json
import os
from typing import Any

import httpx

from packages.extraction.schema import ExtractionData


class GroqExtractor:
    """Groq API extraction adapter with structured JSON output."""

    def __init__(
        self,
        name: str = "Groq",
        model_id: str = "llama-3.3-70b-versatile",
        api_key: str | None = None,
        timeout_sec: float = 30.0,
    ) -> None:
        self.name = name
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.timeout_sec = timeout_sec

    def extract(self, clause: str, language_hint: str | None = None) -> ExtractionData:
        if not self.api_key:
            raise ValueError(f"{self.name} API key not found in environment (GROQ_API_KEY).")

        url = "https://api.groq.com/openai/v1/chat/completions"

        system_instruction = (
            "You extract structured data from one tender clause. Output JSON only matching the schema. "
            "Never invent or correct IS numbers, parts, or years. "
            "Output character spans that are exact substrings of the clause."
        )

        user_content = f"Clause text:\n{clause}"
        if language_hint:
            user_content += f"\nLanguage hint: {language_hint}"

        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_sec) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            res_json = resp.json()

        try:
            content = res_json["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            parsed["clause_id"] = parsed.get("clause_id", "c1")
            return ExtractionData.model_validate(parsed)
        except Exception as e:
            raise ValueError(f"Failed to parse structured output from Groq: {e}") from e
