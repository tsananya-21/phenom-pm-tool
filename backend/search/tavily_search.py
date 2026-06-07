"""
TavilySearchProvider — real search pipeline using the Tavily API.
Activated by: PHENOM_SEARCH_PROVIDER=tavily + TAVILY_API_KEY=<key>
"""
from __future__ import annotations

from models.evidence import EvidenceBundle
from search.base import SearchProvider


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required for TavilySearchProvider")
        try:
            from tavily import TavilyClient
        except ImportError:
            raise ImportError("Install tavily-python: pip install tavily-python")
        self._client = TavilyClient(api_key=api_key)

    def search_company(self, company_name: str) -> EvidenceBundle:
        from pipeline.orchestrator import run_pipeline
        return run_pipeline(company_name, self._client)
