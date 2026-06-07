"""
Pipeline Orchestrator

Wires stages 1–5 together for the real (Tavily) search path.
Called by TavilySearchProvider.search_company().
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from pipeline.stage1_discovery import build_discovery_plan
from pipeline.stage2_fetch import fetch_pages
from pipeline.stage3_extract import (
    extract_careers_site_signals,
    extract_glassdoor_signals,
    extract_job_signals,
    extract_linkedin_signals,
    extract_news_signals,
    extract_review_signals,
)
from pipeline.stage4_bundle import assemble_bundle
from models.evidence import EvidenceBundle, Signal


def _apex_domain(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        parts = parsed.netloc.lower().removeprefix("www.").split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
    except Exception:
        pass
    return None


def _infer_domain(company_name: str, search_results: list[dict]) -> str | None:
    """
    Try to infer the company's official domain from top search results.
    Prefer results that don't look like job boards / review sites.
    """
    JOB_BOARDS = {"linkedin.com", "glassdoor.com", "indeed.com", "greenhouse.io",
                  "lever.co", "myworkdayjobs.com", "taleo.net", "icims.com"}
    for r in search_results:
        dom = _apex_domain(r.get("url", ""))
        if dom and dom not in JOB_BOARDS:
            slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
            if slug[:4] in dom:
                return dom
    return None


def run_pipeline(company_name: str, tavily_client) -> EvidenceBundle:
    """
    Full 5-stage pipeline.
    tavily_client: an initialized TavilyClient instance.
    """
    plan = build_discovery_plan(company_name)
    all_signals: list[Signal] = []
    all_serp_results: dict[str, list[dict]] = {}  # source_type -> results

    # ── Stage 1 + partial Stage 2 (search) ───────────────────────────────────
    job_urls: list[str] = []
    urls_to_fetch: list[str] = []
    domain: str | None = None

    # Run all discovery queries concurrently — they're independent network calls.
    def _run_query(query) -> list[dict]:
        kwargs = {
            "query": query.query,
            "max_results": query.max_results,
            "include_answer": False,
        }
        # Recency: news queries are limited to the last N days via Tavily's news topic.
        if getattr(query, "topic", "general") == "news":
            kwargs["topic"] = "news"
            if getattr(query, "days", None):
                kwargs["days"] = query.days
        try:
            results = tavily_client.search(**kwargs)
            return results.get("results", [])
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=min(8, len(plan.queries) or 1)) as ex:
        query_items = list(ex.map(_run_query, plan.queries))

    # Process results in plan order so downstream behavior stays deterministic.
    for query, items in zip(plan.queries, query_items):
        all_serp_results.setdefault(query.source_type, []).extend(items)

        for item in items:
            url = item.get("url", "")
            if not url:
                continue
            if query.source_type == "job_posting":
                job_urls.append(url)
                urls_to_fetch.append(url)
            elif query.source_type == "careers_site":
                urls_to_fetch.append(url)
                if domain is None:
                    domain = _infer_domain(company_name, items)
            elif query.source_type == "news":
                urls_to_fetch.append(url)
            # linkedin / glassdoor / review: SERP snippets only, no direct fetch

    # ── Stage 2 (fetch) ───────────────────────────────────────────────────────
    # Deduplicate and cap
    unique_fetch = list(dict.fromkeys(urls_to_fetch))[:20]
    fetched_pages = fetch_pages(unique_fetch)
    successfully_fetched = [u for u, p in fetched_pages.items() if p.status == 200]

    # ── Stage 3 (extract) ─────────────────────────────────────────────────────
    # Job signals from fetched job posting pages
    job_texts = [
        (u, fetched_pages[u].body_text)
        for u in unique_fetch
        if u in fetched_pages and fetched_pages[u].status == 200
        and any(jb in u for jb in ["greenhouse", "lever", "workday", "taleo", "icims", "ashby", "jobvite"])
    ]
    ats_url_hit = next((u for u in job_urls if fetched_pages.get(u, None) and fetched_pages[u].status == 200), None)
    all_signals += extract_job_signals(job_texts, ats_url_hit)

    # Careers site signals
    for url, page in fetched_pages.items():
        if page.status == 200 and "careers" in url.lower():
            all_signals += extract_careers_site_signals(url, page.raw_html, page.body_text)

    # LinkedIn signals (SERP snippets — Tavily results only)
    all_signals += extract_linkedin_signals(all_serp_results.get("linkedin", []))

    # Glassdoor signals (SERP snippets — Tavily results only)
    all_signals += extract_glassdoor_signals(all_serp_results.get("glassdoor", []))

    # Indeed review signals (SERP snippets)
    all_signals += extract_review_signals(all_serp_results.get("review", []))

    # News signals (fetched pages)
    news_texts = [
        (u, fetched_pages[u].body_text)
        for u in unique_fetch
        if u in fetched_pages and fetched_pages[u].status == 200
        and any(kw in u.lower() for kw in ["news", "press", "blog", "announce", "release", "reuters", "techcrunch", "businessinsider"])
    ]
    all_signals += extract_news_signals(news_texts)

    # ── Stages 4 + 5 (bundle + coverage) ─────────────────────────────────────
    return assemble_bundle(
        company_name=company_name,
        domain=domain,
        all_signals=all_signals,
        fetched_urls=successfully_fetched,
        attempted_urls=unique_fetch,
        fetched_pages=fetched_pages,
        job_urls=job_urls,
    )
