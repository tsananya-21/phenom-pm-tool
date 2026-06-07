"""
ATS Detection — two-pass approach:
  Pass 1: URL/domain pattern matching (highest confidence, no HTML needed)
  Pass 2: HTML markup signals (medium confidence, fallback)

compile_patterns() is called once at module load.
detect(url, html) is the public API.
"""
from __future__ import annotations

import re
import json
from typing import Optional

from models.evidence import ATSDetection


# ── Pass 1: URL patterns ──────────────────────────────────────────────────────

_URL_PATTERNS: list[tuple[str, list[str]]] = [
    ("Workday",          ["myworkdayjobs\\.com", r"/wday/", r"workday\.[a-z0-9]+/en-us"]),
    ("Greenhouse",       ["boards\\.greenhouse\\.io", "greenhouse\\.io/jobs"]),
    ("Lever",            ["jobs\\.lever\\.co"]),
    ("iCIMS",            [r"\.icims\.com/jobs", r"careers\.[a-z0-9\-]+\.icims\.com"]),
    ("SuccessFactors",   ["successfactors\\.com", "sap-successfactors"]),
    ("Taleo",            ["taleo\\.net", r"tbe\.taleo\.net", r"oracle\.taleo\.net"]),
    ("Ashby",            ["jobs\\.ashbyhq\\.com"]),
    ("SmartRecruiters",  ["careers\\.smartrecruiters\\.com"]),
    ("BambooHR",         [r"\.bamboohr\.com/jobs", r"\.bamboohr\.com/careers"]),
    ("Phenom",           ["phenom\\.people\\.com", "phenompeople\\.com", r"myphenompeople\.com"]),
    ("Jobvite",          ["jobs\\.jobvite\\.com"]),
    ("Workable",         ["apply\\.workable\\.com"]),
    ("JazzHR",           ["resumator\\.com", r"app\.jazz\.co/apply"]),
    ("Rippling",         [r"app\.rippling\.com/job"]),
]

# Compile once
_COMPILED_URL: list[tuple[str, list[re.Pattern]]] = [
    (ats, [re.compile(p, re.IGNORECASE) for p in patterns])
    for ats, patterns in _URL_PATTERNS
]


def _match_url(url: str) -> Optional[tuple[str, str]]:
    """Return (ats_name, matched_pattern_str) or None."""
    for ats_name, patterns in _COMPILED_URL:
        for pat in patterns:
            if pat.search(url):
                return ats_name, pat.pattern
    return None


# ── Pass 2: HTML markup signals ───────────────────────────────────────────────

_MARKUP_PATTERNS: list[tuple[str, list[str]]] = [
    ("Workday",         [r'src=["\'][^"\']*workday[^"\']*["\']',
                         r'workday_domain\s*=',
                         r'"@type"\s*:\s*"JobPosting".*myworkdayjobs']),
    ("Greenhouse",      [r'src=["\'][^"\']*greenhouse[^"\']*["\']',
                         r'action=["\'][^"\']*greenhouse\.io']),
    ("Lever",           [r'src=["\'][^"\']*lever\.co[^"\']*["\']',
                         r'iframe[^>]+src=["\'][^"\']*jobs\.lever\.co']),
    ("iCIMS",           [r'src=["\'][^"\']*icims[^"\']*["\']',
                         r'icims\.com/jobs']),
    ("SuccessFactors",  [r'successfactors\.com', r'sap-successfactors']),
    ("Taleo",           [r'taleo\.net', r'class=["\'][^"\']*taleo']),
    ("Ashby",           [r'ashbyhq\.com']),
    ("SmartRecruiters", [r'smartrecruiters\.com']),
    ("BambooHR",        [r'bamboohr\.com']),
    ("Phenom",          [r'phenompeople\.com', r'phenom\.people\.com',
                         r'myphenompeople\.com']),
    ("Jobvite",         [r'jobvite\.com']),
    ("Workable",        [r'workable\.com']),
]

_COMPILED_MARKUP: list[tuple[str, list[re.Pattern]]] = [
    (ats, [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns])
    for ats, patterns in _MARKUP_PATTERNS
]


def _match_markup(html: str) -> Optional[tuple[str, str]]:
    """Return (ats_name, detection_method) or None."""
    # Also try JSON-LD JobPosting url field
    ld_match = re.search(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    )
    if ld_match:
        try:
            ld = json.loads(ld_match.group(1))
            items = ld if isinstance(ld, list) else [ld]
            for item in items:
                if item.get("@type") == "JobPosting":
                    apply_url = item.get("url") or item.get("applyUrl") or ""
                    result = _match_url(apply_url)
                    if result:
                        return result[0], "json_ld"
        except (json.JSONDecodeError, AttributeError):
            pass

    for ats_name, patterns in _COMPILED_MARKUP:
        for pat in patterns:
            if pat.search(html):
                return ats_name, "markup"

    return None


# ── Public API ────────────────────────────────────────────────────────────────

def detect(url: str, html: str = "") -> ATSDetection:
    """
    Detect ATS from a URL (and optionally its HTML content).
    Returns ATSDetection with confidence and detection_method.
    """
    # Pass 1: URL
    url_result = _match_url(url)
    if url_result:
        ats_name, pattern = url_result
        return ATSDetection(
            ats_name=ats_name,
            evidence_url=url,
            detection_method="apply_url",
            confidence=0.95,
        )

    # Pass 2: markup (only if HTML provided)
    if html:
        markup_result = _match_markup(html)
        if markup_result:
            ats_name, method = markup_result
            confidence = 0.8 if method == "json_ld" else 0.65
            return ATSDetection(
                ats_name=ats_name,
                evidence_url=url,
                detection_method=method,
                confidence=confidence,
            )

    return ATSDetection(detection_method="none", confidence=0.0)


def detect_from_urls(urls: list[str]) -> ATSDetection:
    """Run Pass 1 across a list of URLs; return highest-confidence hit."""
    for url in urls:
        result = _match_url(url)
        if result:
            ats_name, _ = result
            return ATSDetection(
                ats_name=ats_name,
                evidence_url=url,
                detection_method="apply_url",
                confidence=0.95,
            )
    return ATSDetection(detection_method="none", confidence=0.0)
