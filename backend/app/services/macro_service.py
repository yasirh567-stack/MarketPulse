"""Orchestrates the Buffett Indicator: provider fetch (with caching) plus the
percentile-rank/interpretation logic that turns a raw ratio into readable
context — always a factual, historically-relative statement, never a
buy/sell signal.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.config import Settings
from app.providers.macro import BuffettIndicatorData, CompositeBuffettIndicatorProvider

CACHE_KEY = "macro:buffett_indicator"
CACHE_TTL_SECONDS = 6 * 60 * 60  # GDP/Wilshire data moves slowly; 6h is plenty fresh


def _percentile_rank(current: float, history: list[float]) -> float:
    if not history:
        return 50.0
    below_or_equal = sum(1 for v in history if v <= current)
    return round((below_or_equal / len(history)) * 100, 1)


def _interpretation(percentile: float) -> str:
    if percentile >= 90:
        return (
            f"The current ratio is higher than about {percentile:.0f}% of its own history in "
            "this dataset — historically elevated, suggesting richer valuations relative to GDP "
            "than has typically been the case."
        )
    if percentile >= 70:
        return (
            f"The current ratio is higher than about {percentile:.0f}% of its own history in "
            "this dataset — above its typical historical range."
        )
    if percentile >= 30:
        return (
            f"The current ratio sits near the middle of its own history in this dataset "
            f"({percentile:.0f}th percentile) — close to its typical historical range."
        )
    if percentile >= 10:
        return (
            f"The current ratio is lower than about {100 - percentile:.0f}% of its own history "
            "in this dataset — below its typical historical range."
        )
    return (
        f"The current ratio is lower than about {100 - percentile:.0f}% of its own history in "
        "this dataset — historically low relative to GDP."
    )


def get_buffett_indicator(db: Session, settings: Settings) -> dict:
    cache = get_cache(db)
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    provider = CompositeBuffettIndicatorProvider(settings)
    data: BuffettIndicatorData = provider.get()

    history_values = [p.ratio_pct for p in data.historical]
    percentile = _percentile_rank(data.current_ratio_pct, history_values)

    result = {
        "current_ratio_pct": data.current_ratio_pct,
        "as_of": data.as_of.isoformat(),
        "data_status": data.data_status.value,
        "source": data.source,
        "percentile_rank": percentile,
        "interpretation": _interpretation(percentile),
        "historical": [
            {"quarter_end": p.quarter_end.isoformat(), "ratio_pct": p.ratio_pct}
            for p in data.historical
        ],
    }
    cache.set(CACHE_KEY, result, CACHE_TTL_SECONDS)
    return result
