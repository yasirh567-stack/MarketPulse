from __future__ import annotations

from pydantic import BaseModel


class SentimentTimelinePoint(BaseModel):
    date: str
    avg_compound: float
    bullish_count: int
    neutral_count: int
    bearish_count: int
    total_count: int


class SourceComparisonEntry(BaseModel):
    avg_compound: float
    count: int


class SentimentResponse(BaseModel):
    ticker: str
    active_model: str
    timeline: list[SentimentTimelinePoint]
    by_source_type: dict[str, SourceComparisonEntry]
    by_model: dict[str, SourceComparisonEntry]
