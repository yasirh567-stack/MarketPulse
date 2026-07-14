from __future__ import annotations

from fastapi import APIRouter, Path, Query

from app.api.deps import AppSettings, DbSession
from app.schemas.news import NewsArticleResponse, NewsListResponse
from app.services import news_service

router = APIRouter()


@router.get("/{ticker}", response_model=NewsListResponse)
def get_news(
    db: DbSession,
    settings: AppSettings,
    ticker: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    ticker = ticker.upper()
    fetch_limit = page * page_size + page_size
    all_articles = news_service.fetch_and_store_news(
        db, settings, ticker, limit=max(fetch_limit, 20)
    )
    start = (page - 1) * page_size
    page_items = all_articles[start : start + page_size]
    return NewsListResponse(
        ticker=ticker,
        total=len(all_articles),
        page=page,
        page_size=page_size,
        articles=[NewsArticleResponse.model_validate(a) for a in page_items],
    )
