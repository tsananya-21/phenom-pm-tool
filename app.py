"""
Phenom Forward-Deployed PM Intelligence Tool
"""
from __future__ import annotations

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from config.settings import load_config
from models.evidence import Dimension, EvidenceBundle
from search.base import get_search_provider
from search.mock_search import MockSearchProvider
from providers.base import get_llm_provider
from synthesis.synthesizer import synthesize

st.set_page_config(
    page_title="Phenom PM Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []   # list of {company, timestamp, fit_score, bundle, analysis}
if "current" not in st.session_state:
    st.session_state.current = None # {bundle, analysis}

# ── Cached resources ──────────────────────────────────────────────────────────
@st.cache_resource
def _get_config():
    return load_config()

@st.cache_resource
def _get_providers():
    cfg = _get_config()
    return get_search_provider(cfg), get_llm_provider(cfg)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_100(v) -> int:
    if v is None:
        return 0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0
    return int(f) if f > 1 else int(f * 100)

def _coverage_label(cov: str) -> str:
    return {
        "high":     "Strong evidence",
        "medium":   "Moderate evidence",
        "low":      "Limited data",
        "inferred": "Inferred — low confidence",
    }.get((cov or "").lower(), cov or "—")

def _bullet(item) -> str:
    if isinstance(item, dict):
        product = item.get("phenomProduct") or item.get("product") or ""
        desc = item.get("description") or item.get("whatItDoes") or str(item)
        return f"**{product}** — {desc}" if product else desc
    return str(item)

def _fit_score(analysis: dict) -> int:
    dims = analysis.get("dimensions", {})
    if not dims:
        return 50
    scores = [_to_100(d.get("score", 50)) for d in dims.values()]
    avg = sum(scores) / len(scores)
    # Lower maturity = higher Phenom fit (more room to add value)
    return min(100, max(10, round(110 - avg * 0.6)))

def _fit_label(score: int) -> str:
    if score >= 80:
        return "Strong fit"
    if score >= 65:
        return "Good fit"
    if score >= 50:
        return "Moderate fit"
    return "Weak fit"

def _run_research(company: str) -> None:
    search_provider, llm_provider = _get_providers()
    with st.spinner(f"Researching {company}..."):
        try:
            bundle = search_provider.search_company(company.strip())
        except ValueError as e:
            st.error(str(e))
            return
    with st.spinner("Synthesizing analysis..."):
        try:
            analysis = synthesize(bundle, llm_provider)
        except RuntimeError as e:
            st.error(f"Synthesis failed: {e}")
            return

    fit = _fit_score(analysis)
    st.session_state.current = {"bundle": bundle, "analysis": analysis}
    # Deduplicate history by company name, most recent first
    st.session_state.history = [
        h for h in st.session_state.history
        if h["company"].lower() != bundle.company_name.lower()
    ]
    st.session_state.history.insert(0, {
        "company": bundle.company_name,
        "timestamp": datetime.datetime.now().strftime("%b %d, %H:%M"),
        "fit_score": fit,
        "bundle": bundle,
        "analysis": analysis,
    })
    st.rerun()

def _build_export(company: str, analysis: dict, bundle: EvidenceBundle, notes: str) -> str:
    lines = [f"# {company} — Phenom Intelligence Report", ""]
    industry = analysis.get("industry", "")
    size = analysis.get("companySize", "")
    if industry or size:
        lines += [f"**{industry}** · {size}", ""]
    stack = analysis.get("detectedStack", {})
    if stack.get("ats"):
        lines += [f"ATS: {stack['ats']} ({_to_100(stack.get('confidence', 0))}% confidence)", ""]
    top = analysis.get("topOpportunity", "")
    if top:
        lines += [f"**Top opportunity:** {top}", ""]
    lines += ["---", "## Talent Operations", ""]
    dims = analysis.get("dimensions", {})
    for key, d in dims.items():
        label = key.replace("_", " ").title()
        score = _to_100(d.get("score"))
        lines += [f"### {label} — {score}/100", d.get("currentState", ""), ""]
        for g in d.get("gaps", []):
            lines.append(f"- {g}")
        lines.append("")
    pitch = analysis.get("pitch", {})
    lines += ["---", "## Summary", ""]
    if pitch.get("strengths"):
        lines += ["**Doing well:**"] + [f"- {_bullet(s)}" for s in pitch["strengths"]] + [""]
    if pitch.get("weaknesses"):
        lines += ["**Can do better:**"] + [f"- {_bullet(w)}" for w in pitch["weaknesses"]] + [""]
    if pitch.get("opportunities"):
        lines += ["**Opportunity:**"] + [f"- {_bullet(o)}" for o in pitch["opportunities"]] + [""]
    fit = _fit_score(analysis)
    lines += [f"**Phenom Fit Score:** {fit}/100 — {_fit_label(fit)}", "", "---", "## Sales Pitch", ""]
    if pitch.get("hook"):
        lines += [f"*{pitch['hook']}*", ""]
    for p in analysis.get("solutionPrototypes", []):
        lines += [f"**{p.get('phenomProduct', '')}**", p.get("whatItDoes", "")]
        if p.get("successMetric"):
            lines.append(f"*{p['successMetric']}*")
        lines.append("")
    if pitch.get("roi"):
        lines += [f"**ROI:** {pitch['roi']}", ""]
    if pitch.get("cta"):
        lines += [f"**Next step:** {pitch['cta']}", ""]
    if notes.strip():
        lines += ["---", "## Notes", "", notes]
    return "\n".join(lines)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    cfg = _get_config()
    st.markdown("**Phenom PM Intelligence**")
    mode = f"{cfg.llm_provider} · {'mock data' if cfg.search_provider == 'mock' else 'live research'}"
    st.caption(mode)

    if st.session_state.history:
        st.divider()
        st.markdown("**Past searches**")
        for h in st.session_state.history:
            fit = h["fit_score"]
            col_btn, col_fit = st.columns([3, 1])
            if col_btn.button(h["company"], key=f"hist_{h['company']}", use_container_width=True):
                st.session_state.current = {"bundle": h["bundle"], "analysis": h["analysis"]}
                st.rerun()
            col_fit.caption(f"{fit}/100")
            st.caption(h["timestamp"])

    st.divider()
    st.caption("Set `PHENOM_SEARCH_PROVIDER=tavily` and `PHENOM_LLM_PROVIDER=anthropic` for live mode.")


# ── Home state (no results yet) ───────────────────────────────────────────────
current = st.session_state.current

if current is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("## Phenom PM Intelligence")
        st.markdown("Research a prospect's talent operations and generate a tailored sales pitch.")
        st.markdown("")
        company_input = st.text_input(
            "company",
            label_visibility="collapsed",
            placeholder="Enter a company name...",
        )
        if st.button("Research", type="primary", use_container_width=True, disabled=not (company_input or "").strip()):
            _run_research(company_input.strip())

        st.markdown("")
        st.caption("Try one of these:")
        rec_cols = st.columns(len(MockSearchProvider.available_companies()))
        for i, name in enumerate(MockSearchProvider.available_companies()):
            if rec_cols[i].button(name, use_container_width=True, key=f"rec_{name}"):
                _run_research(name)


# ── Results state ─────────────────────────────────────────────────────────────
else:
    bundle: EvidenceBundle = current["bundle"]
    analysis: dict = current["analysis"]
    company = analysis.get("company", bundle.company_name)
    dims = analysis.get("dimensions", {})
    prototypes = analysis.get("solutionPrototypes", [])
    pitch = analysis.get("pitch", {})

    # Derive pitch fallback when model omits it
    if not pitch or not any(pitch.get(k) for k in ("strengths", "weaknesses", "opportunities")):
        pitch = pitch or {}
        if not pitch.get("strengths"):
            pitch["strengths"] = [
                v.get("currentState", "")
                for v in dims.values()
                if v.get("coverage") in ("high", "medium") and v.get("currentState") and not v.get("gaps")
            ][:4]
        if not pitch.get("weaknesses"):
            pitch["weaknesses"] = [g for v in dims.values() for g in v.get("gaps", [])][:4]
        if not pitch.get("opportunities"):
            pitch["opportunities"] = [
                f"{p.get('phenomProduct')}: {p.get('whatItDoes', '')}"
                for p in prototypes if p.get("phenomProduct")
            ][:4]

    fit = _fit_score(analysis)
    industry = analysis.get("industry", "")
    size = analysis.get("companySize", "")
    stack = analysis.get("detectedStack", {})

    # ── Company overview ──────────────────────────────────────────────────────
    top_left, top_right = st.columns([4, 1])
    with top_left:
        st.markdown(f"## {company}")
        meta = " · ".join(p for p in [industry, size] if p)
        if meta:
            st.caption(meta)
        if bundle.is_mock:
            st.caption("Using offline mock data")
    with top_right:
        st.metric("Phenom Fit", f"{fit} / 100", delta=_fit_label(fit), delta_color="off")

    if stack.get("ats"):
        conf = _to_100(stack.get("confidence", 0))
        st.info(f"ATS: **{stack['ats']}** — detected with {conf}% confidence")

    top_opp = analysis.get("topOpportunity", "")
    if top_opp:
        st.success(f"Top opportunity: {top_opp}")

    news_signals = [s for s in bundle.signals if s.source_type in ("news", "filing")]
    if news_signals:
        with st.expander("Latest news & signals"):
            for s in news_signals[:6]:
                st.markdown(f"- {s.content}")

    st.divider()

    # ── Talent operations (2×2 cards) ─────────────────────────────────────────
    MAIN_DIMS = [
        ("hiring",    "How They Hire"),
        ("onboarding","Onboarding"),
        ("hrit",      "HRIT Tools"),
        ("retention", "Employee Retention"),
    ]
    EXTRA_DIMS = [
        ("people_analytics", "People Analytics"),
        ("internal_mobility","Internal Mobility"),
    ]

    st.subheader("Talent Operations")
    left_col, right_col = st.columns(2)
    card_cols = [left_col, right_col, left_col, right_col]

    for i, (key, label) in enumerate(MAIN_DIMS):
        d = dims.get(key, {})
        score = _to_100(d.get("score"))
        color = "green" if score >= 70 else "orange" if score >= 40 else "red"
        with card_cols[i]:
            with st.container(border=True):
                score_col, label_col = st.columns([1, 2])
                score_col.markdown(f":{color}[**{score}/100**]")
                score_col.caption(_coverage_label(d.get("coverage", "")))
                label_col.markdown(f"**{label}**")
                label_col.markdown(d.get("currentState", "*No data.*"))
                gaps = d.get("gaps", [])
                if gaps:
                    st.markdown("**Gaps:**")
                    for g in gaps:
                        st.markdown(f"- {g}")

    extra = [(k, lbl) for k, lbl in EXTRA_DIMS if k in dims]
    if extra:
        with st.expander("Additional dimensions"):
            for key, label in extra:
                d = dims[key]
                score = _to_100(d.get("score"))
                st.markdown(f"**{label}** — {score}/100")
                st.markdown(d.get("currentState", ""))
                for g in d.get("gaps", []):
                    st.markdown(f"- {g}")
                st.markdown("")

    st.divider()

    # ── Summary ───────────────────────────────────────────────────────────────
    st.subheader("Summary")
    col_well, col_better, col_opp = st.columns(3)
    with col_well:
        st.markdown("**Doing well**")
        for item in pitch.get("strengths", []):
            st.markdown(f"- {_bullet(item)}")
    with col_better:
        st.markdown("**Can do better**")
        for item in pitch.get("weaknesses", []):
            st.markdown(f"- {_bullet(item)}")
    with col_opp:
        st.markdown("**Opportunity**")
        for item in pitch.get("opportunities", []):
            st.markdown(f"- {_bullet(item)}")

    st.markdown("")
    fit_col, _ = st.columns([1, 3])
    fit_col.metric("Phenom Fit Score", f"{fit} / 100", delta=_fit_label(fit), delta_color="off")

    st.divider()

    # ── Sales pitch ───────────────────────────────────────────────────────────
    st.subheader("Sales Pitch")
    hook = pitch.get("hook", "")
    if hook:
        st.markdown(f"*{hook}*")
        st.markdown("")

    high_protos = [p for p in prototypes if p.get("priority") == "high"]
    other_protos = [p for p in prototypes if p.get("priority") != "high"]
    for proto in high_protos + other_protos:
        priority = proto.get("priority", "medium")
        prefix = "[High priority] " if priority == "high" else ""
        with st.expander(
            f"{prefix}{proto.get('phenomProduct', '')} — {proto.get('gap', '')}",
            expanded=(priority == "high"),
        ):
            st.markdown(proto.get("whatItDoes", ""))
            if proto.get("successMetric"):
                st.caption(f"Success metric: {proto['successMetric']}")

    roi = pitch.get("roi", "")
    cta = pitch.get("cta", "")
    if roi:
        st.info(f"**ROI:** {roi}")
    if cta:
        st.success(f"**Next step:** {cta}")

    st.divider()

    # ── Evidence coverage (small) ─────────────────────────────────────────────
    with st.expander(f"Evidence coverage  ({len(bundle.signals)} signals)"):
        cov_cols = st.columns(len(bundle.coverage))
        for i, cov in enumerate(bundle.coverage):
            lbl = cov.dimension.value.replace("_", " ").title()
            cov_cols[i].metric(lbl, f"{int(cov.score * 100)}/100", delta=f"{cov.signal_count} signals", delta_color="off")
            if cov.is_thin:
                cov_cols[i].caption(f"Low — {cov.thin_reason}")

    st.divider()

    # ── Notes ─────────────────────────────────────────────────────────────────
    st.subheader("Notes")
    notes_key = f"notes_{bundle.company_name.lower().replace(' ', '_')}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = ""
    st.text_area(
        "notes",
        key=notes_key,
        height=120,
        placeholder="Add your notes, talking points, or follow-up actions here...",
        label_visibility="collapsed",
    )

    st.divider()

    # ── Export ────────────────────────────────────────────────────────────────
    notes_text = st.session_state.get(notes_key, "")
    report_md = _build_export(company, analysis, bundle, notes_text)
    filename = f"{company.lower().replace(' ', '_')}_phenom_report.md"
    dl_col, _ = st.columns([1, 3])
    dl_col.download_button(
        "Export report",
        data=report_md,
        file_name=filename,
        mime="text/markdown",
    )

    # ── Search another company ────────────────────────────────────────────────
    st.divider()
    _, bottom_center, _ = st.columns([1, 2, 1])
    with bottom_center:
        new_company = st.text_input(
            "search_another",
            label_visibility="collapsed",
            placeholder="Search another company...",
        )
        if st.button("Research", type="primary", key="btn_another", use_container_width=True,
                     disabled=not (new_company or "").strip()):
            _run_research(new_company.strip())
