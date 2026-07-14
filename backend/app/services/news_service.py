"""News ingestion service: fetch, normalize, de-duplicate, persist, and kick
off sentiment scoring + event detection for newly seen articles."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.news import NewsArticle
from app.providers.news import CompositeNewsProvider
from app.services import event_service, provider_health_service, sentiment_service


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def fetch_and_store_news(
    db: Session, settings: Settings, ticker: str, limit: int = 20
) -> list[NewsArticle]:
    ticker = ticker.upper()
    provider = CompositeNewsProvider(settings)
    try:
        articles = provider.get_headlines(ticker, limit)
        provider_health_service.record_success(db, "news")
    except Exception as exc:
        provider_health_service.record_failure(db, "news", str(exc))
        articles = []

    new_rows: list[NewsArticle] = []
    for art in articles:
        url_hash = _url_hash(art.url)
        existing = db.scalar(select(NewsArticle).where(NewsArticle.url_hash == url_hash))
        if existing is not None:
            continue
        row = NewsArticle(
            ticker=art.ticker,
            title=art.title,
            summary=art.summary,
            url=art.url,
            url_hash=url_hash,
            source=art.source,
            published_at=art.published_at,
            data_status=art.data_status.value,
            is_demo=art.is_demo,
        )
        db.add(row)
        new_rows.append(row)
    if new_rows:
        db.commit()
        for row in new_rows:
            db.refresh(row)
        sentiment_service.score_and_store_articles(db, settings, new_rows)
        event_service.detect_and_store_events(db, new_rows)

    return list(
        db.scalars(
            select(NewsArticle)
            .where(NewsArticle.ticker == ticker)
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        ).all()
    )
