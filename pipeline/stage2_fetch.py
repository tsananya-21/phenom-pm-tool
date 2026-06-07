"""
Stage 2 — Targeted Fetch

Fetches HTML for discovered careers/job/news page URLs.
- robots.txt check before each fetch (cached per domain)
- Rate limit: 1 req/2s per domain
- trafilatura for main-content extraction; BS4 fallback
- Max 20 pages total per company run

LinkedIn and Glassdoor domain URLs are explicitly skipped here —
those signals come from Tavily SERP snippets only (see compliance notes).
"""
from __future__ import annotations

import time
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from typing import Optional

import httpx

try:
    import trafilatura
    _HAS_TRAFILATURA = True
except ImportError:
    _HAS_TRAFILATURA = False

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False

# Domains we never fetch directly (ToS / robots.txt boundary)
_BLOCKED_DOMAINS = frozenset({
    "linkedin.com",
    "glassdoor.com",
    "indeed.com",
    "facebook.com",
    "twitter.com",
    "x.com",
})

_ROBOTS_CACHE: dict[str, RobotFileParser] = {}
_DOMAIN_LAST_FETCH: dict[str, float] = {}
_RATE_LIMIT_SECS = 2.0
_MAX_PAGES = 20

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 research-tool/1.0"


@dataclass
class ParsedPage:
    url: str
    title: str
    body_text: str
    raw_html: str
    status: int
    fetch_error: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _is_blocked(url: str) -> bool:
    dom = _domain(url)
    return any(dom == b or dom.endswith("." + b) for b in _BLOCKED_DOMAINS)


def _robots_allowed(url: str, client: httpx.Client) -> bool:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base}/robots.txt"
    dom = _domain(url)

    if dom not in _ROBOTS_CACHE:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            resp = client.get(robots_url, timeout=5.0)
            rp.parse(resp.text.splitlines())
        except Exception:
            # If we can't fetch robots.txt, default to allowed
            rp.allow_all = True
        _ROBOTS_CACHE[dom] = rp

    return _ROBOTS_CACHE[dom].can_fetch(UA, url)


def _rate_limit(url: str) -> None:
    dom = _domain(url)
    last = _DOMAIN_LAST_FETCH.get(dom, 0)
    elapsed = time.time() - last
    if elapsed < _RATE_LIMIT_SECS:
        time.sleep(_RATE_LIMIT_SECS - elapsed)
    _DOMAIN_LAST_FETCH[dom] = time.time()


def _extract_text(html: str, url: str) -> tuple[str, str]:
    """Returns (title, body_text)."""
    title = ""
    # Try title tag
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if t:
        title = re.sub(r"\s+", " ", t.group(1)).strip()

    body = ""
    if _HAS_TRAFILATURA:
        body = trafilatura.extract(html, url=url, include_comments=False, include_tables=False) or ""

    if not body and _HAS_BS4:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        body = soup.get_text(separator=" ", strip=True)

    # Truncate to 8k chars — enough signal, keeps memory reasonable
    return title, body[:8000]


def fetch_pages(urls: list[str]) -> dict[str, ParsedPage]:
    """Fetch and parse a list of URLs. Respects robots.txt and rate limits."""
    results: dict[str, ParsedPage] = {}
    fetched_count = 0

    with httpx.Client(headers={"User-Agent": UA}, follow_redirects=True, timeout=15.0) as client:
        for url in urls:
            if fetched_count >= _MAX_PAGES:
                break
            if _is_blocked(url):
                results[url] = ParsedPage(
                    url=url, title="", body_text="", raw_html="",
                    status=0, fetch_error="Domain blocked (ToS boundary)",
                )
                continue

            if not _robots_allowed(url, client):
                results[url] = ParsedPage(
                    url=url, title="", body_text="", raw_html="",
                    status=0, fetch_error="robots.txt disallows",
                )
                continue

            _rate_limit(url)

            try:
                resp = client.get(url)
                html = resp.text
                title, body = _extract_text(html, url)
                results[url] = ParsedPage(
                    url=url,
                    title=title,
                    body_text=body,
                    raw_html=html[:50000],  # keep first 50k for ATS markup pass
                    status=resp.status_code,
                )
                fetched_count += 1
            except httpx.TimeoutException:
                results[url] = ParsedPage(
                    url=url, title="", body_text="", raw_html="",
                    status=0, fetch_error="Timeout",
                )
            except Exception as e:
                results[url] = ParsedPage(
                    url=url, title="", body_text="", raw_html="",
                    status=0, fetch_error=str(e)[:200],
                )

    return results
