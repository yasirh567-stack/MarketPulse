from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Path, Query

from app.api.deps import AppSettings, DbSession
from app.schemas.market import HistoryResponse, PriceBarResponse, QuoteResponse
from app.services import market_service

router = APIRouter()

TICKER_PATTERN = re.compile(r"^[A-Za-z.\-]{1,10}$")
VALID_INTERVALS = {"1d", "1h", "1wk"}


def _validate_ticker(ticker: str) -> str:
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(status_code=422, detail="Invalid ticker symbol format")
    return ticker.upper()


@router.get("/{ticker}/quote", response_model=QuoteResponse)
def get_quote(db: DbSession, settings: AppSettings, ticker: str = Path(...)):
    ticker = _validate_ticker(ticker)
    quote = market_service.get_quote(db, settings, ticker)
    return QuoteResponse(
        ticker=quote.ticker,
        price=quote.price,
        previous_close=quote.previous_close,
        change_abs=quote.change_abs,
        change_pct=quote.change_pct,
        currency=quote.currency,
        market_status=quote.market_status,
        as_of=quote.as_of,
        data_status=quote.data_status,
        source=quote.source,
    )


@router.get("/{ticker}/history", response_model=HistoryResponse)
def get_history(
    db: DbSession,
    settings: AppSettings,
    ticker: str = Path(...),
    interval: str = Query("1d"),
    period_days: int = Query(180, ge=1, le=1825),
):
    ticker = _validate_ticker(ticker)
    if interval not in VALID_INTERVALS:
        raise HTTPException(
            status_code=422, detail=f"interval must be one of {sorted(VALID_INTERVALS)}"
        )
    bars = market_service.get_history(db, settings, ticker, interval, period_days)

    # Downsample very large payloads for chart rendering while keeping the
    # underlying stored bars intact for analysis (spec: "limit chart payload
    # sizes ... while preserving raw data").
    max_points = 500
    if len(bars) > max_points:
        step = len(bars) // max_points
        bars = bars[::step]

    data_status = bars[0].data_status if bars else None
    source = bars[0].source if bars else "none"
    return HistoryResponse(
        ticker=ticker,
        interval=interval,
        data_status=data_status or "demo",
        source=source,
        bars=[
            PriceBarResponse(
                ts=b.ts,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                adj_close=b.adj_close,
                volume=b.volume,
            )
            for b in bars
        ],
    )
