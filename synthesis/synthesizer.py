"""
Synthesis step: single model call over an EvidenceBundle -> structured analysis dict.

Tolerant JSON parser:
  1. Strip markdown code fences
  2. Extract first balanced JSON object using brace counting
  3. Remove trailing commas
  4. Try json.loads
  5. If model wraps output in extra keys, unwrap it
  6. On failure: retry once with explicit JSON reminder
  7. On second failure: return minimal fallback built from the bundle signals
"""
from __future__ import annotations

import json
import re

from models.evidence import EvidenceBundle
from providers.base import LLMProvider
from synthesis.prompts import build_system_prompt, build_user_message, build_output_schema

_EXPECTED_KEYS = frozenset(["company", "dimensions", "solutionPrototypes", "pitch"])


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _fix_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _extract_first_json_object(text: str) -> str:
    """Extract the first balanced JSON object using brace counting."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    escaped = False
    for i, c in enumerate(text[start:], start):
        if escaped:
            escaped = False
            continue
        if c == "\\" and in_string:
            escaped = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    # Truncated response — return what we have and let the parser deal with it
    return text[start:]


def _unwrap_if_needed(data: dict) -> dict:
    """
    Handle models that wrap their output in extra keys.
    E.g. {"prospect": {"ServiceNow": {...actual output...}}}
    """
    if _EXPECTED_KEYS & data.keys():
        return data
    for v in data.values():
        if isinstance(v, dict):
            if _EXPECTED_KEYS & v.keys():
                return v
            for vv in v.values():
                if isinstance(vv, dict) and (_EXPECTED_KEYS & vv.keys()):
                    return vv
    return data


_REQUIRED_DIM_KEYS = {"hiring", "onboarding", "retention"}


def _is_valid_output(data: dict) -> bool:
    """
    Check that parsed output has the expected shape with real content — not just
    the right keys. Guards against models that emit hollow dimension objects
    (e.g. {"strong": [...], "thin": true}) which technically parse but carry none
    of the fields the UI reads.
    """
    dims = data.get("dimensions")
    if not isinstance(dims, dict):
        return False
    present = _REQUIRED_DIM_KEYS & dims.keys()
    if not present:
        return False
    # Each core dimension present must actually carry analysis content.
    for key in present:
        d = dims[key]
        if not isinstance(d, dict) or "currentState" not in d or "score" not in d:
            return False
    return True


def _parse_json(raw: str) -> dict:
    cleaned = _fix_trailing_commas(_extract_first_json_object(_strip_fences(raw)))
    data = json.loads(cleaned)
    unwrapped = _unwrap_if_needed(data)
    if not _is_valid_output(unwrapped):
        raise ValueError("Parsed JSON does not match expected output schema")
    return unwrapped


_RETRY_SUFFIX = (
    "\n\nIMPORTANT: Your previous response was not valid JSON. "
    "Respond with ONLY a valid JSON object — no text before or after, no markdown fences. "
    "Start your response with { and end with }."
)


def _build_fallback(bundle: EvidenceBundle) -> dict:
    """
    Build a minimal analysis dict from the bundle signals alone.
    Used when the LLM fails to generate valid JSON after retries.
    """
    from models.evidence import Dimension

    ats = bundle.ats
    ats_str = ats.ats_name if ats.ats_name else "Unknown"

    # Derive company size and industry from signals
    size_str = ""
    industry_str = ""
    for s in bundle.signals:
        if not size_str and "employees" in s.content.lower() and s.source_type in ("linkedin", "job_posting"):
            m = re.search(r"([\d,]+[\+,–\-]+[\d,]+|[\d,]+\+?)\s*employees", s.content, re.I)
            if m:
                size_str = m.group(1) + " employees"
        if not industry_str and s.source_type == "linkedin":
            # LinkedIn snippets contain "· Industry Name ·" in raw_snippet
            for field in (s.raw_snippet, s.content):
                m = re.search(r"·\s*([A-Z][^·\n]{3,40})\s*·", field)
                if m:
                    candidate = m.group(1).strip()
                    if not re.search(r"\d", candidate):  # skip employee counts
                        industry_str = candidate
                        break

    dim_template = {
        "score": 50,
        "currentState": "Insufficient data to synthesize — see raw signals.",
        "evidence": [],
        "gaps": ["Synthesis failed; review raw evidence bundle."],
        "coverage": "inferred",
    }

    def dim_data(dim: Dimension) -> dict:
        sigs = [s for s in bundle.signals if s.dimension == dim]
        cov = next((c for c in bundle.coverage if c.dimension == dim), None)
        score = int((cov.score if cov else 0.0) * 100)
        evidence = [f"{s.content} — {s.source_url}" for s in sigs[:3]]
        return {
            "score": score,
            "currentState": sigs[0].content if sigs else "No signals found.",
            "evidence": evidence,
            "gaps": ["Synthesis unavailable — consult raw evidence."],
            "coverage": "high" if score >= 60 else "medium" if score >= 30 else "inferred",
        }

    return {
        "company": bundle.company_name,
        "industry": industry_str,
        "companySize": size_str,
        "description": "",
        "revenueHistory": [],
        "detectedStack": {
            "ats": ats_str,
            "confidence": ats.confidence,
            "source": ats.evidence_url,
        },
        "dimensions": {
            "hiring": dim_data(Dimension.HIRING),
            "onboarding": dim_data(Dimension.ONBOARDING),
            "retention": dim_data(Dimension.RETENTION),
            "people_analytics": dim_data(Dimension.PEOPLE_ANALYTICS),
            "hrit": dim_data(Dimension.HRIT),
            "internal_mobility": dim_data(Dimension.INTERNAL_MOBILITY),
        },
        "solutionPrototypes": [],
        "topOpportunity": "Synthesis failed — review raw signals and re-run.",
        "pitch": {
            "hook": "Synthesis failed.",
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "roi": "",
            "cta": "",
        },
    }


def synthesize(bundle: EvidenceBundle, provider: LLMProvider) -> dict:
    system = build_system_prompt()
    user = build_user_message(bundle)
    schema = build_output_schema()

    raw = provider.generate(system, user, format_schema=schema)

    try:
        return _parse_json(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    # Retry once with explicit JSON reminder
    try:
        raw2 = provider.generate(system, user + _RETRY_SUFFIX, format_schema=schema)
        return _parse_json(raw2)
    except (json.JSONDecodeError, ValueError):
        pass

    # Both attempts failed — return minimal fallback from signals
    return _build_fallback(bundle)
