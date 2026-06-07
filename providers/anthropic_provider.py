"""
AnthropicProvider.

Set PHENOM_LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY to activate.

Latency / cost optimizations applied in generate():
  - Prompt caching: the system prompt (static Phenom catalog + instructions) is
    sent as a cache_control ephemeral block, so repeated searches within the
    5-min TTL skip re-processing it (~90% cheaper, lower latency on the prefix).
  - Streaming: the response is streamed and reassembled via get_final_message(),
    which avoids the SDK's non-streaming timeout guard on long generations.

Note: format_schema is accepted for interface parity but not sent as
output_config.format — that API requires a newer anthropic SDK than is pinned,
and Claude already adheres to the schema described in the system prompt (the
synthesizer's tolerant parser handles the result). Upgrade the SDK and add
output_config={"format": {"type": "json_schema", "schema": format_schema}} if a
hard schema guarantee is later required.
"""
from __future__ import annotations

from providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicProvider")
        self._api_key = api_key
        self._model = model
        # Lazy import so anthropic package is not required in dev
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        format_schema: dict | None = None,
    ) -> str:
        kwargs: dict = {
            "model": self._model,
            # The full analysis JSON runs ~4,150 tokens; a 4096 cap truncated it,
            # producing invalid JSON that forced a second full generation (~2x time).
            # Headroom lets it finish in one streamed pass.
            "max_tokens": 8192,
            # Cache the static system prefix (catalog + instructions) for repeat calls.
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user_message}],
        }

        with self._client.messages.stream(**kwargs) as stream:
            msg = stream.get_final_message()

        return next((b.text for b in msg.content if b.type == "text"), "")
