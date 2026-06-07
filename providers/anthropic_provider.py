"""
AnthropicProvider — production stub.

Wired but NOT called in dev (PHENOM_LLM_PROVIDER=ollama by default).
Set PHENOM_LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY to activate.

Prompt caching: the Phenom catalog block is a static, large system-prompt prefix —
ideal for Anthropic cache_control ephemeral blocks (5-min TTL, up to 90% cost
reduction on repeated calls). See the TODO comment in generate() below.
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

    def generate(self, system_prompt: str, user_message: str) -> str:
        # TODO: split system_prompt into [catalog_block (cacheable), instruction_block]
        # and annotate catalog_block with cache_control={"type": "ephemeral"} to
        # activate Anthropic prompt caching. Saves ~70-90% on repeated calls.
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return msg.content[0].text
