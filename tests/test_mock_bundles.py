import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from search.mock_search import MockSearchProvider
from models.evidence import Dimension


COMPANIES = ["HubSpot", "ServiceNow", "Wayfair", "Marriott International"]


@pytest.mark.parametrize("company", COMPANIES)
def test_bundle_loads(company):
    bundle = MockSearchProvider().search_company(company)
    assert bundle.company_name
    assert len(bundle.signals) >= 5
    assert bundle.is_mock is True


@pytest.mark.parametrize("company", COMPANIES)
def test_bundle_has_ats(company):
    bundle = MockSearchProvider().search_company(company)
    assert bundle.ats.ats_name is not None
    assert bundle.ats.confidence > 0.5


@pytest.mark.parametrize("company", COMPANIES)
def test_all_dimensions_covered(company):
    bundle = MockSearchProvider().search_company(company)
    covered = {s.dimension for s in bundle.signals}
    # At minimum HRIT and HIRING should always have signals
    assert Dimension.HRIT in covered
    assert Dimension.HIRING in covered


@pytest.mark.parametrize("company", COMPANIES)
def test_coverage_scores_populated(company):
    bundle = MockSearchProvider().search_company(company)
    assert len(bundle.coverage) == len(Dimension)
    for cov in bundle.coverage:
        assert 0.0 <= cov.score <= 1.0


@pytest.mark.parametrize("company", COMPANIES)
def test_all_signals_have_source_url(company):
    bundle = MockSearchProvider().search_company(company)
    for sig in bundle.signals:
        assert sig.source_url, f"Signal {sig.signal_type} missing source_url"


def test_fuzzy_match_marriott():
    bundle = MockSearchProvider().search_company("marriott")
    assert "Marriott" in bundle.company_name


def test_unknown_company_raises():
    with pytest.raises(ValueError, match="No mock data"):
        MockSearchProvider().search_company("Nonexistent Corp XYZ")
