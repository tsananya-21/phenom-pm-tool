"""
Prompt templates for the single synthesis model call.

The system prompt injects the Phenom product catalog (static config).
The user message injects the EvidenceBundle as structured JSON.
The model is instructed to output strict JSON matching the output schema.
"""
from __future__ import annotations

import json
from pathlib import Path

from models.evidence import EvidenceBundle

_CATALOG_PATH = Path(__file__).parent.parent / "config" / "phenom_catalog.json"


def _load_catalog() -> str:
    with open(_CATALOG_PATH) as f:
        return json.dumps(json.load(f), indent=2)


SYSTEM_PROMPT_TEMPLATE = """\
You are a senior solutions consultant at Phenom, an intelligent talent experience platform.
Write like a sharp, confident human consultant — not a template filler. Use plain, \
direct English. No buzzword padding, no "leverage synergies", no hollow filler phrases. \
Every sentence should say something specific about THIS company.

YOUR TASK: Read the EVIDENCE INPUT in the user message, then write a NEW JSON object \
in the OUTPUT SCHEMA defined below. Do NOT copy or echo the input data — generate \
a fresh analysis and pitch based on it.

## Phenom Product Catalog
{catalog}

## Output Requirements
Respond with ONLY a single valid JSON object — no markdown fences, no explanation, no preamble.
Use exactly this schema:

{{
  "company": "<string>",
  "industry": "<string>",
  "companySize": "<string: e.g. '7,000–10,000 employees'>",
  "description": "<2 sentences: what this company does and what market they serve>",
  "revenueHistory": [
    {{"period": "<e.g. Q1 2024>", "amount": "<e.g. $617M>"}}
  ],
  "detectedStack": {{
    "ats": "<string or null>",
    "confidence": <float 0-1>,
    "source": "<url or null>"
  }},
  "dimensions": {{
    "hiring":            {{"score": <integer 0-100>, "currentState": "<2-3 natural sentences describing what hiring looks like here>", "evidence": ["<specific fact — source_url>"], "gaps": ["<concrete gap as a full sentence>"], "coverage": "<high|medium|low|inferred>"}},
    "onboarding":        {{"score": <integer 0-100>, "currentState": "<2-3 natural sentences>", "evidence": ["<specific fact — source_url>"], "gaps": ["<concrete gap as a full sentence>"], "coverage": "<high|medium|low|inferred>"}},
    "retention":         {{"score": <integer 0-100>, "currentState": "<2-3 natural sentences>", "evidence": ["<specific fact — source_url>"], "gaps": ["<concrete gap as a full sentence>"], "coverage": "<high|medium|low|inferred>"}},
    "people_analytics":  {{"score": <integer 0-100>, "currentState": "<2-3 natural sentences>", "evidence": ["<specific fact — source_url>"], "gaps": ["<concrete gap as a full sentence>"], "coverage": "<high|medium|low|inferred>"}},
    "hrit":              {{"score": <integer 0-100>, "currentState": "<2-3 natural sentences>", "evidence": ["<specific fact — source_url>"], "gaps": ["<concrete gap as a full sentence>"], "coverage": "<high|medium|low|inferred>"}},
    "internal_mobility": {{"score": <integer 0-100>, "currentState": "<2-3 natural sentences>", "evidence": ["<specific fact — source_url>"], "gaps": ["<concrete gap as a full sentence>"], "coverage": "<high|medium|low|inferred>"}}
  }},
  "solutionPrototypes": [
    {{
      "phenomProduct": "<exact product name from catalog>",
      "gap": "<the specific gap this addresses, as a plain sentence>",
      "evidenceRef": "<source_url from the evidence>",
      "whatItDoes": "<2-3 natural sentences: what Phenom would concretely do for THIS company, not generic>",
      "successMetric": "<specific, measurable outcome for this company, e.g. 'Cut time-to-fill for hourly roles from 3 weeks to under 7 days'>",
      "priority": "<high|medium|low>"
    }}
  ],
  "topOpportunity": "<1 punchy sentence naming the single strongest opening, specific to this company>",
  "pitch": {{
    "hook":          "<1 sentence that opens with something specific about their situation — not a generic opener>",
    "strengths":     ["<full sentence: one thing they're doing well, grounded in evidence>"],
    "weaknesses":    ["<full sentence: one concrete gap or problem, grounded in evidence>"],
    "opportunities": ["<Product Name>: one sentence on what it would change for them specifically>"],
    "roi":           "<2 sentences with a specific metric or benchmark, not vague 'improve efficiency'>",
    "cta":           "<specific, actionable next step — name a role, a workshop, a pilot>"
  }}
}}

## Critical Rules
1. OUTPUT SCHEMA ONLY — your entire response must be a single JSON object matching the schema above. \
   Do not return the input data. Do not include any text outside the JSON object.
2. Every claim in dimensions[].evidence[] MUST reference a real source_url from the evidence bundle.
3. If a dimension's coverage_score is below 0.3 (is_thin=true), set coverage to "inferred" \
and use hedging language ("likely", "insufficient public data") — do NOT assert confidence you don't have.
4. solutionPrototypes must name exact products from the catalog above.
5. Minimum 2 solutionPrototypes. Prioritize the gaps with the most evidence.
6. pitch.strengths: 2–4 bullets of what the company is already doing well (backed by evidence).
7. pitch.weaknesses: 2–4 bullets of concrete gaps or problems (backed by evidence).
8. pitch.opportunities: 2–4 plain strings, each formatted as "Product Name: one sentence". No nested objects.
"""


def build_system_prompt() -> str:
    catalog = _load_catalog()
    return SYSTEM_PROMPT_TEMPLATE.format(catalog=catalog)


# JSON Schema mirroring the OUTPUT SCHEMA above. Passed to Ollama as `format` so
# decoding is grammar-constrained to this exact shape — small models can no longer
# echo input-bundle keys (e.g. "strong"/"thin") into the dimension objects.
def _dimension_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "score": {"type": "integer"},
            "currentState": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "gaps": {"type": "array", "items": {"type": "string"}},
            "coverage": {"type": "string", "enum": ["high", "medium", "low", "inferred"]},
        },
        "required": ["score", "currentState", "evidence", "gaps", "coverage"],
        "additionalProperties": False,
    }


def build_output_schema() -> dict:
    dim = _dimension_schema()
    dim_keys = ["hiring", "onboarding", "retention", "people_analytics", "hrit", "internal_mobility"]
    return {
        "type": "object",
        "properties": {
            "company": {"type": "string"},
            "industry": {"type": "string"},
            "companySize": {"type": "string"},
            "description": {"type": "string"},
            "revenueHistory": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"period": {"type": "string"}, "amount": {"type": "string"}},
                    "required": ["period", "amount"],
                },
            },
            "detectedStack": {
                "type": "object",
                "properties": {
                    "ats": {"type": ["string", "null"]},
                    "confidence": {"type": "number"},
                    "source": {"type": ["string", "null"]},
                },
                "required": ["ats", "confidence", "source"],
            },
            "dimensions": {
                "type": "object",
                "properties": {k: dim for k in dim_keys},
                "required": dim_keys,
                "additionalProperties": False,
            },
            "solutionPrototypes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "phenomProduct": {"type": "string"},
                        "gap": {"type": "string"},
                        "evidenceRef": {"type": "string"},
                        "whatItDoes": {"type": "string"},
                        "successMetric": {"type": "string"},
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["phenomProduct", "gap", "whatItDoes", "successMetric", "priority"],
                },
            },
            "topOpportunity": {"type": "string"},
            "pitch": {
                "type": "object",
                "properties": {
                    "hook": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}},
                    "opportunities": {"type": "array", "items": {"type": "string"}},
                    "roi": {"type": "string"},
                    "cta": {"type": "string"},
                },
                "required": ["hook", "strengths", "weaknesses", "opportunities", "roi", "cta"],
            },
        },
        "required": [
            "company", "industry", "companySize", "description", "detectedStack",
            "dimensions", "solutionPrototypes", "topOpportunity", "pitch",
        ],
    }


def build_user_message(bundle: EvidenceBundle) -> str:
    """
    Convert EvidenceBundle to a natural-language briefing document.
    Small local models handle 'summarize this text into JSON' far better than
    'transform this JSON into different JSON', so we avoid sending raw JSON as input.
    """
    thin_dims = {c.dimension.value for c in bundle.coverage if c.is_thin}
    cov_map = {c.dimension.value: c for c in bundle.coverage}

    lines: list[str] = []
    lines.append(f"PROSPECT: {bundle.company_name}" + (f" ({bundle.domain})" if bundle.domain else ""))

    if bundle.ats.ats_name:
        lines.append(
            f"ATS: {bundle.ats.ats_name} "
            f"({bundle.ats.confidence:.0%} confidence via {bundle.ats.detection_method}, "
            f"evidence: {bundle.ats.evidence_url})"
        )
    else:
        lines.append("ATS: Unknown — not detected from available sources")

    lines.append("")

    # Group signals by dimension
    dim_order = ["hrit", "hiring", "onboarding", "retention", "people_analytics", "internal_mobility"]
    from models.evidence import Dimension
    dim_map = {d.value: d for d in Dimension}

    for dim_val in dim_order:
        dim = dim_map[dim_val]
        sigs = [s for s in bundle.signals if s.dimension == dim]
        cov = cov_map.get(dim_val)
        if not sigs:
            lines.append(f"{dim_val.upper().replace('_',' ')} — no signals (infer with caution)")
            continue

        coverage_label = "strong" if (cov and cov.score >= 0.6) else \
                         "moderate" if (cov and cov.score >= 0.3) else "low — hedge language required"
        thin_note = " [THIN — use 'likely' / 'insufficient data' language]" if dim_val in thin_dims else ""

        lines.append(f"{dim_val.upper().replace('_',' ')} ({coverage_label}){thin_note}:")
        for s in sigs:
            lines.append(f"  - {s.content} [confidence: {s.confidence:.0%}, source: {s.source_url}]")

    lines.append("")
    lines.append(
        f"THIN DIMENSIONS (low evidence — must hedge): {', '.join(thin_dims) if thin_dims else 'none'}"
    )
    lines.append("")
    lines.append(
        f"Now produce the OUTPUT SCHEMA JSON for {bundle.company_name}. "
        f"Start your response with {{ and end with }}. "
        f"Include at least 2 solutionPrototypes. "
        f"Use exact Phenom product names from the catalog."
    )

    return "\n".join(lines)
