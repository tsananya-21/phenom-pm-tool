from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        format_schema: dict | None = None,
    ) -> str:
        """
        Return the model's text response (expected to be JSON).

        format_schema: optional JSON Schema for providers that support structured
        outputs; providers that don't may ignore it.
        """
        ...


def get_llm_provider(config) -> LLMProvider:
    if config.llm_provider == "anthropic":
        from providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(config.anthropic_api_key)
    raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
