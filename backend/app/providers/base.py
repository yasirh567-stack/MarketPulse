"""Provider interfaces.

Every data source (real or demo) implements one of these Protocols, so
services/routers never branch on "which vendor" — they call the interface and
the currently-configured provider (with its own internal fallback chain)
handles the rest. This is what makes `DEMO_MODE` a one-line env toggle rather
than a maze of `if demo:` checks scattered through the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.schemas.common import DataStatus


@dataclass
class Quote:
    ticker: str
    price: float
    previous_close: float | None
    change_abs: float | None
    change_pct: float | None
    currency: str
    market_status: str | None
    as_of: datetime
    data_status: DataStatus
    source: str


@dataclass
class Bar:
    ticker: str
    interval: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float | None
    volume: int | None
    data_status: DataStatus
    source: str


@dataclass
class RawArticle:
    ticker: str
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    data_status: DataStatus
    is_demo: bool = False


@dataclass
class RawSocialPost:
    ticker: str
    platform: str
    external_id: str
    text: str
    author: str | None
    url: str | None
    created_at: datetime
    is_demo: bool = False


@dataclass
class InstrumentInfo:
    ticker: str
    name: str
    exchange: str | None = None
    sector: str | None = None


class MarketDataProvider(Protocol):
    name: str

    def get_quote(self, ticker: str) -> Quote: ...
    def get_history(self, ticker: str, interval: str, period_days: int) -> list[Bar]: ...
    def search(self, query: str) -> list[InstrumentInfo]: ...


class NewsProvider(Protocol):
    name: str

    def get_headlines(self, ticker: str, limit: int) -> list[RawArticle]: ...


class SocialProvider(Protocol):
    name: str
    enabled: bool

    def get_posts(self, ticker: str, limit: int) -> list[RawSocialPost]: ...
