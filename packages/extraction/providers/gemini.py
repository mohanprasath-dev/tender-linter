from __future__ import annotations

import json
import os
from typing import Any

import httpx

from packages.extraction.schema import ExtractionData


class GeminiExtractor:
    """Google Gemini API extraction adapter with structured JSON output."""

    def __init__(
        self,
        name: str = "GoogleGemini",
        model_id: str = "gemini-1.5-flash",
        api_key: str | None = None,
        timeout_sec: float = 30.0,
    ) -> None:
        self.name = name
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.timeout_sec = timeout_sec

    def extract(self, clause: str, language_hint: str | None = None) -> ExtractionData:
        if not self.api_key:
            raise ValueError(f"{self.name} API key not found in environment (GEMINI_API_KEY).")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.api_key}"

        system_instruction = (
            "You extract structured data from one tender clause. Output JSON only matching the schema. "
            "Never invent or correct IS numbers, parts, or years. "
            "Output character spans that are exact substrings of the clause."
        )

        prompt = f"Clause text:\n{clause}"
        if language_hint:
            prompt += f"\nLanguage hint: {language_hint}"

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        with httpx.Client(timeout=self.timeout_sec) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            res_json = resp.json()

        try:
            candidate_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(candidate_text)
            parsed["clause_id"] = parsed.get("clause_id", "c1")
            return ExtractionData.model_validate(parsed)
        except Exception as e:
            raise ValueError(f"Failed to parse structured output from Gemini: {e}") from e
