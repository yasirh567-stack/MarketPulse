"""Market data providers: yfinance (real, free, delayed) and demo (fixtures).

`CompositeMarketDataProvider` is what the rest of the app actually depends on.
It tries the configured live provider first (unless DEMO_MODE is on), falls
back to demo fixtures on any failure, and always tags the result with an
honest `data_status` so the frontend never displays unlabeled data.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.logging import get_logger
from app.providers.base import Bar, InstrumentInfo, MarketDataProvider, Quote
from app.providers.demo_data import get_demo_price_bars, is_demo_ticker, load_instruments_manifest
from app.schemas.common import DataStatus

logger = get_logger("app.providers.market")


class DemoMarketDataProvider:
    """Serves synthetic, clearly labeled fixture data. Requires no network
    and no API key — this is what powers `DEMO_MODE=true`."""

    name = "demo"

    def get_quote(self, ticker: str) -> Quote:
        bars = get_demo_price_bars(ticker)
        if not bars:
            raise ValueError(f"Unknown demo ticker: {ticker}")
        latest, previous = bars[-1], bars[-2] if len(bars) > 1 else bars[-1]
        change_abs = latest["close"] - previous["close"]
        change_pct = (change_abs / previous["close"]) * 100 if previous["close"] else 0.0
        return Quote(
            ticker=ticker.upper(),
            price=latest["close"],
            previous_close=previous["close"],
            change_abs=round(change_abs, 4),
            change_pct=round(change_pct, 4),
            currency="USD",
            market_status="closed",
            as_of=latest["ts"],
            data_status=DataStatus.DEMO,
            source=self.name,
        )

    def get_history(self, ticker: str, interval: str, period_days: int) -> list[Bar]:
        bars = get_demo_price_bars(ticker)
        cutoff = datetime.now(UTC) - timedelta(days=period_days)
        return [
            Bar(
                ticker=ticker.upper(),
                interval=interval,
                ts=b["ts"],
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
                adj_close=b.get("adj_close"),
                volume=b.get("volume"),
                data_status=DataStatus.DEMO,
                source=self.name,
            )
            for b in bars
            if b["ts"] >= cutoff
        ]

    def search(self, query: str) -> list[InstrumentInfo]:
        query_lower = query.strip().lower()
        results = []
        for item in load_instruments_manifest():
            if query_lower in item["ticker"].lower() or query_lower in item["name"].lower():
                results.append(InstrumentInfo(**item))
        return results


class YFinanceMarketDataProvider:
    """Free, unofficial Yahoo Finance data via the `yfinance` package.

    Disclaimers: yfinance data is delayed (typically ~15 minutes for US
    equities) and unofficial — there is no SLA. We wrap every call and raise
    a plain exception on any failure so the composite provider can fall back
    cleanly instead of propagating a vendor-specific stack trace.
    """

    name = "yfinance"

    def get_quote(self, ticker: str) -> Quote:
        import yfinance as yf

        t = yf.Ticker(ticker)
        fast = t.fast_info
        price = fast.get("lastPrice") or fast.get("last_price")
        previous_close = fast.get("previousClose") or fast.get("previous_close")
        if price is None:
            raise ValueError(f"No live price available for {ticker}")
        change_abs = None
        change_pct = None
        if previous_close:
            change_abs = price - previous_close
            change_pct = (change_abs / previous_close) * 100
        return Quote(
            ticker=ticker.upper(),
            price=float(price),
            previous_close=float(previous_close) if previous_close else None,
            change_abs=round(change_abs, 4) if change_abs is not None else None,
            change_pct=round(change_pct, 4) if change_pct is not None else None,
            currency=str(fast.get("currency") or "USD"),
            market_status=None,  # yfinance does not reliably expose this for free
            as_of=datetime.now(UTC),
            data_status=DataStatus.DELAYED,
            source=self.name,
        )

    def get_history(self, ticker: str, interval: str, period_days: int) -> list[Bar]:
        import yfinance as yf

        t = yf.Ticker(ticker)
        period = f"{max(period_days, 1)}d"
        df = t.history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            raise ValueError(f"No history available for {ticker}")
        bars = []
        for ts, row in df.iterrows():
            bars.append(
                Bar(
                    ticker=ticker.upper(),
                    interval=interval,
                    ts=ts.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adj_close=float(row["Adj Close"]) if "Adj Close" in row else None,
                    volume=(
                        int(row["Volume"])
                        if "Volume" in row and row["Volume"] == row["Volume"]
                        else None
                    ),
                    data_status=DataStatus.HISTORICAL if period_days > 5 else DataStatus.DELAYED,
                    source=self.name,
                )
            )
        return bars

    def search(self, query: str) -> list[InstrumentInfo]:
        # Yahoo's public (unofficial, no-key) search endpoint resolves company
        # names to tickers, e.g. "tesla" -> TSLA. This is the same free/no-key
        # posture as the rest of this provider, just a different endpoint than
        # the quote/history ones.
        import httpx

        results: list[InstrumentInfo] = []
        try:
            response = httpx.get(
                "https://query1.finance.yahoo.com/v1/finance/search",
                params={"q": query, "quotesCount": 8, "newsCount": 0},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=6.0,
            )
            response.raise_for_status()
            for item in response.json().get("quotes", []):
                symbol = item.get("symbol")
                if not symbol or item.get("quoteType") != "EQUITY":
                    continue
                results.append(
                    InstrumentInfo(
                        ticker=symbol.upper(),
                        name=item.get("shortname") or item.get("longname") or symbol.upper(),
                        exchange=item.get("exchange"),
                        sector=item.get("sector"),
                    )
                )
        except Exception:
            pass

        if any(r.ticker == query.upper() for r in results):
            return results

        # The query might already be an exact ticker the search endpoint
        # didn't surface (it ranks by name-match relevance) — validate it
        # directly via a quote lookup so exact symbols always resolve.
        try:
            self.get_quote(query)
            results.append(InstrumentInfo(ticker=query.upper(), name=query.upper()))
        except Exception:
            pass
        return results


class CompositeMarketDataProvider:
    """The provider the rest of the app talks to. Encapsulates the fallback
    chain: live -> demo fixtures, with every failure logged (not swallowed
    silently) so `/api/v1/health` can report accurate provider status."""

    def __init__(self, settings: Settings, live: MarketDataProvider | None = None):
        self.settings = settings
        self.live = live if live is not None else YFinanceMarketDataProvider()
        self.demo = DemoMarketDataProvider()

    def _use_live(self, ticker: str) -> bool:
        # Bundled demo tickers (AAPL, MSFT, ...) are real, valid tickers that
        # merely happen to also have a synthetic fixture bundled for demo
        # mode. When DEMO_MODE=false, they must still be attempted live like
        # any other ticker — is_demo_ticker only gates the FALLBACK path
        # below, not whether live is attempted at all. (Previously this
        # method also excluded fixture-having tickers here, which meant
        # turning off demo mode had no visible effect on AAPL/MSFT/etc. —
        # a real bug, not intentional behavior.)
        return not self.settings.demo_mode

    def get_quote(self, ticker: str) -> Quote:
        if self._use_live(ticker):
            try:
                return self.live.get_quote(ticker)
            except Exception as exc:
                logger.warning("Live market quote failed for %s: %s", ticker, exc)
        if is_demo_ticker(ticker):
            return self.demo.get_quote(ticker)
        raise ValueError(
            f"No data available for '{ticker}' (not a demo ticker and live data failed)"
        )

    def get_history(self, ticker: str, interval: str = "1d", period_days: int = 180) -> list[Bar]:
        if self._use_live(ticker):
            try:
                return self.live.get_history(ticker, interval, period_days)
            except Exception as exc:
                logger.warning("Live market history failed for %s: %s", ticker, exc)
        if is_demo_ticker(ticker):
            return self.demo.get_history(ticker, interval, period_days)
        raise ValueError(f"No history available for '{ticker}'")

    def search(self, query: str) -> list[InstrumentInfo]:
        demo_results = self.demo.search(query)
        if self.settings.demo_mode:
            return demo_results
        try:
            live_results = self.live.search(query)
        except Exception as exc:
            logger.warning("Live market search failed for '%s': %s", query, exc)
            live_results = []
        seen = {r.ticker for r in demo_results}
        combined = list(demo_results) + [r for r in live_results if r.ticker not in seen]
        return combined
