"""
Stage 3 — Signal Extraction

Deterministic extractors. Each function takes raw text / snippets and returns
list[Signal]. No model calls here. Every signal carries source_url + confidence.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from models.evidence import Dimension, Signal

_NOW = lambda: datetime.now(timezone.utc).isoformat()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sig(source_url: str, source_type: str, dim: Dimension, signal_type: str,
         content: str, snippet: str, confidence: float) -> Signal:
    return Signal(
        source_url=source_url,
        source_type=source_type,
        dimension=dim,
        signal_type=signal_type,
        content=content,
        raw_snippet=snippet[:400],
        confidence=confidence,
        extracted_at=_NOW(),
    )


# ── Job posting extractor ─────────────────────────────────────────────────────

_HR_TITLES = re.compile(
    r"\b(recruiter|talent acquisition|people ops|people partner|HR business partner|"
    r"HRBP|workforce analytics|people analytics|talent intelligence|DEI|diversity)\b",
    re.IGNORECASE,
)
_PAY_RE = re.compile(r"\$[\d,]+\s*[–\-]\s*\$[\d,]+", re.IGNORECASE)
_REMOTE_RE = re.compile(r"\b(remote|hybrid|in[-\s]office|on[-\s]site)\b", re.IGNORECASE)
_ROLE_BUCKETS = {
    "engineering":  re.compile(r"\b(engineer|developer|architect|SRE|devops|data scientist|ML)\b", re.IGNORECASE),
    "sales":        re.compile(r"\b(account executive|AE|sales|business development|SDR|BDR)\b", re.IGNORECASE),
    "hr_ta":        _HR_TITLES,
    "operations":   re.compile(r"\b(operations|ops|supply chain|logistics|analyst)\b", re.IGNORECASE),
    "marketing":    re.compile(r"\b(marketing|brand|content|growth|demand gen)\b", re.IGNORECASE),
}


def extract_job_signals(job_texts: list[tuple[str, str]], ats_url: Optional[str]) -> list[Signal]:
    """
    job_texts: list of (url, text) pairs from fetched job listing pages.
    Returns signals for hiring volume, role mix, pay transparency, HR investment.
    """
    signals: list[Signal] = []
    if not job_texts:
        return signals

    all_text = " ".join(t for _, t in job_texts)
    representative_url = job_texts[0][0]

    # Estimate count from text patterns
    count_match = re.search(r"(\d+)\s*(open\s+)?(position|job|role|opening)s?", all_text, re.IGNORECASE)
    count_est = int(count_match.group(1)) if count_match else len(job_texts)
    signals.append(_sig(
        representative_url, "job_posting", Dimension.HIRING, "hiring_volume",
        f"~{count_est} open roles detected across {len(job_texts)} pages",
        all_text[:200], min(0.5 + 0.1 * len(job_texts), 0.85),
    ))

    # Role mix
    bucket_counts = {k: len(pat.findall(all_text)) for k, pat in _ROLE_BUCKETS.items()}
    top_buckets = sorted(bucket_counts.items(), key=lambda x: -x[1])[:3]
    role_mix_str = ", ".join(f"{k}({v})" for k, v in top_buckets if v > 0)
    if role_mix_str:
        signals.append(_sig(
            representative_url, "job_posting", Dimension.HIRING, "role_mix",
            f"Top role categories: {role_mix_str}",
            role_mix_str, 0.6,
        ))

    # HR/TA investment signal
    hr_count = sum(len(_HR_TITLES.findall(t)) for _, t in job_texts)
    if hr_count >= 2:
        signals.append(_sig(
            representative_url, "job_posting", Dimension.HRIT, "ta_team_investment",
            f"{hr_count} HR/TA/People-related role mentions — active TA team investment",
            f"{hr_count} HR/TA role mentions", 0.7,
        ))

    # Pay transparency
    pay_pages = sum(1 for _, t in job_texts if _PAY_RE.search(t))
    if pay_pages:
        pct = pay_pages / len(job_texts)
        signals.append(_sig(
            representative_url, "job_posting", Dimension.HIRING, "pay_transparency",
            f"Salary ranges present in {pay_pages}/{len(job_texts)} postings ({pct:.0%})",
            f"Pay transparency in {pct:.0%} of sampled postings", 0.7,
        ))

    # Work model
    remote_hits = [m.group() for _, t in job_texts for m in [_REMOTE_RE.search(t)] if m]
    if remote_hits:
        from collections import Counter
        top_model = Counter(h.lower() for h in remote_hits).most_common(1)[0][0]
        signals.append(_sig(
            representative_url, "job_posting", Dimension.HIRING, "work_model",
            f"Dominant work model in postings: {top_model}",
            f"Work model mentions: {', '.join(set(h.lower() for h in remote_hits[:5]))}", 0.6,
        ))

    return signals


# ── Careers site extractor ────────────────────────────────────────────────────

_CHATBOT_RE = re.compile(
    r"(intercom|drift|tidio|livechat|tawk|freshchat|zendesk|phenom.*chat|"
    r"chat.*widget|virtual.*assistant|ask.*assistant)",
    re.IGNORECASE,
)
_TALENT_COMMUNITY_RE = re.compile(
    r"(join.*talent|talent.*network|talent.*community|join.*community|"
    r"stay.*connected|get.*notified.*jobs|job.*alert)",
    re.IGNORECASE,
)
_PERSONALIZATION_RE = re.compile(
    r"(recommended.*for\s+you|jobs.*you.*might|based\s+on\s+your|"
    r"personali[sz]ed|your\s+career\s+path)",
    re.IGNORECASE,
)
_SEARCH_FILTER_RE = re.compile(
    r"(filter\s+by|sort\s+by|keyword\s+search|refine\s+results)",
    re.IGNORECASE,
)


def extract_careers_site_signals(url: str, html: str, text: str) -> list[Signal]:
    signals: list[Signal] = []
    if not text and not html:
        return signals

    combined = (html + " " + text)[:20000]

    has_chatbot = bool(_CHATBOT_RE.search(combined))
    has_talent_community = bool(_TALENT_COMMUNITY_RE.search(combined))
    has_personalization = bool(_PERSONALIZATION_RE.search(combined))
    has_search = bool(_SEARCH_FILTER_RE.search(text))

    maturity_score = sum([has_chatbot, has_talent_community, has_personalization, has_search])
    maturity_label = ["basic", "basic", "developing", "mature", "advanced"][maturity_score]

    features = []
    if has_chatbot:
        features.append("chatbot/assistant")
    if has_talent_community:
        features.append("talent community CTA")
    if has_personalization:
        features.append("personalization")
    if has_search:
        features.append("search/filter")

    signals.append(_sig(
        url, "careers_site", Dimension.ONBOARDING, "careers_site_maturity",
        f"Careers site maturity: {maturity_label}. "
        f"Features present: {', '.join(features) if features else 'none detected'}",
        f"Maturity: {maturity_label}; features: {', '.join(features) or 'none'}",
        0.6 if features else 0.45,
    ))

    if not has_chatbot:
        signals.append(_sig(
            url, "careers_site", Dimension.ONBOARDING, "no_chatbot",
            "No chatbot or AI assistant detected on careers site — candidate engagement gap",
            "No chat widget detected in page source", 0.55,
        ))

    if not has_talent_community:
        signals.append(_sig(
            url, "careers_site", Dimension.HIRING, "no_talent_community",
            "No talent community / CRM signup found — passive candidate pipeline gap",
            "No 'join talent network' or 'get job alerts' CTA found", 0.5,
        ))

    return signals


# ── LinkedIn signal extractor (from Tavily SERP snippets) ─────────────────────

_EMPLOYEE_COUNT_RE = re.compile(r"([\d,]+(?:\+|–[\d,]+)?)\s*employees?", re.IGNORECASE)
_FOLLOWER_RE = re.compile(r"([\d,]+(?:\+|k|K)?)\s*followers?", re.IGNORECASE)


def extract_linkedin_signals(serp_results: list[dict]) -> list[Signal]:
    """
    serp_results: list of Tavily result dicts {url, title, content/snippet}.
    Extracts employee count, followers, role keywords from snippets.
    """
    signals: list[Signal] = []

    for result in serp_results:
        url = result.get("url", "")
        snippet = result.get("content", result.get("snippet", ""))
        if not snippet:
            continue

        emp_match = _EMPLOYEE_COUNT_RE.search(snippet)
        if emp_match:
            signals.append(_sig(
                url, "linkedin", Dimension.HIRING, "employee_count",
                f"LinkedIn employee count: {emp_match.group(0)}",
                snippet[:300], 0.5,
            ))

        follower_match = _FOLLOWER_RE.search(snippet)
        if follower_match:
            signals.append(_sig(
                url, "linkedin", Dimension.HIRING, "employer_brand_reach",
                f"LinkedIn followers: {follower_match.group(0)}",
                snippet[:300], 0.45,
            ))

        # Culture/brand keywords in snippet
        culture_kws = re.findall(
            r"\b(culture|values|DEI|inclusion|flexibility|growth|learning|"
            r"innovation|mission|purpose)\b",
            snippet, re.IGNORECASE,
        )
        if culture_kws:
            signals.append(_sig(
                url, "linkedin", Dimension.ONBOARDING, "employer_brand_language",
                f"LinkedIn brand language keywords: {', '.join(set(k.lower() for k in culture_kws))}",
                snippet[:300], 0.4,
            ))

    return signals


# ── Glassdoor signal extractor (from Tavily SERP snippets) ───────────────────

_RATING_RE = re.compile(r"(\d\.\d)\s*[★✩☆]", re.IGNORECASE)
_RECOMMEND_RE = re.compile(r"(\d+)%\s*(?:would\s+)?recommend", re.IGNORECASE)
_CEO_RE = re.compile(r"(\d+)%\s*CEO approval", re.IGNORECASE)
_INTERVIEW_POS_RE = re.compile(r"(\d+)%\s*positive\s+(?:interview\s+)?experience", re.IGNORECASE)


def extract_glassdoor_signals(serp_results: list[dict]) -> list[Signal]:
    signals: list[Signal] = []

    for result in serp_results:
        url = result.get("url", "")
        snippet = result.get("content", result.get("snippet", ""))
        if not snippet:
            continue

        rating_m = _RATING_RE.search(snippet)
        if rating_m:
            rating = float(rating_m.group(1))
            sentiment = "strong" if rating >= 4.0 else "moderate" if rating >= 3.5 else "weak"
            signals.append(_sig(
                url, "glassdoor", Dimension.RETENTION, "glassdoor_rating",
                f"Glassdoor rating: {rating}★ ({sentiment} retention signal)",
                snippet[:300], 0.7,
            ))

        rec_m = _RECOMMEND_RE.search(snippet)
        if rec_m:
            pct = int(rec_m.group(1))
            signals.append(_sig(
                url, "glassdoor", Dimension.RETENTION, "recommend_rate",
                f"{pct}% of Glassdoor reviewers recommend this employer",
                snippet[:300], 0.6,
            ))

        ceo_m = _CEO_RE.search(snippet)
        if ceo_m:
            signals.append(_sig(
                url, "glassdoor", Dimension.RETENTION, "ceo_approval",
                f"CEO approval: {ceo_m.group(1)}%",
                snippet[:300], 0.55,
            ))

        int_m = _INTERVIEW_POS_RE.search(snippet)
        if int_m:
            pct = int(int_m.group(1))
            label = "positive" if pct >= 70 else "mixed"
            signals.append(_sig(
                url, "glassdoor", Dimension.HIRING, "interview_experience",
                f"Interview experience: {pct}% positive ({label})",
                snippet[:300], 0.6,
            ))

        # Sentiment keywords in cons/pros
        neg_kws = re.findall(
            r"\b(turnover|attrition|burnout|layoff|toxic|micromanage|"
            r"onboarding|slow ramp|unclear|disorgani[sz])\b",
            snippet, re.IGNORECASE,
        )
        if neg_kws:
            signals.append(_sig(
                url, "glassdoor", Dimension.RETENTION, "review_sentiment",
                f"Glassdoor review flags: {', '.join(set(k.lower() for k in neg_kws))}",
                snippet[:300], 0.4,
            ))

    return signals


# ── News signal extractor ─────────────────────────────────────────────────────

_CHRO_RE = re.compile(
    r"(appoint|name[sd]?|hire[sd]?|welcome[sd]?)\s+.*?(CHRO|CPO|Chief People Officer|"
    r"Chief HR Officer|Chief Human Resources)",
    re.IGNORECASE,
)
_LAYOFF_RE = re.compile(
    r"\b(layoff|lay.off|redu[ct]|RIF|reduction.in.force|workforce.reduction|"
    r"job.cut|eliminating.position)\b",
    re.IGNORECASE,
)
_EXPANSION_RE = re.compile(
    r"\b(expand|expansion|new.office|new.hub|opening|hiring.spree|growth|funding|"
    r"Series.[A-E]|IPO|acquisition|acqui[rs])\b",
    re.IGNORECASE,
)


def extract_news_signals(news_texts: list[tuple[str, str]]) -> list[Signal]:
    signals: list[Signal] = []

    for url, text in news_texts:
        if _CHRO_RE.search(text):
            signals.append(_sig(
                url, "news", Dimension.HRIT, "chro_change",
                "Leadership change: CHRO/CPO appointment detected — transformation-appetite signal",
                text[:300], 0.85,
            ))

        if _LAYOFF_RE.search(text):
            signals.append(_sig(
                url, "news", Dimension.RETENTION, "layoff_event",
                "Layoff/RIF event detected in news — retention and morale risk signal",
                text[:300], 0.9,
            ))

        if _EXPANSION_RE.search(text):
            signals.append(_sig(
                url, "news", Dimension.HIRING, "growth_signal",
                "Expansion/growth signal in news — hiring ramp likely",
                text[:300], 0.75,
            ))

    return signals


# ── Review signal extractor (Indeed SERP snippets) ────────────────────────────

def extract_review_signals(serp_results: list[dict]) -> list[Signal]:
    signals: list[Signal] = []

    sentiment_kws = re.compile(
        r"\b(onboarding|turnover|attrition|management|interview|culture|"
        r"work.life|flexibility|growth|advance)\b",
        re.IGNORECASE,
    )

    for result in serp_results:
        url = result.get("url", "")
        snippet = result.get("content", result.get("snippet", ""))
        if not snippet:
            continue

        kws = list(set(m.lower() for m in sentiment_kws.findall(snippet)))
        if kws:
            signals.append(_sig(
                url, "review", Dimension.RETENTION, "review_sentiment",
                f"Indeed review keywords: {', '.join(kws)}",
                snippet[:300], 0.35,
            ))

    return signals
