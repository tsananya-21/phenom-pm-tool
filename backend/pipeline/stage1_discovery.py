"""
Stage 1 — Source Discovery

Given a company name, build the list of search queries and target URLs
for each source type. All queries go through the SearchProvider abstraction.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field

# Only consider time-sensitive evidence (news) from roughly the last 6 months.
RECENT_DAYS = 180


@dataclass
class SearchQuery:
    query: str
    source_type: str   # job_posting | careers_site | linkedin | glassdoor | review | news | filing
    max_results: int = 5
    topic: str = "general"      # "general" | "news"
    days: int | None = None     # recency window in days; applied when topic == "news"


@dataclass
class DiscoveryPlan:
    company_name: str
    queries: list[SearchQuery] = field(default_factory=list)


def build_discovery_plan(company_name: str) -> DiscoveryPlan:
    n = company_name.strip()
    plan = DiscoveryPlan(company_name=n)

    # Domain + careers page
    plan.queries += [
        SearchQuery(f'"{n}" official website careers jobs', "careers_site", max_results=3),
        SearchQuery(f'"{n}" site:myworkdayjobs.com OR site:boards.greenhouse.io OR site:jobs.lever.co OR site:icims.com OR site:ashbyhq.com OR site:taleo.net OR site:smartrecruiters.com', "job_posting", max_results=10),
        SearchQuery(f'"{n}" careers jobs apply', "job_posting", max_results=5),
    ]

    # LinkedIn via Tavily (no LinkedIn API — see compliance notes)
    plan.queries += [
        SearchQuery(f'site:linkedin.com/company "{n}"', "linkedin", max_results=3),
        SearchQuery(f'site:linkedin.com/jobs/view "{n}"', "linkedin", max_results=5),
    ]

    # Glassdoor via Tavily (SERP snippets only — no direct glassdoor.com fetch)
    plan.queries += [
        SearchQuery(f'site:glassdoor.com/Reviews "{n}" reviews rating', "glassdoor", max_results=3),
        SearchQuery(f'site:glassdoor.com/Interview "{n}" interview experience', "glassdoor", max_results=3),
    ]

    # Indeed reviews (SERP snippets only)
    plan.queries.append(
        SearchQuery(f'site:indeed.com/cmp "{n}" reviews', "review", max_results=3)
    )

    # News — restricted to roughly the last 6 months (recent signals only)
    recent_cutoff = (datetime.date.today() - datetime.timedelta(days=RECENT_DAYS)).isoformat()
    plan.queries.append(
        SearchQuery(
            f'"{n}" (CHRO OR CPO OR "Chief People Officer" OR layoffs OR hiring OR expansion OR funding) after:{recent_cutoff}',
            "news",
            max_results=5,
            topic="news",
            days=RECENT_DAYS,
        )
    )

    # SEC filings (skip for most; add conditionally)
    plan.queries.append(
        SearchQuery(f'"{n}" 10-K "talent" OR "headcount" site:sec.gov', "filing", max_results=3)
    )

    return plan
