"""Multi-ticker overview ("screener"): the single call the dashboard/watchlist
sidebar uses to show price + aggregate sentiment for several tickers at once,
instead of the frontend firing N separate requests per ticker.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.providers.demo_data import load_instruments_manifest
from app.schemas.common import SentimentLabel
from app.schemas.screener import ScreenerEntry
from app.services import news_service, sentiment_service
from app.services.market_service import get_quote

logger = get_logger("app.services.screener")

_NAME_LOOKUP = {item["ticker"]: item["name"] for item in load_instruments_manifest()}


def _sentiment_label(avg_compound: float) -> SentimentLabel:
    if avg_compound >= 0.05:
        return SentimentLabel.BULLISH
    if avg_compound <= -0.05:
        return SentimentLabel.BEARISH
    return SentimentLabel.NEUTRAL


def get_screener(db: Session, settings: Settings, tickers: list[str]) -> list[ScreenerEntry]:
    entries: list[ScreenerEntry] = []
    for ticker in tickers:
        ticker = ticker.upper()
        try:
            quote = get_quote(db, settings, ticker)
        except Exception as exc:
            logger.warning("Screener: skipping %s, quote unavailable: %s", ticker, exc)
            continue

        # Ensure at least demo/cached news+sentiment exists for this ticker,
        # same as the dedicated sentiment endpoint does.
        news_service.fetch_and_store_news(db, settings, ticker, limit=20)
        timeline = sentiment_service.aggregate_timeline(db, ticker, limit_buckets=10)

        if timeline:
            avg_compound = sum(p["avg_compound"] for p in timeline) / len(timeline)
            bullish = sum(p["bullish_count"] for p in timeline)
            bearish = sum(p["bearish_count"] for p in timeline)
            article_count = sum(p["total_count"] for p in timeline)
        else:
            avg_compound, bullish, bearish, article_count = 0.0, 0, 0, 0

        entries.append(
            ScreenerEntry(
                ticker=ticker,
                name=_NAME_LOOKUP.get(ticker),
                price=quote.price,
                change_pct=quote.change_pct,
                data_status=quote.data_status,
                avg_sentiment=round(avg_compound, 4),
                sentiment_label=_sentiment_label(avg_compound),
                bullish_mentions=bullish,
                bearish_mentions=bearish,
                article_count=article_count,
            )
        )
    return entries
