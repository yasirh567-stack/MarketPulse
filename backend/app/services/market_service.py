"""Market data service: fetches quotes/history via the composite provider,
persists them, and serves cached results when available so repeated
dashboard loads don't re-hit the provider (or its rate limits) every time."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.config import Settings
from app.core.errors import ProviderUnavailableError
from app.models.market_data import PriceBar, PriceSnapshot
from app.providers.base import Bar, Quote
from app.providers.market import CompositeMarketDataProvider
from app.schemas.common import DataStatus
from app.services import provider_health_service

QUOTE_CACHE_TTL_SECONDS = 30
HISTORY_CACHE_TTL_SECONDS = 300


def _quote_cache_key(ticker: str) -> str:
    return f"quote:{ticker.upper()}"


def _history_cache_key(ticker: str, interval: str, period_days: int) -> str:
    return f"history:{ticker.upper()}:{interval}:{period_days}"


def get_quote(db: Session, settings: Settings, ticker: str) -> Quote:
    cache = get_cache(db)
    cache_key = _quote_cache_key(ticker)
    cached = cache.get(cache_key)
    if cached is not None:
        return Quote(
            **{
                **cached,
                "as_of": datetime.fromisoformat(cached["as_of"]),
                "data_status": DataStatus(cached["data_status"]),
            }
        )

    provider = CompositeMarketDataProvider(settings)
    try:
        quote = provider.get_quote(ticker)
    except Exception as exc:
        provider_health_service.record_failure(db, "market_data", str(exc))
        raise ProviderUnavailableError("market data", str(exc)) from exc

    provider_health_service.record_success(db, "market_data")
    _persist_snapshot(db, quote)
    cache.set(
        cache_key,
        {
            **quote.__dict__,
            "as_of": quote.as_of.isoformat(),
            "data_status": quote.data_status.value,
        },
        QUOTE_CACHE_TTL_SECONDS,
    )
    return quote


def _persist_snapshot(db: Session, quote: Quote) -> None:
    row = PriceSnapshot(
        ticker=quote.ticker,
        price=quote.price,
        previous_close=quote.previous_close,
        change_abs=quote.change_abs,
        change_pct=quote.change_pct,
        currency=quote.currency,
        market_status=quote.market_status,
        data_status=quote.data_status.value,
        source=quote.source,
        as_of=quote.as_of,
    )
    db.add(row)
    db.commit()


def get_history(
    db: Session, settings: Settings, ticker: str, interval: str = "1d", period_days: int = 180
) -> list[Bar]:
    cache = get_cache(db)
    cache_key = _history_cache_key(ticker, interval, period_days)
    cached = cache.get(cache_key)
    if cached is not None:
        return [
            Bar(
                **{
                    **b,
                    "ts": datetime.fromisoformat(b["ts"]),
                    "data_status": DataStatus(b["data_status"]),
                }
            )
            for b in cached
        ]

    provider = CompositeMarketDataProvider(settings)
    try:
        bars = provider.get_history(ticker, interval, period_days)
    except Exception as exc:
        provider_health_service.record_failure(db, "market_data", str(exc))
        raise ProviderUnavailableError("market data", str(exc)) from exc

    provider_health_service.record_success(db, "market_data")
    _persist_bars(db, bars)
    cache.set(
        cache_key,
        [{**b.__dict__, "ts": b.ts.isoformat(), "data_status": b.data_status.value} for b in bars],
        HISTORY_CACHE_TTL_SECONDS,
    )
    return bars


def _persist_bars(db: Session, bars: list[Bar]) -> None:
    if not bars:
        return
    # A single atomic upsert (rather than the previous check-existing-then-
    # insert loop) so two overlapping requests for the same ticker (e.g. two
    # different period_days windows, or React re-fetching on remount) can
    # never both pass the "does it exist" check and then race each other into
    # a UNIQUE constraint violation on (ticker, interval, ts).
    now = datetime.now(UTC)
    rows = [
        {
            "ticker": bar.ticker,
            "interval": bar.interval,
            "ts": bar.ts,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "adj_close": bar.adj_close,
            "volume": bar.volume,
            "data_status": bar.data_status.value,
            "source": bar.source,
            "fetched_at": now,
        }
        for bar in bars
    ]
    insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
    stmt = insert(PriceBar).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["ticker", "interval", "ts"])
    db.execute(stmt)
    db.commit()
