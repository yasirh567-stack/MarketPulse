"""Shared enums/schemas used across API response models.

`DataStatus` is the backbone of the "never present unlabeled data" constraint:
every payload that carries market/news/sentiment data includes one of these
values, and the frontend renders a badge directly from it.
"""

from __future__ import annotations

from enum import StrEnum


class DataStatus(StrEnum):
    LIVE = "live"
    DELAYED = "delayed"
    HISTORICAL = "historical"
    CACHED = "cached"
    DEMO = "demo"


class SentimentLabel(StrEnum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
