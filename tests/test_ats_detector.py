import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from ats.detector import detect, detect_from_urls


# ── Pass 1: URL pattern tests ─────────────────────────────────────────────────

@pytest.mark.parametrize("url,expected_ats", [
    ("https://servicenow.wd5.myworkdayjobs.com/External",  "Workday"),
    ("https://hubspot.wd1.myworkdayjobs.com/en-US/careers", "Workday"),
    ("https://boards.greenhouse.io/hubspot/jobs/12345",    "Greenhouse"),
    ("https://wayfair.greenhouse.io/jobs",                 "Greenhouse"),
    ("https://jobs.lever.co/acme/abc-def",                 "Lever"),
    ("https://careers.acme.icims.com/jobs/search",         "iCIMS"),
    ("https://acme.icims.com/jobs/1234",                   "iCIMS"),
    ("https://marriott.taleo.net/careersection/2/job.ftl",  "Taleo"),
    ("https://tbe.taleo.net/NA14/ats/careers/apply.jsp",   "Taleo"),
    ("https://jobs.ashbyhq.com/acme/12345",                "Ashby"),
    ("https://careers.smartrecruiters.com/Acme/",          "SmartRecruiters"),
    ("https://acme.bamboohr.com/jobs/",                    "BambooHR"),
    ("https://acme.myphenompeople.com/careers",            "Phenom"),
    ("https://jobs.jobvite.com/acme/job/A1b2",             "Jobvite"),
    ("https://apply.workable.com/acme/j/123/",             "Workable"),
])
def test_url_patterns(url, expected_ats):
    result = detect(url)
    assert result.ats_name == expected_ats, f"Expected {expected_ats}, got {result.ats_name} for {url}"
    assert result.detection_method == "apply_url"
    assert result.confidence == 0.95


def test_unknown_url_returns_none():
    result = detect("https://example.com/careers")
    assert result.ats_name is None
    assert result.confidence == 0.0


def test_detect_from_urls_finds_first_match():
    urls = [
        "https://example.com/careers",
        "https://boards.greenhouse.io/acme/jobs/1",
        "https://acme.wd1.myworkdayjobs.com/jobs",
    ]
    result = detect_from_urls(urls)
    assert result.ats_name == "Greenhouse"  # first match wins


def test_detect_from_urls_all_unknown():
    result = detect_from_urls(["https://example.com", "https://example.org"])
    assert result.ats_name is None


# ── Pass 2: HTML markup tests ─────────────────────────────────────────────────

def test_markup_greenhouse_script():
    html = '<script src="https://app.greenhouse.io/apply.js"></script><div>apply</div>'
    result = detect("https://example.com/careers", html)
    assert result.ats_name == "Greenhouse"
    assert result.detection_method in ("markup", "json_ld")


def test_markup_workday_json_ld():
    html = '''
    <script type="application/ld+json">
    {"@type": "JobPosting", "url": "https://acme.wd5.myworkdayjobs.com/en-US/External/job/123"}
    </script>
    '''
    result = detect("https://acme.com/careers", html)
    assert result.ats_name == "Workday"
    assert result.detection_method == "json_ld"


def test_markup_taleo():
    html = '<iframe src="https://acme.taleo.net/careersection/2/jobapply.ftl"></iframe>'
    result = detect("https://acme.com/careers", html)
    assert result.ats_name == "Taleo"
