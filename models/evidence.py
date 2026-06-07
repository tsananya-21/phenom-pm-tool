from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Dimension(str, Enum):
    HIRING = "hiring"
    ONBOARDING = "onboarding"
    RETENTION = "retention"
    PEOPLE_ANALYTICS = "people_analytics"
    HRIT = "hrit"
    INTERNAL_MOBILITY = "internal_mobility"


class Signal(BaseModel):
    source_url: str
    source_type: str  # job_posting | careers_site | linkedin | glassdoor | review | news | filing
    dimension: Dimension
    signal_type: str  # ats_detection | hiring_volume | glassdoor_rating | chro_change | ...
    content: str       # human-readable extracted fact
    raw_snippet: str   # verbatim text from source, max 500 chars
    confidence: float  # 0.0–1.0
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ATSDetection(BaseModel):
    ats_name: Optional[str] = None   # "Workday" | "Greenhouse" | "Lever" | ... | None
    evidence_url: Optional[str] = None
    detection_method: str = "none"   # apply_url | markup | meta_tag | inferred | none
    confidence: float = 0.0


class CoverageScore(BaseModel):
    dimension: Dimension
    score: float        # 0.0–1.0
    signal_count: int
    is_thin: bool       # True if score < 0.3
    thin_reason: Optional[str] = None


class EvidenceBundle(BaseModel):
    company_name: str
    domain: Optional[str] = None
    sources_attempted: list[str] = Field(default_factory=list)
    sources_fetched: list[str] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)
    ats: ATSDetection = Field(default_factory=ATSDetection)
    coverage: list[CoverageScore] = Field(default_factory=list)
    is_mock: bool = False
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def signals_for(self, dimension: Dimension) -> list[Signal]:
        return [s for s in self.signals if s.dimension == dimension]

    def coverage_for(self, dimension: Dimension) -> Optional[CoverageScore]:
        for c in self.coverage:
            if c.dimension == dimension:
                return c
        return None
