"""
Offline mock search provider. Returns rich, realistic EvidenceBundle objects
for 4 golden companies without any API calls. Default when no env vars are set.

Fuzzy match: case-insensitive substring on company name.
"""
from __future__ import annotations

from datetime import datetime, timezone

from models.evidence import (
    ATSDetection,
    CoverageScore,
    Dimension,
    EvidenceBundle,
    Signal,
)
from search.base import SearchProvider

_NOW = datetime.now(timezone.utc).isoformat()


def _score(signals: list[Signal], dim: Dimension) -> CoverageScore:
    dim_signals = [s for s in signals if s.dimension == dim]
    if not dim_signals:
        return CoverageScore(
            dimension=dim,
            score=0.0,
            signal_count=0,
            is_thin=True,
            thin_reason="No signals found for this dimension",
        )
    raw = sum(s.confidence for s in dim_signals)
    score = min(raw / 3.0, 1.0)
    return CoverageScore(
        dimension=dim,
        score=round(score, 2),
        signal_count=len(dim_signals),
        is_thin=score < 0.3,
        thin_reason=None if score >= 0.3 else "Fewer than 2 low-confidence signals",
    )


def _coverage(signals: list[Signal]) -> list[CoverageScore]:
    return [_score(signals, d) for d in Dimension]


# ---------------------------------------------------------------------------
# Company A — HubSpot
# ---------------------------------------------------------------------------
def _hubspot() -> EvidenceBundle:
    signals = [
        # HRIT
        Signal(
            source_url="https://boards.greenhouse.io/hubspot",
            source_type="job_posting",
            dimension=Dimension.HRIT,
            signal_type="ats_detection",
            content="HubSpot uses Greenhouse ATS; apply URLs route through boards.greenhouse.io/hubspot",
            raw_snippet="boards.greenhouse.io/hubspot — Apply for jobs at HubSpot",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://boards.greenhouse.io/hubspot",
            source_type="job_posting",
            dimension=Dimension.HRIT,
            signal_type="ta_team_investment",
            content="3 open Talent Acquisition / Recruiting roles signal active TA team build-out",
            raw_snippet="Senior Technical Recruiter · Recruiting Coordinator · Head of University Recruiting",
            confidence=0.8,
            extracted_at=_NOW,
        ),
        # HIRING
        Signal(
            source_url="https://boards.greenhouse.io/hubspot",
            source_type="job_posting",
            dimension=Dimension.HIRING,
            signal_type="hiring_volume",
            content="80+ open roles across Engineering (42), Sales (22), Marketing (10), G&A (8)",
            raw_snippet="82 open positions · Engineering: 42 · Sales: 22 · Marketing: 10",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://boards.greenhouse.io/hubspot",
            source_type="job_posting",
            dimension=Dimension.HIRING,
            signal_type="pay_transparency",
            content="Salary bands included on ~60% of US postings; no pay data on international roles",
            raw_snippet="Base salary: $130,000 – $165,000 USD · plus equity and bonus",
            confidence=0.7,
            extracted_at=_NOW,
        ),
        # ONBOARDING
        Signal(
            source_url="https://www.hubspot.com/careers",
            source_type="careers_site",
            dimension=Dimension.ONBOARDING,
            signal_type="careers_site_maturity",
            content="Careers site has role search and basic filtering but no chatbot, no talent community signup, no personalized recommendations",
            raw_snippet="Join our team · Search open roles · Filter by team, location, remote",
            confidence=0.65,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://www.glassdoor.com/Reviews/HubSpot-Reviews-E227137.htm",
            source_type="glassdoor",
            dimension=Dimension.ONBOARDING,
            signal_type="onboarding_sentiment",
            content="Glassdoor reviewers cite strong culture but consistently flag slow onboarding ramp as a weakness",
            raw_snippet="4.2 ★ · Pros: great culture, smart people · Cons: slow onboarding ramp, unclear first-90-days structure",
            confidence=0.6,
            extracted_at=_NOW,
        ),
        # RETENTION
        Signal(
            source_url="https://www.glassdoor.com/Reviews/HubSpot-Reviews-E227137.htm",
            source_type="glassdoor",
            dimension=Dimension.RETENTION,
            signal_type="glassdoor_rating",
            content="HubSpot Glassdoor: 4.2★, 89% recommend, 92% CEO approval — strong retention sentiment overall",
            raw_snippet="4.2 ★ · 89% recommend to a friend · CEO Yamini Rangan 92% approval",
            confidence=0.75,
            extracted_at=_NOW,
        ),
        # PEOPLE_ANALYTICS
        Signal(
            source_url="https://boards.greenhouse.io/hubspot",
            source_type="job_posting",
            dimension=Dimension.PEOPLE_ANALYTICS,
            signal_type="people_analytics_roles",
            content="No open People Analytics or Workforce Intelligence roles found — analytics maturity unclear",
            raw_snippet="0 results for 'people analytics' OR 'workforce analytics' in open roles",
            confidence=0.35,
            extracted_at=_NOW,
        ),
        # INTERNAL_MOBILITY
        Signal(
            source_url="https://www.hubspot.com/careers",
            source_type="careers_site",
            dimension=Dimension.INTERNAL_MOBILITY,
            signal_type="internal_mobility_program",
            content="No public mention of internal mobility program or internal job board on careers site",
            raw_snippet="careers.hubspot.com — no internal mobility or career path content found",
            confidence=0.25,
            extracted_at=_NOW,
        ),
        # NEWS — Leadership
        Signal(
            source_url="https://www.prnewswire.com/news-releases/hubspot-appoints-new-chief-people-officer-2024",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="chro_change",
            content="HubSpot appointed a new Chief People Officer in Q2 2024 — strong transformation-appetite signal",
            raw_snippet="HubSpot today announced the appointment of [CPO name] as Chief People Officer, effective Q2 2024",
            confidence=0.9,
            extracted_at=_NOW,
        ),
        # NEWS — AI strategy
        Signal(
            source_url="https://www.hubspot.com/products/artificial-intelligence",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="ai_strategy",
            content="HubSpot launched Breeze AI in 2024 — AI agents embedded across CRM, marketing, and sales products; CEO Yamini Rangan called AI 'the biggest platform shift since mobile'",
            raw_snippet="Breeze AI: Copilot + AI Agents + Intelligence layer across HubSpot platform",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://ir.hubspot.com/news-releases/news-release-details/hubspot-announces-fourth-quarter-and-full-year-2024-results",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="ai_strategy",
            content="CEO stated: 'AI is fundamentally changing how businesses grow — and HubSpot is positioned to be the AI-powered platform for SMBs'",
            raw_snippet="CEO Yamini Rangan, Q4 2024 earnings call: AI-powered platform for SMBs, Breeze AI adoption accelerating",
            confidence=0.8,
            extracted_at=_NOW,
        ),
        # FILING — Financial
        Signal(
            source_url="https://ir.hubspot.com/news-releases/news-release-details/hubspot-announces-fourth-quarter-and-full-year-2024-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="HubSpot Q4 2024 revenue: $693M (+21% YoY); Full-year 2024 revenue: $2.63B (+21% YoY)",
            raw_snippet="Q4 2024: Revenue $693.0M, +21% YoY · FY2024 Total Revenue: $2.63B",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://ir.hubspot.com/news-releases/news-release-details/hubspot-announces-first-quarter-2024-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="HubSpot quarterly revenue trend: Q1 2024 $617M → Q2 2024 $651M → Q3 2024 $670M → Q4 2024 $693M",
            raw_snippet="Q1: $617M · Q2: $651M · Q3: $670M · Q4: $693M",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        # HIRING — LinkedIn
        Signal(
            source_url="https://www.linkedin.com/company/hubspot",
            source_type="linkedin",
            dimension=Dimension.HIRING,
            signal_type="employee_count",
            content="LinkedIn lists HubSpot at 7,001–10,000 employees with 210,000+ followers",
            raw_snippet="HubSpot · 7,001–10,000 employees · Software Development · 210,847 followers",
            confidence=0.5,
            extracted_at=_NOW,
        ),
    ]
    return EvidenceBundle(
        company_name="HubSpot",
        domain="hubspot.com",
        sources_attempted=[
            "https://www.hubspot.com/careers",
            "https://boards.greenhouse.io/hubspot",
            "https://www.glassdoor.com/Reviews/HubSpot-Reviews-E227137.htm",
            "https://www.linkedin.com/company/hubspot",
            "https://ir.hubspot.com/news-releases",
        ],
        sources_fetched=[
            "https://www.hubspot.com/careers",
            "https://boards.greenhouse.io/hubspot",
            "https://ir.hubspot.com/news-releases",
        ],
        signals=signals,
        ats=ATSDetection(
            ats_name="Greenhouse",
            evidence_url="https://boards.greenhouse.io/hubspot",
            detection_method="apply_url",
            confidence=0.95,
        ),
        coverage=_coverage(signals),
        is_mock=True,
        fetched_at=_NOW,
    )


# ---------------------------------------------------------------------------
# Company B — ServiceNow
# ---------------------------------------------------------------------------
def _servicenow() -> EvidenceBundle:
    signals = [
        # HRIT
        Signal(
            source_url="https://servicenow.wd5.myworkdayjobs.com/External",
            source_type="job_posting",
            dimension=Dimension.HRIT,
            signal_type="ats_detection",
            content="ServiceNow uses Workday ATS; apply URLs route through servicenow.wd5.myworkdayjobs.com",
            raw_snippet="servicenow.wd5.myworkdayjobs.com/External — ServiceNow careers powered by Workday",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        # HIRING
        Signal(
            source_url="https://servicenow.wd5.myworkdayjobs.com/External",
            source_type="job_posting",
            dimension=Dimension.HIRING,
            signal_type="hiring_volume",
            content="200+ open roles globally; heavy in Platform Engineering (68), Enterprise Sales (45), Solution Consulting (28)",
            raw_snippet="213 open positions · Platform Engineering: 68 · Sales: 45 · Solution Consulting: 28 · People: 12",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://www.glassdoor.com/Interview/ServiceNow-Interview-Questions-E403249.htm",
            source_type="glassdoor",
            dimension=Dimension.HIRING,
            signal_type="interview_experience",
            content="Interview process rated 'Difficult' with only 67% positive experience — candidate drop-off risk; average process takes 4–6 weeks",
            raw_snippet="Difficulty: 3.4/5 · 67% positive experience · Average interview takes 4–6 weeks · Cons: process is long and unclear",
            confidence=0.65,
            extracted_at=_NOW,
        ),
        # PEOPLE_ANALYTICS
        Signal(
            source_url="https://servicenow.wd5.myworkdayjobs.com/External",
            source_type="job_posting",
            dimension=Dimension.PEOPLE_ANALYTICS,
            signal_type="ta_team_investment",
            content="12 open HR/People roles including Sr. People Analyst and Workforce Analytics Manager — high analytics maturity signal",
            raw_snippet="Sr. People Analyst · Workforce Analytics Manager · People Business Partner (APAC) · Talent Intelligence Lead",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        # ONBOARDING
        Signal(
            source_url="https://www.servicenow.com/careers.html",
            source_type="careers_site",
            dimension=Dimension.ONBOARDING,
            signal_type="careers_site_maturity",
            content="Careers site has role-based filtering, some personalization via source tracking, but no chatbot or talent community signup visible",
            raw_snippet="servicenow.com/careers · Find your next role · Filter by location, team, level · No chatbot widget detected",
            confidence=0.6,
            extracted_at=_NOW,
        ),
        # RETENTION
        Signal(
            source_url="https://www.glassdoor.com/Reviews/ServiceNow-Reviews-E403249.htm",
            source_type="glassdoor",
            dimension=Dimension.RETENTION,
            signal_type="glassdoor_rating",
            content="ServiceNow Glassdoor: 4.1★, 84% recommend, 78% CEO approval",
            raw_snippet="4.1 ★ · 84% recommend to a friend · CEO Bill McDermott 78% approval · 3,200+ reviews",
            confidence=0.75,
            extracted_at=_NOW,
        ),
        # HIRING — LinkedIn
        Signal(
            source_url="https://www.linkedin.com/company/servicenow",
            source_type="linkedin",
            dimension=Dimension.HIRING,
            signal_type="employee_count",
            content="LinkedIn lists ServiceNow at 23,000+ employees with 480,000+ followers; currently hiring Platform Engineers and People Analysts",
            raw_snippet="ServiceNow · 23,000+ employees · IT Services & Consulting · 481,220 followers · Hiring: Platform Engineer, Sr. People Analyst",
            confidence=0.5,
            extracted_at=_NOW,
        ),
        # INTERNAL_MOBILITY
        Signal(
            source_url="https://www.servicenow.com/careers.html",
            source_type="careers_site",
            dimension=Dimension.INTERNAL_MOBILITY,
            signal_type="internal_mobility_program",
            content="No public-facing internal mobility or career-path content found on careers site",
            raw_snippet="servicenow.com/careers — no internal career marketplace or mobility program page found",
            confidence=0.2,
            extracted_at=_NOW,
        ),
        # FILING — Financial (quarterly revenue)
        Signal(
            source_url="https://investors.servicenow.com/news-releases/news-release-details/servicenow-reports-first-quarter-2026-financial-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="ServiceNow Q1 FY2026: total revenue $3.77B (+22% YoY); subscription revenue $3.67B; remaining performance obligations $27.7B",
            raw_snippet="Q1 FY2026: Total Revenue $3.77B · Subscription Revenue $3.67B · RPO $27.7B · 22% YoY growth",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://investors.servicenow.com/news-releases/news-release-details/servicenow-reports-third-quarter-2025-financial-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="ServiceNow quarterly revenue trend: Q1 FY2025 $2.95B → Q2 FY2025 $3.09B → Q3 FY2025 $3.35B → Q1 FY2026 $3.77B",
            raw_snippet="Q1 FY25: $2.95B · Q2 FY25: $3.09B · Q3 FY25: $3.35B · Q1 FY26: $3.77B",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://investors.servicenow.com/news-releases/news-release-details/servicenow-reports-first-quarter-2026-financial-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="Management raised full-year FY2026 subscription revenue guidance; customers spending $1M+ on Now Assist grew 130%+ YoY",
            raw_snippet="FY2026 guidance raised · Now Assist $1M+ customers: +130% YoY · Management commentary: AI growth exceeding expectations",
            confidence=0.9,
            extracted_at=_NOW,
        ),
        # NEWS — AI strategy
        Signal(
            source_url="https://newsroom.servicenow.com/news/servicenow-q1-2026-results",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="ai_strategy",
            content="ServiceNow Now Assist and AI Agents are core growth drivers; Now Assist customers spending $1M+ grew 130%+ YoY; platform positions itself as the 'AI control tower for enterprise workflows'",
            raw_snippet="Now Assist · AI Agents · AI Control Tower · Agentic AI workflows · integrates OpenAI and Anthropic models",
            confidence=0.9,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://newsroom.servicenow.com/news/servicenow-q1-2026-results",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="ai_strategy",
            content="ServiceNow integrates OpenAI, Anthropic, and other LLMs — focuses on orchestration layer, not building foundation models",
            raw_snippet="ServiceNow partners with OpenAI and Anthropic — acting as orchestration layer for enterprise AI deployment",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        # NEWS — Leadership
        Signal(
            source_url="https://newsroom.servicenow.com/news/servicenow-q1-2026-results",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="chro_change",
            content="CEO Bill McDermott on Q1 FY2026 earnings: 'AI will fundamentally reshape white-collar work; enterprises need ServiceNow as the coordination layer for AI agents across the business'",
            raw_snippet="CEO McDermott Q1 FY2026: 'AI is reshaping work, ServiceNow is the AI control tower' · Also warned AI agents could impact graduate-level jobs",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        # NEWS — Hiring / expansion
        Signal(
            source_url="https://investors.servicenow.com/news-releases/2024-annual-report",
            source_type="news",
            dimension=Dimension.HIRING,
            signal_type="growth_signal",
            content="ServiceNow expanding engineering presence in APAC and EU; new hubs announced in London (300 roles) and Singapore (150 roles) in 2024",
            raw_snippet="ServiceNow to open engineering hub in London (300 roles) and expand Singapore office (150 roles) in H2 2024",
            confidence=0.8,
            extracted_at=_NOW,
        ),
        # M&A
        Signal(
            source_url="https://newsroom.servicenow.com/news/servicenow-acquires-armis",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="integration_complexity",
            content="ServiceNow acquired Armis (cybersecurity / asset visibility) — expands total addressable market into security operations and AI-powered asset management",
            raw_snippet="ServiceNow acquires Armis · Strengthens security operations and AI-powered asset visibility · One of ServiceNow's most strategic acquisitions",
            confidence=0.9,
            extracted_at=_NOW,
        ),
    ]
    return EvidenceBundle(
        company_name="ServiceNow",
        domain="servicenow.com",
        sources_attempted=[
            "https://www.servicenow.com/careers.html",
            "https://servicenow.wd5.myworkdayjobs.com/External",
            "https://www.glassdoor.com/Reviews/ServiceNow-Reviews-E403249.htm",
            "https://www.linkedin.com/company/servicenow",
            "https://investors.servicenow.com/news-releases",
            "https://newsroom.servicenow.com",
        ],
        sources_fetched=[
            "https://www.servicenow.com/careers.html",
            "https://servicenow.wd5.myworkdayjobs.com/External",
            "https://investors.servicenow.com/news-releases",
            "https://newsroom.servicenow.com",
        ],
        signals=signals,
        ats=ATSDetection(
            ats_name="Workday",
            evidence_url="https://servicenow.wd5.myworkdayjobs.com/External",
            detection_method="apply_url",
            confidence=0.95,
        ),
        coverage=_coverage(signals),
        is_mock=True,
        fetched_at=_NOW,
    )


# ---------------------------------------------------------------------------
# Company C — Wayfair
# ---------------------------------------------------------------------------
def _wayfair() -> EvidenceBundle:
    signals = [
        # HRIT
        Signal(
            source_url="https://boards.greenhouse.io/wayfair",
            source_type="job_posting",
            dimension=Dimension.HRIT,
            signal_type="ats_detection",
            content="Wayfair uses Greenhouse ATS; apply URLs route through boards.greenhouse.io/wayfair",
            raw_snippet="boards.greenhouse.io/wayfair — Wayfair open positions",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        # HIRING
        Signal(
            source_url="https://boards.greenhouse.io/wayfair",
            source_type="job_posting",
            dimension=Dimension.HIRING,
            signal_type="hiring_volume",
            content="~50 open roles post-RIF; selective hiring in Technology (28) and Operations (14) — significantly reduced from pre-layoff levels",
            raw_snippet="52 open positions · Technology: 28 · Operations: 14 · Corporate: 10",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        # NEWS — Layoffs
        Signal(
            source_url="https://www.businessinsider.com/wayfair-layoffs-2024",
            source_type="news",
            dimension=Dimension.RETENTION,
            signal_type="layoff_event",
            content="Wayfair conducted two large layoff rounds: Jan 2023 (1,750 employees, ~10% workforce) and Jan 2024 (1,650 employees, ~13% workforce)",
            raw_snippet="Wayfair layoffs: 1,750 in Jan 2023 + 1,650 in Jan 2024 · CEO Niraj Shah cited cost discipline",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://techcrunch.com/wayfair-layoffs-2024-follow-up",
            source_type="news",
            dimension=Dimension.RETENTION,
            signal_type="layoff_event",
            content="Post-layoff Glassdoor sentiment dropped sharply: CEO approval fell from 72% to 61%; 42% of reviews mention 'uncertainty' or 'unclear direction'",
            raw_snippet="Glassdoor CEO approval: 61% (down from 72%) · Review themes: layoff anxiety, unclear strategy, reduced morale",
            confidence=0.8,
            extracted_at=_NOW,
        ),
        # NEWS — Leadership
        Signal(
            source_url="https://www.prnewswire.com/news-releases/wayfair-names-new-cpo-2024",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="chro_change",
            content="Wayfair appointed a new Chief People Officer in Q1 2024, tasked with rebuilding talent strategy and restoring employee trust following headcount reductions",
            raw_snippet="Wayfair new CPO appointed March 2024 — tasked with rebuilding people strategy after two rounds of reductions",
            confidence=0.9,
            extracted_at=_NOW,
        ),
        # NEWS — AI strategy
        Signal(
            source_url="https://www.wayfair.com/about/press-releases/wayfair-ai-2024",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="ai_strategy",
            content="Wayfair investing in AI for visual search, personalized recommendations, and supply chain optimization; limited public signal on AI in HR or talent acquisition",
            raw_snippet="Wayfair AI: Visual search, personalization, pricing AI — no talent AI announcements found",
            confidence=0.6,
            extracted_at=_NOW,
        ),
        # RETENTION
        Signal(
            source_url="https://www.glassdoor.com/Reviews/Wayfair-Reviews-E14657.htm",
            source_type="glassdoor",
            dimension=Dimension.RETENTION,
            signal_type="glassdoor_rating",
            content="Wayfair Glassdoor: 3.4★, 58% recommend, 61% CEO approval — below industry average; morale damage from layoffs clearly visible",
            raw_snippet="3.4 ★ · 58% would recommend · CEO Niraj Shah 61% approval · Cons: morale low after layoffs, unclear direction",
            confidence=0.75,
            extracted_at=_NOW,
        ),
        # ONBOARDING
        Signal(
            source_url="https://www.glassdoor.com/Reviews/Wayfair-Reviews-E14657.htm",
            source_type="glassdoor",
            dimension=Dimension.ONBOARDING,
            signal_type="onboarding_sentiment",
            content="Glassdoor reviewers cite inconsistent onboarding and unclear role expectations post-restructuring",
            raw_snippet="Pros: talented colleagues · Cons: onboarding is inconsistent, unclear expectations after reorg",
            confidence=0.55,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://www.wayfair.com/careers",
            source_type="careers_site",
            dimension=Dimension.ONBOARDING,
            signal_type="careers_site_maturity",
            content="Careers site is basic — no chatbot, no talent community, no personalization features; standard role listing only",
            raw_snippet="wayfair.com/careers — Search jobs · No chat widget detected · No 'Join talent network' CTA found",
            confidence=0.6,
            extracted_at=_NOW,
        ),
        # INTERNAL_MOBILITY
        Signal(
            source_url="https://www.wayfair.com/careers",
            source_type="careers_site",
            dimension=Dimension.INTERNAL_MOBILITY,
            signal_type="internal_mobility_program",
            content="No internal mobility or career development content visible on public careers site",
            raw_snippet="wayfair.com/careers — no internal career marketplace found",
            confidence=0.2,
            extracted_at=_NOW,
        ),
        # FILING — Financial
        Signal(
            source_url="https://ir.wayfair.com/news-releases/2025/wayfair-q4-2024-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="Wayfair FY2024 net revenue: $11.6B (down from $12.0B in FY2023); gross margin improved to 31.7%; pursuing profitability over growth",
            raw_snippet="FY2024 Net Revenue: $11.6B · Gross Margin: 31.7% · Adj. EBITDA positive for first time since 2020",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://ir.wayfair.com/news-releases/2025/wayfair-q4-2024-results",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="Revenue trend: FY2022 $13.7B → FY2023 $12.0B → FY2024 $11.6B — three consecutive years of decline; management focused on margin recovery",
            raw_snippet="FY22: $13.7B · FY23: $12.0B · FY24: $11.6B · Shift from growth to profitability",
            confidence=0.9,
            extracted_at=_NOW,
        ),
        # HIRING — LinkedIn
        Signal(
            source_url="https://www.linkedin.com/company/wayfair",
            source_type="linkedin",
            dimension=Dimension.HIRING,
            signal_type="employer_brand_reach",
            content="LinkedIn lists Wayfair at ~11,000 employees; recent posts about 'rebuilding culture' and 'people-first focus'",
            raw_snippet="Wayfair · 11,000 employees · Retail · recent company post: 'Rebuilding culture: what it means for our people'",
            confidence=0.5,
            extracted_at=_NOW,
        ),
    ]
    return EvidenceBundle(
        company_name="Wayfair",
        domain="wayfair.com",
        sources_attempted=[
            "https://www.wayfair.com/careers",
            "https://boards.greenhouse.io/wayfair",
            "https://www.glassdoor.com/Reviews/Wayfair-Reviews-E14657.htm",
            "https://www.linkedin.com/company/wayfair",
            "https://www.businessinsider.com/wayfair-layoffs-2024",
            "https://ir.wayfair.com/news-releases",
        ],
        sources_fetched=[
            "https://www.wayfair.com/careers",
            "https://boards.greenhouse.io/wayfair",
            "https://www.businessinsider.com/wayfair-layoffs-2024",
            "https://ir.wayfair.com/news-releases",
        ],
        signals=signals,
        ats=ATSDetection(
            ats_name="Greenhouse",
            evidence_url="https://boards.greenhouse.io/wayfair",
            detection_method="apply_url",
            confidence=0.95,
        ),
        coverage=_coverage(signals),
        is_mock=True,
        fetched_at=_NOW,
    )


# ---------------------------------------------------------------------------
# Company D — Marriott International
# ---------------------------------------------------------------------------
def _marriott() -> EvidenceBundle:
    signals = [
        # HRIT
        Signal(
            source_url="https://marriott.taleo.net/careersection/2/jobsearch.ftl",
            source_type="job_posting",
            dimension=Dimension.HRIT,
            signal_type="ats_detection",
            content="Marriott uses Taleo ATS (Oracle); apply URLs route through marriott.taleo.net — legacy platform, strong modernization signal",
            raw_snippet="marriott.taleo.net/careersection/2/jobsearch.ftl — Marriott Careers powered by Taleo",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        # HIRING
        Signal(
            source_url="https://marriott.taleo.net/careersection/2/jobsearch.ftl",
            source_type="job_posting",
            dimension=Dimension.HIRING,
            signal_type="hiring_volume",
            content="500+ open roles; majority hourly/operations: Front Desk (120+), Housekeeping (95+), F&B (80+); high seasonal variance",
            raw_snippet="512 open positions · Front Desk Agent: 127 · Housekeeping: 98 · Food & Beverage: 84 · Management: 62",
            confidence=0.85,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://marriott.taleo.net/careersection/2/jobsearch.ftl",
            source_type="job_posting",
            dimension=Dimension.HIRING,
            signal_type="role_mix",
            content="85% of open roles are hourly/frontline — high-volume hiring motion dominates; corporate roles are a small fraction",
            raw_snippet="Hourly roles: 437 (85%) · Salaried/management: 75 (15%)",
            confidence=0.8,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://www.glassdoor.com/Interview/Marriott-International-Interview-Questions-E2734.htm",
            source_type="glassdoor",
            dimension=Dimension.HIRING,
            signal_type="interview_experience",
            content="Hourly hiring process rated negative: 54% positive experience; many citing 'took 3 weeks to hear back' for entry-level roles",
            raw_snippet="Interview difficulty: Easy · Experience: 54% positive · Cons: process disorganized, took 3 weeks to hear back for front desk role",
            confidence=0.7,
            extracted_at=_NOW,
        ),
        # RETENTION
        Signal(
            source_url="https://www.glassdoor.com/Reviews/Marriott-International-Reviews-E2734.htm",
            source_type="glassdoor",
            dimension=Dimension.RETENTION,
            signal_type="glassdoor_rating",
            content="Marriott Glassdoor: 3.8★, 71% recommend — below hotel-industry average; high turnover explicitly mentioned in reviews",
            raw_snippet="3.8 ★ · 71% recommend to a friend · Cons: high turnover, inconsistent management, limited advancement",
            confidence=0.75,
            extracted_at=_NOW,
        ),
        # ONBOARDING
        Signal(
            source_url="https://www.marriott.com/careers",
            source_type="careers_site",
            dimension=Dimension.ONBOARDING,
            signal_type="careers_site_maturity",
            content="Careers site has dated UX — basic role search only, no chatbot/assistant, no talent community, no personalization",
            raw_snippet="marriott.com/careers · Search jobs by location · No chat widget · No 'Join talent network' CTA · Basic filter UI",
            confidence=0.65,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://www.glassdoor.com/Reviews/Marriott-International-Reviews-E2734.htm",
            source_type="glassdoor",
            dimension=Dimension.ONBOARDING,
            signal_type="onboarding_sentiment",
            content="Glassdoor reviewers note inconsistent onboarding quality across properties; 'depends on the manager and property'",
            raw_snippet="Cons: onboarding is inconsistent, depends on the property and manager · no structured first-week plan",
            confidence=0.55,
            extracted_at=_NOW,
        ),
        # HIRING — LinkedIn + growth
        Signal(
            source_url="https://www.linkedin.com/company/marriott-international",
            source_type="linkedin",
            dimension=Dimension.HIRING,
            signal_type="employee_count",
            content="LinkedIn lists Marriott at 352,000+ employees — one of the world's largest hospitality employers",
            raw_snippet="Marriott International · 352,000+ employees · Hospitality · currently hiring: Front Desk Agent, Housekeeping, F&B Manager",
            confidence=0.5,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://www.reuters.com/marriott-expansion-2024",
            source_type="news",
            dimension=Dimension.HIRING,
            signal_type="growth_signal",
            content="Marriott post-COVID expansion: plans to open 500+ new properties globally by 2026, requiring significant frontline hiring ramp",
            raw_snippet="Marriott plans to add 500 properties globally by 2026, requiring aggressive frontline hiring across all brands",
            confidence=0.8,
            extracted_at=_NOW,
        ),
        # INTERNAL_MOBILITY
        Signal(
            source_url="https://www.marriott.com/careers",
            source_type="careers_site",
            dimension=Dimension.INTERNAL_MOBILITY,
            signal_type="internal_mobility_program",
            content="'Explore Careers' page mentions cross-brand mobility but no digital career marketplace or skills-based pathing visible",
            raw_snippet="Marriott Bonvoy Career — explore opportunities across our 30 brands · No internal marketplace found",
            confidence=0.3,
            extracted_at=_NOW,
        ),
        # FILING — Financial
        Signal(
            source_url="https://ir.marriott.com/news-releases/news-release-details/marriott-international-reports-fourth-quarter-and-full-year-2024",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="Marriott FY2024 total revenues: $25.1B (+6% YoY); net income $2.4B; RevPAR grew 4.2% globally driven by leisure and international travel",
            raw_snippet="FY2024: Total Revenue $25.1B · Net Income $2.4B · RevPAR +4.2% · 9,100+ properties worldwide",
            confidence=0.95,
            extracted_at=_NOW,
        ),
        Signal(
            source_url="https://ir.marriott.com/news-releases",
            source_type="filing",
            dimension=Dimension.HRIT,
            signal_type="revenue",
            content="Marriott quarterly revenue: Q1 2024 $5.98B → Q2 2024 $6.44B → Q3 2024 $6.26B → Q4 2024 $6.42B — consistent post-COVID recovery",
            raw_snippet="Q1 2024: $5.98B · Q2 2024: $6.44B · Q3 2024: $6.26B · Q4 2024: $6.42B",
            confidence=0.9,
            extracted_at=_NOW,
        ),
        # NEWS — AI strategy
        Signal(
            source_url="https://newsroom.marriott.com/2024/ai-hospitality",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="ai_strategy",
            content="Marriott testing AI concierge for guest services and AI-powered scheduling for housekeeping; no public AI announcements for talent acquisition or HR",
            raw_snippet="Marriott piloting AI concierge and AI scheduling · No talent AI announcements found · HR tech investment limited to operational tools",
            confidence=0.6,
            extracted_at=_NOW,
        ),
        # NEWS — Leadership
        Signal(
            source_url="https://newsroom.marriott.com/2024/ceo-outlook",
            source_type="news",
            dimension=Dimension.HRIT,
            signal_type="chro_change",
            content="CEO Anthony Capuano at 2024 investor day: 'Our associates are our competitive advantage — investing in tools that reduce hiring friction and improve retention is a top priority'",
            raw_snippet="CEO Capuano investor day 2024: associate investment, hiring friction reduction, retention as strategic priority",
            confidence=0.75,
            extracted_at=_NOW,
        ),
    ]
    return EvidenceBundle(
        company_name="Marriott International",
        domain="marriott.com",
        sources_attempted=[
            "https://www.marriott.com/careers",
            "https://marriott.taleo.net/careersection/2/jobsearch.ftl",
            "https://www.glassdoor.com/Reviews/Marriott-International-Reviews-E2734.htm",
            "https://www.linkedin.com/company/marriott-international",
            "https://www.reuters.com/marriott-expansion-2024",
            "https://ir.marriott.com/news-releases",
        ],
        sources_fetched=[
            "https://www.marriott.com/careers",
            "https://marriott.taleo.net/careersection/2/jobsearch.ftl",
            "https://www.reuters.com/marriott-expansion-2024",
            "https://ir.marriott.com/news-releases",
        ],
        signals=signals,
        ats=ATSDetection(
            ats_name="Taleo",
            evidence_url="https://marriott.taleo.net/careersection/2/jobsearch.ftl",
            detection_method="apply_url",
            confidence=0.95,
        ),
        coverage=_coverage(signals),
        is_mock=True,
        fetched_at=_NOW,
    )


# ---------------------------------------------------------------------------
# Registry + provider class
# ---------------------------------------------------------------------------

_COMPANIES: dict[str, EvidenceBundle] = {
    "hubspot": _hubspot(),
    "servicenow": _servicenow(),
    "wayfair": _wayfair(),
    "marriott": _marriott(),
    "marriott international": _marriott(),
}


class MockSearchProvider(SearchProvider):
    def search_company(self, company_name: str) -> EvidenceBundle:
        key = company_name.lower().strip()
        if key in _COMPANIES:
            return _COMPANIES[key]
        for name, bundle in _COMPANIES.items():
            if key in name or name in key:
                return bundle
        raise ValueError(
            f"No mock data for '{company_name}'. "
            f"Available: {', '.join(k.title() for k in _COMPANIES if ' ' not in k)}"
        )

    @staticmethod
    def available_companies() -> list[str]:
        return ["HubSpot", "ServiceNow", "Wayfair", "Marriott International"]
