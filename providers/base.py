from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return the model's text response (expected to be JSON)."""
        ...


def get_llm_provider(config) -> LLMProvider:
    if config.llm_provider == "ollama":
        from providers.ollama_provider import OllamaProvider
        return OllamaProvider(config.ollama_base_url, config.ollama_model)
    if config.llm_provider == "anthropic":
        from providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(config.anthropic_api_key)
    raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
