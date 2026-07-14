from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utcnow


class SentimentScore(Base):
    """A sentiment score for one piece of text (news article or social post).

    `source_type` + `source_id` point back at the originating row so we never
    duplicate the underlying text, only the derived score. `model_name` /
    `model_version` make it possible to compare VADER vs FinBERT scores for
    the same text later without ambiguity about which model produced which row.
    """

    __tablename__ = "sentiment_scores"
    __table_args__ = (Index("ix_sentiment_ticker_scored", "ticker", "scored_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "news" | "social"
    source_id: Mapped[int] = mapped_column(nullable=False)
    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    compound: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(16), nullable=False)  # bullish|neutral|bearish
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(40), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
