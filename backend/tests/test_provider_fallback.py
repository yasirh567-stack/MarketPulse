"""Unit tests for the market/news provider fallback chains — no network or
FastAPI app needed, just the provider classes directly."""

from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.providers.base import Quote, RawArticle
from app.providers.market import CompositeMarketDataProvider, YFinanceMarketDataProvider
from app.providers.news import CompositeNewsProvider
from app.schemas.common import DataStatus


class _WorkingMarketProvider:
    """A live provider stand-in that always succeeds — used to prove a demo
    ticker (e.g. AAPL) actually reaches the live path when DEMO_MODE=false,
    rather than always being short-circuited to its fixture."""

    name = "working-live"

    def get_quote(self, ticker):
        return Quote(
            ticker=ticker.upper(),
            price=999.99,
            previous_close=900.0,
            change_abs=99.99,
            change_pct=11.11,
            currency="USD",
            market_status=None,
            as_of=datetime.now(UTC),
            data_status=DataStatus.DELAYED,
            source="working-live",
        )

    def get_history(self, ticker, interval, period_days):
        raise NotImplementedError

    def search(self, query):
        raise NotImplementedError


class _WorkingNewsProvider:
    name = "working-live"

    def get_headlines(self, ticker, limit):
        return [
            RawArticle(
                ticker=ticker.upper(),
                title="Live headline",
                summary="A real headline from the live provider.",
                url="https://example.com/live-headline",
                source="working-live",
                published_at=datetime.now(UTC),
                data_status=DataStatus.CACHED,
                is_demo=False,
            )
        ]


class _BrokenMarketProvider:
    name = "broken"

    def get_quote(self, ticker):
        raise RuntimeError("simulated outage")

    def get_history(self, ticker, interval, period_days):
        raise RuntimeError("simulated outage")

    def search(self, query):
        raise RuntimeError("simulated outage")


class _BrokenNewsProvider:
    name = "broken"

    def get_headlines(self, ticker, limit):
        raise RuntimeError("simulated outage")


def test_market_falls_back_to_demo_when_live_provider_down():
    settings = Settings(demo_mode=False)
    provider = CompositeMarketDataProvider(settings, live=_BrokenMarketProvider())
    quote = provider.get_quote("AAPL")
    assert quote.data_status.value == "demo"
    assert quote.source == "demo"


def test_market_raises_for_unknown_ticker_when_live_also_down():
    settings = Settings(demo_mode=False)
    provider = CompositeMarketDataProvider(settings, live=_BrokenMarketProvider())
    with pytest.raises(ValueError):
        provider.get_quote("NOTATICKER")


def test_news_falls_back_to_demo_when_live_provider_down():
    settings = Settings(demo_mode=False)
    provider = CompositeNewsProvider(settings, live=_BrokenNewsProvider())
    articles = provider.get_headlines("AAPL", limit=10)
    assert articles
    assert all(a.is_demo for a in articles)


def test_news_returns_empty_for_unknown_ticker_when_live_down():
    settings = Settings(demo_mode=False)
    provider = CompositeNewsProvider(settings, live=_BrokenNewsProvider())
    assert provider.get_headlines("NOTATICKER", limit=10) == []


def test_bundled_demo_ticker_uses_live_data_when_demo_mode_off_and_live_succeeds():
    """Regression test: AAPL/MSFT/etc. are real tickers that merely also have
    a bundled fixture — with DEMO_MODE=false and a working live provider, the
    LIVE result must win, not the fixture. (Previously a bug made these
    tickers always use the fixture regardless of demo_mode.)"""
    settings = Settings(demo_mode=False)
    provider = CompositeMarketDataProvider(settings, live=_WorkingMarketProvider())
    quote = provider.get_quote("AAPL")
    assert quote.source == "working-live"
    assert quote.data_status == DataStatus.DELAYED
    assert quote.price == 999.99


def test_bundled_demo_ticker_news_uses_live_when_demo_mode_off_and_live_succeeds():
    settings = Settings(demo_mode=False)
    provider = CompositeNewsProvider(settings, live=_WorkingNewsProvider())
    articles = provider.get_headlines("AAPL", limit=10)
    assert articles
    assert all(not a.is_demo for a in articles)
    assert articles[0].title == "Live headline"


def test_demo_mode_never_calls_live_provider():
    """When DEMO_MODE=true, the live provider must not be invoked at all —
    this is the guarantee that lets the app run with zero API keys/network."""

    class _ExplodingIfCalled:
        name = "should-not-be-called"

        def get_quote(self, ticker):
            raise AssertionError("live provider should not be called in demo mode")

        def get_history(self, ticker, interval, period_days):
            raise AssertionError("live provider should not be called in demo mode")

        def search(self, query):
            raise AssertionError("live provider should not be called in demo mode")

    settings = Settings(demo_mode=True)
    provider = CompositeMarketDataProvider(settings, live=_ExplodingIfCalled())
    quote = provider.get_quote("AAPL")
    assert quote.data_status.value == "demo"


class _FakeSearchResponse:
    def __init__(self, quotes):
        self._quotes = quotes

    def raise_for_status(self):
        pass

    def json(self):
        return {"quotes": self._quotes}


def test_live_search_resolves_company_name_to_ticker(monkeypatch):
    """Typing a company name (not the exact ticker) must resolve via Yahoo's
    free search endpoint — this is what lets the app search any stock, not
    just tickers the user already knows."""

    def fake_get(url, params, headers, timeout):
        assert params["q"] == "tesla"
        return _FakeSearchResponse(
            [
                {
                    "symbol": "TSLA",
                    "shortname": "Tesla, Inc.",
                    "quoteType": "EQUITY",
                    "exchange": "NMS",
                },
                {
                    "symbol": "TL0.F",
                    "shortname": "Tesla Inc.",
                    "quoteType": "EQUITY",
                    "exchange": "FRA",
                },
                {
                    "symbol": "TSLAUSD",
                    "shortname": "Some ETF",
                    "quoteType": "ETF",
                    "exchange": "PCX",
                },
            ]
        )

    monkeypatch.setattr("httpx.get", fake_get)
    provider = YFinanceMarketDataProvider()
    results = provider.search("tesla")
    tickers = [r.ticker for r in results]
    assert "TSLA" in tickers
    assert "TL0.F" in tickers
    assert "TSLAUSD" not in tickers  # non-equity quote types are excluded
    tsla = next(r for r in results if r.ticker == "TSLA")
    assert tsla.name == "Tesla, Inc."
    assert tsla.exchange == "NMS"


def test_live_search_falls_back_to_direct_quote_for_exact_ticker(monkeypatch):
    """If Yahoo's search endpoint is unreachable, an exact ticker the user
    typed must still resolve via a direct quote lookup."""

    def fake_get(url, params, headers, timeout):
        raise RuntimeError("search endpoint unreachable")

    monkeypatch.setattr("httpx.get", fake_get)
    monkeypatch.setattr(
        YFinanceMarketDataProvider,
        "get_quote",
        lambda self, ticker: Quote(
            ticker=ticker.upper(),
            price=1.0,
            previous_close=1.0,
            change_abs=0.0,
            change_pct=0.0,
            currency="USD",
            market_status=None,
            as_of=datetime.now(UTC),
            data_status=DataStatus.DELAYED,
            source="yfinance",
        ),
    )
    provider = YFinanceMarketDataProvider()
    results = provider.search("NVDA")
    assert [r.ticker for r in results] == ["NVDA"]
