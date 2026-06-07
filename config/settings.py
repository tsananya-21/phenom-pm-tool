from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    llm_provider: str        # "ollama" | "anthropic"
    search_provider: str     # "mock" | "tavily"
    ollama_base_url: str
    ollama_model: str
    anthropic_api_key: str
    tavily_api_key: str


def load_config() -> Config:
    llm = os.getenv("PHENOM_LLM_PROVIDER", "ollama")
    search = os.getenv("PHENOM_SEARCH_PROVIDER", "mock")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    if llm == "anthropic" and not anthropic_key:
        raise ValueError("PHENOM_LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set")
    if search == "tavily" and not tavily_key:
        raise ValueError("PHENOM_SEARCH_PROVIDER=tavily requires TAVILY_API_KEY to be set")

    return Config(
        llm_provider=llm,
        search_provider=search,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:latest"),
        anthropic_api_key=anthropic_key,
        tavily_api_key=tavily_key,
    )
