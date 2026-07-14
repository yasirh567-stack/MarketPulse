from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import DataStatus, SentimentLabel


class ScreenerEntry(BaseModel):
    ticker: str
    name: str | None = None
    price: float
    change_pct: float | None
    data_status: DataStatus
    avg_sentiment: float
    sentiment_label: SentimentLabel
    bullish_mentions: int
    bearish_mentions: int
    article_count: int


class ScreenerResponse(BaseModel):
    entries: list[ScreenerEntry]
    disclaimer: str = (
        "Sentiment and price direction are informational signals derived from recent demo/cached "
        "data — not a recommendation to buy or sell."
    )
