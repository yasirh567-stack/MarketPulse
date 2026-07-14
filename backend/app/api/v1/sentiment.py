from __future__ import annotations

from fastapi import APIRouter, Path, Query

from app.api.deps import AppSettings, DbSession
from app.schemas.sentiment import SentimentResponse
from app.services import news_service, sentiment_service

router = APIRouter()


@router.get("/{ticker}", response_model=SentimentResponse)
def get_sentiment(
    db: DbSession,
    settings: AppSettings,
    ticker: str = Path(...),
    window_days: int = Query(30, ge=1, le=180),
):
    ticker = ticker.upper()
    # Ensure we have at least demo/news-derived sentiment rows to aggregate.
    news_service.fetch_and_store_news(db, settings, ticker, limit=20)

    timeline = sentiment_service.aggregate_timeline(db, ticker, limit_buckets=window_days)
    comparison = sentiment_service.source_comparison(db, ticker)
    engine = sentiment_service.get_engine(settings)

    return SentimentResponse(
        ticker=ticker,
        active_model=engine.active_model_name,
        timeline=timeline,
        by_source_type=comparison["by_source_type"],
        by_model=comparison["by_model"],
    )
