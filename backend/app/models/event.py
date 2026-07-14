from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utcnow


class DetectedEvent(Base):
    """A rule-based detected market event (earnings, M&A, downgrade, etc.),
    always tied back to the headline that triggered it. Detection is a
    transparent keyword/category match — never presented as causally certain."""

    __tablename__ = "detected_events"
    __table_args__ = (Index("ix_events_ticker_detected", "ticker", "detected_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    matched_keywords: Mapped[str] = mapped_column(Text, nullable=False)  # comma-joined
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
