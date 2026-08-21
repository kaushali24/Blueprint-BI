import json
from typing import Protocol, Any
from google import genai
from google.genai import types

from app.extraction.exceptions import ExtractionProviderError


class LLMProvider(Protocol):
    def extract(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Extract structured data using the LLM provider."""
        ...


class GeminiProvider:
    def __init__(self, api_key: str, model_name: str = "gemini-3.6-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def extract(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0,
                ),
            )
            # Response text should be JSON
            if not response.text:
                raise ExtractionProviderError("Empty response from Gemini")
            return json.loads(response.text)
        except Exception as e:
            raise ExtractionProviderError(f"Gemini extraction failed: {str(e)}") from e


class FakeLLMProvider:
    def __init__(self, response_dict: dict[str, Any] | None = None, should_raise: bool = False):
        self.response_dict = response_dict or {}
        self.should_raise = should_raise
        self.calls = []

    def extract(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, "schema": schema})
        if self.should_raise:
            raise ExtractionProviderError("Fake LLM Provider Error")
        return self.response_dict
