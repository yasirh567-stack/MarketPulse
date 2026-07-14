"""Scores stored news/social text and aggregates sentiment over time.

Scoring runs in-process (VADER is fast enough not to need a worker queue at
this scale; FinBERT, if enabled, is lazy-loaded and cached so it only pays
its startup cost once). Endpoints that call into this module are registered
as sync `def` routes so Starlette runs them in its threadpool, keeping the
event loop free even if FinBERT is active.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.news import NewsArticle, SocialPost
from app.models.sentiment import SentimentScore
from app.nlp.sentiment import SentimentEngine
from app.schemas.common import SentimentLabel

_engine_cache: dict[bool, SentimentEngine] = {}


def get_engine(settings: Settings) -> SentimentEngine:
    if settings.enable_finbert not in _engine_cache:
        _engine_cache[settings.enable_finbert] = SentimentEngine(settings.enable_finbert)
    return _engine_cache[settings.enable_finbert]


def score_and_store_articles(db: Session, settings: Settings, articles: list[NewsArticle]) -> None:
    engine = get_engine(settings)
    texts = [f"{a.title}. {a.summary or ''}".strip() for a in articles]
    results = engine.score_batch(texts)
    for article, result in zip(articles, results, strict=True):
        db.add(
            SentimentScore(
                ticker=article.ticker,
                source_type="news",
                source_id=article.id,
                text_excerpt=(article.title or "")[:500],
                compound=result.compound,
                label=result.label.value,
                confidence=result.confidence,
                model_name=result.model_name,
                model_version=result.model_version,
                published_at=article.published_at,
            )
        )
    db.commit()


def score_and_store_social(db: Session, settings: Settings, posts: list[SocialPost]) -> None:
    engine = get_engine(settings)
    results = engine.score_batch([p.text for p in posts])
    for post, result in zip(posts, results, strict=True):
        db.add(
            SentimentScore(
                ticker=post.ticker,
                source_type="social",
                source_id=post.id,
                text_excerpt=post.text[:500],
                compound=result.compound,
                label=result.label.value,
                confidence=result.confidence,
                model_name=result.model_name,
                model_version=result.model_version,
                published_at=post.created_at,
            )
        )
    db.commit()


def get_recent_scores(db: Session, ticker: str, limit: int = 200) -> list[SentimentScore]:
    return list(
        db.scalars(
            select(SentimentScore)
            .where(SentimentScore.ticker == ticker.upper())
            .order_by(SentimentScore.published_at.desc())
            .limit(limit)
        ).all()
    )


def aggregate_timeline(
    db: Session, ticker: str, bucket: str = "day", limit_buckets: int = 30
) -> list[dict]:
    """Aggregate sentiment into buckets (currently daily) for the timeline
    chart and mention-volume chart."""
    scores = get_recent_scores(db, ticker, limit=1000)
    buckets: dict[str, list[SentimentScore]] = defaultdict(list)
    for s in scores:
        key = s.published_at.date().isoformat()
        buckets[key].append(s)

    timeline = []
    for date_key in sorted(buckets.keys(), reverse=True)[:limit_buckets]:
        day_scores = buckets[date_key]
        bullish = sum(1 for s in day_scores if s.label == SentimentLabel.BULLISH.value)
        bearish = sum(1 for s in day_scores if s.label == SentimentLabel.BEARISH.value)
        neutral = sum(1 for s in day_scores if s.label == SentimentLabel.NEUTRAL.value)
        avg_compound = sum(s.compound for s in day_scores) / len(day_scores)
        timeline.append(
            {
                "date": date_key,
                "avg_compound": round(avg_compound, 4),
                "bullish_count": bullish,
                "neutral_count": neutral,
                "bearish_count": bearish,
                "total_count": len(day_scores),
            }
        )
    return sorted(timeline, key=lambda r: r["date"])


def source_comparison(db: Session, ticker: str) -> dict:
    """Compares average sentiment across sources (news vs social) and, when
    both VADER and FinBERT scores exist for the same underlying text, across
    models — this is what backs the "compare VADER vs FinBERT" UI panel."""
    scores = get_recent_scores(db, ticker, limit=1000)
    by_source_type: dict[str, list[float]] = defaultdict(list)
    by_model: dict[str, list[float]] = defaultdict(list)
    for s in scores:
        by_source_type[s.source_type].append(s.compound)
        by_model[s.model_name].append(s.compound)

    def _avg(values: list[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    return {
        "by_source_type": {
            k: {"avg_compound": _avg(v), "count": len(v)} for k, v in by_source_type.items()
        },
        "by_model": {k: {"avg_compound": _avg(v), "count": len(v)} for k, v in by_model.items()},
    }
