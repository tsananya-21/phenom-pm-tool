from __future__ import annotations

import json
import httpx

from providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        format_schema: dict | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 4096,
            },
        }
        # Structured outputs: when a JSON Schema is supplied, Ollama constrains
        # decoding to it. This is stronger than format:"json" (which lets small
        # models echo the input shape) — the model must emit exactly this schema.
        if format_schema is not None:
            payload["format"] = format_schema
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error {e.response.status_code}: {e.response.text}")
        except KeyError:
            raise RuntimeError("Unexpected Ollama response shape")
