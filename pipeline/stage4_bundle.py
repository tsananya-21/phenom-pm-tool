"""
Stage 4 — Evidence Bundle Assembly

Takes raw search results + fetched pages + extracted signals and assembles
the final EvidenceBundle. Deduplicates signals by (source_url, signal_type).
"""
from __future__ import annotations

from models.evidence import ATSDetection, EvidenceBundle, Signal
from ats.detector import detect, detect_from_urls
from pipeline.stage5_coverage import score_coverage


def assemble_bundle(
    company_name: str,
    domain: str | None,
    all_signals: list[Signal],
    fetched_urls: list[str],
    attempted_urls: list[str],
    fetched_pages: dict,  # url -> ParsedPage
    job_urls: list[str],
) -> EvidenceBundle:
    # Deduplicate signals
    seen: set[tuple[str, str]] = set()
    unique_signals: list[Signal] = []
    for sig in all_signals:
        key = (sig.source_url, sig.signal_type)
        if key not in seen:
            seen.add(key)
            unique_signals.append(sig)

    # ATS detection: run across all job URLs + fetched HTML
    ats = detect_from_urls(job_urls)
    if ats.ats_name is None:
        # Try markup pass on fetched pages
        for url, page in fetched_pages.items():
            if hasattr(page, "raw_html") and page.raw_html:
                candidate = detect(url, page.raw_html)
                if candidate.ats_name:
                    ats = candidate
                    break

    # Inject ATS signal if detected and not already in signals
    if ats.ats_name:
        ats_key = (ats.evidence_url or "", "ats_detection")
        if ats_key not in {(s.source_url, s.signal_type) for s in unique_signals}:
            from models.evidence import Dimension
            unique_signals.append(Signal(
                source_url=ats.evidence_url or "",
                source_type="job_posting",
                dimension=Dimension.HRIT,
                signal_type="ats_detection",
                content=f"ATS detected: {ats.ats_name} via {ats.detection_method}",
                raw_snippet=f"{ats.evidence_url} — {ats.detection_method}",
                confidence=ats.confidence,
            ))

    coverage = score_coverage(unique_signals)

    return EvidenceBundle(
        company_name=company_name,
        domain=domain,
        sources_attempted=attempted_urls,
        sources_fetched=fetched_urls,
        signals=unique_signals,
        ats=ats,
        coverage=coverage,
        is_mock=False,
    )
