from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import DetectedEvent
from app.models.news import NewsArticle
from app.nlp.event_detection import detect_events


def detect_and_store_events(db: Session, articles: list[NewsArticle]) -> list[DetectedEvent]:
    new_events: list[DetectedEvent] = []
    for article in articles:
        matches = detect_events(article.title, article.summary or "")
        for match in matches:
            existing = db.scalar(
                select(DetectedEvent).where(
                    DetectedEvent.ticker == article.ticker,
                    DetectedEvent.category == match.category,
                    DetectedEvent.headline == article.title,
                )
            )
            if existing is not None:
                continue
            row = DetectedEvent(
                ticker=article.ticker,
                category=match.category,
                headline=article.title,
                source_url=article.url,
                matched_keywords=", ".join(match.matched_keywords),
                confidence=match.confidence,
                published_at=article.published_at,
                is_demo=article.is_demo,
            )
            db.add(row)
            new_events.append(row)
    if new_events:
        db.commit()
    return new_events


def get_recent_events(db: Session, ticker: str, limit: int = 20) -> list[DetectedEvent]:
    return list(
        db.scalars(
            select(DetectedEvent)
            .where(DetectedEvent.ticker == ticker.upper())
            .order_by(DetectedEvent.published_at.desc())
            .limit(limit)
        ).all()
    )
