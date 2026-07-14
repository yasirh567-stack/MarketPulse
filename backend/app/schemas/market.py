from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import DataStatus


class InstrumentSearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str | None = None
    sector: str | None = None
    is_demo: bool = False


class QuoteResponse(BaseModel):
    ticker: str
    name: str | None = None
    price: float
    previous_close: float | None
    change_abs: float | None
    change_pct: float | None
    currency: str
    market_status: str | None
    as_of: datetime
    data_status: DataStatus
    source: str


class PriceBarResponse(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float | None
    volume: int | None


class HistoryResponse(BaseModel):
    ticker: str
    interval: str
    data_status: DataStatus
    source: str
    bars: list[PriceBarResponse]
