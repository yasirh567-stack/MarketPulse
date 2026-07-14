from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import AppSettings, DbSession
from app.providers.demo_data import is_demo_ticker
from app.providers.market import CompositeMarketDataProvider
from app.schemas.market import InstrumentSearchResult
from app.schemas.screener import ScreenerResponse
from app.services.screener_service import get_screener

router = APIRouter()


@router.get("/search", response_model=list[InstrumentSearchResult])
def search_instruments(settings: AppSettings, q: str = Query(..., min_length=1, max_length=50)):
    provider = CompositeMarketDataProvider(settings)
    results = provider.search(q)
    return [
        InstrumentSearchResult(
            ticker=r.ticker,
            name=r.name,
            exchange=r.exchange,
            sector=r.sector,
            is_demo=is_demo_ticker(r.ticker),
        )
        for r in results
    ]


@router.get("/screener", response_model=ScreenerResponse)
def get_instrument_screener(
    db: DbSession,
    settings: AppSettings,
    tickers: str | None = Query(
        None, description="Comma-separated tickers. Defaults to the bundled demo tickers."
    ),
):
    """One-call overview of price + aggregate sentiment across several
    tickers — what the dashboard's watchlist sidebar and landing-page
    "at a glance" view are built on, so the UI never has to fire one request
    per ticker just to answer "which of these look bullish right now?"."""
    ticker_list = (
        [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if tickers
        else settings.demo_ticker_list
    )
    entries = get_screener(db, settings, ticker_list[:25])
    return ScreenerResponse(entries=entries)
