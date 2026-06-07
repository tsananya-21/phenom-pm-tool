from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env explicitly (parent of this config/ dir) so it's found
# regardless of the process's working directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Config:
    llm_provider: str        # "anthropic"
    search_provider: str     # "tavily"
    anthropic_api_key: str
    tavily_api_key: str


def load_config() -> Config:
    llm = os.getenv("PHENOM_LLM_PROVIDER", "anthropic")
    search = os.getenv("PHENOM_SEARCH_PROVIDER", "tavily")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    if llm == "anthropic" and not anthropic_key:
        raise ValueError("PHENOM_LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set")
    if search == "tavily" and not tavily_key:
        raise ValueError("PHENOM_SEARCH_PROVIDER=tavily requires TAVILY_API_KEY to be set")

    return Config(
        llm_provider=llm,
        search_provider=search,
        anthropic_api_key=anthropic_key,
        tavily_api_key=tavily_key,
    )
