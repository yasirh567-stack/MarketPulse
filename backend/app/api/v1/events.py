from __future__ import annotations

from fastapi import APIRouter, Path

from app.api.deps import AppSettings, DbSession
from app.schemas.events import DetectedEventResponse, EventsListResponse
from app.services import event_service, news_service

router = APIRouter()


@router.get("/{ticker}", response_model=EventsListResponse)
def get_events(db: DbSession, settings: AppSettings, ticker: str = Path(...)):
    ticker = ticker.upper()
    news_service.fetch_and_store_news(db, settings, ticker, limit=20)
    events = event_service.get_recent_events(db, ticker, limit=30)
    return EventsListResponse(
        ticker=ticker,
        events=[
            DetectedEventResponse(
                id=e.id,
                ticker=e.ticker,
                category=e.category,
                headline=e.headline,
                source_url=e.source_url,
                matched_keywords=[k.strip() for k in e.matched_keywords.split(",")],
                confidence=e.confidence,
                published_at=e.published_at,
            )
            for e in events
        ],
    )
