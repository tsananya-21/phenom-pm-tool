from __future__ import annotations

import json
import httpx

from providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, system_prompt: str, user_message: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            # Note: format:"json" is intentionally omitted — small models with JSON mode
            # tend to echo the input JSON rather than generate the output schema.
            # We rely on the tolerant parser in synthesizer.py to extract valid JSON instead.
            "options": {
                "temperature": 0.1,
                "num_predict": 4096,
            },
        }
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
