"""Tests for the Buffett Indicator macro feature: provider fallback,
percentile/interpretation logic, caching, and the API endpoint."""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.config import Settings
from app.providers.macro import (
    BuffettIndicatorData,
    CompositeBuffettIndicatorProvider,
    DemoBuffettIndicatorProvider,
    QuarterlyRatio,
)
from app.schemas.common import DataStatus
from app.services.macro_service import _interpretation, _percentile_rank, get_buffett_indicator


def test_demo_provider_returns_sorted_historical_series_and_demo_status():
    provider = DemoBuffettIndicatorProvider()
    data = provider.get()
    assert data.data_status == DataStatus.DEMO
    assert data.source == "demo"
    assert len(data.historical) > 0
    dates = [p.quarter_end for p in data.historical]
    assert dates == sorted(dates)
    assert data.current_ratio_pct == data.historical[-1].ratio_pct


def test_composite_uses_demo_when_no_live_configured():
    settings = Settings(demo_mode=False, enable_fred=False)
    provider = CompositeBuffettIndicatorProvider(settings)
    data = provider.get()
    assert data.data_status == DataStatus.DEMO


def test_composite_uses_demo_when_demo_mode_on_even_if_live_configured():
    class _ExplodingLive:
        name = "should-not-be-called"

        def get(self):
            raise AssertionError("live provider should not be called in demo mode")

    settings = Settings(demo_mode=True, enable_fred=True, fred_api_key="fake-key")
    provider = CompositeBuffettIndicatorProvider(settings, live=_ExplodingLive())
    data = provider.get()
    assert data.data_status == DataStatus.DEMO


def test_composite_uses_live_when_demo_mode_off_and_live_succeeds():
    class _WorkingLive:
        name = "fred"

        def get(self):
            return BuffettIndicatorData(
                current_ratio_pct=123.4,
                as_of=datetime.now(UTC),
                historical=[QuarterlyRatio(quarter_end=date(2026, 1, 1), ratio_pct=123.4)],
                data_status=DataStatus.CACHED,
                source="fred",
            )

    settings = Settings(demo_mode=False, enable_fred=True, fred_api_key="fake-key")
    provider = CompositeBuffettIndicatorProvider(settings, live=_WorkingLive())
    data = provider.get()
    assert data.source == "fred"
    assert data.current_ratio_pct == 123.4


def test_composite_falls_back_to_demo_when_live_raises():
    class _BrokenLive:
        name = "fred"

        def get(self):
            raise RuntimeError("simulated FRED outage")

    settings = Settings(demo_mode=False, enable_fred=True, fred_api_key="fake-key")
    provider = CompositeBuffettIndicatorProvider(settings, live=_BrokenLive())
    data = provider.get()
    assert data.data_status == DataStatus.DEMO


def test_percentile_rank_known_values():
    history = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert _percentile_rank(50.0, history) == 100.0
    assert _percentile_rank(10.0, history) == 20.0
    assert _percentile_rank(0.0, history) == 0.0


def test_percentile_rank_empty_history_defaults_to_midpoint():
    assert _percentile_rank(100.0, []) == 50.0


def test_interpretation_buckets_are_distinct():
    high = _interpretation(95)
    mid = _interpretation(50)
    low = _interpretation(5)
    assert "elevated" in high
    assert "middle" in mid
    assert "historically low" in low


def test_get_buffett_indicator_caches_result(client, monkeypatch):
    from app.core.config import get_settings
    from app.database.session import get_session_factory

    call_count = {"n": 0}

    class _CountingProvider:
        name = "demo-counting"

        def get(self):
            call_count["n"] += 1
            return BuffettIndicatorData(
                current_ratio_pct=100.0,
                as_of=datetime.now(UTC),
                historical=[QuarterlyRatio(quarter_end=date(2026, 1, 1), ratio_pct=100.0)],
                data_status=DataStatus.DEMO,
                source="demo-counting",
            )

    import app.services.macro_service as macro_service_module

    monkeypatch.setattr(
        macro_service_module,
        "CompositeBuffettIndicatorProvider",
        lambda settings: _CountingProvider(),
    )

    settings = get_settings()
    db = get_session_factory()()
    try:
        first = get_buffett_indicator(db, settings)
        second = get_buffett_indicator(db, settings)
        assert first == second
        assert call_count["n"] == 1  # second call served from cache
    finally:
        db.close()


def test_buffett_indicator_endpoint_returns_valid_response(client):
    resp = client.get("/api/v1/macro/buffett-indicator")
    assert resp.status_code == 200
    body = resp.json()
    assert "current_ratio_pct" in body
    assert "percentile_rank" in body
    assert 0 <= body["percentile_rank"] <= 100
    assert body["data_status"] == "demo"  # DEMO_MODE=true in the test environment
    assert len(body["historical"]) > 0
    assert "not financial advice" in body["disclaimer"]
