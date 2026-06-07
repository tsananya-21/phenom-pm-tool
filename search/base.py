from __future__ import annotations

from abc import ABC, abstractmethod

from models.evidence import EvidenceBundle


class SearchProvider(ABC):
    @abstractmethod
    def search_company(self, company_name: str) -> EvidenceBundle:
        """Run the full research pipeline for a company name."""
        ...


def get_search_provider(config) -> SearchProvider:
    if config.search_provider == "mock":
        from search.mock_search import MockSearchProvider
        return MockSearchProvider()
    if config.search_provider == "tavily":
        from search.tavily_search import TavilySearchProvider
        return TavilySearchProvider(config.tavily_api_key)
    raise ValueError(f"Unknown search provider: {config.search_provider}")
